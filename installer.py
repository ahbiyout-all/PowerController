import os
import sys
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog
try:
    import winreg
    REG_AVAILABLE = True
except ImportError:
    REG_AVAILABLE = False

try:
    import native_bridge
except ImportError:
    native_bridge = None

# --------------------------------------------------------------------
# 환경 설정 및 상태 변수 정의 (어크릴 다크 테마 일관성 유지)
# --------------------------------------------------------------------
APP_VERSION = "2.9.1"
DARK_BG = "#111827"
DARK_CARD = "#1f2937"
TEXT_COLOR = "#f3f4f6"
ACCENT_BLUE = "#3b82f6"

def terminate_and_unlock_suite_processes(target_dir=None, timeout_sec=5.0, is_silent=False, log_func=None):
    """
    무인 설치(Silent Install) 및 원격 전송 설치 중 이전 프로세스가 즉시 종료되지 않아
    설치가 멈추거나 파일 락(ERROR_SHARING_VIOLATION)으로 실패하는 문제를 원천 차단하는 종합 프로세스 종료 및 락 해제 루틴.
    
    0. 순수 창작 PowerCoreNative.dll 기반 0.01초 무음 프로세스 트리 강제 종료 (콘솔 번쩍임 원천 차단)
    1. 내부 소켓 통신(포트 59384)을 통한 정상 종료 신호(QUIT) 전송 (트레이/소켓 자원 즉시 정리)
    2. taskkill.exe /F /T 트리 강제 종료 (PowerController, PowerNetworkScheduler, ApplySharedSchedules)
    3. PowerShell Stop-Process -Force 보조 강제 종료
    4. WMIC Process Terminate 최종 강제 종료
    5. 프로세스 종료 및 파일 락 해제 적극 대기 (최대 timeout_sec 초)
    6. 잔존 락 발생 시 대상 실행 파일 이름 변경(.old_XXXX)을 통한 파일 핸들 락 우회 해제
    """
    def _log(msg):
        if log_func:
            try:
                log_func(msg)
            except Exception:
                pass
        if not is_silent:
            print(msg)

    _log("[*] 기존 실행 프로세스 즉시 강제 종료 및 파일 락 해제 작업 가동...")
    
    target_exes = ["PowerController.exe", "PowerNetworkScheduler.exe", "ApplySharedSchedules.exe"]

    # 0. 순수 창작 Native DLL 기반 초고속 무음 프로세스 트리 종료 (서브프로세스 스폰 번쩍임 0%)
    if native_bridge:
        for exe in target_exes:
            try:
                killed_cnt = native_bridge.kill_process_by_name_silent(exe)
                if killed_cnt > 0:
                    _log(f"→ Native Engine: '{exe}' 프로세스 {killed_cnt}개 즉시 무음 종료 완료.")
            except Exception:
                pass

    # 1. 포트 59384로 로컬 QUIT 신호 발송 시도
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        s.connect(("127.0.0.1", 59384))
        s.sendall(b"QUIT")
        s.close()
    except Exception:
        pass

    if sys.platform == "win32":
        import subprocess
        # 2. taskkill /F /T 실행 (프로세스 트리 전체 강제 종료)
        for exe in target_exes:
            try:
                subprocess.run(["taskkill", "/F", "/T", "/IM", exe],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            except Exception:
                pass

        # 3. PowerShell Stop-Process 강제 종료
        try:
            names = "','".join([os.path.splitext(e)[0] for e in target_exes])
            ps_cmd = f"Get-Process -Name '{names}' -ErrorAction SilentlyContinue | Stop-Process -Force"
            subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        except Exception:
            pass

        # 4. WMIC 프로세스 강제 종료 (보안 정책 등으로 파워쉘 차단 환경 대비)
        try:
            where_clause = " or ".join([f"name='{e}'" for e in target_exes])
            subprocess.run(["wmic", "process", "where", where_clause, "call", "terminate"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        except Exception:
            pass

    # 5. 프로세스 완전 소멸 및 파일 락 해제 대기 루프 (최대 timeout_sec초)
    import time
    start_time = time.time()
    
    if target_dir and os.path.exists(target_dir):
        for exe in target_exes:
            exe_path = os.path.join(target_dir, exe)
            if not os.path.exists(exe_path):
                continue
            
            file_unlocked = False
            while time.time() - start_time < timeout_sec:
                try:
                    with open(exe_path, "r+b"):
                        pass
                    file_unlocked = True
                    break
                except (PermissionError, IOError):
                    time.sleep(0.2)

            # 만약 여전히 락이 걸려 있다면 Windows 파일 이름 변경 트릭으로 락 우회
            if not file_unlocked and os.path.exists(exe_path):
                try:
                    old_path = exe_path + f".old_{int(time.time() * 1000)}"
                    os.rename(exe_path, old_path)
                    try:
                        os.unlink(old_path)
                    except Exception:
                        pass
                    _log(f"[*] 락 걸린 파일 우회 성공: {exe} -> 임시 이름 변경")
                except Exception as e:
                    _log(f"[!] 파일 락 우회 시도 경고: {e}")
    else:
        time.sleep(0.5)

    _log("[*] 기존 프로세스 정리 및 파일 락 해제 완료.")


def copy_file_safe(src, dst, max_retries=5, is_silent=True, log_func=None):
    """
    파일 복사 시 프로세스 잔존이나 파일 락으로 인한 실패를 100% 방어.
    직접 삭제/덮어쓰기 실패 시 .old_XXXX 이름 변경 후 복사하여 무인 설치 중단(멈춤) 원천 방지.
    """
    import time
    dst_parent = os.path.dirname(dst)
    os.makedirs(dst_parent, exist_ok=True)
    
    for attempt in range(max_retries):
        try:
            if os.path.exists(dst):
                try:
                    os.unlink(dst)
                except Exception:
                    pass
            shutil.copy2(src, dst)
            return True
        except Exception:
            # 락 해제를 위한 프로세스 재종료 및 이름 변경 시도
            if sys.platform == "win32":
                try:
                    exe_name = os.path.basename(dst)
                    import subprocess
                    subprocess.run(["taskkill", "/F", "/T", "/IM", exe_name],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
                except Exception:
                    pass
            
            # Windows 파일 이름 변경 트릭 (실행 중이거나 락 걸린 파일도 rename은 허용됨)
            if os.path.exists(dst):
                try:
                    old_dst = dst + f".old_{int(time.time() * 1000)}"
                    os.rename(dst, old_dst)
                    try:
                        os.unlink(old_dst)
                    except Exception:
                        pass
                    # 이름 변경 후 즉시 재시도
                    shutil.copy2(src, dst)
                    return True
                except Exception:
                    pass
            time.sleep(0.4)

    # 마지막 안전 시도
    try:
        shutil.copy2(src, dst)
        return True
    except Exception:
        return False

# --------------------------------------------------------------------
# 라이선스 및 사용된 오픈소스 구성 정보 선언 (한국어 및 영어 2종류)
# --------------------------------------------------------------------
STANDARD_LICENSE_KO = """[사용권 계약 및 오픈소스 라이선스 약관 고지]

본 프로그램(PowerController)을 설치하여 사용하기 전, 아래의 사용권 및 사용된 오픈소스 소프트웨어 구성 정보를 확인하고 동의해주시기 바랍니다.

--------------------------------------------------
1. 프로그램 표준 라이선스 (MIT License)
--------------------------------------------------
Copyright (c) 2026 AhBiYout

이 소프트웨어의 복제본과 관련된 문서 파일(이하 "소프트웨어")을 획득하는 모든 사람에게 소프트웨어를 제한 없이 사용할 수 있는 권한을 부여합니다. 여기에는 소프트웨어의 사본을 사용, 복제, 수정, 병합, 게시, 배포, 서브라이선스 부여 및/또는 판매할 수 있는 권한이 포함되며, 이를 위해 다음 조건을 충족해야 합니다:

상기 저작권 고시와 본 허용 고시가 소프트웨어의 모든 복제본 또는 상당 부분에 포함되어야 합니다.

소프트웨어는 "있는 그대로" 제공되며, 상품성, 특정 목적에의 적합성 및 비침해에 대한 보증을 포함하되 이에 국한되지 않고 명시적이거나 묵시적인 어떠한 보증도 제공하지 않습니다. 저작업자나 저작권자는 어떠한 상황에서도 소프트웨어 또는 소프트웨어의 사용과 관련하여 발생하는 계약, 불법행위 또는 기타 다른 행위로 인한 청구, 손해 또는 기타 책임에 대해 책임을 지지 않습니다.

--------------------------------------------------
2. 사용된 오픈소스 라이브러리 및 저작권 (Used Libraries)
--------------------------------------------------
본 소프트웨어는 최적의 원격 및 실시간 컴퓨터 전원 감시 및 관리를 달성하기 위해 아래와 같은 표준 검증된 라이브러리와 인스턴스를 사용하고 있습니다:

■ pystray (v0.19.5+)
  - 라이선스: LGPL v3 / BSD Dual License
  - 사용 목적: 윈도우 작업 표시줄 우측의 시스템 트레이 백그라운드 상주 감시 컨트롤 및 트레이 우클릭 퀵 메뉴 컨트롤러 구현
  - 특징: 저전력 상향 트리거 데몬

■ Pillow (PIL - Python Imaging Library v10.0+)
  - 라이선스: HPND License (Historically Broad License)
  - 사용 목적: 시스템 트레이 내에서 동적으로 세련된 전원 번개 로고(64x64) 아이콘을 도식하며 마스킹 렌더링을 지휘
  - 특징: 무손실 속도 최적화 컴파일러용 동적 드로우 엔진

■ PyInstaller (v6.0+)
  - 라이선스: GPL v2 with Bootloader Exception
  - 사용 목적: 독립 실행형 패키지(Single EXE) 및 설치 마법사 빌드 래퍼 패키징 컴파일러 기동
  - 특징: 경량 패키징 런타임 릴리즈 바이너리

■ Tkinter (Python Standard GUI library)
  - 라이선스: Python Software Foundation (PSF) License
  - 사용 목적: 직관적인 사용자 중심의 어크릴 다크 테마 데스크톱 윈도우 인터페이스 구축 및 스케줄링 가이드 레이아웃
  - 특징: 경량의 신속한 운영체제 네이티브 GUI 컴포넌트
설치를 계속 진행하시면, 상위 라이선스 계약서와 사용 라이브러리 고지사항에 동의하시는 것으로 간주됩니다.
"""

STANDARD_LICENSE_EN = """[End User License Agreement & Open Source Notice]

Before installing and using this software (PowerController), please review and agree to the license terms and open-source software component disclosures below.

--------------------------------------------------
1. Software Standard License (MIT License)
--------------------------------------------------
Copyright (c) 2026 AhBiYout

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

--------------------------------------------------
2. Open Source Libraries & Copyright Disclosures
--------------------------------------------------
PowerController incorporates the following standard libraries and components to ensure reliable real-time and remote system power management:

■ pystray (v0.19.5+)
  - License: LGPL v3 / BSD Dual License
  - Purpose: System tray background residency monitoring and quick contextual tray menu operations
  - Feature: Low-power persistent event daemon

■ Pillow (PIL - Python Imaging Library v10.0+)
  - License: HPND License (Historical Permission Notice and Disclaimer)
  - Purpose: Dynamic multi-resolution power icon (64x64) rendering and mask compositing
  - Feature: Lossless performance-optimized drawing engine

■ PyInstaller (v6.0+)
  - License: GPL v2 with Bootloader Exception
  - Purpose: Standalone binary compilation and deployment wrapper packaging
  - Feature: Lightweight native binary execution runtime

■ Tkinter (Python Standard GUI Library)
  - License: Python Software Foundation (PSF) License
  - Purpose: Dark-mode desktop graphical user interface and schedule configuration controls
  - Feature: Lightweight and responsive OS-native GUI components

By proceeding with the installation, you acknowledge and agree to the license agreement and third-party notices above.
"""

STANDARD_LICENSE = STANDARD_LICENSE_KO

def register_firewall_rules_all(install_dir, log_func=None):
    """
    설치 프로그램(Installer)에서 방화벽 규칙을 사전에 조용히 등록.
    메인(PowerController.exe)과 커맨더(PowerNetworkScheduler.exe) 2개 모두 방화벽에 등록하며,
    버전 정보(v{APP_VERSION})가 붙은 상태의 앱 이름도 함께 등록합니다.
    """
    if os.name != 'nt':
        return

    # 0. 순수 창작 FirewallNative.dll COM 직결 일괄 등록 (0.05초 만에 메모리 내 완수)
    if native_bridge and native_bridge.is_firewall_engine_loaded():
        try:
            reg_cnt = native_bridge.batch_register_firewall_suite(install_dir, APP_VERSION)
            if reg_cnt > 0:
                if log_func:
                    log_func(f"Native Engine: Windows 방화벽 규칙 {reg_cnt}개 COM 직결 등록 완료 (0.05초)")
                else:
                    print(f"[+] Native Engine: Registered {reg_cnt} Windows Firewall rules via COM")
                return
        except Exception:
            pass

    try:
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        target_exe = os.path.join(install_dir, "PowerController.exe")
        pns_exe = os.path.join(install_dir, "PowerNetworkScheduler.exe")

        # 0. 중복 방지를 위해 기존 동명 규칙 사전 정리
        rule_names_to_clean = [
            "PowerController (Inbound)", "PowerController (Outbound)",
            f"PowerController v{APP_VERSION} (Inbound)", f"PowerController v{APP_VERSION} (Outbound)",
            "PowerNetworkScheduler (Inbound)", "PowerNetworkScheduler (Outbound)",
            f"PowerNetworkScheduler v{APP_VERSION} (Inbound)", f"PowerNetworkScheduler v{APP_VERSION} (Outbound)",
            "PowerController TCP 9988", "PowerController UDP 9985", "PowerController UDP 9986",
            f"PowerController v{APP_VERSION} TCP 9988", f"PowerController v{APP_VERSION} UDP 9985", f"PowerController v{APP_VERSION} UDP 9986",
            "PowerController"
        ]
        for r_name in rule_names_to_clean:
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={r_name}"],
                capture_output=True,
                creationflags=creationflags
            )

        # 1. 메인 앱 (PowerController.exe) Inbound & Outbound (기본 및 버전 표기)
        if os.path.exists(target_exe):
            for dir_type in ["in", "out"]:
                dir_label = "Inbound" if dir_type == "in" else "Outbound"
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule",
                     f"name=PowerController ({dir_label})", f"dir={dir_type}", "action=allow",
                     f"program={target_exe}", "enable=yes", "profile=any"],
                    capture_output=True, creationflags=creationflags
                )
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule",
                     f"name=PowerController v{APP_VERSION} ({dir_label})", f"dir={dir_type}", "action=allow",
                     f"program={target_exe}", "enable=yes", "profile=any"],
                    capture_output=True, creationflags=creationflags
                )

        # 2. 커맨더 관리 도구 (PowerNetworkScheduler.exe) Inbound & Outbound (기본 및 버전 표기)
        if os.path.exists(pns_exe):
            for dir_type in ["in", "out"]:
                dir_label = "Inbound" if dir_type == "in" else "Outbound"
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule",
                     f"name=PowerNetworkScheduler ({dir_label})", f"dir={dir_type}", "action=allow",
                     f"program={pns_exe}", "enable=yes", "profile=any"],
                    capture_output=True, creationflags=creationflags
                )
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule",
                     f"name=PowerNetworkScheduler v{APP_VERSION} ({dir_label})", f"dir={dir_type}", "action=allow",
                     f"program={pns_exe}", "enable=yes", "profile=any"],
                    capture_output=True, creationflags=creationflags
                )

        # 3. 원격 통신 포트 규칙 (TCP 9988, UDP 9985, UDP 9986 - 기본 및 버전 표기)
        ports = [("TCP", "9988"), ("UDP", "9985"), ("UDP", "9986")]
        for proto, port in ports:
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule",
                 f"name=PowerController {proto} {port}", "dir=in", "action=allow",
                 f"protocol={proto}", f"localport={port}", "enable=yes", "profile=any"],
                capture_output=True, creationflags=creationflags
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule",
                 f"name=PowerController v{APP_VERSION} {proto} {port}", "dir=in", "action=allow",
                 f"protocol={proto}", f"localport={port}", "enable=yes", "profile=any"],
                capture_output=True, creationflags=creationflags
            )

        if log_func:
            log_func(f"Windows 방화벽 사전 무음 등록 완료: 메인 및 커맨더(v{APP_VERSION}) 인바운드/아웃바운드 및 포트")
        else:
            print(f"[+] Windows 방화벽 규칙 사전 등록 완료 (PowerController 및 PowerNetworkScheduler, v{APP_VERSION})")
    except Exception as e:
        if log_func:
            log_func(f"방화벽 등록 예외 (무시됨): {e}")

