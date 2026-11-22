import type { AppLang } from './i18n';

/**
 * Generates a standalone Python Tkinter GUI script for PowerController
 * with all UI labels, presets, dialogs, tray items, and inline comments
 * dynamically localized to the selected/auto-detected language.
 */
export function generatePythonScript(
  lang: AppLang,
  desktopName: string,
  appVersion: string
): string {
  const safeName = desktopName.replace(/[^a-zA-Z0-9_-]/g, '') || 'PowerController';
  const isEn = lang === 'en';

  return `# ==============================================================================
# ${safeName} v${appVersion} — ${isEn ? 'Standalone Windows Power Control & Timer Agent' : '윈도우 독립 실행형 전원 제어 및 자동 종료 에이전트'}
# ${isEn ? 'Author: AhBiYout | Official Blog: https://ahbiyoutvibe.blogspot.com/' : '제작자: AhBiYout | 공식 블로그: https://ahbiyoutvibe.blogspot.com/'}
# ${isEn ? 'Auto-generated script with dynamically localized labels & comments (EN)' : '사용자 언어에 맞춰 레이블과 주석이 동적으로 생성된 스크립트 (KO)'}
# ==============================================================================

import os
import sys
import json
import locale
import ctypes
import datetime
import threading
import tkinter as tk
from tkinter import messagebox

# ${isEn ? 'Optional Windows registry integration for automatic launch on startup' : 'Windows 시작 시 자동 실행 등록을 위한 레지스트리 모듈 로드'}
try:
    import winreg
    WINDOWS_REG_AVAILABLE = True
except ImportError:
    WINDOWS_REG_AVAILABLE = False

# ${isEn ? 'Optional system tray support (install via: pip install pystray pillow)' : '시스템 트레이 백그라운드 상주 모듈 로드 (pip install pystray pillow)'}
try:
    import pystray
    from PIL import Image, ImageDraw
    P_TRAY_AVAILABLE = True
except ImportError:
    P_TRAY_AVAILABLE = False

# ${isEn ? 'Application runtime constants & theme color palette' : '애플리케이션 실행 상수 및 다크 테마 색상 팔레트'}
APP_VERSION = "${appVersion}"
CONFIG_FILE = "power_timer_presets.json"
DEFAULT_LANG = "${lang}"  # ${isEn ? 'Injected from active UI locale' : '현재 감지/선택된 기본 언어'}
DARK_BG = "#111827"
DARK_CARD = "#1f2937"
TEXT_COLOR = "#f3f4f6"
ACCENT_BLUE = "#3b82f6"
ACCENT_RED = "#ef4444"


def detect_system_language(fallback=DEFAULT_LANG):
    """${isEn ? 'Auto-detect OS UI language (Korean vs English) with configurable fallback.' : '운영체제 기본 UI 언어(한국어/영어)를 자동 감지합니다.'}"""
    env_lang = os.getenv("POWERCONTROLLER_LANG", "").strip().lower()
    if env_lang in ("ko", "en"):
        return env_lang

    # ${isEn ? 'Check Windows Kernel32 UI Language ID when running on Windows' : 'Windows 환경에서 Kernel32 UI 언어 ID 조회 (0x0412 = 한국어)'}
    if sys.platform == "win32":
        try:
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if (lang_id & 0xFF) == 0x12:  # LANG_KOREAN
                return "ko"
            if (lang_id & 0xFF) == 0x09:  # LANG_ENGLISH
                return "en"
        except Exception:
            pass

    # ${isEn ? 'Fallback to Python standard locale detection' : '표준 Python locale 모듈을 통한 로케일 폴백 감지'}
    try:
        sys_locale = (locale.getdefaultlocale()[0] or "").lower()
        if sys_locale.startswith("ko"):
            return "ko"
        if sys_locale.startswith("en"):
            return "en"
    except Exception:
        pass

    return fallback


class PowerTimerApp:
    """${isEn ? 'Main desktop timer window controller with system tray and Windows startup support.' : '시스템 트레이 및 시작 프로그램 등록을 지원하는 메인 전원 제어 GUI 클래스'}"""

    def __init__(self, root):
        self.root = root
        self.lang = DEFAULT_LANG or detect_system_language()

        # ${isEn ? 'Configure window title, fixed dimensions, and dark canvas theme' : '메인 윈도우 제목, 크기 고정 및 다크 배경 테마 초기화'}
        self.root.title("${isEn ? `${safeName} v${appVersion} — Power Off / Reboot Timer` : `${safeName} v${appVersion} — 전원 종료/재시작 타이머`}")
        self.root.geometry("390x510")
        self.root.resizable(False, False)
        self.root.configure(bg=DARK_BG)

        # ${isEn ? 'Keep window pinned on top of other desktop windows by default' : '다른 창 위에 항상 고정(Always on Top) 기본 활성화'}
        self.always_on_top = tk.BooleanVar(value=True)
        self.root.attributes("-topmost", True)

        self.mode = "shutdown"
        self.run_type = "timer"
        self.remaining_seconds = 0
        self.timer_running = False
        self.timer_paused = False
        self.favorites = []
        self.tray_icon = None

        # ${isEn ? 'Minimize to system tray on close instead of terminating abruptly' : '창 닫기 버튼 클릭 시 즉시 종료하지 않고 트레이로 최소화'}
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_button)
        self.load_favorites()
        self.auto_start = tk.BooleanVar(value=self.check_startup_reg())
        self.create_widgets()

    def load_favorites(self):
        """${isEn ? 'Load saved presets from JSON file or create localized defaults.' : '저장된 즐겨찾기 JSON 파일을 불러오거나 언어별 기본 프리셋을 생성합니다.'}"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.favorites = json.load(f)
                    return
            except Exception:
                pass
        self.load_default_presets()

    def load_default_presets(self):
        """${isEn ? 'Initialize default quick presets matching the active language.' : '현재 언어에 맞는 기본 빠른 타이머 프리셋을 초기화합니다.'}"""
        if self.lang == "en":
            self.favorites = [
                {"label": "Shutdown after movie (2h)", "mode": "shutdown", "seconds": 7200},
                {"label": "Lunch break quick reboot (1h)", "mode": "restart", "seconds": 3600},
                {"label": "Short focus shutdown (15m)", "mode": "shutdown", "seconds": 900}
            ]
        else:
            self.favorites = [
                {"label": "영화 시청 후 종료 (2시간)", "mode": "shutdown", "seconds": 7200},
                {"label": "점심시간 빠른 재부팅 (1시간)", "mode": "restart", "seconds": 3600},
                {"label": "15분 집중 후 종료", "mode": "shutdown", "seconds": 900}
            ]
        self.save_favorites()

    def save_favorites(self):
        """${isEn ? 'Persist favorite presets cleanly with UTF-8 encoding.' : '즐겨찾기 목록을 UTF-8 인코딩으로 JSON 파일에 저장합니다.'}"""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def create_widgets(self):
        """${isEn ? 'Build Tkinter GUI controls, spinboxes, and action buttons.' : 'Tkinter GUI 위젯, 시간 입력 스핀박스 및 실행 제어 버튼을 구성합니다.'}"""
        header_frame = tk.Frame(self.root, bg=DARK_BG, pady=6)
        header_frame.pack(fill="x", padx=15)

        title_text = "${isEn ? `⚡ ${safeName} · System Power Agent` : `⚡ ${safeName} · 스마트 전원 제어 (AhBiYout)`}"
        title_label = tk.Label(header_frame, text=title_text, font=("Arial", 11, "bold"), fg=TEXT_COLOR, bg=DARK_BG)
        title_label.pack(side="left")

        # ${isEn ? 'Top quick toggles: Always on Top & Windows Startup registration' : '상단 빠른 옵션: 창 항상 위 고정 및 Windows 시작 시 자동 실행'}
        options_frame = tk.Frame(self.root, bg=DARK_BG)
        options_frame.pack(fill="x", padx=15, pady=(0, 5))

        pin_btn = tk.Checkbutton(
            options_frame,
            text="${isEn ? '📌 Always on Top' : '📌 상단 고정'}",
            variable=self.always_on_top,
            command=self.toggle_always_on_top,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            selectcolor=DARK_CARD,
            activebackground=DARK_BG,
            activeforeground=TEXT_COLOR,
            font=("Arial", 8, "bold")
        )
        pin_btn.pack(side="left")

        auto_start_btn = tk.Checkbutton(
            options_frame,
            text="${isEn ? '⚙️ Auto Start with Windows' : '⚙️ 시작 시 자동 실행'}",
            variable=self.auto_start,
            command=self.toggle_startup,
            bg=DARK_BG,
            fg=TEXT_COLOR,
            selectcolor=DARK_CARD,
            activebackground=DARK_BG,
            activeforeground=TEXT_COLOR,
            font=("Arial", 8, "bold")
        )
        auto_start_btn.pack(side="right")

        # ${isEn ? 'Power operation mode selector buttons' : '전원 동작 모드 선택 버튼 영역 (종료, 재시작, 절전, 화면끄기, 로그아웃)'}
        mode_frame = tk.Frame(self.root, bg=DARK_BG, pady=5)
        mode_frame.pack(fill="x", padx=15)

        self.mode_buttons = {}
        modes = [
            ("shutdown", "${isEn ? '🔴 Shutdown' : '🔴 종료'}"),
            ("restart", "${isEn ? '🔵 Restart' : '🔵 재시작'}"),
            ("sleep", "${isEn ? '🌙 Sleep' : '🌙 절전'}"),
            ("screenoff", "${isEn ? '💻 ScreenOff' : '💻 화면끔'}"),
            ("logout", "${isEn ? '🚪 Logout' : '🚪 로그아웃'}")
        ]

        for m_id, label in modes:
            btn = tk.Button(
                mode_frame,
                text=label,
                font=("Arial", 8, "bold"),
                bg=ACCENT_RED if m_id == "shutdown" else DARK_CARD,
                fg="white" if m_id == "shutdown" else TEXT_COLOR,
                relief="flat",
                pady=6,
                command=lambda m=m_id: self.set_mode(m)
            )
            btn.pack(side="left", expand=True, fill="x", padx=2)
            self.mode_buttons[m_id] = btn

        # ${isEn ? 'Execution mode switcher: Countdown Duration vs Fixed Clock Time' : '실행 방식 전환: 경과 시간 타이머 vs 특정 시각 정시 예약'}
        type_frame = tk.Frame(self.root, bg=DARK_BG, pady=5)
        type_frame.pack(fill="x", padx=15)

        self.btn_type_timer = tk.Button(
            type_frame,
            text="${isEn ? '⏳ Duration Timer' : '⏳ 시간 타이머 (후)'}",
            font=("Arial", 9, "bold"),
            bg=ACCENT_BLUE,
            fg="white",
            relief="flat",
            pady=4,
            command=lambda: self.set_run_type("timer")
        )
        self.btn_type_timer.pack(side="left", expand=True, fill="x", padx=5)

        self.btn_type_schedule = tk.Button(
            type_frame,
            text="${isEn ? '⏰ Schedule Clock' : '⏰ 특정 시각 예약 (정시)'}",
            font=("Arial", 9, "bold"),
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            relief="flat",
            pady=4,
            command=lambda: self.set_run_type("schedule")
        )
        self.btn_type_schedule.pack(side="left", expand=True, fill="x", padx=5)

        # ${isEn ? 'Digital countdown display panel' : '디지털 카운트다운 LED 디스플레이 패널'}
        self.display_frame = tk.Frame(self.root, bg=DARK_CARD, bd=1, relief="solid")
        self.display_frame.pack(fill="x", padx=20, pady=10)

        self.lbl_timer = tk.Label(
            self.display_frame,
            text="00:30:00",
            font=("Courier", 32, "bold"),
            bg=DARK_CARD,
            fg="#60a5fa"
        )
        self.lbl_timer.pack(pady=10)

        # ${isEn ? 'Hour / Minute / Second spinbox input container' : '시 / 분 / 초 스핀박스 숫자 입력 필드'}
        self.input_parent_frame = tk.Frame(self.root, bg=DARK_BG)
        self.input_parent_frame.pack(fill="x", padx=20)

        self.lbl_input_guide = tk.Label(
            self.input_parent_frame,
            text="${isEn ? '[Duration] Enter hours/minutes/seconds before trigger:' : '[경과 시간 입력] 몇 시간/분/초 후에 전원을 제어할지 지정하십시오.'}",
            font=("Arial", 8, "bold"),
            fg="#9ca3af",
            bg=DARK_BG,
            anchor="w"
        )
        self.lbl_input_guide.pack(fill="x", pady=2)

        self.input_fields_frame = tk.Frame(self.input_parent_frame, bg=DARK_BG)
        self.input_fields_frame.pack(pady=5)

        self.lbl_field_1 = tk.Label(self.input_fields_frame, text="${isEn ? 'Hour' : '시 (H)'}", font=("Arial", 8), fg="#9ca3af", bg=DARK_BG)
        self.lbl_field_1.grid(row=0, column=0, padx=5)
        self.lbl_field_2 = tk.Label(self.input_fields_frame, text="${isEn ? 'Min' : '분 (M)'}", font=("Arial", 8), fg="#9ca3af", bg=DARK_BG)
        self.lbl_field_2.grid(row=0, column=1, padx=5)
        self.lbl_field_3 = tk.Label(self.input_fields_frame, text="${isEn ? 'Sec' : '초 (S)'}", font=("Arial", 8), fg="#9ca3af", bg=DARK_BG)
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

        self.bind_spin_interactions(self.ent_h, "h")
        self.bind_spin_interactions(self.ent_m, "m")
        self.bind_spin_interactions(self.ent_s, "s")

        # ${isEn ? 'Primary action controls: Start / Pause and Reset' : '주요 제어 버튼: 타이머 시작/일시정지 및 초기화(리셋)'}
        ctrl_frame = tk.Frame(self.root, bg=DARK_BG, pady=10)
        ctrl_frame.pack(fill="x", padx=20)

        self.btn_start = tk.Button(
            ctrl_frame,
            text="${isEn ? '▶ Start Timer' : '▶ 타이머 시작'}",
            font=("Arial", 10, "bold"),
            bg=ACCENT_BLUE,
            fg="white",
            relief="flat",
            command=self.start_timer
        )
        self.btn_start.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_reset = tk.Button(
            ctrl_frame,
            text="${isEn ? '🔄 Reset' : '🔄 리셋'}",
            font=("Arial", 10, "bold"),
            bg="#374151",
            fg=TEXT_COLOR,
            relief="flat",
            command=self.reset_timer
        )
        self.btn_reset.pack(side="left", expand=True, fill="x", padx=2)

        credit_label = tk.Label(
            self.root,
            text="${isEn ? 'Developed by AhBiYout · cisnet.co.kr' : '제작자: AhBiYout · cisnet.co.kr'}",
            font=("Arial", 8),
            fg="#6b7280",
            bg=DARK_BG
        )
        credit_label.pack(side="bottom", pady=5)

    def bind_spin_interactions(self, entry, field_type):
        """${isEn ? 'Bind mouse wheel and Up/Down arrow keys to increment/decrement input fields.' : '마우스 휠 및 방향키(상/하) 입력으로 숫자를 증감할 수 있도록 바인딩합니다.'}"""
        entry.bind("<MouseWheel>", lambda event: self.handle_spin(event, entry, field_type, "wheel"))
        entry.bind("<Button-4>", lambda event: self.handle_spin(event, entry, field_type, "up"))
        entry.bind("<Button-5>", lambda event: self.handle_spin(event, entry, field_type, "down"))
        entry.bind("<Up>", lambda event: self.handle_spin(event, entry, field_type, "up"))
        entry.bind("<Down>", lambda event: self.handle_spin(event, entry, field_type, "down"))

    def handle_spin(self, event, entry, field_type, direction):
        if self.timer_running:
            return "break"

        delta = (1 if event.delta > 0 else -1) if direction == "wheel" else (1 if direction == "up" else -1)
        try:
            val = int(entry.get() or 0)
        except ValueError:
            val = 0

        if field_type == "h":
            min_val, max_val, wrap = (0, 23, True) if self.run_type == "schedule" else (0, 999, False)
        else:
            min_val, max_val, wrap = 0, 59, True

        new_val = val + delta
        if wrap:
            new_val = min_val if new_val > max_val else (max_val if new_val < min_val else new_val)
        else:
            new_val = max(min_val, min(max_val, new_val))

        entry.delete(0, tk.END)
        entry.insert(0, str(new_val))
        return "break"

    def toggle_always_on_top(self):
        self.root.attributes("-topmost", self.always_on_top.get())

    def get_mode_label(self, mode):
        if self.lang == "en":
            return {"shutdown": "Shutdown", "restart": "Restart", "sleep": "Sleep", "screenoff": "Screen Off", "logout": "Logout"}.get(mode, "Power Action")
        return {"shutdown": "종료", "restart": "재시작", "sleep": "절전", "screenoff": "화면 끄기", "logout": "로그아웃"}.get(mode, "전원 동작")

    def set_mode(self, mode):
        self.mode = mode
        for m_id, btn in self.mode_buttons.items():
            btn.configure(bg=(ACCENT_RED if mode == "shutdown" else ACCENT_BLUE) if m_id == mode else DARK_CARD, fg="white" if m_id == mode else TEXT_COLOR)

    def set_run_type(self, run_type):
        if self.timer_running:
            messagebox.showwarning(
                "${isEn ? 'Warning' : '오류'}",
                "${isEn ? 'Please stop or reset the running timer first.' : '예약이 이미 가동 중일 때는 변경할 수 없습니다. 리셋 후 변경하십시오.'}"
            )
            return

        self.run_type = run_type
        if run_type == "timer":
            self.btn_type_timer.configure(bg=ACCENT_BLUE, fg="white")
            self.btn_type_schedule.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            self.lbl_input_guide.configure(text="${isEn ? '[Duration] Enter hours/minutes/seconds before trigger:' : '[경과 시간 입력] 몇 시간/분/초 후에 전원을 제어할지 지정하십시오.'}")
            self.lbl_field_1.configure(text="${isEn ? 'Hour' : '시 (H)'}")
            self.lbl_field_2.configure(text="${isEn ? 'Min' : '분 (M)'}")
            self.lbl_field_3.grid(row=0, column=2, padx=5)
            self.ent_s.grid(row=1, column=2, padx=5)
            self.btn_start.configure(text="${isEn ? '▶ Start Timer' : '▶ 타이머 시작'}")
        else:
            self.btn_type_timer.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            self.btn_type_schedule.configure(bg=ACCENT_BLUE, fg="white")
            self.lbl_input_guide.configure(text="${isEn ? '[Clock Schedule] Specify target hour and minute (24h format):' : '[특정 예약 시각 지정] 24시 형식으로 실행할 시와 분을 입력하십시오.'}")
            self.lbl_field_1.configure(text="${isEn ? 'Hour (0-23)' : '시 (0~23)'}")
            self.lbl_field_2.configure(text="${isEn ? 'Min (0-59)' : '분 (0~59)'}")
            self.lbl_field_3.grid_forget()
            self.ent_s.grid_forget()
            self.btn_start.configure(text="${isEn ? '▶ Schedule Clock' : '▶ 특정 시각 예약'}")

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
                    messagebox.showwarning("${isEn ? 'Error' : '오류'}", "${isEn ? 'Please set duration to at least 1 second.' : '시간을 1초 이상으로 입력하세요.'}")
                    return
                self.start_timer_with_seconds(total)
            else:
                if not (0 <= h <= 23) or not (0 <= m <= 59):
                    messagebox.showerror("${isEn ? 'Error' : '오류'}", "${isEn ? 'Hours must be 0-23 and minutes 0-59.' : '시는 0~23, 분은 0~59 사이로 입력하십시오.'}")
                    return
                now = datetime.datetime.now()
                target_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if target_time <= now:
                    target_time += datetime.timedelta(days=1)
                total_seconds = int((target_time - now).total_seconds())
                mode_txt = self.get_mode_label(self.mode)
                date_str = target_time.strftime("${isEn ? '%Y-%m-%d %H:%M' : '%m월 %d일 %H시 %M분'}")
                if messagebox.askyesno(
                    "${isEn ? 'Confirm Schedule' : '예약 확인'}",
                    "${isEn ? "f'Scheduled Time: {date_str}\\\\nTrigger [{mode_txt}] at this time?'" : "f'설정 시각: {date_str}\\\\n해당 시각에 [{mode_txt}] 작업을 시작하시겠습니까?'"}"
                ):
                    self.start_timer_with_seconds(total_seconds)
        except ValueError:
            messagebox.showerror("${isEn ? 'Error' : '오류'}", "${isEn ? 'Please enter valid numbers only.' : '유효한 정수 숫자만 입력할 수 있습니다.'}")

    def start_timer_with_seconds(self, seconds):
        self.remaining_seconds = seconds
        self.timer_running = True
        self.timer_paused = False
        self.btn_start.configure(text="${isEn ? '⏸ Pause' : '⏸ 일시정지'}", bg="#eab308")
        self.update_countdown()

    def reset_timer(self):
        self.timer_running = False
        self.timer_paused = False
        self.btn_start.configure(text="${isEn ? '▶ Start Timer' : '▶ 타이머 시작'}", bg=ACCENT_BLUE, state="normal")
        self.lbl_timer.configure(text="00:30:00", fg="#60a5fa")

    def toggle_pause(self):
        if not self.timer_running:
            return
        self.timer_paused = not self.timer_paused
        if self.timer_paused:
            self.btn_start.configure(text="${isEn ? '▶ Resume' : '▶ 다시 시작'}", bg=ACCENT_BLUE)
            self.lbl_timer.configure(fg="#eab308")
        else:
            self.btn_start.configure(text="${isEn ? '⏸ Pause' : '⏸ 일시정지'}", bg="#eab308")
            self.lbl_timer.configure(fg="#60a5fa")
            self.update_countdown()

    def update_countdown(self):
        if not self.timer_running or self.timer_paused:
            return
        if self.remaining_seconds > 0:
            h, rem = divmod(self.remaining_seconds, 3600)
            m, s = divmod(rem, 60)
            self.lbl_timer.configure(text=f"{h:02d}:{m:02d}:{s:02d}")
            self.remaining_seconds -= 1
            self.root.after(1000, self.update_countdown)
        else:
            self.lbl_timer.configure(text="00:00:00", fg=ACCENT_RED)
            self.execute_power_action()

    def on_close_button(self):
        """${isEn ? 'Hide to tray if pystray is available; otherwise prompt before closing.' : '트레이 모듈이 있으면 트레이로 숨기고, 없으면 종료 여부를 확인합니다.'}"""
        if P_TRAY_AVAILABLE:
            self.root.withdraw()
            self.start_tray_icon()
        else:
            if messagebox.askyesno(
                "${isEn ? 'Exit Confirmation' : '종료 확인'}",
                "${isEn ? 'System tray module (pystray) is unavailable. Exit app completely?' : '트레이 모듈(pystray)이 없습니다. 프로그램을 완전히 종료하시겠습니까?'}"
            ):
                self.quit_app_completely()

    def start_tray_icon(self):
        """${isEn ? 'Create an in-memory icon and register contextual tray menu actions.' : '메모리 내 아이콘 이미지를 생성하고 시스템 트레이 우클릭 메뉴를 등록합니다.'}"""
        if self.tray_icon is not None:
            return
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, 56, 56], fill=ACCENT_BLUE)
        draw.polygon([(32, 12), (44, 32), (32, 32), (32, 52), (20, 32), (32, 32)], fill="white")

        menu = pystray.Menu(
            pystray.MenuItem("${isEn ? 'Restore Window' : '창 열기 (복원)'}", self.restore_from_tray, default=True),
            pystray.MenuItem("${isEn ? 'Shutdown Now' : '즉시 종료 (Shutdown Now)'}", self.immediate_shutdown_from_tray),
            pystray.MenuItem("${isEn ? 'Restart Now' : '즉시 재시작 (Restart Now)'}", self.immediate_restart_from_tray),
            pystray.MenuItem("${isEn ? 'Exit Completely' : '완전 종료 (Exit)'}", self.quit_app_completely)
        )
        self.tray_icon = pystray.Icon(
            "${safeName}",
            image,
            "${isEn ? `${safeName} Active in Tray` : `${safeName} 트레이 대기 중`}",
            menu
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def immediate_shutdown_from_tray(self, icon=None, item=None):
        self.mode = "shutdown"
        self.root.after(0, self.execute_power_action)

    def immediate_restart_from_tray(self, icon=None, item=None):
        self.mode = "restart"
        self.root.after(0, self.execute_power_action)

    def restore_from_tray(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.after(0, self.root.deiconify)

    def quit_app_completely(self, icon=None, item=None):
        self.timer_running = False
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.quit()
        sys.exit(0)

    def check_startup_reg(self):
        """${isEn ? 'Inspect HKCU Run registry key to detect whether startup launch is enabled.' : 'Windows 레지스트리 Run 키를 조회하여 시작 프로그램 등록 여부를 확인합니다.'}"""
        if not WINDOWS_REG_AVAILABLE:
            return False
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "${safeName}")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False

    def toggle_startup(self):
        """${isEn ? 'Register or remove the executable in Windows CurrentVersion\\\\Run.' : 'Windows 시작 시 자동 실행 레지스트리 값을 등록하거나 해제합니다.'}"""
        if not WINDOWS_REG_AVAILABLE:
            messagebox.showerror("${isEn ? 'Unsupported OS' : '오류'}", "${isEn ? 'Windows startup registry is only supported on Windows.' : 'Windows 환경에서만 시작 프로그램 등록을 지원합니다.'}")
            self.auto_start.set(False)
            return

        exe_path = os.path.abspath(sys.argv[0])
        cmd_val = f'"{sys.executable}" "{exe_path}"' if exe_path.endswith(".py") else f'"{exe_path}"'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_WRITE)
            if self.auto_start.get():
                winreg.SetValueEx(key, "${safeName}", 0, winreg.REG_SZ, cmd_val)
                messagebox.showinfo("${isEn ? 'Startup Enabled' : '등록 완료'}", "${isEn ? 'Registered for automatic startup with Windows.' : 'Windows 시작 시 자동 실행되도록 등록되었습니다.'}")
            else:
                try:
                    winreg.DeleteValue(key, "${safeName}")
                    messagebox.showinfo("${isEn ? 'Startup Disabled' : '해제 완료'}", "${isEn ? 'Removed from Windows startup items.' : '시작 프로그램 자동 실행이 해제되었습니다.'}")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            messagebox.showerror("${isEn ? 'Registry Error' : '레지스트리 오류'}", f"${isEn ? 'Failed to update startup key' : '레지스트리 수정 실패'}: {e}")
            self.auto_start.set(not self.auto_start.get())

    def execute_power_action(self):
        """${isEn ? 'Execute the selected OS-level power command safely.' : '선택된 운영체제 전원 제어 명령(/f 강제 종료 포함)을 즉시 실행합니다.'}"""
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None

        if self.mode == "shutdown":
            os.system("shutdown /s /f /t 5")
        elif self.mode == "restart":
            os.system("shutdown /r /f /t 5")
        elif self.mode == "sleep":
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        elif self.mode == "screenoff":
            os.system('powershell (Add-Type \\'[DllImport("user32.dll")]public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);\\' -Name a -PassThru)::SendMessage(-1,0x0112,0xF170,2)')
        elif self.mode == "logout":
            os.system("shutdown /l /f")

        messagebox.showinfo(
            "${isEn ? 'Power Command Dispatched' : '전원 제어 실행'}",
            "${isEn ? 'System power command executed successfully.' : '시스템 전원 제어 명령이 정상적으로 실행되었습니다.'}"
        )
        self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = PowerTimerApp(root)
    root.mainloop()`;
}

