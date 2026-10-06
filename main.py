import os
import sys
import json
import datetime
import threading
try:
    import tkinter as tk
    from tkinter import messagebox
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False
    tk = None
    messagebox = None
import socket
import math
import subprocess
import time

try:
    import native_bridge
except ImportError:
    native_bridge = None

# --------------------------------------------------------------------
# 0. 윈도우 시작 시 자동 실행 라이브러리 (registry) 및 트레이 필터링
# --------------------------------------------------------------------
try:
    import winreg
    WINDOWS_REG_AVAILABLE = True
except ImportError:
    WINDOWS_REG_AVAILABLE = False

try:
    import pystray
    from PIL import Image, ImageDraw
    P_TRAY_AVAILABLE = True
except ImportError:
    P_TRAY_AVAILABLE = False

# --------------------------------------------------------------------
# 1. 환경 설정 및 상태 변수 정의 (종료/재시작 컨트롤러)
# --------------------------------------------------------------------
# Absolute script directory to keep files persistent even on startup reboots
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_data_filepath(filename):
    """안전한 설정 저장 경로 반환. Program Files 등 쓰기 권한이 제한된 환경일 경우 %APPDATA%/PowerController로 안전하게 폴백합니다."""
    script_path = os.path.join(SCRIPT_DIR, filename)
    appdata = os.getenv("APPDATA") or os.path.expanduser("~")
    appdata_path = os.path.join(appdata, "PowerController", filename)

    if os.path.exists(appdata_path):
        return appdata_path
    if os.path.exists(script_path):
        try:
            with open(script_path, "a", encoding="utf-8"):
                pass
            return script_path
        except Exception:
            return appdata_path
    try:
        test_path = os.path.join(SCRIPT_DIR, f".perm_test_{os.getpid()}")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test_path)
        return script_path
    except Exception:
        try:
            os.makedirs(os.path.dirname(appdata_path), exist_ok=True)
            return appdata_path
        except Exception:
            return script_path

APP_VERSION = "2.9.1"
GITHUB_REPO_OWNER = "AhBiYout"
GITHUB_REPO_NAME = "PowerController"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases"

def parse_semver(ver_str):
    """v2.9.1 또는 2.9.1 형태의 문자열을 (2, 9, 1) 튜플로 파싱하여 대소 비교합니다."""
    clean = str(ver_str).strip().lstrip("vV")
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def check_github_update(current_version=APP_VERSION, timeout=5):
    """
    GitHub Releases API를 통해 최신 릴리스 정보를 실시간 조회하여 반환합니다.
    Returns: (has_update: bool, latest_ver: str, release_url: str, release_title: str, release_body: str)
    """
    import urllib.request
    req = urllib.request.Request(
        GITHUB_RELEASES_API,
        headers={"User-Agent": f"PowerController-UpdateChecker/{current_version}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                tag_name = data.get("tag_name", "").strip().lstrip("vV")
                html_url = data.get("html_url", GITHUB_RELEASES_URL)
                title = data.get("name", f"v{tag_name}")
                body = data.get("body", "")
                
                curr_sem = parse_semver(current_version)
                latest_sem = parse_semver(tag_name)
                
                has_update = latest_sem > curr_sem
                return (has_update, tag_name, html_url, title, body)
    except Exception as e:
        return (False, "", "", "", str(e))
    return (False, "", "", "", "")

CONFIG_FILE = get_data_filepath("power_timer_presets.json")
RULES_FILE = get_data_filepath("power_scheduler_rules.json")
SETTINGS_FILE = get_data_filepath("power_timer_settings.json")
THEME_CONFIG_FILE = get_data_filepath("power_theme_config.json")
SIDEBAR_THEME_FILE = get_data_filepath("sidebar_theme_config.json")
HISTORY_FILE = get_data_filepath("power_controller_history.log")
DEFAULT_PORT = 3032

DEFAULT_MASTER_RECOVERY_KEY = "PowerRescue#2026!Admin"

def get_local_mac():
    """로컬 네트워크 어댑터의 MAC 주소를 추출하여 Wake-on-LAN 원격 부팅 지원용으로 반환합니다."""
    try:
        import uuid
        node = uuid.getnode()
        mac = ':'.join(['{:02x}'.format((node >> i) & 0xff) for i in range(0, 48, 8)][::-1])
        return mac.upper()
    except Exception:
        return ""

def get_master_recovery_key():
    """
    관리자가 보안 인증 토큰을 분실하였을 때 사용하는 마스터 비상 복구 키 반환.
    환경변수 POWER_TIMER_MASTER_KEY 또는 power_master_key.txt 설정 파일이 있으면 최우선 적용합니다.
    """
    env_key = os.getenv("POWER_TIMER_MASTER_KEY", "").strip()
    if env_key:
        return env_key
    try:
        key_file = get_data_filepath("power_master_key.txt")
        if os.path.exists(key_file):
            with open(key_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
    except Exception:
        pass
    return DEFAULT_MASTER_RECOVERY_KEY

def handle_cli_token_commands():
    """
    GUI(Tkinter) 실행 전 명령줄 인자(--reset-token, --set-token, --show-token)를 감지하여
    헤드리스 및 원격 CLI 환경에서도 즉각적으로 토큰을 복구/초기화합니다.
    """
    if len(sys.argv) > 1:
        cli_cmd = sys.argv[1].strip().lower()
        if cli_cmd in ["--reset-token", "-rt", "/resettoken"]:
            try:
                settings_path = SETTINGS_FILE
                settings_dict = {}
                if os.path.exists(settings_path):
                    with open(settings_path, "r", encoding="utf-8") as f:
                        settings_dict = json.load(f)
                settings_dict["network_auth_token"] = ""
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings_dict, f, indent=4)
                print("SUCCESS: PowerTimer network security token has been reset to blank.")
                sys.exit(0)
            except Exception as e:
                print(f"ERROR: Failed to reset token: {e}")
                sys.exit(1)
        elif cli_cmd in ["--set-token", "-st"] and len(sys.argv) > 2:
            new_val = sys.argv[2].strip()
            try:
                settings_path = SETTINGS_FILE
                settings_dict = {}
                if os.path.exists(settings_path):
                    with open(settings_path, "r", encoding="utf-8") as f:
                        settings_dict = json.load(f)
                settings_dict["network_auth_token"] = new_val
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings_dict, f, indent=4)
                print(f"SUCCESS: PowerTimer network security token has been set to '{new_val}'.")
                sys.exit(0)
            except Exception as e:
                print(f"ERROR: Failed to set token: {e}")
                sys.exit(1)
        elif cli_cmd in ["--show-token", "-stk", "/showtoken"]:
            try:
                settings_path = SETTINGS_FILE
                tok_val = ""
                if os.path.exists(settings_path):
                    with open(settings_path, "r", encoding="utf-8") as f:
                        tok_val = json.load(f).get("network_auth_token", "")
                print(f"CURRENT_TOKEN:{tok_val}")
                sys.exit(0)
            except Exception as e:
                print(f"ERROR: {e}")
                sys.exit(1)

handle_cli_token_commands()

THEMES = {
    "dark": {
        "bg": "#111827",
        "card": "#1f2937",
        "text": "#f3f4f6",
        "blue": "#3b82f6",
        "red": "#ef4444",
        "green": "#10b981",
        "yellow": "#eab308",
        "subtext": "#9ca3af",
        "secondary": "#374151",
        "name_ko": "다크",
        "name_en": "Dark"
    },
    "gray": {
        "bg": "#1e293b",
        "card": "#334155",
        "text": "#f1f5f9",
        "blue": "#475569",
        "red": "#ba3c2a",
        "green": "#4a5d4e",
        "yellow": "#d97706",
        "subtext": "#cbd5e1",
        "secondary": "#475569",
        "name_ko": "회색",
        "name_en": "Gray"
    },
    "beige": {
        "bg": "#f5f0e6",
        "card": "#faf6ee",
        "text": "#4a3e2b",
        "blue": "#8c785c",
        "red": "#ba3c2a",
        "green": "#4a5d4e",
        "yellow": "#b45309",
        "subtext": "#8d795f",
        "secondary": "#d6d3d1",
        "name_ko": "베이지",
        "name_en": "Beige"
    }
}

def load_startup_theme():
    try:
        if os.path.exists(SIDEBAR_THEME_FILE): # compatible if renamed
            with open(SIDEBAR_THEME_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("theme", "beige")
        if os.path.exists(THEME_CONFIG_FILE):
            with open(THEME_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("theme", "beige")
    except:
        return "beige"
    return "beige"

STARTUP_THEME = load_startup_theme()
theme_cfg = THEMES.get(STARTUP_THEME, THEMES["beige"])

DARK_BG = theme_cfg["bg"]
DARK_CARD = theme_cfg["card"]
TEXT_COLOR = theme_cfg["text"]
ACCENT_BLUE = theme_cfg["blue"]
ACCENT_RED = theme_cfg["red"]
ACCENT_YELLOW = theme_cfg["yellow"]
CURRENT_GREEN = theme_cfg["green"]
CURRENT_SUBTEXT = theme_cfg["subtext"]
SECONDARY_BG = theme_cfg["secondary"]

# --------------------------------------------------------------------
# 자주 사용하는 스케줄 제목 프리셋 (10개)
# --------------------------------------------------------------------
POPULAR_SCHEDULE_TITLES_KO = [
    "심야 PC 자동 종료",
    "퇴근 시간 전원 끄기",
    "대용량 다운로드 후 종료",
    "점심시간 빠른 재부팅",
    "자리 비움 절전 모드",
    "새벽 정기 시스템 점검 재시작",
    "업무 시작 준비 알람",
    "영화/영상 시청 후 종료",
    "미사용 모니터 화면 끄기",
    "렌더링/인코딩 완료 후 종료"
]

POPULAR_SCHEDULE_TITLES_EN = [
    "Midnight Auto Shutdown",
    "End of Work Shutdown",
    "Post-Download Auto Shutdown",
    "Lunch Break Reboot",
    "Away / Idle Sleep Mode",
    "Dawn Scheduled System Reboot",
    "Work Start Reminder Alarm",
    "Post-Movie Auto Shutdown",
    "Screen Off on Inactivity",
    "Post-Rendering Auto Shutdown"
]

# --------------------------------------------------------------------
# 스크롤 가능 프레임 엘리먼트 정의 (고급 스케줄러 목록용)
# --------------------------------------------------------------------
class ScrollableFrame(tk.Frame):
    _active_frame = None

    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg=DARK_BG, bd=0, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=DARK_BG)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Synchronize width of the scrollable_frame with the canvas width so expand fill="x" is respected
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window_id, width=e.width)
        )
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Track active scroll target on mouse enter
        self.bind("<Enter>", self._set_active_target)
        self.canvas.bind("<Enter>", self._set_active_target)
        self.scrollable_frame.bind("<Enter>", self._set_active_target)

        # Bind mouse scroll wheel to canvas & internal frame
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel_up)
        self.canvas.bind("<Button-5>", self._on_mousewheel_down)
        self.scrollable_frame.bind("<Button-4>", self._on_mousewheel_up)
        self.scrollable_frame.bind("<Button-5>", self._on_mousewheel_down)

    def _set_active_target(self, event=None):
        ScrollableFrame._active_frame = self

    def _on_mousewheel(self, event):
        try:
            target = getattr(ScrollableFrame, "_active_frame", None) or self
            if not target or not hasattr(target, "canvas") or not target.canvas.winfo_exists():
                target = self
            if getattr(event, "delta", 0):
                # Windows delta is typically multiples of 120; scroll 3 units per notch for smooth, natural movement
                if abs(event.delta) >= 120:
                    lines = int(-1 * (event.delta / 120) * 3)
                else:
                    lines = int(-1 * event.delta * 2)
                target.canvas.yview_scroll(lines, "units")
            elif getattr(event, "num", None) == 4:
                target.canvas.yview_scroll(-3, "units")
            elif getattr(event, "num", None) == 5:
                target.canvas.yview_scroll(3, "units")
        except Exception:
            pass

    def _on_mousewheel_up(self, event):
        try:
            target = getattr(ScrollableFrame, "_active_frame", None) or self
            if target and hasattr(target, "canvas") and target.canvas.winfo_exists():
                target.canvas.yview_scroll(-3, "units")
        except Exception:
            pass

    def _on_mousewheel_down(self, event):
        try:
            target = getattr(ScrollableFrame, "_active_frame", None) or self
            if target and hasattr(target, "canvas") and target.canvas.winfo_exists():
                target.canvas.yview_scroll(3, "units")
        except Exception:
            pass

    def bind_children_mousewheel(self, widget=None):
        """Recursively bind mouse wheel to all inner children elements so scrolling works on all content"""
        if widget is None:
            widget = self.scrollable_frame
        try:
            widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
            widget.bind("<Button-4>", self._on_mousewheel_up, add="+")
            widget.bind("<Button-5>", self._on_mousewheel_down, add="+")
            widget.bind("<Enter>", self._set_active_target, add="+")
            for child in widget.winfo_children():
                self.bind_children_mousewheel(child)
        except Exception:
            pass


def ensure_firewall_rule_silent():
    """Windows Defender Firewall 예외 규칙을 무음(백그라운드) 등록하여 인바운드/공용 네트워크 차단 및 팝업 방지 (기본 및 버전 표기)"""
    if os.name == 'nt':
        try:
            exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.executable
            app_dir = os.path.dirname(os.path.abspath(exe_path))
            commander_exe = os.path.join(app_dir, "PowerNetworkScheduler.exe")
            
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
            
            # [1] 메인 프로그램 (PowerController.exe) 인바운드 및 아웃바운드 허용 (기본 및 버전 표기)
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 "name=PowerController (Inbound)", "dir=in", "action=allow", 
                 f"program={exe_path}", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 "name=PowerController (Outbound)", "dir=out", "action=allow", 
                 f"program={exe_path}", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 f"name=PowerController v{APP_VERSION} (Inbound)", "dir=in", "action=allow", 
                 f"program={exe_path}", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 f"name=PowerController v{APP_VERSION} (Outbound)", "dir=out", "action=allow", 
                 f"program={exe_path}", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
            
            # [2] 커맨더 프로그램 (PowerNetworkScheduler.exe) 인바운드 및 아웃바운드 허용 (기본 및 버전 표기)
            if os.path.exists(commander_exe):
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule", 
                     "name=PowerNetworkScheduler (Inbound)", "dir=in", "action=allow", 
                     f"program={commander_exe}", "enable=yes", "profile=any"],
                    capture_output=True,
                    creationflags=creationflags
                )
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule", 
                     "name=PowerNetworkScheduler (Outbound)", "dir=out", "action=allow", 
                     f"program={commander_exe}", "enable=yes", "profile=any"],
                    capture_output=True,
                    creationflags=creationflags
                )
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule", 
                     f"name=PowerNetworkScheduler v{APP_VERSION} (Inbound)", "dir=in", "action=allow", 
                     f"program={commander_exe}", "enable=yes", "profile=any"],
                    capture_output=True,
                    creationflags=creationflags
                )
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule", 
                     f"name=PowerNetworkScheduler v{APP_VERSION} (Outbound)", "dir=out", "action=allow", 
                     f"program={commander_exe}", "enable=yes", "profile=any"],
                    capture_output=True,
                    creationflags=creationflags
                )
            
            # [3] TCP 9988 포트 허용 규칙 (원격 스케줄 제어)
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 "name=PowerController TCP 9988", "dir=in", "action=allow", 
                 "protocol=TCP", "localport=9988", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 f"name=PowerController v{APP_VERSION} TCP 9988", "dir=in", "action=allow", 
                 "protocol=TCP", "localport=9988", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
            # [4] UDP 9985 & UDP 9986 포트 허용 규칙 (로컬 LAN 브로드캐스트 탐색 및 중앙 허브 동기화)
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 "name=PowerController UDP 9985", "dir=in", "action=allow", 
                 "protocol=UDP", "localport=9985", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 "name=PowerController UDP 9986", "dir=in", "action=allow", 
                 "protocol=UDP", "localport=9986", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 f"name=PowerController v{APP_VERSION} UDP 9985", "dir=in", "action=allow", 
                 "protocol=UDP", "localport=9985", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 f"name=PowerController v{APP_VERSION} UDP 9986", "dir=in", "action=allow", 
                 "protocol=UDP", "localport=9986", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
        except Exception:
            pass


def auto_fit_window(win, min_w=380, min_h=200, max_w=None, max_h=None, center_parent=None, padding_w=30, padding_h=30):
    """
    내부 텍스트 및 위젯들의 크기를 측정(update_idletasks)하여
    글자가 짤리지 않도록 창 크기를 자동 조절하고 중앙에 배치하는 범용 헬퍼 함수
    """
    try:
        win.update_idletasks()
        req_w = win.winfo_reqwidth() + padding_w
        req_h = win.winfo_reqheight() + padding_h
        
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        
        target_w = max(min_w, req_w)
        target_h = max(min_h, req_h)
        
        if max_w:
            target_w = min(max_w, target_w)
        else:
            target_w = min(int(sw * 0.95), target_w)
            
        if max_h:
            target_h = min(max_h, target_h)
        else:
            target_h = min(int(sh * 0.92), target_h)
            
        if center_parent and center_parent.winfo_exists():
            pw = center_parent.winfo_width()
            ph = center_parent.winfo_height()
            px = center_parent.winfo_x()
            py = center_parent.winfo_y()
            cx = max(0, px + (pw // 2) - (target_w // 2))
            cy = max(0, py + (ph // 2) - (target_h // 2))
        else:
            cx = max(0, (sw // 2) - (target_w // 2))
            cy = max(0, (sh // 2) - (target_h // 2))
            
        win.geometry(f"{target_w}x{target_h}+{cx}+{cy}")
    except Exception:
        pass


class PowerTimerApp:
    def __init__(self, root, start_hidden=False):
        self.root = root
        self.start_hidden = start_hidden
        self.lang = "ko"
        self.root.title("전원 종료/재시작 타이머")
        
        # 시작 시 메인창이 화면에 깜빡이거나 번쩍이지 않도록 시작 숨김 모드이면 즉각 withdraw 유지
        if self.start_hidden:
            self.root.withdraw()
        
        window_width = 500
        window_height = 690
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        self.root.minsize(500, 660)
        self.root.resizable(True, True)
        self.root.configure(bg=DARK_BG)

        if self.start_hidden:
            self.root.withdraw()
        
        # Set window icon using PowerController.png (cross-platform/PNG support) or PowerController.ico
        try:
            png_path = os.path.join(SCRIPT_DIR, "PowerController.png")
            ico_path = os.path.join(SCRIPT_DIR, "PowerController.ico")
            
            # Fallback to current working directory if not found in script dir
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
            try:
                if os.path.exists("PowerController.ico"):
                    self.root.iconbitmap("PowerController.ico")
            except Exception:
                pass
        
        # 시스템 기본 설정 정보 구축 및 지연 로드
        self.always_on_top = tk.BooleanVar(value=True)
        self.minimize_to_tray = tk.BooleanVar(value=True)
        self.boot_to_tray = tk.BooleanVar(value=True)
        self.main_opacity = tk.IntVar(value=100)
        self.widget_opacity = tk.IntVar(value=95)
        self.show_current_time_compact = tk.BooleanVar(value=False)
        self.widget_design = tk.StringVar(value="standard")
        self.widget_width = tk.IntVar(value=286)
        self.widget_height = tk.IntVar(value=95)
        self.mini_context_popup = None
        self.clock_font_size = tk.IntVar(value=13)
        self.timer_font_size = tk.IntVar(value=20)
        self.hourly_chime_enabled = tk.BooleanVar(value=True)
        self.startup_alert_enabled = tk.BooleanVar(value=True)
        self.last_chime_hour = -1
        self.selected_font = tk.StringVar(value="font-sans")
        self.selected_font_label = tk.StringVar(value="산세리프 (Inter)")
        self.selected_font_weight = tk.StringVar(value="normal")
        self.selected_font_weight_label = tk.StringVar(value="보통")
        self.network_receive_enabled = tk.BooleanVar(value=False)
        self.network_auth_token = tk.StringVar(value="")
        self.grace_seconds_setting = tk.IntVar(value=10)
        self.grace_seconds_label = tk.StringVar(value="10초 (10 seconds)")
        self.force_close_enabled = tk.BooleanVar(value=True)
        self.load_settings()
        
        try:
            self.root.attributes("-alpha", self.main_opacity.get() / 100.0)
        except Exception:
            pass
            
        # 기본 변수 구동계
        self.mode = "shutdown" # "shutdown" or "restart"
        self.run_type = "timer" # "timer" (시간 지정 후 카운트다운) or "schedule" (특정 시정 시각 예약)
        self.remaining_seconds = 0
        self.timer_running = False
        self.timer_paused = False
        self.favorites = []
        self.rules = []
        self.editing_rule_id = None
        self.tray_icon = None
        self.mouse_in_tray_previously = False
        self.last_checked_minute = -1
        self.cached_tray_base_image = None
        
        # 최소화 시 트레이 숨김 이벤트 감지
        self.root.bind("<Unmap>", self.on_minimize)
        
        # 윈도우 X 닫기 버튼 클릭 시 동작을 트레이 최소화로 전환
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_button)
        
        # 기본 즐겨찾기 및 스케줄러 데이터베이스 로드
        self.load_favorites()
        self.load_rules()
        
        # 윈도우 시작 시 자동 실행 여부 체크 변수
        self.auto_start = tk.BooleanVar(value=self.check_startup_reg())
        
        # 시작 프로그램 레지스트리 자동 점검 및 보정 (--startup --tray 누락 시 즉각 치유)
        if self.auto_start.get():
            self.heal_startup_reg()

        # 부팅 시점 또는 트레이 실행 종합 판별
        startup_flags = ["--startup", "-startup", "/startup", "--tray", "-tray", "/tray", "-s", "--boot", "-boot", "--minimized", "-minimized", "-m"]
        is_cli_startup = any(arg.lower() in startup_flags for arg in sys.argv[1:])
        is_boot_recent = False
        if sys.platform == "win32":
            try:
                import ctypes
                uptime_ms = ctypes.windll.kernel32.GetTickCount64()
                # 윈도우 부팅 후 6분 이내 실행 + (자동 실행 등록 또는 부팅 트레이 활성)
                if uptime_ms < 360000 and (self.auto_start.get() or self.boot_to_tray.get()):
                    is_boot_recent = True
            except Exception:
                pass
        
        self.is_boot_startup = getattr(self, "start_hidden", False) or is_cli_startup or is_boot_recent or self.boot_to_tray.get()

        # 테마 변수 통제 엔진
        self.current_theme = STARTUP_THEME
        self.current_green = CURRENT_GREEN
        self.current_subtext = CURRENT_SUBTEXT
        self.active_tab = "control"

        # UI 레이아웃 로드
        self.create_widgets()
        self.update_ui_translations()
        self.apply_current_font_to_widgets()
        self.highlight_active_theme_button(self.current_theme)

        # 시작 모드 분기: 컴퓨터 시작(부팅) 시에는 메인창을 일절 화면에 띄우지 않고 시스템 트레이 백그라운드로 안전하게 동작
        if self.is_boot_startup:
            self.root.attributes('-topmost', False)
            self.root.withdraw()
            if P_TRAY_AVAILABLE:
                self.log_event("컴퓨터 시작(부팅) 감지: 메인창을 띄우지 않고 시스템 트레이 백그라운드로 안전하게 시작합니다." if self.lang == "ko" else "System startup detected: Starting silently in system tray without showing main window.")
                self.root.after(150, self.start_tray_icon)
        else:
            self.root.deiconify()
            self.sync_always_on_top_mini_win()

        self.log_event("전원 제어 스마트 어시스턴트 애플리케이션 시작" if self.lang == "ko" else "Power Control Smart Assistant Application Started")
        
        # 순수 창작 SysPowerHook 윈도우 세션 감시 훅 가동 (화면 잠금 및 전원 이벤트 실시간 감지)
        if native_bridge:
            try:
                native_bridge.start_session_hook()
            except Exception:
                pass

        # 1초 주기로 돌아가며 고급 스케줄러 규칙을 검증하는 감시 엔진 실행
        self.root.after(1000, self.check_advanced_schedules)
        
        # 150ms 주기로 돌아가는 시스템 트레이 아이콘 애니메이션 루프 실행
        self.root.after(1000, self.animate_tray_icon_loop)

        # 윈도우 방화벽 인바운드 차단/예외 등록 무음 시도
        try:
            ensure_firewall_rule_silent()
        except:
            pass

        # 네트워크 원격 예약 및 보안 토큰 수신 서버 시작 (무조작 수신 대기)
        self.start_network_receive_server()

        # 방화벽 '허용' 비활성화 환경에서도 무조작으로 토큰/명령을 수신하는 아웃바운드 자동 동기화 에이전트 시작
        self.start_outbound_sync_daemon()

        # 시작 시 오늘 예약 작업 확인 및 안내 모달 팝업 (시스템 트레이 전용 알림창)
        if self.startup_alert_enabled.get():
            self.root.after(800, self.check_and_show_startup_today_tasks)

        # 시작 시 백그라운드로 GitHub 최신 릴리스 확인 및 새 버전 발견 시 업데이트 알림 팝업창 자동 실행
        self.root.after(1500, self.check_auto_update_on_startup)

    def toggle_language(self):
        self.lang = "en" if self.lang == "ko" else "ko"
        self.save_settings()
        self.update_ui_translations()

    def update_ui_translations(self):
        # Translate default favorites labels if they match
        fav_map = {
            "ko_to_en": {
                "영화 시청 후 종료 (2시간)": "Shutdown After Movie (2h)",
                "점심시간 빠른 재부팅 (1시간)": "Quick Lunch Reboot (1h)",
                "15분 집중 후 종료": "Shutdown in 15m Focus"
            },
            "en_to_ko": {
                "Shutdown After Movie (2h)": "영화 시청 후 종료 (2시간)",
                "Quick Lunch Reboot (1h)": "점심시간 빠른 재부팅 (1시간)",
                "Shutdown in 15m Focus": "15분 집중 후 종료"
            }
        }
        for fav in self.favorites:
            lbl = fav.get("label", "")
            if self.lang == "en" and lbl in fav_map["ko_to_en"]:
                fav["label"] = fav_map["ko_to_en"][lbl]
            elif self.lang == "ko" and lbl in fav_map["en_to_ko"]:
                fav["label"] = fav_map["en_to_ko"][lbl]

        # Update language toggle button text
        self.btn_lang.config(text="EN" if self.lang == "ko" else "KO")
        
        # Update title text
        self.root.title("전원 종료/재시작 타이머" if self.lang == "ko" else "Power Shut Down/Restart Timer")
        self.title_label.config(text="⚡ PowerController (제작자: AhBiYout)" if self.lang == "ko" else "⚡ PowerController (Author: AhBiYout)")
        
        # Always On Top checkbutton
        self.pin_btn.config(text="📌 상단 고정" if self.lang == "ko" else "📌 Always On Top")
        
        # Open Scheduler button
        self.btn_open_scheduler_popup.config(text="🖥️ 스케줄러 팝업창 열기" if self.lang == "ko" else "🖥️ Open Task Scheduler")
        
        # Auto Start checkbutton
        self.auto_start_btn.config(text="⚙️ 시작 시 자동 실행" if self.lang == "ko" else "⚙️ Run on Startup")
        
        # Boot to Tray checkbutton
        self.boot_to_tray_btn.config(text="📥 부팅 시 트레이" if self.lang == "ko" else "📥 Boot to Tray")
        
        # Minimize to Tray checkbutton
        self.minimize_tray_btn.config(text="📁 최소화 시 트레이" if self.lang == "ko" else "📁 Minimize to Tray")
        
        # Remote Receive Checkbutton
        if hasattr(self, "net_recv_btn") and self.net_recv_btn.winfo_exists():
            self.net_recv_btn.config(text="📡 원격 예약 수신 허용 (포트 9988)" if self.lang == "ko" else "📡 Enable Remote Receiver (Port 9988)")
        
        # Settings Toggle Button
        if hasattr(self, "settings_toggle_btn") and self.settings_toggle_btn.winfo_exists():
            self.settings_toggle_btn.config(text="⚙️ 설정 (Settings) ..." if self.lang == "ko" else "⚙️ Settings ...")

        # Choose Theme label
        if hasattr(self, "lbl_theme") and self.lbl_theme.winfo_exists():
            self.lbl_theme.config(text="🎨 테마 선택:" if self.lang == "ko" else "🎨 Choose Theme:")
        if hasattr(self, "theme_btns"):
            for t_key, btn in self.theme_btns.items():
                if btn.winfo_exists():
                    btn.config(text=THEMES[t_key]["name_ko"] if self.lang == "ko" else THEMES[t_key]["name_en"])
        
        # Translate Sound Theme label and buttons
        sound_themes_labels = {
            "classic": {"ko": "클래식 비프", "en": "Classic Beep"},
            "scifi": {"ko": "SF 신스", "en": "Sci-Fi Synth"},
            "cozy": {"ko": "아늑한 멜로디", "en": "Cozy Chime"}
        }
        if hasattr(self, "lbl_sound_theme") and self.lbl_sound_theme.winfo_exists():
            self.lbl_sound_theme.config(text="🎵 사운드 테마:" if self.lang == "ko" else "🎵 Sound Theme:")
        if hasattr(self, "sound_theme_btns"):
            for st_key, btn in self.sound_theme_btns.items():
                if btn.winfo_exists():
                    btn.config(text=sound_themes_labels[st_key]["ko"] if self.lang == "ko" else sound_themes_labels[st_key]["en"])
        
        # Navigation Tabs
        self.btn_tab_control.config(text="⏱ 간편 제어" if self.lang == "ko" else "⏱ Control Panel")
        self.btn_tab_scheduler.config(text="📅 규칙 스케줄러" if self.lang == "ko" else "📅 Scheduler")
        self.btn_tab_history.config(text="📋 동작 기록" if self.lang == "ko" else "📋 History Log")
        
        # Mode buttons (optional, but it's super nice to keep icons and translate Korean labels)
        if hasattr(self, 'mode_buttons'):
            self.mode_buttons["shutdown"].config(text="종료" if self.lang == "ko" else "Shut down")
            self.mode_buttons["restart"].config(text="재시작" if self.lang == "ko" else "Restart")
            self.mode_buttons["sleep"].config(text="절전" if self.lang == "ko" else "Sleep")
            self.mode_buttons["screenoff"].config(text="화면끔" if self.lang == "ko" else "Screen Off")
            self.mode_buttons["logout"].config(text="로그아웃" if self.lang == "ko" else "Log out")
            self.mode_buttons["alarm"].config(text="알람" if self.lang == "ko" else "Alarm")
            
        # Run type toggle buttons
        self.btn_type_timer.config(text="⏳ 시간 타이머 (후)" if self.lang == "ko" else "⏳ Timer delay (after)")
        self.btn_type_schedule.config(text="⏰ 특정 시각 예약 (정시)" if self.lang == "ko" else "⏰ Specific Clock (at)")
        
        # Update input guide text according to current type (timer vs schedule)
        if self.run_type == "timer":
            self.lbl_input_guide.config(text="[타이머] 지정된 시간/분/초 후 동작을 수행합니다." if self.lang == "ko" else "[Timer Mode] Specify delay in hours/minutes/seconds.")
        else:
            self.lbl_input_guide.config(text="[지정 시각] 동작을 실행할 목표 시각을 지정하십시오." if self.lang == "ko" else "[Clock Mode] Specify target hours/minutes/seconds.")
            
        # Field labels for Time selection (H, M, S)
        self.lbl_field_1.config(text="시" if self.lang == "ko" else "H")
        self.lbl_field_2.config(text="분" if self.lang == "ko" else "M")
        self.lbl_field_3.config(text="초" if self.lang == "ko" else "S")
        
        # Trigger buttons
        if hasattr(self, 'timer_running') and self.timer_running:
            self.btn_start.config(text="⏹ 타이머 정지" if self.lang == "ko" else "⏹ Stop Timer")
        else:
            self.btn_start.config(text="▶ 타이머 시작" if self.lang == "ko" else "▶ Start Timer")
            
        self.btn_reset.config(text="🔄 리셋" if self.lang == "ko" else "🔄 Reset")
        
        # Presets Panel
        if hasattr(self, 'fav_label'):
            self.fav_label.config(text="⭐ 더블 클릭 시 즉시 스케줄링 가동" if self.lang == "ko" else "⭐ Double Click to Trigger Preset")
        if hasattr(self, 'btn_add_fav'):
            self.btn_add_fav.config(text="➕ 추가" if self.lang == "ko" else "➕ Add")
        if hasattr(self, 'btn_edit_fav'):
            self.btn_edit_fav.config(text="✏️ 수정" if self.lang == "ko" else "✏️ Edit")
        if hasattr(self, 'btn_del_fav'):
            self.btn_del_fav.config(text="❌ 삭제" if self.lang == "ko" else "❌ Delete")
        
        # Presets Render
        if hasattr(self, 'fav_listbox'):
            self.render_favorites()
        
        # License notice label
        if hasattr(self, 'lbl_license_notice'):
            self.lbl_license_notice.config(text="📄 라이선스 및 약관 동의 고지서" if self.lang == "ko" else "📄 License & Terms Agreement Notice")
        
        # Footer label
        if hasattr(self, 'lbl_footer_info'):
            self.lbl_footer_info.config(text=f"소속: http://www.cisnet.co.kr/ | 개발자: AhBiYout | 버전: v{APP_VERSION}" if self.lang == "ko" else f"Organization: http://www.cisnet.co.kr/ | Developer: AhBiYout | Version: v{APP_VERSION}")
        if hasattr(self, 'lbl_blog_info'):
            self.lbl_blog_info.config(text="구글블로그: https://ahbiyoutvibe.blogspot.com/" if self.lang == "ko" else "Google Blog: https://ahbiyoutvibe.blogspot.com/")
        
        # History Tab Label and clear button
        if hasattr(self, 'lbl_info'):
            self.lbl_info.config(text="📋 시스템 전원 제어 및 타이머 동작 기록" if self.lang == "ko" else "📋 Power Control & Timer Logs")
        if hasattr(self, 'btn_clear'):
            self.btn_clear.config(text="🗑️ 로그 기록 초기화" if self.lang == "ko" else "🗑️ Clear Logs")
            
        # Rule Form (Scheduler Creation page) translations if it exists
        if hasattr(self, 'frm_add_rule') and self.frm_add_rule.winfo_exists():
            if self.editing_rule_id:
                for r in self.rules:
                    if r.get("id") == self.editing_rule_id:
                        lbl_txt = r.get('label')[:15]
                        self.frm_add_rule.config(text=f"규칙 수정 중: {lbl_txt}" if self.lang == "ko" else f"Editing Rule: {lbl_txt}")
                        break
            else:
                self.frm_add_rule.config(text="규칙 생성 조건" if self.lang == "ko" else "Add Scheduler Rule")
            
            if hasattr(self, 'lbl_add_title'):
                self.lbl_add_title.config(text="➕ 새 스케줄 규칙 등록기" if self.lang == "ko" else "➕ Add New Scheduler Rule")
            if hasattr(self, 'lbl_rule_name'):
                self.lbl_rule_name.config(text="스케줄 이름 (메모):" if self.lang == "ko" else "Schedule Title (Memo):")
            if hasattr(self, 'om_preset') and hasattr(self, 'var_preset_title'):
                ph = "📋 자주 쓰는 제목 (10개)..." if self.lang == "ko" else "📋 Popular Titles (10)..."
                self.var_preset_title.set(ph)
                menu = self.om_preset["menu"]
                menu.delete(0, "end")
                titles = POPULAR_SCHEDULE_TITLES_KO if self.lang == "ko" else POPULAR_SCHEDULE_TITLES_EN
                for t in titles:
                    def make_tab_cmd(sel_title=t, placeholder=ph):
                        return lambda: (self.var_rule_label.set(sel_title), self.clear_form_validation_errors(), self.var_preset_title.set(placeholder))
                    menu.add_command(label=t, command=make_tab_cmd(t, ph))
            if hasattr(self, 'lbl_rule_action'):
                self.lbl_rule_action.config(text="트리거 대기 전원 행동:" if self.lang == "ko" else "Action Mode to Trigger:")
            if hasattr(self, 'lbl_rule_type_title'):
                self.lbl_rule_type_title.config(text="반복 플랜 타입:" if self.lang == "ko" else "Interval Repeat Type:")
            if hasattr(self, 'lbl_time_helper'):
                self.lbl_time_helper.config(text="알람 시각 (24시 형식):" if self.lang == "ko" else "Precise alarm trigger time (24h format):")
            if hasattr(self, 'lbl_interval_txt_1'):
                self.lbl_interval_txt_1.config(text="실행 발생 순환 간격:" if self.lang == "ko" else "Repeat interval cycle:")
            if hasattr(self, 'lbl_interval_txt_2'):
                self.lbl_interval_txt_2.config(text="분 마다 구동" if self.lang == "ko" else "minutes cycle")
            if hasattr(self, 'cmd_chk_f'):
                self.cmd_chk_f.config(text="파일/앱 강제 종료 (/f)" if self.lang == "ko" else "Force close apps (/f)")
            if hasattr(self, 'cmd_chk_beep'):
                self.cmd_chk_beep.config(text="1분 전 비프음 수동 경보" if self.lang == "ko" else "Audio warning 1min before")
            if hasattr(self, 'btn_submit_rule'):
                if self.editing_rule_id:
                    self.btn_submit_rule.config(text="스케줄 규칙 수정 반영하기" if self.lang == "ko" else "Update Rules & Save Modifications")
                else:
                    self.btn_submit_rule.config(text="스케줄 규칙 등록" if self.lang == "ko" else "Register Rule")
            if hasattr(self, 'btn_cancel_edit'):
                self.btn_cancel_edit.config(text="수정 취소" if self.lang == "ko" else "Cancel Edit")

            # Translate actions radios in rule form
            action_options_text = {
                "shutdown": {"ko": "종료", "en": "Shut down"},
                "restart": {"ko": "재시동", "en": "Restart"},
                "sleep": {"ko": "절전", "en": "Sleep"},
                "screenoff": {"ko": "화면끔", "en": "Screen off"},
                "logout": {"ko": "아웃", "en": "Log out"},
                "alarm": {"ko": "알람", "en": "Alarm"}
            }
            if hasattr(self, 'action_sel_btn'):
                for k, btn in self.action_sel_btn.items():
                    btn.config(text=action_options_text[k]["ko"] if self.lang == "ko" else action_options_text[k]["en"])

            # Translate repeat types in rule form
            type_options_text = {
                "once": {"ko": "일회성 (Once)", "en": "Once Plan"},
                "daily": {"ko": "매일 (Daily)", "en": "Daily Plan"},
                "weekly": {"ko": "요일 반복 (Weekly)", "en": "Weekly Plan"},
                "interval": {"ko": "동작주기 (Interval)", "en": "Interval Cycle"}
            }
            if hasattr(self, 'type_sel_btn'):
                for k, btn in self.type_sel_btn.items():
                    btn.config(text=type_options_text[k]["ko"] if self.lang == "ko" else type_options_text[k]["en"])
                    
            # Translate weekly days checkbox
            day_names = ["일", "월", "화", "수", "목", "금", "토"]
            day_names_en = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            if hasattr(self, 'day_checkboxes'):
                for chk, idx in self.day_checkboxes:
                    chk.config(text=day_names[idx] if self.lang == "ko" else day_names_en[idx])

        # Bidirectional mapping for default scheduler rules
        rules_map = {
            "ko_to_en": {
                "야간 대기 전력 차단 (매일)": "Night standby power cutoff (Daily)",
                "서버 클린 일요 조기 정기 점검": "Sunday regular server clean assessment"
            },
            "en_to_ko": {
                "Night standby power cutoff (Daily)": "야간 대기 전력 차단 (매일)",
                "Sunday regular server clean assessment": "서버 클린 일요 조기 정기 점검"
            }
        }
        for r in self.rules:
            lbl = r.get("label", "")
            if self.lang == "en" and lbl in rules_map["ko_to_en"]:
                r["label"] = rules_map["ko_to_en"][lbl]
            elif self.lang == "ko" and lbl in rules_map["en_to_ko"]:
                r["label"] = rules_map["en_to_ko"][lbl]

        # Translate display options section
        if hasattr(self, "lbl_widget_title"):
            self.lbl_widget_title.config(text="📌 상단고정 설정:" if self.lang == "ko" else "📌 Always-on-Top:")
        if hasattr(self, "chk_show_time"):
            self.chk_show_time.config(text="현재 시각 표시" if self.lang == "ko" else "Show Clock")
        if hasattr(self, "lbl_widget_opacity"):
            self.lbl_widget_opacity.config(text="투명도:" if self.lang == "ko" else "Opacity:")
        if hasattr(self, "lbl_main_title"):
            self.lbl_main_title.config(text="👁️ 메인창 설정:" if self.lang == "ko" else "👁️ Main Window:")
        if hasattr(self, "lbl_main_opacity"):
            self.lbl_main_opacity.config(text="투명도:" if self.lang == "ko" else "Opacity:")
        if hasattr(self, "lbl_font_title"):
            self.lbl_font_title.config(text="글꼴:" if self.lang == "ko" else "Font:")
        if hasattr(self, "lbl_font_weight_title"):
            self.lbl_font_weight_title.config(text="두께:" if self.lang == "ko" else "Wgt:")
            
        # Re-populate Font OptionMenu with translated display names
        FONT_LABELS = {
            "ko": {
                "font-sans": "산세리프 (Inter)",
                "font-display": "테크 (Grotesk)",
                "font-mono": "고정폭 (Mono)",
                "font-serif": "명조 (나눔명조)",
                "font-malgun": "맑은 고딕 (Malgun)",
                "font-gulim": "굴림 (Gulim)",
                "font-batang": "바탕 (Batang)"
            },
            "en": {
                "font-sans": "Sans (Inter)",
                "font-display": "Tech (Grotesk)",
                "font-mono": "Mono (Coding)",
                "font-serif": "Serif (Myeongjo)",
                "font-malgun": "Malgun Gothic",
                "font-gulim": "Gulim",
                "font-batang": "Batang"
            }
        }
        if hasattr(self, "opt_font"):
            self.opt_font['menu'].delete(0, 'end')
            for option in ["font-sans", "font-display", "font-mono", "font-serif", "font-malgun", "font-gulim", "font-batang"]:
                lbl = FONT_LABELS[self.lang][option]
                self.opt_font['menu'].add_command(label=lbl, command=lambda o=option: self.handle_font_change(o))
            # Sync label value
            self.selected_font_label.set(FONT_LABELS[self.lang].get(self.selected_font.get(), "Unknown"))

        # Re-populate Font Weight OptionMenu with translated display names
        if hasattr(self, "opt_font_weight"):
            self.opt_font_weight['menu'].delete(0, 'end')
            weight_labels = {
                "normal": "보통" if self.lang == "ko" else "Normal",
                "bold": "굵게" if self.lang == "ko" else "Bold"
            }
            for weight_opt in ["normal", "bold"]:
                lbl = weight_labels[weight_opt]
                self.opt_font_weight['menu'].add_command(label=lbl, command=lambda w=weight_opt: self.handle_font_weight_change(w))
            # Sync label value
            self.selected_font_weight_label.set(weight_labels[self.selected_font_weight.get()])

        # Translate Reservation Grace Warning UI elements
        if hasattr(self, "frm_grace") and self.frm_grace.winfo_exists():
            self.frm_grace.config(text="⏰ 예약작업 알림 설정" if self.lang == "ko" else "⏰ Grace Warning Settings")
        if hasattr(self, "lbl_grace_desc") and self.lbl_grace_desc.winfo_exists():
            self.lbl_grace_desc.config(text="예약작업 실행 전 안내 대기창 지속 시간:" if self.lang == "ko" else "Countdown before running task:")
        if hasattr(self, "opt_grace") and self.opt_grace.winfo_exists():
            self.opt_grace['menu'].delete(0, 'end')
            for secs_opt in [5, 10, 20, 30, 60, 180, 300]:
                lbl = self.get_grace_label_by_seconds(secs_opt)
                self.opt_grace['menu'].add_command(label=lbl, command=lambda s=secs_opt: self.handle_grace_seconds_change(s))
            self.grace_seconds_label.set(self.get_grace_label_by_seconds(self.grace_seconds_setting.get()))

        if hasattr(self, "render_rules_list"):
            self.render_rules_list()
            
        if hasattr(self, "refresh_accordion_ui"):
            self.refresh_accordion_ui()

    def load_favorites(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.favorites = json.load(f)
            except:
                self.load_default_presets()
        else:
            self.load_default_presets()
            
    def load_default_presets(self):
        if self.lang == "ko":
            self.favorites = [
                {"label": "영화 시청 후 종료 (2시간)", "mode": "shutdown", "seconds": 7200},
                {"label": "점심시간 빠른 재부팅 (1시간)", "mode": "restart", "seconds": 3600},
                {"label": "15분 집중 후 종료", "mode": "shutdown", "seconds": 900}
            ]
        else:
            self.favorites = [
                {"label": "Shutdown After Movie (2h)", "mode": "shutdown", "seconds": 7200},
                {"label": "Quick Lunch Reboot (1h)", "mode": "restart", "seconds": 3600},
                {"label": "Shutdown in 15m Focus", "mode": "shutdown", "seconds": 900}
            ]
        self.save_favorites()
        
    def save_favorites(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, indent=4, ensure_ascii=False)
        except Exception as e:
            pass

    def show_in_app_toast(self, message, bg_color="#10b981", fg_color="white", duration=3000):
        if hasattr(self, "_in_app_toast_frame") and self._in_app_toast_frame.winfo_exists():
            self._in_app_toast_frame.destroy()
            
        self._in_app_toast_frame = tk.Frame(self.root, bg=bg_color, padx=15, pady=8, bd=1, relief="ridge", highlightbackground="#065f46", highlightthickness=1)
        lbl = tk.Label(self._in_app_toast_frame, text=message, font=("Arial", 10, "bold"), bg=bg_color, fg=fg_color)
        lbl.pack()
        
        self._in_app_toast_frame.place(relx=0.5, rely=0.92, anchor="s")
        self.root.after(duration, lambda f=self._in_app_toast_frame: self._destroy_in_app_toast(f))
        
    def _destroy_in_app_toast(self, frame):
        if frame.winfo_exists():
            frame.destroy()

    def log_event(self, event_text, in_app_toast=False):
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] {event_text}\n"
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(log_line)
            # If historical logger UI needs refreshing
            if hasattr(self, "refresh_history_log_view"):
                self.refresh_history_log_view()
        except:
            pass
            
        if in_app_toast:
            self.show_in_app_toast(event_text)

    # --------------------------------------------------------------------
    # 영구 스케줄 규칙 저장 및 로드
    # --------------------------------------------------------------------
    def load_rules(self):
        if os.path.exists(RULES_FILE):
            try:
                with open(RULES_FILE, "r", encoding="utf-8") as f:
                    self.rules = json.load(f)
            except Exception:
                self.rules = []
                self.load_default_scheduler_rules()
        else:
            self.load_default_scheduler_rules()
            
    def load_default_scheduler_rules(self):
        now_str = datetime.datetime.now().isoformat()
        self.rules = [
            {
                "id": "rule-1",
                "label": "야간 대기 전력 차단 (매일)",
                "type": "daily",
                "mode": "sleep",
                "time": "23:30",
                "force_close": True,
                "warning_beep": True,
                "is_active": True,
                "created_at": now_str,
                "last_executed": ""
            },
            {
                "id": "rule-2",
                "label": "서버 클린 일요 조기 정기 점검",
                "type": "weekly",
                "mode": "restart",
                "time": "04:00",
                "days": [0], # Sunday
                "force_close": True,
                "warning_beep": True,
                "is_active": True,
                "created_at": now_str,
                "last_executed": ""
            }
        ]
        self.save_rules()
        
    def save_rules(self):
        try:
            with open(RULES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.rules, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

        # --------------------------------------------------------------------
        # 스케줄 등록/수정 시 schedule_share_builder.py 생성 또는 즉시 수정 보장
        # --------------------------------------------------------------------
        try:
            builder_content = r'''# -*- coding: utf-8 -*-
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

def print_styled(text, style_color):
    if os.name == 'nt':
        # Windows CMD/PowerShell ANSI 지원 여부에 따른 처리
        print(text)
    else:
        print(f"{style_color}{text}{COLOR_RESET}")

def generate_injector_source(rules_data_str):
    """
    다른 PC에서 작동할 스케줄 주입기 소스코드를 생성합니다.
    내부에 현재 시점의 JSON 데이터를 직접 텍스트 상수로 포함(임베딩)합니다.
    """
    source_code = f"""# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import shutil
import subprocess
try:
    import winreg
    REG_AVAILABLE = True
except ImportError:
    REG_AVAILABLE = False

# 주입할 스케줄 데이터가 내장되어 있습니다.
EMBEDDED_RULES = {repr(rules_data_str)}

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
            
            # UninstallString 예시: "C:\\Users\\user\\AppData\\Local\\PowerController\\uninstaller.exe" --uninstall
            # 따옴표 제거 및 디렉토리 추출
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
            
    # 레지스트리 추적 실패 시 기본 경로 검증
    for path in possible_paths:
        if os.path.exists(path) and os.path.exists(os.path.join(path, "PowerController.exe")):
            return path
            
    return None

def inject_schedule():
    print("==================================================")
    print("      PowerController 스케줄 강제 주입/복사 도구      ")
    print("==================================================")
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
        os.system("taskkill /f /im PowerController.exe")
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

    # 빌드 명령어 조합
    # icon 파일이 존재하면 포함
    ico_path = "PowerController.ico"
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
'''
            builder_path = os.path.join(SCRIPT_DIR, "schedule_share_builder.py")
            if not os.path.exists(builder_path):
                with open(builder_path, "w", encoding="utf-8") as f:
                    f.write(builder_content)
        except Exception:
            pass

    # --------------------------------------------------------------------
    # 2. UI 위젯 생성 (시간 간역 및 다중 고급 스케줄러 탭 분배)
    # --------------------------------------------------------------------
    def create_widgets(self):
        # 상단 타이틀 바 대용
        header_frame = tk.Frame(self.root, bg=DARK_BG, pady=5)
        header_frame.pack(fill="x", padx=15)

        self.title_label = tk.Label(header_frame, text="⚡ PowerController (제작자: AhBiYout)" if self.lang == "ko" else "⚡ PowerController (Author: AhBiYout)", font=("Arial", 11, "bold"), fg=TEXT_COLOR, bg=DARK_BG)
        self.title_label.pack(side="left")
        
        self.btn_lang = tk.Button(
            header_frame,
            text="EN" if self.lang == "ko" else "KO",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            relief="flat",
            padx=10,
            pady=1,
            cursor="hand2",
            command=self.toggle_language
        )
        self.btn_lang.pack(side="right")
        
        # 상단 옵션 탭 (고정 및 자동 시작 설정)
        options_frame = tk.Frame(self.root, bg=DARK_BG)
        options_frame.pack(fill="x", padx=15, pady=(0, 5))
        
        opt_row1 = tk.Frame(options_frame, bg=DARK_BG)
        opt_row1.pack(fill="x", pady=2)
        
        self.pin_btn = tk.Checkbutton(
            opt_row1, 
            text="📌 상단 고정" if self.lang == "ko" else "📌 Always On Top", 
            variable=self.always_on_top,
            command=self.toggle_always_on_top,
            bg=DARK_BG, 
            fg=TEXT_COLOR,
            selectcolor=DARK_CARD,
            activebackground=DARK_BG,
            activeforeground=TEXT_COLOR,
            font=("Arial", 10, "bold")
        )
        self.pin_btn.pack(side="left")

        self.btn_open_scheduler_popup = tk.Button(
            opt_row1,
            text="🖥️ 스케줄러 팝업창 열기" if self.lang == "ko" else "🖥️ Open Task Scheduler",
            font=("Arial", 10, "bold"),
            bg=ACCENT_BLUE,
            fg="white",
            relief="flat",
            padx=10,
            pady=2,
            command=self.open_scheduler_popup
        )
        self.btn_open_scheduler_popup.pack(side="right")
        
        opt_row2 = tk.Frame(options_frame, bg=DARK_BG)
        opt_row2.pack(fill="x", pady=2)

        self.auto_start_btn = tk.Checkbutton(
            opt_row2, 
            text="⚙️ 시작 시 자동 실행" if self.lang == "ko" else "⚙️ Run on Startup", 
            variable=self.auto_start,
            command=self.toggle_startup,
            bg=DARK_BG, 
            fg=TEXT_COLOR,
            selectcolor=DARK_CARD,
            activebackground=DARK_BG,
            activeforeground=TEXT_COLOR,
            font=("Arial", 10, "bold")
        )
        self.auto_start_btn.pack(side="left")

        self.boot_to_tray_btn = tk.Checkbutton(
            opt_row2,
            text="📥 부팅 시 트레이" if self.lang == "ko" else "📥 Boot to Tray",
            variable=self.boot_to_tray,
            command=self.toggle_boot_to_tray,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            selectcolor=DARK_CARD,
            activebackground=DARK_BG,
            activeforeground=TEXT_COLOR,
            font=("Arial", 10, "bold")
        )
        self.boot_to_tray_btn.pack(side="right")

        opt_row3 = tk.Frame(options_frame, bg=DARK_BG)
        opt_row3.pack(fill="x", pady=2)

        self.minimize_tray_btn = tk.Checkbutton(
            opt_row3,
            text="📁 최소화 시 트레이" if self.lang == "ko" else "📁 Minimize to Tray",
            variable=self.minimize_to_tray,
            command=self.save_settings,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            selectcolor=DARK_CARD,
            activebackground=DARK_BG,
            activeforeground=TEXT_COLOR,
            font=("Arial", 10, "bold")
        )
        self.minimize_tray_btn.pack(side="left")

        self.force_close_btn = tk.Checkbutton(
            opt_row3,
            text="⚡ 강제 닫기 (/f)" if self.lang == "ko" else "⚡ Force Close (/f)",
            variable=self.force_close_enabled,
            command=self.save_settings,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            selectcolor=DARK_CARD,
            activebackground=DARK_BG,
            activeforeground=TEXT_COLOR,
            font=("Arial", 10, "bold")
        )
        self.force_close_btn.pack(side="right")
        
        opt_row4 = tk.Frame(options_frame, bg=DARK_BG)
        opt_row4.pack(fill="x", pady=2)

        self.net_recv_btn = tk.Checkbutton(
            opt_row4,
            text="📡 원격 예약 수신 허용 (포트 9988)" if self.lang == "ko" else "📡 Enable Remote Receiver (Port 9988)",
            variable=self.network_receive_enabled,
            command=self.toggle_network_receive,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            selectcolor=DARK_CARD,
            activebackground=DARK_BG,
            activeforeground=TEXT_COLOR,
            font=("Arial", 10, "bold")
        )
        self.net_recv_btn.pack(side="left")
        
        # --------------------------------------------------------------------
        # 설정 팝업창을 여는 토글 버튼
        # --------------------------------------------------------------------
        self.settings_outer_frame = tk.Frame(self.root, bg=DARK_BG)
        self.settings_outer_frame.pack(fill="x", padx=15, pady=(2, 6))

        self.settings_toggle_btn = tk.Button(
            self.settings_outer_frame,
            text="⚙️ 설정 (Settings) ..." if self.lang == "ko" else "⚙️ Settings ...",
            font=("Arial", 10, "bold"),
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            activebackground=DARK_CARD,
            activeforeground=TEXT_COLOR,
            relief="flat",
            pady=6,
            cursor="hand2",
            command=self.open_settings_popup
        )
        self.settings_toggle_btn.pack(fill="x")

        # --------------------------------------------------------------------
        # 탭 네비게이션 헤더 바 (⏱ 일반 간편 제어 vs 📅 고급 다중 스케줄러 vs 📋 동작 기록)
        # --------------------------------------------------------------------
        tab_nav_frame = tk.Frame(self.root, bg=DARK_BG, pady=5)
        tab_nav_frame.pack(fill="x", padx=15)
        
        self.btn_tab_control = tk.Button(
            tab_nav_frame,
            text="⏱ 간편 제어",
            font=("Arial", 10, "bold"),
            bg="#3b82f6",
            fg="white",
            relief="flat",
            pady=5,
            command=lambda: self.switch_tab("control")
        )
        self.btn_tab_control.pack(side="left", expand=True, fill="x", padx=2)
        
        self.btn_tab_scheduler = tk.Button(
            tab_nav_frame,
            text="📅 스케줄러",
            font=("Arial", 10, "bold"),
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            relief="flat",
            pady=5,
            command=lambda: self.switch_tab("scheduler")
        )
        self.btn_tab_scheduler.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_tab_history = tk.Button(
            tab_nav_frame,
            text="📋 동작 기록",
            font=("Arial", 10, "bold"),
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            relief="flat",
            pady=5,
            command=lambda: self.switch_tab("history")
        )
        self.btn_tab_history.pack(side="left", expand=True, fill="x", padx=2)

        # --------------------------------------------------------------------
        # 하단 푸터 영역 (회사 및 버전 정보) - 반드시 확장 프레임보다 먼저 side="bottom"으로 패킹
        # --------------------------------------------------------------------
        def open_cisnet_website(event=None):
            try:
                import webbrowser
                webbrowser.open("http://www.cisnet.co.kr/")
            except Exception:
                pass

        footer_frame = tk.Frame(self.root, bg=DARK_BG, pady=6, cursor="hand2")
        footer_frame.pack(side="bottom", fill="x", padx=15)
        footer_frame.bind("<Button-1>", open_cisnet_website)
        
        def open_blog_website(event=None):
            try:
                import webbrowser
                webbrowser.open("https://ahbiyoutvibe.blogspot.com/")
            except Exception:
                pass

        self.lbl_footer_info = tk.Label(
            footer_frame,
            text=f"소속: http://www.cisnet.co.kr/ | 개발자: AhBiYout | 버전: v{APP_VERSION}" if self.lang == "ko" else f"Organization: http://www.cisnet.co.kr/ | Developer: AhBiYout | Version: v{APP_VERSION}",
            font=("Arial", 10),
            fg=getattr(self, "current_subtext", CURRENT_SUBTEXT),
            bg=DARK_BG,
            cursor="hand2"
        )
        self.lbl_footer_info.pack()
        self.lbl_footer_info.bind("<Button-1>", open_cisnet_website)

        self.lbl_blog_info = tk.Label(
            footer_frame,
            text="구글블로그: https://ahbiyoutvibe.blogspot.com/" if self.lang == "ko" else "Google Blog: https://ahbiyoutvibe.blogspot.com/",
            font=("Arial", 10, "underline"),
            fg="#60a5fa",
            bg=DARK_BG,
            cursor="hand2"
        )
        self.lbl_blog_info.pack(pady=(2, 0))
        self.lbl_blog_info.bind("<Button-1>", open_blog_website)

        # --------------------------------------------------------------------
        # 콘텐츠 프레임 준비 (Control vs Scheduler vs History)
        # --------------------------------------------------------------------
        self.control_frame = tk.Frame(self.root, bg=DARK_BG)
        self.control_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        self.scheduler_frame = tk.Frame(self.root, bg=DARK_BG)
        # scheduler_frame은 탭 클릭 전까지 비활성화(pack_forget) 상태

        self.history_frame = tk.Frame(self.root, bg=DARK_BG)
        # history_frame은 탭 클릭 전까지 비활성화(pack_forget) 상태
        
        self.build_control_tab_ui()
        self.build_scheduler_tab_ui()
        self.build_history_tab_ui()

    def build_history_tab_ui(self):
        # Header description
        self.lbl_info = tk.Label(
            self.history_frame,
            text="📋 시스템 전원 제어 및 타이머 동작 기록" if self.lang == "ko" else "📋 Power Control & Timer Logs",
            font=("Arial", 10, "bold"),
            fg=self.current_subtext if hasattr(self, "current_subtext") else "#d1d5db",
            bg=DARK_BG,
            pady=5
        )
        self.lbl_info.pack(anchor="w")

        # Scrollable text log viewer
        log_container = tk.Frame(self.history_frame, bg=DARK_BG)
        log_container.pack(fill="both", expand=True, pady=5)

        scrollbar = tk.Scrollbar(log_container)
        scrollbar.pack(side="right", fill="y")

        self.log_text = tk.Text(
            log_container,
            wrap="word",
            yscrollcommand=scrollbar.set,
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            font=("Consolas", 10),
            relief="flat",
            padx=8,
            pady=8
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.log_text.yview)

        # Clear logs button
        self.btn_clear = tk.Button(
            self.history_frame,
            text="🗑️ 로그 기록 초기화" if self.lang == "ko" else "🗑️ Clear Logs",
            font=("Arial", 10, "bold"),
            bg="#ef4444",
            fg="white",
            relief="flat",
            pady=4,
            command=self.clear_logs
        )
        self.btn_clear.pack(fill="x", pady=(5, 0))

        # Initial load of logs
        self.refresh_history_log_view()

    def refresh_history_log_view(self):
        if not hasattr(self, "log_text") or not self.log_text.winfo_exists():
            return
            
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
                self.log_text.insert("1.0", content)
            except Exception:
                err_msg = "로그 데이터를 불러오는 중 오류가 발생했습니다.\n" if self.lang == "ko" else "An error occurred while loading log data.\n"
                self.log_text.insert("1.0", err_msg)
        else:
            no_logs_msg = "기록된 동작 로그가 아직 없습니다.\n" if self.lang == "ko" else "No action logs recorded yet.\n"
            self.log_text.insert("1.0", no_logs_msg)
            
        self.log_text.config(state="disabled")
        self.log_text.see(tk.END)

    def clear_logs(self):
        title = "로그 초기화" if self.lang == "ko" else "Clear Logs"
        msg = "정말로 저장된 모든 동작 기록 로그를 완전히 영구 삭제하시겠습니까?" if self.lang == "ko" else "Are you sure you want to permanently delete all action history logs?"
        if messagebox.askyesno(title, msg):
            try:
                if os.path.exists(HISTORY_FILE):
                    os.remove(HISTORY_FILE)
                log_msg = "동작 기록 로그가 사용자에 의해 수동으로 청소/초기화 되었습니다." if self.lang == "ko" else "Action history logs have been manually cleared by the user."
                self.log_event(log_msg, in_app_toast=True)
            except Exception as e:
                err_title = "오류" if self.lang == "ko" else "Error"
                err_msg = f"로그 초기화 실패: {e}" if self.lang == "ko" else f"Failed to clear logs: {e}"
                messagebox.showerror(err_title, err_msg)

    # --------------------------------------------------------------------
    # TAB 1: 일반 간역 제어 UI 설계구조
    # --------------------------------------------------------------------
    def build_control_tab_ui(self):
        # 모드 선택 탭 (5가지 전원 옵션)
        mode_frame = tk.Frame(self.control_frame, bg=DARK_BG, pady=5)
        mode_frame.pack(fill="x")
        
        self.mode_buttons = {}
        modes = [
            ("shutdown", "종료" if self.lang == "ko" else "Shut down"),
            ("restart", "재시작" if self.lang == "ko" else "Restart"),
            ("sleep", "절전" if self.lang == "ko" else "Sleep"),
            ("screenoff", "화면끔" if self.lang == "ko" else "Screen Off"),
            ("logout", "로그아웃" if self.lang == "ko" else "Log out"),
            ("alarm", "알람" if self.lang == "ko" else "Alarm")
        ]
        
        # Configure grid for mode_frame (2 rows, 3 cols)
        mode_frame.columnconfigure(0, weight=1)
        mode_frame.columnconfigure(1, weight=1)
        mode_frame.columnconfigure(2, weight=1)
        
        for i, (m_id, label) in enumerate(modes):
            btn = tk.Button(
                mode_frame,
                text=label,
                font=("Arial", 10, "bold"),
                bg=ACCENT_RED if m_id == "shutdown" else DARK_CARD,
                fg="white" if m_id == "shutdown" else TEXT_COLOR,
                relief="flat",
                pady=6,
                command=lambda m=m_id: self.set_mode(m)
            )
            row = i // 3
            col = i % 3
            btn.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            self.mode_buttons[m_id] = btn
        
        # 스케줄링 유형 토글 탭 (경과 시간 vs 특정 시각)
        type_frame = tk.Frame(self.control_frame, bg=DARK_BG, pady=5)
        type_frame.pack(fill="x")
        
        self.btn_type_timer = tk.Button(
            type_frame,
            text="⏳ 시간 타이머 (후)",
            font=("Arial", 10, "bold"),
            bg="#3b82f6",
            fg="white",
            relief="flat",
            pady=4,
            command=lambda: self.set_run_type("timer")
        )
        self.btn_type_timer.pack(side="left", expand=True, fill="x", padx=5)
        
        self.btn_type_schedule = tk.Button(
            type_frame,
            text="⏰ 특정 시각 예약 (정시)",
            font=("Arial", 10, "bold"),
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            relief="flat",
            pady=4,
            command=lambda: self.set_run_type("schedule")
        )
        self.btn_type_schedule.pack(side="left", expand=True, fill="x", padx=5)
        
        # 시간 표시 장치 (대형 디지털 계기판)
        self.display_frame = tk.Frame(self.control_frame, bg=DARK_CARD, bd=1, relief="solid")
        self.display_frame.pack(fill="x", pady=10)
        
        self.lbl_timer = tk.Label(
            self.display_frame, 
            text="00:30:00", 
            font=("Courier", 32, "bold"), 
            bg=DARK_CARD, 
            fg=ACCENT_BLUE
        )
        self.lbl_timer.pack(pady=10)
        
        # 시간 입력 컨트롤러 프레임
        self.input_parent_frame = tk.Frame(self.control_frame, bg=DARK_BG)
        self.input_parent_frame.pack(fill="x")
        
        # 입력 가이드 라벨
        self.lbl_input_guide = tk.Label(
            self.input_parent_frame, 
            text="[타이머] 지정된 시간/분/초 후 동작을 수행합니다.", 
            font=("Arial", 10, "bold"), 
            fg="#9ca3af", 
            bg=DARK_BG,
            anchor="w"
        )
        self.lbl_input_guide.pack(fill="x", pady=2)

        # 시간 입력 컨트롤러 (시 / 분 / 초) - 자식 프레임
        self.input_fields_frame = tk.Frame(self.input_parent_frame, bg=DARK_BG)
        self.input_fields_frame.pack(pady=5)
        
        self.lbl_field_1 = tk.Label(self.input_fields_frame, text="시" if self.lang == "ko" else "H", font=("Arial", 10), fg="#9ca3af", bg=DARK_BG)
        self.lbl_field_1.grid(row=0, column=0, padx=5)
        self.lbl_field_2 = tk.Label(self.input_fields_frame, text="분" if self.lang == "ko" else "M", font=("Arial", 10), fg="#9ca3af", bg=DARK_BG)
        self.lbl_field_2.grid(row=0, column=1, padx=5)
        self.lbl_field_3 = tk.Label(self.input_fields_frame, text="초" if self.lang == "ko" else "S", font=("Arial", 10), fg="#9ca3af", bg=DARK_BG)
        self.lbl_field_3.grid(row=0, column=2, padx=5)
        
        self.ent_h = tk.Entry(self.input_fields_frame, width=5, font=("Arial", 12, "bold"), justify="center")
        self.ent_h.insert(0, "0")
        self.ent_h.grid(row=1, column=0, padx=5)
        
        self.ent_m = tk.Entry(self.input_fields_frame, width=5, font=("Arial", 12, "bold"), justify="center")
        self.ent_m.insert(0, "30")
        self.ent_m.grid(row=1, column=1, padx=5)
        
        self.ent_s = tk.Entry(self.input_fields_frame, width=5, font=("Arial", 12, "bold"), justify="center")
        self.ent_s.insert(0, "0")
        self.ent_s.grid(row=1, column=2, padx=5)
        
        # 마우스 휠 및 방향키 상/하 상호작용 등록
        self.bind_spin_interactions(self.ent_h, "h")
        self.bind_spin_interactions(self.ent_m, "m")
        self.bind_spin_interactions(self.ent_s, "s")
        
        # 실행 컨트롤러 버튼들 (원클릭 가동)
        ctrl_frame = tk.Frame(self.control_frame, bg=DARK_BG, pady=10)
        ctrl_frame.pack(fill="x")
        
        self.btn_start = tk.Button(
            ctrl_frame, 
            text="▶ 타이머 시작" if self.lang == "ko" else "▶ Start Timer", 
            font=("Arial", 10, "bold"),
            bg=ACCENT_BLUE, 
            fg="white", 
            relief="flat",
            command=self.start_timer
        )
        self.btn_start.pack(side="left", expand=True, fill="x", padx=2)
        
        self.btn_reset = tk.Button(
            ctrl_frame, 
            text="🔄 리셋" if self.lang == "ko" else "🔄 Reset", 
            font=("Arial", 10, "bold"),
            bg=SECONDARY_BG if "SECONDARY_BG" in globals() else "#374151", 
            fg=TEXT_COLOR, 
            relief="flat",
            command=self.reset_timer
        )
        self.btn_reset.pack(side="left", expand=True, fill="x", padx=2)

        # 라이선스 및 약관 동의 고지서 라벨
        self.lbl_license_notice = tk.Label(
            self.control_frame,
            text="📄 라이선스 및 약관 동의 고지서" if self.lang == "ko" else "📄 License & Terms Agreement Notice",
            font=("Arial", 10, "underline"),
            fg="#9ca3af",
            bg=DARK_BG,
            cursor="hand2"
        )
        self.lbl_license_notice.pack(side="bottom", pady=(6, 2))
        self.lbl_license_notice.bind("<Button-1>", lambda event: self.click_license_notice())


    # --------------------------------------------------------------------
    # TAB 2: 고급 다중 스케줄러 UI 구조 및 동적 폼 구현
    # --------------------------------------------------------------------
    def build_scheduler_tab_ui(self):
        # 1. 새 스케줄 생성 폼 타이틀 및 축소
        add_form_title_frame = tk.Frame(self.scheduler_frame, bg=DARK_BG)
        add_form_title_frame.pack(fill="x", pady=(5, 5))
        
        self.lbl_add_title = tk.Label(add_form_title_frame, text="➕ 새 스케줄 규칙 등록기" if self.lang == "ko" else "➕ Add New Scheduler Rule", font=("Arial", 10, "bold"), fg=ACCENT_BLUE, bg=DARK_BG)
        self.lbl_add_title.pack(side="left")

        # 스케줄 등록 카드 폼 지정
        self.frm_add_rule = tk.LabelFrame(self.scheduler_frame, bg=DARK_CARD, text="규칙 생성 조건" if self.lang == "ko" else "Add Scheduler Rule", font=("Arial", 10, "bold"), fg="#9ca3af", bd=1, relief="solid")
        self.frm_add_rule.pack(fill="x", pady=5, padx=2)

        # 폼 내 데이터 수집 변수들
        self.var_rule_label = tk.StringVar(value="")
        self.var_rule_mode = tk.StringVar(value="shutdown")
        self.var_rule_type = tk.StringVar(value="daily")
        self.var_rule_force = tk.BooleanVar(value=True)
        self.var_rule_beep = tk.BooleanVar(value=True)

        # A. 스케줄 레이블 입력
        frm_name_header = tk.Frame(self.frm_add_rule, bg=DARK_CARD)
        frm_name_header.pack(fill="x", padx=10, pady=(5, 1))

        self.lbl_rule_name = tk.Label(frm_name_header, text="스케줄 이름 (메모):" if self.lang == "ko" else "Schedule Title (Memo):", font=("Arial", 10, "bold"), fg=TEXT_COLOR, bg=DARK_CARD)
        self.lbl_rule_name.pack(side="left")

        # 자주 사용하는 10개 제목 프리셋 선택 드롭다운
        preset_list_tab = POPULAR_SCHEDULE_TITLES_KO if self.lang == "ko" else POPULAR_SCHEDULE_TITLES_EN
        self.preset_placeholder_txt = "📋 자주 쓰는 제목 (10개)..." if self.lang == "ko" else "📋 Popular Titles (10)..."
        self.var_preset_title = tk.StringVar(value=self.preset_placeholder_txt)

        def on_tab_preset_selected(val):
            ph = "📋 자주 쓰는 제목 (10개)..." if self.lang == "ko" else "📋 Popular Titles (10)..."
            if val and val != ph:
                self.var_rule_label.set(val)
                self.clear_form_validation_errors()
                self.var_preset_title.set(ph)

        self.om_preset = tk.OptionMenu(
            frm_name_header,
            self.var_preset_title,
            self.preset_placeholder_txt,
            *preset_list_tab,
            command=on_tab_preset_selected
        )
        self.om_preset.config(
            font=("Arial", 9),
            bg=DARK_BG,
            fg="#93c5fd",
            activebackground="#2563eb",
            activeforeground="white",
            highlightthickness=0,
            bd=0,
            padx=4,
            pady=0,
            cursor="hand2"
        )
        self.om_preset["menu"].config(font=("Arial", 9), bg=DARK_CARD, fg=TEXT_COLOR)
        self.om_preset.pack(side="right")
        
        self.ent_rule_name = tk.Entry(self.frm_add_rule, textvariable=self.var_rule_label, bg=DARK_BG, fg=TEXT_COLOR, bd=0, insertbackground=TEXT_COLOR, highlightthickness=1, highlightcolor="#3b82f6", font=("Arial", 10))
        self.ent_rule_name.pack(fill="x", padx=10, pady=2, ipady=3)
        self.ent_rule_name.bind("<KeyRelease>", lambda event: self.clear_form_validation_errors())

        # B. 전원 행동 라디오 행
        self.lbl_rule_action = tk.Label(self.frm_add_rule, text="트리거 대기 전원 행동:" if self.lang == "ko" else "Action Mode to Trigger:", font=("Arial", 10, "bold"), fg=TEXT_COLOR, bg=DARK_CARD)
        self.lbl_rule_action.pack(anchor="w", padx=10, pady=(5, 1))

        self.rule_action_buttons_frame = tk.Frame(self.frm_add_rule, bg=DARK_CARD)
        self.rule_action_buttons_frame.pack(fill="x", padx=10, pady=2)
        
        self.action_sel_btn = {}
        action_options = [
            ("shutdown", "종료" if self.lang == "ko" else "Shut down"),
            ("restart", "재시동" if self.lang == "ko" else "Restart"),
            ("sleep", "절전" if self.lang == "ko" else "Sleep"),
            ("screenoff", "화면끔" if self.lang == "ko" else "Screen off"),
            ("logout", "아웃" if self.lang == "ko" else "Log out"),
            ("alarm", "알람" if self.lang == "ko" else "Alarm")
        ]
        
        for act_id, act_nm in action_options:
            btn = tk.Button(
                self.rule_action_buttons_frame,
                text=act_nm,
                font=("Arial", 10, "bold"),
                bg="#3b82f6" if act_id == "shutdown" else DARK_BG,
                fg="white" if act_id == "shutdown" else TEXT_COLOR,
                padx=5,
                pady=3,
                relief="flat",
                command=lambda opt=act_id: self.select_rule_form_action(opt)
            )
            btn.pack(side="left", expand=True, fill="x", padx=1)
            self.action_sel_btn[act_id] = btn

        # C. 반복 주기 플랜 선택 단추 행
        self.lbl_rule_type_title = tk.Label(self.frm_add_rule, text="반복 플랜 타입:" if self.lang == "ko" else "Interval Repeat Type:", font=("Arial", 10, "bold"), fg=TEXT_COLOR, bg=DARK_CARD)
        self.lbl_rule_type_title.pack(anchor="w", padx=10, pady=(5, 1))

        self.rule_type_buttons_frame = tk.Frame(self.frm_add_rule, bg=DARK_CARD)
        self.rule_type_buttons_frame.pack(fill="x", padx=10, pady=2)

        self.type_sel_btn = {}
        type_options = [
            ("once", "일회성 (Once)" if self.lang == "ko" else "Once Plan"),
            ("daily", "매일 (Daily)" if self.lang == "ko" else "Daily Plan"),
            ("weekly", "요일 반복 (Weekly)" if self.lang == "ko" else "Weekly Plan"),
            ("interval", "동작주기 (Interval)" if self.lang == "ko" else "Interval Cycle")
        ]

        for typ_id, typ_nm in type_options:
            btn = tk.Button(
                self.rule_type_buttons_frame,
                text=typ_nm,
                font=("Arial", 10, "bold"),
                bg="#3b82f6" if typ_id == "daily" else DARK_BG,
                fg="white" if typ_id == "daily" else TEXT_COLOR,
                padx=3,
                pady=4,
                relief="flat",
                command=lambda opt=typ_id: self.select_rule_form_type(opt)
            )
            btn.pack(side="left", expand=True, fill="x", padx=1, pady=1)
            self.type_sel_btn[typ_id] = btn

        # D. 가변 세부 주입부 프레임 (시간 선택 / 요일 / 또는 주기 값)
        self.frm_custom_args = tk.Frame(self.frm_add_rule, bg=DARK_CARD, pady=5)
        self.frm_custom_args.pack(fill="x", padx=10, pady=2)

        # 시간 지정 하이터틀
        self.lbl_time_helper = tk.Label(self.frm_custom_args, text="정밀 알람 격발 시각 (24시 형식):" if self.lang == "ko" else "Precise alarm trigger time (24h format):", font=("Arial", 10), fg="#9ca3af", bg=DARK_CARD)
        self.lbl_time_helper.pack(anchor="w")

        self.frm_time_selectors = tk.Frame(self.frm_custom_args, bg=DARK_CARD)
        self.frm_time_selectors.pack(anchor="w", pady=2)

        # 시간 / 분 콤보 옵션 설정 (Spinbox 나 Entry 대신 OptionMenus 로 충돌 및 입력 버그 예방)
        self.var_time_h = tk.StringVar(value="22")
        self.var_time_m = tk.StringVar(value="00")

        hours_opt = [f"{i:02d}" for i in range(24)]
        mins_opt = [f"{i:02d}" for i in range(60)]

        opt_h = tk.OptionMenu(self.frm_time_selectors, self.var_time_h, *hours_opt)
        opt_h.config(bg=DARK_BG, fg=TEXT_COLOR, relief="flat", highlightthickness=0, font=("Courier", 10, "bold"))
        opt_h["menu"].config(bg=DARK_CARD, fg=TEXT_COLOR)
        opt_h.pack(side="left")

        lbl_colon = tk.Label(self.frm_time_selectors, text=":", font=("Arial", 10, "bold"), fg=TEXT_COLOR, bg=DARK_CARD, padx=5)
        lbl_colon.pack(side="left")

        opt_m = tk.OptionMenu(self.frm_time_selectors, self.var_time_m, *mins_opt)
        opt_m.config(bg=DARK_BG, fg=TEXT_COLOR, relief="flat", highlightthickness=0, font=("Courier", 10, "bold"))
        opt_m["menu"].config(bg=DARK_CARD, fg=TEXT_COLOR)
        opt_m.pack(side="left")

        # 주중 요일 선택부 (스페셜 감시 - Weekly 선택시에만 grid 부착용)
        self.frm_weekly_days = tk.Frame(self.frm_custom_args, bg=DARK_CARD)
        self.day_checkbox_vars = []
        self.day_checkboxes = []
        day_names = ["일", "월", "화", "수", "목", "금", "토"]
        day_names_en = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for idx in range(7):
            d_nm = day_names[idx] if self.lang == "ko" else day_names_en[idx]
            d_var = tk.BooleanVar(value=True if idx in [1,2,3,4,5] else False) # 평일 기본 활성
            self.day_checkbox_vars.append(d_var)
            chk = tk.Checkbutton(
                self.frm_weekly_days, 
                text=d_nm, 
                variable=d_var, 
                bg=DARK_CARD, 
                fg=TEXT_COLOR, 
                selectcolor=DARK_BG,
                activebackground=DARK_CARD,
                activeforeground=TEXT_COLOR,
                font=("Arial", 10),
                command=self.clear_form_validation_errors
            )
            chk.pack(side="left", padx=2)
            self.day_checkboxes.append((chk, idx))

        # 주기 분 설정 엘리먼트 (Interval 선택 시에만 노출)
        self.frm_interval_entry = tk.Frame(self.frm_custom_args, bg=DARK_CARD)
        self.var_interval_mins = tk.IntVar(value=45)
        
        self.lbl_interval_txt_1 = tk.Label(self.frm_interval_entry, text="실행 발생 순환 간격:" if self.lang == "ko" else "Repeat interval cycle:", font=("Arial", 10), fg="#9ca3af", bg=DARK_CARD)
        self.lbl_interval_txt_1.pack(side="left")
        
        self.ent_interval = tk.Entry(self.frm_interval_entry, textvariable=self.var_interval_mins, width=5, bg=DARK_BG, fg=TEXT_COLOR, justify="center", bd=0, highlightthickness=1, highlightcolor="#3b82f6")
        self.ent_interval.pack(side="left", padx=5)
        self.ent_interval.bind("<KeyRelease>", lambda event: self.clear_form_validation_errors())
        
        self.lbl_interval_txt_2 = tk.Label(self.frm_interval_entry, text="분 마다 구동" if self.lang == "ko" else "minutes cycle", font=("Arial", 10, "bold"), fg=TEXT_COLOR, bg=DARK_CARD)
        self.lbl_interval_txt_2.pack(side="left")

        # E. 강제 종료 및 효과음 체크박스 라인
        self.flags_frame = tk.Frame(self.frm_add_rule, bg=DARK_CARD)
        self.flags_frame.pack(fill="x", padx=10, pady=5)

        self.cmd_chk_f = tk.Checkbutton(
            self.flags_frame, 
            text="파일/앱 강제 종료 (/f)" if self.lang == "ko" else "Force close apps (/f)", 
            variable=self.var_rule_force,
            bg=DARK_CARD, 
            fg=TEXT_COLOR,
            selectcolor=DARK_BG,
            activebackground=DARK_CARD,
            activeforeground=TEXT_COLOR,
            font=("Arial", 10)
        )
        self.cmd_chk_f.pack(side="left", expand=True)

        self.cmd_chk_beep = tk.Checkbutton(
            self.flags_frame, 
            text="1분 전 비프음 수동 경보" if self.lang == "ko" else "Audio warning 1min before", 
            variable=self.var_rule_beep,
            bg=DARK_CARD, 
            fg=TEXT_COLOR,
            selectcolor=DARK_BG,
            activebackground=DARK_CARD,
            activeforeground=TEXT_COLOR,
            font=("Arial", 10)
        )
        self.cmd_chk_beep.pack(side="left", expand=True)

        # ⚠️ 실시간 유효성 시각 피드백 레이블
        self.lbl_rule_error_msg = tk.Label(
            self.frm_add_rule,
            text="",
            font=("Arial", 10, "bold"),
            fg=ACCENT_RED,
            bg=DARK_CARD,
            wraplength=480,
            justify="center"
        )

        # F. 생성 전송 단추 및 수정 취소 단추 프레임
        self.frm_submit_actions = tk.Frame(self.frm_add_rule, bg=DARK_CARD)
        self.frm_submit_actions.pack(fill="x", padx=10, pady=(5, 10))

        self.btn_submit_rule = tk.Button(
            self.frm_submit_actions,
            text="스케줄 규칙 등록 및 감시 엔진에 합류" if self.lang == "ko" else "Register Rule & Start Background Sleep Guard",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            relief="flat",
            pady=6,
            command=self.submit_rule_form
        )
        self.btn_submit_rule.pack(side="left", expand=True, fill="x")

        self.btn_cancel_edit = tk.Button(
            self.frm_submit_actions,
            text="수정 취소" if self.lang == "ko" else "Cancel Edit",
            font=("Arial", 10, "bold"),
            bg="#4b5563",
            fg="white",
            relief="flat",
            padx=12,
            pady=6,
            command=self.cancel_rule_edit
        )

        # 2. 등록된 고급 스케줄 리스트 뷰 영역 (스케줄러 팝업창 열기에 위임하고 메인 화면에서는 팩하지 않고 제외)
        lbl_list_header = tk.Label(self.scheduler_frame, text="📋 등록된 규칙 및 상시 모니터링 현황", font=("Arial", 10, "bold"), fg="#9ca3af", bg=DARK_BG)
        # lbl_list_header.pack(anchor="w", pady=(5, 2))  # Excluded from main screen by user request

        # 스크롤 캔버스 적용된 스케줄 리스트박스 기믹
        self.rules_list_container = ScrollableFrame(self.scheduler_frame, bg=DARK_BG)
        # self.rules_list_container.pack(fill="both", expand=True, pady=2)  # Excluded from main screen by user request

        # 리스트 초기 갱신 투영
        self.render_rules_list()

    # --------------------------------------------------------------------
    # TAB 폼 인터랙션 서브 보조 컨트롤들 (Select Action, Select Type)
    # --------------------------------------------------------------------
    def select_rule_form_action(self, action_id):
        self.var_rule_mode.set(action_id)
        for act_id, btn in self.action_sel_btn.items():
            if act_id == action_id:
                btn.configure(bg="#3b82f6", fg="white")
            else:
                btn.configure(bg=DARK_BG, fg=TEXT_COLOR)
        self.clear_form_validation_errors()

    def select_rule_form_type(self, type_id):
        self.var_rule_type.set(type_id)
        for t_id, btn in self.type_sel_btn.items():
            if t_id == type_id:
                btn.configure(bg="#3b82f6", fg="white")
            else:
                btn.configure(bg=DARK_BG, fg=TEXT_COLOR)
        self.clear_form_validation_errors()

        # 요일 선택, 시간 선택, 주기 설정 보이며 사라지게 토글링 배치
        self.frm_time_selectors.pack_forget()
        self.frm_weekly_days.pack_forget()
        self.frm_interval_entry.pack_forget()

        if type_id in ["once", "daily"]:
            self.lbl_time_helper.configure(text="정밀 알람 격발 시각 (24시 형식):" if self.lang == "ko" else "Precise alarm trigger time (24h format):")
            self.frm_time_selectors.pack(anchor="w", pady=2)
        elif type_id == "weekly":
            self.lbl_time_helper.configure(text="정밀 알람 격발 시각 및 적용 요일 선택:" if self.lang == "ko" else "Select alarm time & active days of week:")
            self.frm_time_selectors.pack(anchor="w", pady=2)
            self.frm_weekly_days.pack(anchor="w", pady=2)
        elif type_id == "interval":
            self.lbl_time_helper.configure(text="반복 순환 루프 주기 지정:" if self.lang == "ko" else "Specify repeating loop interval:")
            self.frm_interval_entry.pack(anchor="w", pady=2)

    def clear_form_validation_errors(self):
        current_bg = getattr(self, "new_theme", {}).get("bg", DARK_BG)
        current_blue = getattr(self, "new_theme", {}).get("blue", "#3b82f6")
        
        if hasattr(self, "ent_rule_name") and self.ent_rule_name.winfo_exists():
            self.ent_rule_name.config(
                highlightcolor=current_blue,
                highlightbackground=current_bg,
                highlightthickness=1
            )
        if hasattr(self, "ent_interval") and self.ent_interval.winfo_exists():
            self.ent_interval.config(
                highlightcolor=current_blue,
                highlightbackground=current_bg,
                highlightthickness=1
            )
        if hasattr(self, "frm_weekly_days") and self.frm_weekly_days.winfo_exists():
            self.frm_weekly_days.config(highlightthickness=0)
            
        if hasattr(self, "lbl_rule_error_msg") and self.lbl_rule_error_msg.winfo_exists():
            self.lbl_rule_error_msg.config(text="")
            self.lbl_rule_error_msg.pack_forget()

    # --------------------------------------------------------------------
    # 스케줄 폼 복합 유효성 검사 및 데이터 저장 가동
    # --------------------------------------------------------------------
    def submit_rule_form(self):
        self.clear_form_validation_errors()
        
        label_txt = self.var_rule_label.get().strip()
        if not label_txt:
            warn_msg = "스케줄 규칙 이름(메모)을 상세히 입력해 주십시오." if self.lang == "ko" else "Please enter a schedule rule name (memo)."
            
            # 폼 내부 시각적 오류 피드백 구성
            self.ent_rule_name.config(
                highlightcolor=ACCENT_RED,
                highlightbackground=ACCENT_RED,
                highlightthickness=1.5
            )
            self.lbl_rule_error_msg.config(text=f"⚠️ {warn_msg}")
            self.lbl_rule_error_msg.pack(fill="x", padx=10, pady=(5, 5), before=self.frm_submit_actions)
            self.ent_rule_name.focus_set()
            
            warn_title = "불합격" if self.lang == "ko" else "Invalid Input"
            messagebox.showwarning(warn_title, warn_msg)
            return

        rule_type = self.var_rule_type.get()
        rule_mode = self.var_rule_mode.get()
        force_val = self.var_rule_force.get()
        beep_val = self.var_rule_beep.get()

        time_str = f"{self.var_time_h.get()}:{self.var_time_m.get()}"
        days_selected = []
        interval_val = 30

        if rule_type == "weekly":
            for idx, d_var in enumerate(self.day_checkbox_vars):
                if d_var.get():
                    days_selected.append(idx)
            if not days_selected:
                warn_msg = "하나 이상의 적용 요일을 선택하여 주십시오." if self.lang == "ko" else "Please select at least one active day of the week."
                
                # 요일 선택 프레임 테두리를 빨간색으로 시각적 강조
                self.frm_weekly_days.config(
                    highlightbackground=ACCENT_RED,
                    highlightcolor=ACCENT_RED,
                    highlightthickness=1
                )
                self.lbl_rule_error_msg.config(text=f"⚠️ {warn_msg}")
                self.lbl_rule_error_msg.pack(fill="x", padx=10, pady=(5, 5), before=self.frm_submit_actions)
                
                warn_title = "불합격" if self.lang == "ko" else "Invalid Input"
                messagebox.showwarning(warn_title, warn_msg)
                return
        elif rule_type == "interval":
            try:
                interval_val = int(self.var_interval_mins.get())
                if interval_val <= 0:
                    raise ValueError()
            except:
                warn_msg = "주기는 최소 1분 이상 설정하여야 합니다." if self.lang == "ko" else "Cycle interval must be at least 1 minute."
                
                # 주기 입력창 테두리를 빨간색으로 시각적 강조
                self.ent_interval.config(
                    highlightcolor=ACCENT_RED,
                    highlightbackground=ACCENT_RED,
                    highlightthickness=1.5
                )
                self.lbl_rule_error_msg.config(text=f"⚠️ {warn_msg}")
                self.lbl_rule_error_msg.pack(fill="x", padx=10, pady=(5, 5), before=self.frm_submit_actions)
                self.ent_interval.focus_set()
                
                warn_title = "불합격" if self.lang == "ko" else "Invalid Input"
                messagebox.showwarning(warn_title, warn_msg)
                return

        if hasattr(self, "editing_rule_id") and self.editing_rule_id:
            for rule in self.rules:
                if rule.get("id") == self.editing_rule_id:
                    rule["label"] = label_txt
                    rule["type"] = rule_type
                    rule["mode"] = rule_mode
                    rule["time"] = time_str if rule_type != "interval" else ""
                    rule["days"] = days_selected if rule_type == "weekly" else []
                    rule["interval_minutes"] = interval_val if rule_type == "interval" else 0
                    rule["force_close"] = force_val
                    rule["warning_beep"] = beep_val
                    break
            self.save_rules()
            type_lbls = {"once": "일회성", "daily": "매일", "weekly": "요일반복", "interval": "주기순환"} if self.lang == "ko" else {"once": "Once", "daily": "Daily", "weekly": "Weekly", "interval": "Interval"}
            type_lbl_str = type_lbls.get(rule_type, rule_type)
            log_msg = f"스케줄러 규칙 수정 완료: [{label_txt}] ({type_lbl_str}, {self.get_mode_label(rule_mode)})" if self.lang == "ko" else f"Scheduler rule updated: [{label_txt}] ({type_lbl_str}, {self.get_mode_label(rule_mode)})"
            self.log_event(log_msg, in_app_toast=True)
            self.cancel_rule_edit()
            self.render_rules_list()
            return

        new_rule = {
            "id": f"rule-{int(datetime.datetime.now().timestamp() * 1000)}",
            "label": label_txt,
            "type": rule_type,
            "mode": rule_mode,
            "time": time_str if rule_type != "interval" else "",
            "days": days_selected if rule_type == "weekly" else [],
            "interval_minutes": interval_val if rule_type == "interval" else 0,
            "force_close": force_val,
            "warning_beep": beep_val,
            "is_active": True,
            "created_at": datetime.datetime.now().isoformat(),
            "last_executed": ""
        }

        self.rules.append(new_rule)
        self.save_rules()
        type_lbls = {"once": "일회성", "daily": "매일", "weekly": "요일반복", "interval": "주기순환"} if self.lang == "ko" else {"once": "Once", "daily": "Daily", "weekly": "Weekly", "interval": "Interval"}
        type_lbl_str = type_lbls.get(rule_type, rule_type)
        log_msg = f"새 스케줄러 규칙 생성 완료: [{label_txt}] ({type_lbl_str}, {self.get_mode_label(rule_mode)})" if self.lang == "ko" else f"New scheduler rule created: [{label_txt}] ({type_lbl_str}, {self.get_mode_label(rule_mode)})"
        self.log_event(log_msg, in_app_toast=True)
        
        # 폼 상태 초기화
        self.var_rule_label.set("")
        self.ent_rule_name.delete(0, tk.END)
        self.clear_form_validation_errors()
        self.render_rules_list()

    def start_rule_edit(self, rule):
        self.clear_form_validation_errors()
        self.editing_rule_id = rule.get("id")
        self.var_rule_label.set(rule.get("label", ""))
        self.select_rule_form_action(rule.get("mode", "sleep"))
        self.select_rule_form_type(rule.get("type", "daily"))
        self.var_rule_force.set(rule.get("force_close", True))
        self.var_rule_beep.set(rule.get("warning_beep", True))
        
        r_type = rule.get("type", "daily")
        if r_type != "interval":
            time_str = rule.get("time", "22:00")
            if ":" in time_str:
                h, m = time_str.split(":")
                self.var_time_h.set(h)
                self.var_time_m.set(m)
        
        if r_type == "weekly":
            allowed_days = rule.get("days", [])
            for idx, d_var in enumerate(self.day_checkbox_vars):
                d_var.set(idx in allowed_days)
                 
        if r_type == "interval":
            self.var_interval_mins.set(rule.get("interval_minutes", 45))
            
        self.btn_cancel_edit.pack(side="right", padx=(5, 0))
        btn_submit_text = "스케줄 규칙 수정 반영하기" if self.lang == "ko" else "Update Rules & Save Modifications"
        self.btn_submit_rule.configure(text=btn_submit_text, bg="#8b5cf6")
        frm_add_text = f"규칙 수정 중: {rule.get('label')[:15]}" if self.lang == "ko" else f"Editing Rule: {rule.get('label')[:15]}"
        self.frm_add_rule.configure(text=frm_add_text)

        # 메인 규칙스케줄러 창이 앞으로 나오고 수정 내용이 보이도록 처리
        self.switch_tab("scheduler")
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass
            
        if hasattr(self, "popup_window") and self.popup_window and self.popup_window.winfo_exists():
            try:
                self.popup_window.withdraw()
            except Exception:
                pass

    def cancel_rule_edit(self):
        self.clear_form_validation_errors()
        self.editing_rule_id = None
        self.var_rule_label.set("")
        self.ent_rule_name.delete(0, tk.END)
        frm_add_text = "규칙 생성 조건" if self.lang == "ko" else "Add Scheduler Rule"
        self.frm_add_rule.configure(text=frm_add_text)
        
        self.select_rule_form_action("sleep")
        self.select_rule_form_type("daily")
        self.var_rule_force.set(True)
        self.var_rule_beep.set(True)
        self.var_time_h.set("22")
        self.var_time_m.set("00")
        for idx, d_var in enumerate(self.day_checkbox_vars):
            d_var.set(True if idx in [1,2,3,4,5] else False)
            
        self.var_interval_mins.set(45)
        self.btn_cancel_edit.pack_forget()
        btn_submit_normal = "스케줄 규칙 등록 및 감시 엔진에 합류" if self.lang == "ko" else "Register Rule & Start Background Sleep Guard"
        self.btn_submit_rule.configure(text=btn_submit_normal, bg="#2563eb")

        # 스케줄 편집이 완료되거나 취소되었으므로, 숨겼던 팝업창을 다시 자동으로 복원해 편의성 극대화
        if hasattr(self, "popup_window") and self.popup_window and self.popup_window.winfo_exists():
            try:
                self.popup_window.deiconify()
                self.popup_window.lift()
                self.popup_window.focus_force()
            except Exception:
                pass

    # --------------------------------------------------------------------
    # 고급 스케줄 규칙들을 동적으로 카드로 그려 스크롤 상자에 렌더링
    # --------------------------------------------------------------------
    def render_rules_list(self):
        # 기존 렌더링 카드들 제거
        containers = [self.rules_list_container]
        if hasattr(self, "popup_rules_list_container") and self.popup_rules_list_container and self.popup_rules_list_container.winfo_exists():
            containers.append(self.popup_rules_list_container)

        for container in list(containers):
            try:
                for widget in container.scrollable_frame.winfo_children():
                    widget.destroy()
            except Exception:
                continue

            if not self.rules:
                empty_txt = (
                    "활성화된 예약 규칙이 존재하지 않습니다.\n상단 폼을 채워 신규 배치 감시를 합류시키세요."
                    if self.lang == "ko"
                    else "No active scheduled rules are registered.\nFill in the form above to add a new rule."
                )
                lbl_empty = tk.Label(
                    container.scrollable_frame, 
                    text=empty_txt, 
                    font=("Arial", 10, "italic"), 
                    fg="#6b7280", 
                    bg=DARK_BG,
                    pady=40,
                    width=45 # 강제 넓이 보증
                )
                lbl_empty.pack(fill="x", expand=True)
                continue

            # 동적 카드 레이아웃 지휘
            for r_item in self.rules:
                card = tk.Frame(container.scrollable_frame, bg=DARK_CARD, bd=1, relief="solid")
                card.pack(fill="x", padx=5, pady=4)

                # 제목 가이드
                r_id = r_item.get("id")
                r_label = r_item.get("label")
                r_type = r_item.get("type")
                r_mode = r_item.get("mode")
                is_active = r_item.get("is_active", True)
                
                mode_lbl = self.get_mode_label(r_mode)
                type_lbl = ""
                details_lbl = ""
                
                if r_type == "once":
                    type_lbl = "일회성" if self.lang == "ko" else "Once"
                    details_lbl = f"기동: {r_item.get('time')} 정각" if self.lang == "ko" else f"Trigger: {r_item.get('time')}"
                elif r_type == "daily":
                    type_lbl = "매일" if self.lang == "ko" else "Daily"
                    details_lbl = f"기동: 주간 {r_item.get('time')} 정시 감시" if self.lang == "ko" else f"Trigger: Daily at {r_item.get('time')}"
                elif r_type == "weekly":
                    type_lbl = "요일반복" if self.lang == "ko" else "Weekly"
                    days_lbl = self.get_days_label(r_item.get("days", []))
                    details_lbl = f"기동: {r_item.get('time')} ({days_lbl})" if self.lang == "ko" else f"Trigger: {r_item.get('time')} ({days_lbl})"
                elif r_type == "interval":
                    type_lbl = "주기순환" if self.lang == "ko" else "Interval"
                    details_lbl = f"구동: 매 {r_item.get('interval_minutes')} 분 간격" if self.lang == "ko" else f"Run: Every {r_item.get('interval_minutes')}m interval"

                # 1라인 오프너 메인 데이터
                title_line = tk.Frame(card, bg=DARK_CARD)
                title_line.pack(fill="x", padx=8, pady=(4, 2))

                # 타입 뱃지
                lbl_badge = tk.Label(title_line, text=type_lbl, font=("Arial", 10, "bold"), fg="#3b82f6", bg=DARK_BG, padx=4, pady=1)
                lbl_badge.pack(side="left")

                # 전원 행 뱃지
                lbl_mode_badge = tk.Label(title_line, text=mode_lbl, font=("Arial", 10, "bold"), fg=ACCENT_RED if r_mode == "shutdown" else "#10b981", bg=DARK_BG, padx=4, pady=1)
                lbl_mode_badge.pack(side="left", padx=4)

                # 상태 제어 단추 (켜기/끄기 토글 구현)
                if self.lang == "ko":
                    status_txt = "🟢 작동중" if is_active else "🔴 중단"
                else:
                    status_txt = "🟢 Active" if is_active else "🔴 Paused"
                status_col = "#10b981" if is_active else "#ef4444"
                btn_status = tk.Button(
                    title_line,
                    text=status_txt,
                    font=("Arial", 10, "bold"),
                    bg=DARK_BG,
                    fg=status_col,
                    relief="flat",
                    command=lambda rid=r_id: self.toggle_rule_status(rid)
                )
                btn_status.pack(side="right")

                # 삭제 단추 추가
                btn_del_txt = "❌ 삭제" if self.lang == "ko" else "❌ Delete"
                btn_del = tk.Button(
                    title_line,
                    text=btn_del_txt,
                    font=("Arial", 10, "bold"),
                    bg=ACCENT_RED,
                    fg="white",
                    padx=6,
                    pady=2,
                    relief="flat",
                    command=lambda rid=r_id: self.delete_rule_by_id(rid)
                )
                btn_del.pack(side="right", padx=3)

                # 수정 단추 추가
                btn_edit_txt = "✏️ 수정" if self.lang == "ko" else "✏️ Edit"
                btn_edit = tk.Button(
                    title_line,
                    text=btn_edit_txt,
                    font=("Arial", 10, "bold"),
                    bg=ACCENT_BLUE,
                    fg="white",
                    padx=6,
                    pady=2,
                    relief="flat",
                    command=lambda ritem=r_item: self.start_rule_edit(ritem)
                )
                btn_edit.pack(side="right", padx=3)

                # 2라인 규칙 이름
                lbl_r_title = tk.Label(card, text=r_label, font=("Arial", 10, "bold"), fg=TEXT_COLOR, bg=DARK_CARD, anchor="w")
                lbl_r_title.pack(fill="x", padx=10, pady=(2, 1))

                # 3라인 지연상태
                lbl_r_desc = tk.Label(card, text=details_lbl, font=("Arial", 10), fg="#9ca3af", bg=DARK_CARD, anchor="w")
                lbl_r_desc.pack(fill="x", padx=10, pady=1)

                # 4라인 실시간 카운트다운 잔여시간
                countdown_standby = "[대기열 대기 중]" if self.lang == "ko" else "[Standing by in Queue]"
                lbl_r_countdown = tk.Label(card, text=countdown_standby, font=("Courier", 10, "bold"), fg=ACCENT_BLUE, bg=DARK_CARD, anchor="e")
                lbl_r_countdown.pack(fill="x", padx=10, pady=(1, 4))
                
                # 다이내믹 바인딩 참조용으로 저장 (메인 스레드 ticks 가동용)
                card.countdown_label = lbl_r_countdown
                card.rule_data = r_item

        for container in list(containers):
            if hasattr(container, "bind_children_mousewheel"):
                container.bind_children_mousewheel()

    def get_days_label(self, days):
        if self.lang == "ko":
            if not days:
                return "요일 미지정"
            day_names = ["일", "월", "화", "수", "목", "금", "토"]
            if len(days) == 7:
                return "매일"
            if len(days) == 5 and 0 not in days and 6 not in days:
                return "평일(월-금)"
            return ",".join([day_names[d] for d in days])
        else:
            if not days:
                return "Days unset"
            day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            if len(days) == 7:
                return "Everyday"
            if len(days) == 5 and 0 not in days and 6 not in days:
                return "Weekdays (Mon-Fri)"
            return ",".join([day_names[d] for d in days])

    def toggle_rule_status(self, rule_id):
        for r in self.rules:
            if r.get("id") == rule_id:
                curr = r.get("is_active", True)
                r["is_active"] = not curr
                lbl = r.get('label', '이름 없음' if self.lang == 'ko' else 'Unnamed')
                log_msg = f"스케줄러 규칙 '{lbl}' 활성화 상태 변경: {curr} -> {r['is_active']}" if self.lang == "ko" else f"Scheduler rule '{lbl}' active state changed: {curr} -> {r['is_active']}"
                self.log_event(log_msg)
                break
        self.save_rules()
        self.render_rules_list()

    def delete_rule_by_id(self, rule_id):
        removed_rule_name = "이름 없음" if self.lang == "ko" else "Unnamed"
        for r in self.rules:
            if r.get("id") == rule_id:
                removed_rule_name = r.get("label", "이름 없음" if self.lang == "ko" else "Unnamed")
                break
        self.rules = [r for r in self.rules if r.get("id") != rule_id]
        log_msg = f"스케줄러 규칙 제거 완료: '{removed_rule_name}'" if self.lang == "ko" else f"Scheduler rule removed successfully: '{removed_rule_name}'"
        self.log_event(log_msg, in_app_toast=True)
        self.save_rules()
        self.render_rules_list()

    # --------------------------------------------------------------------
    # 탭 네비게이션 트리거
    # --------------------------------------------------------------------
    def switch_tab(self, tab):
        self.active_tab = tab
        if tab == "control":
            self.btn_tab_control.configure(bg=ACCENT_BLUE, fg="white")
            self.btn_tab_scheduler.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            self.btn_tab_history.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            self.scheduler_frame.pack_forget()
            self.history_frame.pack_forget()
            self.control_frame.pack(fill="both", expand=True, padx=15, pady=5)
        elif tab == "scheduler":
            self.btn_tab_control.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            self.btn_tab_scheduler.configure(bg=ACCENT_BLUE, fg="white")
            self.btn_tab_history.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            self.control_frame.pack_forget()
            self.history_frame.pack_forget()
            self.scheduler_frame.pack(fill="both", expand=True, padx=15, pady=5)
        else: # "history"
            self.btn_tab_control.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            self.btn_tab_scheduler.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            self.btn_tab_history.configure(bg=ACCENT_BLUE, fg="white")
            self.control_frame.pack_forget()
            self.scheduler_frame.pack_forget()
            self.history_frame.pack(fill="both", expand=True, padx=15, pady=5)
            self.refresh_history_log_view()

        try:
            self.root.update_idletasks()
            req_w = self.root.winfo_reqwidth()
            req_h = self.root.winfo_reqheight()
            cur_w = self.root.winfo_width()
            cur_h = self.root.winfo_height()
            min_w = max(500, req_w)
            min_h = max(660, req_h)
            self.root.minsize(min_w, min_h)
            if cur_w < min_w or cur_h < min_h:
                self.root.geometry(f"{max(cur_w, min_w)}x{max(cur_h, min_h)}")
        except Exception:
            pass

    # --------------------------------------------------------------------
    # 2.5 정각 알림(Hourly Chime) 및 오늘 예약 작업 브리핑(Startup Briefing)
    # --------------------------------------------------------------------
    def trigger_hourly_chime(self, hour):
        """매 시 정각 4음계 웨스트민스터 차임벨 사운드 및 알림 송출"""
        def _play_tones():
            try:
                import winsound
                # 4-note Westminster melodic chime: E5(659Hz), C5(523Hz), D5(587Hz), G4(392Hz)
                melody = [(659, 140), (523, 140), (587, 140), (392, 280)]
                for freq, duration in melody:
                    winsound.Beep(freq, duration)
            except Exception:
                try:
                    self.root.bell()
                except Exception:
                    pass
                    
        threading.Thread(target=_play_tones, daemon=True).start()
        msg = f"🔔 [정각 알림] 현재 시각 {hour:02d}:00 입니다." if self.lang == "ko" else f"🔔 [Hourly Chime] It is now {hour:02d}:00."
        self.log_event(msg, in_app_toast=True)

    def check_and_show_startup_today_tasks(self):
        """앱 시작 시 오늘 실행될 예약 작업이 있는지 검사하고 브리핑 팝업을 표시합니다."""
        if not self.startup_alert_enabled.get():
            return
        today_tasks = self.get_today_active_tasks()
        if not today_tasks:
            return
        self.show_startup_today_tasks_modal(today_tasks)

    def get_today_active_tasks(self):
        """오늘 실행 예정인 모든 활성 스케줄 목록을 수집합니다."""
        now = datetime.datetime.now()
        cur_day = (now.weekday() + 1) % 7 # 0=일요일, 1=월요일 ~ 6=토요일
        today_str = now.strftime("%Y-%m-%d")
        
        today_tasks = []
        for r in getattr(self, "rules", []):
            if not r.get("is_active", True):
                continue
            r_type = r.get("type", "daily")
            if r_type == "daily":
                today_tasks.append(r)
            elif r_type == "weekly":
                if cur_day in r.get("days", []):
                    today_tasks.append(r)
            elif r_type == "once":
                if r.get("date") == today_str:
                    today_tasks.append(r)
            elif r_type == "interval":
                today_tasks.append(r)
        return today_tasks

    def show_startup_today_tasks_modal(self, tasks, is_preview=False):
        """시작 시 오늘 예약 작업 안내 브리핑 팝업 - 시스템 트레이(우측 하단) 알림창 방식으로 표시 (5초 후 자동 닫힘 & 메인창 비활성 유지)"""
        if hasattr(self, "startup_modal") and self.startup_modal and self.startup_modal.winfo_exists():
            self.startup_modal.lift()
            return

        # 현재 메인 윈도우의 가시성 상태 정밀 감지
        is_main_visible = False
        try:
            if self.root.winfo_exists() and self.root.state() != "withdrawn" and self.root.winfo_viewable():
                is_main_visible = True
        except Exception:
            is_main_visible = False

        # [버그 수정]: 사용자가 설정창에서 미리보기(테스트)를 눌렀거나 메인창이 이미 노출되어 있을 때는 절대 메인창을 withdraw하지 않음
        if not is_preview and not is_main_visible and getattr(self, "is_boot_startup", False):
            try:
                self.root.withdraw()
            except Exception:
                pass
            # 부팅 백그라운드 트레이 모드인 경우 시스템 트레이 아이콘이 확실히 가동되도록 보장
            if P_TRAY_AVAILABLE and self.tray_icon is None:
                self.start_tray_icon()
            
        self.startup_modal = tk.Toplevel(self.root)
        self.startup_modal.title("📅 오늘 예약 작업 알림 (시스템 트레이)" if self.lang == "ko" else "📅 Today's Scheduled Tasks (System Tray)")
        self.startup_modal.configure(bg=DARK_BG)
        # 메인창이 숨겨져 있거나 부팅 시 트레이로 시작한 경우에도 독립적으로 상단에 표시
        self.startup_modal.attributes("-topmost", True)
        
        # 시스템 트레이 알림창 크기 및 위치 (우측 하단 작업표시줄 위 배치)
        sw = self.startup_modal.winfo_screenwidth()
        sh = self.startup_modal.winfo_screenheight()
        w = 430
        h = min(440, max(260, 160 + len(tasks) * 65))
        rx = max(10, sw - w - 24)
        ry = max(10, sh - h - 56)
        self.startup_modal.geometry(f"{w}x{h}+{rx}+{ry}")
        
        # 안전한 모달 닫기 핸들러 (메인창, 설정창 및 시스템 트레이 아이콘 소멸 방지)
        def safe_close_modal():
            if hasattr(self, "_startup_modal_timer_id") and self._startup_modal_timer_id:
                try:
                    self.root.after_cancel(self._startup_modal_timer_id)
                except Exception:
                    pass
                self._startup_modal_timer_id = None
            if hasattr(self, "startup_modal") and self.startup_modal and self.startup_modal.winfo_exists():
                try:
                    self.startup_modal.destroy()
                except Exception:
                    pass
                self.startup_modal = None

            # 메인창 복원 및 가시성 안전성 검증
            if is_preview or is_main_visible:
                try:
                    if self.root.state() == "withdrawn":
                        self.root.deiconify()
                except Exception:
                    pass
            else:
                # 부팅 백그라운드 트레이 상태 유지 중인 경우 트레이 아이콘 활성 상태 확인
                if P_TRAY_AVAILABLE and self.tray_icon is None:
                    self.start_tray_icon()

            # 상단 고정 미니창(컴팩트 위젯) 동기화
            if self.always_on_top.get():
                self.sync_always_on_top_mini_win()

        self.startup_modal.protocol("WM_DELETE_WINDOW", safe_close_modal)
        
        # 1. 상단 포인트 악센트 바 (시스템 트레이 알림 시각적 강조)
        accent_bar = tk.Frame(self.startup_modal, bg=ACCENT_BLUE, height=4)
        accent_bar.pack(fill="x", side="top")
        
        # 2. 헤더 영역 (타이틀, 일자, 트레이 배지 및 우측 상단 닫기 [✕] 버튼)
        frm_hdr = tk.Frame(self.startup_modal, bg=DARK_BG)
        frm_hdr.pack(fill="x", padx=14, pady=(10, 6))
        
        f_title_row = tk.Frame(frm_hdr, bg=DARK_BG)
        f_title_row.pack(fill="x")
        
        now = datetime.datetime.now()
        day_names_ko = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"]
        cur_day_ko = day_names_ko[(now.weekday() + 1) % 7]
        dt_title = f"📅 오늘 예약 작업 알림" if self.lang == "ko" else "📅 Today's Scheduled Tasks"
        
        f_title_left = tk.Frame(f_title_row, bg=DARK_BG)
        f_title_left.pack(side="left", fill="x", expand=True)
        
        tk.Label(
            f_title_left, 
            text=f"{dt_title}  •  {now.strftime('%Y-%m-%d')} ({cur_day_ko if self.lang == 'ko' else now.strftime('%a')})", 
            font=("Arial", 10, "bold"), 
            fg=ACCENT_BLUE, 
            bg=DARK_BG
        ).pack(anchor="w")
        
        # 우측 상단 컴팩트 닫기 [✕] 버튼
        btn_close_top = tk.Button(
            f_title_row,
            text="✕",
            font=("Arial", 10, "bold"),
            bg=DARK_BG,
            fg="#9ca3af",
            activebackground=DARK_CARD,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=5,
            pady=0,
            cursor="hand2",
            command=safe_close_modal
        )
        btn_close_top.pack(side="right")
        
        sub_text = f"📥 시스템 트레이 브리핑: 오늘 총 {len(tasks)}개의 예약 작업이 대기 중입니다." if self.lang == "ko" else f"📥 Tray Briefing: {len(tasks)} scheduled task(s) active for today."
        tk.Label(frm_hdr, text=sub_text, font=("Arial", 10), fg=getattr(self, "current_subtext", "#9ca3af"), bg=DARK_BG).pack(anchor="w", pady=(3, 0))
        
        # 3. 예약 작업 카드 스크롤 목록
        scroll = ScrollableFrame(self.startup_modal, bg=DARK_BG)
        scroll.pack(fill="both", expand=True, padx=12, pady=4)
        
        mode_colors = {
            "shutdown": ACCENT_RED,
            "restart": ACCENT_BLUE,
            "sleep": "#8b5cf6",
            "screenoff": "#06b6d4",
            "logout": "#d97706",
            "alarm": "#10b981"
        }
        
        for t in tasks:
            card = tk.Frame(scroll.scrollable_frame, bg=DARK_CARD, bd=1, relief="solid", highlightthickness=0)
            card.pack(fill="x", pady=3, padx=2)
            
            m_mode = t.get("mode", "shutdown")
            m_color = mode_colors.get(m_mode, ACCENT_BLUE)
            m_label = self.get_mode_label(m_mode)
            
            f_top = tk.Frame(card, bg=DARK_CARD)
            f_top.pack(fill="x", padx=8, pady=(5, 2))
            
            tk.Label(f_top, text=f"[{m_label}]", font=("Arial", 10, "bold"), fg=m_color, bg=DARK_CARD).pack(side="left")
            
            t_type = t.get("type", "daily")
            if t_type == "interval":
                t_time = f"매 {t.get('interval', 45)}분" if self.lang == "ko" else f"Every {t.get('interval', 45)}m"
            else:
                t_time = t.get("time", "--:--")
            tk.Label(f_top, text=f"⏰ {t_time}", font=("Arial", 10, "bold"), fg=TEXT_COLOR, bg=DARK_CARD).pack(side="right")
            
            lbl_name = t.get("label", "") or ("(이름 없음)" if self.lang == "ko" else "(No memo)")
            tk.Label(card, text=lbl_name, font=("Arial", 10), fg=getattr(self, "current_subtext", "#9ca3af"), bg=DARK_CARD, anchor="w").pack(fill="x", padx=8, pady=(0, 5))
            
        # 4. 하단 버튼 바 (스케줄러 열기, 5초 자동 닫힘 타이머 표시 버튼)
        frm_b = tk.Frame(self.startup_modal, bg=DARK_BG)
        frm_b.pack(fill="x", padx=14, pady=8)
        
        def open_and_close():
            if hasattr(self, "_startup_modal_timer_id") and self._startup_modal_timer_id:
                try:
                    self.root.after_cancel(self._startup_modal_timer_id)
                except Exception:
                    pass
            self.startup_modal.destroy()
            if not self.root.winfo_viewable():
                self.restore_from_tray()
            self.open_advanced_scheduler()
            
        btn_sched = tk.Button(
            frm_b,
            text="📅 스케줄러 열기" if self.lang == "ko" else "📅 Open Scheduler",
            font=("Arial", 10, "bold"),
            bg=DARK_CARD,
            fg=ACCENT_BLUE,
            relief="flat",
            pady=5,
            cursor="hand2",
            command=open_and_close
        )
        btn_sched.pack(side="left", fill="x", expand=True, padx=(0, 4))
        
        btn_ok = tk.Button(
            frm_b,
            text="닫기 (5초)" if self.lang == "ko" else "Close (5s)",
            font=("Arial", 10, "bold"),
            bg=ACCENT_BLUE,
            fg="white",
            relief="flat",
            pady=5,
            cursor="hand2",
            command=safe_close_modal
        )
        btn_ok.pack(side="right", fill="x", expand=True, padx=(4, 0))
        
        # 5. 시스템 트레이 우측 하단 도킹 정렬 및 페이드 인 애니메이션
        try:
            self.startup_modal.update_idletasks()
            req_h = min(460, max(240, self.startup_modal.winfo_reqheight() + 10))
            ry_final = max(10, sh - req_h - 56)
            self.startup_modal.geometry(f"{w}x{req_h}+{rx}+{ry_final}")
            
            # 부드러운 페이드인
            self.startup_modal.attributes("-alpha", 0.0)
            def fade_in_tray(alpha=0.0):
                if not hasattr(self, "startup_modal") or not self.startup_modal or not self.startup_modal.winfo_exists():
                    return
                if alpha < 0.98:
                    alpha += 0.18
                    self.startup_modal.attributes("-alpha", alpha)
                    self.root.after(20, lambda: fade_in_tray(alpha))
                else:
                    self.startup_modal.attributes("-alpha", 0.98)
            fade_in_tray(0.0)
        except Exception:
            pass

        # 6. 5초 후 자동 닫기 카운트다운 루프 (사용자 조작 없을 시 부드럽게 자동 소멸)
        countdown_secs = [5]
        def update_auto_close():
            if not hasattr(self, "startup_modal") or not self.startup_modal or not self.startup_modal.winfo_exists():
                return
            if countdown_secs[0] <= 1:
                safe_close_modal()
            else:
                countdown_secs[0] -= 1
                try:
                    btn_text = f"닫기 ({countdown_secs[0]}초)" if self.lang == "ko" else f"Close ({countdown_secs[0]}s)"
                    btn_ok.configure(text=btn_text)
                    self._startup_modal_timer_id = self.root.after(1000, update_auto_close)
                except Exception:
                    pass

        self._startup_modal_timer_id = self.root.after(1000, update_auto_close)

    # --------------------------------------------------------------------
    # 3. 고급 스케줄러 1초 단위 실시간 무중단 검사 엔진 데몬 (Tick & Trigger)
    # --------------------------------------------------------------------
    def check_advanced_schedules(self):
        if not self.root:
            return
            
        now = datetime.datetime.now()
        
        # 만약 미니창(상단고정 창)이 활성화되어 있다면 (현재 시각 표시 등의 갱신을 위해) 매초 미니창 갱신
        if hasattr(self, "mini_win") and self.mini_win and self.mini_win.winfo_exists():
            self.update_mini_window()
            
        cur_h = now.hour
        cur_m = now.minute
        cur_s = now.second
        
        # 파이썬의 weekday(): 0=월, 6=일. 
        # 리액트와의 완벽한 동치성을 맞추기 위해 0=일요일, 1=월요일 ~ 6=토요일 구조 변환
        cur_day = (now.weekday() + 1) % 7 
        
        # 스케줄러 화면이 열려있거나 데이터를 가지고 있을 시 카운트다운 텍스트 일괄 갱신
        if self.scheduler_frame.winfo_manager() != "":
            self.update_scheduler_countdowns(now)

        # 순수 창작 SysPowerHook 세션 이벤트 실시간 감시 (화면 잠금/해제)
        if native_bridge and native_bridge.is_power_hook_loaded():
            while True:
                ev_data = native_bridge.get_next_session_event()
                if not ev_data:
                    break
                ev_type, _ = ev_data
                if ev_type == 7:  # WTS_SESSION_LOCK
                    self.log_event("🔒 [세션 보안] 화면 잠금(Win + L / 자리 비움)이 감지되었습니다." if self.lang == "ko" else "🔒 [Session Hook] Screen lock / Away detected.", in_app_toast=True)
                elif ev_type == 8:  # WTS_SESSION_UNLOCK
                    self.log_event("🔓 [세션 보안] 화면 잠금이 정상 해제되었습니다." if self.lang == "ko" else "🔓 [Session Hook] Screen unlocked.", in_app_toast=True)

        # 감시는 1분 단위로 바뀐 시점에 격발 (매초 검사 대신 1분 단위 감시로 CPU / IO 극적 절약)
        minute_changed = False
        if not hasattr(self, "last_checked_minute"):
            self.last_checked_minute = -1
            
        if self.last_checked_minute != cur_m:
            minute_changed = True
            self.last_checked_minute = cur_m
            
        if minute_changed:
            # 🔋 하드웨어 배터리 위험 수위(10% 이하) 감지
            if native_bridge and native_bridge.is_power_hook_loaded():
                if native_bridge.is_battery_critical(10):
                    pct = native_bridge.get_battery_percent()
                    self.log_event(f"⚠️ [하드웨어 배터리 경고] 배터리 잔량 {pct}% (위험 수위) 감지!" if self.lang == "ko" else f"⚠️ [Critical Battery] Level {pct}% detected!", in_app_toast=True)

            # 🔔 정각 알림 (Hourly Chime)
            if self.hourly_chime_enabled.get() and cur_m == 0:
                if not hasattr(self, "last_chime_hour") or self.last_chime_hour != cur_h:
                    self.last_chime_hour = cur_h
                    self.trigger_hourly_chime(cur_h)
            changed_state = False
            for r_item in self.rules:
                if not r_item.get("is_active", True):
                    continue
                    
                should_trigger = False
                rule_type = r_item.get("type", "daily")
                time_str = r_item.get("time", "")
                
                tgt_h, tgt_m = 0, 0
                if ":" in time_str:
                    try:
                        h_p, m_p = map(int, time_str.split(":"))
                        tgt_h, tgt_m = h_p, m_p
                    except:
                        pass
                
                if rule_type == "once":
                    if cur_h == tgt_h and cur_m == tgt_m:
                        should_trigger = True
                        r_item["is_active"] = False # 1회성이므로 즉시 감시 off
                        changed_state = True
                elif rule_type == "daily":
                    if cur_h == tgt_h and cur_m == tgt_m:
                        should_trigger = True
                elif rule_type == "weekly":
                    allowed_days = r_item.get("days", [])
                    if cur_day in allowed_days and cur_h == tgt_h and cur_m == tgt_m:
                        should_trigger = True
                elif rule_type == "interval":
                    try:
                        cr_dt = datetime.datetime.fromisoformat(r_item.get("created_at"))
                    except:
                        cr_dt = now
                    
                    diff_seconds = (now - cr_dt).total_seconds()
                    diff_minutes = int(diff_seconds // 60)
                    interval_val = r_item.get("interval_minutes", 30)
                    
                    if diff_minutes > 0 and diff_minutes % interval_val == 0:
                        should_trigger = True
                
                if should_trigger:
                    # 3. 유휴 시간 감지 조건 체크 (Idle Time Trigger)
                    if r_item.get("idle_only", False):
                        idle_thresh_sec = int(r_item.get("idle_minutes", 15)) * 60
                        curr_idle = self.get_system_idle_seconds()
                        if curr_idle < idle_thresh_sec:
                            # 사용자가 현재 PC 사용 중이므로 이번 분에는 실행 대기
                            self.log_event(f"유휴 대기: 사용자 활동 감지됨 (현재 {int(curr_idle // 60)}분 유휴 / 필요 {r_item.get('idle_minutes', 15)}분)")
                            continue

                    r_item["last_executed"] = now.strftime("%Y-%m-%d %H:%M:%S")
                    changed_state = True
                    
                    rule_lbl = r_item.get('label', '이름 없음' if self.lang == 'ko' else 'Unnamed')
                    mode_lbl = self.get_mode_label(r_item.get('mode', 'shutdown'))
                    trigger_log_text = f"스케줄러 규칙 감지 호출: {rule_lbl} [{mode_lbl}]" if self.lang == "ko" else f"Scheduler rule triggered: {rule_lbl} [{mode_lbl}]"
                    self.log_event(trigger_log_text)
                    
                    # 4. 사전 임시 파일 정리 (Clean Temp)
                    if r_item.get("clean_temp", False):
                        self.clean_temp_files_safe()

                    # 4. 사전 명령어 실행 (Pre-command execution)
                    pre_cmd = r_item.get("pre_command", "").strip()
                    if pre_cmd:
                        try:
                            import subprocess
                            self.log_event(f"사전 명령어 실행: {pre_cmd}")
                            subprocess.Popen(pre_cmd, shell=True)
                        except Exception as e:
                            self.log_event(f"사전 명령어 실행 오류: {e}")

                    # 2. 지연 비프 경고
                    if r_item.get("warning_beep", True):
                        self.play_sound_theme("chime")
                    
                    # 트레이에 접혀있을 리 복구를 지시
                    self.restore_from_tray()
                    
                    # 1 & 2. 모드 설정 및 긴급 취소/연기 팝업창 가동
                    self.mode = r_item.get("mode", "shutdown")
                    self.force_flag = r_item.get("force_close", True)
                    self.open_grace_popup(rule_data=r_item)
            
            if changed_state:
                self.save_rules()
                self.render_rules_list()

        # 실시간 트레이 툴팁 타이틀 갱신
        if getattr(self, "tray_icon", None) is not None:
            try:
                _, soonest_text = self.get_soonest_trigger_info()
                
                # 툴팁 텍스트 갱신 (Windows 125자 상한)
                if len(soonest_text) > 125:
                    soonest_text = soonest_text[:122] + "..."
                self.tray_icon.title = soonest_text
            except Exception:
                pass

        # 트레이 최소화(withdrawn) 여부 및 상단고정 미니창 활성화 여부에 따라 동적 감시 주기 완화 (CPU 대폭 절약)
        is_minimized_to_tray = (self.root.state() == "withdrawn")
        mini_active = (hasattr(self, "mini_win") and self.mini_win and self.mini_win.winfo_exists())
        
        if is_minimized_to_tray and not mini_active:
            tick_interval = 5000  # 최소화 상태이며 미니창이 꺼져 있다면 5초 주기로 검사 주기 완화
        else:
            tick_interval = 1000  # 일반적인 가동 상태는 1초 정밀 검증
            
        self.root.after(tick_interval, self.check_advanced_schedules)

    def update_scheduler_countdowns(self, now):
        """그려진 규칙 카드의 카운트다운 라벨 텍스트를 실시간으로 계산해 명시"""
        scrollable_frames = [self.rules_list_container.scrollable_frame]
        if hasattr(self, "popup_rules_list_container") and self.popup_rules_list_container and self.popup_rules_list_container.winfo_exists():
            scrollable_frames.append(self.popup_rules_list_container.scrollable_frame)

        for frm in scrollable_frames:
            try:
                widgets = frm.winfo_children()
            except Exception:
                continue

            for widget in widgets:
                if hasattr(widget, "countdown_label") and hasattr(widget, "rule_data"):
                    lbl = widget.countdown_label
                    rule = widget.rule_data
                    
                    if not rule.get("is_active", True):
                        pause_txt = "⏸ 일시 정지됨" if self.lang == "ko" else "⏸ Paused"
                        lbl.configure(text=pause_txt, fg="#9ca3af")
                        continue
                        
                    r_type = rule.get("type", "daily")
                    time_str = rule.get("time", "00:00")
                    tgt_h, tgt_m = 0, 0
                    if ":" in time_str:
                        try:
                            tgt_h, tgt_m = map(int, time_str.split(":"))
                        except:
                            pass
                    
                    target_dt = None
                    if r_type in ["once", "daily"]:
                        target_dt = now.replace(hour=tgt_h, minute=tgt_m, second=0, microsecond=0)
                        if target_dt <= now:
                            target_dt += datetime.timedelta(days=1)
                    elif r_type == "weekly":
                        allowed_days = rule.get("days", [])
                        if not allowed_days:
                            no_days = "요일 미배정" if self.lang == "ko" else "Days Unassigned"
                            lbl.configure(text=no_days, fg="#ef4444")
                            continue
                            
                        for i in range(8):
                            test_dt = now + datetime.timedelta(days=i)
                            test_dt = test_dt.replace(hour=tgt_h, minute=tgt_m, second=0, microsecond=0)
                            test_day = (test_dt.weekday() + 1) % 7
                            if test_day in allowed_days:
                                if test_dt > now:
                                    target_dt = test_dt
                                    break
                    elif r_type == "interval":
                        interval = rule.get("interval_minutes", 30)
                        try:
                            cr_dt = datetime.datetime.fromisoformat(rule.get("created_at"))
                        except:
                            cr_dt = now
                        
                        diff_seconds = (now - cr_dt).total_seconds()
                        diff_minutes = int(diff_seconds // 60)
                        
                        intervals_passed = diff_minutes // interval
                        next_interval_count = intervals_passed + 1
                        target_dt = cr_dt + datetime.timedelta(minutes=next_interval_count * interval)
                    
                    if target_dt:
                        diff_sec = int((target_dt - now).total_seconds())
                        if diff_sec <= 0:
                            triggering_soon = "곧 트리거 예정" if self.lang == "ko" else "Triggering soon"
                            lbl.configure(text=triggering_soon, fg="#10b981")
                        else:
                            hours = diff_sec // 3600
                            mins = (diff_sec % 3600) // 60
                            secs = diff_sec % 60
                            
                            parts = []
                            if self.lang == "ko":
                                if hours > 0:
                                    parts.append(f"{hours}시간")
                                if mins > 0:
                                    parts.append(f"{mins}분")
                                parts.append(f"{secs}초")
                                lbl.configure(text=f"⏳ {' '.join(parts)} 후 실행", fg="#3b82f6")
                            else:
                                if hours > 0:
                                    parts.append(f"{hours}h")
                                if mins > 0:
                                    parts.append(f"{mins}m")
                                parts.append(f"{secs}s")
                                lbl.configure(text=f"⏳ scheduled in {' '.join(parts)}", fg="#3b82f6")
                    else:
                        hold_calc = "계산 보류" if self.lang == "ko" else "Hold Calculation"
                        lbl.configure(text=hold_calc, fg="#9ca3af")


    # --------------------------------------------------------------------
    # 4. 기능 인터랙션 코어 엔진 (시분초 마우스 휠 및 스핀)
    # --------------------------------------------------------------------
    def bind_spin_interactions(self, entry, field_type):
        """마우스 휠 및 키보드 위/아래 방향키 이벤트 연동"""
        entry.bind("<MouseWheel>", lambda event: self.handle_spin(event, entry, field_type, "wheel"))
        entry.bind("<Button-4>", lambda event: self.handle_spin(event, entry, field_type, "up"))
        entry.bind("<Button-5>", lambda event: self.handle_spin(event, entry, field_type, "down"))
        entry.bind("<Up>", lambda event: self.handle_spin(event, entry, field_type, "up"))
        entry.bind("<Down>", lambda event: self.handle_spin(event, entry, field_type, "down"))

    def handle_spin(self, event, entry, field_type, direction):
        """입력 필드 스핀 동작 계산 데몬"""
        if self.timer_running:
            return "break" # 동작 중에는 변경 금지

        # 증감분 계산 
        if direction == "wheel":
            delta = 1 if event.delta > 0 else -1
        elif direction == "up":
            delta = 1
        else:
            delta = -1

        # 현재 값 읽기 및 정수치 보증
        try:
            val = int(entry.get() or 0)
        except ValueError:
            val = 0

        # 동작 모드 기반 최소/최대 바운더리 산출
        if field_type == "h":
            if self.run_type == "schedule":
                min_val, max_val, wrap = 0, 23, True
            else:
                min_val, max_val, wrap = 0, 999, False
        elif field_type == "m":
            min_val, max_val, wrap = 0, 59, True
        else: # s
            min_val, max_val, wrap = 0, 59, True

        new_val = val + delta

        # 루프 한계 도달 시 자동 오버플로우 순환 쉘 기믹
        if wrap:
            if new_val > max_val:
                new_val = min_val
            elif new_val < min_val:
                new_val = max_val
        else:
            if new_val > max_val:
                new_val = max_val
            elif new_val < min_val:
                new_val = min_val

        # 입력란 갱신 반영
        entry.delete(0, tk.END)
        entry.insert(0, str(new_val))
        
        # 커널 내장 커서 상하 스크롤 등의 역효과 차단
        return "break"

    def toggle_always_on_top(self):
        self.root.attributes('-topmost', False)
        self.sync_always_on_top_mini_win()
        self.save_settings()

    def sync_always_on_top_mini_win(self):
        if self.always_on_top.get():
            # Create a mini window if it does not exist
            if not hasattr(self, "mini_win") or not self.mini_win or not self.mini_win.winfo_exists():
                self.create_mini_window()
            else:
                try:
                    # Make sure it's visible (deiconified)
                    self.mini_win.deiconify()
                    self.mini_win.attributes("-topmost", True)
                except Exception:
                    pass
                self.update_mini_window()
        else:
            # Destroy the mini window if it exists
            if hasattr(self, "mini_win") and self.mini_win and self.mini_win.winfo_exists():
                try:
                    self.mini_win.destroy()
                except Exception:
                    pass
                self.mini_win = None

    def close_mini_context_menu(self):
        """상단 고정창 전용 빠른 제어 팝업 닫기"""
        try:
            if hasattr(self, "mini_context_popup") and self.mini_context_popup:
                if self.mini_context_popup.winfo_exists():
                    self.mini_context_popup.destroy()
                self.mini_context_popup = None
        except Exception:
            pass

    def show_mini_custom_context_menu(self, event):
        """상단 고정창 전용 빠른 제어 팝업 메뉴 (크기조절/투명도/글자크기를 여러 번 클릭해도 닫히지 않음)"""
        try:
            self.close_mini_context_menu()
            if not hasattr(self, "mini_win") or not self.mini_win or not self.mini_win.winfo_exists():
                return

            popup = tk.Toplevel(self.mini_win)
            self.mini_context_popup = popup
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)
            popup.configure(bg="#0f172a")

            outer = tk.Frame(popup, bg="#0f172a", highlightbackground="#334155", highlightthickness=1)
            outer.pack(fill="both", expand=True)

            # --- Header ---
            f_head = tk.Frame(outer, bg="#1e293b")
            f_head.pack(fill="x", padx=1, pady=(1, 3))

            lbl_head = tk.Label(
                f_head,
                text="⚡ 상단 고정창 제어" if self.lang == "ko" else "⚡ Mini Window Controls",
                font=("Arial", 9, "bold"),
                fg="#94a3b8",
                bg="#1e293b"
            )
            lbl_head.pack(side="left", padx=8, pady=4)

            btn_close_menu = tk.Button(
                f_head,
                text="✕",
                font=("Arial", 9, "bold"),
                fg="#94a3b8",
                bg="#1e293b",
                activebackground="#dc2626",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                cursor="hand2",
                command=self.close_mini_context_menu
            )
            btn_close_menu.pack(side="right", padx=6, pady=4)

            # --- 1. 창 크기조절 섹션 (여러 번 연속 클릭해도 닫히지 않음) ---
            f_resize = tk.Frame(outer, bg="#0f172a")
            f_resize.pack(fill="x", padx=8, pady=(4, 2))

            lbl_resize_title = tk.Label(
                f_resize,
                text="📐 창 크기조절 (연속 클릭 가능)" if self.lang == "ko" else "📐 Window Size",
                font=("Arial", 8, "bold"),
                fg="#f8fafc",
                bg="#0f172a"
            )
            lbl_resize_title.pack(side="left")

            cur_w = self.mini_win.winfo_width()
            cur_h = self.mini_win.winfo_height()
            if cur_w <= 1 or cur_h <= 1:
                cur_w = self.widget_width.get()
                cur_h = self.widget_height.get() if hasattr(self, "widget_height") else 95

            self.lbl_popup_size_display = tk.Label(
                f_resize,
                text=f"{cur_w}×{cur_h}",
                font=("Arial", 8),
                fg="#38bdf8",
                bg="#0f172a"
            )
            self.lbl_popup_size_display.pack(side="right")

            f_resize_btns = tk.Frame(outer, bg="#0f172a")
            f_resize_btns.pack(fill="x", padx=8, pady=(1, 4))

            def do_zoom(factor):
                self.zoom_mini_window(factor)
                if hasattr(self, "lbl_popup_size_display") and self.lbl_popup_size_display.winfo_exists():
                    try:
                        nw = self.mini_win.winfo_width()
                        nh = self.mini_win.winfo_height()
                        self.lbl_popup_size_display.configure(text=f"{nw}×{nh}")
                    except Exception:
                        pass
                if hasattr(self, "lbl_popup_tf_val") and self.lbl_popup_tf_val.winfo_exists():
                    self.lbl_popup_tf_val.configure(text=f"{self.timer_font_size.get()}pt")
                if hasattr(self, "lbl_popup_cf_val") and self.lbl_popup_cf_val.winfo_exists():
                    self.lbl_popup_cf_val.configure(text=f"{self.clock_font_size.get()}pt")

            def do_reset_size():
                self.reset_mini_window_size()
                if hasattr(self, "lbl_popup_size_display") and self.lbl_popup_size_display.winfo_exists():
                    self.lbl_popup_size_display.configure(text=f"286×95")
                if hasattr(self, "lbl_popup_tf_val") and self.lbl_popup_tf_val.winfo_exists():
                    self.lbl_popup_tf_val.configure(text="20pt")
                if hasattr(self, "lbl_popup_cf_val") and self.lbl_popup_cf_val.winfo_exists():
                    self.lbl_popup_cf_val.configure(text="13pt")

            btn_shrink = tk.Button(
                f_resize_btns,
                text="🔍 축소 (-)" if self.lang == "ko" else "🔍 Shrink (-)",
                font=("Arial", 9),
                bg="#1e293b",
                fg="#38bdf8",
                activebackground="#0284c7",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=6,
                pady=3,
                cursor="hand2",
                command=lambda: do_zoom(0.9)
            )
            btn_shrink.pack(side="left", expand=True, fill="x", padx=(0, 2))

            btn_enlarge = tk.Button(
                f_resize_btns,
                text="🔍 확대 (+)" if self.lang == "ko" else "🔍 Enlarge (+)",
                font=("Arial", 9),
                bg="#1e293b",
                fg="#38bdf8",
                activebackground="#0284c7",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=6,
                pady=3,
                cursor="hand2",
                command=lambda: do_zoom(1.1)
            )
            btn_enlarge.pack(side="left", expand=True, fill="x", padx=2)

            btn_reset = tk.Button(
                f_resize_btns,
                text="↺ 기본" if self.lang == "ko" else "↺ Reset",
                font=("Arial", 9),
                bg="#1e293b",
                fg="#94a3b8",
                activebackground="#475569",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=6,
                pady=3,
                cursor="hand2",
                command=do_reset_size
            )
            btn_reset.pack(side="left", padx=(2, 0))

            # --- 2. 투명도 조절 섹션 ---
            f_op = tk.Frame(outer, bg="#0f172a")
            f_op.pack(fill="x", padx=8, pady=(4, 2))

            lbl_op_title = tk.Label(
                f_op,
                text="🎨 투명도 조절" if self.lang == "ko" else "🎨 Opacity",
                font=("Arial", 8, "bold"),
                fg="#f8fafc",
                bg="#0f172a"
            )
            lbl_op_title.pack(side="left")

            self.lbl_popup_op_val = tk.Label(
                f_op,
                text=f"{self.widget_opacity.get()}%",
                font=("Arial", 8),
                fg="#38bdf8",
                bg="#0f172a"
            )
            self.lbl_popup_op_val.pack(side="right")

            def do_opacity(delta):
                self.adjust_widget_opacity(delta)
                if hasattr(self, "lbl_popup_op_val") and self.lbl_popup_op_val.winfo_exists():
                    self.lbl_popup_op_val.configure(text=f"{self.widget_opacity.get()}%")

            def do_set_opacity(val):
                self.set_widget_opacity(val)
                if hasattr(self, "lbl_popup_op_val") and self.lbl_popup_op_val.winfo_exists():
                    self.lbl_popup_op_val.configure(text=f"{val}%")

            f_op_btns = tk.Frame(outer, bg="#0f172a")
            f_op_btns.pack(fill="x", padx=8, pady=(1, 4))

            btn_op_minus = tk.Button(
                f_op_btns, text="➖ 투명 (-5%)" if self.lang == "ko" else "➖ -5%",
                font=("Arial", 8), bg="#1e293b", fg="#e2e8f0", activebackground="#334155",
                relief="flat", bd=0, padx=4, pady=2, cursor="hand2",
                command=lambda: do_opacity(-5)
            )
            btn_op_minus.pack(side="left", expand=True, fill="x", padx=(0, 2))

            btn_op_plus = tk.Button(
                f_op_btns, text="➕ 불투명 (+5%)" if self.lang == "ko" else "➕ +5%",
                font=("Arial", 8), bg="#1e293b", fg="#e2e8f0", activebackground="#334155",
                relief="flat", bd=0, padx=4, pady=2, cursor="hand2",
                command=lambda: do_opacity(5)
            )
            btn_op_plus.pack(side="left", expand=True, fill="x", padx=2)

            btn_op_preset100 = tk.Button(
                f_op_btns, text="100%", font=("Arial", 8), bg="#1e293b", fg="#94a3b8",
                activebackground="#334155", relief="flat", bd=0, padx=4, pady=2, cursor="hand2",
                command=lambda: do_set_opacity(100)
            )
            btn_op_preset100.pack(side="left", padx=1)

            btn_op_preset80 = tk.Button(
                f_op_btns, text="80%", font=("Arial", 8), bg="#1e293b", fg="#94a3b8",
                activebackground="#334155", relief="flat", bd=0, padx=4, pady=2, cursor="hand2",
                command=lambda: do_set_opacity(80)
            )
            btn_op_preset80.pack(side="left", padx=(1, 0))

            # --- 3. 글자 크기 세부 조정 (시계 & 타이머) ---
            f_fonts = tk.Frame(outer, bg="#0f172a")
            f_fonts.pack(fill="x", padx=8, pady=(4, 2))

            # Clock Font Row
            f_cf = tk.Frame(f_fonts, bg="#0f172a")
            f_cf.pack(fill="x", pady=1)

            lbl_cf = tk.Label(
                f_cf, text="🕒 시계 글자 크기" if self.lang == "ko" else "🕒 Clock Font",
                font=("Arial", 8), fg="#cbd5e1", bg="#0f172a"
            )
            lbl_cf.pack(side="left")

            self.lbl_popup_cf_val = tk.Label(
                f_cf, text=f"{self.clock_font_size.get()}pt",
                font=("Arial", 8, "bold"), fg="#38bdf8", bg="#0f172a", width=5
            )
            self.lbl_popup_cf_val.pack(side="right")

            def do_cf(delta):
                self.adjust_mini_clock_font_size(delta)
                if hasattr(self, "lbl_popup_cf_val") and self.lbl_popup_cf_val.winfo_exists():
                    self.lbl_popup_cf_val.configure(text=f"{self.clock_font_size.get()}pt")

            btn_cf_plus = tk.Button(
                f_cf, text="+", font=("Arial", 8, "bold"), bg="#1e293b", fg="#38bdf8",
                relief="flat", bd=0, padx=5, pady=0, cursor="hand2", command=lambda: do_cf(1)
            )
            btn_cf_plus.pack(side="right", padx=1)

            btn_cf_minus = tk.Button(
                f_cf, text="-", font=("Arial", 8, "bold"), bg="#1e293b", fg="#38bdf8",
                relief="flat", bd=0, padx=5, pady=0, cursor="hand2", command=lambda: do_cf(-1)
            )
            btn_cf_minus.pack(side="right", padx=1)

            # Timer Font Row
            f_tf = tk.Frame(f_fonts, bg="#0f172a")
            f_tf.pack(fill="x", pady=1)

            lbl_tf = tk.Label(
                f_tf, text="⏱️ 타이머 글자 크기" if self.lang == "ko" else "⏱️ Timer Font",
                font=("Arial", 8), fg="#cbd5e1", bg="#0f172a"
            )
            lbl_tf.pack(side="left")

            self.lbl_popup_tf_val = tk.Label(
                f_tf, text=f"{self.timer_font_size.get()}pt",
                font=("Arial", 8, "bold"), fg="#38bdf8", bg="#0f172a", width=5
            )
            self.lbl_popup_tf_val.pack(side="right")

            def do_tf(delta):
                self.adjust_mini_timer_font_size(delta)
                if hasattr(self, "lbl_popup_tf_val") and self.lbl_popup_tf_val.winfo_exists():
                    self.lbl_popup_tf_val.configure(text=f"{self.timer_font_size.get()}pt")

            btn_tf_plus = tk.Button(
                f_tf, text="+", font=("Arial", 8, "bold"), bg="#1e293b", fg="#38bdf8",
                relief="flat", bd=0, padx=5, pady=0, cursor="hand2", command=lambda: do_tf(1)
            )
            btn_tf_plus.pack(side="right", padx=1)

            btn_tf_minus = tk.Button(
                f_tf, text="-", font=("Arial", 8, "bold"), bg="#1e293b", fg="#38bdf8",
                relief="flat", bd=0, padx=5, pady=0, cursor="hand2", command=lambda: do_tf(-1)
            )
            btn_tf_minus.pack(side="right", padx=1)

            # --- 4. 시계(현재 시각) 토글 버튼 ---
            is_clk_on = self.show_current_time_compact.get()
            clk_txt = ("✓ 현재 시각(시계) 표시 중" if is_clk_on else "☐ 현재 시각(시계) 숨김") if self.lang == "ko" else ("✓ Clock Visible" if is_clk_on else "☐ Clock Hidden")

            btn_clk = tk.Button(
                outer,
                text=clk_txt,
                font=("Arial", 9),
                bg="#1e293b",
                fg="#38bdf8" if is_clk_on else "#94a3b8",
                activebackground="#334155",
                relief="flat",
                bd=0,
                padx=8,
                pady=3,
                anchor="w",
                cursor="hand2"
            )

            def do_toggle_clk():
                self.toggle_mini_clock()
                on = self.show_current_time_compact.get()
                t = ("✓ 현재 시각(시계) 표시 중" if on else "☐ 현재 시각(시계) 숨김") if self.lang == "ko" else ("✓ Clock Visible" if on else "☐ Clock Hidden")
                if btn_clk.winfo_exists():
                    btn_clk.configure(text=t, fg="#38bdf8" if on else "#94a3b8")

            btn_clk.configure(command=do_toggle_clk)
            btn_clk.pack(fill="x", padx=8, pady=(4, 2))

            # --- Divider ---
            sep = tk.Frame(outer, bg="#334155", height=1)
            sep.pack(fill="x", padx=8, pady=4)

            # --- 5. 타이머 제어, 환경설정, 닫기 ---
            if self.timer_running:
                p_txt = ("▶️ 타이머 계속 진행 (재개)" if self.timer_paused else "⏸️ 타이머 일시정지") if self.lang == "ko" else ("▶️ Resume Timer" if self.timer_paused else "⏸️ Pause Timer")
                btn_pause = tk.Button(
                    outer,
                    text=p_txt,
                    font=("Arial", 9),
                    bg="#1e293b",
                    fg="#eab308" if self.timer_paused else "#38bdf8",
                    activebackground="#334155",
                    relief="flat",
                    bd=0,
                    padx=8,
                    pady=3,
                    anchor="w",
                    cursor="hand2",
                    command=lambda: [self.toggle_pause_timer(), self.close_mini_context_menu()]
                )
                btn_pause.pack(fill="x", padx=8, pady=1)

            btn_settings = tk.Button(
                outer,
                text="⚙️ 환경설정 열기..." if self.lang == "ko" else "⚙️ Preferences...",
                font=("Arial", 9),
                bg="#1e293b",
                fg="#cbd5e1",
                activebackground="#334155",
                relief="flat",
                bd=0,
                padx=8,
                pady=3,
                anchor="w",
                cursor="hand2",
                command=lambda: [self.close_mini_context_menu(), self.open_settings_popup()]
            )
            btn_settings.pack(fill="x", padx=8, pady=1)

            btn_close_top = tk.Button(
                outer,
                text="✕ 상단 고정창 닫기 (항상 위 해제)" if self.lang == "ko" else "✕ Close Always-on-Top Window",
                font=("Arial", 9),
                bg="#1e293b",
                fg="#f87171",
                activebackground="#7f1d1d",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=8,
                pady=3,
                anchor="w",
                cursor="hand2",
                command=lambda: [self.close_mini_context_menu(), self.close_always_on_top_mini_win()]
            )
            btn_close_top.pack(fill="x", padx=8, pady=1)

            # Footer "완료 (메뉴 닫기)" 버튼
            btn_done = tk.Button(
                outer,
                text="✔ 완료 (메뉴 닫기)" if self.lang == "ko" else "✔ Done (Close Menu)",
                font=("Arial", 8, "bold"),
                bg="#334155",
                fg="#f8fafc",
                activebackground="#475569",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=8,
                pady=3,
                cursor="hand2",
                command=self.close_mini_context_menu
            )
            btn_done.pack(fill="x", padx=8, pady=(4, 6))

            # --- Positioning & Event Binding ---
            popup.update_idletasks()
            pw = popup.winfo_reqwidth()
            ph = popup.winfo_reqheight()
            sw = popup.winfo_screenwidth()
            sh = popup.winfo_screenheight()

            px = event.x_root
            py = event.y_root
            if px + pw > sw - 10:
                px = max(10, sw - pw - 10)
            if py + ph > sh - 40:
                py = max(10, sh - ph - 40)

            popup.geometry(f"+{px}+{py}")

            def on_focus_lost(e=None):
                try:
                    if not self.mini_context_popup or not self.mini_context_popup.winfo_exists():
                        return
                    mx, my = self.mini_context_popup.winfo_pointerxy()
                    rx = self.mini_context_popup.winfo_rootx()
                    ry = self.mini_context_popup.winfo_rooty()
                    rw = self.mini_context_popup.winfo_width()
                    rh = self.mini_context_popup.winfo_height()
                    if not (rx <= mx <= rx + rw and ry <= my <= ry + rh):
                        self.close_mini_context_menu()
                except Exception:
                    self.close_mini_context_menu()

            popup.bind("<Escape>", lambda e: self.close_mini_context_menu())
            popup.bind("<FocusOut>", lambda e: popup.after(250, on_focus_lost))
            try:
                popup.focus_set()
            except Exception:
                pass
        except Exception:
            pass

    def close_always_on_top_mini_win(self):
        self.close_mini_context_menu()
        self.always_on_top.set(False)
        self.sync_always_on_top_mini_win()
        self.save_settings()
        self.show_toast(
            title="📌 상단 고정 해제" if self.lang == "ko" else "📌 Always On Top Disabled",
            message="상단 고정 미니 창이 닫혀 항상 위에 표시 옵션이 해제되었습니다." if self.lang == "ko" else "The mini window is closed and Always On Top is disabled.",
            accent_color=ACCENT_RED
        )

    def rebuild_mini_window(self):
        """현재 위치를 기억한 상태로 미니창을 재구성(테마 변경, 글꼴 크기 변경, 크기 변경 즉각 반영)"""
        self.close_mini_context_menu()
        if not hasattr(self, "mini_win") or not self.mini_win or not self.mini_win.winfo_exists():
            return
        try:
            curr_x = self.mini_win.winfo_x()
            curr_y = self.mini_win.winfo_y()
        except Exception:
            curr_x, curr_y = None, None
        try:
            self.mini_win.destroy()
        except Exception:
            pass
        self.mini_win = None
        self.create_mini_window(saved_x=curr_x, saved_y=curr_y)

    def create_mini_window(self, saved_x=None, saved_y=None):
        self.mini_win = tk.Toplevel(self.root)
        self.mini_win.title("타이머 미니창" if self.lang == "ko" else "Timer Mini Window")
        
        # Configure look: frameless & always on top
        self.mini_win.overrideredirect(True)
        try:
            self.mini_win.attributes("-topmost", True)
            self.mini_win.attributes("-alpha", self.widget_opacity.get() / 100.0)
        except Exception:
            pass
            
        design = self.widget_design.get()
        show_clock = self.show_current_time_compact.get()
        custom_w = max(180, min(600, self.widget_width.get()))
        custom_h = max(36, min(450, self.widget_height.get() if hasattr(self, "widget_height") else 135))
        clock_sz = self.clock_font_size.get()
        timer_sz = self.timer_font_size.get()

        if design == "minimal_bar":
            width = max(220, custom_w)
            # If user has set a custom height, respect it; default min bar is compact
            height = custom_h if custom_h <= 80 else 42
        else:
            width = custom_w
            height = custom_h

        screen_width = self.mini_win.winfo_screenwidth()
        if saved_x is not None and saved_y is not None:
            x, y = saved_x, saved_y
        else:
            x = screen_width - width - 25
            y = 25
        self.mini_win.geometry(f"{width}x{height}+{x}+{y}")
        
        # Dragging support
        def make_draggable(widget):
            def start_drag(event):
                if getattr(self, "_is_resizing", False):
                    return "break"
                if hasattr(self, "mini_resize_grip") and event.widget == self.mini_resize_grip:
                    return "break"
                rx = self.mini_win.winfo_rootx()
                ry = self.mini_win.winfo_rooty()
                if rx == 0 and ry == 0:
                    rx = self.mini_win.winfo_x()
                    ry = self.mini_win.winfo_y()
                self.mini_win._drag_x = event.x_root - rx
                self.mini_win._drag_y = event.y_root - ry
                return "break"

            def drag(event):
                if getattr(self, "_is_resizing", False):
                    return "break"
                if hasattr(self, "mini_resize_grip") and event.widget == self.mini_resize_grip:
                    return "break"
                if not hasattr(self.mini_win, "_drag_x"):
                    return "break"
                dx = event.x_root - self.mini_win._drag_x
                dy = event.y_root - self.mini_win._drag_y
                self.mini_win.geometry(f"+{dx}+{dy}")
                return "break"

            widget.bind("<Button-1>", start_drag)
            widget.bind("<B1-Motion>", drag)

        make_draggable(self.mini_win)

        # -------------------------------------------------------------
        # Theme 1: MINIMAL_BAR (가로형 초슬림 바)
        # -------------------------------------------------------------
        if design == "minimal_bar":
            self.mini_main_frame = tk.Frame(
                self.mini_win,
                bg="#0f172a",
                highlightbackground="#3b82f6" if self.mode == "shutdown" else "#ef4444",
                highlightthickness=1
            )
            self.mini_main_frame.pack(fill="both", expand=True)
            make_draggable(self.mini_main_frame)

            # Left group: Badge & Timer
            f_left = tk.Frame(self.mini_main_frame, bg="#0f172a")
            f_left.pack(side="left", fill="y", padx=(8, 4), pady=6)
            make_draggable(f_left)

            self.mini_lbl_status = tk.Label(
                f_left,
                text="⚡ 종료",
                font=("Arial", 10, "bold"),
                fg="#93c5fd",
                bg="#1e3a8a",
                padx=5,
                pady=1
            )
            self.mini_lbl_status.pack(side="left", padx=(0, 6))

            self.mini_lbl_timer = tk.Label(
                f_left,
                text="00:00:00",
                font=("Arial", min(15, timer_sz), "bold"),
                fg="#60a5fa",
                bg="#0f172a"
            )
            self.mini_lbl_timer.pack(side="left", padx=(0, 4))

            self.mini_lbl_clock = tk.Label(
                f_left,
                text="00:00:00",
                font=("Arial", min(18, max(7, clock_sz))),
                fg="#94a3b8",
                bg="#0f172a"
            )
            if show_clock:
                self.mini_lbl_clock.pack(side="left", padx=(2, 0))

            # Right group: Action buttons & Close
            f_right = tk.Frame(self.mini_main_frame, bg="#0f172a")
            f_right.pack(side="right", padx=(4, 6), pady=6)

            self.mini_btn_close = tk.Button(
                f_right,
                text="✕",
                font=("Arial", 10, "bold"),
                bg="#1e293b",
                fg="#94a3b8",
                activebackground="#ef4444",
                activeforeground="white",
                relief="flat",
                bd=0,
                padx=5,
                pady=1,
                cursor="hand2",
                command=self.close_always_on_top_mini_win
            )
            self.mini_btn_close.pack(side="right", padx=1)

            # Quick Pause/Resume button
            self.mini_btn_pause = tk.Button(
                f_right,
                text="⏸",
                font=("Arial", 10, "bold"),
                bg="#1e293b",
                fg="#38bdf8",
                relief="flat",
                bd=0,
                padx=4,
                pady=1,
                cursor="hand2",
                command=self.toggle_pause
            )
            self.mini_btn_pause.pack(side="right", padx=1)

        # -------------------------------------------------------------
        # Theme 2: CYBER_HUD (사이버 하이테크 HUD)
        # -------------------------------------------------------------
        elif design == "cyber_hud":
            self.mini_main_frame = tk.Frame(
                self.mini_win,
                bg="#030712",
                highlightbackground="#06b6d4",
                highlightthickness=1
            )
            self.mini_main_frame.pack(fill="both", expand=True)
            make_draggable(self.mini_main_frame)

            # Header bar
            f_hdr = tk.Frame(self.mini_main_frame, bg="#030712")
            f_hdr.pack(fill="x", padx=6, pady=(4, 0))
            make_draggable(f_hdr)

            self.mini_lbl_status = tk.Label(
                f_hdr,
                text="[SYS.HUD // ONLINE]",
                font=("Consolas", 10, "bold"),
                fg="#22d3ee",
                bg="#030712"
            )
            self.mini_lbl_status.pack(side="left")

            self.mini_btn_close = tk.Button(
                f_hdr,
                text="✕",
                font=("Consolas", 10, "bold"),
                bg="#030712",
                fg="#06b6d4",
                activebackground="#ef4444",
                activeforeground="white",
                relief="flat",
                bd=0,
                cursor="hand2",
                command=self.close_always_on_top_mini_win
            )
            self.mini_btn_close.pack(side="right")

            # Clock Label
            self.mini_lbl_clock = tk.Label(
                self.mini_main_frame,
                text="CLK: 00:00:00",
                font=("Consolas", clock_sz, "bold"),
                fg="#38bdf8",
                bg="#030712"
            )
            if show_clock:
                self.mini_lbl_clock.pack(pady=(2, 0))
            make_draggable(self.mini_lbl_clock)

            # Timer Display
            self.mini_lbl_timer = tk.Label(
                self.mini_main_frame,
                text="TMR: 00:00:00",
                font=("Consolas", timer_sz, "bold"),
                fg="#22d3ee",
                bg="#030712"
            )
            self.mini_lbl_timer.pack(pady=(1, 4))
            make_draggable(self.mini_lbl_timer)

        # -------------------------------------------------------------
        # Theme 3: RETRO_LED (디지털 LED 전광판)
        # -------------------------------------------------------------
        elif design == "retro_led":
            self.mini_main_frame = tk.Frame(
                self.mini_win,
                bg="#000000",
                highlightbackground="#15803d",
                highlightthickness=2
            )
            self.mini_main_frame.pack(fill="both", expand=True)
            make_draggable(self.mini_main_frame)

            # Header
            f_hdr = tk.Frame(self.mini_main_frame, bg="#000000")
            f_hdr.pack(fill="x", padx=6, pady=(3, 0))
            make_draggable(f_hdr)

            self.mini_lbl_status = tk.Label(
                f_hdr,
                text="▶ LED DIGITAL TIMER",
                font=("Consolas", 10, "bold"),
                fg="#16a34a",
                bg="#000000"
            )
            self.mini_lbl_status.pack(side="left")

            self.mini_btn_close = tk.Button(
                f_hdr,
                text="✕",
                font=("Arial", 10, "bold"),
                bg="#000000",
                fg="#4ade80",
                activebackground="#dc2626",
                activeforeground="white",
                relief="flat",
                bd=0,
                cursor="hand2",
                command=self.close_always_on_top_mini_win
            )
            self.mini_btn_close.pack(side="right")

            self.mini_lbl_clock = tk.Label(
                self.mini_main_frame,
                text="00:00:00",
                font=("Consolas", clock_sz, "bold"),
                fg="#86efac",
                bg="#000000"
            )
            if show_clock:
                self.mini_lbl_clock.pack(pady=(1, 0))
            make_draggable(self.mini_lbl_clock)

            self.mini_lbl_timer = tk.Label(
                self.mini_main_frame,
                text="00:00:00",
                font=("Consolas", timer_sz, "bold"),
                fg="#22c55e",
                bg="#000000"
            )
            self.mini_lbl_timer.pack(pady=(1, 4))
            make_draggable(self.mini_lbl_timer)

        # -------------------------------------------------------------
        # Theme 4: CLEAN_CARD (모던 슬레이트 미니멀)
        # -------------------------------------------------------------
        elif design == "clean_card":
            self.mini_main_frame = tk.Frame(
                self.mini_win,
                bg="#1e293b",
                highlightbackground="#475569",
                highlightthickness=1
            )
            self.mini_main_frame.pack(fill="both", expand=True)
            make_draggable(self.mini_main_frame)

            # Header
            f_hdr = tk.Frame(self.mini_main_frame, bg="#1e293b")
            f_hdr.pack(fill="x", padx=8, pady=(5, 0))
            make_draggable(f_hdr)

            self.mini_lbl_status = tk.Label(
                f_hdr,
                text="대기 상태" if self.lang == "ko" else "Idle State",
                font=("Arial", 10),
                fg="#94a3b8",
                bg="#1e293b"
            )
            self.mini_lbl_status.pack(side="left")

            self.mini_btn_close = tk.Button(
                f_hdr,
                text="✕",
                font=("Arial", 10),
                bg="#1e293b",
                fg="#94a3b8",
                activebackground="#1e293b",
                activeforeground="#ef4444",
                relief="flat",
                bd=0,
                cursor="hand2",
                command=self.close_always_on_top_mini_win
            )
            self.mini_btn_close.pack(side="right")

            self.mini_lbl_clock = tk.Label(
                self.mini_main_frame,
                text="00:00:00",
                font=("Arial", clock_sz),
                fg="#cbd5e1",
                bg="#1e293b"
            )
            if show_clock:
                self.mini_lbl_clock.pack(pady=(2, 0))
            make_draggable(self.mini_lbl_clock)

            self.mini_lbl_timer = tk.Label(
                self.mini_main_frame,
                text="00:00:00",
                font=("Arial", timer_sz, "bold"),
                fg="#f8fafc",
                bg="#1e293b"
            )
            self.mini_lbl_timer.pack(pady=(1, 4))
            make_draggable(self.mini_lbl_timer)

        # -------------------------------------------------------------
        # Theme 5: STANDARD (기본 네온 링 카드)
        # -------------------------------------------------------------
        else:
            self.mini_main_frame = tk.Frame(
                self.mini_win,
                bg=DARK_CARD,
                highlightbackground=ACCENT_BLUE if self.mode == "shutdown" else ACCENT_RED,
                highlightthickness=1
            )
            self.mini_main_frame.pack(fill="both", expand=True)
            make_draggable(self.mini_main_frame)
            
            self.mini_lbl_status = tk.Label(
                self.mini_main_frame, 
                text="대기 상태" if self.lang == "ko" else "Idle State", 
                font=("Arial", 10, "bold"), 
                fg=self.current_subtext, 
                bg=DARK_CARD
            )
            self.mini_lbl_status.pack(pady=(6, 0))
            make_draggable(self.mini_lbl_status)
            
            self.mini_lbl_clock = tk.Label(
                self.mini_main_frame,
                text="00:00:00",
                font=("Arial", clock_sz, "bold"),
                fg=TEXT_COLOR,
                bg=DARK_CARD
            )
            if show_clock:
                self.mini_lbl_clock.pack(pady=(1, 1))
            make_draggable(self.mini_lbl_clock)
            
            self.mini_lbl_timer = tk.Label(
                self.mini_main_frame, 
                text="00:00:00", 
                font=("Arial", timer_sz, "bold"), 
                fg=TEXT_COLOR, 
                bg=DARK_CARD
            )
            self.mini_lbl_timer.pack(pady=(1, 5))
            make_draggable(self.mini_lbl_timer)

            self.mini_btn_close = tk.Button(
                self.mini_main_frame,
                text="×",
                font=("Arial", 11, "bold"),
                bg=DARK_CARD,
                fg="#9ca3af",
                activebackground=DARK_CARD,
                activeforeground=ACCENT_RED,
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=2,
                pady=0,
                command=self.close_always_on_top_mini_win
            )
            self.mini_btn_close.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=3)

        # -------------------------------------------------------------
        # 가로 / 세로 양방향 자유 크기 조절 리사이즈 핸들 (Interactive Corner Grip)
        # -------------------------------------------------------------
        try:
            grip_bg = self.mini_main_frame.cget("bg") if hasattr(self, "mini_main_frame") else "#1e293b"
            grip_fg = "#94a3b8" if design != "retro_led" else "#22c55e"
            self.mini_resize_grip = tk.Label(
                self.mini_win,
                text="◢",
                font=("Arial", 11, "bold"),
                fg=grip_fg,
                bg=grip_bg,
                cursor="size_nw_se",
                padx=1,
                pady=1
            )
            self.mini_resize_grip.place(relx=1.0, rely=1.0, anchor="se", x=-1, y=-1)
            self.mini_resize_grip.lift()

            def start_resize(event):
                self._is_resizing = True
                self._resize_start_x = event.x_root
                self._resize_start_y = event.y_root

                # 정확한 시작 윈도우 크기 캡처
                w = self.mini_win.winfo_width()
                h = self.mini_win.winfo_height()
                if w <= 1 or h <= 1:
                    w = self.widget_width.get()
                    h = self.widget_height.get() if hasattr(self, "widget_height") else 135
                self._resize_start_w = w
                self._resize_start_h = h

                # 좌상단 기준 좌표를 절대 화면 좌표계로 고정하여 리사이즈 중 위치 이동 방지
                rx = self.mini_win.winfo_rootx()
                ry = self.mini_win.winfo_rooty()
                if rx == 0 and ry == 0:
                    rx = self.mini_win.winfo_x()
                    ry = self.mini_win.winfo_y()
                self._resize_origin_x = rx
                self._resize_origin_y = ry
                return "break"

            def do_resize(event):
                if not getattr(self, "_is_resizing", False):
                    return "break"
                try:
                    dx = event.x_root - self._resize_start_x
                    dy = event.y_root - self._resize_start_y
                    min_w = 200 if design == "minimal_bar" else 180
                    min_h = 36 if design == "minimal_bar" else 70
                    new_w = max(min_w, min(600, self._resize_start_w + dx))
                    new_h = max(min_h, min(450, self._resize_start_h + dy))

                    # 좌상단 위치는 절대 고정시키고, 마우스 드래그 좌표와 1:1로 창 크기만 조절
                    self.mini_win.geometry(f"{new_w}x{new_h}+{self._resize_origin_x}+{self._resize_origin_y}")
                    self.widget_width.set(new_w)
                    self.widget_height.set(new_h)
                    if hasattr(self, "scale_w_width") and self.scale_w_width.winfo_exists():
                        try:
                            self.scale_w_width.set(new_w)
                        except Exception:
                            pass
                    if hasattr(self, "scale_w_height") and self.scale_w_height.winfo_exists():
                        try:
                            self.scale_w_height.set(new_h)
                        except Exception:
                            pass
                except Exception:
                    pass
                return "break"

            def stop_resize(event):
                self._is_resizing = False
                self.save_settings()
                return "break"

            self.mini_resize_grip.bind("<Button-1>", start_resize)
            self.mini_resize_grip.bind("<B1-Motion>", do_resize)
            self.mini_resize_grip.bind("<ButtonRelease-1>", stop_resize)
        except Exception:
            pass

        # -------------------------------------------------------------
        # 시계 / 타이머 글자 크기 실시간 마우스 휠 조절 & 우클릭 메뉴
        # -------------------------------------------------------------
        try:
            if hasattr(self, "mini_lbl_clock") and self.mini_lbl_clock and self.mini_lbl_clock.winfo_exists():
                def on_clock_wheel(event):
                    try:
                        delta = 0
                        if getattr(event, "delta", 0):
                            delta = 1 if event.delta > 0 else -1
                        elif getattr(event, "num", None) == 4:
                            delta = 1
                        elif getattr(event, "num", None) == 5:
                            delta = -1
                        if delta != 0:
                            self.adjust_mini_clock_font_size(delta)
                    except Exception:
                        pass

                self.mini_lbl_clock.bind("<MouseWheel>", on_clock_wheel, add="+")
                self.mini_lbl_clock.bind("<Button-4>", on_clock_wheel, add="+")
                self.mini_lbl_clock.bind("<Button-5>", on_clock_wheel, add="+")

            def on_opacity_wheel(event):
                try:
                    delta = 0
                    if getattr(event, "delta", 0) > 0:
                        delta = 5
                    elif getattr(event, "delta", 0) < 0:
                        delta = -5
                    elif getattr(event, "num", None) == 4:
                        delta = 5
                    elif getattr(event, "num", None) == 5:
                        delta = -5
                    if delta != 0:
                        self.adjust_widget_opacity(delta)
                except Exception:
                    pass

            if hasattr(self, "mini_opacity_frame") and self.mini_opacity_frame.winfo_exists():
                self.mini_opacity_frame.bind("<MouseWheel>", on_opacity_wheel, add="+")
                self.mini_opacity_frame.bind("<Button-4>", on_opacity_wheel, add="+")
                self.mini_opacity_frame.bind("<Button-5>", on_opacity_wheel, add="+")
            if hasattr(self, "mini_lbl_op_val") and self.mini_lbl_op_val.winfo_exists():
                self.mini_lbl_op_val.bind("<MouseWheel>", on_opacity_wheel, add="+")
                self.mini_lbl_op_val.bind("<Button-4>", on_opacity_wheel, add="+")
                self.mini_lbl_op_val.bind("<Button-5>", on_opacity_wheel, add="+")

            def show_mini_context_menu(event):
                self.show_mini_custom_context_menu(event)

            def bind_mini_context_menu_tree(w):
                try:
                    w.bind("<Button-3>", show_mini_context_menu, add="+")
                    w.bind("<Button-1>", lambda e: self.close_mini_context_menu(), add="+")
                except Exception:
                    pass
                for child in w.winfo_children():
                    bind_mini_context_menu_tree(child)

            bind_mini_context_menu_tree(self.mini_win)
        except Exception:
            pass

        # Apply custom typography if needed
        self.apply_current_font_to_widgets(self.mini_win)
        self.update_mini_window()

    def update_mini_window(self):
        if not hasattr(self, "mini_win") or not self.mini_win or not self.mini_win.winfo_exists():
            return
            
        design = self.widget_design.get()
        show_clock = self.show_current_time_compact.get()
        now_str = datetime.datetime.now().strftime("%H:%M:%S")

        # Determine state
        mode_lbl = self.get_mode_label(self.mode)
        if self.timer_running:
            h = self.remaining_seconds // 3600
            m = (self.remaining_seconds % 3600) // 60
            s = self.remaining_seconds % 60
            time_str = f"{h:02d}:{m:02d}:{s:02d}"
            
            if self.timer_paused:
                stat_txt = f"⏸️ {mode_lbl} " + ("일시정지" if self.lang == "ko" else "Paused")
                time_color = ACCENT_YELLOW
            else:
                stat_txt = f"⏱️ {mode_lbl} " + ("진행 중" if self.lang == "ko" else "Running")
                time_color = ACCENT_RED if self.mode == "shutdown" else ACCENT_BLUE
        else:
            time_str = "00:00:00"
            stat_txt = "⏱️ " + ("대기 상태" if self.lang == "ko" else "Idle State")
            time_color = self.current_subtext

        # -------------------------------------------------------------
        # 1. MINIMAL BAR
        # -------------------------------------------------------------
        if design == "minimal_bar":
            try:
                if hasattr(self, "mini_lbl_status") and self.mini_lbl_status.winfo_exists():
                    self.mini_lbl_status.configure(text=f"⚡ {mode_lbl}")
                if hasattr(self, "mini_lbl_timer") and self.mini_lbl_timer.winfo_exists():
                    self.mini_lbl_timer.configure(text=time_str, fg=time_color)
                if hasattr(self, "mini_lbl_clock") and self.mini_lbl_clock.winfo_exists():
                    self.mini_lbl_clock.configure(text=f"🕒 {now_str}")
                if hasattr(self, "mini_main_frame") and self.mini_main_frame.winfo_exists():
                    self.mini_main_frame.configure(highlightbackground=time_color)
                if hasattr(self, "mini_btn_pause") and self.mini_btn_pause.winfo_exists():
                    self.mini_btn_pause.configure(text="▶" if self.timer_paused else "⏸")
            except Exception:
                pass
            return

        # -------------------------------------------------------------
        # 2. CYBER HUD
        # -------------------------------------------------------------
        if design == "cyber_hud":
            try:
                hud_status = "PAUSED" if self.timer_paused else "ACTIVE" if self.timer_running else "ONLINE"
                hud_color = "#eab308" if self.timer_paused else "#06b6d4" if self.timer_running else "#22d3ee"
                if hasattr(self, "mini_lbl_status") and self.mini_lbl_status.winfo_exists():
                    self.mini_lbl_status.configure(text=f"[SYS.HUD // {hud_status}]", fg=hud_color)
                if hasattr(self, "mini_lbl_timer") and self.mini_lbl_timer.winfo_exists():
                    self.mini_lbl_timer.configure(text=f"TMR: {time_str}", fg=hud_color)
                if hasattr(self, "mini_lbl_clock") and self.mini_lbl_clock.winfo_exists():
                    self.mini_lbl_clock.configure(text=f"CLK: {now_str}")
                if hasattr(self, "mini_main_frame") and self.mini_main_frame.winfo_exists():
                    self.mini_main_frame.configure(highlightbackground=hud_color)
                if hasattr(self, "mini_lbl_op_val") and self.mini_lbl_op_val.winfo_exists():
                    self.mini_lbl_op_val.configure(text=f"{self.widget_opacity.get()}%")
            except Exception:
                pass
            return

        # -------------------------------------------------------------
        # 3. RETRO LED
        # -------------------------------------------------------------
        if design == "retro_led":
            try:
                led_stat = "[PAUSE]" if self.timer_paused else "[RUNNING]" if self.timer_running else "[READY]"
                led_color = "#eab308" if self.timer_paused else "#22c55e"
                if hasattr(self, "mini_lbl_status") and self.mini_lbl_status.winfo_exists():
                    self.mini_lbl_status.configure(text=f"▶ {led_stat} {mode_lbl.upper()}", fg=led_color)
                if hasattr(self, "mini_lbl_timer") and self.mini_lbl_timer.winfo_exists():
                    self.mini_lbl_timer.configure(text=time_str, fg=led_color)
                if hasattr(self, "mini_lbl_clock") and self.mini_lbl_clock.winfo_exists():
                    self.mini_lbl_clock.configure(text=now_str, fg="#86efac")
                if hasattr(self, "mini_main_frame") and self.mini_main_frame.winfo_exists():
                    self.mini_main_frame.configure(highlightbackground=led_color)
                if hasattr(self, "mini_lbl_op_val") and self.mini_lbl_op_val.winfo_exists():
                    self.mini_lbl_op_val.configure(text=f"{self.widget_opacity.get()}%")
            except Exception:
                pass
            return

        # -------------------------------------------------------------
        # 4. CLEAN CARD & 5. STANDARD
        # -------------------------------------------------------------
        try:
            if hasattr(self, "mini_lbl_status") and self.mini_lbl_status.winfo_exists():
                self.mini_lbl_status.configure(text=stat_txt)
            if hasattr(self, "mini_lbl_timer") and self.mini_lbl_timer.winfo_exists():
                self.mini_lbl_timer.configure(text=time_str, fg=time_color)
            if hasattr(self, "mini_lbl_clock") and self.mini_lbl_clock.winfo_exists():
                self.mini_lbl_clock.configure(text=f"🕒 {now_str}")
            if hasattr(self, "mini_main_frame") and self.mini_main_frame.winfo_exists():
                self.mini_main_frame.configure(highlightbackground=time_color)
            if hasattr(self, "mini_lbl_op_val") and self.mini_lbl_op_val.winfo_exists():
                self.mini_lbl_op_val.configure(text=f"{self.widget_opacity.get()}%")
            if hasattr(self, "mini_btn_clock_toggle") and self.mini_btn_clock_toggle.winfo_exists():
                is_on = self.show_current_time_compact.get()
                self.mini_btn_clock_toggle.configure(
                    bg=ACCENT_BLUE if is_on else "#374151",
                    font=("Arial", 10, "bold" if is_on else "normal")
                )
        except Exception:
            pass
        
    def get_mode_label(self, mode):
        if self.lang == "ko":
            labels = {
                "shutdown": "종료", "restart": "재시작", "reboot": "재시작",
                "sleep": "절전", "hibernate": "최대 절전", "screenoff": "화면끄기",
                "logout": "로그아웃", "lock": "화면 잠금", "alarm": "알람"
            }
            return labels.get(mode, "알 수 없음")
        else:
            labels = {
                "shutdown": "Shutdown", "restart": "Restart", "reboot": "Restart",
                "sleep": "Sleep", "hibernate": "Hibernate", "screenoff": "Screen Off",
                "logout": "Log out", "lock": "Lock Screen", "alarm": "Alarm"
            }
            return labels.get(mode, "Unknown")

    def get_system_idle_seconds(self):
        """Windows API GetLastInputInfo를 통해 사용자의 마지막 입력 경과 시간(초)을 감지합니다."""
        try:
            import ctypes
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
                return max(0.0, millis / 1000.0)
        except Exception:
            pass
        return 999999.0

    def clean_temp_files_safe(self):
        """종료/제어 직전 임시 폴더(%TEMP%) 파일 안전 자동 정리"""
        def _clean_worker():
            cleaned = 0
            for env_key in ["TEMP", "TMP"]:
                tdir = os.environ.get(env_key)
                if tdir and os.path.isdir(tdir):
                    try:
                        for fname in os.listdir(tdir):
                            fpath = os.path.join(tdir, fname)
                            try:
                                if os.path.isfile(fpath) or os.path.islink(fpath):
                                    os.remove(fpath)
                                    cleaned += 1
                                elif os.path.isdir(fpath):
                                    import shutil
                                    shutil.rmtree(fpath, ignore_errors=True)
                                    cleaned += 1
                            except Exception:
                                pass
                    except Exception:
                        pass
            msg = f"종료 전 임시 파일 자동 정리 완료 ({cleaned}개 정리)" if self.lang == "ko" else f"Pre-shutdown temp files cleaned ({cleaned} items)"
            self.log_event(msg)
        threading.Thread(target=_clean_worker, daemon=True).start()

    def set_mode(self, mode):
        self.mode = mode
        for m_id, btn in self.mode_buttons.items():
            if m_id == mode:
                color = ACCENT_RED if mode == "shutdown" else ACCENT_BLUE
                btn.configure(bg=color, fg="white")
            else:
                btn.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            
    def set_run_type(self, run_type):
        """시간 타이머 모드 vs 특정 시각 예약 모드 전환"""
        if self.timer_running:
            err_title = "오류" if self.lang == "ko" else "Error"
            err_msg = "예약이 이미 가동 중일 때는 변경할 수 없습니다. 리셋 후 변경하십시오." if self.lang == "ko" else "Cannot switch mode while a task is running. Please reset first."
            messagebox.showwarning(err_title, err_msg)
            return
            
        self.run_type = run_type
        if run_type == "timer":
            self.btn_type_timer.configure(bg="#3b82f6", fg="white")
            self.btn_type_schedule.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            
            # 레이블 및 가이드 가동 변경
            self.lbl_input_guide.configure(text="[타이머] 지정된 시간/분/초 후 동작을 수행합니다." if self.lang == "ko" else "[Timer Mode] Specify delay in hours/minutes/seconds.")
            self.lbl_field_1.configure(text="시" if self.lang == "ko" else "H")
            self.lbl_field_2.configure(text="분" if self.lang == "ko" else "M")
            self.lbl_field_3.grid(row=0, column=2, padx=5) # 초 필드 다시 활성화
            self.ent_s.grid(row=1, column=2, padx=5)
            self.btn_start.configure(text="▶ 타이머 시작" if self.lang == "ko" else "▶ Start Timer")
            
            # 기본값 설정
            self.ent_h.delete(0, tk.END)
            self.ent_h.insert(0, "0")
            self.ent_m.delete(0, tk.END)
            self.ent_m.insert(0, "30")
            self.ent_s.delete(0, tk.END)
            self.ent_s.insert(0, "0")
        else:
            self.btn_type_timer.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            self.btn_type_schedule.configure(bg="#3b82f6", fg="white")
            
            # 레이블 및 가이드 가동 변경
            self.lbl_input_guide.configure(text="[특정 예약 시각 지정] 오늘/내일 몇 시 몇 분에 실행할지 24시 형식으로 입력하십시오." if self.lang == "ko" else "[Clock Mode] Specify target hour and minute (24h format).")
            self.lbl_field_1.configure(text="실행 시(0~23)" if self.lang == "ko" else "Hour (0-23)")
            self.lbl_field_2.configure(text="실행 분(0~59)" if self.lang == "ko" else "Minute (0-59)")
            self.lbl_field_3.grid_forget() # 스케줄러 시각 지정에서는 초 필요없음
            self.ent_s.grid_forget()
            self.btn_start.configure(text="▶ 특정 시각 예약 가동" if self.lang == "ko" else "▶ Start Clock Timer")
            
            # 현재 시각 기준으로 기본값 설정 (예: 1시간 뒤 정시)
            now = datetime.datetime.now()
            default_h = (now.hour + 1) % 24
            self.ent_h.delete(0, tk.END)
            self.ent_h.insert(0, str(default_h))
            self.ent_m.delete(0, tk.END)
            self.ent_m.insert(0, "00")

    def render_favorites(self):
        if hasattr(self, 'fav_listbox'):
            self.fav_listbox.delete(0, tk.END)
            for idx, item in enumerate(self.favorites):
                mode_lbl = self.get_mode_label(item["mode"])
                duration_minutes = int(item["seconds"] / 60)
                suffix = "분" if self.lang == "ko" else " mins"
                self.fav_listbox.insert(tk.END, f" {idx+1}. [{mode_lbl}] {item['label']} ({duration_minutes}{suffix})")
            
    def on_fav_double_click(self, event):
        selection = self.fav_listbox.curselection()
        if selection:
            # 즐겨찾기 스케줄은 범용적으로 경과 타이머 형식으로 작동
            self.set_run_type("timer")
            idx = selection[0]
            fav = self.favorites[idx]
            self.set_mode(fav["mode"])
            self.start_timer_with_seconds(fav["seconds"])
            
    def delete_favorite_action(self):
        selection = self.fav_listbox.curselection()
        if not selection:
            warn_title = "선택 없음" if self.lang == "ko" else "No Selection"
            warn_msg = "수정 또는 삭제할 즐겨찾기 항목을 목록에서 선택해 주십시오." if self.lang == "ko" else "Please select a favorite preset from the list."
            messagebox.showwarning(warn_title, warn_msg)
            return
        idx = selection[0]
        fav = self.favorites[idx]
        confirm_title = "즐겨찾기 삭제" if self.lang == "ko" else "Delete Favorite"
        confirm_msg = f"선택한 즐겨찾기 [{fav['label']}]을(를) 영구 파기하시겠습니까?" if self.lang == "ko" else f"Are you sure you want to permanently delete the favorite [{fav['label']}]?"
        confirm = messagebox.askyesno(confirm_title, confirm_msg)
        if confirm:
            self.favorites.pop(idx)
            self.save_favorites()
            self.render_favorites()
            msg = f"즐겨찾기 [{fav['label']}] 항목이 제거되었습니다." if self.lang == "ko" else f"Favorite [{fav['label']}] has been removed."
            self.log_event(msg, in_app_toast=True)

    def add_favorite_dialog(self):
        self.open_favorite_editor_dialog(None)

    def edit_favorite_dialog(self):
        selection = self.fav_listbox.curselection()
        if not selection:
            warn_title = "선택 없음" if self.lang == "ko" else "No Selection"
            warn_msg = "수정 또는 삭제할 즐겨찾기 항목을 목록에서 선택해 주십시오." if self.lang == "ko" else "Please select a favorite preset from the list."
            messagebox.showwarning(warn_title, warn_msg)
            return
        idx = selection[0]
        self.open_favorite_editor_dialog(idx)

    def open_favorite_editor_dialog(self, edit_idx):
        dialog = tk.Toplevel(self.root)
        dialog.title(("즐겨찾기 추가" if edit_idx is None else "즐겨찾기 수정") if self.lang == "ko" else ("Add Favorite" if edit_idx is None else "Edit Favorite"))
        dialog.geometry("374x280")
        dialog.configure(bg=DARK_BG)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog relative to main window
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 187
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 140
        dialog.geometry(f"+{x}+{y}")
        
        # Initial values
        initial_label = ""
        initial_mode = "shutdown"
        initial_h = "0"
        initial_m = "15"
        initial_s = "0"
        
        if edit_idx is not None:
            fav = self.favorites[edit_idx]
            initial_label = fav["label"]
            initial_mode = fav["mode"]
            secs = fav["seconds"]
            h = secs // 3600
            m = (secs % 3600) // 60
            s = secs % 60
            initial_h = str(h)
            initial_m = str(m)
            initial_s = str(s)
            
        # Entry widgets
        lbl_title_val = "⭐ 즉시 실행 즐겨찾기 편집기" if self.lang == "ko" else "⭐ Quick Preset Editor"
        lbl_title = tk.Label(dialog, text=lbl_title_val, font=("Arial", 10, "bold"), fg="#3b82f6", bg=DARK_BG)
        lbl_title.pack(pady=(12, 5))
        
        # Name Label & Entry
        lbl_name = tk.Label(dialog, text="즐겨찾기 이름 (별칭):" if self.lang == "ko" else "Favorite Name (Alias):", font=("Arial", 10), fg=TEXT_COLOR, bg=DARK_BG)
        lbl_name.pack(anchor="w", padx=20, pady=(5, 2))
        ent_name = tk.Entry(dialog, bg=DARK_CARD, fg=TEXT_COLOR, relief="flat", highlightthickness=1, highlightcolor=ACCENT_BLUE, insertbackground=TEXT_COLOR)
        ent_name.pack(fill="x", padx=20)
        ent_name.insert(0, initial_label)
        
        # Mode Selection Box
        lbl_mode = tk.Label(dialog, text="전원 동작 모드:" if self.lang == "ko" else "Power Operation Mode:", font=("Arial", 10), fg=TEXT_COLOR, bg=DARK_BG)
        lbl_mode.pack(anchor="w", padx=20, pady=(5, 2))
        
        mode_grid = tk.Frame(dialog, bg=DARK_BG)
        mode_grid.pack(fill="x", padx=20, pady=2)
        
        mode_opts = {
            "shutdown": "종료 (Shutdown)" if self.lang == "ko" else "Shutdown",
            "restart": "재시작 (Restart)" if self.lang == "ko" else "Restart",
            "sleep": "절전 (Sleep)" if self.lang == "ko" else "Sleep",
            "screenoff": "화면끄기 (ScreenOff)" if self.lang == "ko" else "Screen Off",
            "logout": "로그아웃 (Logout)" if self.lang == "ko" else "Log Out",
            "alarm": "알람 (Alarm)" if self.lang == "ko" else "Alarm"
        }
        mode_opts_rev = {v: k for k, v in mode_opts.items()}
        current_opt = mode_opts[initial_mode]
        opt_var = tk.StringVar(value=current_opt)
        
        opt_menu = tk.OptionMenu(mode_grid, opt_var, *mode_opts.values())
        opt_menu.config(bg=DARK_CARD, fg=TEXT_COLOR, activebackground=DARK_CARD, activeforeground=TEXT_COLOR, highlightthickness=0, relief="flat", font=("Arial", 10))
        opt_menu["menu"].config(bg=DARK_CARD, fg=TEXT_COLOR, activebackground=DARK_CARD, activeforeground=TEXT_COLOR)
        opt_menu.pack(fill="x")
        
        # Duration selection
        lbl_dur = tk.Label(dialog, text="카운트다운 지속 시간:" if self.lang == "ko" else "Countdown Duration:", font=("Arial", 10), fg=TEXT_COLOR, bg=DARK_BG)
        lbl_dur.pack(anchor="w", padx=20, pady=(5, 2))
        
        dur_frame = tk.Frame(dialog, bg=DARK_BG)
        dur_frame.pack(fill="x", padx=20)
        
        ent_h = tk.Entry(dur_frame, bg=DARK_CARD, fg=TEXT_COLOR, width=5, justify="center", relief="flat", highlightthickness=1, insertbackground=TEXT_COLOR)
        ent_h.pack(side="left")
        ent_h.insert(0, initial_h)
        lbl_h = tk.Label(dur_frame, text="시간" if self.lang == "ko" else "h", font=("Arial", 10), fg=TEXT_COLOR, bg=DARK_BG)
        lbl_h.pack(side="left", padx=(2, 10))
        
        ent_m = tk.Entry(dur_frame, bg=DARK_CARD, fg=TEXT_COLOR, width=5, justify="center", relief="flat", highlightthickness=1, insertbackground=TEXT_COLOR)
        ent_m.pack(side="left")
        ent_m.insert(0, initial_m)
        lbl_m = tk.Label(dur_frame, text="분" if self.lang == "ko" else "m", font=("Arial", 10), fg=TEXT_COLOR, bg=DARK_BG)
        lbl_m.pack(side="left", padx=(2, 10))
        
        ent_s = tk.Entry(dur_frame, bg=DARK_CARD, fg=TEXT_COLOR, width=5, justify="center", relief="flat", highlightthickness=1, insertbackground=TEXT_COLOR)
        ent_s.pack(side="left")
        ent_s.insert(0, initial_s)
        lbl_s = tk.Label(dur_frame, text="초" if self.lang == "ko" else "s", font=("Arial", 10), fg=TEXT_COLOR, bg=DARK_BG)
        lbl_s.pack(side="left", padx=(2, 10))
        
        def on_save():
            name_val = ent_name.get().strip()
            if not name_val:
                if self.lang == "ko":
                    messagebox.showerror("오류", "즐겨찾기 이름을 입력해 주십시오.")
                else:
                    messagebox.showerror("Error", "Please enter a name for the favorite.")
                return
            
            try:
                h_val = int(ent_h.get() or 0)
                m_val = int(ent_m.get() or 0)
                s_val = int(ent_s.get() or 0)
            except ValueError:
                if self.lang == "ko":
                    messagebox.showerror("오류", "시간은 반드시 숫자 형태여야 합니다.")
                else:
                    messagebox.showerror("Error", "Hours, minutes, and seconds must be numbers.")
                return
                
            tot_secs = (h_val * 3600) + (m_val * 60) + s_val
            if tot_secs <= 0:
                if self.lang == "ko":
                    messagebox.showerror("오류", "지속 시간은 최소 1초 이상이어야 합니다.")
                else:
                    messagebox.showerror("Error", "Duration must be at least 1 second.")
                return
                
            sel_mode = mode_opts_rev[opt_var.get()]
            
            new_item = {
                "label": name_val,
                "mode": sel_mode,
                "seconds": tot_secs
            }
            
            if edit_idx is None:
                self.favorites.append(new_item)
                msg = f"새 즐겨찾기 스케줄 [{name_val}]이(가) 등록되었습니다." if self.lang == "ko" else f"New favorite [{name_val}] has been registered."
            else:
                self.favorites[edit_idx] = new_item
                msg = f"즐겨찾기 스케줄 [{name_val}]이(가) 수정 완료되었습니다." if self.lang == "ko" else f"Favorite [{name_val}] has been updated."
                
            self.save_favorites()
            self.render_favorites()
            self.log_event(msg, in_app_toast=True)
            dialog.destroy()
            
        btn_txt = ""
        if edit_idx is not None:
            btn_txt = "적용 완료" if self.lang == "ko" else "Update Preset"
        else:
            btn_txt = "새로 등록하기" if self.lang == "ko" else "Add Preset"

        btn_action = tk.Button(
            dialog,
            text=btn_txt,
            font=("Arial", 10, "bold"),
            bg="#10b981" if edit_idx is None else "#2563eb",
            fg="white",
            relief="flat",
            pady=6,
            command=on_save
        )
        btn_action.pack(fill="x", padx=20, pady=(15, 10))
        
        # Auto-fit dialog dimensions to inner labels and entries dynamically
        auto_fit_window(dialog, min_w=380, min_h=280, center_parent=self.root)

    def open_scheduler_popup(self):
        if hasattr(self, "popup_window") and self.popup_window and self.popup_window.winfo_exists():
            try:
                self.popup_window.deiconify()
                self.popup_window.lift()
                self.popup_window.focus_force()
            except Exception:
                pass
            return

        self.popup_window = tk.Toplevel(self.root)
        self.popup_window.title("다중 스케줄러 & 실시간 모니터링" if self.lang == "ko" else "Advanced Scheduler & Monitoring Terminal")
        self.popup_window.geometry("616x780")
        self.popup_window.configure(bg=DARK_BG)
        self.popup_window.transient(self.root)
        
        # Center dialog
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 308
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 390
        self.popup_window.geometry(f"+{x}+{y}")

        # Frame with scrollable contents
        popup_scroll = ScrollableFrame(self.popup_window, bg=DARK_BG)
        popup_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        parent = popup_scroll.scrollable_frame
        
        # Title
        title_txt = "📅 스케줄러 관리" if self.lang == "ko" else "📅 Scheduler Control"
        tk.Label(parent, text=title_txt, font=("Arial", 12, "bold"), fg="#3b82f6", bg=DARK_BG).pack(pady=(10, 5))
        
        # 1. New Rule Form
        frm_add_text = "새로운 규칙 등록" if self.lang == "ko" else "Register New Rule"
        frm_add = tk.LabelFrame(parent, bg=DARK_CARD, text=frm_add_text, font=("Arial", 10, "bold"), fg="#9ca3af", bd=1, relief="solid")
        frm_add.pack(fill="x", padx=15, pady=10)
        
        # Variables for popup form
        pop_var_label = tk.StringVar()
        pop_var_mode = tk.StringVar(value="shutdown")
        pop_var_type = tk.StringVar(value="daily")
        pop_var_force = tk.BooleanVar(value=True)
        pop_var_beep = tk.BooleanVar(value=True)
        pop_var_h = tk.StringVar(value="22")
        pop_var_m = tk.StringVar(value="00")
        pop_var_interval = tk.IntVar(value=45)
        
        # Form Layout (Label)
        frm_pop_name_header = tk.Frame(frm_add, bg=DARK_CARD)
        frm_pop_name_header.pack(fill="x", padx=10, pady=(5, 1))

        lbl_name_txt = "스케줄 이름 (메모):" if self.lang == "ko" else "Schedule Title (Memo):"
        tk.Label(frm_pop_name_header, text=lbl_name_txt, font=("Arial", 10, "bold"), fg=TEXT_COLOR, bg=DARK_CARD).pack(side="left")

        # 자주 사용하는 10개 제목 프리셋 선택 드롭다운 (팝업 창)
        pop_preset_titles = POPULAR_SCHEDULE_TITLES_KO if self.lang == "ko" else POPULAR_SCHEDULE_TITLES_EN
        pop_placeholder = "📋 자주 쓰는 제목 (10개)..." if self.lang == "ko" else "📋 Popular Titles (10)..."
        var_pop_preset = tk.StringVar(value=pop_placeholder)

        def on_pop_preset_selected(val):
            ph = "📋 자주 쓰는 제목 (10개)..." if self.lang == "ko" else "📋 Popular Titles (10)..."
            if val and val != ph:
                pop_var_label.set(val)
                var_pop_preset.set(ph)

        om_pop_preset = tk.OptionMenu(
            frm_pop_name_header,
            var_pop_preset,
            pop_placeholder,
            *pop_preset_titles,
            command=on_pop_preset_selected
        )
        om_pop_preset.config(
            font=("Arial", 9),
            bg=DARK_BG,
            fg="#93c5fd",
            activebackground="#2563eb",
            activeforeground="white",
            highlightthickness=0,
            bd=0,
            padx=4,
            pady=0,
            cursor="hand2"
        )
        om_pop_preset["menu"].config(font=("Arial", 9), bg=DARK_CARD, fg=TEXT_COLOR)
        om_pop_preset.pack(side="right")

        ent_name = tk.Entry(frm_add, textvariable=pop_var_label, bg=DARK_BG, fg=TEXT_COLOR, bd=0, insertbackground=TEXT_COLOR, highlightthickness=1, highlightcolor="#3b82f6", font=("Arial", 10))
        ent_name.pack(fill="x", padx=10, pady=2, ipady=3)
        
        # Action selector (Buttons)
        lbl_action_txt = "트리거 대기 전원 행동:" if self.lang == "ko" else "Action Mode to Trigger:"
        tk.Label(frm_add, text=lbl_action_txt, font=("Arial", 10, "bold"), fg=TEXT_COLOR, bg=DARK_CARD).pack(anchor="w", padx=10, pady=(5, 1))
        frm_actions = tk.Frame(frm_add, bg=DARK_CARD)
        frm_actions.pack(fill="x", padx=10, pady=2)
        
        act_btns = {}
        def select_pop_action(aid):
            pop_var_mode.set(aid)
            for k, btn in act_btns.items():
                if k == aid:
                    btn.configure(bg="#3b82f6", fg="white")
                else:
                    btn.configure(bg=DARK_BG, fg=TEXT_COLOR)
                    
        act_options_pop = {
            "shutdown": "종료" if self.lang == "ko" else "Shut down",
            "restart": "재시동" if self.lang == "ko" else "Restart",
            "sleep": "절전" if self.lang == "ko" else "Sleep",
            "screenoff": "화면끔" if self.lang == "ko" else "Screen Off",
            "logout": "아웃" if self.lang == "ko" else "Log out",
            "alarm": "알람" if self.lang == "ko" else "Alarm"
        }
        for act_id, act_nm in act_options_pop.items():
            b = tk.Button(
                frm_actions, text=act_nm, font=("Arial", 10, "bold"),
                bg="#3b82f6" if act_id == "shutdown" else DARK_BG,
                fg="white" if act_id == "shutdown" else TEXT_COLOR,
                padx=5, pady=3, relief="flat",
                command=lambda opt=act_id: select_pop_action(opt)
            )
            b.pack(side="left", expand=True, fill="x", padx=1)
            act_btns[act_id] = b

        # Type Options
        lbl_type_txt = "반복 플랜 타입:" if self.lang == "ko" else "Interval Repeat Type:"
        tk.Label(frm_add, text=lbl_type_txt, font=("Arial", 10, "bold"), fg=TEXT_COLOR, bg=DARK_CARD).pack(anchor="w", padx=10, pady=(5, 1))
        frm_types = tk.Frame(frm_add, bg=DARK_CARD)
        frm_types.pack(fill="x", padx=10, pady=2)
        
        typ_btns = {}
        frm_time_fields = tk.Frame(frm_add, bg=DARK_CARD)
        frm_time_fields.pack(fill="x", padx=10, pady=2)
        
        lbl_helper_text = "정밀 알람 격발 시각 (24시 형식):" if self.lang == "ko" else "Precise alarm trigger time (24h format):"
        lbl_helper = tk.Label(frm_time_fields, text=lbl_helper_text, font=("Arial", 10), fg="#9ca3af", bg=DARK_CARD)
        lbl_helper.pack(anchor="w")
        
        # Time option menus
        frm_h_m = tk.Frame(frm_time_fields, bg=DARK_CARD)
        frm_h_m.pack(anchor="w", pady=2)
        
        hours_opt = [f"{i:02d}" for i in range(24)]
        mins_opt = [f"{i:02d}" for i in range(60)]
        
        opt_h = tk.OptionMenu(frm_h_m, pop_var_h, *hours_opt)
        opt_h.config(bg=DARK_BG, fg=TEXT_COLOR, relief="flat", highlightthickness=0)
        opt_h.pack(side="left")
        
        tk.Label(frm_h_m, text=":", font=("Arial", 10, "bold"), fg=TEXT_COLOR, bg=DARK_CARD, padx=5).pack(side="left")
        
        opt_m = tk.OptionMenu(frm_h_m, pop_var_m, *mins_opt)
        opt_m.config(bg=DARK_BG, fg=TEXT_COLOR, relief="flat", highlightthickness=0)
        opt_m.pack(side="left")
        
        # Weekly checkboxes
        frm_wk = tk.Frame(frm_time_fields, bg=DARK_CARD)
        wk_vars = []
        day_names_pop = ["일", "월", "화", "수", "목", "금", "토"] if self.lang == "ko" else ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for idx, d_nm in enumerate(day_names_pop):
            v = tk.BooleanVar(value=True if idx in [1,2,3,4,5] else False)
            wk_vars.append(v)
            tk.Checkbutton(frm_wk, text=d_nm, variable=v, bg=DARK_CARD, fg=TEXT_COLOR, selectcolor=DARK_BG, font=("Arial", 10)).pack(side="left", padx=1)
            
        # Interval fields
        frm_int = tk.Frame(frm_time_fields, bg=DARK_CARD)
        tk.Label(frm_int, text="간격:" if self.lang == "ko" else "Interval:", font=("Arial", 10), fg="#9ca3af", bg=DARK_CARD).pack(side="left")
        tk.Entry(frm_int, textvariable=pop_var_interval, width=5, bg=DARK_BG, fg=TEXT_COLOR, justify="center", bd=0, highlightthickness=1, insertbackground=TEXT_COLOR).pack(side="left", padx=5)
        tk.Label(frm_int, text="분 마다 동작" if self.lang == "ko" else "minutes cycle", font=("Arial", 10, "bold"), fg=TEXT_COLOR, bg=DARK_CARD).pack(side="left")

        def select_pop_type(tid):
            pop_var_type.set(tid)
            for k, btn in typ_btns.items():
                if k == tid:
                    btn.configure(bg="#3b82f6", fg="white")
                else:
                    btn.configure(bg=DARK_BG, fg=TEXT_COLOR)
            
            frm_h_m.pack_forget()
            frm_wk.pack_forget()
            frm_int.pack_forget()
            
            if tid in ["once", "daily"]:
                lbl_helper.configure(text="정밀 알람 격발 시각 (24시 형식):" if self.lang == "ko" else "Precise alarm trigger time (24h format):")
                frm_h_m.pack(anchor="w", pady=2)
            elif tid == "weekly":
                lbl_helper.configure(text="정밀 알람 격발 시각 및 적용 요일 선택:" if self.lang == "ko" else "Select alarm time & active days of week:")
                frm_h_m.pack(anchor="w", pady=2)
                frm_wk.pack(anchor="w", pady=2)
            elif tid == "interval":
                lbl_helper.configure(text="반복 순환 루프 주기 지정:" if self.lang == "ko" else "Specify repeating loop interval:")
                frm_int.pack(anchor="w", pady=2)
                
        for typ_id, typ_nm in [
            ("once", "일회성" if self.lang == "ko" else "Once"),
            ("daily", "매일" if self.lang == "ko" else "Daily"),
            ("weekly", "요일 반복" if self.lang == "ko" else "Weekly"),
            ("interval", "동작 주기" if self.lang == "ko" else "Interval")
        ]:
            b = tk.Button(
                frm_types, text=typ_nm, font=("Arial", 10, "bold"),
                bg="#3b82f6" if typ_id == "daily" else DARK_BG,
                fg="white" if typ_id == "daily" else TEXT_COLOR,
                padx=5, pady=3, relief="flat",
                command=lambda opt=typ_id: select_pop_type(opt)
            )
            b.pack(side="left", expand=True, fill="x", padx=1)
            typ_btns[typ_id] = b

        # Flags (Force Close, Warning Beep)
        frm_flg = tk.Frame(frm_add, bg=DARK_CARD)
        frm_flg.pack(fill="x", padx=10, pady=5)
        
        force_txt = "파일/앱 강제 종료" if self.lang == "ko" else "Force close apps"
        beep_txt = "1분 전 비프 경고" if self.lang == "ko" else "Audio Warning (1m before)"
        tk.Checkbutton(frm_flg, text=force_txt, variable=pop_var_force, bg=DARK_CARD, fg=TEXT_COLOR, selectcolor=DARK_BG, font=("Arial", 10)).pack(side="left", expand=True)
        tk.Checkbutton(frm_flg, text=beep_txt, variable=pop_var_beep, bg=DARK_CARD, fg=TEXT_COLOR, selectcolor=DARK_BG, font=("Arial", 10)).pack(side="left", expand=True)

        # Submit Action
        def submit_pop():
            lbl = pop_var_label.get().strip()
            if not lbl:
                err_title = "입력 미달" if self.lang == "ko" else "Missing Input"
                err_msg = "규칙의 스케줄 이름을 입력해 주십시오." if self.lang == "ko" else "Please enter a schedule name."
                messagebox.showerror(err_title, err_msg)
                return
            
            tid = pop_var_type.get()
            act = pop_var_mode.get()
            
            new_rule = {
                "id": f"rule-{int(datetime.datetime.now().timestamp() * 1000)}",
                "label": lbl,
                "type": tid,
                "mode": act,
                "force_close": pop_var_force.get(),
                "warning_beep": pop_var_beep.get(),
                "is_active": True,
                "created_at": datetime.datetime.now().isoformat(),
                "last_executed": ""
            }
            
            if tid in ["once", "daily", "weekly"]:
                new_rule["time"] = f"{pop_var_h.get()}:{pop_var_m.get()}"
                
            if tid == "weekly":
                sel_days = [idx for idx, v in enumerate(wk_vars) if v.get()]
                if not sel_days:
                    err_title = "입력 미달" if self.lang == "ko" else "Missing Input"
                    err_msg = "체크된 요일이 존재하지 않습니다. 요일을 최소 1개 이상 선택하십시오." if self.lang == "ko" else "Please select at least one day."
                    messagebox.showerror(err_title, err_msg)
                    return
                new_rule["days"] = sel_days
                
            if tid == "interval":
                try:
                    interval_min = int(pop_var_interval.get())
                    if interval_min <= 0:
                        raise ValueError()
                except:
                    err_title = "입력 오류" if self.lang == "ko" else "Input Error"
                    err_msg = "순환 주기는 1분 이상 설정해 주셔야 정상 감시됩니다." if self.lang == "ko" else "Repeat interval must be at least 1 minute."
                    messagebox.showerror(err_title, err_msg)
                    return
                new_rule["interval_minutes"] = interval_min
                
            self.rules.append(new_rule)
            self.save_rules()
            self.render_rules_list()
            
            success_msg = "팝업창에서 스케줄 규칙을 성공적으로 추가하였습니다." if self.lang == "ko" else "Schedule rule added successfully from popup."
            self.log_event(success_msg, in_app_toast=True)
            
            # Reset form
            pop_var_label.set("")
            select_pop_action("shutdown")
            select_pop_type("daily")
            pop_var_force.set(True)
            pop_var_beep.set(True)
            
        submit_btn_txt = "팝업창에서 규칙 등록 및 엔진 합류" if self.lang == "ko" else "Register Rule & Start Background Sleep Guard"
        tk.Button(frm_add, text=submit_btn_txt, font=("Arial", 10, "bold"), bg="#10b981", fg="white", relief="flat", pady=6, command=submit_pop).pack(fill="x", padx=10, pady=(5, 10))

        # 2. Scrolled Rules monitoring list
        daemon_lbl_txt = "📋 상시 엔진 모니터링 현황" if self.lang == "ko" else "📋 Daemon Engine Realtime Logs"
        tk.Label(parent, text=daemon_lbl_txt, font=("Arial", 10, "bold"), fg="#9ca3af", bg=DARK_BG).pack(anchor="w", padx=15, pady=(15, 2))
        
        self.popup_rules_list_container = ScrollableFrame(parent, bg=DARK_BG)
        self.popup_rules_list_container.pack(fill="both", expand=True, padx=15, pady=5)
        
        # 3. Synchronize rendering
        self.render_rules_list()

    def start_timer(self):
        if self.timer_running:
            self.toggle_pause()
            return

        try:
            h = int(self.ent_h.get() or 0)
            m = int(self.ent_m.get() or 0)
            
            if self.run_type == "timer":
                s = int(self.ent_s.get() or 0)
                total = (h * 3600) + (m * 60) + s
                if total <= 0:
                    err_title = "오류" if self.lang == "ko" else "Error"
                    err_msg = "시간을 1초 이상으로 입력하세요." if self.lang == "ko" else "Please enter a time of at least 1 second."
                    messagebox.showwarning(err_title, err_msg)
                    return
                self.start_timer_with_seconds(total)
            else:
                # 특정 예약 시각 모드 (Schedule) 에 대한 스마트 정밀 계산 엔진
                if not (0 <= h <= 23) or not (0 <= m <= 59):
                    err_title = "오류" if self.lang == "ko" else "Error"
                    err_msg = "시는 0~23 사이, 분은 0~59 사이로 입력하여 주십시오." if self.lang == "ko" else "Please enter hours between 0-23 and minutes between 0-59."
                    messagebox.showerror(err_title, err_msg)
                    return
                
                now = datetime.datetime.now()
                target_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                
                # 예약한 시각이 현재 시각보다 같거나 이전이면 자동으로 익일(다음날)로 부드럽게 예약 변경
                if target_time <= now:
                    target_time += datetime.timedelta(days=1)
                
                # 차이 초 구하기
                total_seconds = int((target_time - now).total_seconds())
                
                # 스케줄 정보 콤보 팝업 메시지
                mode_txt = self.get_mode_label(self.mode)
                if self.lang == "ko":
                    date_str = target_time.strftime("%m월 %d일 %H시 %M분")
                    conf_title = "예약 확인"
                    conf_msg = f"설정 시각: {date_str}\n해당 시간 정각에 컴퓨터 [{mode_txt}] 예약이 진행됩니다. 시작하시겠습니까?"
                else:
                    date_str = target_time.strftime("%B %d, %H:%M")
                    conf_title = "Confirm Schedule"
                    conf_msg = f"Target Time: {date_str}\nComputer [{mode_txt}] will be triggered at this exact time. Do you want to start?"
                
                ans = messagebox.askyesno(conf_title, conf_msg)
                if not ans:
                    return
                    
                self.start_timer_with_seconds(total_seconds)
        except ValueError:
            err_title = "오류" if self.lang == "ko" else "Error"
            err_msg = "숫자만 입력할 수 있습니다." if self.lang == "ko" else "Only numbers can be entered."
            messagebox.showerror(err_title, err_msg)

    def start_timer_with_seconds(self, seconds, show_notification=True):
        self.remaining_seconds = seconds
        self.timer_running = True
        self.timer_paused = False
        self.force_flag = self.force_close_enabled.get() if hasattr(self, "force_close_enabled") else True
        pause_txt = "⏸ 일시정지" if self.lang == "ko" else "⏸ Pause"
        self.btn_start.configure(text=pause_txt, bg=ACCENT_YELLOW)
        self.update_countdown()
        self.sync_always_on_top_mini_win()
        
        # 순수 창작 Native Engine 연동: 하드웨어 RTC 웨이크업 타이머 및 시스템 절전 차단 가동
        if native_bridge:
            try:
                native_bridge.set_hardware_wake_timer(float(seconds))
                native_bridge.set_sleep_prevention(prevent_sleep=True, keep_display=False)
            except Exception:
                pass

        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        duration_str = f"{h:02d}:{m:02d}:{s:02d}"
        log_msg = f"전원 예약 설정 시작: {duration_str} 후 [{self.get_mode_label(self.mode)}]" if self.lang == "ko" else f"Power reservation started: {duration_str} remains until [{self.get_mode_label(self.mode)}]"
        self.log_event(log_msg)

        if show_notification:
            h_tot = seconds // 3600
            m_tot = (seconds % 3600) // 60
            s_tot = seconds % 60
            time_parts = []
            if self.lang == "ko":
                if h_tot > 0:
                    time_parts.append(f"{h_tot}시간")
                if m_tot > 0:
                    time_parts.append(f"{m_tot}분")
                if s_tot > 0 or not time_parts:
                    time_parts.append(f"{s_tot}초")
            else:
                if h_tot > 0:
                    time_parts.append(f"{h_tot}h")
                if m_tot > 0:
                    time_parts.append(f"{m_tot}m")
                if s_tot > 0 or not time_parts:
                    time_parts.append(f"{s_tot}s")
            total_time_str = " ".join(time_parts)

            toast_title = "⏱️ 타이머 가동 시작" if self.lang == "ko" else "⏱️ Timer Started"
            toast_msg = f"{total_time_str} 후 컴퓨터 [{self.get_mode_label(self.mode)}] 예약이 정상 작동됩니다." if self.lang == "ko" else f"Computer [{self.get_mode_label(self.mode)}] will be triggered in {total_time_str}."
            self.show_toast(
                title=toast_title,
                message=toast_msg,
                accent_color="#3b82f6" if self.mode == "shutdown" else "#f59e0b"
            )
        
    def reset_timer(self):
        self.timer_running = False
        self.timer_paused = False

        # 순수 창작 Native Engine 연동: 하드웨어 RTC 웨이크업 타이머 해제 및 절전 락 복원
        if native_bridge:
            try:
                native_bridge.cancel_hardware_wake_timer()
                native_bridge.set_sleep_prevention(prevent_sleep=False, keep_display=False)
            except Exception:
                pass

        default_text = "▶ 타이머 시작" if self.run_type == "timer" else "▶ 특정 시각 예약 가동"
        if self.lang != "ko":
            default_text = "▶ Start Timer" if self.run_type == "timer" else "▶ Start Clock Timer"
        self.btn_start.configure(text=default_text, bg=ACCENT_BLUE, state="normal")
        self.lbl_timer.configure(text="00:30:00" if self.run_type == "timer" else "00:00:00", fg=ACCENT_BLUE)
        log_msg = "전원 제어 예약 취소 / 대기 상태 초기화" if self.lang == "ko" else "Power control reservation cancelled / Idle state reset"
        self.log_event(log_msg, in_app_toast=True)
        self.update_mini_window()
        self.sync_always_on_top_mini_win()
        
    def toggle_pause(self):
        if not self.timer_running:
            return
            
        self.timer_paused = not self.timer_paused
        if self.timer_paused:
            self.btn_start.configure(text="▶ 다시 시작" if self.lang == "ko" else "▶ Resume", bg=ACCENT_BLUE)
            self.lbl_timer.configure(fg=ACCENT_YELLOW)
        else:
            self.btn_start.configure(text="⏸ 일시정지" if self.lang == "ko" else "⏸ Pause", bg=ACCENT_YELLOW)
            self.lbl_timer.configure(fg=ACCENT_BLUE)
            self.update_countdown()
        self.update_mini_window()
            
    def update_countdown(self):
        if not self.timer_running or self.timer_paused:
            self.update_mini_window()
            return
            
        if self.remaining_seconds > 0:
            h = self.remaining_seconds // 3600
            m = (self.remaining_seconds % 3600) // 60
            s = self.remaining_seconds % 60
            time_str = f"{h:02d}:{m:02d}:{s:02d}"
            
            self.lbl_timer.configure(text=time_str)
            self.remaining_seconds -= 1
            self.update_mini_window()
            self.root.after(1000, self.update_countdown)
        else:
            self.lbl_timer.configure(text="00:00:00", fg=ACCENT_RED)
            self.update_mini_window()
            self.sync_always_on_top_mini_win()
            self.open_grace_popup()

    def open_grace_popup(self, rule_data=None):
        """실제 전원 실행 전, 마지막 확인 카운트다운 팝업창 가동"""
        if self.root.state() == "withdrawn":
            self.restore_from_tray()
            
        # 팝업 대화상자 생성
        self.grace_win = tk.Toplevel(self.root)
        grace_win_title = "⚠️ 시스템 전원 제어 경고" if self.lang == "ko" else "⚠️ System Power Control Warning"
        self.grace_win.title(grace_win_title)
        
        # 파라미터 파싱
        if rule_data:
            self.grace_seconds = int(rule_data.get("grace_period_sec", self.grace_seconds_setting.get()))
            custom_msg = rule_data.get("warning_message", "")
            allow_delay = rule_data.get("allow_delay", True)
            self.force_flag = rule_data.get("force_close", self.force_close_enabled.get() if hasattr(self, "force_close_enabled") else True)
        else:
            self.grace_seconds = self.grace_seconds_setting.get()
            custom_msg = ""
            allow_delay = True
            self.force_flag = self.force_close_enabled.get() if hasattr(self, "force_close_enabled") else True

        win_height = 320 if custom_msg else 270
        self.grace_win.geometry(f"550x{win_height}")
        self.grace_win.configure(bg="#ef4444" if self.mode in ["shutdown", "restart", "reboot"] else "#3b82f6")
        self.grace_win.resizable(False, False)
        
        # 화면 정중앙 배치
        self.grace_win.update_idletasks()
        width = 550
        height = win_height
        x = (self.grace_win.winfo_screenwidth() // 2) - (width // 2)
        y = (self.grace_win.winfo_screenheight() // 2) - (height // 2)
        self.grace_win.geometry(f"{width}x{height}+{x}+{y}")
        
        self.grace_win.attributes("-topmost", True)
        self.grace_win.grab_set()
        
        # 닫기 버튼 이벤트 바인딩
        self.grace_win.protocol("WM_DELETE_WINDOW", self.cancel_grace_popup if allow_delay else lambda: None)
        
        mode_txt = self.get_mode_label(self.mode)
        
        info_frame = tk.Frame(self.grace_win, bg=DARK_BG, bd=2, relief="solid")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        lbl_info_text = f"⚠️ 잠시 후 컴퓨터가 [{mode_txt}]됩니다!" if self.lang == "ko" else f"⚠️ Computer will [{mode_txt}] shortly!"
        lbl_info = tk.Label(
            info_frame, 
            text=lbl_info_text, 
            font=("Arial", 15, "bold"), 
            fg="#ef4444" if self.mode in ["shutdown", "restart", "reboot"] else ACCENT_BLUE, 
            bg=DARK_BG,
            pady=8
        )
        lbl_info.pack()

        if custom_msg:
            lbl_custom = tk.Label(
                info_frame,
                text=custom_msg,
                font=("Arial", 10),
                fg="#f3f4f6",
                bg="#1f2937",
                wraplength=450,
                padx=10,
                pady=6
            )
            lbl_custom.pack(fill="x", padx=15, pady=(0, 5))
        
        lbl_grace_timer_text = f"{self.grace_seconds}초 후 실행" if self.lang == "ko" else f"Executing in {self.grace_seconds}s"
        self.lbl_grace_timer = tk.Label(
            info_frame, 
            text=lbl_grace_timer_text, 
            font=("Courier", 26, "bold"), 
            fg=TEXT_COLOR, 
            bg=DARK_BG
        )
        self.lbl_grace_timer.pack(pady=6)

        btn_frame = tk.Frame(info_frame, bg=DARK_BG)
        btn_frame.pack(pady=8)

        if allow_delay:
            btn_delay = tk.Button(
                btn_frame,
                text="⏳ 10분 연기 (+10 Min)" if self.lang == "ko" else "⏳ Delay 10 Min",
                font=("Arial", 10, "bold"),
                bg="#3b82f6",
                fg="white",
                relief="flat",
                padx=14,
                pady=6,
                command=self.delay_grace_popup_10min
            )
            btn_delay.pack(side="left", padx=5)

            btn_cancel_text = "❌ 전원 예약 [취소하기]" if self.lang == "ko" else "❌ Cancel Power Action"
            btn_cancel = tk.Button(
                btn_frame, 
                text=btn_cancel_text, 
                font=("Arial", 10, "bold"), 
                bg="#4b5563", 
                fg="white", 
                relief="flat", 
                padx=14, 
                pady=6, 
                command=self.cancel_grace_popup
            )
            btn_cancel.pack(side="left", padx=5)
        else:
            lbl_lock = tk.Label(
                btn_frame,
                text="🔒 관리자에 의해 강제 실행 모드로 설정됨 (사용자 취소 불가)" if self.lang == "ko" else "🔒 Enforced by administrator (Cancellation disabled)",
                font=("Arial", 10, "bold"),
                fg="#f87171",
                bg=DARK_BG
            )
            lbl_lock.pack(pady=4)
        
        self.update_grace_countdown()
        auto_fit_window(self.grace_win, min_w=550, min_h=280)

    def delay_grace_popup_10min(self):
        """사용자가 10분 연기 버튼을 클릭했을 때의 처리"""
        if hasattr(self, "grace_win") and self.grace_win.winfo_exists():
            try:
                self.grace_win.grab_release()
                self.grace_win.destroy()
            except:
                pass
        self.reset_timer()
        # 10분(600초) 타이머 가동
        self.remaining_seconds = 600
        self.timer_running = True
        self.timer_paused = False
        self.update_timer_display()
        self.root.after(1000, self.timer_tick)
        log_msg = "전원 제어 실행이 사용자에 의해 [10분 연기]되었습니다." if self.lang == "ko" else "Power action has been delayed by 10 minutes by user."
        self.log_event(log_msg, in_app_toast=True)

    def update_grace_countdown(self):
        if not hasattr(self, "grace_win") or not self.grace_win.winfo_exists():
            return
            
        if self.grace_seconds > 0:
            lbl_text = f"{self.grace_seconds}초 후 실행" if self.lang == "ko" else f"Executing in {self.grace_seconds}s"
            self.lbl_grace_timer.configure(text=lbl_text)
            self.play_sound_theme("tick")
            self.grace_seconds -= 1
            self.grace_win.after(1000, self.update_grace_countdown)
        else:
            try:
                self.grace_win.grab_release()
                self.grace_win.destroy()
            except:
                pass
            self.execute_power_action()
            
    def cancel_grace_popup(self):
        if hasattr(self, "grace_win") and self.grace_win.winfo_exists():
            try:
                self.grace_win.grab_release()
                self.grace_win.destroy()
            except:
                pass
        self.reset_timer()
        info_msg = "전원 예약 제어가 안전하게 취소되었습니다." if self.lang == "ko" else "Power control reservation has been successfully cancelled."
        self.log_event(info_msg, in_app_toast=True)

    def trigger_alarm_popup(self, alarm_label=""):
        """스케줄러 예약 알람 전용 팝업 모달 가동 및 알람 챠임 반복 연주"""
        if hasattr(self, "alarm_win") and self.alarm_win and self.alarm_win.winfo_exists():
            return # Already showing
            
        self.alarm_win = tk.Toplevel(self.root)
        alarm_win_title = "⏰ 스케줄러 예약 알람 경보" if self.lang == "ko" else "⏰ Scheduler Alarm Alert"
        self.alarm_win.title(alarm_win_title)
        self.alarm_win.geometry("506x280")
        self.alarm_win.configure(bg="#ec4899") # Gorgeous deep pink/rose theme
        self.alarm_win.resizable(False, False)
        
        # Center of screen
        self.alarm_win.update_idletasks()
        width = 506
        height = 280
        x = (self.alarm_win.winfo_screenwidth() // 2) - (width // 2)
        y = (self.alarm_win.winfo_screenheight() // 2) - (height // 2)
        self.alarm_win.geometry(f"{width}x{height}+{x}+{y}")
        
        self.alarm_win.attributes("-topmost", True)
        self.alarm_win.grab_set()
        
        self.alarm_win.protocol("WM_DELETE_WINDOW", self.dismiss_alarm_popup)
        
        info_frame = tk.Frame(self.alarm_win, bg=DARK_BG, bd=2, relief="solid")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Icon label with bouncing animation character
        lbl_icon = tk.Label(
            info_frame,
            text="⏰   ⏰   ⏰",
            font=("Arial", 28),
            fg="#ec4899",
            bg=DARK_BG,
            pady=10
        )
        lbl_icon.pack()
        
        title_txt = f"[{alarm_label}] 알람 시간이 완료되었습니다!" if self.lang == "ko" else f"[{alarm_label}] Alarm triggered!"
        lbl_title = tk.Label(
            info_frame,
            text=title_txt,
            font=("Arial", 14, "bold"),
            fg="white",
            bg=DARK_BG,
            wraplength=400,
            justify="center"
        )
        lbl_title.pack(pady=5)
        
        desc_txt = "지정한 오늘의 예약 시간 혹은 간편 예약 주기가 만료되어 경보를 호출했습니다." if self.lang == "ko" else "The scheduled time or quick reservation interval has finished."
        lbl_desc = tk.Label(
            info_frame,
            text=desc_txt,
            font=("Arial", 10),
            fg=TEXT_COLOR,
            bg=DARK_BG,
            wraplength=400,
            justify="center"
        )
        lbl_desc.pack(pady=5)
        
        btn_ok = tk.Button(
            info_frame,
            text="✔️ 확인 및 알람 해제" if self.lang == "ko" else "✔️ Clear Alarm",
            font=("Arial", 12, "bold"),
            bg="#ec4899",
            fg="white",
            activebackground="#db2777",
            activeforeground="white",
            relief="flat",
            padx=25,
            pady=8,
            command=self.dismiss_alarm_popup
        )
        btn_ok.pack(pady=15)
        
        auto_fit_window(self.alarm_win, min_w=506, min_h=280)
        
        # Start sound loop
        self.is_alarm_ringing = True
        self.ring_alarm_loop()
        
    def ring_alarm_loop(self):
        if not hasattr(self, "is_alarm_ringing") or not self.is_alarm_ringing:
            return
        if not hasattr(self, "alarm_win") or not self.alarm_win or not self.alarm_win.winfo_exists():
            return
            
        self.play_sound_theme("alarm")
        # Loop every 3.5 seconds
        self.alarm_win.after(3500, self.ring_alarm_loop)
        
    def dismiss_alarm_popup(self):
        self.is_alarm_ringing = False
        if hasattr(self, "alarm_win") and self.alarm_win.winfo_exists():
            try:
                self.alarm_win.grab_release()
                self.alarm_win.destroy()
            except:
                pass
        self.log_event("예약 알람 알림창이 해제되었습니다." if self.lang == "ko" else "Alarm alert has been dismissed.", in_app_toast=True)

    def get_soonest_trigger_info(self):
        now = datetime.datetime.now()
        candidates = []
        
        # 1. Main Timer
        if hasattr(self, "timer_running") and self.timer_running and not getattr(self, "timer_paused", False):
            rem_sec = getattr(self, "remaining_seconds", 0)
            if rem_sec > 0:
                mode_lbl = self.get_mode_label(self.mode)
                timer_title = f"⏱️ 간편 타이머 [{mode_lbl}]" if self.lang == "ko" else f"⏱️ Quick Timer [{mode_lbl}]"
                candidates.append((rem_sec, timer_title))
                
        # 2. Advanced Scheduler Rules
        if hasattr(self, "rules") and self.rules:
            for rule in self.rules:
                if not rule.get("is_active", True):
                    continue
                
                r_type = rule.get("type", "daily")
                time_str = rule.get("time", "00:00")
                tgt_h, tgt_m = 0, 0
                if ":" in time_str:
                    try:
                        tgt_h, tgt_m = map(int, time_str.split(":"))
                    except:
                        pass
                
                target_dt = None
                if r_type in ["once", "daily"]:
                    target_dt = now.replace(hour=tgt_h, minute=tgt_m, second=0, microsecond=0)
                    if target_dt <= now:
                        target_dt += datetime.timedelta(days=1)
                elif r_type == "weekly":
                    allowed_days = rule.get("days", [])
                    if not allowed_days:
                        continue
                    for i in range(8):
                        test_dt = now + datetime.timedelta(days=i)
                        test_dt = test_dt.replace(hour=tgt_h, minute=tgt_m, second=0, microsecond=0)
                        test_day = (test_dt.weekday() + 1) % 7
                        if test_day in allowed_days:
                            if test_dt > now:
                                target_dt = test_dt
                                break
                elif r_type == "interval":
                    interval = rule.get("interval_minutes", 30)
                    try:
                        cr_dt = datetime.datetime.fromisoformat(rule.get("created_at"))
                    except:
                        cr_dt = now
                    
                    diff_seconds = (now - cr_dt).total_seconds()
                    diff_minutes = int(diff_seconds // 60)
                    
                    intervals_passed = diff_minutes // interval
                    next_interval_count = intervals_passed + 1
                    target_dt = cr_dt + datetime.timedelta(minutes=next_interval_count * interval)
                
                if target_dt:
                    diff_sec = int((target_dt - now).total_seconds())
                    if diff_sec > 0:
                        rule_lbl = rule.get("label", "무명 규칙" if self.lang == "ko" else "Unnamed Rule")
                        mode_lbl = self.get_mode_label(rule.get("mode", "sleep"))
                        candidates.append((diff_sec, f"📅 {rule_lbl} [{mode_lbl}]"))
                        
        if not candidates:
            no_schedules_msg = "대기 중인 예약 일정이 없습니다." if self.lang == "ko" else "No upcoming schedules."
            return None, no_schedules_msg
            
        candidates.sort(key=lambda x: x[0])
        best_sec, label = candidates[0]
        
        hours = best_sec // 3600
        mins = (best_sec % 3600) // 60
        secs = best_sec % 60
        
        parts = []
        if self.lang == "ko":
            if hours > 0:
                parts.append(f"{hours}시간")
            if mins > 0:
                parts.append(f"{mins}분")
            parts.append(f"{secs}초")
            time_text = " ".join(parts)
            return best_sec, f"{label} - {time_text} 후 실행 예정"
        else:
            if hours > 0:
                parts.append(f"{hours}h")
            if mins > 0:
                parts.append(f"{mins}m")
            parts.append(f"{secs}s")
            time_text = " ".join(parts)
            return best_sec, f"{label} - scheduled in {time_text}"

    def get_tray_menu_header(self):
        _, text = self.get_soonest_trigger_info()
        return text

    def is_mouse_in_system_tray(self):
        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            mx, my = self.root.winfo_pointerxy()
            # Bottom-right 220px horizontal and 80px vertical corner check
            if (screen_width - 220) <= mx <= screen_width and (screen_height - 80) <= my <= screen_height:
                return True
        except:
            pass
            
        if WINDOWS_REG_AVAILABLE:
            try:
                import win32gui
                hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
                if hwnd:
                    notify_hwnd = win32gui.FindWindowEx(hwnd, 0, "TrayNotifyWnd", None)
                    if notify_hwnd:
                        rect = win32gui.GetWindowRect(notify_hwnd)
                        mx, my = self.root.winfo_pointerxy()
                        if rect[0] <= mx <= rect[2] and rect[1] <= my <= rect[3]:
                            return True
            except:
                pass
                
        return False

    def show_toast(self, message, title="알림", accent_color="#3b82f6"):
        """시스템 트레이 및 화면에 메시지를 세련되게 알리는 범용 알림 엔진"""
        if title == "알림" and self.lang != "ko":
            title = "Notification"
        # 1. 시스템 트레이 기본 풍선 도움말 알림 송출 (자체 예외 복구 탑재)
        if getattr(self, "tray_icon", None) is not None:
            try:
                self.tray_icon.notify(message, title)
            except Exception:
                pass
                
        # 2. 화면에 표시될 커스텀 플로팅 토스트 UI 생성
        try:
            toast = tk.Toplevel(self.root)
            toast.overrideredirect(True)
            toast.attributes("-topmost", True)
            toast.attributes("-alpha", 0.0)
            toast.configure(bg="#111827") # 매우 깊고 세련된 다크 그레이 계열
            
            # 주 모니터 해상도 획득 및 알림 위치 (우측 하단) 조율
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            w, h = 352, 75
            x = screen_width - w - 24
            y = screen_height - h - 64
            toast.geometry(f"{w}x{h}+{x}+{y}")
            
            # 포인트 컬러 데코 바 구축
            accent_bar = tk.Frame(toast, bg=accent_color, width=5)
            accent_bar.pack(side="left", fill="y")
            
            # 콘텐츠 내부 레이 아웃
            content_fn = tk.Frame(toast, bg="#111827")
            content_fn.pack(side="left", fill="both", expand=True, padx=12, pady=10)
            
            # 타이틀 & 본문 라벨 드로우
            lbl_tit = tk.Label(content_fn, text=title, font=("Arial", 10, "bold"), fg="#ffffff", bg="#111827", anchor="w")
            lbl_tit.pack(fill="x", anchor="w")
            
            lbl_desc = tk.Label(content_fn, text=message, font=("Arial", 10), fg="#9ca3af", bg="#111827", anchor="w", justify="left")
            lbl_desc.pack(fill="x", anchor="w", pady=(3, 0))
            
            # 부드러운 페이드 인/아웃 페이징 프레임
            def fade_in(alpha=0.0):
                if alpha < 0.95:
                    alpha += 0.15
                    toast.attributes("-alpha", alpha)
                    self.root.after(15, lambda: fade_in(alpha))
                else:
                    toast.attributes("-alpha", 0.95)
                    self.root.after(2500, fade_out)
                    
            def fade_out(alpha=0.95):
                if alpha > 0.0:
                    alpha -= 0.15
                    toast.attributes("-alpha", alpha)
                    self.root.after(15, lambda: fade_out(alpha))
                else:
                    toast.destroy()
                    
            fade_in()
        except Exception:
            pass

    def on_minimize(self, event):
        """창이 최소화될 때 트레이로 숨길지 결정"""
        if event.widget == self.root:
            if self.root.state() == "iconic":
                if self.minimize_to_tray.get():
                    if P_TRAY_AVAILABLE:
                        self.log_event("클라이언트 최소화 활성화: 시스템 트레이 백그라운드 모드로 가동을 이전합니다." if self.lang == "ko" else "Client minimized: transitioning execution to system tray background mode.")
                        self.root.withdraw()
                        self.sync_always_on_top_mini_win()
                        self.start_tray_icon()

    def start_single_instance_listener(self, server_socket):
        """중복 실행 요청 접수 시 메인 윈도우 원복 처리 루프"""
        def listen_loop():
            while True:
                try:
                    conn, addr = server_socket.accept()
                    data = conn.recv(1024)
                    if data == b"RESTORE":
                        self.log_event("중복 실행 신호 수신: 복구 시퀀스 작동을 지시합니다." if self.lang == "ko" else "Duplicate instance signature received: Triggering window recovery sequence.")
                        self.root.after(0, self.restore_from_tray)
                    elif data in (b"QUIT", b"TERMINATE", b"EXIT", b"CLOSE"):
                        self.log_event("외부 종료 신호 수신: 무인 설치/업데이트를 위해 프로세스를 즉시 안전 종료합니다." if self.lang == "ko" else "External termination signal received: Exiting process immediately.")
                        self.root.after(0, self.quit_app_completely)
                    conn.close()
                except Exception:
                    break
        t = threading.Thread(target=listen_loop, daemon=True)
        t.start()

    # --------------------------------------------------------------------
    # 5. 시스템 트레이 인터랙션 제어부 (닫기 가로채기 포함)
    # --------------------------------------------------------------------
    def on_close_button(self):
        """X 버튼 클릭 시 시스템 트레이로 숨김 처리"""
        if P_TRAY_AVAILABLE:
            log_msg = "X 버튼 닫기 액션 감지: 트레이 상주 백그라운드로 소멸 및 숨김 처리를 가동합니다." if self.lang == "ko" else "Close button detected: Hiding window to system tray background."
            self.log_event(log_msg)
            self.root.withdraw()  # 메인 윈도우 보이지 않게 숨김
            self.sync_always_on_top_mini_win()
            self.start_tray_icon()
        else:
            # 트레이 모듈이 비활성화 상태인 경우 직접 완전 종료 확인
            title = "알림" if self.lang == "ko" else "Notification"
            msg = "트레이 모듈(pystray)이 설치되지 않았습니다. 실시간 감시 대신 프로그램을 즉시 종료하시겠습니까?" if self.lang == "ko" else "System tray module (pystray) is not installed. Close the application immediately instead of background monitoring?"
            ans = messagebox.askyesno(title, msg)
            if ans:
                self.quit_app_completely()

    def animate_tray_icon_loop(self):
        """시스템 트레이 아이콘을 실시간으로 프레임 단위별 애니메이션 업데이트"""
        if not self.root:
            return
            
        is_active = (self.timer_running and not self.timer_paused)
        
        if getattr(self, "tray_icon", None) is not None:
            try:
                # 애니메이션 프레임 각도 또는 파라미터 갱신
                if not hasattr(self, "tray_anim_frame"):
                    self.tray_anim_frame = 0
                self.tray_anim_frame += 1
                
                # 이미지 로드 및 리사이즈 캐싱 (I/O 및 CPU 극적 절약)
                if not hasattr(self, "cached_tray_base_image") or self.cached_tray_base_image is None:
                    png_path = os.path.join(SCRIPT_DIR, "PowerController.png")
                    if not os.path.exists(png_path) and os.path.exists("PowerController.png"):
                        png_path = "PowerController.png"
                    
                    if os.path.exists(png_path):
                        base_img = Image.open(png_path).convert("RGBA")
                        self.cached_tray_base_image = base_img.resize((256, 256), Image.Resampling.LANCZOS)
                    else:
                        self.cached_tray_base_image = "fallback"
                
                if self.cached_tray_base_image != "fallback":
                    image = self.cached_tray_base_image.copy()
                    draw = ImageDraw.Draw(image)
                    
                    if is_active:
                        # Draw a pulsing indicator ring/circle in the bottom-right corner
                        pulse_val = 0.5 + 0.5 * math.sin(self.tray_anim_frame * 0.4)
                        base_color = (59, 130, 246)  # Blue
                        if self.mode == "shutdown":
                            base_color = (239, 68, 68)  # Red
                        elif self.mode == "restart":
                            base_color = (245, 158, 11)  # Orange
                            
                        # Alpha blending for the pulse
                        alpha = int(100 + 155 * pulse_val)
                        color_with_alpha = base_color + (alpha,)
                        
                        # Draw indicator at bottom right (center at 200, 200, radius 32)
                        draw.ellipse([168, 168, 232, 232], fill=color_with_alpha, outline="white", width=4)
                    else:
                        # Idle state: draw a subtle breathing green dot in the bottom-right corner to indicate running smoothly
                        pulse_val = 0.5 + 0.5 * math.sin(self.tray_anim_frame * 0.1)
                        alpha = int(50 + 100 * pulse_val)
                        draw.ellipse([180, 180, 220, 220], fill=(34, 197, 94, alpha), outline="white", width=2)
                else:
                    # Fallback to the default drawn lightning bolt animation
                    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(image)
                    
                    if is_active:
                        # 타이머 실행 중일 때는 더 빠르게 회전/깜빡임
                        pulse_val = math.sin(self.tray_anim_frame * 0.4)
                        base_color = "#3b82f6"
                        if self.mode == "shutdown":
                            base_color = "#ef4444"
                        elif self.mode == "restart":
                            base_color = "#f59e0b"
                        
                        r_offset = 8 * pulse_val
                        draw.ellipse([8 - r_offset, 8 - r_offset, 248 + r_offset, 248 + r_offset], fill=base_color)
                        angle_deg = (self.tray_anim_frame * 12) % 360
                    else:
                        # 대기 중(idle)일 때는 부드럽게 맥박 깜빡임 효과 수행
                        pulse_val = math.sin(self.tray_anim_frame * 0.1)
                        base_color = "#3b82f6"
                        
                        r_offset = 4 * pulse_val
                        draw.ellipse([8 - r_offset, 8 - r_offset, 248 + r_offset, 248 + r_offset], fill=base_color)
                        angle_deg = (self.tray_anim_frame * 1.5) % 360
                    
                    orig_pts = [(128, 28), (188, 128), (128, 128), (128, 228), (68, 128), (128, 128)]
                    
                    angle_rad = math.radians(angle_deg)
                    cos_a = math.cos(angle_rad)
                    sin_a = math.sin(angle_rad)
                    
                    rotated_pts = []
                    for px, py in orig_pts:
                        dx = px - 128
                        dy = py - 128
                        rx = dx * cos_a - dy * sin_a + 128
                        ry = dx * sin_a + dy * cos_a + 128
                        rotated_pts.append((rx, ry))
                    
                    lightning_fill = "white" if not is_active else "#fef08a"
                    draw.polygon(rotated_pts, fill=lightning_fill)
                
                # 업데이트 반영
                self.tray_icon.icon = image
            except Exception:
                pass
                
        # 타이머 활성화 상태와 유휴 상태에 따라 애니메이션 주기 조율 (CPU 극적 절약)
        interval = 250 if is_active else 1200
        self.root.after(interval, self.animate_tray_icon_loop)

    def start_tray_icon(self):
        """백그라운드 스레드에서 실시간으로 돌아가는 트레이 아이콘 가동"""
        if getattr(self, "tray_starting", False) or self.tray_icon is not None:
            return  # 이미 가동 준비중이거나 작동 중
        self.tray_starting = True
        
        # Try to load user's PowerController.png if available, otherwise draw the default
        image = None
        png_path = os.path.join(SCRIPT_DIR, "PowerController.png")
        if not os.path.exists(png_path) and os.path.exists("PowerController.png"):
            png_path = "PowerController.png"
            
        if os.path.exists(png_path):
            try:
                image = Image.open(png_path)
            except Exception:
                pass
                
        if image is None:
            # 둥근 전원 번개 로고 드로우 생성 (256x256 사이즈)
            image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.ellipse([8, 8, 248, 248], fill="#3b82f6") # 세련된 블루 도그 서클
            # 번개 일레트론 폴리곤
            draw.polygon([(128, 28), (188, 128), (128, 128), (128, 228), (68, 128), (128, 128)], fill="white")
        
        # 트레이 메뉴 인덱스 매핑
        menu = pystray.Menu(
            pystray.MenuItem(lambda item: self.get_tray_menu_header(), None, enabled=False),
            pystray.MenuItem(lambda item: "열기 (Restore)" if self.lang == "ko" else "Restore Window", self.restore_from_tray, default=True),
            pystray.MenuItem(lambda item: "⏳ 빠른 종료 타이머 (Quick Shutdown)" if self.lang == "ko" else "⏳ Quick Shutdown Timer", pystray.Menu(
                pystray.MenuItem(lambda item: "1분 (1 Minute)" if self.lang == "ko" else "1 Minute", lambda: self.quick_timer_from_tray(60, "shutdown")),
                pystray.MenuItem(lambda item: "5분 (5 Minutes)" if self.lang == "ko" else "5 Minutes", lambda: self.quick_timer_from_tray(300, "shutdown")),
                pystray.MenuItem(lambda item: "10분 (10 Minutes)" if self.lang == "ko" else "10 Minutes", lambda: self.quick_timer_from_tray(600, "shutdown")),
                pystray.MenuItem(lambda item: "15분 (15 Minutes)" if self.lang == "ko" else "15 Minutes", lambda: self.quick_timer_from_tray(900, "shutdown")),
                pystray.MenuItem(lambda item: "30분 (30 Minutes)" if self.lang == "ko" else "30 Minutes", lambda: self.quick_timer_from_tray(1800, "shutdown")),
                pystray.MenuItem(lambda item: "1시간 (1 Hour)" if self.lang == "ko" else "1 Hour", lambda: self.quick_timer_from_tray(3600, "shutdown"))
            )),
            pystray.MenuItem(lambda item: "🔄 빠른 재시작 타이머 (Quick Restart)" if self.lang == "ko" else "🔄 Quick Restart Timer", pystray.Menu(
                pystray.MenuItem(lambda item: "1분 (1 Minute)" if self.lang == "ko" else "1 Minute", lambda: self.quick_timer_from_tray(60, "restart")),
                pystray.MenuItem(lambda item: "5분 (5 Minutes)" if self.lang == "ko" else "5 Minutes", lambda: self.quick_timer_from_tray(300, "restart")),
                pystray.MenuItem(lambda item: "10분 (10 Minutes)" if self.lang == "ko" else "10 Minutes", lambda: self.quick_timer_from_tray(600, "restart")),
                pystray.MenuItem(lambda item: "15분 (15 Minutes)" if self.lang == "ko" else "15 Minutes", lambda: self.quick_timer_from_tray(900, "restart")),
                pystray.MenuItem(lambda item: "30분 (30 Minutes)" if self.lang == "ko" else "30 Minutes", lambda: self.quick_timer_from_tray(1800, "restart")),
                pystray.MenuItem(lambda item: "1시간 (1 Hour)" if self.lang == "ko" else "1 Hour", lambda: self.quick_timer_from_tray(3600, "restart"))
            )),
            pystray.MenuItem(lambda item: ("▶ 타이머 다시 시작 (Resume)" if self.timer_paused else "⏸ 타이머 일시정지 (Pause)") if self.lang == "ko" else ("▶ Resume Timer" if self.timer_paused else "⏸ Pause Timer"), self.toggle_pause_from_tray, enabled=lambda item: self.timer_running),
            pystray.MenuItem(lambda item: "타이머 취소 (Cancel Timer)" if self.lang == "ko" else "Cancel Timer", self.reset_timer_from_tray),
            pystray.MenuItem(lambda item: "즉시 컴퓨터 종료 (Shutdown Now)" if self.lang == "ko" else "Shut Down Computer Now", self.immediate_shutdown_from_tray),
            pystray.MenuItem(lambda item: "즉시 컴퓨터 재시작 (Restart Now)" if self.lang == "ko" else "Restart Computer Now", self.immediate_restart_from_tray),
            pystray.MenuItem(lambda item: "완전 종료 (Exit)" if self.lang == "ko" else "Exit Application", self.quit_app_completely)
        )
        
        _, soonest_text = self.get_soonest_trigger_info()
        if len(soonest_text) > 125:
            soonest_text = soonest_text[:122] + "..."
        self.tray_icon = pystray.Icon("PowerController", image, soonest_text, menu)
        
        # 백그라운드 스레드로 빌드업 실행
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        self.tray_starting = False

    def quick_timer_from_tray(self, seconds, mode):
        """트레이 메뉴에서 경과 타이머 즉시 시작 및 통보 (클릭 및 추가 누적 지원)"""
        def action():
            accumulated = False
            # 이미 타이머가 실행 중이고, 모드가 동일하며, 타이머 모드(timer)일 경우 합산
            if self.timer_running and self.mode == mode and self.run_type == "timer":
                self.remaining_seconds += seconds
                self.timer_paused = False
                pause_txt = "⏸ 일시정지" if self.lang == "ko" else "⏸ Pause"
                self.btn_start.configure(text=pause_txt, bg=ACCENT_YELLOW)
                accumulated = True
                new_seconds = self.remaining_seconds
            else:
                self.timer_running = False  # 기존 실행중인 타이머 중지 후 초기화
                self.set_mode(mode)
                self.set_run_type("timer")
                self.start_timer_with_seconds(seconds, show_notification=False)
                new_seconds = seconds

            # 피드백 내용 생성
            mode_lbl = self.get_mode_label(mode)
            
            # 추가된 시간 문자열
            added_time_parts = []
            h_add = seconds // 3600
            m_add = (seconds % 3600) // 60
            s_add = seconds % 60
            if self.lang == "ko":
                if h_add > 0:
                    added_time_parts.append(f"{h_add}시간")
                if m_add > 0:
                    added_time_parts.append(f"{m_add}분")
                if s_add > 0 or not added_time_parts:
                    added_time_parts.append(f"{s_add}초")
            else:
                if h_add > 0:
                    added_time_parts.append(f"{h_add}h")
                if m_add > 0:
                    added_time_parts.append(f"{m_add}m")
                if s_add > 0 or not added_time_parts:
                    added_time_parts.append(f"{s_add}s")
            added_time_str = " ".join(added_time_parts)

            # 전체 남은 시간 문자열
            total_time_parts = []
            h_tot = new_seconds // 3600
            m_tot = (new_seconds % 3600) // 60
            s_tot = new_seconds % 60
            if self.lang == "ko":
                if h_tot > 0:
                    total_time_parts.append(f"{h_tot}시간")
                if m_tot > 0:
                    total_time_parts.append(f"{m_tot}분")
                if s_tot > 0 or not total_time_parts:
                    total_time_parts.append(f"{s_tot}초")
            else:
                if h_tot > 0:
                    total_time_parts.append(f"{h_tot}h")
                if m_tot > 0:
                    total_time_parts.append(f"{m_tot}m")
                if s_tot > 0 or not total_time_parts:
                    total_time_parts.append(f"{s_tot}s")
            total_time_str = " ".join(total_time_parts)

            if accumulated:
                log_msg = f"트레이 빠른 타이머 합산 추가: {added_time_str} 추가됨 (총 {total_time_str} 후 [{mode_lbl}])" if self.lang == "ko" else f"Tray Quick Timer Added: {added_time_str} added (Total {total_time_str} remains for [{mode_lbl}])"
                self.log_event(log_msg)
                
                toast_title = "➕ 타이머 시간 추가 합산" if self.lang == "ko" else "➕ Timer Time Added"
                toast_msg = f"기존 타이머에 {added_time_str}이 합산되었습니다.\n총 남은 시간: {total_time_str} 후 [{mode_lbl}]" if self.lang == "ko" else f"{added_time_str} added to existing timer.\nTotal: {total_time_str} remaining until [{mode_lbl}]"
                self.show_toast(
                    title=toast_title,
                    message=toast_msg,
                    accent_color="#ef4444" if mode == "shutdown" or mode == "restart" else "#3b82f6"
                )
            else:
                log_msg = f"트레이 빠른 타이머 신규 설정: {total_time_str} 후 [{mode_lbl}]" if self.lang == "ko" else f"Tray Quick Timer Scheduled: {total_time_str} remains until [{mode_lbl}]"
                self.log_event(log_msg)
                
                toast_title = "⚡ 빠른 예약 가동" if self.lang == "ko" else "⚡ Quick Schedule"
                toast_msg = f"{total_time_str} 후 컴퓨터 [{mode_lbl}] 예약이 시작되었습니다." if self.lang == "ko" else f"Computer [{mode_lbl}] scheduled to trigger in {total_time_str}."
                self.show_toast(
                    title=toast_title,
                    message=toast_msg,
                    accent_color="#ef4444" if mode == "shutdown" or mode == "restart" else "#3b82f6"
                )
        self.root.after(0, action)

    def toggle_pause_from_tray(self, icon=None, item=None):
        """트레이 메뉴에서 타이머 일시정지/다시시작 토글 및 통보"""
        def action():
            self.toggle_pause()
            if self.timer_paused:
                toast_title = "⏸️ 타이머 일시정지" if self.lang == "ko" else "⏸️ Timer Paused"
                toast_msg = "간편 전원 제어 타이머가 일시정지 되었습니다." if self.lang == "ko" else "Quick power control timer has been paused."
                self.show_toast(
                    title=toast_title,
                    message=toast_msg,
                    accent_color=ACCENT_YELLOW
                )
            else:
                toast_title = "▶️ 타이머 재생" if self.lang == "ko" else "▶️ Timer Resumed"
                toast_msg = "간편 전원 제어 타이머가 다시 가동됩니다." if self.lang == "ko" else "Quick power control timer has resumed."
                self.show_toast(
                    title=toast_title,
                    message=toast_msg,
                    accent_color="#10b981"
                )
        self.root.after(0, action)

    def reset_timer_from_tray(self, icon=None, item=None):
        """트레이 메뉴에서 타이머 즉시 초기화 및 통보"""
        def action():
            was_running = self.timer_running
            self.reset_timer()
            if was_running:
                toast_title = "🛑 예약 가동 취소" if self.lang == "ko" else "🛑 Reservation Cancelled"
                toast_msg = "진행 중이던 모든 예약 제어 타이머가 완전히 취소되었습니다." if self.lang == "ko" else "All active power control timers have been cancelled."
                self.show_toast(
                    title=toast_title,
                    message=toast_msg,
                    accent_color="#ef4444"
                )
                info_title = "예약 취소 안내" if self.lang == "ko" else "Reservation Cancellation"
                info_msg = (
                    "진행 중이던 모든 예약 전원 제어 타이머가 완전히 취소되었습니다.\n\n"
                    "시스템 예약 제어 상태가 무사히 해제되었으며, 컴퓨터는 자동 종료되지 않고 정상 유지됩니다."
                ) if self.lang == "ko" else (
                    "All pending power control timers have been cancelled.\n\n"
                    "The system schedule has been safely released, and the computer will not be turned off/restarted."
                )
                messagebox.showinfo(info_title, info_msg)
            else:
                toast_title = "ℹ️ 타이머 대기 상태" if self.lang == "ko" else "ℹ️ Timer Idle State"
                toast_msg = "현재 실행 중이거나 예약된 타이머 타이틀이 없습니다." if self.lang == "ko" else "There is no active or scheduled timer running."
                self.show_toast(
                    title=toast_title,
                    message=toast_msg,
                    accent_color="#9ca3af"
                )
                info_title = "대기 상태 안내" if self.lang == "ko" else "Timer Idle"
                info_msg = "현재 예약되었거나 가동 상태인 기한식 전원 종료 타이머가 존재하지 않습니다." if self.lang == "ko" else "There is no scheduled power timer active at this moment."
                messagebox.showinfo(info_title, info_msg)
        self.root.after(0, action)

    def immediate_shutdown_from_tray(self, icon=None, item=None):
        """트레이 메뉴에서 컴퓨터 즉시 종료"""
        def action():
            title = "즉시 종료" if self.lang == "ko" else "Immediate Shutdown"
            msg = "컴퓨터를 지금 즉시 종료하시겠습니까?" if self.lang == "ko" else "Do you want to shut down the computer immediately?"
            ans = messagebox.askyesno(title, msg)
            if ans:
                toast_title = "⚠️ 즉시 종료 실행" if self.lang == "ko" else "⚠️ Immediate Shutdown"
                toast_msg = "컴퓨터 즉시 종료 명령을 실행합니다." if self.lang == "ko" else "Executing immediate computer shutdown command."
                self.show_toast(title=toast_title, message=toast_msg, accent_color="#ef4444")
                self.mode = "shutdown"
                self.execute_power_action()
        self.root.after(0, action)

    def immediate_restart_from_tray(self, icon=None, item=None):
        """트레이 메뉴에서 컴퓨터 즉시 재시작"""
        def action():
            title = "즉시 재시작" if self.lang == "ko" else "Immediate Restart"
            msg = "컴퓨터를 지금 즉시 재시작하시겠습니까?" if self.lang == "ko" else "Do you want to restart the computer immediately?"
            ans = messagebox.askyesno(title, msg)
            if ans:
                toast_title = "🔄 즉시 재시작 실행" if self.lang == "ko" else "🔄 Immediate Restart"
                toast_msg = "컴퓨터 즉시 재시작 명령을 실행합니다." if self.lang == "ko" else "Executing immediate computer restart command."
                self.show_toast(title=toast_title, message=toast_msg, accent_color="#ef4444")
                self.mode = "restart"
                self.execute_power_action()
        self.root.after(0, action)

    def restore_from_tray(self, icon=None, item=None):
        """트레이 아이콘 중지 후 메인화면 원복 및 피드백 알림"""
        self.is_boot_startup = False  # 복원 시 부팅 백그라운드 모드 해제
        log_msg = "시스템 트레이 복원 동작 감지: 백그라운드로부터 복구를 개시합니다." if self.lang == "ko" else "System tray restore action detected: Restoring from background."
        self.log_event(log_msg)
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        
        # 백그라운드에서 드로우 호출을 지연 배치 처리
        self.root.after(0, self.root.deiconify)
        self.root.after(10, lambda: self.root.attributes("-topmost", False))
        self.root.after(12, self.sync_always_on_top_mini_win)
        toast_title = "🖥️ UI 제어 화면 노출" if self.lang == "ko" else "🖥️ UI Restored"
        toast_msg = "전원 예약 제어 관리자 화면이 성공적으로 복원되었습니다." if self.lang == "ko" else "Power reservation control dashboard has been successfully restored."
        self.root.after(15, lambda: self.show_toast(
            title=toast_title,
            message=toast_msg,
            accent_color="#10b981"
        ))

    def quit_app_completely(self, icon=None, item=None):
        """시스템 종료 요청 시 메모리 완전 누수 방지 차원 정리"""
        self.timer_running = False
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        if hasattr(self, 'network_server_socket') and self.network_server_socket:
            try:
                self.network_server_socket.close()
            except:
                pass
        global server_socket_ref
        if server_socket_ref:
            try:
                server_socket_ref.close()
            except:
                pass
        self.root.quit()
        sys.exit(0)
            
    def get_grace_label_by_seconds(self, secs):
        grace_options_map = {
            5: "5초 (5 seconds)",
            10: "10초 (10 seconds)",
            20: "20초 (20 seconds)",
            30: "30초 (30 seconds)",
            60: "1분 (1 minute)",
            180: "3분 (3 minutes)",
            300: "5분 (5 minutes)"
        }
        return grace_options_map.get(secs, f"{secs}초 ({secs} seconds)")

    def handle_grace_seconds_change(self, secs):
        self.grace_seconds_setting.set(secs)
        self.grace_seconds_label.set(self.get_grace_label_by_seconds(secs))
        self.save_settings()
        
        # Add event log
        label_friendly = self.get_grace_label_by_seconds(secs)
        log_msg = f"예약작업 전 알림 대기 시간이 {label_friendly}으로 변경되었습니다." if self.lang == "ko" else f"Reservation notification countdown set to {label_friendly}."
        self.log_event(log_msg, in_app_toast=True)

    def load_settings(self):
        # Default choices
        self.always_on_top.set(True)
        self.minimize_to_tray.set(True)
        self.boot_to_tray.set(True)
        self.main_opacity.set(100)
        self.widget_opacity.set(95)
        self.show_current_time_compact.set(False)
        if hasattr(self, "widget_design"):
            self.widget_design.set("standard")
        if hasattr(self, "widget_width"):
            self.widget_width.set(260)
        if hasattr(self, "widget_height"):
            self.widget_height.set(135)
        if hasattr(self, "clock_font_size"):
            self.clock_font_size.set(13)
        if hasattr(self, "timer_font_size"):
            self.timer_font_size.set(20)
        if hasattr(self, "hourly_chime_enabled"):
            self.hourly_chime_enabled.set(True)
        if hasattr(self, "startup_alert_enabled"):
            self.startup_alert_enabled.set(True)
        self.selected_font.set("font-sans")
        if hasattr(self, "selected_font_weight"):
            self.selected_font_weight.set("normal")
        if hasattr(self, "network_receive_enabled"):
            self.network_receive_enabled.set(False)
        self.grace_seconds_setting.set(10)
        self.grace_seconds_label.set("10초 (10 seconds)")
        self.lang = "ko"
        self.sound_theme = "classic"
        
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.always_on_top.set(data.get("always_on_top", True))
                    self.minimize_to_tray.set(data.get("minimize_to_tray", True))
                    self.boot_to_tray.set(data.get("boot_to_tray", True))
                    self.main_opacity.set(data.get("main_opacity", 100))
                    self.widget_opacity.set(data.get("widget_opacity", 95))
                    self.show_current_time_compact.set(data.get("show_current_time_compact", False))
                    if hasattr(self, "widget_design"):
                        self.widget_design.set(data.get("widget_design", "standard"))
                    if hasattr(self, "widget_width"):
                        self.widget_width.set(data.get("widget_width", 260))
                    if hasattr(self, "widget_height"):
                        self.widget_height.set(data.get("widget_height", 135))
                    if hasattr(self, "clock_font_size"):
                        self.clock_font_size.set(data.get("clock_font_size", 13))
                    if hasattr(self, "timer_font_size"):
                        self.timer_font_size.set(data.get("timer_font_size", 20))
                    if hasattr(self, "hourly_chime_enabled"):
                        self.hourly_chime_enabled.set(data.get("hourly_chime_enabled", True))
                    if hasattr(self, "startup_alert_enabled"):
                        self.startup_alert_enabled.set(data.get("startup_alert_enabled", True))
                    self.selected_font.set(data.get("selected_font", "font-sans"))
                    if hasattr(self, "selected_font_weight"):
                        self.selected_font_weight.set(data.get("selected_font_weight", "normal"))
                    if hasattr(self, "network_receive_enabled"):
                        self.network_receive_enabled.set(data.get("network_receive_enabled", False))
                    if hasattr(self, "network_auth_token"):
                        self.network_auth_token.set(data.get("network_auth_token", ""))
                    if hasattr(self, "force_close_enabled"):
                        self.force_close_enabled.set(data.get("force_close_enabled", True))
                    self.grace_seconds_setting.set(data.get("grace_seconds", 10))
                    self.grace_seconds_label.set(self.get_grace_label_by_seconds(self.grace_seconds_setting.get()))
                    self.lang = data.get("lang", "ko")
                    self.sound_theme = data.get("sound_theme", "classic")
            except:
                pass
                
        # Ensure self.root topmost attribute is always False as Always on Top is now handled by the mini window
        self.root.attributes('-topmost', False)

    def save_settings(self):
        try:
            data = {
                "always_on_top": self.always_on_top.get(),
                "minimize_to_tray": self.minimize_to_tray.get(),
                "boot_to_tray": self.boot_to_tray.get(),
                "main_opacity": self.main_opacity.get(),
                "widget_opacity": self.widget_opacity.get(),
                "show_current_time_compact": self.show_current_time_compact.get(),
                "widget_design": self.widget_design.get() if hasattr(self, "widget_design") else "standard",
                "widget_width": self.widget_width.get() if hasattr(self, "widget_width") else 260,
                "widget_height": self.widget_height.get() if hasattr(self, "widget_height") else 135,
                "clock_font_size": self.clock_font_size.get() if hasattr(self, "clock_font_size") else 13,
                "timer_font_size": self.timer_font_size.get() if hasattr(self, "timer_font_size") else 20,
                "hourly_chime_enabled": self.hourly_chime_enabled.get() if hasattr(self, "hourly_chime_enabled") else True,
                "startup_alert_enabled": self.startup_alert_enabled.get() if hasattr(self, "startup_alert_enabled") else True,
                "selected_font": self.selected_font.get(),
                "selected_font_weight": self.selected_font_weight.get() if hasattr(self, "selected_font_weight") else "normal",
                "network_receive_enabled": self.network_receive_enabled.get() if hasattr(self, "network_receive_enabled") else False,
                "network_auth_token": self.network_auth_token.get() if hasattr(self, "network_auth_token") else "",
                "force_close_enabled": self.force_close_enabled.get() if hasattr(self, "force_close_enabled") else True,
                "grace_seconds": self.grace_seconds_setting.get(),
                "lang": self.lang,
                "sound_theme": getattr(self, "sound_theme", "classic")
            }
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except:
            pass

    def start_network_receive_server(self):
        """네트워크 원격 예약 수신용 TCP 서버"""
        if hasattr(self, 'network_server_socket') and self.network_server_socket:
            return # Already running
            
        def server_loop():
            self.network_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.network_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.network_server_socket.bind(("0.0.0.0", 9988))
                self.network_server_socket.listen(5)
                self.log_event("네트워크 수신 서버 시작: 포트 9988에서 원격 스케줄 규칙 대기 중..." if self.lang == "ko" else "Network receiver server started: Listening for remote schedule rules on port 9988...")
            except Exception as e:
                self.log_event(f"네트워크 수신 서버 바인딩 실패: {e}" if self.lang == "ko" else f"Network receiver server bind failed: {e}")
                self.network_server_socket = None
                return
                
            while True:
                try:
                    conn, addr = self.network_server_socket.accept()
                    threading.Thread(target=self.handle_network_client, args=(conn, addr), daemon=True).start()
                except Exception:
                    break
                    
        t = threading.Thread(target=server_loop, daemon=True)
        t.start()

    def stop_network_receive_server(self):
        if hasattr(self, 'network_server_socket') and self.network_server_socket:
            try:
                self.network_server_socket.close()
            except:
                pass
            self.network_server_socket = None
            self.log_event("네트워크 수신 서버 정지" if self.lang == "ko" else "Network receiver server stopped")

    def toggle_network_receive(self):
        self.save_settings()
        if self.network_receive_enabled.get():
            self.log_event("원격 예약 수신 기능 활성화" if self.lang == "ko" else "Remote schedule receiver enabled")
        else:
            self.log_event("원격 예약 수신 옵션 해제 (보안 토큰 수신은 무조작 항시 대기)" if self.lang == "ko" else "Remote schedule receiver disabled (Security token listener remains active)")

    def process_network_payload(self, payload, client_ip="127.0.0.1"):
        """
        네트워크(인바운드 TCP 또는 아웃바운드 방화벽 우회 동기화 채널)로부터
        수신된 명령 페이로드를 처리하고 응답 딕셔너리를 반환합니다.
        """
        server_token = self.network_auth_token.get().strip() if hasattr(self, "network_auth_token") else ""
        client_token = payload.get("auth_token", "").strip()
        master_key_input = payload.get("master_key", "").strip()
        action = payload.get("action", "register_schedule")

        # 관리자 토큰 분실 대비: 마스터 비상 복구 키 권한 검증
        master_actual = get_master_recovery_key()
        is_master_authorized = (
            (master_key_input and master_key_input == master_actual) or
            (client_token and client_token == master_actual)
        )

        # ScheduleCrypto 디지털 서명 무결성 감사
        sig = payload.get("signature", "")
        if sig and native_bridge:
            try:
                raw_to_check = json.dumps({k: v for k, v in payload.items() if k != "signature"}, sort_keys=True, ensure_ascii=False)
                if native_bridge.verify_schedule_signature(raw_to_check, sig):
                    self.log_event(f"🛡️ [ScheduleCrypto] 원격 명령 서명 검증 성공 ({client_ip})")
            except Exception:
                pass

        # 0. 마스터 비상 복구: 원격 보안 토큰 강제 초기화/재설정 (emergency_reset_token)
        # 관리자가 기존 토큰을 분실했을 때 마스터 복구 키로 즉시 새 토큰으로 갱신하거나 초기화(공백)합니다.
        if action == "emergency_reset_token":
            if not is_master_authorized:
                err_msg = "인증 실패: 마스터 비상 복구 키가 일치하지 않습니다." if self.lang == "ko" else "Authentication failed: Master recovery key does not match."
                self.log_event(f"비상 토큰 재설정 거부 ({client_ip}): 마스터 복구 키 불일치")
                return {
                    "success": False,
                    "message": err_msg,
                    "device": socket.gethostname() if "socket" in globals() else "PowerPC"
                }

            new_tok = payload.get("new_token", "").strip()
            self.network_auth_token.set(new_tok)
            self.save_settings()
            if hasattr(self, "entry_auth_token") and self.entry_auth_token.winfo_exists():
                try:
                    self.entry_auth_token.delete(0, tk.END)
                    self.entry_auth_token.insert(0, new_tok)
                except:
                    pass
            tok_desc = f"'{new_tok}'" if new_tok else "(초기화/공백 상태)"
            msg = f"마스터 복구 키 인증 성공: 보안 토큰이 {tok_desc}으로 강제 재설정되었습니다." if self.lang == "ko" else f"Master key verified: Security token reset to {tok_desc}."
            self.log_event(f"🚨 [비상 복구] 마스터 복구 키를 통해 보안 토큰이 원격으로 재설정되었습니다 ({client_ip}) -> {tok_desc}")
            return {
                "success": True,
                "message": msg,
                "device": socket.gethostname() if "socket" in globals() else "PowerPC",
                "new_token": new_tok
            }

        # 0-1. 마스터 비상 복구: 원격 기존 보안 토큰 확인/조회 (query_token)
        # 관리자가 기존 토큰을 기억하지 못할 때 마스터 복구 키로 기존 설정된 토큰값을 읽어옵니다.
        if action == "query_token":
            if not is_master_authorized:
                err_msg = "인증 실패: 마스터 비상 복구 키가 일치하지 않습니다." if self.lang == "ko" else "Authentication failed: Master recovery key does not match."
                self.log_event(f"보안 토큰 조회 거부 ({client_ip}): 마스터 복구 키 불일치")
                return {
                    "success": False,
                    "message": err_msg,
                    "device": socket.gethostname() if "socket" in globals() else "PowerPC"
                }

            self.log_event(f"🚨 [비상 복구] 마스터 복구 키로 보안 토큰 원격 조회 성공 ({client_ip})")
            return {
                "success": True,
                "message": f"기존 보안 토큰 조회 성공: '{server_token}'" if server_token else "현재 클라이언트에 보안 토큰이 미설정(공백)되어 있습니다.",
                "token": server_token,
                "device": socket.gethostname() if "socket" in globals() else "PowerPC"
            }

        # 1. 보안 토큰 설정/적용 명령 (set_token)
        # 클라이언트 측에 '허용' 버튼이 비활성화되거나 차단된 경우에도
        # 관리자로부터 수신한 보안 토큰을 무조작으로 즉시 적용 및 영구 저장합니다.
        if action == "set_token":
            new_tok = payload.get("new_token", client_token).strip()
            # 기존 토큰이 등록되어 있는데 전달받은 현재 인증 토큰과 다른 경우(공백 포함) 거부
            # 단, 마스터 복구 키가 일치하는 경우 기존 토큰을 몰라도 강제 덮어쓰기 허용
            if server_token and server_token != client_token and not is_master_authorized:
                err_msg = "인증 실패: 기존 보안 토큰이 일치하지 않습니다. (분실 시 마스터 복구 키를 사용하십시오)" if self.lang == "ko" else "Authentication failed: Existing token mismatch. Use master recovery key if lost."
                self.log_event(f"보안 토큰 갱신 거부 ({client_ip}): 기존 토큰 불일치")
                return {"success": False, "message": err_msg}

            self.network_auth_token.set(new_tok)
            self.save_settings()
            if hasattr(self, "entry_auth_token") and self.entry_auth_token.winfo_exists():
                try:
                    self.entry_auth_token.delete(0, tk.END)
                    self.entry_auth_token.insert(0, new_tok)
                except:
                    pass
            msg = f"보안 인증 토큰이 원격 관리자({client_ip})로부터 수신되어 클라이언트에 자동 적용되었습니다." if self.lang == "ko" else f"Security token received and saved from remote admin ({client_ip})."
            self.log_event(msg)
            return {
                "success": True,
                "message": msg,
                "device": socket.gethostname() if "socket" in globals() else "PowerPC"
            }

        # 2. 그 외의 원격 제어 명령은 보안 토큰 검증 필수 (마스터 복구 키 인증 시 자동 통과)
        if server_token and server_token != client_token and not is_master_authorized:
            err_msg = "인증 실패: 보안 토큰이 일치하지 않습니다. (분실 시 비상 복구 기능 활용)" if self.lang == "ko" else "Authentication failed: Invalid security token."
            self.log_event(f"네트워크 수신 거부 ({client_ip}): 보안 토큰 불일치")
            return {"success": False, "message": err_msg}

        # 3. 원격 스케줄 전체 삭제 (초기화) 명령
        if action == "clear_schedules":
            self.rules = []
            self.save_rules()
            self.root.after(0, self.render_rules_list)
            msg = f"외부 관리자({client_ip})의 요청으로 모든 예약 규칙이 원격 초기화되었습니다." if self.lang == "ko" else f"All schedule rules cleared by remote admin ({client_ip})."
            self.log_event(msg)
            return {"success": True, "message": msg, "count": 0}

        # 4. 원격 상태 조회 명령
        if action == "query_status":
            return {
                "success": True, 
                "count": len(getattr(self, "rules", [])),
                "receiver_active": True,
                "device": socket.gethostname() if "socket" in globals() else "PowerPC",
                "mac": get_local_mac()
            }

        # 5. 보안 토큰 단독 인증 검증 명령
        if action == "verify_token":
            has_token = bool(server_token)
            status_desc = "토큰 일치 확인 (보안 인증 성공)" if has_token else "인증 성공 (클라이언트에 보안 토큰이 미설정된 상태)"
            msg = f"보안 토큰 검증 완료: {status_desc}" if self.lang == "ko" else f"Security Token Verified: {status_desc}"
            self.log_event(f"보안 토큰 수신 검증 ({client_ip}): {status_desc}")
            return {
                "success": True,
                "message": msg,
                "token_protected": has_token,
                "device": socket.gethostname() if "socket" in globals() else "PowerPC"
            }

        # 5-1. 원격 즉시 전원 실행 명령 (immediate_power) - 'shutdown'(종료), 'reboot'(다시시작)
        if action == "immediate_power":
            if hasattr(self, "network_receive_enabled") and not self.network_receive_enabled.get():
                msg = "클라이언트의 '원격 예약 수신' 옵션이 해제되어 있어 즉시 전원 제어 명령을 거부합니다." if self.lang == "ko" else "Remote receiver is disabled on client. Immediate power command rejected."
                self.log_event(f"네트워크 즉시 실행 거부 ({client_ip}): 원격 수신 옵션 꺼짐")
                return {"success": False, "message": msg}

            power_cmd = str(payload.get("power_cmd", "shutdown")).lower().strip()
            is_reboot = power_cmd in ["restart", "reboot", "다시시작", "다시 시작"]
            cmd_kr = "다시 시작" if is_reboot else "시스템 종료"
            force = payload.get("force", True)
            f_param = " /f" if force else ""
            grace = max(0, int(payload.get("grace_period_sec", 3)))

            msg = f"외부 관리자({client_ip})로부터 즉시 [{cmd_kr}] 명령이 수신되어 {grace}초 후 실행됩니다." if self.lang == "ko" else f"Immediate [{cmd_kr}] command received from admin ({client_ip}). Executing in {grace}s."
            self.log_event(msg)

            def _execute_immediate_worker():
                import time
                time.sleep(1.2)  # 네트워크 ACK 응답 패킷 전송 완료 대기
                if is_reboot:
                    os.system(f"shutdown /r{f_param} /t {grace}")
                else:
                    os.system(f"shutdown /s{f_param} /t {grace}")
                try:
                    self.root.destroy()
                except:
                    pass
                sys.exit(0)

            threading.Thread(target=_execute_immediate_worker, daemon=True).start()

            return {
                "success": True,
                "message": msg,
                "device": socket.gethostname() if "socket" in globals() else "PowerPC"
            }

        # 6. 스케줄 등록 명령 (기본)
        # 클라이언트의 '원격 예약 수신' 옵션이 해제되어 있는 경우 스케줄 등록만 제한 (보안 토큰은 정상 수신/저장 완료)
        if hasattr(self, "network_receive_enabled") and not self.network_receive_enabled.get():
            msg = "클라이언트의 '원격 예약 수신' 옵션이 해제되어 있어 스케줄을 등록할 수 없습니다. (보안 토큰 전송은 정상 완료되었습니다.)" if self.lang == "ko" else "Remote schedule receiver is disabled on client. (Security token was received and applied successfully.)"
            self.log_event(f"네트워크 예약 등록 거부 ({client_ip}): 원격 수신 옵션 꺼짐")
            return {"success": False, "message": msg}

        label = payload.get("label", "원격 예약")
        mode = payload.get("mode", "shutdown")
        time_str = payload.get("time", "23:00")
        overwrite = payload.get("overwrite", False)

        import uuid
        new_rule = {
            "id": f"net-{str(uuid.uuid4())[:8]}",
            "label": label,
            "type": payload.get("type", "daily"),
            "mode": mode,
            "time": time_str,
            "days": payload.get("days", [0, 1, 2, 3, 4, 5, 6]),
            "interval_min": payload.get("interval_min", 0),
            "force_close": payload.get("force_close", True),
            "warning_beep": payload.get("warning_beep", True),
            "grace_period_sec": int(payload.get("grace_period_sec", 10)),
            "warning_message": payload.get("warning_message", ""),
            "allow_delay": payload.get("allow_delay", True),
            "idle_only": payload.get("idle_only", False),
            "idle_minutes": int(payload.get("idle_minutes", 15)),
            "clean_temp": payload.get("clean_temp", False),
            "pre_command": payload.get("pre_command", "").strip(),
            "is_active": True,
            "created_at": datetime.datetime.now().isoformat(),
            "last_executed": ""
        }

        rules = list(getattr(self, "rules", []))
        if overwrite:
            rules = [new_rule]
            msg = f"기존 규칙이 삭제되고 {client_ip}로부터 새 규칙이 성공적으로 덮어쓰기 등록되었습니다." if self.lang == "ko" else f"Existing rules deleted and a new rule from {client_ip} was successfully overwritten."
        else:
            rules.append(new_rule)
            msg = f"외부 컴퓨터({client_ip})로부터 새로운 원격 예약 규칙이 추가 등록되었습니다." if self.lang == "ko" else f"A new remote schedule rule has been successfully appended from {client_ip}."

        self.rules = rules
        self.save_rules()
        self.root.after(0, self.render_rules_list)

        if new_rule.get("pre_command"):
            self.log_event(f"🛡️ [보안 감사] 원격 예약에 사전 실행 명령어 포함됨 ({client_ip}): '{new_rule['pre_command']}'")

        self.log_event(f"네트워크 원격 예약 등록 성공: {label} ({time_str}, 모드: {mode})" if self.lang == "ko" else f"Network remote schedule registered: {label} ({time_str}, mode: {mode})")

        from tkinter import messagebox
        self.root.after(0, lambda: messagebox.showinfo(
            "네트워크 예약 등록" if self.lang == "ko" else "Network Schedule Registered",
            f"{msg}\n\n"
            f"규칙명: {label}\n"
            f"시간: {time_str} ({mode})\n"
            f"현재 총 등록 규칙: {len(rules)}개"
        ))
        return {"success": True, "message": msg, "count": len(rules)}

    def handle_network_client(self, conn, addr):
        try:
            conn.settimeout(5.0)
            data = conn.recv(4096)
            if not data:
                return
            payload = json.loads(data.decode("utf-8"))
            response = self.process_network_payload(payload, client_ip=addr[0])
            conn.sendall(json.dumps(response, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            try:
                response = {"success": False, "message": str(e)}
                conn.sendall(json.dumps(response, ensure_ascii=False).encode("utf-8"))
            except:
                pass
            self.log_event(f"네트워크 수신 처리 중 오류: {e}" if self.lang == "ko" else f"Error during network receive processing: {e}")
        finally:
            try:
                conn.close()
            except:
                pass

    def start_outbound_sync_daemon(self):
        """
        윈도우 방화벽 인바운드 차단(조직 정책으로 '허용' 버튼 회색 비활성화 등) 상황에서도
        클라이언트에서 아무런 추가 조작 없이 보안 토큰 및 스케줄 명령을 100% 수신하는
        역방향 아웃바운드 자동 동기화 에이전트.
        (아웃바운드 요청 및 이에 대한 회신은 Windows 방화벽에서 기본 허용되며 팝업이 발생하지 않음)
        """
        if getattr(self, "_outbound_sync_started", False):
            return
        self._outbound_sync_started = True

        def sync_worker():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            if hasattr(socket, "SO_REUSEPORT"):
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except Exception:
                    pass
            try:
                sock.bind(("", 9985))
            except Exception:
                try:
                    sock.bind(("", 0))
                except Exception:
                    return

            sock.settimeout(1.5)
            last_poll_time = 0

            while True:
                now = time.time()
                # 2초마다 아웃바운드 비콘/폴링 전송 (방화벽 SPI 상태 유지 및 관리자 스케줄러에 존재 통보)
                if now - last_poll_time >= 2.0:
                    last_poll_time = now
                    try:
                        local_ip = "127.0.0.1"
                        try:
                            s_tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            s_tmp.connect(("8.8.8.8", 80))
                            local_ip = s_tmp.getsockname()[0]
                            s_tmp.close()
                        except:
                            pass

                        poll_packet = {
                            "type": "client_sync_poll",
                            "client_ip": local_ip,
                            "hostname": socket.gethostname() if "socket" in globals() else "PowerPC",
                            "mac": get_local_mac(),
                            "has_token": bool(self.network_auth_token.get().strip()) if hasattr(self, "network_auth_token") else False,
                            "rules_count": len(getattr(self, "rules", []))
                        }
                        data_bytes = json.dumps(poll_packet).encode("utf-8")
                        
                        # 순수 창작 NetBeaconEngine 고속 브로드캐스트 우선 가동
                        if native_bridge and native_bridge.is_beacon_engine_loaded():
                            try:
                                native_bridge.send_beacon_broadcast(9986, json.dumps(poll_packet))
                            except Exception:
                                pass

                        try:
                            sock.sendto(data_bytes, ("<broadcast>", 9986))
                        except Exception:
                            pass
                        try:
                            sock.sendto(data_bytes, ("127.0.0.1", 9986))
                        except Exception:
                            pass
                    except Exception:
                        pass

                # 관리자 스케줄러로부터의 패킷 수신 대기
                try:
                    recv_data, addr = sock.recvfrom(8192)
                    if not recv_data:
                        continue
                    payload = json.loads(recv_data.decode("utf-8"))
                    action = payload.get("action")
                    if action in ["set_token", "verify_token", "immediate_power", "register_schedule", "clear_schedules", "query_status", "emergency_reset_token", "query_token"]:
                        # 명령 처리 수행
                        resp = self.process_network_payload(payload, client_ip=addr[0])
                        resp["reply_to"] = action
                        # 관리자 스케줄러로 처리 결과 ACK 즉시 회신
                        sock.sendto(json.dumps(resp, ensure_ascii=False).encode("utf-8"), addr)
                except socket.timeout:
                    continue
                except Exception:
                    time.sleep(0.5)

        t = threading.Thread(target=sync_worker, daemon=True)
        t.start()

    def handle_main_opacity_change(self, val):
        try:
            opacity_val = float(val) / 100.0
            self.root.attributes("-alpha", opacity_val)
            self.save_settings()
        except Exception:
            pass

    def handle_widget_opacity_change(self, val):
        try:
            int_val = int(round(float(val)))
            opacity_val = float(int_val) / 100.0
            if hasattr(self, "mini_win") and self.mini_win and self.mini_win.winfo_exists():
                self.mini_win.attributes("-alpha", opacity_val)
            if hasattr(self, "mini_lbl_op_val") and self.mini_lbl_op_val and self.mini_lbl_op_val.winfo_exists():
                try:
                    self.mini_lbl_op_val.configure(text=f"{int_val}%")
                except Exception:
                    pass
            self.save_settings()
        except Exception:
            pass

    def toggle_show_current_time_compact(self):
        self.save_settings()
        if hasattr(self, "mini_win") and self.mini_win and self.mini_win.winfo_exists():
            self.rebuild_mini_window()

    def toggle_mini_clock(self):
        self.show_current_time_compact.set(not self.show_current_time_compact.get())
        self.toggle_show_current_time_compact()

    def adjust_mini_clock_font_size(self, delta):
        current_sz = self.clock_font_size.get() if hasattr(self, "clock_font_size") else 13
        new_sz = max(8, min(32, current_sz + delta))
        self.set_mini_clock_font_size(new_sz)
        if hasattr(self, "scale_clock_sz") and self.scale_clock_sz.winfo_exists():
            self.scale_clock_sz.set(new_sz)

    def set_mini_clock_font_size(self, val):
        try:
            sz = int(float(val))
            self.clock_font_size.set(sz)
        except Exception:
            sz = self.clock_font_size.get() if hasattr(self, "clock_font_size") else 13
        self.save_settings()
        if hasattr(self, "mini_lbl_clock") and self.mini_lbl_clock and self.mini_lbl_clock.winfo_exists():
            design = self.widget_design.get() if hasattr(self, "widget_design") else "standard"
            if design in ("cyber_hud", "retro_led"):
                fam = "Consolas"
                wt = "bold"
            elif design == "minimal_bar":
                fam = "Arial"
                wt = "normal"
                sz = min(18, max(7, sz))
            elif design == "clean_card":
                fam = "Arial"
                wt = "normal"
            else:
                fam = "Arial"
                wt = "bold"
            try:
                f_cat = "mono" if design in ("cyber_hud", "retro_led") else "sans"
                new_f = self.get_font(f_cat, sz, wt)
                self.mini_lbl_clock.configure(font=new_f)
            except Exception:
                self.mini_lbl_clock.configure(font=(fam, sz, wt))
            self.mini_lbl_clock._original_font_category = "mono" if design in ("cyber_hud", "retro_led") else "sans"
            self.mini_lbl_clock._original_font_weight = wt
        else:
            if hasattr(self, "mini_win") and self.mini_win and self.mini_win.winfo_exists():
                self.rebuild_mini_window()

    def adjust_mini_timer_font_size(self, delta):
        current_sz = self.timer_font_size.get() if hasattr(self, "timer_font_size") else 20
        new_sz = max(12, min(36, current_sz + delta))
        self.set_mini_timer_font_size(new_sz)
        if hasattr(self, "scale_timer_sz") and self.scale_timer_sz.winfo_exists():
            self.scale_timer_sz.set(new_sz)

    def set_mini_timer_font_size(self, val):
        try:
            sz = int(float(val))
            self.timer_font_size.set(sz)
        except Exception:
            sz = self.timer_font_size.get() if hasattr(self, "timer_font_size") else 20
        self.save_settings()
        if hasattr(self, "mini_lbl_timer") and self.mini_lbl_timer and self.mini_lbl_timer.winfo_exists():
            design = self.widget_design.get() if hasattr(self, "widget_design") else "standard"
            fam = "Consolas" if design in ("cyber_hud", "retro_led") else "Arial"
            wt = "bold"
            if design == "minimal_bar":
                sz = min(18, max(9, sz))
            try:
                f_cat = "mono" if design in ("cyber_hud", "retro_led") else "sans"
                new_f = self.get_font(f_cat, sz, wt)
                self.mini_lbl_timer.configure(font=new_f)
            except Exception:
                self.mini_lbl_timer.configure(font=(fam, sz, wt))
            self.mini_lbl_timer._original_font_category = "mono" if design in ("cyber_hud", "retro_led") else "sans"
            self.mini_lbl_timer._original_font_weight = wt
        else:
            if hasattr(self, "mini_win") and self.mini_win and self.mini_win.winfo_exists():
                self.rebuild_mini_window()

    def set_widget_opacity(self, val):
        try:
            int_val = max(30, min(100, int(round(float(val)))))
            self.widget_opacity.set(int_val)
            if hasattr(self, "scale_widget_opacity") and self.scale_widget_opacity.winfo_exists():
                try:
                    self.scale_widget_opacity.set(int_val)
                except Exception:
                    pass
            self.handle_widget_opacity_change(int_val)
        except Exception:
            pass

    def adjust_widget_opacity(self, delta):
        current = self.widget_opacity.get()
        new_val = max(30, min(100, current + delta))
        self.set_widget_opacity(new_val)

    def zoom_mini_window(self, factor):
        """상단 고정창 전체 크기 및 글자 크기 일괄 확대/축소 (factor > 1: 확대, factor < 1: 축소)"""
        if not hasattr(self, "mini_win") or not self.mini_win or not self.mini_win.winfo_exists():
            return
        try:
            cur_w = self.mini_win.winfo_width()
            cur_h = self.mini_win.winfo_height()
            if cur_w <= 1 or cur_h <= 1:
                cur_w = self.widget_width.get()
                cur_h = self.widget_height.get() if hasattr(self, "widget_height") else 95

            design = self.widget_design.get() if hasattr(self, "widget_design") else "standard"
            min_w = 200 if design == "minimal_bar" else 180
            min_h = 36 if design == "minimal_bar" else 50

            if factor > 1.0:
                new_w = min(600, cur_w + 30)
                new_h = min(450, cur_h + 15)
                delta_t = 2
                delta_c = 1
            else:
                new_w = max(min_w, cur_w - 30)
                new_h = max(min_h, cur_h - 15)
                delta_t = -2
                delta_c = -1

            cur_t_sz = self.timer_font_size.get() if hasattr(self, "timer_font_size") else 20
            cur_c_sz = self.clock_font_size.get() if hasattr(self, "clock_font_size") else 13

            new_t_sz = max(12, min(36, cur_t_sz + delta_t))
            new_c_sz = max(8, min(28, cur_c_sz + delta_c))

            self.timer_font_size.set(new_t_sz)
            self.clock_font_size.set(new_c_sz)
            self.widget_width.set(new_w)
            self.widget_height.set(new_h)

            x = self.mini_win.winfo_x()
            y = self.mini_win.winfo_y()
            self.mini_win.geometry(f"{new_w}x{new_h}+{x}+{y}")

            self.set_mini_timer_font_size(new_t_sz)
            self.set_mini_clock_font_size(new_c_sz)
            self.save_settings()
        except Exception:
            pass

    def reset_mini_window_size(self):
        """상단 고정창 크기 및 글자 크기 기본값 복원"""
        try:
            self.widget_width.set(286)
            self.widget_height.set(95)
            self.timer_font_size.set(20)
            self.clock_font_size.set(13)
            self.save_settings()
            if hasattr(self, "mini_win") and self.mini_win and self.mini_win.winfo_exists():
                x = self.mini_win.winfo_x()
                y = self.mini_win.winfo_y()
                self.mini_win.geometry(f"286x95+{x}+{y}")
                self.set_mini_timer_font_size(20)
                self.set_mini_clock_font_size(13)
        except Exception:
            pass

    def handle_font_change(self, val):
        self.selected_font.set(val)
        FONT_LABELS = {
            "ko": {
                "font-sans": "산세리프 (Inter)",
                "font-display": "테크 (Grotesk)",
                "font-mono": "고정폭 (Mono)",
                "font-serif": "명조 (나눔명조)",
                "font-malgun": "맑은 고딕 (Malgun)",
                "font-gulim": "굴림 (Gulim)",
                "font-batang": "바탕 (Batang)"
            },
            "en": {
                "font-sans": "Sans (Inter)",
                "font-display": "Tech (Grotesk)",
                "font-mono": "Mono (Coding)",
                "font-serif": "Serif (Myeongjo)",
                "font-malgun": "Malgun Gothic",
                "font-gulim": "Gulim",
                "font-batang": "Batang"
            }
        }
        self.selected_font_label.set(FONT_LABELS[self.lang].get(val, "Unknown"))
        self.save_settings()
        self.apply_current_font_to_widgets()
        
        # Add event log
        name_friendly = FONT_LABELS["ko"].get(val, val) if self.lang == "ko" else FONT_LABELS["en"].get(val, val)
        log_msg = f"글꼴이 {name_friendly}로 성공적으로 변경되었습니다." if self.lang == "ko" else f"App font changed to {name_friendly} successfully."
        self.log_event(log_msg, in_app_toast=True)

    def handle_font_weight_change(self, val):
        self.selected_font_weight.set(val)
        weight_labels = {
            "normal": "보통" if self.lang == "ko" else "Normal",
            "bold": "굵게" if self.lang == "ko" else "Bold"
        }
        self.selected_font_weight_label.set(weight_labels[val])
        self.save_settings()
        self.apply_current_font_to_widgets()
        
        # Add event log
        name_friendly = weight_labels[val]
        log_msg = f"글꼴 두께가 {name_friendly}로 성공적으로 변경되었습니다." if self.lang == "ko" else f"App font weight changed to {name_friendly} successfully."
        self.log_event(log_msg, in_app_toast=True)

    def get_font(self, family_key, size, weight=""):
        current_font = self.selected_font.get() # 'font-sans', 'font-display', 'font-mono', 'font-serif'
        current_weight = self.selected_font_weight.get() if hasattr(self, "selected_font_weight") else "normal"
        
        try:
            import tkinter.font as tkfont
            avail_families = [f.lower() for f in tkfont.families()]
        except Exception:
            avail_families = []
            
        def find_best_family(candidates):
            for c in candidates:
                if c.lower() in avail_families:
                    return c
            return candidates[-1] # Fallback to standard
            
        if current_font == 'font-display':
            best = find_best_family(["Space Grotesk", "Century Gothic", "Trebuchet MS", "Arial"])
        elif current_font == 'font-mono':
            best = find_best_family(["JetBrains Mono", "Consolas", "Courier New"])
        elif current_font == 'font-serif':
            best = find_best_family(["Nanum Myeongjo", "Batang", "Georgia", "Times New Roman"])
        elif current_font == 'font-malgun':
            best = find_best_family(["Malgun Gothic", "맑은 고딕", "Arial"])
        elif current_font == 'font-gulim':
            best = find_best_family(["Gulim", "굴림", "Arial"])
        elif current_font == 'font-batang':
            best = find_best_family(["Batang", "바탕", "Times New Roman"])
        else: # font-sans
            best = find_best_family(["Inter", "Segoe UI", "Malgun Gothic", "Arial"])
            
        if family_key == "mono":
            best = find_best_family(["JetBrains Mono", "Consolas", "Courier New"])
            
        # Determine the final weight to apply
        if current_weight == "bold":
            final_weight = "bold"
        else:
            final_weight = "bold" if (weight == "bold" or weight is True) else "normal"
            
        # Optical size normalization to prevent UI truncation across different font metrics
        adj_size = size
        if current_font in ['font-malgun', 'font-batang', 'font-gulim', 'font-serif']:
            if adj_size >= 28:
                adj_size = max(20, adj_size - 4)
            elif adj_size >= 16:
                adj_size = max(13, adj_size - 2)
            elif adj_size >= 10:
                adj_size = max(8, adj_size - 1)
        elif current_font == 'font-mono':
            if adj_size >= 28:
                adj_size = max(20, adj_size - 4)
            elif adj_size >= 13:
                adj_size = max(9, adj_size - 1)

        if final_weight == "bold":
            if adj_size >= 24:
                adj_size = max(18, adj_size - 2)
            elif adj_size >= 11:
                adj_size = max(9, adj_size - 1)

        return (best, adj_size, final_weight)

    def apply_current_font_to_widgets(self, parent=None):
        if parent is None:
            parent = self.root
            
        widgets_to_process = [parent]
        if parent == self.root:
            if hasattr(self, "mini_win") and self.mini_win and self.mini_win.winfo_exists():
                widgets_to_process.append(self.mini_win)
            if hasattr(self, "popup_window") and self.popup_window and self.popup_window.winfo_exists():
                widgets_to_process.append(self.popup_window)
                
        for root_node in widgets_to_process:
            self._apply_font_recursive(root_node)

        # After applying fonts, dynamically update the window geometry & minsize if content expanded
        try:
            if hasattr(self, "root") and self.root and self.root.winfo_exists():
                self.root.update_idletasks()
                req_w = self.root.winfo_reqwidth()
                req_h = self.root.winfo_reqheight()
                cur_w = self.root.winfo_width()
                cur_h = self.root.winfo_height()

                target_min_w = max(500, req_w)
                target_min_h = max(660, req_h)
                self.root.minsize(target_min_w, target_min_h)

                if cur_w < target_min_w or cur_h < target_min_h:
                    new_w = max(cur_w, target_min_w)
                    new_h = max(cur_h, target_min_h)
                    self.root.geometry(f"{new_w}x{new_h}")
        except Exception:
            pass

        # Mini window auto-fit if content expanded
        try:
            if hasattr(self, "mini_win") and self.mini_win and self.mini_win.winfo_exists():
                self.mini_win.update_idletasks()
                req_w = self.mini_win.winfo_reqwidth()
                req_h = self.mini_win.winfo_reqheight()
                cur_w = self.mini_win.winfo_width()
                cur_h = self.mini_win.winfo_height()
                if req_w > cur_w or req_h > cur_h:
                    x = self.mini_win.winfo_x()
                    y = self.mini_win.winfo_y()
                    new_w = max(cur_w, req_w)
                    new_h = max(cur_h, req_h)
                    self.mini_win.geometry(f"{new_w}x{new_h}+{x}+{y}")
        except Exception:
            pass

    def _apply_font_recursive(self, widget):
        try:
            config = widget.configure()
            if "font" in config:
                current_font = widget.cget("font")
                if current_font:
                    import tkinter.font as tkfont
                    try:
                        f_obj = tkfont.Font(font=current_font)
                        family = f_obj.actual("family")
                        size = f_obj.actual("size")
                        weight = f_obj.actual("weight")
                    except Exception:
                        if isinstance(current_font, (list, tuple)):
                            family = current_font[0]
                            size = current_font[1] if len(current_font) > 1 else 9
                            weight = current_font[2] if len(current_font) > 2 else ""
                        else:
                            family = "Arial"
                            size = 9
                            weight = ""

                    # Cache the original classification of the widget's font to prevent loss of context
                    if not hasattr(widget, "_original_font_category"):
                        if "courier" in family.lower() or "consolas" in family.lower() or "mono" in family.lower():
                            widget._original_font_category = "mono"
                        elif "myeongjo" in family.lower() or "serif" in family.lower() or "batang" in family.lower() or "georgia" in family.lower():
                            widget._original_font_category = "serif"
                        elif "space" in family.lower() or "grotesk" in family.lower() or "gothic" in family.lower():
                            widget._original_font_category = "display"
                        else:
                            widget._original_font_category = "sans"
                            
                    if not hasattr(widget, "_original_font_weight"):
                        widget._original_font_weight = weight if weight else "normal"

                    if not hasattr(widget, "_original_font_size"):
                        widget._original_font_size = size

                    family_key = widget._original_font_category
                    orig_weight = widget._original_font_weight
                    orig_size = widget._original_font_size
                        
                    new_font = self.get_font(family_key, orig_size, orig_weight)
                    widget.configure(font=new_font)
        except Exception:
            pass
            
        try:
            for child in widget.winfo_children():
                self._apply_font_recursive(child)
        except Exception:
            pass

    def play_sound_theme(self, sound_type="alert"):
        """ plays the selected sound theme (classic, scifi, cozy) """
        try:
            import winsound
        except ImportError:
            winsound = None

        if winsound is not None:
            import threading
            def play_audio():
                try:
                    theme = getattr(self, "sound_theme", "classic")
                    if sound_type == "tick":
                        if theme == "classic":
                            winsound.Beep(1000, 100)
                        elif theme == "scifi":
                            winsound.Beep(2000, 50)
                        else: # cozy
                            winsound.Beep(523, 150)
                    elif sound_type == "alert":
                        if theme == "classic":
                            winsound.Beep(587, 120)
                            winsound.Beep(880, 180)
                        elif theme == "scifi":
                            winsound.Beep(1200, 80)
                            winsound.Beep(1800, 120)
                        else: # cozy
                            winsound.Beep(698, 120)
                            winsound.Beep(932, 200)
                    elif sound_type == "chime":
                        if theme == "classic":
                            winsound.Beep(523, 120)
                            winsound.Beep(659, 120)
                            winsound.Beep(783, 150)
                        elif theme == "scifi":
                            winsound.Beep(880, 80)
                            winsound.Beep(1760, 80)
                            winsound.Beep(2200, 120)
                        else: # cozy
                            winsound.Beep(523, 100)
                            winsound.Beep(698, 100)
                            winsound.Beep(880, 100)
                            winsound.Beep(1046, 180)
                    elif sound_type == "alarm":
                        # Repeats twice or three times, beautiful alarm melody
                        import time
                        for _ in range(3):
                            winsound.Beep(880, 150)
                            winsound.Beep(987, 150)
                            winsound.Beep(1046, 250)
                            time.sleep(0.1)
                except Exception:
                    try:
                        self.root.bell()
                    except:
                        pass
            threading.Thread(target=play_audio, daemon=True).start()
        else:
            try:
                self.root.bell()
            except:
                pass

    def apply_sound_theme(self, sound_key, play_preview=False):
        self.sound_theme = sound_key
        self.save_settings()
        self.update_sound_theme_buttons_ui()
        if play_preview:
            self.play_sound_theme("alert")

    def update_sound_theme_buttons_ui(self):
        theme = getattr(self, "sound_theme", "classic")
        for st_key, btn in getattr(self, "sound_theme_btns", {}).items():
            if st_key == theme:
                btn.configure(bg="#8b5cf6", fg="white") # Violet highlight for active!
            else:
                btn.configure(bg=DARK_CARD, fg=TEXT_COLOR)

    def check_startup_reg(self):
        if not WINDOWS_REG_AVAILABLE:
            return False
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            try:
                # The app name in run is "PowerController"
                value, _ = winreg.QueryValueEx(key, "PowerController")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False

    def heal_startup_reg(self):
        """기존 윈도우 시작 레지스트리에 --startup --tray 인자가 누락되어 있으면 자동으로 최신 인자를 보정합니다."""
        if not WINDOWS_REG_AVAILABLE:
            return
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            try:
                value, _ = winreg.QueryValueEx(key, "PowerController")
                winreg.CloseKey(key)
                if "--tray" not in str(value) and "--startup" not in str(value):
                    self.update_startup_reg()
            except FileNotFoundError:
                winreg.CloseKey(key)
        except Exception:
            pass

    def update_startup_reg(self):
        if not WINDOWS_REG_AVAILABLE:
            return
        exe_path = os.path.abspath(sys.argv[0])
        if exe_path.endswith(".py"):
            # Use pythonw (no console window) to prevent black CLI flash on boot
            python_exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            if not os.path.exists(python_exe):
                python_exe = sys.executable
            exe_path = f'"{python_exe}" "{exe_path}"'
        else:
            exe_path = f'"{exe_path}"'

        # 컴퓨터 시작 시에는 메인창을 띄우지 않고 시스템 트레이에서만 알람이 나오도록 항상 --startup --tray 인자 등록
        exe_path += " --startup --tray"

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE
            )
            if self.auto_start.get():
                winreg.SetValueEx(key, "PowerController", 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, "PowerController")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass

    def toggle_startup(self):
        if not WINDOWS_REG_AVAILABLE:
            err_title = "오류" if self.lang == "ko" else "Error"
            err_msg = "윈도우 환경에서만 자동 실행 설정을 조정할 수 있습니다." if self.lang == "ko" else "Auto-startup can only be configured in a Windows environment."
            messagebox.showerror(err_title, err_msg)
            self.auto_start.set(False)
            return
        if self.auto_start.get():
            self.boot_to_tray.set(True)
        self.update_startup_reg()
        self.save_settings()
        if self.auto_start.get():
            info_msg = "윈도우 시작 시 메인창 없이 트레이 백그라운드로 자동 실행되도록 등록되었습니다." if self.lang == "ko" else "Registered to run silently in system tray without main window at Windows startup."
            self.log_event(info_msg, in_app_toast=True)
        else:
            info_msg = "자동 실행 등록이 해제되었습니다." if self.lang == "ko" else "Auto-startup registration has been removed."
            self.log_event(info_msg, in_app_toast=True)

    def toggle_boot_to_tray(self):
        self.save_settings()
        if self.auto_start.get():
            self.update_startup_reg()

    def execute_power_action(self):
        if self.mode == "alarm":
            print("로그: 알람 경보 실행")
            log_msg = "⏰ 예약된 사운드 알람 경보가 작동되었습니다!" if self.lang == "ko" else "⏰ Scheduled alarm alert triggered!"
            self.log_event(log_msg, in_app_toast=True)
            self.trigger_alarm_popup("예약 알람" if self.lang == "ko" else "Scheduled Alarm")
            self.reset_timer()
            return

        # 액션 돌입 전 트레이 완벽 클리어
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None

        # 전원 동작 직전 네이티브 웨이크 타이머 및 절전 락 정리
        if native_bridge:
            try:
                native_bridge.cancel_hardware_wake_timer()
                native_bridge.set_sleep_prevention(prevent_sleep=False, keep_display=False)
            except Exception:
                pass

        log_msg = f"전원 동작 명령 최종 실행: [{self.get_mode_label(self.mode)}]" if self.lang == "ko" else f"Executing final power action command: [{self.get_mode_label(self.mode)}]"
        self.log_event(log_msg)

        # 윈도우 파괴를 먼저 진행하여 모달 창이나 어플리케이션 자체가 종료/로그아웃/재부팅을 방해하지 않도록 보장
        try:
            self.root.destroy()
        except:
            pass

        force_flag = getattr(self, "force_flag", None)
        if force_flag is None:
            force_flag = self.force_close_enabled.get() if hasattr(self, "force_close_enabled") else True
        f_param = " /f" if force_flag else ""

        if self.mode == "shutdown":
            print("로그: 시스템 종료 명령 실행")
            os.system(f"shutdown /s{f_param} /t 2")
        elif self.mode in ["restart", "reboot"]:
            print("로그: 시스템 재시작 명령 실행")
            os.system(f"shutdown /r{f_param} /t 2")
        elif self.mode == "sleep":
            print("로그: 시스템 절전 명령 실행")
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        elif self.mode == "hibernate":
            print("로그: 시스템 최대 절전 명령 실행")
            os.system("shutdown /h")
        elif self.mode == "lock":
            print("로그: 화면 잠금 명령 실행")
            if native_bridge:
                native_bridge.lock_workstation_fast()
            else:
                os.system("rundll32.exe user32.dll,LockWorkStation")
        elif self.mode == "screenoff":
            print("로그: 화면 끄기 명령 실행")
            if native_bridge:
                native_bridge.turn_off_monitor_fast()
            else:
                os.system("powershell (Add-Type '[DllImport(\"user32.dll\")]^public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);' -Name a -PassThru)::SendMessage(-1,0x0112,0xF170,2)")
        elif self.mode == "logout":
            print("로그: 시스템 로그아웃 명령 실행")
            os.system(f"shutdown /l{f_param}")
            
        sys.exit(0)

    def load_theme(self):
        if os.path.exists(THEME_CONFIG_FILE):
            try:
                with open(THEME_CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    return cfg.get("theme", "dark")
            except:
                return "dark"
        return "dark"

    def save_theme(self, theme_name):
        try:
            with open(THEME_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"theme": theme_name}, f, indent=4)
            with open(SIDEBAR_THEME_FILE, "w", encoding="utf-8") as f:
                json.dump({"theme": theme_name}, f, indent=4)
        except:
            pass

    def apply_theme(self, theme_name, save=True):
        if theme_name not in THEMES:
            theme_name = "dark"
            
        global DARK_BG, DARK_CARD, TEXT_COLOR, ACCENT_BLUE, ACCENT_RED, ACCENT_YELLOW
        
        # Save old values so we can map old -> new in existing widgets
        self.old_theme = {
            "bg": DARK_BG,
            "card": DARK_CARD,
            "text": TEXT_COLOR,
            "blue": ACCENT_BLUE,
            "red": ACCENT_RED,
            "yellow": ACCENT_YELLOW,
            "green": getattr(self, "current_green", "#10b981"),
            "subtext": getattr(self, "current_subtext", "#9ca3af"),
            "secondary": getattr(self, "current_secondary", SECONDARY_BG if "SECONDARY_BG" in globals() else "#374151")
        }
        
        self.new_theme = THEMES[theme_name]
        
        # Update globals
        DARK_BG = self.new_theme["bg"]
        DARK_CARD = self.new_theme["card"]
        TEXT_COLOR = self.new_theme["text"]
        ACCENT_BLUE = self.new_theme["blue"]
        ACCENT_RED = self.new_theme["red"]
        ACCENT_YELLOW = self.new_theme["yellow"]
        self.current_green = self.new_theme["green"]
        self.current_subtext = self.new_theme["subtext"]
        self.current_secondary = self.new_theme["secondary"]
        
        self.current_theme = theme_name
        
        # Configure app root background
        self.root.configure(bg=DARK_BG)
        
        # Update widgets recursively
        self.update_all_widget_colors()
        
        # Highlight theme button
        self.highlight_active_theme_button(theme_name)
        
        # Re-sync tab colors if any tab button exists
        if hasattr(self, "active_tab") and hasattr(self, "switch_tab"):
            self.switch_tab(self.active_tab)
            
        if save:
            self.save_theme(theme_name)
            
    def update_all_widget_colors(self):
        # Update top level root
        self._update_widget_colors_recursive(self.root)
        
        # Update sound theme buttons for correct highlight representation under new coloring
        self.update_sound_theme_buttons_ui()
        
        # Update popup window if it is currently active/open
        if hasattr(self, "popup_window") and self.popup_window and self.popup_window.winfo_exists():
            self.popup_window.configure(bg=DARK_BG)
            self._update_widget_colors_recursive(self.popup_window)
            
        # Update settings popup window if it is currently active/open
        if hasattr(self, "settings_popup") and self.settings_popup and self.settings_popup.winfo_exists():
            self.settings_popup.configure(bg=DARK_BG)
            self._update_widget_colors_recursive(self.settings_popup)
            
        # Re-apply user's font preferences across updated themes
        self.apply_current_font_to_widgets()
            
    def _update_widget_colors_recursive(self, parent):
        for widget in parent.winfo_children():
            try:
                # Retrieve configuration
                config = widget.configure()
                
                # Check for background configurations
                if "bg" in config or "background" in config:
                    curr_bg = widget.cget("bg")
                    if curr_bg == self.old_theme["bg"]:
                        widget.configure(bg=self.new_theme["bg"])
                    elif curr_bg == self.old_theme["card"]:
                        widget.configure(bg=self.new_theme["card"])
                    elif curr_bg == self.old_theme["blue"]:
                        widget.configure(bg=self.new_theme["blue"])
                    elif curr_bg == self.old_theme["red"]:
                        widget.configure(bg=self.new_theme["red"])
                    elif curr_bg == self.old_theme["green"]:
                        widget.configure(bg=self.new_theme["green"])
                    elif curr_bg == self.old_theme.get("yellow", "#eab308"):
                        widget.configure(bg=self.new_theme["yellow"])
                    elif curr_bg == self.old_theme.get("secondary", "#374151"):
                        widget.configure(bg=self.new_theme["secondary"])

                # Check for foreground configurations
                if "fg" in config or "foreground" in config:
                    curr_fg = widget.cget("fg")
                    if curr_fg == self.old_theme["text"]:
                        widget.configure(fg=self.new_theme["text"])
                    elif curr_fg == self.old_theme["blue"]:
                        widget.configure(fg=self.new_theme["blue"])
                    elif curr_fg == self.old_theme["red"]:
                        widget.configure(fg=self.new_theme["red"])
                    elif curr_fg == self.old_theme["green"]:
                        widget.configure(fg=self.new_theme["green"])
                    elif curr_fg == self.old_theme.get("yellow", "#eab308"):
                        widget.configure(fg=self.new_theme["yellow"])
                    elif curr_fg == self.old_theme["subtext"]:
                        widget.configure(fg=self.new_theme["subtext"])
                    elif curr_fg in ["#9ca3af", "#6b7280"]:
                        widget.configure(fg=self.new_theme["subtext"])

                # Check specific widget traits
                if isinstance(widget, tk.Checkbutton):
                    if "selectcolor" in config:
                        curr_sel = widget.cget("selectcolor")
                        if curr_sel == self.old_theme["card"]:
                            widget.configure(selectcolor=self.new_theme["card"])
                        elif curr_sel == self.old_theme["bg"]:
                            widget.configure(selectcolor=self.new_theme["bg"])
                        elif curr_sel == self.old_theme.get("secondary", "#374151"):
                            widget.configure(selectcolor=self.new_theme["secondary"])
                    if "activebackground" in config:
                        widget.configure(activebackground=self.new_theme["bg"])
                    if "activeforeground" in config:
                        widget.configure(activeforeground=self.new_theme["text"])

                elif isinstance(widget, tk.Listbox):
                    widget.configure(
                        bg=self.new_theme["card"],
                        fg=self.new_theme["text"],
                        highlightcolor=self.new_theme["blue"]
                    )

                elif isinstance(widget, tk.Entry):
                    widget.configure(
                        bg=self.new_theme["card"] if widget.cget("bg") == self.old_theme["card"] else self.new_theme["bg"],
                        fg=self.new_theme["text"],
                        insertbackground=self.new_theme["text"]
                    )

                elif isinstance(widget, tk.Canvas):
                    widget.configure(bg=self.new_theme["bg"])

                elif isinstance(widget, tk.LabelFrame):
                    widget.configure(
                        bg=self.new_theme["card"] if widget.cget("bg") == self.old_theme["card"] else self.new_theme["bg"],
                        fg=self.new_theme["subtext"]
                    )

                # OptionMenu menu components
                try:
                    if "menu" in config:
                        m = widget.nametowidget(widget.cget("menu"))
                        m.configure(
                            bg=self.new_theme["card"],
                            fg=self.new_theme["text"],
                            activebackground=self.new_theme["blue"],
                            activeforeground=self.new_theme["bg"]
                        )
                except Exception:
                    pass

            except Exception:
                pass
            
            # Recursive traverse
            self._update_widget_colors_recursive(widget)

    def highlight_active_theme_button(self, active_theme):
        if not hasattr(self, "theme_btns"):
            return
        for theme_key, btn in self.theme_btns.items():
            if theme_key == active_theme:
                btn.configure(
                    bg=ACCENT_BLUE,
                    fg="#ffffff"
                )
            else:
                btn.configure(
                    bg=DARK_CARD,
                    fg=TEXT_COLOR
                )

    def show_settings_popup(self):
        self.open_settings_popup()

    def open_settings_popup(self):
        self.is_boot_startup = False  # 설정 팝업 조작 시 활성 사용자 모드로 전환
        # If settings window is already active/open, raise and focus it
        if hasattr(self, "settings_popup") and self.settings_popup and self.settings_popup.winfo_exists():
            self.settings_popup.lift()
            self.settings_popup.focus_force()
            return

        self.settings_popup = tk.Toplevel(self.root)
        self.settings_popup.title("⚙️ 설정 (Settings)" if self.lang == "ko" else "⚙️ Settings")
        self.settings_popup.configure(bg=DARK_BG)
        self.settings_popup.resizable(False, False)
        
        # Transient window keeps it above the main window
        self.settings_popup.transient(self.root)
        
        # Central placement relative to the main window
        w = 528
        h = min(780, self.root.winfo_screenheight() - 60)
        rx = self.root.winfo_x() + (self.root.winfo_width() // 2) - (w // 2)
        ry = self.root.winfo_y() + (self.root.winfo_height() // 2) - (h // 2)
        self.settings_popup.geometry(f"{w}x{h}+{rx}+{ry}")
        
        # Title Label
        lbl_title = tk.Label(
            self.settings_popup, 
            text="⚙️ 환경 설정 (Preferences)" if self.lang == "ko" else "⚙️ Preferences", 
            font=("Arial", 11, "bold"), 
            fg=TEXT_COLOR, 
            bg=DARK_BG, 
            pady=8
        )
        lbl_title.pack()

        # Scrollable container for all preferences
        scroll_container = ScrollableFrame(self.settings_popup, bg=DARK_BG)
        scroll_container.pack(fill="both", expand=True, padx=8, pady=(0, 5))
        ScrollableFrame._active_frame = scroll_container
        parent = scroll_container.scrollable_frame

        # Bind mouse wheel directly to popup window for guaranteed smooth scrolling anywhere inside
        self.settings_popup.bind("<MouseWheel>", scroll_container._on_mousewheel, add="+")
        self.settings_popup.bind("<Button-4>", scroll_container._on_mousewheel_up, add="+")
        self.settings_popup.bind("<Button-5>", scroll_container._on_mousewheel_down, add="+")

        # 1. Theme Selection Frame
        frm_theme = tk.LabelFrame(
            parent, 
            text="🎨 테마 선택 (Theme)" if self.lang == "ko" else "🎨 Theme", 
            font=("Arial", 10, "bold"), 
            fg=ACCENT_BLUE, 
            bg=DARK_BG, 
            bd=1, 
            relief="solid", 
            padx=10, 
            pady=8
        )
        frm_theme.pack(fill="x", padx=6, pady=4)
        
        self.theme_btns = {}
        for theme_key, theme_data in THEMES.items():
            btn = tk.Button(
                frm_theme,
                text=theme_data["name_ko"] if self.lang == "ko" else theme_data["name_en"],
                font=("Arial", 10, "bold"),
                relief="flat",
                pady=4,
                cursor="hand2",
                command=lambda tk_key=theme_key: self.apply_theme(tk_key)
            )
            btn.pack(side="left", padx=2, expand=True, fill="x")
            self.theme_btns[theme_key] = btn

        # 2. Sound Theme Frame
        frm_sound = tk.LabelFrame(
            parent, 
            text="🎵 사운드 테마 (Sound)" if self.lang == "ko" else "🎵 Sound", 
            font=("Arial", 10, "bold"), 
            fg=getattr(self, "current_green", "#10b981"), 
            bg=DARK_BG, 
            bd=1, 
            relief="solid", 
            padx=10, 
            pady=8
        )
        frm_sound.pack(fill="x", padx=6, pady=4)
        
        self.sound_theme_btns = {}
        sound_themes_list = {
            "classic": {"ko": "클래식 비프", "en": "Classic Beep"},
            "scifi": {"ko": "SF 신스", "en": "Sci-Fi Synth"},
            "cozy": {"ko": "아늑한 멜로디", "en": "Cozy Chime"}
        }
        for st_key, st_names in sound_themes_list.items():
            btn = tk.Button(
                frm_sound,
                text=st_names["ko"] if self.lang == "ko" else st_names["en"],
                font=("Arial", 10, "bold"),
                relief="flat",
                pady=4,
                cursor="hand2",
                command=lambda s_key=st_key: self.apply_sound_theme(s_key, play_preview=True)
            )
            btn.pack(side="left", padx=2, expand=True, fill="x")
            self.sound_theme_btns[st_key] = btn

        # 3. Mini Widget Customization (Themes & Layout)
        frm_widget = tk.LabelFrame(
            parent, 
            text="📌 상단고정 미니 위젯 테마 & 디자인" if self.lang == "ko" else "📌 Mini Widget Themes & Style", 
            font=("Arial", 10, "bold"), 
            fg=ACCENT_BLUE, 
            bg=DARK_BG, 
            bd=1, 
            relief="solid", 
            padx=10, 
            pady=8
        )
        frm_widget.pack(fill="x", padx=6, pady=4)

        lbl_w_design = tk.Label(
            frm_widget,
            text="위젯 테마 스타일:" if self.lang == "ko" else "Widget Theme Style:",
            font=("Arial", 10, "bold"),
            fg=getattr(self, "current_subtext", "#9ca3af"),
            bg=DARK_BG
        )
        lbl_w_design.pack(anchor="w", pady=(0, 4))

        f_w_themes = tk.Frame(frm_widget, bg=DARK_BG)
        f_w_themes.pack(fill="x", pady=(0, 6))

        widget_styles = [
            ("standard", "네온 링", "Neon Ring"),
            ("cyber_hud", "사이버 HUD", "Cyber HUD"),
            ("minimal_bar", "초슬림 바", "Slim Bar"),
            ("retro_led", "레트로 LED", "Retro LED"),
            ("clean_card", "클린 카드", "Clean Card")
        ]

        self.widget_theme_btns = {}
        def on_widget_design_select(d_key):
            self.widget_design.set(d_key)
            self.save_settings()
            self.rebuild_mini_window()
            for k, b in self.widget_theme_btns.items():
                is_active = (k == d_key)
                b.configure(
                    bg=ACCENT_BLUE if is_active else DARK_CARD,
                    fg="white" if is_active else TEXT_COLOR
                )

        for w_key, ko_name, en_name in widget_styles:
            is_active = (self.widget_design.get() == w_key)
            btn_w = tk.Button(
                f_w_themes,
                text=ko_name if self.lang == "ko" else en_name,
                font=("Arial", 10, "bold"),
                bg=ACCENT_BLUE if is_active else DARK_CARD,
                fg="white" if is_active else TEXT_COLOR,
                relief="flat",
                pady=3,
                cursor="hand2",
                command=lambda k=w_key: on_widget_design_select(k)
            )
            btn_w.pack(side="left", padx=1, expand=True, fill="x")
            self.widget_theme_btns[w_key] = btn_w

        # Widget Controls Row 1: Width (가로), Height (세로), Opacity (투명도)
        f_w_sliders1 = tk.Frame(frm_widget, bg=DARK_BG)
        f_w_sliders1.pack(fill="x", pady=(2, 4))

        # 가로 (너비)
        lbl_w_width = tk.Label(
            f_w_sliders1,
            text="가로:" if self.lang == "ko" else "Width:",
            font=("Arial", 10),
            fg=getattr(self, "current_subtext", "#9ca3af"),
            bg=DARK_BG
        )
        lbl_w_width.pack(side="left", padx=(1, 1))

        def on_width_change(val):
            self.save_settings()
            if hasattr(self, "mini_win") and self.mini_win and self.mini_win.winfo_exists():
                try:
                    w = int(float(val))
                    h = self.mini_win.winfo_height()
                    x = self.mini_win.winfo_x()
                    y = self.mini_win.winfo_y()
                    self.mini_win.geometry(f"{w}x{h}+{x}+{y}")
                except Exception:
                    self.rebuild_mini_window()
            else:
                self.rebuild_mini_window()

        self.scale_w_width = tk.Scale(
            f_w_sliders1,
            from_=180,
            to=500,
            orient="horizontal",
            variable=self.widget_width,
            command=on_width_change,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            troughcolor=DARK_CARD,
            highlightthickness=0,
            bd=0,
            showvalue=True,
            font=("Arial", 10),
            width=8,
            length=65
        )
        self.scale_w_width.pack(side="left", padx=(0, 4))

        # 세로 (높이)
        lbl_w_height = tk.Label(
            f_w_sliders1,
            text="세로:" if self.lang == "ko" else "Height:",
            font=("Arial", 10),
            fg=getattr(self, "current_subtext", "#9ca3af"),
            bg=DARK_BG
        )
        lbl_w_height.pack(side="left", padx=(2, 1))

        def on_height_change(val):
            self.save_settings()
            if hasattr(self, "mini_win") and self.mini_win and self.mini_win.winfo_exists():
                try:
                    h = int(float(val))
                    w = self.mini_win.winfo_width()
                    x = self.mini_win.winfo_x()
                    y = self.mini_win.winfo_y()
                    self.mini_win.geometry(f"{w}x{h}+{x}+{y}")
                except Exception:
                    self.rebuild_mini_window()
            else:
                self.rebuild_mini_window()

        self.scale_w_height = tk.Scale(
            f_w_sliders1,
            from_=36,
            to=350,
            orient="horizontal",
            variable=self.widget_height,
            command=on_height_change,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            troughcolor=DARK_CARD,
            highlightthickness=0,
            bd=0,
            showvalue=True,
            font=("Arial", 10),
            width=8,
            length=65
        )
        self.scale_w_height.pack(side="left", padx=(0, 4))

        # 투명도
        lbl_w_op = tk.Label(
            f_w_sliders1,
            text="투명도:" if self.lang == "ko" else "Opacity:",
            font=("Arial", 10),
            fg=getattr(self, "current_subtext", "#9ca3af"),
            bg=DARK_BG
        )
        lbl_w_op.pack(side="left", padx=(2, 1))

        self.scale_widget_opacity = tk.Scale(
            f_w_sliders1,
            from_=30,
            to=100,
            orient="horizontal",
            variable=self.widget_opacity,
            command=self.handle_widget_opacity_change,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            troughcolor=DARK_CARD,
            highlightthickness=0,
            bd=0,
            showvalue=True,
            font=("Arial", 10),
            width=8,
            length=65
        )
        self.scale_widget_opacity.pack(side="left", padx=(0, 2), fill="x", expand=True)

        # Resizing Tip
        lbl_w_tip = tk.Label(
            frm_widget,
            text="💡 위젯 우측 하단(◢) 드래그로 크기 조절, 시계 위에 마우스 휠을 굴리거나 우클릭하여 글자 크기를 바로 조절할 수 있습니다." if self.lang == "ko" else "💡 Drag corner (◢) to resize, or scroll wheel/right-click on clock to adjust font size.",
            font=("Arial", 10),
            fg=getattr(self, "current_yellow", "#eab308"),
            bg=DARK_BG,
            anchor="w",
            justify="left",
            wraplength=475
        )
        lbl_w_tip.pack(fill="x", padx=4, pady=(0, 3))

        # Widget Controls Row 2: Digital Font Sizes & Clock Toggle
        f_w_sliders2 = tk.Frame(frm_widget, bg=DARK_BG)
        f_w_sliders2.pack(fill="x", pady=(2, 2))

        # 1) 시계 글꼴 크기
        lbl_clock_sz = tk.Label(
            f_w_sliders2,
            text="시계:" if self.lang == "ko" else "Clock:",
            font=("Arial", 10),
            fg=getattr(self, "current_subtext", "#9ca3af"),
            bg=DARK_BG
        )
        lbl_clock_sz.pack(side="left", padx=(1, 1))

        self.scale_clock_sz = tk.Scale(
            f_w_sliders2,
            from_=10,
            to=28,
            orient="horizontal",
            variable=self.clock_font_size,
            command=self.set_mini_clock_font_size,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            troughcolor=DARK_CARD,
            highlightthickness=0,
            bd=0,
            showvalue=True,
            font=("Arial", 10),
            width=8,
            length=56
        )
        self.scale_clock_sz.pack(side="left", padx=(0, 4))

        # 2) 타이머 글꼴 크기
        lbl_timer_sz = tk.Label(
            f_w_sliders2,
            text="타이머:" if self.lang == "ko" else "Timer:",
            font=("Arial", 10),
            fg=getattr(self, "current_subtext", "#9ca3af"),
            bg=DARK_BG
        )
        lbl_timer_sz.pack(side="left", padx=(2, 1))

        self.scale_timer_sz = tk.Scale(
            f_w_sliders2,
            from_=12,
            to=32,
            orient="horizontal",
            variable=self.timer_font_size,
            command=self.set_mini_timer_font_size,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            troughcolor=DARK_CARD,
            highlightthickness=0,
            bd=0,
            showvalue=True,
            font=("Arial", 10),
            width=8,
            length=56
        )
        self.scale_timer_sz.pack(side="left", padx=(0, 4))

        # 3) 현재 시각 표시 체크박스
        self.chk_show_time = tk.Checkbutton(
            f_w_sliders2,
            text="현재 시각 표시" if self.lang == "ko" else "Show Clock",
            variable=self.show_current_time_compact,
            command=self.toggle_show_current_time_compact,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            selectcolor=DARK_CARD,
            activebackground=DARK_BG,
            activeforeground=TEXT_COLOR,
            font=("Arial", 10, "bold")
        )
        self.chk_show_time.pack(side="left", padx=(3, 0))

        # 4. Smart Alerts & Briefing (Hourly Chime & Startup Briefing)
        frm_alerts = tk.LabelFrame(
            parent,
            text="🔔 스마트 알림 & 브리핑 (Smart Alerts)" if self.lang == "ko" else "🔔 Smart Alerts & Chime",
            font=("Arial", 10, "bold"),
            fg=getattr(self, "current_yellow", "#eab308"),
            bg=DARK_BG,
            bd=1,
            relief="solid",
            padx=10,
            pady=8
        )
        frm_alerts.pack(fill="x", padx=6, pady=4)

        f_chime_row = tk.Frame(frm_alerts, bg=DARK_BG)
        f_chime_row.pack(fill="x", pady=(0, 4))

        chk_chime = tk.Checkbutton(
            f_chime_row,
            text="🔔 매 시 정각 웨스트민스터 차임벨 소리 & 알림" if self.lang == "ko" else "🔔 Hourly Westminster Chime melody & alert",
            variable=self.hourly_chime_enabled,
            command=self.save_settings,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            selectcolor=DARK_CARD,
            activebackground=DARK_BG,
            activeforeground=TEXT_COLOR,
            font=("Arial", 10, "bold"),
            wraplength=340,
            justify="left"
        )
        chk_chime.pack(side="left")

        btn_chime_test = tk.Button(
            f_chime_row,
            text="🔊 테스트" if self.lang == "ko" else "🔊 Test",
            font=("Arial", 10, "bold"),
            bg=DARK_CARD,
            fg=getattr(self, "current_yellow", "#eab308"),
            relief="flat",
            padx=4,
            pady=1,
            cursor="hand2",
            command=lambda: self.trigger_hourly_chime(datetime.datetime.now().hour)
        )
        btn_chime_test.pack(side="right")

        f_startup_row = tk.Frame(frm_alerts, bg=DARK_BG)
        f_startup_row.pack(fill="x")

        chk_startup = tk.Checkbutton(
            f_startup_row,
            text="📅 앱 실행 시 오늘 예약 작업 트레이 브리핑 팝업" if self.lang == "ko" else "📅 System tray briefing for today's tasks on startup",
            variable=self.startup_alert_enabled,
            command=self.save_settings,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            selectcolor=DARK_CARD,
            activebackground=DARK_BG,
            activeforeground=TEXT_COLOR,
            font=("Arial", 10, "bold"),
            wraplength=340,
            justify="left"
        )
        chk_startup.pack(side="left")

        btn_today_test = tk.Button(
            f_startup_row,
            text="📋 미리보기" if self.lang == "ko" else "📋 Preview",
            font=("Arial", 10, "bold"),
            bg=DARK_CARD,
            fg=ACCENT_BLUE,
            relief="flat",
            padx=4,
            pady=1,
            cursor="hand2",
            command=lambda: self.show_startup_today_tasks_modal(self.get_today_active_tasks() or [
                {"mode": "shutdown", "type": "daily", "time": "23:00", "label": "야간 자동 종료 예시"}
            ], is_preview=True)
        )
        btn_today_test.pack(side="right")

        # 5. Main Window Opacity & Font Family
        frm_mw = tk.LabelFrame(
            parent, 
            text="👁️ 메인창 설정 (Window)" if self.lang == "ko" else "👁️ Window Settings", 
            font=("Arial", 10, "bold"), 
            fg=ACCENT_RED, 
            bg=DARK_BG, 
            bd=1, 
            relief="solid", 
            padx=10, 
            pady=8
        )
        frm_mw.pack(fill="x", padx=6, pady=4)
        
        frm_mw_top = tk.Frame(frm_mw, bg=DARK_BG)
        frm_mw_top.pack(fill="x", pady=(0, 5))
        frm_mw_bottom = tk.Frame(frm_mw, bg=DARK_BG)
        frm_mw_bottom.pack(fill="x")
        
        lbl_main_opacity = tk.Label(
            frm_mw_top, 
            text="투명도:" if self.lang == "ko" else "Opacity:", 
            font=("Arial", 10), 
            fg=getattr(self, "current_subtext", "#9ca3af"), 
            bg=DARK_BG
        )
        lbl_main_opacity.pack(side="left", padx=(2, 2))
        
        self.scale_main_opacity = tk.Scale(
            frm_mw_top,
            from_=20,
            to=100,
            orient="horizontal",
            variable=self.main_opacity,
            command=self.handle_main_opacity_change,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            troughcolor=DARK_CARD,
            highlightthickness=0,
            bd=0,
            showvalue=True,
            font=("Arial", 10),
            width=8,
            length=160
        )
        self.scale_main_opacity.pack(side="left", padx=2, expand=True, fill="x")
        
        lbl_font_title = tk.Label(
            frm_mw_bottom,  
            text="글꼴:" if self.lang == "ko" else "Font:", 
            font=("Arial", 10, "bold"), 
            fg=getattr(self, "current_subtext", "#9ca3af"), 
            bg=DARK_BG
        )
        lbl_font_title.pack(side="left", padx=(10, 2))
        
        self.opt_font = tk.OptionMenu(
            frm_mw_bottom,
            self.selected_font_label,
            "산세리프 (Inter)",
            "테크 (Grotesk)",
            "고정폭 (Mono)",
            "명조 (나눔명조)",
            "맑은 고딕 (Malgun)",
            "굴림 (Gulim)",
            "바탕 (Batang)"
        )
        self.opt_font.config(
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            activebackground=DARK_CARD,
            activeforeground=TEXT_COLOR,
            highlightthickness=0,
            relief="flat",
            font=("Arial", 10),
            pady=0,
            padx=2
        )
        self.opt_font["menu"].config(
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            activebackground=ACCENT_BLUE,
            activeforeground="white",
            relief="flat",
            font=("Arial", 10)
        )
        self.opt_font.pack(side="left", padx=2, expand=True, fill="x")

        lbl_font_weight_title = tk.Label(
            frm_mw_bottom, 
            text="두께:" if self.lang == "ko" else "Wgt:", 
            font=("Arial", 10, "bold"), 
            fg=getattr(self, "current_subtext", "#9ca3af"), 
            bg=DARK_BG
        )
        lbl_font_weight_title.pack(side="left", padx=(6, 2))
        
        self.opt_font_weight = tk.OptionMenu(
            frm_mw_bottom,
            self.selected_font_weight_label,
            "보통" if self.lang == "ko" else "Normal",
            "굵게" if self.lang == "ko" else "Bold"
        )
        self.opt_font_weight.config(
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            activebackground=DARK_CARD,
            activeforeground=TEXT_COLOR,
            highlightthickness=0,
            relief="flat",
            font=("Arial", 10),
            pady=0,
            padx=2
        )
        self.opt_font_weight["menu"].config(
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            activebackground=ACCENT_BLUE,
            activeforeground="white",
            relief="flat",
            font=("Arial", 10)
        )
        self.opt_font_weight.pack(side="left", padx=2, expand=True, fill="x")

        # 6. 예약작업 알림 설정 (Grace Warning Time Settings)
        self.frm_grace = tk.LabelFrame(
            parent, 
            text="⏰ 예약작업 알림 설정" if self.lang == "ko" else "⏰ Grace Warning Settings", 
            font=("Arial", 10, "bold"), 
            fg=ACCENT_BLUE, 
            bg=DARK_BG, 
            bd=1, 
            relief="solid", 
            padx=10, 
            pady=8
        )
        self.frm_grace.pack(fill="x", padx=6, pady=4)
        
        self.lbl_grace_desc = tk.Label(
            self.frm_grace,
            text="예약작업 실행 전 안내 대기시간:" if self.lang == "ko" else "Countdown before running task:",
            font=("Arial", 10),
            fg=getattr(self, "current_subtext", "#9ca3af"),
            bg=DARK_BG
        )
        self.lbl_grace_desc.pack(side="left", padx=(2, 5))
        
        self.opt_grace = tk.OptionMenu(
            self.frm_grace,
            self.grace_seconds_label,
            "10초 (10 seconds)"
        )
        self.opt_grace.config(
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            activebackground=DARK_CARD,
            activeforeground=TEXT_COLOR,
            highlightthickness=0,
            relief="flat",
            font=("Arial", 10),
            pady=0,
            padx=2
        )
        self.opt_grace["menu"].config(
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            activebackground=ACCENT_BLUE,
            activeforeground="white",
            relief="flat",
            font=("Arial", 10)
        )
        self.opt_grace['menu'].delete(0, 'end')
        for secs_opt in [5, 10, 20, 30, 60, 180, 300]:
            lbl = self.get_grace_label_by_seconds(secs_opt)
            self.opt_grace['menu'].add_command(label=lbl, command=lambda s=secs_opt: self.handle_grace_seconds_change(s))
        self.opt_grace.pack(side="left", padx=2, expand=True, fill="x")

        # 7. 강제 닫기 플래그 (/f 파라미터)
        frm_force = tk.LabelFrame(
            parent,
            text="⚡ 실행 중인 앱 강제 종료 플래그 (/f)" if self.lang == "ko" else "⚡ Force Close Apps Flag (/f)",
            font=("Arial", 10, "bold"),
            fg=getattr(self, "current_red", "#ef4444"),
            bg=DARK_BG,
            bd=1,
            relief="solid",
            padx=10,
            pady=8
        )
        frm_force.pack(fill="x", padx=6, pady=4)

        lbl_force_desc = tk.Label(
            frm_force,
            text="컴퓨터 종료/재시작 시 저장 확인 대화상자나 멈춘 앱이 있더라도 차단 없이 즉시 강제 종료(Windows /f 파라미터)합니다. (기본: 활성화)" if self.lang == "ko" else "Forces open apps and unsaved prompts to close immediately using Windows /f parameter. (Default: Enabled)",
            font=("Arial", 10),
            fg=getattr(self, "current_subtext", "#9ca3af"),
            bg=DARK_BG,
            justify="left",
            wraplength=475
        )
        lbl_force_desc.pack(anchor="w", pady=(0, 4))

        chk_pop_force = tk.Checkbutton(
            frm_force,
            text="⚡ 시스템 종료/재시작 시 강제 종료 (/f) 기본 적용" if self.lang == "ko" else "⚡ Apply Force Close (/f) by default",
            variable=self.force_close_enabled,
            command=self.save_settings,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            selectcolor=DARK_CARD,
            activebackground=DARK_BG,
            activeforeground=TEXT_COLOR,
            font=("Arial", 10, "bold"),
            wraplength=475,
            justify="left"
        )
        chk_pop_force.pack(anchor="w")

        # 8. 네트워크 수신 보안 토큰 (Network Remote Auth Token)
        frm_net_sec = tk.LabelFrame(
            parent,
            text="🔐 네트워크 수신 보안 토큰 (Auth Token)" if self.lang == "ko" else "🔐 Remote Security Token",
            font=("Arial", 10, "bold"),
            fg=getattr(self, "current_orange", "#f59e0b"),
            bg=DARK_BG,
            bd=1,
            relief="solid",
            padx=10,
            pady=8
        )
        frm_net_sec.pack(fill="x", padx=6, pady=4)

        lbl_token_desc = tk.Label(
            frm_net_sec,
            text="외부 원격 스케줄 전송 도구로부터의 요청을 승인할 인증 암호입니다.\n(비워둘 경우 인증 없이 모든 로컬 요청을 허용합니다)" if self.lang == "ko" else "Secret token required for remote scheduler requests.\n(Leave blank to allow all requests without token)",
            font=("Arial", 10),
            fg=getattr(self, "current_subtext", "#9ca3af"),
            bg=DARK_BG,
            justify="left",
            wraplength=475
        )
        lbl_token_desc.pack(anchor="w", pady=(0, 4))

        f_token_input = tk.Frame(frm_net_sec, bg=DARK_BG)
        f_token_input.pack(fill="x")

        entry_sec_token = tk.Entry(
            f_token_input,
            textvariable=self.network_auth_token,
            bg=DARK_CARD,
            fg="#fbbf24",
            insertbackground="white",
            relief="flat",
            font=("Arial", 10, "bold"),
            width=18
        )
        entry_sec_token.pack(side="left", fill="x", expand=True, padx=(0, 6))

        def copy_token_to_clipboard():
            tok = self.network_auth_token.get().strip()
            if tok:
                try:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(tok)
                except Exception:
                    pass
                from tkinter import messagebox
                messagebox.showinfo("토큰 복사" if self.lang == "ko" else "Copy Token", f"보안 인증 토큰이 클립보드에 복사되었습니다:\n{tok}" if self.lang == "ko" else f"Security token copied to clipboard:\n{tok}")
            else:
                from tkinter import messagebox
                messagebox.showinfo("토큰 복사" if self.lang == "ko" else "Copy Token", "현재 설정된 보안 토큰이 없습니다 (공백 상태)." if self.lang == "ko" else "No security token is set (blank).")

        def reset_token_manually():
            from tkinter import messagebox
            if messagebox.askyesno(
                "보안 토큰 초기화 (분실 복구)" if self.lang == "ko" else "Reset Security Token",
                "현재 등록된 보안 인증 토큰을 삭제(초기화)하시겠습니까?\n\n초기화 시 관리자가 토큰 없이 제어하거나 새 토큰을 즉시 다시 전송할 수 있습니다." if self.lang == "ko" else "Do you want to reset and clear the security token?\n\nThe administrator can then re-issue a new token remotely."
            ):
                self.network_auth_token.set("")
                self.save_settings()
                self.log_event("사용자 수동 요청으로 보안 인증 토큰이 초기화(공백)되었습니다." if self.lang == "ko" else "Security token manually reset to blank.")
                messagebox.showinfo(
                    "초기화 완료" if self.lang == "ko" else "Reset Complete",
                    "보안 인증 토큰이 성공적으로 초기화되었습니다.\n관리자 프로그램에서 새 토큰을 다시 설정할 수 있습니다." if self.lang == "ko" else "Security token has been successfully reset."
                )

        btn_copy_token = tk.Button(
            f_token_input,
            text="📋 복사" if self.lang == "ko" else "📋 Copy",
            font=("Arial", 10),
            bg="#374151",
            fg="white",
            relief="flat",
            padx=6,
            pady=1,
            command=copy_token_to_clipboard
        )
        btn_copy_token.pack(side="left", padx=(0, 4))

        btn_reset_token = tk.Button(
            f_token_input,
            text="🔄 토큰 초기화" if self.lang == "ko" else "🔄 Reset",
            font=("Arial", 10, "bold"),
            bg="#b91c1c",
            fg="white",
            relief="flat",
            padx=6,
            pady=1,
            command=reset_token_manually
        )
        btn_reset_token.pack(side="left")

        lbl_token_lost_tip = tk.Label(
            frm_net_sec,
            text="🚨 팁: 관리자가 토큰을 분실한 경우 위 [토큰 초기화]를 누르거나, 스케줄러의 [🚨 토큰 분실 복구] 마스터 키를 사용하십시오." if self.lang == "ko" else "Tip: If the admin forgot the token, click [Reset] or use the Scheduler's Master Rescue Key.",
            font=("Arial", 10),
            fg="#f59e0b",
            bg=DARK_BG,
            justify="left",
            wraplength=475
        )
        lbl_token_lost_tip.pack(anchor="w", pady=(3, 4))

        def on_token_change(*args):
            self.save_settings()

        self.network_auth_token.trace_add("write", on_token_change)

        # 9. 스케줄 공유 배포기 빌드 (Export Offline Share)
        frm_share = tk.LabelFrame(
            parent, 
            text="📤 스케줄 공유 배포기 빌드 (Share)" if self.lang == "ko" else "📤 Schedule Share Builder", 
            font=("Arial", 10, "bold"), 
            fg=getattr(self, "current_green", "#10b981"), 
            bg=DARK_BG, 
            bd=1, 
            relief="solid", 
            padx=10, 
            pady=8
        )
        frm_share.pack(fill="x", padx=6, pady=4)
        
        lbl_share_desc = tk.Label(
            frm_share,
            text="현재 설정된 모든 스케줄을 원스톱으로 강제 주입해 주는\n독립 무설치 실행파일(ApplySharedSchedules.exe)을 생성합니다." if self.lang == "ko" else "Generate a standalone one-click injector (.exe)\npre-loaded with all your current schedules.",
            font=("Arial", 10),
            fg=getattr(self, "current_subtext", "#9ca3af"),
            bg=DARK_BG,
            justify="left",
            wraplength=475
        )
        lbl_share_desc.pack(anchor="w", pady=(0, 5))
        
        btn_build_share = tk.Button(
            frm_share,
            text="📦 배포용 파일(.exe) 생성 시작" if self.lang == "ko" else "📦 Build Share Injector (.exe)",
            font=("Arial", 10, "bold"),
            bg=getattr(self, "current_green", "#10b981"),
            fg="white",
            relief="flat",
            pady=4,
            cursor="hand2",
            command=self.start_share_injector_build_thread
        )
        btn_build_share.pack(fill="x", pady=2)

        # 10. GitHub Releases 실시간 자동 업데이트 확인 (Live Auto-Update)
        frm_update = tk.LabelFrame(
            parent, 
            text="🚀 GitHub 실시간 업데이트 (Auto-Update)" if self.lang == "ko" else "🚀 GitHub Live Updates", 
            font=("Arial", 10, "bold"), 
            fg=ACCENT_BLUE, 
            bg=DARK_BG, 
            bd=1, 
            relief="solid", 
            padx=10, 
            pady=8
        )
        frm_update.pack(fill="x", padx=6, pady=4)

        f_up_info = tk.Frame(frm_update, bg=DARK_BG)
        f_up_info.pack(fill="x", pady=(0, 4))

        lbl_cur_ver = tk.Label(
            f_up_info,
            text=f"현재 설치 버전: v{APP_VERSION} ({GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME})" if self.lang == "ko" else f"Installed: v{APP_VERSION} ({GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME})",
            font=("Arial", 10, "bold"),
            fg=TEXT_COLOR,
            bg=DARK_BG
        )
        lbl_cur_ver.pack(side="left")

        self.lbl_update_status = tk.Label(
            frm_update,
            text="GitHub Releases 채널을 통해 최신 릴리스 및 업데이트를 실시간 검사합니다." if self.lang == "ko" else "Check the latest releases on GitHub in real time.",
            font=("Arial", 9),
            fg=getattr(self, "current_subtext", "#9ca3af"),
            bg=DARK_BG,
            justify="left",
            wraplength=475
        )
        self.lbl_update_status.pack(anchor="w", pady=(0, 5))

        f_up_actions = tk.Frame(frm_update, bg=DARK_BG)
        f_up_actions.pack(fill="x", pady=2)

        btn_check_now = tk.Button(
            f_up_actions,
            text="🔄 최신 업데이트 지금 확인" if self.lang == "ko" else "🔄 Check Updates Now",
            font=("Arial", 10, "bold"),
            bg=ACCENT_BLUE,
            fg="white",
            relief="flat",
            padx=8,
            pady=3,
            cursor="hand2",
            command=lambda: self.run_manual_update_check(parent_win=self.settings_popup)
        )
        btn_check_now.pack(side="left", padx=(0, 6))

        btn_view_releases = tk.Button(
            f_up_actions,
            text="🌐 릴리스 페이지 열기" if self.lang == "ko" else "🌐 View Releases",
            font=("Arial", 10),
            bg=DARK_CARD,
            fg=ACCENT_BLUE,
            relief="flat",
            padx=8,
            pady=3,
            cursor="hand2",
            command=lambda: self.open_url(GITHUB_RELEASES_URL)
        )
        btn_view_releases.pack(side="left")

        # Close handler and cleanup
        def on_close_settings():
            try:
                if getattr(ScrollableFrame, "_active_frame", None) == scroll_container:
                    ScrollableFrame._active_frame = None
                self.settings_popup.destroy()
            except Exception:
                pass

        # Confirm Close Button at bottom of popup
        btn_close = tk.Button(
            self.settings_popup,
            text="확인 (Confirm)" if self.lang == "ko" else "Confirm",
            font=("Arial", 10, "bold"),
            bg=ACCENT_BLUE,
            fg="white",
            relief="flat",
            pady=6,
            cursor="hand2",
            command=on_close_settings
        )
        btn_close.pack(fill="x", padx=15, pady=(4, 10))
        self.settings_popup.protocol("WM_DELETE_WINDOW", on_close_settings)

        # Reflect current configuration states
        self.highlight_active_theme_button(self.current_theme)
        self.update_sound_theme_buttons_ui()
        
        # Dynamically apply theme color adjustments and font overrides to this pop-up instance
        self._update_widget_colors_recursive(self.settings_popup)
        self.apply_current_font_to_widgets()
        self.update_ui_translations()

        # Recursively bind mouse wheel to all inner widgets in settings so mousewheel scrolling works seamlessly anywhere
        scroll_container.bind_children_mousewheel()

    def start_share_injector_build_thread(self):
        import tkinter.messagebox as messagebox
        import threading
        
        title = "공유 배포기 생성" if self.lang == "ko" else "Build Share Injector"
        msg = (
            "현재 저장된 모든 스케줄을 원스톱으로 강제 복사해 주는 독립 실행 파일(ApplySharedSchedules.exe)을 빌드합니다.\n\n"
            "※ 이 과정은 PyInstaller 라이브러리가 필요하며 약 10~25초가 소요됩니다. 진행하시겠습니까?"
        ) if self.lang == "ko" else (
            "Build a standalone executable (ApplySharedSchedules.exe) that instantly applies all your current schedules to other PCs.\n\n"
            "※ This process requires PyInstaller and may take 10-25 seconds. Proceed?"
        )
        
        if not messagebox.askyesno(title, msg, parent=self.settings_popup):
            return
            
        loading_win = tk.Toplevel(self.settings_popup)
        loading_win.title("빌드 중..." if self.lang == "ko" else "Building...")
        loading_win.configure(bg=DARK_BG)
        loading_win.transient(self.settings_popup)
        loading_win.grab_set()
        
        lw = 352
        lh = 120
        lx = self.settings_popup.winfo_x() + (self.settings_popup.winfo_width() // 2) - (lw // 2)
        ly = self.settings_popup.winfo_y() + (self.settings_popup.winfo_height() // 2) - (lh // 2)
        loading_win.geometry(f"{lw}x{lh}+{lx}+{ly}")
        loading_win.resizable(False, False)
        
        lbl_msg = tk.Label(
            loading_win,
            text="🛠️ 패키징 컴파일이 진행 중입니다.\n잠시만 기다려 주십시오..." if self.lang == "ko" else "🛠️ Packaging compile is in progress.\nPlease wait a moment...",
            font=("Arial", 10, "bold"),
            fg=TEXT_COLOR,
            bg=DARK_BG,
            pady=20
        )
        lbl_msg.pack()
        
        def worker():
            import sys
            import subprocess
            import os
            
            success = False
            error_detail = ""
            
            try:
                script_path = os.path.join(SCRIPT_DIR, "schedule_share_builder.py")
                if os.path.exists(script_path):
                    res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, encoding="utf-8", errors="ignore")
                    if res.returncode == 0:
                        success = True
                    else:
                        error_detail = res.stderr or res.stdout
                else:
                    error_detail = f"schedule_share_builder.py script not found at:\n{script_path}"
            except Exception as e:
                error_detail = str(e)
                
            self.root.after(0, lambda: self.finish_share_injector_build(loading_win, success, error_detail))
            
        threading.Thread(target=worker, daemon=True).start()

    def finish_share_injector_build(self, loading_win, success, error_detail):
        import tkinter.messagebox as messagebox
        import os
        import subprocess
        try:
            loading_win.destroy()
        except:
            pass
            
        # My Documents (내 문서) 경로 획득
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
            
        dest_exe_path = os.path.join(my_documents, "ApplySharedSchedules.exe")
            
        title = "빌드 완료" if self.lang == "ko" else "Build Complete"
        if success:
            msg = (
                "🎉 단일 실행형 스케줄 공유 배포기 빌드가 성사되었습니다!\n\n"
                f"생성 위치: {dest_exe_path}\n\n"
                "[사용 설명]\n"
                f"1. '{dest_exe_path}' 파일을 다른 컴퓨터로 가져갑니다.\n"
                "2. 대상 컴퓨터에서 실행하면 자동으로 기존 PowerController 프로그램을 안전하게 종료하고 현재 스케줄을 주입한 뒤 앱을 재부팅해 줍니다!"
            ) if self.lang == "ko" else (
                "🎉 Standalone schedule share injector built successfully!\n\n"
                f"Created at: {dest_exe_path}\n\n"
                "[How to use]\n"
                f"1. Distribute '{dest_exe_path}' to other PCs.\n"
                "2. Simply double-click to automatically close PowerController, copy current schedules, and restart the app!"
            )
            messagebox.showinfo(title, msg, parent=self.settings_popup)
            
            try:
                if os.name == 'nt':
                    os.startfile(my_documents)
                elif sys.platform == 'darwin':
                    subprocess.Popen(["open", my_documents])
                else:
                    subprocess.Popen(["xdg-open", my_documents])
            except:
                pass
        else:
            err_title = "빌드 실패" if self.lang == "ko" else "Build Failed"
            err_msg = (
                f"배포기 빌드 중 오류가 발생했습니다.\n\n[상세 내용]\n{error_detail}"
            ) if self.lang == "ko" else (
                f"An error occurred during build.\n\n[Details]\n{error_detail}"
            )
            messagebox.showerror(err_title, err_msg, parent=self.settings_popup)

    def check_auto_update_on_startup(self):
        """앱 구동 시 백그라운드로 GitHub Releases 최신 버전을 확인하고, 신규 업데이트가 있으면 알림 팝업창을 자동 실행합니다."""
        def worker():
            try:
                has_update, latest_ver, release_url, release_title, release_body = check_github_update(APP_VERSION)
                if has_update:
                    def on_found():
                        # 메인 윈도우 표시 여부와 관계없이 최신 업데이트 팝업창 자동 실행
                        p_win = self.root if not self.start_hidden else None
                        self.show_update_modal(latest_ver, release_url, release_title, release_body, parent_win=p_win)
                        self.log_event(
                            f"🔔 최신 버전(v{latest_ver}) 발견: 업데이트 알림 팝업창을 자동으로 실행했습니다." if self.lang == "ko" else f"🔔 New version v{latest_ver} detected: Auto-launched update notification popup."
                        )
                    self.root.after(0, on_found)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def run_manual_update_check(self, parent_win=None):
        """수동으로 GitHub Releases 최신 버전을 실시간 조회하여 사용자에게 안내합니다."""
        import tkinter.messagebox as messagebox
        p_win = parent_win or self.root
        
        if hasattr(self, "lbl_update_status") and self.lbl_update_status and self.lbl_update_status.winfo_exists():
            self.lbl_update_status.config(
                text="⏳ GitHub API를 통해 최신 릴리스 정보를 확인하고 있습니다..." if self.lang == "ko" else "⏳ Checking GitHub API for the latest release...",
                fg=ACCENT_BLUE
            )

        def worker():
            has_update, latest_ver, release_url, release_title, release_body = check_github_update(APP_VERSION)
            
            def on_done():
                if has_update:
                    if hasattr(self, "lbl_update_status") and self.lbl_update_status and self.lbl_update_status.winfo_exists():
                        self.lbl_update_status.config(
                            text=f"🎉 최신 업데이트 발견: v{latest_ver}! (현재 v{APP_VERSION})" if self.lang == "ko" else f"🎉 New version found: v{latest_ver}! (Installed: v{APP_VERSION})",
                            fg=getattr(self, "current_green", "#10b981")
                        )
                    self.show_update_modal(latest_ver, release_url, release_title, release_body, parent_win=p_win)
                else:
                    msg = (
                        f"현재 설치된 버전(v{APP_VERSION})이 최신 버전입니다!\n\n"
                        f"GitHub 저장소: {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}\n"
                        "새로운 업데이트가 게시되면 다시 안내해 드립니다."
                    ) if self.lang == "ko" else (
                        f"You are running the latest version (v{APP_VERSION})!\n\n"
                        f"GitHub Repo: {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}\n"
                        "No new updates found."
                    )
                    if hasattr(self, "lbl_update_status") and self.lbl_update_status and self.lbl_update_status.winfo_exists():
                        self.lbl_update_status.config(
                            text=f"✓ 현재 최신 버전(v{APP_VERSION})을 사용 중입니다." if self.lang == "ko" else f"✓ You are up to date (v{APP_VERSION}).",
                            fg=getattr(self, "current_subtext", "#9ca3af")
                        )
                    messagebox.showinfo("업데이트 확인" if self.lang == "ko" else "Update Check", msg, parent=p_win)
            
            self.root.after(0, on_done)

        threading.Thread(target=worker, daemon=True).start()

    def show_update_modal(self, latest_ver, release_url, release_title, release_body, parent_win=None):
        """새 버전 발견 시 세련된 릴리스 안내 모달 팝업창을 최상단으로 자동 표시합니다."""
        p_win = parent_win or self.root
        modal = tk.Toplevel(p_win)
        modal.title("🚀 새로운 업데이트 알림" if self.lang == "ko" else "🚀 New Update Available")
        modal.configure(bg=DARK_BG)
        modal.transient(p_win)
        modal.resizable(False, False)
        modal.attributes('-topmost', True)

        mw = 480
        mh = 340
        try:
            mx = p_win.winfo_x() + (p_win.winfo_width() // 2) - (mw // 2)
            my = p_win.winfo_y() + (p_win.winfo_height() // 2) - (mh // 2)
        except:
            mx = (modal.winfo_screenwidth() // 2) - (mw // 2)
            my = (modal.winfo_screenheight() // 2) - (mh // 2)
        modal.geometry(f"{mw}x{mh}+{mx}+{my}")
        modal.lift()
        modal.focus_force()

        lbl_t = tk.Label(
            modal,
            text=f"🎉 새로운 버전 v{latest_ver} 이 출시되었습니다!" if self.lang == "ko" else f"🎉 New Version v{latest_ver} is Available!",
            font=("Arial", 11, "bold"),
            fg=getattr(self, "current_green", "#10b981"),
            bg=DARK_BG,
            pady=10
        )
        lbl_t.pack()

        lbl_sub = tk.Label(
            modal,
            text=f"현재 버전: v{APP_VERSION}  ➔  최신 버전: v{latest_ver}\n릴리스 명: {release_title}",
            font=("Arial", 10),
            fg=TEXT_COLOR,
            bg=DARK_BG,
            justify="center"
        )
        lbl_sub.pack(pady=(0, 8))

        # Release body text box
        txt_frame = tk.Frame(modal, bg=DARK_CARD, bd=1, relief="solid")
        txt_frame.pack(fill="both", expand=True, padx=16, pady=4)

        txt_body = tk.Text(
            txt_frame,
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            font=("Arial", 9),
            wrap="word",
            bd=0,
            padx=8,
            pady=8
        )
        txt_body.pack(fill="both", expand=True)
        txt_body.insert("1.0", release_body or "새로운 기능 개선 및 안정성 향상이 포함되었습니다.")
        txt_body.config(state="disabled")

        # Bottom buttons
        btn_frame = tk.Frame(modal, bg=DARK_BG)
        btn_frame.pack(fill="x", padx=16, pady=10)

        def download_now():
            self.open_url(release_url or GITHUB_RELEASES_URL)
            modal.destroy()

        btn_download = tk.Button(
            btn_frame,
            text="📥 최신 버전 다운로드 (GitHub)" if self.lang == "ko" else "📥 Download Now (GitHub)",
            font=("Arial", 10, "bold"),
            bg=getattr(self, "current_green", "#10b981"),
            fg="white",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=download_now
        )
        btn_download.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_close = tk.Button(
            btn_frame,
            text="나중에" if self.lang == "ko" else "Later",
            font=("Arial", 10),
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=modal.destroy
        )
        btn_close.pack(side="right")

    def click_license_notice(self):
        # Stop the running timer
        self.reset_timer()
        
        # Show standard license popup dialog with scrolled text
        license_win = tk.Toplevel(self.root)
        license_win.title("사용권 계약 및 오픈소스 라이선스 약관 고지" if self.lang == "ko" else "License & Terms Agreement Notice")
        license_win.configure(bg=DARK_BG)
        
        # Geometry and center
        window_width = 506
        window_height = 420
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        license_win.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        license_win.resizable(False, False)
        
        # Top Header Frame with Title & Language Switch Buttons
        header_frame = tk.Frame(license_win, bg=DARK_BG)
        header_frame.pack(fill="x", padx=15, pady=(8, 4))
        
        current_lic_lang = "ko" if self.lang == "ko" else "en"
        
        # Title Label
        title_lbl = tk.Label(
            header_frame,
            text="📜 라이선스 및 약관 동의 고지서" if current_lic_lang == "ko" else "📜 License & Terms Agreement Notice",
            font=("Arial", 10, "bold"),
            fg=ACCENT_BLUE,
            bg=DARK_BG
        )
        title_lbl.pack(side="left")
        
        # Try to import standard licenses from installer or fallback to inline definitions
        lic_ko = ""
        lic_en = ""
        try:
            from installer import STANDARD_LICENSE_KO, STANDARD_LICENSE_EN
            lic_ko = STANDARD_LICENSE_KO
            lic_en = STANDARD_LICENSE_EN
        except ImportError:
            lic_ko = (
                "[사용권 계약 및 오픈소스 라이선스 약관 고지]\n\n"
                "본 프로그램(PowerController)의 사용권 및 사용된 오픈소스 소프트웨어 구성 정보 고지사항입니다.\n\n"
                "1. 프로그램 표준 라이선스 (MIT License)\n"
                "Copyright (c) 2026 AhBiYout\n\n"
                "이 소프트웨어의 복제본과 관련된 문서 파일(이하 '소프트웨어')을 획득하는 모든 사람에게 소프트웨어를 제한 없이 사용할 수 있는 권한을 부여합니다. 여기에는 소프트웨어의 사본을 사용, 복제, 수정, 병합, 게시, 배포, 서브라이선스 부여 및/또는 판매할 수 있는 권한이 포함됩니다.\n\n"
                "소프트웨어는 '있는 그대로' 제공되며, 어떠한 종류의 보증도 제공하지 않습니다. 저작자나 저작권자는 소프트웨어 또는 소프트웨어의 사용과 관련하여 발생하는 어떠한 손해나 책임에 대해서도 책임지지 않습니다.\n\n"
                "2. 사용된 오픈소스 라이브러리 및 저작권\n"
                "■ pystray (v0.19.5+) - LGPL v3 / BSD Dual License\n"
                "■ Pillow (PIL) - HPND License\n"
                "■ PyInstaller (v6.0+) - GPL v2 with Bootloader Exception\n"
                "■ Tkinter - PSF License\n"
            )
            lic_en = (
                "[License and Terms Agreement Notice]\n\n"
                "This is the license and third-party software configuration notice for PowerController.\n\n"
                "1. Standard MIT License\n"
                "Copyright (c) 2026 AhBiYout\n\n"
                "Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software.\n\n"
                "THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE.\n\n"
                "2. Open Source Libraries\n"
                "■ pystray (v0.19.5+) - LGPL v3 / BSD Dual License\n"
                "■ Pillow (PIL) - HPND License\n"
                "■ PyInstaller (v6.0+) - GPL v2 with Bootloader Exception\n"
                "■ Tkinter - PSF License\n"
            )

        # Scrolled text area for license
        text_frame = tk.Frame(license_win, bg=DARK_BG)
        text_frame.pack(fill="both", expand=True, padx=15, pady=(4, 6))
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        license_text_widget = tk.Text(
            text_frame,
            wrap="word",
            yscrollcommand=scrollbar.set,
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            font=("Arial", 10),
            relief="flat",
            padx=10,
            pady=10
        )
        license_text_widget.insert("1.0", lic_ko if current_lic_lang == "ko" else lic_en)
        license_text_widget.config(state="disabled")
        license_text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=license_text_widget.yview)
        
        # Info about timer stopped
        info_lbl_text = "⚠️ 고지서 열람으로 인해 가동 중이던 타이머가 즉시 정지되었습니다." if current_lic_lang == "ko" else "⚠️ Active timer has been stopped due to license viewing."
        info_lbl = tk.Label(
            license_win,
            text=info_lbl_text,
            font=("Arial", 10, "bold"),
            fg=ACCENT_RED,
            bg=DARK_BG,
            pady=4
        )
        info_lbl.pack(fill="x")
        
        # Close button
        close_btn = tk.Button(
            license_win,
            text="확인" if current_lic_lang == "ko" else "OK",
            font=("Arial", 10, "bold"),
            bg=ACCENT_BLUE,
            fg="white",
            relief="flat",
            padx=15,
            pady=4,
            command=license_win.destroy
        )
        close_btn.pack(pady=(4, 10))

        # Language toggle function
        def set_modal_license_lang(target_code):
            nonlocal current_lic_lang
            current_lic_lang = target_code
            license_text_widget.config(state="normal")
            license_text_widget.delete("1.0", "end")
            license_text_widget.insert("1.0", lic_ko if target_code == "ko" else lic_en)
            license_text_widget.config(state="disabled")
            license_text_widget.yview_moveto(0.0)
            
            title_lbl.config(
                text="📜 라이선스 및 약관 동의 고지서" if target_code == "ko" else "📜 License & Terms Agreement Notice"
            )
            license_win.title(
                "사용권 계약 및 오픈소스 라이선스 약관 고지" if target_code == "ko" else "License & Terms Agreement Notice"
            )
            info_lbl.config(
                text="⚠️ 고지서 열람으로 인해 가동 중이던 타이머가 즉시 정지되었습니다." if target_code == "ko" else "⚠️ Active timer has been stopped due to license viewing."
            )
            close_btn.config(
                text="확인" if target_code == "ko" else "OK"
            )
            btn_ko.config(
                bg=ACCENT_BLUE if target_code == "ko" else DARK_CARD,
                fg="white" if target_code == "ko" else "#9ca3af"
            )
            btn_en.config(
                bg=ACCENT_BLUE if target_code == "en" else DARK_CARD,
                fg="white" if target_code == "en" else "#9ca3af"
            )

        btn_en = tk.Button(
            header_frame,
            text="🇺🇸 EN",
            font=("Arial", 8, "bold"),
            bg=ACCENT_BLUE if current_lic_lang == "en" else DARK_CARD,
            fg="white" if current_lic_lang == "en" else "#9ca3af",
            relief="flat",
            padx=7,
            pady=1,
            cursor="hand2",
            command=lambda: set_modal_license_lang("en")
        )
        btn_en.pack(side="right", padx=(2, 0))

        btn_ko = tk.Button(
            header_frame,
            text="🇰🇷 KO",
            font=("Arial", 8, "bold"),
            bg=ACCENT_BLUE if current_lic_lang == "ko" else DARK_CARD,
            fg="white" if current_lic_lang == "ko" else "#9ca3af",
            relief="flat",
            padx=7,
            pady=1,
            cursor="hand2",
            command=lambda: set_modal_license_lang("ko")
        )
        btn_ko.pack(side="right", padx=(0, 2))
        
        # Make the window grab focus (modal style but non-blocking)
        license_win.transient(self.root)
        license_win.grab_set()
        auto_fit_window(license_win, min_w=506, min_h=420, center_parent=self.root)

SINGLE_INSTANCE_PORT = 59384
server_socket_ref = None
mutex_lock_object = None  # Prevent garbage collection of mutex handle

def is_startup_invocation():
    """CLI 파라미터 또는 윈도우 부팅 직후 자동 실행 여부를 판별합니다."""
    startup_flags = ["--startup", "-startup", "/startup", "--tray", "-tray", "/tray", "-s", "--boot", "-boot", "--minimized", "-minimized", "-m"]
    if any(arg.lower() in startup_flags for arg in sys.argv[1:]):
        return True
    if sys.platform == "win32":
        try:
            import ctypes
            uptime_ms = ctypes.windll.kernel32.GetTickCount64()
            if uptime_ms < 360000:
                return True
        except Exception:
            pass
    return False

def check_single_instance_built_in():
    global server_socket_ref, mutex_lock_object
    
    # 설치 마법사 또는 스크립트에서 기존 인스턴스 종료 요청(--kill, --quit 등) 시 QUIT 전송 후 즉시 종료
    if any(arg.lower() in ["--kill", "-kill", "/kill", "--quit", "-quit", "/quit", "--terminate", "-terminate"] for arg in sys.argv[1:]):
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.settimeout(0.5)
            conn.connect(("127.0.0.1", SINGLE_INSTANCE_PORT))
            conn.sendall(b"QUIT")
            conn.close()
        except Exception:
            pass
        sys.exit(0)

    is_startup = is_startup_invocation()
    
    # 1. Windows Named Mutex Check (Zero Race Condition)
    if sys.platform == "win32":
        try:
            import ctypes
            mutex_name = "Global\\PowerControllerSingleInstanceMutex_f8908445"
            kernel32 = ctypes.windll.kernel32
            mutex_lock_object = kernel32.CreateMutexW(None, False, mutex_name)
            last_error = kernel32.GetLastError()
            if last_error == 183:  # ERROR_ALREADY_EXISTS
                # 이미 실행 중인 경우:
                # 컴퓨터 시작(부팅) 시 백그라운드로 뜰 때는 메인 창 복원 요청을 보내지 않고 무음 즉시 종료
                if is_startup:
                    sys.exit(0)
                # 사용자가 직접 바로가기를 클릭하여 실행한 경우에만 기존 창 원복 지시
                try:
                    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    conn.settimeout(0.5)
                    conn.connect(("127.0.0.1", SINGLE_INSTANCE_PORT))
                    conn.sendall(b"RESTORE")
                    conn.close()
                except Exception:
                    pass
                sys.exit(0)
        except Exception:
            pass

    # 2. General Port Binding Check (Fallback or cross-platform)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", SINGLE_INSTANCE_PORT))
        s.listen(1)
        server_socket_ref = s
        return True
    except socket.error:
        # 이미 다른 인스턴스가 동작 중이므로 활성화된 인스턴스에 복구 전송 후 종료
        if is_startup:
            sys.exit(0)
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.settimeout(0.5)
            conn.connect(("127.0.0.1", SINGLE_INSTANCE_PORT))
            conn.sendall(b"RESTORE")
            conn.close()
        except Exception:
            pass
        sys.exit(0)

if __name__ == "__main__":
    check_single_instance_built_in()
    root = tk.Tk()

    startup_flags = ["--startup", "-startup", "/startup", "--tray", "-tray", "/tray", "-s", "--boot", "-boot", "--minimized", "-minimized", "-m"]
    is_cli_startup = any(arg.lower() in startup_flags for arg in sys.argv[1:])

    is_boot_time = False
    if sys.platform == "win32":
        try:
            import ctypes
            uptime_ms = ctypes.windll.kernel32.GetTickCount64()
            if uptime_ms < 360000:
                is_boot_time = True
        except Exception:
            pass

    is_saved_boot_to_tray = True
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                _cfg = json.load(f)
                is_saved_boot_to_tray = _cfg.get("boot_to_tray", True)
    except Exception:
        pass

    # 컴퓨터 시작 시에는 메인창이 화면에 일절 노출되지 않도록 최초 인스턴스화 시점부터 즉시 withdraw
    start_hidden = is_cli_startup or (is_boot_time and is_saved_boot_to_tray)
    if start_hidden:
        root.withdraw()

    app = PowerTimerApp(root, start_hidden=start_hidden)
    if server_socket_ref:
        app.start_single_instance_listener(server_socket_ref)
    root.mainloop()