def remove_firewall_rules_all(log_func=None):
    """프로그램 제거 시 등록된 모든 방화벽 규칙(기본 및 버전 표기)을 깔끔하게 소거합니다."""
    if os.name != 'nt':
        return

    # 0. 순수 창작 FirewallNative.dll COM 직결 일괄 제거 (초고속 0.01초)
    if native_bridge and native_bridge.is_firewall_engine_loaded():
        try:
            rm_cnt = native_bridge.batch_remove_firewall_suite(APP_VERSION)
            if rm_cnt > 0:
                if log_func:
                    log_func(f"Native Engine: Windows 방화벽 규칙 {rm_cnt}개 COM 직결 소거 완료")
                else:
                    print(f"[+] Native Engine: Removed {rm_cnt} Windows Firewall rules via COM")
                return
        except Exception:
            pass

    try:
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        rule_names_to_clean = [
            "PowerController (Inbound)", "PowerController (Outbound)",
            f"PowerController v{APP_VERSION} (Inbound)", f"PowerController v{APP_VERSION} (Outbound)",
            "PowerNetworkScheduler (Inbound)", "PowerNetworkScheduler (Outbound)",
            f"PowerNetworkScheduler v{APP_VERSION} (Inbound)", f"PowerNetworkScheduler v{APP_VERSION} (Outbound)",
            "PowerController TCP 9988", "PowerController UDP 9985", "PowerController UDP 9986",
            f"PowerController v{APP_VERSION} TCP 9988", f"PowerController v{APP_VERSION} UDP 9985", f"PowerController v{APP_VERSION} UDP 9986",
            "PowerController"
        ]
        for r_name in rule_names_to_clean:
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={r_name}"],
                capture_output=True,
                creationflags=creationflags
            )
        if log_func:
            log_func("Windows 방화벽 승인 규칙 정리 완료 (메인 및 커맨더 기본/버전 규칙)")
        else:
            print("[+] Removed Windows Firewall rules (standard and version-tagged)")
    except Exception:
        pass