/**
 * Generates an Inno Setup 6 (.iss) compiler script enforcing the exact setup sequence:
 * 1. Force-kill running app processes
 * 2. Detect existing installation and ask Uninstall (Clean) vs Overwrite
 * 3. License agreement declaration (wpLicense)
 * 4. Installation + formal Windows Add/Remove Programs registration
 * 5. Desktop shortcut checkbox on completion screen (wpFinished)
 * 6. Launch application checkbox (wpFinished)
 * All comments, [Setup] metadata, [Languages] ordering, and prompts are dynamically localized.
 */
export function generateInnoSetupScript(
  lang: AppLang,
  desktopName: string,
  appVersion: string
): string {
  const safeName = desktopName.replace(/[^a-zA-Z0-9_-]/g, '') || 'PowerController';
  const isEn = lang === 'en';

  const languagesBlock = isEn
    ? `Name: "english"; MessagesFile: "compiler:Default.isl"; LicenseFile: "docs\\LICENSE_en.txt"
Name: "korean"; MessagesFile: "compiler:Languages\\Korean.isl"; LicenseFile: "docs\\LICENSE_ko.txt"`
    : `Name: "korean"; MessagesFile: "compiler:Languages\\Korean.isl"; LicenseFile: "docs\\LICENSE_ko.txt"
Name: "english"; MessagesFile: "compiler:Default.isl"; LicenseFile: "docs\\LICENSE_en.txt"`;

  return `; ===============================================================================
; ${safeName} v${appVersion} — ${isEn ? 'Inno Setup 6 Compiler Script' : 'Inno Setup 6 설치 마법사 컴파일 스크립트'}
; ${isEn ? 'Flow: Kill Running App -> Uninstall/Overwrite Prompt -> License -> Install -> Desktop Shortcut Check -> Launch' : '진행 순서: 기존 앱 강제 종료 -> 설치됨 감지 시 삭제/덮어쓰기 질의 -> 라이선스 선언 -> 설치 -> 바탕화면 바로가기 체크 -> 앱 실행'}
; ${isEn ? 'Publisher: AhBiYout | Official Blog: https://ahbiyoutvibe.blogspot.com/' : '제작 및 배포: AhBiYout | 공식 블로그: https://ahbiyoutvibe.blogspot.com/'}
; ===============================================================================

#ifndef MyAppVersion
#define MyAppVersion "${appVersion}"
#endif

#define MyAppName "${safeName}"
#define MyAppPublisher "AhBiYout"
#define MyAppURL "https://ahbiyoutvibe.blogspot.com/"
#define MyAppExeName "${safeName}.exe"

[Setup]
; ${isEn ? 'Uniquely identifies this application in Windows Add/Remove Programs (Apps & Features)' : 'Windows 프로그램 추가/제거(설치된 앱) 목록에서 이 앱을 고유하게 식별하는 GUID'}
AppId={{5A8C9B23-7F12-4D39-8C92-E6B3C0F59871}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
LicenseFile=${isEn ? 'docs\\LICENSE_en.txt' : 'docs\\LICENSE_ko.txt'}
OutputDir=dist
OutputBaseFilename=${safeName}_Setup_v{#MyAppVersion}
SetupIconFile=${safeName}.ico
; ${isEn ? 'Formal Windows Add/Remove Programs registration directives' : 'Windows 프로그램 추가/제거 정식 등록 지시어'}
Uninstallable=yes
CreateUninstallRegKey=yes
UninstallDisplayName={#MyAppName} v{#MyAppVersion}
UninstallDisplayIcon={app}\\{#MyAppExeName}
UninstallFilesDir={app}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
LanguageDetectionMethod=uilanguage
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=force
RestartApplications=no
CloseApplicationsFilter=*.exe
ArchitecturesInstallIn64BitMode=x64compatible

; ===============================================================================
; ${isEn ? 'Windows File Properties (Details Tab) Version Metadata' : 'Windows 파일 속성 > 자세히 탭 버전 메타데이터 설정'}
; ===============================================================================
VersionInfoVersion={#MyAppVersion}.0
VersionInfoTextVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=${isEn ? `${safeName} - Smart System Power & Remote Shutdown Setup Wizard` : `${safeName} - 스마트 시스템 전원 제어 및 원격 종료 예약 설치 마법사`}
VersionInfoCopyright=Copyright (c) 2026 AhBiYout. All rights reserved.
VersionInfoProductName={#MyAppName} - Smart Shutdown Agent
VersionInfoProductVersion={#MyAppVersion}.0
VersionInfoProductTextVersion={#MyAppVersion}
VersionInfoOriginalFileName=${safeName}_Setup_v{#MyAppVersion}.exe

[Languages]
; ${isEn ? 'Primary language listed first determines the default wizard language' : '상단에 배치된 언어가 설치 마법사의 기본 언어로 우선 적용됩니다'}
${languagesBlock}

[CustomMessages]
; ${isEn ? 'Localized checkbox prompts for shortcuts, startup, and post-install launch' : '바탕화면 바로가기, 시작 프로그램 등록 및 앱 실행 옵션 다국어 메시지'}
english.CreateDesktopIcon=Create a &desktop shortcut
english.CreateStartupIcon=Register to start automatically with &Windows
english.LaunchProgram=Launch ${safeName} now
english.AdditionalTasksGroup=Additional tasks:
korean.CreateDesktopIcon=바탕 화면에 바로가기 아이콘 생성(&D)
korean.CreateStartupIcon=Windows 시작 시 자동 실행 등록(&S)
korean.LaunchProgram=${safeName} 지금 바로 실행하기(&R)
korean.AdditionalTasksGroup=추가 작업 선택:

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalTasksGroup}"
Name: "startupicon"; Description: "{cm:CreateStartupIcon}"; GroupDescription: "{cm:AdditionalTasksGroup}"; Flags: unchecked

[Files]
; ${isEn ? '1. Unpacked PyInstaller multi-file directory distribution (--onedir)' : '1. PyInstaller 폴더형 개별 파일 배포 트리 (--onedir 출력물)'}
Source: "dist\\${safeName}\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

; ${isEn ? '2. Standalone single-file binaries & enterprise network commander' : '2. 단독 실행 바이너리 및 사내 네트워크 통합 제어 타워'}
Source: "dist\\${safeName}.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\\PowerNetworkScheduler.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\\ApplySharedSchedules.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; ${isEn ? '3. Native C/C++ DLL engines, runtime scripts, icons, and EULA documents' : '3. 순수 창작 C/C++ 네이티브 DLL 엔진, 보조 스크립트, 아이콘 및 라이선스 문서'}
Source: "PowerCoreNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "NetBeaconEngine.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "FirewallNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "SysPowerHook.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "ScheduleCrypto.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "DiskFlushNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "AudioDimmerNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "DisplayDdcNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "LowLevelInputIdleNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "CommanderTcpDispatcherNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "CommanderPingScannerNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "PowerExecNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "native_bridge.py"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "${safeName}.ico"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "${safeName}.png"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "docs\\LICENSE_en.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "docs\\LICENSE_ko.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; ${isEn ? 'Start Menu, Desktop, and Windows Startup shortcuts' : '시작 메뉴, 바탕화면 및 Windows 시작프로그램 바로가기 생성'}
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; IconFilename: "{app}\\${safeName}.ico"
Name: "{group}\\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; IconFilename: "{app}\\${safeName}.ico"; Tasks: desktopicon
Name: "{autostartup}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Parameters: "--startup --tray"; Tasks: startupicon

[Run]
; ${isEn ? 'Silently pre-register Windows Defender Firewall rules for TCP 9988 & UDP 9985/9986' : '설치 중 Windows 방화벽 팝업 차단을 위해 TCP 9988 및 UDP 9985/9986 규칙을 무음 사전 등록'}
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""${safeName} (Inbound)"" dir=in action=allow program=""{app}\\{#MyAppExeName}"" enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""${safeName} (Outbound)"" dir=out action=allow program=""{app}\\{#MyAppExeName}"" enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""${safeName} TCP 9988"" dir=in action=allow protocol=TCP localport=9988 enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""${safeName} UDP 9986"" dir=in action=allow protocol=UDP localport=9986 enable=yes profile=any"; Flags: runhidden

; ${isEn ? 'Launch application checkbox on Finished page (postinstall)' : '설치 완료 화면에서 바로 앱 실행 체크박스 제공'}
Filename: "{app}\\{#MyAppExeName}"; Description: "{cm:LaunchProgram}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; ${isEn ? 'Cleanly remove registered firewall rules on uninstall' : '프로그램 제거 시 등록했던 방화벽 예외 규칙을 모두 깔끔하게 삭제'}
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""${safeName} (Inbound)"""; Flags: runhidden; RunOnceId: "DelFwRuleIn"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""${safeName} (Outbound)"""; Flags: runhidden; RunOnceId: "DelFwRuleOut"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""${safeName} TCP 9988"""; Flags: runhidden; RunOnceId: "DelFwRuleTCP"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""${safeName} UDP 9986"""; Flags: runhidden; RunOnceId: "DelFwRuleUDP"

[UninstallDelete]
Type: files; Name: "{autodesktop}\\{#MyAppName}.lnk"
Type: files; Name: "{userdesktop}\\{#MyAppName}.lnk"
Type: files; Name: "{app}\\*.log"
Type: files; Name: "{app}\\*.tmp"
Type: dirifempty; Name: "{app}"

[Code]
var
  CleanInstallSelected: Boolean;
  DesktopShortcutCheck: TNewCheckBox;
  FinishedLayoutAdjusted: Boolean;

// ${isEn ? '1. Force-terminate running processes before checking or overwriting' : '1단계: 기존 실행 중인 앱을 강제 종료하고 파일 잠금을 해제'}
procedure ForceKillProcess(const ExeName: String);
var
  ResultCode: Integer;
  BaseName: String;
begin
  BaseName := ChangeFileExt(ExeName, '');
  Exec(ExpandConstant('{cmd}'), '/c taskkill.exe /F /T /IM "' + ExeName + '" >nul 2>&1', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec('powershell.exe', '-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "Get-Process -Name ''' + BaseName + ''' -ErrorAction SilentlyContinue | Stop-Process -Force"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure KillAllPowerProcesses();
begin
  ForceKillProcess('{#MyAppExeName}');
  ForceKillProcess('PowerNetworkScheduler.exe');
  ForceKillProcess('ApplySharedSchedules.exe');
  Sleep(250);
end;

function QueryUninstallPath(const RootKey: Integer; const SubKey: String; var OutPath, OutUninst: String): Boolean;
begin
  Result := False;
  OutPath := '';
  OutUninst := '';
  if not RegKeyExists(RootKey, SubKey) then Exit;
  if not RegQueryStringValue(RootKey, SubKey, 'Inno Setup: App Path', OutPath) then
    RegQueryStringValue(RootKey, SubKey, 'InstallLocation', OutPath);
  if not RegQueryStringValue(RootKey, SubKey, 'QuietUninstallString', OutUninst) then
    RegQueryStringValue(RootKey, SubKey, 'UninstallString', OutUninst);
  if (OutPath = '') and (OutUninst <> '') then
    OutPath := ExtractFileDir(RemoveQuotes(OutUninst));
  Result := (OutPath <> '') or (OutUninst <> '');
end;

function GetExistingInstallInfo(var PrevPath, PrevUninst: String): Boolean;
var
  KeyGuid, KeyLegacy: String;
begin
  Result := False;
  PrevPath := '';
  PrevUninst := '';
  KeyGuid := 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{5A8C9B23-7F12-4D39-8C92-E6B3C0F59871}_is1';
  KeyLegacy := 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{#MyAppName}';

  if QueryUninstallPath(HKLM, KeyGuid, PrevPath, PrevUninst) or
     QueryUninstallPath(HKCU, KeyGuid, PrevPath, PrevUninst) or
     QueryUninstallPath(HKCU, KeyLegacy, PrevPath, PrevUninst) or
     QueryUninstallPath(HKLM, KeyLegacy, PrevPath, PrevUninst) then
  begin
    Result := True;
    Exit;
  end;
end;

// ${isEn ? '2. Prompt Uninstall (Clean) vs Overwrite when previous install is found' : '2단계: 기존 설치 감지 시 삭제 후 재설치 / 덮어쓰기 선택 질의 후 라이선스 단계로 진입'}
function InitializeSetup(): Boolean;
var
  PrevPath, PrevUninst, UninstExe, PromptMsg: String;
  UserChoice, ResultCode: Integer;
begin
  Result := True;
  CleanInstallSelected := False;
  FinishedLayoutAdjusted := False;
  KillAllPowerProcesses();

  if GetExistingInstallInfo(PrevPath, PrevUninst) then
  begin
    if not WizardSilent() then
    begin
      if ActiveLanguage = 'korean' then
        PromptMsg := '[기존 버전 설치 감지]' + #13#10#13#10 + '이미 설치된 {#MyAppName}가 감지되었습니다.' + #13#10 + '경로: ' + PrevPath + #13#10#13#10 + '• [예]: 기존 앱 삭제 후 새로 설치' + #13#10 + '• [아니오]: 기존 파일 위에 덮어쓰기 설치' + #13#10 + '• [취소]: 설치 중단'
      else
        PromptMsg := '[Existing Installation Detected]' + #13#10#13#10 + '{#MyAppName} is already installed at: ' + PrevPath + #13#10#13#10 + '- [Yes]: Uninstall existing version first (Clean Install)' + #13#10 + '- [No]: Overwrite / upgrade existing installation' + #13#10 + '- [Cancel]: Exit setup';

      UserChoice := MsgBox(PromptMsg, mbConfirmation, MB_YESNOCANCEL);
      if UserChoice = IDYES then CleanInstallSelected := True
      else if UserChoice = IDCANCEL then begin Result := False; Exit; end;
    end;

    if CleanInstallSelected then
    begin
      UninstExe := AddBackslash(PrevPath) + 'unins000.exe';
      if FileExists(UninstExe) then
      begin
        Exec(UninstExe, '/SILENT /VERYSILENT /SUPPRESSMSGBOXES /NORESTART', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        Sleep(800);
      end
      else if PrevUninst <> '' then
      begin
        Exec(ExpandConstant('{cmd}'), '/c ' + PrevUninst + ' --silent', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        Sleep(800);
      end;
    end;
  end;
end;

procedure InitializeWizard();
begin
  // ${isEn ? '5. Desktop shortcut checkbox rendered on Finished page right after installation' : '5단계: 설치 완료 화면(wpFinished)에 바탕화면 바로가기 체크박스 생성'}
  DesktopShortcutCheck := TNewCheckBox.Create(WizardForm);
  DesktopShortcutCheck.Parent := WizardForm.FinishedPage;
  DesktopShortcutCheck.Caption := ExpandConstant('{cm:CreateDesktopIcon}');
  DesktopShortcutCheck.Checked := True;
  DesktopShortcutCheck.Visible := False;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := (not WizardSilent()) and (PageID = wpSelectTasks);
end;

procedure CurPageChanged(CurPageID: Integer);
var
  OffsetY: Integer;
begin
  if (CurPageID = wpFinished) and (not WizardSilent()) and (DesktopShortcutCheck <> nil) then
  begin
    DesktopShortcutCheck.Left := WizardForm.RunList.Left;
    DesktopShortcutCheck.Width := WizardForm.RunList.Width;
    DesktopShortcutCheck.Height := ScaleY(20);
    if not FinishedLayoutAdjusted then
    begin
      FinishedLayoutAdjusted := True;
      DesktopShortcutCheck.Top := WizardForm.RunList.Top;
      OffsetY := ScaleY(24);
      if WizardForm.RunList.Visible then
      begin
        WizardForm.RunList.Top := WizardForm.RunList.Top + OffsetY;
        if WizardForm.RunList.Height > OffsetY + ScaleY(20) then
          WizardForm.RunList.Height := WizardForm.RunList.Height - OffsetY;
      end;
    end;
    DesktopShortcutCheck.Visible := True;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  DesktopLnk, UserDesktopLnk: String;
begin
  Result := True;
  if CurPageID = wpFinished then
  begin
    DesktopLnk := ExpandConstant('{autodesktop}\\{#MyAppName}.lnk');
    UserDesktopLnk := ExpandConstant('{userdesktop}\\{#MyAppName}.lnk');
    if (DesktopShortcutCheck <> nil) and (not DesktopShortcutCheck.Checked) then
    begin
      if FileExists(DesktopLnk) then DeleteFile(DesktopLnk);
      if FileExists(UserDesktopLnk) then DeleteFile(UserDesktopLnk);
    end
    else if (DesktopShortcutCheck <> nil) and DesktopShortcutCheck.Checked then
    begin
      if not FileExists(DesktopLnk) then
        CreateShellLink(DesktopLnk, '{#MyAppName}', ExpandConstant('{app}\\{#MyAppExeName}'), '', ExpandConstant('{app}'), ExpandConstant('{app}\\${safeName}.ico'), 0, SW_SHOWNORMAL);
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    KillAllPowerProcesses();
end;

function InitializeUninstall(): Boolean;
begin
  KillAllPowerProcesses();
  Result := True;
end;`;
}

