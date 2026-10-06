# -*- coding: utf-8 -*-
"""
PowerController v2.0-python: Schedule Share & Injector Builder
이 유틸리티는 현재 컴퓨터에 설정된 'power_scheduler_rules.json' 파일을 읽어와,
다른 컴퓨터에서 실행하기만 하면 자동으로 PowerController 설치 경로를 추적하여 스케줄 데이터를 안전하게 덮어씌우는
독립형 원클릭 스케줄 동기화 실행 파일(ApplySharedSchedules.exe)을 자동 컴파일/생성해 줍니다.
"""

import os
import sys
import json
import shutil
import subprocess

# 색상 및 스타일 정의 (터미널용)
COLOR_SUCCESS = "\033[92m"
COLOR_INFO = "\033[94m"
COLOR_WARNING = "\033[93m"
COLOR_ERROR = "\033[91m"
COLOR_RESET = "\033[0m"

try:
    import native_bridge
    NATIVE_BRIDGE_AVAILABLE = True
except ImportError:
    NATIVE_BRIDGE_AVAILABLE = False


def print_styled(text, style_color):
    if os.name == 'nt':
        # Windows CMD/PowerShell ANSI 지원 여부에 따른 처리
        print(text)
    else:
        print(f"{style_color}{text}{COLOR_RESET}")