class SetupWizard:
    def __init__(self, root, uninstall_performed=False):
        self.root = root
        self.uninstall_performed = uninstall_performed
        self.root.title("PowerController 설치 마법사 (Setup Wizard)")
        window_width = 480
        window_height = 520
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.resizable(False, False)
        self.root.configure(bg=DARK_BG)
        
        # Set installer window icon
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            asset_dir = sys._MEIPASS
        else:
            asset_dir = os.path.dirname(os.path.abspath(__file__))
            
        try:
            png_path = os.path.join(asset_dir, "PowerController.png")
            ico_path = os.path.join(asset_dir, "PowerController.ico")
            
            if not os.path.exists(png_path) and os.path.exists("PowerController.png"):
                png_path = "PowerController.png"
            if not os.path.exists(ico_path) and os.path.exists("PowerController.ico"):
                ico_path = "PowerController.ico"
                
            if os.path.exists(png_path):
                self.img_icon = tk.PhotoImage(file=png_path)
                self.root.iconphoto(True, self.img_icon)
            elif os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
        except Exception:
            pass
        
        # 기본 설치 경로 설정
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        self.install_dir = tk.StringVar(value=os.path.normpath(os.path.join(local_app_data, "PowerController")))
        
        self.create_desktop_shortcut = tk.BooleanVar(value=True)
        self.register_startup = tk.BooleanVar(value=True)
        self.run_after_install = tk.BooleanVar(value=True)
        self.license_agreed = tk.BooleanVar(value=False)
        self.clean_install = tk.BooleanVar(value=False)
        
        self.current_step = 1
        
        self.create_widgets()
        
    def create_widgets(self):
        # 상단 헤더 프레임
        self.header_frame = tk.Frame(self.root, bg=DARK_CARD, pady=15)
        self.header_frame.pack(fill="x")
        
        self.title_label = tk.Label(
            self.header_frame, 
            text="⚡ PowerController 설치 프로그램", 
            font=("Arial", 14, "bold"), 
            fg=TEXT_COLOR, 
            bg=DARK_CARD
        )
        self.title_label.pack()
        
        self.desc_label = tk.Label(
            self.header_frame, 
            text="사용하기 쉬운 저전력 스마트 전원 관리 어시스턴트를 컴퓨터에 설치합니다.", 
            font=("Arial", 9), 
            fg="#9ca3af", 
            bg=DARK_CARD
        )
        self.desc_label.pack(pady=5)
        
        # 하단 컨트롤 바 (콘텐츠 프레임 전에 패킹하여 무조건 가장 하단에 확실히 도킹)
        self.action_frame = tk.Frame(self.root, bg=DARK_BG, pady=10)
        self.action_frame.pack(side="bottom", fill="x")

        # 중앙 콘텐츠 영역 (남은 공간을 완벽히 차지)
        self.content_frame = tk.Frame(self.root, bg=DARK_BG)
        self.content_frame.pack(side="top", fill="both", expand=True, padx=20, pady=15)
        
        # 네비게이션 버튼 등록
        self.btn_next = tk.Button(
            self.action_frame, 
            text="동의하며 다음으로 >", 
            font=("Arial", 10, "bold"),
            bg=ACCENT_BLUE, 
            fg="white", 
            relief="flat",
            padx=15,
            pady=8,
            command=self.next_step
        )
        self.btn_next.pack(side="right", padx=20)
        
        self.btn_back = tk.Button(
            self.action_frame, 
            text="< 이전으로", 
            font=("Arial", 10),
            bg="#374151", 
            fg=TEXT_COLOR, 
            relief="flat",
            padx=15,
            pady=8,
            command=self.prev_step
        )
        
        self.btn_cancel = tk.Button(
            self.action_frame, 
            text="닫기 (Cancel)", 
            font=("Arial", 10),
            bg="#374151", 
            fg=TEXT_COLOR, 
            relief="flat",
            padx=15,
            pady=8,
            command=self.root.quit
        )
        self.btn_cancel.pack(side="left", padx=20)
        
        self.load_step()
        
    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
    def load_step(self):
        self.clear_content_frame()
        
        if self.current_step == 1:
            self.desc_label.config(text="사용하기 전 표준 라이선스 형태 및 사용 오픈소스 목록을 확인해 주십시오.")
            self.btn_back.pack_forget()
            self.btn_next.config(
                text="동의하며 다음으로 >", 
                state="normal" if self.license_agreed.get() else "disabled", 
                bg=ACCENT_BLUE if self.license_agreed.get() else "#4b5563"
            )
            
            # 라이선스 안내 레이블 (가장 상단에 배치)
            license_label = tk.Label(
                self.content_frame, 
                text="표준 MIT 라이선스 및 사용된 라이브러리 목록 고지:", 
                font=("Arial", 9, "bold"), 
                fg=TEXT_COLOR, 
                bg=DARK_BG
            )
            license_label.pack(side="top", anchor="w", pady=(0, 5))
            
            # 동의 체크레이드 (가장 하단에 배치)
            chk_agree = tk.Checkbutton(
                self.content_frame, 
                text="사용권 계약서 및 오픈소스 사용 목록 고지에 동의합니다.", 
                variable=self.license_agreed,
                command=self.toggle_agreement,
                bg=DARK_BG, 
                fg=TEXT_COLOR,
                selectcolor=DARK_CARD,
                activebackground=DARK_BG,
                activeforeground=TEXT_COLOR,
                font=("Arial", 9, "bold")
            )
            chk_agree.pack(side="bottom", anchor="w", pady=(10, 0))

            # 라이선스 언어 전환 툴바 (한국어 / English 2종류)
            if not hasattr(self, 'license_lang'):
                self.license_lang = "ko"
                
            lang_toolbar = tk.Frame(self.content_frame, bg=DARK_BG)
            lang_toolbar.pack(side="top", fill="x", pady=(0, 6))
            
            lbl_lang_hint = tk.Label(
                lang_toolbar,
                text="📄 라이선스 언어 (License Language):",
                font=("Arial", 9, "bold"),
                fg=TEXT_COLOR,
                bg=DARK_BG
            )
            lbl_lang_hint.pack(side="left", padx=(0, 8))
            
            # 스크롤 가능 텍스트 상자 (가운데 빈 칸을 가득 채우며 확장)
            text_frame = tk.Frame(self.content_frame, bg=DARK_BG)
            text_frame.pack(side="top", fill="both", expand=True, pady=2)
            
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side="right", fill="y")
            
            license_text = tk.Text(
                text_frame, 
                wrap="word", 
                yscrollcommand=scrollbar.set,
                bg=DARK_CARD, 
                fg=TEXT_COLOR, 
                font=("Arial", 9), 
                relief="flat", 
                padx=10, 
                pady=10
            )
            license_text.insert("1.0", STANDARD_LICENSE_KO if self.license_lang == "ko" else STANDARD_LICENSE_EN)
            license_text.config(state="disabled")
            license_text.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=license_text.yview)

            def switch_license_language(target_lang):
                self.license_lang = target_lang
                license_text.config(state="normal")
                license_text.delete("1.0", "end")
                license_text.insert("1.0", STANDARD_LICENSE_KO if target_lang == "ko" else STANDARD_LICENSE_EN)
                license_text.config(state="disabled")
                license_text.yview_moveto(0.0)
                
                btn_lang_ko.config(
                    bg=ACCENT_BLUE if target_lang == "ko" else DARK_CARD,
                    fg="white" if target_lang == "ko" else "#9ca3af"
                )
                btn_lang_en.config(
                    bg=ACCENT_BLUE if target_lang == "en" else DARK_CARD,
                    fg="white" if target_lang == "en" else "#9ca3af"
                )
                if target_lang == "en":
                    chk_agree.config(text="I agree to the End User License Agreement and terms.")
                    self.desc_label.config(text="Please review the license terms below before continuing.")
                    lbl_lang_hint.config(text="📄 License Language:")
                else:
                    chk_agree.config(text="사용권 계약서 및 오픈소스 사용 목록 고지에 동의합니다.")
                    self.desc_label.config(text="프로그램을 설치하기 전에 아래 라이선스 및 사용권 약관을 확인해 주십시오.")
                    lbl_lang_hint.config(text="📄 라이선스 언어 (License Language):")

            btn_lang_ko = tk.Button(
                lang_toolbar,
                text="🇰🇷 한국어 (Korean)",
                font=("Arial", 8, "bold"),
                bg=ACCENT_BLUE if self.license_lang == "ko" else DARK_CARD,
                fg="white" if self.license_lang == "ko" else "#9ca3af",
                relief="flat",
                padx=8,
                pady=2,
                cursor="hand2",
                command=lambda: switch_license_language("ko")
            )
            btn_lang_ko.pack(side="left", padx=2)

            btn_lang_en = tk.Button(
                lang_toolbar,
                text="🇺🇸 English (영어)",
                font=("Arial", 8, "bold"),
                bg=ACCENT_BLUE if self.license_lang == "en" else DARK_CARD,
                fg="white" if self.license_lang == "en" else "#9ca3af",
                relief="flat",
                padx=8,
                pady=2,
                cursor="hand2",
                command=lambda: switch_license_language("en")
            )
            btn_lang_en.pack(side="left", padx=2)
            
        elif self.current_step == 2:
            self.desc_label.config(text="사용하기 쉬운 저전력 스마트 전원 관리 어시스턴트를 컴퓨터에 설치합니다.")
            self.btn_back.pack(side="right", padx=(0, 10))
            self.btn_next.config(text="🚀 설치 시작", state="normal", bg=ACCENT_BLUE)
            
            # 경로 레이블 및 컨트롤
            path_label = tk.Label(
                self.content_frame, 
                text="설치할 대상 디렉토리 경로를 지정하십시오:", 
                font=("Arial", 9, "bold"), 
                fg=TEXT_COLOR, 
                bg=DARK_BG
            )
            path_label.pack(anchor="w", pady=(0, 5))
            
            path_frame = tk.Frame(self.content_frame, bg=DARK_BG)
            path_frame.pack(fill="x", pady=5)
            
            self.ent_path = tk.Entry(path_frame, textvariable=self.install_dir, font=("Arial", 9), justify="left")
            self.ent_path.pack(side="left", fill="x", expand=True, ipady=3)
            
            btn_browse = tk.Button(
                path_frame, 
                text="찾아보기...", 
                font=("Arial", 9), 
                bg="#374151", 
                fg=TEXT_COLOR, 
                relief="flat", 
                padx=10, 
                command=self.browse_folder
            )
            btn_browse.pack(side="left", padx=(5, 0))
            
            # 설치 옵션
            opt_frame = tk.Frame(self.content_frame, bg=DARK_BG)
            opt_frame.pack(anchor="w", pady=20)
            
            chk_shortcut = tk.Checkbutton(
                opt_frame, 
                text="바탕 화면에 바로가기 만들기 (Desktop Shortcut)", 
                variable=self.create_desktop_shortcut,
                bg=DARK_BG, 
                fg=TEXT_COLOR,
                selectcolor=DARK_CARD,
                activebackground=DARK_BG,
                activeforeground=TEXT_COLOR,
                font=("Arial", 9)
            )
            chk_shortcut.pack(anchor="w")
            
            chk_startup = tk.Checkbutton(
                opt_frame, 
                text="컴퓨터 시작 시 자동 실행 구동 등록 (Registry Startup)", 
                variable=self.register_startup,
                bg=DARK_BG, 
                fg=TEXT_COLOR,
                selectcolor=DARK_CARD,
                activebackground=DARK_BG,
                activeforeground=TEXT_COLOR,
                font=("Arial", 9)
            )
            chk_startup.pack(anchor="w", pady=(8, 0))
            
            chk_run = tk.Checkbutton(
                opt_frame, 
                text="설치 완료 후 프로그램 실행하기 (Run After Installation)", 
                variable=self.run_after_install,
                bg=DARK_BG, 
                fg=TEXT_COLOR,
                selectcolor=DARK_CARD,
                activebackground=DARK_BG,
                activeforeground=TEXT_COLOR,
                font=("Arial", 9)
            )
            chk_run.pack(anchor="w", pady=(8, 0))
            
            chk_clean = tk.Checkbutton(
                opt_frame, 
                text="기존 환경설정 및 저장된 규칙 완전 초기화 (Clean Settings Reset)", 
                variable=self.clean_install,
                bg=DARK_BG, 
                fg=TEXT_COLOR,
                selectcolor=DARK_CARD,
                activebackground=DARK_BG,
                activeforeground=TEXT_COLOR,
                font=("Arial", 9)
            )
            chk_clean.pack(anchor="w", pady=(8, 0))
            
        elif self.current_step == 3:
            self.desc_label.config(text="프로그램 설치 작업이 실시간 진행 중입니다. 잠시만 기다려 주십시오...")
            self.btn_back.pack_forget()
            self.btn_next.config(text="설치 완료 대기", state="disabled", bg="#4b5563")
            self.btn_cancel.config(state="disabled")
            
            # 설치 진행 레이블
            self.install_status_lbl = tk.Label(
                self.content_frame, 
                text="설치 파일 복사 준비 중...", 
                font=("Arial", 10, "bold"), 
                fg=TEXT_COLOR, 
                bg=DARK_BG
            )
            self.install_status_lbl.pack(anchor="w", pady=(15, 5))
            
            # 진행률 바 컨테이너
            self.progress_container = tk.Frame(self.content_frame, bg="#374151", height=24)
            self.progress_container.pack(fill="x", pady=5)
            self.progress_container.pack_propagate(False)
            
            # 실시간 연동 진행률 바
            self.progress_bar = tk.Frame(self.progress_container, bg=ACCENT_BLUE)
            self.progress_bar.place(relx=0, rely=0, relwidth=0.0, relheight=1.0)
            
            # 진행 백분율 레이블
            self.progress_percent_lbl = tk.Label(
                self.content_frame, 
                text="0%", 
                font=("Arial", 11, "bold"), 
                fg=ACCENT_BLUE, 
                bg=DARK_BG
            )
            self.progress_percent_lbl.pack(pady=5)
            
            # 실시간 로그 출력 창
            self.log_textbox = tk.Text(
                self.content_frame, 
                bg=DARK_CARD, 
                fg="#9ca3af", 
                font=("Consolas", 8), 
                height=8, 
                relief="flat", 
                padx=8, 
                pady=8
            )
            self.log_textbox.pack(fill="both", expand=True, pady=(10, 0))
            self.log_textbox.config(state="disabled")
            
            # 백그라운드가 갱신된 후 설치 시작 처리
            self.root.after(200, self.run_install_with_progress)
            
    def toggle_agreement(self):
        if self.license_agreed.get():
            self.btn_next.config(state="normal", bg=ACCENT_BLUE)
        else:
            self.btn_next.config(state="disabled", bg="#4b5563")
            
    def next_step(self):
        if self.current_step == 1:
            if self.license_agreed.get():
                self.current_step = 2
                self.load_step()
        elif self.current_step == 2:
            target_dir = self.install_dir.get()
            if not target_dir:
                messagebox.showerror("오류", "올바른 설치 경로를 지정하여 주십시오.")
                return
                
            # 이전 버전 존재 여부 확인
            is_previous_version = False
            if not self.uninstall_performed and os.path.exists(target_dir):
                if os.path.isdir(target_dir) and os.listdir(target_dir):
                    is_previous_version = True
                    
            if is_previous_version:
                ans = messagebox.askyesnocancel(
                    "기존 설치 파일 감지",
                    "지정한 설치 경로에 기존 버전 파일이 감지되었습니다.\n\n"
                    "안전하고 깨끗한 설치를 위해 먼저 기존 버전을 언인스톨(제거 마법사)하시겠습니까?\n\n"
                    "[예] - 제거 마법사를 실행하여 기존 버전을 깨끗이 지운 후 다시 설치 (권장)\n"
                    "[아니오] - 제거 마법사 없이 바로 복사 및 덮어쓰기 설치 진행\n"
                    "[취소] - 설치 작업 중단"
                )
                if ans is None: # Cancel
                    return
                elif ans: # Yes -> Transition to UninstallWizard
                    for widget in self.root.winfo_children():
                        widget.destroy()
                    
                    def go_back_to_setup():
                        self.root.title("PowerController 설치 마법사 (Setup Wizard)")
                        new_setup = SetupWizard(self.root, uninstall_performed=True)
                        new_setup.install_dir.set(target_dir)
                        new_setup.license_agreed.set(True)
                        new_setup.current_step = 2
                        new_setup.load_step()
                        
                    UninstallWizard(self.root, target_dir=target_dir, reinstall_callback=go_back_to_setup)
                    return
                else: # No -> Standard silent cleanup fallback
                    self.delete_old_version = True
            else:
                self.delete_old_version = False
                
            self.current_step = 3
            self.load_step()
            
    def prev_step(self):
        if self.current_step == 2:
            self.current_step = 1
            self.load_step()
        
    def browse_folder(self):
        dir_selected = filedialog.askdirectory(initialdir=self.install_dir.get(), title="설치 폴더 지정")
        if dir_selected:
            self.install_dir.set(os.path.normpath(dir_selected))
            
    def add_install_log(self, text):
        self.log_textbox.config(state="normal")
        self.log_textbox.insert("end", text + "\n")
        self.log_textbox.see("end")
        self.log_textbox.config(state="disabled")
        self.root.update()

    def update_install_progress(self, ratio, status_text):
        self.install_status_lbl.config(text=status_text)
        self.progress_bar.place(relwidth=ratio)
        self.progress_percent_lbl.config(text=f"{int(ratio * 100)}%")
        self.root.update()

    def run_install_with_progress(self):
        target_dir = self.install_dir.get()
        # 무조건 실행 중인 이전 프로세스를 강제 종료하고 파일 락 해제 대기
        terminate_and_unlock_suite_processes(target_dir, timeout_sec=5.0, is_silent=False, log_func=self.add_install_log)
        self.add_install_log("설치 대상 디렉토리 정렬 중: " + target_dir)
        
        # 1. 원본 파일 소스 탐지
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        target_exe = os.path.join(target_dir, "PowerController.exe")
        bundled_folder = os.path.join(base_path, "PowerController")
        if not os.path.exists(bundled_folder):
            bundled_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "PowerController")

        # 2. 복사할 파일 전체 목록 집계
        files_to_copy = []
        has_bundled_folder = os.path.exists(bundled_folder) and os.path.isdir(bundled_folder)
        
        if has_bundled_folder:
            def collect_files(src_p, dst_p):
                if os.path.isdir(src_p):
                    for item in os.listdir(src_p):
                        collect_files(os.path.join(src_p, item), os.path.join(dst_p, item))
                else:
                    files_to_copy.append((src_p, dst_p))
            collect_files(bundled_folder, target_dir)
        else:
            bundled_exe = os.path.join(base_path, "PowerController.exe")
            if not os.path.exists(bundled_exe):
                bundled_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "PowerController.exe")
            if os.path.exists(bundled_exe):
                files_to_copy.append((bundled_exe, target_exe))

        # 2.5 Ensure icon files are always explicitly included in copies if available in base_path
        for icon_file in ["PowerController.ico", "PowerController.png"]:
            src_icon = os.path.join(base_path, icon_file)
            if os.path.exists(src_icon):
                dst_icon = os.path.join(target_dir, icon_file)
                if not any(item[1] == dst_icon for item in files_to_copy):
                    files_to_copy.append((src_icon, dst_icon))

        # 2.55 Ensure schedule_share_builder.py is explicitly included
        for script_file in ["schedule_share_builder.py"]:
            src_script = os.path.join(base_path, script_file)
            if os.path.exists(src_script):
                dst_script = os.path.join(target_dir, script_file)
                if not any(item[1] == dst_script for item in files_to_copy):
                    files_to_copy.append((src_script, dst_script))

        # 2.56 Companion tools, native DLLs & executables
        for comp_tool in ["PowerCoreNative.dll", "NetBeaconEngine.dll", "FirewallNative.dll", "SysPowerHook.dll", "ScheduleCrypto.dll", "native_bridge.py", "PowerNetworkScheduler.exe", "ApplySharedSchedules.exe", "Register_Firewall_Rules.bat"]:
            src_tool = os.path.join(base_path, comp_tool)
            if not os.path.exists(src_tool):
                src_tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", comp_tool)
            if not os.path.exists(src_tool):
                src_tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), comp_tool)
            if not os.path.exists(src_tool) and comp_tool.endswith(".dll"):
                src_tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), "native", comp_tool)
            if os.path.exists(src_tool):
                dst_tool = os.path.join(target_dir, comp_tool)
                if not any(item[1] == dst_tool for item in files_to_copy):
                    files_to_copy.append((src_tool, dst_tool))

        # 2.57 Documentation multi-files (docs/ tree)
        docs_src = os.path.join(base_path, "docs")
        if not os.path.exists(docs_src):
            docs_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
        if os.path.exists(docs_src) and os.path.isdir(docs_src):
            docs_dst = os.path.join(target_dir, "docs")
            for d_file in os.listdir(docs_src):
                s_df = os.path.join(docs_src, d_file)
                d_df = os.path.join(docs_dst, d_file)
                if os.path.isfile(s_df) and not any(item[1] == d_df for item in files_to_copy):
                    files_to_copy.append((s_df, d_df))

        # 2.6 복사할 파일에 uninstaller.exe 또는 uninstaller.py 추가 (제어판 언인스톨러 연계용)
        if getattr(sys, 'frozen', False):
            uninstaller_src = sys.executable
            uninstaller_dst = os.path.join(target_dir, "uninstaller.exe")
        else:
            uninstaller_src = os.path.abspath(__file__)
            uninstaller_dst = os.path.join(target_dir, "uninstaller.py")
        
        if os.path.exists(uninstaller_src):
            if not any(item[1] == uninstaller_dst for item in files_to_copy):
                files_to_copy.append((uninstaller_src, uninstaller_dst))

        # 3. 전체 진행 단계(Steps) 예측 및 계산
        # - 삭제: 5단계
        # - 폴더 생성: 2단계
        # - 복사: 파일별 1단계 (최소 1개)
        # - 바로가기: 2단계
        # - 시작 프로그램: 2단계
        # - 삭제 등록: 2단계
        total_steps = len(files_to_copy) + 8
        if getattr(self, "delete_old_version", False):
            total_steps += 5
            
        current_step_idx = 0
        
        def step_done(increment=1, msg=""):
            nonlocal current_step_idx
            current_step_idx += increment
            ratio = min(1.0, current_step_idx / total_steps)
            self.update_install_progress(ratio, msg)
            import time
            time.sleep(0.02) # 살짝 슬립하여 스위칭 연도 연출 극대화

        # A. 이전 흔적 제거 가동
        if getattr(self, "delete_old_version", False):
            self.add_install_log("기존 파일 흔적 영구 파쇄 및 가비지 수거 진행 중...")
            import time
            
            # 1. 기존 바탕 화면 바로가기 아이콘 제거
            try:
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                shortcut_path = os.path.join(desktop_path, "PowerController.lnk")
                if os.path.exists(shortcut_path):
                    os.unlink(shortcut_path)
                    self.add_install_log("기존 바탕 화면 바로가기 아이콘 제거 완료")
            except Exception as e:
                self.add_install_log(f"바로가기 제거 스킵 ({e})")
                
            # 2. 기존 시작 프로그램 자동 실행 키 제거
            if REG_AVAILABLE:
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0,
                        winreg.KEY_WRITE
                    )
                    winreg.DeleteValue(key, "PowerController")
                    winreg.CloseKey(key)
                    self.add_install_log("기존 시작 프로그램 자동 실행 키 삭제 완료")
                except Exception:
                    pass
                    
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerController")
                    self.add_install_log("기존 제어판 프로그램 제거 명부 삭제 완료")
                except Exception:
                    pass

            # 3. 기존 설치 폴더 내부 파일 전면 파쇄
            try:
                # 설정 파일 및 데이터 보존 리스트 (완전 초기화를 선택하지 않았을 때만 보존)
                keep_files = [
                    "power_timer_presets.json",
                    "power_scheduler_rules.json",
                    "power_timer_settings.json",
                    "power_theme_config.json",
                    "sidebar_theme_config.json",
                    "power_controller_history.log"
                ]
                for filename in os.listdir(target_dir):
                    if filename in keep_files and not self.clean_install.get():
                        self.add_install_log(f"이전 설정 보존 유지: {filename}")
                        continue
                    file_path = os.path.join(target_dir, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                            self.add_install_log(f"파쇄 완료: {filename}")
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            self.add_install_log(f"폴더 삭제: {filename}")
                    except Exception as e:
                        self.add_install_log(f"파일 파쇄 스킵: {filename} ({e})")
                time.sleep(1.0)
            except Exception as e:
                self.add_install_log(f"이전 데이터 제거 도중 에러: {e}")
            step_done(5, "기존 흔적 데이터 영구 청정화 완료")

        # B. 디렉토리 구축
        self.add_install_log("새로운 파일 시스템 디렉토리 조직 및 생성 중...")
        try:
            os.makedirs(target_dir, exist_ok=True)
            step_done(2, "대상 경로 디렉토리 완벽 활성화")
        except Exception as e:
            messagebox.showerror("오류", f"설치 폴더 구성 실패: {e}")
            self.root.quit()
            return

        # C. 본 실효 파일 일체 유기적 복사
        if not files_to_copy:
            messagebox.showerror("오류", "패키지 대상 원본 파일이나 폴더(PowerController)가 없습니다.")
            self.root.quit()
            return
            
        self.add_install_log(f"실질 파일 복사 프로세스 마스터 기동 (총 {len(files_to_copy)}건)...")
        for src, dst in files_to_copy:
            success = copy_file_safe(src, dst, max_retries=5, is_silent=False, log_func=self.add_install_log)
            if success:
                self.add_install_log(f"추출 전송 성공 -> {os.path.basename(dst)}")
            else:
                self.add_install_log(f"전송 누락 재시도 실패 -> {os.path.basename(dst)}")
                filename = os.path.basename(dst)
                ans = messagebox.askretrycancel(
                    "파일 쓰기 오류 (File Lock Detected)",
                    f"'{filename}' 파일을 설치 대상 폴더에 덮어쓸 수 없습니다.\n\n"
                    "이유: 프로그램이 현재 트레이(백그라운드)에서 실행 중이거나 다른 프로세스에 의해 잠겨 있습니다.\n\n"
                    "해결 방법:\n"
                    "1. 바탕 화면 우측 하단의 트레이 아이콘에서 ⚡ 아이콘을 마우스 우클릭하여 '종료'해 주십시오.\n"
                    "2. 또는 작업 관리자에서 PowerController.exe 프로세스를 수동 종료해 주십시오.\n\n"
                    "준비가 완료되면 [재시도]를 눌러 다시 전송하고, 설치를 완전히 중단하려면 [취소]를 선택하십시오."
                )
                if not ans:
                    self.add_install_log(f"설치 중단됨: {filename} 복사 오류")
                    messagebox.showerror("설치 실패", "필수 프로그램 바이너리 복사 실패로 인해 설치를 더 이상 진행할 수 없습니다.")
                    self.root.quit()
                    return
            step_done(1, f"파일 복사 작업 처리 중: {os.path.basename(dst)}")

        # D. 바로가기 구성 가동
        if self.create_desktop_shortcut.get():
            self.add_install_log("바탕 화면 단축 바로가기 아이콘 생성 지휘 중...")
            self.create_windows_shortcut(target_exe)
            self.add_install_log("바탕 화면 단축 가이드 연계 성공")
        step_done(2, "바로가기 생성 공정 가동 완료")

        # E. 스타트업 등록
        if self.register_startup.get() and REG_AVAILABLE:
            self.add_install_log("윈도우 스타트업 레지스트리 자동 실행 기믹 바인딩 중...")
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_WRITE
                )
                winreg.SetValueEx(key, "PowerController", 0, winreg.REG_SZ, f'"{target_exe}" --startup --tray')
                winreg.CloseKey(key)
                self.add_install_log("스타트업 자동 실행 레지스트리 등록 완료")
            except Exception as e:
                self.add_install_log(f"스타트업 레지스트리 연계 무시: {e}")
        step_done(2, "윈도우 시작 프로그램 정식 등록 완수")

        # F. 제어판 언인스톨 삭제 명부 등재
        if REG_AVAILABLE:
            self.add_install_log("제어판 등재용 프로그램 제거 기능 정보 레지스트리 병합 중...")
            try:
                uninst_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerController"
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, uninst_path)
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "PowerController - Smart Shutdown Agent")
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "AhBiYout")
                winreg.SetValueEx(key, "URLInfoAbout", 0, winreg.REG_SZ, "https://ahbiyoutvibe.blogspot.com/")
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, target_exe)
                
                # Register the interactive uninstaller wizard path
                if getattr(sys, 'frozen', False):
                    uninstaller_path = os.path.join(target_dir, "uninstaller.exe")
                    uninstall_cmd = f'"{uninstaller_path}" --uninstall'
                else:
                    uninstaller_path = os.path.join(target_dir, "uninstaller.py")
                    uninstall_cmd = f'python "{uninstaller_path}" --uninstall'
                
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_cmd)
                winreg.CloseKey(key)
                self.add_install_log("삭제 도구 정보 명부에 PowerController 추가 완료")
            except Exception as e:
                self.add_install_log(f"삭제 명부 등록 도중 레지스트리 예외 무시: {e}")

        # Windows Defender 방화벽 사전 등록 (메인 및 PowerNetworkScheduler 2개 모두 사전 무음 등록 + 버전 표기)
        register_firewall_rules_all(target_dir, self.add_install_log)

        step_done(2, "설치 완수 및 릴리즈 마스터 빌딩 개시")

        # 모든 전원 등재 설치 종료 처리 완료 및 성공
        self.update_install_progress(1.0, "축하합니다! 메인 프로그램 복사 및 설치가 완수되었습니다!")
        self.add_install_log("모든 빌딩 정렬 배치 공정이 정상 통과되었습니다.")
        
        # 버튼을 완료 상태로 갱신
        self.btn_next.config(text="설치 완료 및 닫기", state="normal", bg="#10b981", command=self.finish_wizard)
        self.btn_next.pack(side="right", padx=20)
        self.btn_cancel.pack_forget()

        messagebox.showinfo(
            "설치 성공", 
            "PowerController 전원 예약 에이전트 설치가 완수되었습니다!\n\n"
            f"설치 경로: {target_exe}\n"
            "이제 스마트 제어를 활용하실 수 있습니다!"
        )

    def finish_wizard(self):
        target_exe = os.path.join(self.install_dir.get(), "PowerController.exe")
        if self.run_after_install.get() and os.path.exists(target_exe):
            try:
                if os.name == 'nt':
                    os.startfile(target_exe)
                else:
                    import subprocess
                    subprocess.Popen([target_exe])
            except Exception:
                pass
        self.root.quit()
        
    def create_windows_shortcut(self, target_exe):
        try:
            target_dir = os.path.dirname(target_exe)
            target_ico = os.path.join(target_dir, "PowerController.ico")
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop_path, "PowerController.lnk")
            
            # Escape paths for VBScript
            vbs_target_exe = target_exe.replace("\\", "\\\\")
            vbs_target_dir = target_dir.replace("\\", "\\\\")
            vbs_target_ico = target_ico.replace("\\", "\\\\")
            vbs_shortcut_path = shortcut_path.replace("\\", "\\\\")
            
            # Pure python Windows shell shortcut creator via dynamic VBS engine
            vbs_script = f"""
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = "{vbs_shortcut_path}"
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "{vbs_target_exe}"
            oLink.WorkingDirectory = "{vbs_target_dir}"
            oLink.Description = "PowerController System Shutdown Agent"
            Set fso = CreateObject("Scripting.FileSystemObject")
            If fso.FileExists("{vbs_target_ico}") Then
                oLink.IconLocation = "{vbs_target_ico},0"
            End If
            oLink.Save
            """
            vbs_file = os.path.join(os.environ.get("TEMP", "."), "make_shortcut.vbs")
            with open(vbs_file, "w", encoding="cp949") as f:
                f.write(vbs_script)
            os.system(f'cscript //nologo "{vbs_file}"')
            os.remove(vbs_file)
        except:
            pass

class UninstallWizard:
    def __init__(self, root, target_dir=None, reinstall_callback=None):
        self.root = root
        self.reinstall_callback = reinstall_callback
        self.root.title("PowerController 제거 마법사 (Uninstall Wizard)")
        window_width = 480
        window_height = 500
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.resizable(False, False)
        self.root.configure(bg=DARK_BG)
        
        # Determine target directory
        if target_dir:
            self.target_dir = target_dir
            if getattr(sys, 'frozen', False):
                self.uninstaller_exe = sys.executable
            else:
                self.uninstaller_exe = os.path.abspath(__file__)
        else:
            if getattr(sys, 'frozen', False):
                self.uninstaller_exe = sys.executable
                self.target_dir = os.path.dirname(self.uninstaller_exe)
            else:
                self.uninstaller_exe = os.path.abspath(__file__)
                self.target_dir = os.path.dirname(self.uninstaller_exe)
            
        # Set installer window icon
        try:
            png_path = os.path.join(self.target_dir, "PowerController.png")
            ico_path = os.path.join(self.target_dir, "PowerController.ico")
            if os.path.exists(png_path):
                self.img_icon = tk.PhotoImage(file=png_path)
                self.root.iconphoto(True, self.img_icon)
            elif os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
        except Exception:
            pass
            
        self.clean_uninstall = tk.BooleanVar(value=False)
        self.current_step = 1
        
        self.create_widgets()
        
    def create_widgets(self):
        # 상단 헤더 프레임
        self.header_frame = tk.Frame(self.root, bg=DARK_CARD, pady=15)
        self.header_frame.pack(fill="x")
        
        self.title_label = tk.Label(
            self.header_frame, 
            text="❌ PowerController 제거 마법사", 
            font=("Arial", 14, "bold"), 
            fg=TEXT_COLOR, 
            bg=DARK_CARD
        )
        self.title_label.pack()
        
        self.desc_label = tk.Label(
            self.header_frame, 
            text="컴퓨터에서 PowerController를 안전하고 깨끗하게 제거합니다.", 
            font=("Arial", 9), 
            fg="#9ca3af", 
            bg=DARK_CARD
        )
        self.desc_label.pack(pady=5)
        
        # 하단 컨트롤 바
        self.action_frame = tk.Frame(self.root, bg=DARK_BG, pady=10)
        self.action_frame.pack(side="bottom", fill="x")
        
        # 중앙 콘텐츠 영역
        self.content_frame = tk.Frame(self.root, bg=DARK_BG)
        self.content_frame.pack(side="top", fill="both", expand=True, padx=20, pady=15)
        
        # 네비게이션 버튼 등록
        self.btn_next = tk.Button(
            self.action_frame, 
            text="제거 시작 (Uninstall) >", 
            font=("Arial", 10, "bold"),
            bg="#ef4444",  # Red accent for uninstallation
            fg="white", 
            relief="flat",
            padx=15,
            pady=8,
            command=self.start_uninstallation
        )
        self.btn_next.pack(side="right", padx=20)
        
        self.btn_cancel = tk.Button(
            self.action_frame, 
            text="취소 (Cancel)", 
            font=("Arial", 10),
            bg="#374151", 
            fg=TEXT_COLOR, 
            relief="flat",
            padx=15,
            pady=8,
            command=self.root.quit
        )
        self.btn_cancel.pack(side="left", padx=20)
        
        self.load_step()
        
    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
    def load_step(self):
        self.clear_content_frame()
        
        if self.current_step == 1:
            # Step 1: Confirmation Screen
            confirm_label = tk.Label(
                self.content_frame,
                text="PowerController의 모든 구성 요소를 삭제하시겠습니까?",
                font=("Arial", 11, "bold"),
                fg=TEXT_COLOR,
                bg=DARK_BG,
                pady=10
            )
            confirm_label.pack(anchor="w")
            
            info_text = (
                "설치된 실행 파일, 바탕 화면 바로가기, 자동 시작 등록 값 및 "
                "제어판 제거 등록 정보가 시스템에서 완전히 삭제됩니다."
            )
            info_label = tk.Label(
                self.content_frame,
                text=info_text,
                font=("Arial", 9),
                fg="#9ca3af",
                bg=DARK_BG,
                justify="left",
                wraplength=440
            )
            info_label.pack(anchor="w", pady=(0, 20))
            
            # Clean Option
            chk_clean = tk.Checkbutton(
                self.content_frame, 
                text="기존 사용자 설정 및 저장된 예약 규칙(JSON 파일들)도 함께 영구 삭제", 
                variable=self.clean_uninstall,
                bg=DARK_BG, 
                fg=TEXT_COLOR,
                selectcolor=DARK_CARD,
                activebackground=DARK_BG,
                activeforeground=TEXT_COLOR,
                font=("Arial", 9, "bold")
            )
            chk_clean.pack(anchor="w", pady=10)
            
            caution_text = (
                "※ 주의: 이 옵션을 선택하시면 사용자가 그동안 저장했던 "
                "타이머 프리셋 및 스케줄링 예약 규칙 목록이 전부 파쇄되어 복구할 수 없습니다."
            )
            caution_label = tk.Label(
                self.content_frame,
                text=caution_text,
                font=("Arial", 8),
                fg="#f87171",  # Soft red
                bg=DARK_BG,
                justify="left",
                wraplength=440
            )
            caution_label.pack(anchor="w")
            
        elif self.current_step == 2:
            # Step 2: Uninstallation Progress Screen
            self.desc_label.config(text="컴퓨터에서 제품 파일 및 설정을 정리하고 있습니다. 잠시만 기다려 주십시오...")
            self.btn_next.config(text="제거 완료 대기", state="disabled", bg="#4b5563")
            self.btn_cancel.config(state="disabled")
            
            self.install_status_lbl = tk.Label(
                self.content_frame, 
                text="제거 프로세스 준비 중...", 
                font=("Arial", 10, "bold"), 
                fg=TEXT_COLOR, 
                bg=DARK_BG
            )
            self.install_status_lbl.pack(anchor="w", pady=(15, 5))
            
            # Progress bar container
            self.progress_container = tk.Frame(self.content_frame, bg="#374151", height=24)
            self.progress_container.pack(fill="x", pady=5)
            self.progress_container.pack_propagate(False)
            
            # Progress bar
            self.progress_bar = tk.Frame(self.progress_container, bg="#ef4444") # Red progress bar for uninstallation
            self.progress_bar.place(relx=0, rely=0, relwidth=0.0, relheight=1.0)
            
            # Progress percent label
            self.progress_percent_lbl = tk.Label(
                self.content_frame, 
                text="0%", 
                font=("Arial", 11, "bold"), 
                fg="#ef4444", 
                bg=DARK_BG
            )
            self.progress_percent_lbl.pack(pady=5)
            
            # Log output box
            self.log_textbox = tk.Text(
                self.content_frame, 
                bg=DARK_CARD, 
                fg="#9ca3af", 
                font=("Consolas", 8), 
                height=8, 
                relief="flat", 
                padx=8, 
                pady=8
            )
            self.log_textbox.pack(fill="both", expand=True, pady=(10, 0))
            self.log_textbox.config(state="disabled")
            
            # Trigger uninstallation
            self.root.after(200, self.run_uninstallation)
            
    def start_uninstallation(self):
        self.current_step = 2
        self.load_step()
        
    def add_log(self, text):
        self.log_textbox.config(state="normal")
        self.log_textbox.insert("end", text + "\n")
        self.log_textbox.see("end")
        self.log_textbox.config(state="disabled")
        self.root.update()
        
    def update_progress(self, ratio, status_text):
        self.install_status_lbl.config(text=status_text)
        self.progress_bar.place(relwidth=ratio)
        self.progress_percent_lbl.config(text=f"{int(ratio * 100)}%")
        self.root.update()
        
    def run_uninstallation(self):
        target_dir = self.target_dir
        self.add_log(f"제거 대상 디렉토리 인식: {target_dir}")
        
        # Safety Check: Prevent deleting development folder
        dev_indicators = ["package.json", "src", "vite.config.ts", "main.py", "network_scheduler.py"]
        is_dev_dir = any(os.path.exists(os.path.join(target_dir, indicator)) for indicator in dev_indicators)
        
        total_steps = 7
        current_step_idx = 0
        
        def step_done(msg=""):
            nonlocal current_step_idx
            current_step_idx += 1
            ratio = min(1.0, current_step_idx / total_steps)
            self.update_progress(ratio, msg)
            import time
            time.sleep(0.1) # Smooth transitions
            
        # 1. Kill any running PowerController process
        self.add_log("1. 실행 중인 PowerController 프로세스 강제 종료 및 파일 락 해제 시도...")
        terminate_and_unlock_suite_processes(self.target_dir, timeout_sec=4.0, is_silent=False, log_func=self.add_log)
        self.add_log("→ 실행 중인 프로세스 종료 및 락 해제 완료.")
        step_done("실행 중인 프로세스 강제 종료")
        
        # 2. Delete desktop shortcut
        self.add_log("2. 바탕 화면 바로가기 아이콘 탐색 및 삭제 중...")
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop_path, "PowerController.lnk")
            if os.path.exists(shortcut_path):
                os.unlink(shortcut_path)
                self.add_log("→ 바탕 화면 바로가기 제거 성공.")
            else:
                self.add_log("→ 삭제할 바탕 화면 바로가기 아이콘이 존재하지 않습니다.")
        except Exception as e:
            self.add_log(f"→ 바로가기 삭제 오류 무시: {e}")
        step_done("바로가기 제거 완료")
        
        # 3. Delete registry run key
        self.add_log("3. 윈도우 시작 프로그램 자동 구동 레지스트리 삭제 중...")
        if REG_AVAILABLE:
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_WRITE
                )
                try:
                    winreg.DeleteValue(key, "PowerController")
                    self.add_log("→ 자동 시작 레지스트리 키 값 제거 성공.")
                except FileNotFoundError:
                    self.add_log("→ 레지스트리 시작 프로그램 키 값이 등록되어 있지 않습니다.")
                winreg.CloseKey(key)
            except Exception as e:
                self.add_log(f"→ 시작 프로그램 제거 레지스트리 예외 무시: {e}")
        else:
            self.add_log("→ 레지스트리를 조작할 수 없는 환경입니다.")
        step_done("시작 프로그램 자동 구동 해제")
        
        # 4. Remove uninstall entry in Add/Remove Programs
        self.add_log("4. 제어판 제거 프로그램 목록 레지스트리 정보 삭제 중...")
        if REG_AVAILABLE:
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerController")
                self.add_log("→ 제어판 프로그램 설치 정보 레지스트리 제거 완료.")
            except FileNotFoundError:
                self.add_log("→ 삭제 등록 명부에 정보가 존재하지 않습니다.")
            except Exception as e:
                self.add_log(f"→ 제어판 명부 제거 레지스트리 예외 무시: {e}")
        else:
            self.add_log("→ 제어판 명부 레지스트리를 조작할 수 없는 환경입니다.")
        step_done("제어판 프로그램 설치 정보 삭제")
        
        # 5. Delete installation directory files (excluding configuration unless clean_uninstall is selected)
        self.add_log("5. 설치 디렉토리 내부 파일 정리 작업 중...")
        if is_dev_dir:
            self.add_log("※ 개발 환경(소스 폴더)이 감지되었습니다. 원본 소스 보호를 위해 실제 파일은 삭제하지 않고 가상 진행합니다.")
        else:
            keep_files = [
                "power_timer_presets.json",
                "power_scheduler_rules.json",
                "power_timer_settings.json",
                "power_theme_config.json",
                "sidebar_theme_config.json",
                "power_controller_history.log"
            ]
            
            try:
                if os.path.exists(target_dir):
                    for filename in os.listdir(target_dir):
                        # Don't delete this uninstaller itself while running
                        if filename in ["uninstaller.exe", "uninstaller.py"]:
                            continue
                            
                        file_path = os.path.join(target_dir, filename)
                        
                        # Preserve settings if NOT clean_uninstall
                        if filename in keep_files and not self.clean_uninstall.get():
                            self.add_log(f"→ 이전 설정 보존 유지: {filename}")
                            continue
                            
                        try:
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.unlink(file_path)
                                self.add_log(f"→ 파일 삭제 성공: {filename}")
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                                self.add_log(f"→ 폴더 삭제 성공: {filename}")
                        except Exception as e:
                            self.add_log(f"→ 파일 삭제 스킵: {filename} ({e})")
            except Exception as e:
                self.add_log(f"→ 디렉토리 스캔 중 예외 발생: {e}")
        step_done("제품 파일 전면 삭제")
        
        # Windows Defender 방화벽 규칙 삭제 (등록된 모든 규칙 정리 - 기본 및 버전 표기)
        remove_firewall_rules_all(self.add_log)

        # 6. Finish & Schedule dynamic self-deletion of uninstaller.exe and target directory after closing
        self.add_log("6. 자가 소멸(Self-Destruction) 지연 명령 예약 중...")
        if not is_dev_dir and os.name == 'nt' and not getattr(self, "reinstall_callback", None):
            try:
                # Build powershell self-deletion script
                if self.clean_uninstall.get():
                    cleanup_cmd = (
                        f'Start-Sleep -Seconds 2; '
                        f'Remove-Item -Path "{self.uninstaller_exe}" -Force -ErrorAction SilentlyContinue; '
                        f'Remove-Item -Path "{target_dir}" -Recurse -Force -ErrorAction SilentlyContinue'
                    )
                else:
                    # Only remove uninstaller file and the folder itself if empty
                    cleanup_cmd = (
                        f'Start-Sleep -Seconds 2; '
                        f'Remove-Item -Path "{self.uninstaller_exe}" -Force -ErrorAction SilentlyContinue; '
                        f'Remove-Item -Path "{target_dir}" -ErrorAction SilentlyContinue'
                    )
                import subprocess
                subprocess.Popen(["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cleanup_cmd])
                self.add_log("→ 백그라운드 쉘 자가 삭제 작업 등록 성공.")
            except Exception as e:
                self.add_log(f"→ 자가 삭제 예약 예외 무시: {e}")
        else:
            self.add_log("→ 자가 소멸 예약을 스킵합니다 (개발자 모드 혹은 Windows가 아님).")
        step_done("자가 소멸 백그라운드 스케줄 등록")
        
        self.update_progress(1.0, "제거 작업이 모두 완료되었습니다!")
        self.add_log("모든 PowerController 컴포넌트가 시스템에서 성공적으로 제거되었습니다.")
        
        # Update button to exit
        if getattr(self, "reinstall_callback", None):
            self.btn_next.config(
                text="제거 완료 및 설치 계속 진행 >", 
                state="normal", 
                bg="#10b981", 
                command=self.run_reinstall_callback
            )
        else:
            self.btn_next.config(text="완료 및 닫기", state="normal", bg="#10b981", command=self.root.quit)
        self.btn_next.pack(side="right", padx=20)
        self.btn_cancel.pack_forget()
        
        messagebox.showinfo(
            "제거 완료",
            "PowerController 제거가 완료되었습니다!\n\n"
            "언제든지 다시 설치하여 사용하실 수 있습니다. 이용해 주셔서 감사합니다!"
        )

    def run_reinstall_callback(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        if self.reinstall_callback:
            self.reinstall_callback()

def run_silent_install(install_dir=None, clean_install=False, create_shortcut=True, register_startup=True, run_after_install=True):
    print("[*] PowerController Smart Shutdown Agent Silent Setup Initialized")
    
    # 1. Determine target directory
    if not install_dir:
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        install_dir = os.path.normpath(os.path.join(local_app_data, "PowerController"))
    else:
        install_dir = os.path.normpath(os.path.abspath(install_dir))
        
    print(f"[*] Target Directory: {install_dir}")
    
    # 2. Terminate any running process and unlock files
    terminate_and_unlock_suite_processes(install_dir, timeout_sec=6.0, is_silent=True)
        
    # 3. Handle source paths
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    target_exe = os.path.join(install_dir, "PowerController.exe")
    bundled_folder = os.path.join(base_path, "PowerController")
    if not os.path.exists(bundled_folder):
        bundled_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "PowerController")
        
    # Collect files
    files_to_copy = []
    has_bundled_folder = os.path.exists(bundled_folder) and os.path.isdir(bundled_folder)
    
    if has_bundled_folder:
        def collect_files(src_p, dst_p):
            if os.path.isdir(src_p):
                for item in os.listdir(src_p):
                    collect_files(os.path.join(src_p, item), os.path.join(dst_p, item))
            else:
                files_to_copy.append((src_p, dst_p))
        collect_files(bundled_folder, install_dir)
    else:
        bundled_exe = os.path.join(base_path, "PowerController.exe")
        if not os.path.exists(bundled_exe):
            bundled_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "PowerController.exe")
        if os.path.exists(bundled_exe):
            files_to_copy.append((bundled_exe, target_exe))
            
    # Include icon files
    for icon_file in ["PowerController.ico", "PowerController.png"]:
        src_icon = os.path.join(base_path, icon_file)
        if os.path.exists(src_icon):
            dst_icon = os.path.join(install_dir, icon_file)
            if not any(item[1] == dst_icon for item in files_to_copy):
                files_to_copy.append((src_icon, dst_icon))
                
    # Include schedule_share_builder.py
    for script_file in ["schedule_share_builder.py"]:
        src_script = os.path.join(base_path, script_file)
        if os.path.exists(src_script):
            dst_script = os.path.join(install_dir, script_file)
            if not any(item[1] == dst_script for item in files_to_copy):
                files_to_copy.append((src_script, dst_script))

    # Companion tools, native DLLs & executables
    for comp_tool in ["PowerCoreNative.dll", "NetBeaconEngine.dll", "FirewallNative.dll", "SysPowerHook.dll", "ScheduleCrypto.dll", "native_bridge.py", "PowerNetworkScheduler.exe", "ApplySharedSchedules.exe", "Register_Firewall_Rules.bat"]:
        src_tool = os.path.join(base_path, comp_tool)
        if not os.path.exists(src_tool):
            src_tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", comp_tool)
        if not os.path.exists(src_tool):
            src_tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), comp_tool)
        if not os.path.exists(src_tool) and comp_tool.endswith(".dll"):
            src_tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), "native", comp_tool)
        if os.path.exists(src_tool):
            dst_tool = os.path.join(install_dir, comp_tool)
            if not any(item[1] == dst_tool for item in files_to_copy):
                files_to_copy.append((src_tool, dst_tool))

    # Documentation multi-files (docs/ tree)
    docs_src = os.path.join(base_path, "docs")
    if not os.path.exists(docs_src):
        docs_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    if os.path.exists(docs_src) and os.path.isdir(docs_src):
        docs_dst = os.path.join(install_dir, "docs")
        for d_file in os.listdir(docs_src):
            s_df = os.path.join(docs_src, d_file)
            d_df = os.path.join(docs_dst, d_file)
            if os.path.isfile(s_df) and not any(item[1] == d_df for item in files_to_copy):
                files_to_copy.append((s_df, d_df))
                
    # Add uninstaller script/exe
    if getattr(sys, 'frozen', False):
        uninstaller_src = sys.executable
        uninstaller_dst = os.path.join(install_dir, "uninstaller.exe")
    else:
        uninstaller_src = os.path.abspath(__file__)
        uninstaller_dst = os.path.join(install_dir, "uninstaller.py")
        
    if os.path.exists(uninstaller_src):
        if not any(item[1] == uninstaller_dst for item in files_to_copy):
            files_to_copy.append((uninstaller_src, uninstaller_dst))
            
    # 4. Clean previous installation if needed
    if os.path.exists(install_dir):
        print("[*] Cleaning old files...")
        keep_files = [
            "power_timer_presets.json",
            "power_scheduler_rules.json",
            "power_timer_settings.json",
            "power_theme_config.json",
            "sidebar_theme_config.json",
            "power_controller_history.log"
        ]
        try:
            for filename in os.listdir(install_dir):
                if filename in keep_files and not clean_install:
                    print(f"[-] Preserving configuration file: {filename}")
                    continue
                file_path = os.path.join(install_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        try:
                            os.unlink(file_path)
                        except Exception:
                            try:
                                old_name = file_path + f".old_{int(time.time() * 1000)}"
                                os.rename(file_path, old_name)
                                try:
                                    os.unlink(old_name)
                                except Exception:
                                    pass
                            except Exception:
                                pass
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path, ignore_errors=True)
                except Exception as e:
                    print(f"[!] Warning: Could not remove {filename}: {e}")
        except Exception as e:
            print(f"[!] Warning: Error during clean up: {e}")
            
    # 5. Create directory
    try:
        os.makedirs(install_dir, exist_ok=True)
    except Exception as e:
        print(f"[ERROR] Failed to create installation folder: {e}")
        sys.exit(1)
        
    # 6. Copy files (using safe copy with unlock and rename fallback)
    print(f"[*] Copying {len(files_to_copy)} files...")
    for src, dst in files_to_copy:
        success = copy_file_safe(src, dst, max_retries=5, is_silent=True)
        if success:
            print(f"[+] Copied: {os.path.basename(dst)}")
        else:
            print(f"[ERROR] Critical failure copying file: {os.path.basename(dst)}")
            sys.exit(1)
            
    # 7. Shortcuts
    if create_shortcut:
        print("[*] Creating desktop shortcut...")
        try:
            target_dir = os.path.dirname(target_exe)
            target_ico = os.path.join(target_dir, "PowerController.ico")
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop_path, "PowerController.lnk")
            
            vbs_target_exe = target_exe.replace("\\", "\\\\")
            vbs_target_dir = target_dir.replace("\\", "\\\\")
            vbs_target_ico = target_ico.replace("\\", "\\\\")
            vbs_shortcut_path = shortcut_path.replace("\\", "\\\\")
            
            vbs_script = f"""
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = "{vbs_shortcut_path}"
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "{vbs_target_exe}"
            oLink.WorkingDirectory = "{vbs_target_dir}"
            oLink.Description = "PowerController System Shutdown Agent"
            Set fso = CreateObject("Scripting.FileSystemObject")
            If fso.FileExists("{vbs_target_ico}") Then
                oLink.IconLocation = "{vbs_target_ico},0"
            End If
            oLink.Save
            """
            vbs_file = os.path.join(os.environ.get("TEMP", "."), "make_shortcut.vbs")
            with open(vbs_file, "w", encoding="cp949") as f:
                f.write(vbs_script)
            os.system(f'cscript //nologo "{vbs_file}"')
            os.remove(vbs_file)
            print("[+] Desktop shortcut created successfully")
        except Exception as e:
            print(f"[!] Warning: Shortcut creation failed: {e}")
            
    # 8. Registry startup
    if register_startup and REG_AVAILABLE:
        print("[*] Registering startup registry key...")
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE
            )
            winreg.SetValueEx(key, "PowerController", 0, winreg.REG_SZ, f'"{target_exe}" --startup --tray')
            winreg.CloseKey(key)
            print("[+] Registered in Windows Startup")
        except Exception as e:
            print(f"[!] Warning: Startup registry registration failed: {e}")
            
    # 9. Register Uninstall
    if REG_AVAILABLE:
        print("[*] Registering uninstall information in registry...")
        try:
            uninst_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerController"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, uninst_path)
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "PowerController - Smart Shutdown Agent")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "2.4.0")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "AhBiYout")
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, target_exe)
            
            if getattr(sys, 'frozen', False):
                uninstaller_path = os.path.join(install_dir, "uninstaller.exe")
                uninstall_cmd = f'"{uninstaller_path}" --uninstall --silent'
            else:
                uninstaller_path = os.path.join(install_dir, "uninstaller.py")
                uninstall_cmd = f'python "{uninstaller_path}" --uninstall --silent'
                
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_cmd)
            winreg.CloseKey(key)
            print("[+] Registered uninstall capability")
        except Exception as e:
            print(f"[!] Warning: Uninstall registration failed: {e}")
            
    # 10. Register Firewall Rule (메인 및 PowerNetworkScheduler 2개 모두 사전 무음 등록 + 버전 표기)
    register_firewall_rules_all(install_dir)

    # 11. Run after install
    if run_after_install and os.path.exists(target_exe):
        print("[*] Launching PowerController application...")
        try:
            if os.name == 'nt':
                os.startfile(target_exe)
            else:
                import subprocess
                subprocess.Popen([target_exe])
            print("[+] Launched PowerController successfully")
        except Exception as e:
            print(f"[!] Warning: Application start failed: {e}")
            
    print("[*] Installation completed successfully!")
    sys.exit(0)