def generate_injector_source(rules_data_str):
    """
    다른 PC에서 작동할 스케줄 주입기 소스코드를 생성합니다.
    순수 창작 ScheduleCrypto 디지털 서명과 무결성 해시를 함께 패키징합니다.
    """
    # 디지털 서명 및 해시 계산
    if NATIVE_BRIDGE_AVAILABLE:
        sig_hex = native_bridge.generate_schedule_hmac(rules_data_str)
        sha_hex = native_bridge.compute_sha256(rules_data_str)
    else:
        import hashlib, hmac
        key = "PowerController_v2.9.1_Enterprise_SecKey_2026"
        sig_hex = hmac.new(key.encode('utf-8'), rules_data_str.encode('utf-8'), hashlib.sha256).hexdigest()
        sha_hex = hashlib.sha256(rules_data_str.encode('utf-8')).hexdigest()

    source_code = f"""# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import shutil
import subprocess
import hashlib
import hmac
try:
    import winreg
    REG_AVAILABLE = True
except ImportError:
    REG_AVAILABLE = False

try:
    import native_bridge
    NATIVE_AVAILABLE = True
except ImportError:
    NATIVE_AVAILABLE = False

# 주입할 스케줄 데이터 및 보안 서명이 내장되어 있습니다.
EMBEDDED_RULES = {repr(rules_data_str)}
EMBEDDED_SIG = {repr(sig_hex)}
EMBEDDED_SHA = {repr(sha_hex)}
MASTER_KEY = "PowerController_v2.9.1_Enterprise_SecKey_2026"

def verify_embedded_integrity():
    \"\"\"스케줄 데이터의 변조 여부를 디지털 서명(HMAC-SHA256)으로 검증합니다.\"\"\"
    if NATIVE_AVAILABLE and native_bridge.is_crypto_engine_loaded():
        return native_bridge.verify_schedule_signature(EMBEDDED_RULES, EMBEDDED_SIG, MASTER_KEY)
    
    computed_sig = hmac.new(MASTER_KEY.encode('utf-8'), EMBEDDED_RULES.encode('utf-8'), hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed_sig.lower(), EMBEDDED_SIG.lower())

def find_power_controller_dir():
    \"\"\"제어판 레지스트리를 추적하여 PowerController의 실제 설치 디렉토리를 탐색합니다.\"\"\"
    possible_paths = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "PowerController"),
        os.path.join(os.environ.get("ProgramFiles", ""), "PowerController"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "PowerController")
    ]
    
    if REG_AVAILABLE:
        try:
            uninst_key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\PowerController"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, uninst_key_path, 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, "UninstallString")
            winreg.CloseKey(key)
            
            cleaned_val = val.replace('"', '').strip()
            if cleaned_val.lower().endswith("uninstaller.exe --uninstall"):
                dir_path = cleaned_val[:-len("uninstaller.exe --uninstall")].strip().rstrip("\\\\/")
                if os.path.exists(dir_path):
                    return dir_path
            elif cleaned_val.lower().endswith("uninstaller.py --uninstall"):
                dir_path = cleaned_val[:-len("uninstaller.py --uninstall")].strip().rstrip("\\\\/")
                if os.path.exists(dir_path):
                    return dir_path
        except Exception:
            pass
            
    for path in possible_paths:
        if os.path.exists(path) and os.path.exists(os.path.join(path, "PowerController.exe")):
            return path
            
    return None

def inject_schedule():
    print("==================================================")
    print("      PowerController 스케줄 강제 주입/복사 도구      ")
    print("==================================================")
    print("[보안] ScheduleCrypto 디지털 서명 및 무결성 검증 중...")
    
    if not verify_embedded_integrity():
        print("[경고] ❌ 스케줄 데이터 변조 또는 위조가 감지되었습니다!")
        print("안전을 위해 주입 작업을 즉시 중단합니다.")
        input("\\n엔터키를 누르면 종료됩니다...")
        sys.exit(1)
        
    print("[보안] ✅ 무결성 검증 완료 (SHA-256 서명 일치)")
    print("[정보] 배포 패키지에 내장된 스케줄 규칙을 감지하는 중...")
    
    try:
        rules = json.loads(EMBEDDED_RULES)
        print(f"[검증] 정상적인 JSON 데이터 형식 확인 완료. (스케줄 개수: {{len(rules)}}개)")
    except Exception as e:
        print(f"[오류] 데이터 파싱 실패: {{e}}")
        input("\\n엔터키를 누르면 종료됩니다...")
        sys.exit(1)
        
    print("[탐색] 이 컴퓨터에 설치된 PowerController 설치 경로를 조회하는 중...")
    target_dir = find_power_controller_dir()
    
    if not target_dir:
        print("[경고] 시스템에서 활성화된 PowerController 설치 환경을 찾지 못했습니다.")
        print("PowerController가 올바르게 설치되어 있는지 확인하거나, 기본 경로에 디렉토리를 생성합니다.")
        # Fallback to local appdata directory
        target_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "PowerController")
        try:
            os.makedirs(target_dir, exist_ok=True)
            print(f"[우회] 사용자 로컬 앱데이터 강제 설정 경로: {{target_dir}}")
        except Exception as e:
            print(f"[오류] 경로 자동 생성 실패: {{e}}")
            input("\\n엔터키를 누르면 종료됩니다...")
            sys.exit(1)
            
    rule_file_path = os.path.join(target_dir, "power_scheduler_rules.json")
    print(f"[대상] 타겟 파일 주소: {{rule_file_path}}")
    
    # 1. 프로세스 종료 시도
    print("[제어] 안전한 덮어쓰기를 위해 실행 중인 PowerController를 종료합니다...")
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        s.connect(("127.0.0.1", 59384))
        s.sendall(b"QUIT")
        s.close()
    except Exception:
        pass
    try:
        os.system("taskkill /f /t /im PowerController.exe >nul 2>&1")
        time.sleep(1)
    except Exception:
        pass
        
    # 2. 백업 생성 (기존 규칙 백업)
    if os.path.exists(rule_file_path):
        backup_path = rule_file_path + ".bak"
        try:
            shutil.copy2(rule_file_path, backup_path)
            print(f"[백업] 기존 스케줄 데이터를 {{backup_path}} 주소로 긴급 백업해두었습니다.")
        except Exception as e:
            print(f"[알림] 백업 건너뜀 (예외: {{e}})")
            
    # 3. 덮어쓰기 실행
    try:
        with open(rule_file_path, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
        print("[성공] 내장된 신규 스케줄 데이터가 완벽하게 복사(덮어씌우기)되었습니다!")
    except Exception as e:
        print(f"[오류] 스케줄 덮어쓰기 실패: {{e}}")
        input("\\n엔터키를 누르면 종료됩니다...")
        sys.exit(1)
        
    # 4. 재부팅 명령 전달
    print("[실행] 스케줄 동기화가 성사되었습니다. 변경 사항을 반영하기 위해")
    print("PowerController 앱을 다시 기동합니다...")
    exe_path = os.path.join(target_dir, "PowerController.exe")
    if os.path.exists(exe_path):
        try:
            subprocess.Popen([exe_path])
            print("[성공] PowerController가 성공적으로 재부팅되었습니다.")
        except Exception as e:
            print(f"[알림] 프로그램 자동 재시작 스킵 (예외: {{e}})")
    else:
        print("[알림] 독립형 실행파일(PowerController.exe)을 찾을 수 없어 프로그램 기동은 수동으로 진행해 주세요.")
        
    print("\\n==================================================")
    print("          스케줄 동기화 주입 작업이 무사히 성사되었습니다!          ")
    print("==================================================")
    for i in range(15, 0, -1):
        print(f"\\r[안내] {{i}}초 후에 프로그램이 자동으로 종료됩니다...", end="", flush=True)
        time.sleep(1)
    print("\\n")

if __name__ == "__main__":
    inject_schedule()
"""
    return source_code