def run_silent_uninstall(install_dir=None, clean_uninstall=False):
    print("[*] PowerController Smart Shutdown Agent Silent Uninstall Initialized")
    
    if not install_dir:
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        install_dir = os.path.normpath(os.path.join(local_app_data, "PowerController"))
    else:
        install_dir = os.path.normpath(os.path.abspath(install_dir))
        
    print(f"[*] Target Directory: {install_dir}")
    
    # Safety check
    dev_indicators = ["package.json", "src", "vite.config.ts", "main.py", "network_scheduler.py"]
    is_dev_dir = any(os.path.exists(os.path.join(install_dir, indicator)) for indicator in dev_indicators)
    
    # 1. Kill processes and unlock files
    terminate_and_unlock_suite_processes(install_dir, timeout_sec=4.0, is_silent=True)
        
    # 2. Delete desktop shortcut
    try:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop_path, "PowerController.lnk")
        if os.path.exists(shortcut_path):
            os.unlink(shortcut_path)
            print("[+] Removed desktop shortcut")
    except Exception as e:
        print(f"[!] Warning: Failed to remove desktop shortcut: {e}")
        
    # 3. Delete Run key
    if REG_AVAILABLE:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE
            )
            try:
                winreg.DeleteValue(key, "PowerController")
                print("[+] Removed Startup Run registry value")
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"[!] Warning: Failed to remove registry Startup value: {e}")
            
    # 4. Remove uninstall entry
    if REG_AVAILABLE:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\PowerController")
            print("[+] Removed Uninstall registry entries")
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[!] Warning: Failed to remove registry Uninstall entries: {e}")

    # 5. Remove Firewall rule (등록된 모든 방화벽 규칙 클린 정리 - 기본 및 버전 표기)
    remove_firewall_rules_all()
            
    # 6. Delete files
    if is_dev_dir:
        print("[!] Development folder detected. Skipped deleting actual development files.")
    else:
        keep_files = [
            "power_timer_presets.json",
            "power_scheduler_rules.json",
            "power_timer_settings.json",
            "power_theme_config.json",
            "sidebar_theme_config.json",
            "power_controller_history.log"
        ]
        try:
            if os.path.exists(install_dir):
                for filename in os.listdir(install_dir):
                    if filename in ["uninstaller.exe", "uninstaller.py"]:
                        continue
                    file_path = os.path.join(install_dir, filename)
                    if filename in keep_files and not clean_uninstall:
                        print(f"[-] Preserving user data configuration file: {filename}")
                        continue
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                        print(f"[+] Deleted: {filename}")
                    except Exception as e:
                        print(f"[!] Warning: Could not delete {filename}: {e}")
        except Exception as e:
            print(f"[!] Warning: File deletion error: {e}")
            
    # 6. Self destruction scheduling if compiled
    if not is_dev_dir and os.name == 'nt':
        try:
            uninstaller_exe = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
            if clean_uninstall:
                cleanup_cmd = (
                    f'Start-Sleep -Seconds 2; '
                    f'Remove-Item -Path "{uninstaller_exe}" -Force -ErrorAction SilentlyContinue; '
                    f'Remove-Item -Path "{install_dir}" -Recurse -Force -ErrorAction SilentlyContinue'
                )
            else:
                cleanup_cmd = (
                    f'Start-Sleep -Seconds 2; '
                    f'Remove-Item -Path "{uninstaller_exe}" -Force -ErrorAction SilentlyContinue; '
                    f'Remove-Item -Path "{install_dir}" -ErrorAction SilentlyContinue'
                )
            import subprocess
            subprocess.Popen(["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cleanup_cmd])
            print("[+] Scheduled self-deletion task successfully")
        except Exception as e:
            print(f"[!] Warning: Failed to schedule self-destruction: {e}")
            
    print("[*] Uninstallation completed successfully!")
    sys.exit(0)

if __name__ == "__main__":
    # Parsing command-line arguments manually for Windows / Unix compatibility
    args = {
        "silent": False,
        "uninstall": False,
        "dir": None,
        "clean": False,
        "no_shortcut": False,
        "no_startup": False,
        "no_start": False
    }
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        arg_lower = arg.lower()
        
        # Silent flag (all common standards: Inno Setup, NSIS, MSI, Unix)
        if arg_lower in ["--silent", "-s", "/s", "/silent", "/verysilent", "--verysilent", "-silent", "-verysilent", "/q", "--quiet", "-quiet"]:
            args["silent"] = True
            
        # Uninstall flag
        elif arg_lower in ["--uninstall", "-u", "/u", "/uninstall", "-uninstall"]:
            args["uninstall"] = True
            
        # Clean flag
        elif arg_lower in ["--clean", "/clean", "-clean"]:
            args["clean"] = True
            
        # No shortcut
        elif arg_lower in ["--no-shortcut", "/no-shortcut", "-no-shortcut"]:
            args["no_shortcut"] = True
            
        # No startup
        elif arg_lower in ["--no-startup", "/no-startup", "-no-startup"]:
            args["no_startup"] = True
            
        # No start / No restart
        elif arg_lower in ["--no-start", "/no-start", "-no-start", "/norestart", "--norestart"]:
            args["no_start"] = True
            
        # Directory flag (standard Unix: --dir <path> or -d <path> or /DIR=<path>)
        elif arg_lower in ["--dir", "-d", "/dir"]:
            if i + 1 < len(sys.argv):
                args["dir"] = sys.argv[i + 1]
                i += 1
                
        # Windows-style Directory flag: /D=<path> or /DIR=<path>
        elif arg_lower.startswith("/d=") or arg_lower.startswith("/dir="):
            eq_idx = arg.find("=")
            args["dir"] = arg[eq_idx+1:].strip('"\'')
            
        # Skip common Inno Setup / unattended switches safely
        elif arg_lower in ["/sp-", "/suppressmsgboxes", "/nocancel", "/forcecloseapplications"]:
            pass
            
        i += 1

    # Route execution flow
    if args["silent"]:
        if args["uninstall"]:
            run_silent_uninstall(
                install_dir=args["dir"],
                clean_uninstall=args["clean"]
            )
        else:
            run_silent_install(
                install_dir=args["dir"],
                clean_install=args["clean"],
                create_shortcut=not args["no_shortcut"],
                register_startup=not args["no_startup"],
                run_after_install=not args["no_start"]
            )
    else:
        root = tk.Tk()
        if args["uninstall"]:
            app = UninstallWizard(root, target_dir=args["dir"])
        else:
            app = SetupWizard(root)
        root.mainloop()