def build_share_injector():
    print_styled("==================================================", COLOR_INFO)
    print_styled("    PowerController 스케줄 공유 배포기 (.exe) 빌드 도구    ", COLOR_INFO)
    print_styled("==================================================", COLOR_INFO)
    
    # 1. 스케줄 파일 경로 추적
    # 개발 폴더 또는 설치 폴더에서 탐색
    possible_rules_paths = [
        "power_scheduler_rules.json",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "PowerController", "power_scheduler_rules.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "power_scheduler_rules.json")
    ]
    
    rules_file_path = None
    for p in possible_rules_paths:
        if os.path.exists(p):
            rules_file_path = p
            break
            
    if not rules_file_path:
        print_styled("[오류] 복사 대상이 될 'power_scheduler_rules.json' 파일을 찾지 못했습니다.", COLOR_ERROR)
        print_styled("스케줄러 탭에서 스케줄을 최소 1개 이상 추가/저장한 뒤 빌드해 주십시오.", COLOR_WARNING)
        sys.exit(1)
        
    print_styled(f"[인식] 복사할 마스터 스케줄 소스: {rules_file_path}", COLOR_SUCCESS)
    
    # 2. JSON 내용 읽기
    try:
        with open(rules_file_path, "r", encoding="utf-8") as f:
            rules_data = json.load(f)
        rules_str = json.dumps(rules_data, ensure_ascii=False)
        print_styled(f"[분석] 데이터 무결성 검증 통과 (포함된 예약 규칙 개수: {len(rules_data)}개)", COLOR_SUCCESS)
    except Exception as e:
        print_styled(f"[오류] 데이터 로딩 실패: {e}", COLOR_ERROR)
        sys.exit(1)
        
    # 3. 주입기 임시 소스코드 생성
    temp_py_name = "ApplySharedSchedules.py"
    try:
        with open(temp_py_name, "w", encoding="utf-8") as f:
            f.write(generate_injector_source(rules_str))
        print_styled(f"[생성] 임시 주입기 파이썬 코드 생성 성공 -> {temp_py_name}", COLOR_SUCCESS)
    except Exception as e:
        print_styled(f"[오류] 주입 소스코드 파일 작성 실패: {e}", COLOR_ERROR)
        sys.exit(1)
        
    # 4. PyInstaller 컴파일 작동
    print_styled("[컴파일] PyInstaller를 사용해 단일 파일 무설치 실행파일(.exe)로 빌드하는 중...", COLOR_INFO)
    print_styled("※ 이 과정은 PyInstaller 라이브러리가 설치되어 있어야 합니다. (pip install pyinstaller)", COLOR_WARNING)
    
    # PyInstaller 확인
    try:
        import PyInstaller
    except ImportError:
        print_styled("[경고] PyInstaller가 설치되어 있지 않습니다. pip를 통해 자동 획득을 시도합니다...", COLOR_WARNING)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        except Exception as e:
            print_styled(f"[오류] PyInstaller 설치 실패: {e}. 수동으로 'pip install pyinstaller'를 구동해 주십시오.", COLOR_ERROR)
            # 임시 파일 유지 후 종료
            sys.exit(1)
            
    # My Documents (내 문서) 경로 획득 및 디렉토리 생성 보장
    my_documents = ""
    if os.name == 'nt':
        try:
            import winreg
            sub_key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                my_documents = winreg.QueryValueEx(key, "Personal")[0]
        except Exception:
            pass
    if not my_documents:
        my_documents = os.path.join(os.path.expanduser("~"), "Documents")
        
    try:
        os.makedirs(my_documents, exist_ok=True)
    except Exception:
        my_documents = os.path.dirname(os.path.abspath(__file__))

    # icon 파일 및 version 파일이 존재하면 포함
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(base_dir, "PowerController.ico") if os.path.exists(os.path.join(base_dir, "PowerController.ico")) else "PowerController.ico"
    ver_path = os.path.join(base_dir, "version_share.txt") if os.path.exists(os.path.join(base_dir, "version_share.txt")) else "version_share.txt"
    build_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name=ApplySharedSchedules",
        "--distpath", my_documents,
    ]
    if os.path.exists(ico_path):
        build_cmd.append(f"--icon={ico_path}")
    if os.path.exists(ver_path):
        build_cmd.append(f"--version-file={ver_path}")
    build_cmd.append(temp_py_name)
    
    # 컴파일 진행
    try:
        print_styled(f"[명령] {' '.join(build_cmd)}", COLOR_INFO)
        result = subprocess.run(build_cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        
        if result.returncode == 0:
            print_styled("\n==================================================", COLOR_SUCCESS)
            print_styled("🎉 단일 실행형 스케줄 공유 배포기 빌드가 성사되었습니다!", COLOR_SUCCESS)
            print_styled("==================================================", COLOR_SUCCESS)
            print_styled(f"생성된 파일 주소: {os.path.join(my_documents, 'ApplySharedSchedules.exe')}", COLOR_SUCCESS)
            print_styled("\n[사용 설명서]", COLOR_INFO)
            print_styled(f"1. '{os.path.join(my_documents, 'ApplySharedSchedules.exe')}' 파일을 USB, 메일, 메신저 등으로 다른 컴퓨터에 배포합니다.", COLOR_INFO)
            print_styled("2. 대상 컴퓨터에서 이 파일만 더블 클릭하여 실행하면:", COLOR_INFO)
            print_styled("   - 설치된 PowerController가 자동 감지되어 안전하게 셧다운 종료됩니다.", COLOR_INFO)
            print_styled("   - 복사본 스케줄 파일(power_scheduler_rules.json)이 원스톱 자동 덮어쓰기 적용됩니다.", COLOR_INFO)
            print_styled("   - PowerController가 리부팅되어 실시간 백그라운드 예약으로 반영됩니다.", COLOR_INFO)
            print_styled("3. 네트워크 없이도 회사, 피시방, 연구실 전체의 스케줄을 마스터 파일 단 하나로 배포/공유할 수 있습니다.", COLOR_SUCCESS)
            
            # 생성 후 폴더 열기 (Open Folder)
            try:
                if os.name == 'nt':
                    os.startfile(my_documents)
                elif sys.platform == 'darwin':
                    subprocess.Popen(["open", my_documents])
                else:
                    subprocess.Popen(["xdg-open", my_documents])
            except Exception:
                pass
        else:
            print_styled("[오류] 컴파일 빌드에 실패했습니다.", COLOR_ERROR)
            print(result.stderr)
    except Exception as e:
        print_styled(f"[오류] 빌드 도중 치명적 예외 발생: {e}", COLOR_ERROR)
    finally:
        # 5. 임시 파일 정리
        try:
            if os.path.exists(temp_py_name):
                os.unlink(temp_py_name)
                print_styled(f"[정리] 임시 템플릿 소스 파일 소거 완료: {temp_py_name}", COLOR_INFO)
        except:
            pass

if __name__ == "__main__":
    build_share_injector()
