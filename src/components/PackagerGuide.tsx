import React, { useState } from 'react';
import { Archive, Copy, Check, Laptop, ShieldAlert, Sparkles } from 'lucide-react';
import { APP_VERSION } from '../types';

interface PackagerGuideProps {
  lang?: 'ko' | 'en';
}

export default function PackagerGuide({ lang = 'ko' }: PackagerGuideProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [desktopName, setDesktopName] = useState('PowerController');

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const pythonScriptCode = `import os
import sys
import json
import datetime
import threading
import tkinter as tk
from tkinter import messagebox

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

CONFIG_FILE = "power_timer_presets.json"
DARK_BG = "#111827"
DARK_CARD = "#1f2937"
TEXT_COLOR = "#f3f4f6"
ACCENT_BLUE = "#3b82f6"
ACCENT_RED = "#ef4444"

class PowerTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("전원 종료/재시작 타이머" if "${lang}" == "ko" else "Power Off/Reboot Timer")
        self.root.geometry("380x485")
        self.root.resizable(False, False)
        self.root.configure(bg=DARK_BG)
        
        self.always_on_top = tk.BooleanVar(value=True)
        self.root.attributes('-topmost', True)
        
        self.mode = "shutdown"
        self.run_type = "timer"
        self.remaining_seconds = 0
        self.timer_running = False
        self.timer_paused = False
        self.favorites = []
        self.tray_icon = None
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_button)
        self.load_favorites()
        self.auto_start = tk.BooleanVar(value=self.check_startup_reg())
        self.create_widgets()
        
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
        if "${lang}" == "en":
            self.favorites = [
                {"label": "Shutdown after watching movie (2h)", "mode": "shutdown", "seconds": 7200},
                {"label": "Lunch break quick reboot (1h)", "mode": "restart", "seconds": 3600},
                {"label": "Shutdown in 15 mins", "mode": "shutdown", "seconds": 900}
            ]
        else:
            self.favorites = [
                {"label": "영화 시청 후 종료 (2시간)", "mode": "shutdown", "seconds": 7200},
                {"label": "점심시간 빠른 재부팅 (1시간)", "mode": "restart", "seconds": 3600},
                {"label": "15분 집중 후 종료", "mode": "shutdown", "seconds": 900}
            ]
        self.save_favorites()
        
    def save_favorites(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, indent=4, ensure_ascii=False)
        except Exception as e:
            pass

    def create_widgets(self):
        header_frame = tk.Frame(self.root, bg=DARK_BG, pady=5)
        header_frame.pack(fill="x", padx=15)
        
        title_text = "⚡ SYSTEM POWER AGENT" if "${lang}" == "en" else "⚡ SYSTEM POWER AGENT (제작자: AhBiYout)"
        title_label = tk.Label(header_frame, text=title_text, font=("Arial", 11, "bold"), fg=TEXT_COLOR, bg=DARK_BG)
        title_label.pack(side="left")
        
        options_frame = tk.Frame(self.root, bg=DARK_BG)
        options_frame.pack(fill="x", padx=15, pady=(0, 5))
        
        pin_text = "📌 Always on Top" if "${lang}" == "en" else "📌 상단 고정"
        pin_btn = tk.Checkbutton(
            options_frame, 
            text=pin_text, 
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
        
        autostart_text = "⚙️ Auto Start with Windows" if "${lang}" == "en" else "⚙️ 시작 시 자동 실행"
        auto_start_btn = tk.Checkbutton(
            options_frame, 
            text=autostart_text, 
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
        
        mode_frame = tk.Frame(self.root, bg=DARK_BG, pady=5)
        mode_frame.pack(fill="x", padx=15)
        
        self.mode_buttons = {}
        if "${lang}" == "en":
            modes = [
                ("shutdown", "🔴 Shutdown"),
                ("restart", "🔵 Restart"),
                ("sleep", "🌙 Sleep"),
                ("screenoff", "💻 ScreenOff"),
                ("logout", "🚪 Logout")
            ]
        else:
            modes = [
                ("shutdown", "🔴 종료"),
                ("restart", "🔵 재시작"),
                ("sleep", "🌙 절전"),
                ("screenoff", "💻 화면끄기"),
                ("logout", "🚪 로그아웃")
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
        
        type_frame = tk.Frame(self.root, bg=DARK_BG, pady=5)
        type_frame.pack(fill="x", padx=15)
        
        timer_text = "⏳ Duration Timer" if "${lang}" == "en" else "⏳ 시간 타이머 (후)"
        self.btn_type_timer = tk.Button(
            type_frame,
            text=timer_text,
            font=("Arial", 9, "bold"),
            bg="#3b82f6",
            fg="white",
            relief="flat",
            pady=4,
            command=lambda: self.set_run_type("timer")
        )
        self.btn_type_timer.pack(side="left", expand=True, fill="x", padx=5)
        
        schedule_text = "⏰ Schedule Clock" if "${lang}" == "en" else "⏰ 특정 시각 예약 (정시)"
        self.btn_type_schedule = tk.Button(
            type_frame,
            text=schedule_text,
            font=("Arial", 9, "bold"),
            bg=DARK_CARD,
            fg=TEXT_COLOR,
            relief="flat",
            pady=4,
            command=lambda: self.set_run_type("schedule")
        )
        self.btn_type_schedule.pack(side="left", expand=True, fill="x", padx=5)
        
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
        
        self.input_parent_frame = tk.Frame(self.root, bg=DARK_BG)
        self.input_parent_frame.pack(fill="x", padx=20)
        
        guide_text = "[Duration Input] Key in the hours/minutes/seconds after which to trigger." if "${lang}" == "en" else "[경과 시간 입력] 몇 시간/분/초 후에 전원을 제어할지 지정하십시오."
        self.lbl_input_guide = tk.Label(
            self.input_parent_frame, 
            text=guide_text, 
            font=("Arial", 8, "bold"), 
            fg="#9ca3af", 
            bg=DARK_BG,
            anchor="w"
        )
        self.lbl_input_guide.pack(fill="x", pady=2)

        self.input_fields_frame = tk.Frame(self.input_parent_frame, bg=DARK_BG)
        self.input_fields_frame.pack(pady=5)
        
        h_lbl = "H" if "${lang}" == "en" else "시"
        self.lbl_field_1 = tk.Label(self.input_fields_frame, text=h_lbl, font=("Arial", 8), fg="#9ca3af", bg=DARK_BG)
        self.lbl_field_1.grid(row=0, column=0, padx=5)
        
        m_lbl = "M" if "${lang}" == "en" else "분"
        self.lbl_field_2 = tk.Label(self.input_fields_frame, text=m_lbl, font=("Arial", 8), fg="#9ca3af", bg=DARK_BG)
        self.lbl_field_2.grid(row=0, column=1, padx=5)
        
        s_lbl = "S" if "${lang}" == "en" else "초"
        self.lbl_field_3 = tk.Label(self.input_fields_frame, text=s_lbl, font=("Arial", 8), fg="#9ca3af", bg=DARK_BG)
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
        
        ctrl_frame = tk.Frame(self.root, bg=DARK_BG, pady=10)
        ctrl_frame.pack(fill="x", padx=20)
        
        start_btn_text = "▶ Start Timer" if "${lang}" == "en" else "▶ 타이머 시작"
        self.btn_start = tk.Button(
            ctrl_frame, 
            text=start_btn_text, 
            font=("Arial", 10, "bold"),
            bg=ACCENT_BLUE, 
            fg="white", 
            relief="flat",
            command=self.start_timer
        )
        self.btn_start.pack(side="left", expand=True, fill="x", padx=2)
        
        reset_btn_text = "🔄 Reset" if "${lang}" == "en" else "🔄 리셋"
        self.btn_reset = tk.Button(
            ctrl_frame, 
            text=reset_btn_text, 
            font=("Arial", 10, "bold"),
            bg="#374151", 
            fg=TEXT_COLOR, 
            relief="flat",
            command=self.reset_timer
        )
        self.btn_reset.pack(side="left", expand=True, fill="x", padx=2)
        
        credit_text = "Designed by AhBiYout" if "${lang}" == "en" else "제작자 : AhBiYout"
        credit_label = tk.Label(self.root, text=credit_text, font=("Arial", 8), fg="#6b7280", bg=DARK_BG)
        credit_label.pack(side="bottom", pady=5)

    def bind_spin_interactions(self, entry, field_type):
        entry.bind("<MouseWheel>", lambda event: self.handle_spin(event, entry, field_type, "wheel"))
        entry.bind("<Button-4>", lambda event: self.handle_spin(event, entry, field_type, "up"))
        entry.bind("<Button-5>", lambda event: self.handle_spin(event, entry, field_type, "down"))
        entry.bind("<Up>", lambda event: self.handle_spin(event, entry, field_type, "up"))
        entry.bind("<Down>", lambda event: self.handle_spin(event, entry, field_type, "down"))

    def handle_spin(self, event, entry, field_type, direction):
        if self.timer_running:
            return "break"

        if direction == "wheel":
            delta = 1 if event.delta > 0 else -1
        elif direction == "up":
            delta = 1
        else:
            delta = -1

        try:
            val = int(entry.get() or 0)
        except ValueError:
            val = 0

        if field_type == "h":
            if self.run_type == "schedule":
                min_val, max_val, wrap = 0, 23, True
            else:
                min_val, max_val, wrap = 0, 999, False
        elif field_type == "m":
            min_val, max_val, wrap = 0, 59, True
        else:
            min_val, max_val, wrap = 0, 59, True

        new_val = val + delta

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

        entry.delete(0, tk.END)
        entry.insert(0, str(new_val))
        return "break"

    def toggle_always_on_top(self):
        self.root.attributes('-topmost', self.always_on_top.get())
        
    def get_mode_label(self, mode):
        if "${lang}" == "en":
            labels = {"shutdown": "Shutdown", "restart": "Reboot", "sleep": "Sleep", "screenoff": "ScreenOff", "logout": "Logout"}
        else:
            labels = {"shutdown": "종료", "restart": "재시작", "sleep": "절전", "screenoff": "화면끄기", "logout": "로그아웃"}
        return labels.get(mode, "Power Action")

    def set_mode(self, mode):
        self.mode = mode
        for m_id, btn in self.mode_buttons.items():
            if m_id == mode:
                color = ACCENT_RED if mode == "shutdown" else ACCENT_BLUE
                btn.configure(bg=color, fg="white")
            else:
                btn.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            
    def set_run_type(self, run_type):
        if self.timer_running:
            err_title = "Warning" if "${lang}" == "en" else "오류"
            err_msg = "Please stop or reset the running timer first." if "${lang}" == "en" else "예약이 이미 가동 중일 때는 변경할 수 없습니다. 리셋 후 변경하십시오."
            messagebox.showwarning(err_title, err_msg)
            return
            
        self.run_type = run_type
        if run_type == "timer":
            self.btn_type_timer.configure(bg="#3b82f6", fg="white")
            self.btn_type_schedule.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            
            guide_txt = "[Duration Input] Key in the hours/minutes/seconds after which to trigger." if "${lang}" == "en" else "[경과 시간 입력] 몇 시간/분/초 후에 전원을 제어할지 지정하십시오."
            self.lbl_input_guide.configure(text=guide_txt)
            self.lbl_field_1.configure(text="H" if "${lang}" == "en" else "시")
            self.lbl_field_2.configure(text="M" if "${lang}" == "en" else "분")
            self.lbl_field_3.grid(row=0, column=2, padx=5)
            self.ent_s.grid(row=1, column=2, padx=5)
            
            p_text = "⏸ Pause" if "${lang}" == "en" else "⏸ 일시정지"
            r_text = "▶ Resume" if "${lang}" == "en" else "▶ 다시 시작"
            s_text = "▶ Start Timer" if "${lang}" == "en" else "▶ 타이머 시작"
            self.btn_start.configure(text=s_text if not self.timer_running else (r_text if self.timer_paused else p_text))
            
            self.ent_h.delete(0, tk.END)
            self.ent_h.insert(0, "0")
            self.ent_m.delete(0, tk.END)
            self.ent_m.insert(0, "30")
            self.ent_s.delete(0, tk.END)
            self.ent_s.insert(0, "0")
        else:
            self.btn_type_timer.configure(bg=DARK_CARD, fg=TEXT_COLOR)
            self.btn_type_schedule.configure(bg="#3b82f6", fg="white")
            
            guide_txt = "[Schedule Input] Specify absolute hour and minute (24h format)." if "${lang}" == "en" else "[특정 예약 시각 지정] 오늘/내일 몇 시 몇 분에 실행할지 24시 형식으로 입력하십시오."
            self.lbl_input_guide.configure(text=guide_txt)
            self.lbl_field_1.configure(text="Hour(0-23)" if "${lang}" == "en" else "실행 시(0~23)")
            self.lbl_field_2.configure(text="Minute(0-59)" if "${lang}" == "en" else "실행 분(0~59)")
            self.lbl_field_3.grid_forget()
            self.ent_s.grid_forget()
            
            p_text = "⏸ Pause" if "${lang}" == "en" else "⏸ 일시정지"
            r_text = "▶ Resume" if "${lang}" == "en" else "▶ 다시 시작"
            s_text = "▶ Schedule Timer" if "${lang}" == "en" else "▶ 특정 시각 예약 가동"
            self.btn_start.configure(text=s_text if not self.timer_running else (r_text if self.timer_paused else p_text))
            
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
                mins_lbl = " mins" if "${lang}" == "en" else "분"
                self.fav_listbox.insert(tk.END, f" {idx+1}. [{mode_lbl}] {item['label']} ({duration_minutes}{mins_lbl})")
            
    def on_fav_double_click(self, event):
        if hasattr(self, 'fav_listbox'):
            selection = self.fav_listbox.curselection()
            if selection:
                self.set_run_type("timer")
                idx = selection[0]
                fav = self.favorites[idx]
                self.set_mode(fav["mode"])
                self.start_timer_with_seconds(fav["seconds"])
            
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
                    err_title = "Error" if "${lang}" == "en" else "오류"
                    err_msg = "Please set duration to 1 second or more." if "${lang}" == "en" else "시간을 1초 이상으로 입력하세요."
                    messagebox.showwarning(err_title, err_msg)
                    return
                self.start_timer_with_seconds(total)
            else:
                if not (0 <= h <= 23) or not (0 <= m <= 59):
                    err_title = "Error" if "${lang}" == "en" else "오류"
                    err_msg = "Hours must be 0-23, and minutes must be 0-59." if "${lang}" == "en" else "시는 0~23 사이, 분은 0~59 사이로 입력하여 주십시오."
                    messagebox.showerror(err_title, err_msg)
                    return
                
                now = datetime.datetime.now()
                target_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                
                if target_time <= now:
                    target_time += datetime.timedelta(days=1)
                
                total_seconds = int((target_time - now).total_seconds())
                
                mode_txt = self.get_mode_label(self.mode)
                date_str = target_time.strftime("%m-%d %H:%M" if "${lang}" == "en" else "%m월 %d일 %H시 %M분")
                
                confirm_title = "Confirm Schedule" if "${lang}" == "en" else "예약 확인"
                confirm_msg = f"Target Time: {date_str}\\nYour PC will trigger [{mode_txt}] at this time. Proceed?" if "${lang}" == "en" else f"설정 시각: {date_str}\\n해당 시간 정각에 컴퓨터 [{mode_txt}] 예약이 진행됩니다. 시작하시겠습니까?"
                
                ans = messagebox.askyesno(confirm_title, confirm_msg)
                if not ans:
                    return
                    
                self.start_timer_with_seconds(total_seconds)
        except ValueError:
            err_title = "Error" if "${lang}" == "en" else "오류"
            err_msg = "Please enter integers only." if "${lang}" == "en" else "숫자만 입력할 수 있습니다."
            messagebox.showerror(err_title, err_msg)

    def start_timer_with_seconds(self, seconds):
        self.remaining_seconds = seconds
        self.timer_running = True
        self.timer_paused = False
        pause_lbl = "⏸ Pause" if "${lang}" == "en" else "⏸ 일시정지"
        self.btn_start.configure(text=pause_lbl, bg="#eab308")
        self.update_countdown()
        
    def reset_timer(self):
        self.timer_running = False
        self.timer_paused = False
        default_text = ("▶ Start Timer" if "${lang}" == "en" else "▶ 타이머 시작") if self.run_type == "timer" else ("▶ Schedule Clock" if "${lang}" == "en" else "▶ 특정 시각 예약 가동")
        self.btn_start.configure(text=default_text, bg=ACCENT_BLUE, state="normal")
        self.lbl_timer.configure(text="00:30:00" if self.run_type == "timer" else "00:00:00", fg="#60a5fa")
        
    def toggle_pause(self):
        if not self.timer_running:
            return
            
        self.timer_paused = not self.timer_paused
        if self.timer_paused:
            resume_text = "▶ Resume" if "${lang}" == "en" else "▶ 다시 시작"
            self.btn_start.configure(text=resume_text, bg=ACCENT_BLUE)
            self.lbl_timer.configure(fg="#eab308")
        else:
            pause_lbl = "⏸ Pause" if "${lang}" == "en" else "⏸ 일시정지"
            self.btn_start.configure(text=pause_lbl, bg="#eab308")
            self.lbl_timer.configure(fg="#60a5fa")
            self.update_countdown()
            
    def update_countdown(self):
        if not self.timer_running or self.timer_paused:
            return
            
        if self.remaining_seconds > 0:
            h = self.remaining_seconds // 3600
            m = (self.remaining_seconds % 3600) // 60
            s = self.remaining_seconds % 60
            time_str = f"{h:02d}:{m:02d}:{s:02d}"
            
            self.lbl_timer.configure(text=time_str)
            self.remaining_seconds -= 1
            self.root.after(1000, self.update_countdown)
        else:
            self.lbl_timer.configure(text="00:00:00", fg=ACCENT_RED)
            self.open_grace_popup()

    def open_grace_popup(self):
        if self.root.state() == "withdrawn":
            self.restore_from_tray()
            
        self.grace_win = tk.Toplevel(self.root)
        warn_title = "⚠️ Power Management Alert" if "${lang}" == "en" else "⚠️ 시스템 전원 제어 경고"
        self.grace_win.title(warn_title)
        self.grace_win.geometry("450x260")
        self.grace_win.configure(bg="#ef4444" if self.mode == "shutdown" else "#3b82f6")
        self.grace_win.resizable(False, False)
        
        self.grace_win.update_idletasks()
        width = 450
        height = 260
        x = (self.grace_win.winfo_screenwidth() // 2) - (width // 2)
        y = (self.grace_win.winfo_screenheight() // 2) - (height // 2)
        self.grace_win.geometry(f"{width}x{height}+{x}+{y}")
        
        self.grace_win.attributes("-topmost", True)
        self.grace_win.grab_set()
        
        self.grace_win.protocol("WM_DELETE_WINDOW", self.cancel_grace_popup)
        
        mode_txt = self.get_mode_label(self.mode)
        
        info_frame = tk.Frame(self.grace_win, bg=DARK_BG, bd=2, relief="solid")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        caption_text = f"⚠️ PC will [{mode_txt}] shortly!" if "${lang}" == "en" else f"⚠️ 잠시 후 컴퓨터가 [{mode_txt}]됩니다!"
        lbl_info = tk.Label(
            info_frame, 
            text=caption_text, 
            font=("Arial", 16, "bold"), 
            fg="#ef4444" if self.mode == "shutdown" else "#60a5fa", 
            bg=DARK_BG,
            pady=15
        )
        lbl_info.pack()
        
        self.grace_seconds = 10
        btn_caption_s = "seconds" if "${lang}" == "en" else "초 후 실행"
        self.lbl_grace_timer = tk.Label(
            info_frame, 
            text=f"{self.grace_seconds} {btn_caption_s}", 
            font=("Courier", 28, "bold"), 
            fg=TEXT_COLOR, 
            bg=DARK_BG
        )
        self.lbl_grace_timer.pack(pady=10)
        
        cancel_caption = "❌ Abort Power Schedule" if "${lang}" == "en" else "❌ 전원 예약 종료 [취소하기]"
        btn_cancel = tk.Button(
            info_frame, 
            text=cancel_caption, 
            font=("Arial", 12, "bold"), 
            bg="#374151", 
            fg="white", 
            relief="flat", 
            padx=20, 
            pady=10, 
            command=self.cancel_grace_popup
        )
        btn_cancel.pack(pady=15)
        
        self.update_grace_countdown()

    def update_grace_countdown(self):
        if not hasattr(self, "grace_win") or not self.grace_win.winfo_exists():
            return
            
        if self.grace_seconds > 0:
            btn_caption_s = "seconds remaining" if "${lang}" == "en" else "초 후 실행"
            self.lbl_grace_timer.configure(text=f"{self.grace_seconds} {btn_caption_s}")
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
        info_title = "Aborted" if "${lang}" == "en" else "취소 완료"
        info_msg = "Power scheduler aborted successfully." if "${lang}" == "en" else "전원 예약 제어가 안전하게 취소되었습니다."
        messagebox.showinfo(info_title, info_msg)

    def on_close_button(self):
        if P_TRAY_AVAILABLE:
            self.root.withdraw()
            self.start_tray_icon()
        else:
            ans_title = "Alert" if "${lang}" == "en" else "알림"
            ans_msg = "Tray module (pystray) is missing. Exit application completely?" if "${lang}" == "en" else "트레이 모듈(pystray)이 설치되지 않았습니다. 실시간 감시 대신 프로그램을 즉시 종료하시겠습니까?"
            ans = messagebox.askyesno(ans_title, ans_msg)
            if ans:
                self.quit_app_completely()

    def start_tray_icon(self):
        if self.tray_icon is not None:
            return
            
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, 56, 56], fill="#3b82f6")
        draw.polygon([(32, 12), (44, 32), (32, 32), (32, 52), (20, 32), (32, 32)], fill="white")
        
        t_open = "Restore" if "${lang}" == "en" else "열기 (Restore)"
        t_quick_s = "Quick Shutdown" if "${lang}" == "en" else "⏳ 빠른 종료 타이머 (Quick Shutdown)"
        t_sec_5 = "5 Seconds" if "${lang}" == "en" else "5초 (5 Seconds)"
        t_sec_30 = "30 Seconds" if "${lang}" == "en" else "30초 (30 Seconds)"
        t_min_1 = "1 Minute" if "${lang}" == "en" else "1분 (1 Minute)"
        t_min_30 = "30 Minutes" if "${lang}" == "en" else "30분 (30 Minutes)"
        t_hour_1 = "1 Hour" if "${lang}" == "en" else "1시간 (1 Hour)"
        t_quick_r = "Quick Restart" if "${lang}" == "en" else "🔄 빠른 재시작 타이머 (Quick Restart)"
        t_act_res = "Resume" if "${lang}" == "en" else "▶ 타이머 다시 시작 (Resume)"
        t_act_pau = "Pause" if "${lang}" == "en" else "⏸ 타이머 일시정지 (Pause)"
        t_act_cancel = "Cancel Timer" if "${lang}" == "en" else "타이머 취소 (Cancel Timer)"
        t_act_s_now = "Shutdown Now" if "${lang}" == "en" else "즉시 컴퓨터 종료 (Shutdown Now)"
        t_act_r_now = "Restart Now" if "${lang}" == "en" else "즉시 컴퓨터 재시작 (Restart Now)"
        t_act_exit = "Exit" if "${lang}" == "en" else "완전 종료 (Exit)"

        menu = pystray.Menu(
            pystray.MenuItem(t_open, self.restore_from_tray, default=True),
            pystray.MenuItem(t_quick_s, pystray.Menu(
                pystray.MenuItem(t_sec_5, lambda: self.quick_timer_from_tray(5, "shutdown")),
                pystray.MenuItem(t_sec_30, lambda: self.quick_timer_from_tray(30, "shutdown")),
                pystray.MenuItem(t_min_1, lambda: self.quick_timer_from_tray(60, "shutdown")),
                pystray.MenuItem(t_min_30, lambda: self.quick_timer_from_tray(1800, "shutdown")),
                pystray.MenuItem(t_hour_1, lambda: self.quick_timer_from_tray(3600, "shutdown"))
            )),
            pystray.MenuItem(t_quick_r, pystray.Menu(
                pystray.MenuItem(t_sec_5, lambda: self.quick_timer_from_tray(5, "restart")),
                pystray.MenuItem(t_sec_30, lambda: self.quick_timer_from_tray(30, "restart")),
                pystray.MenuItem(t_min_1, lambda: self.quick_timer_from_tray(60, "restart")),
                pystray.MenuItem(t_min_30, lambda: self.quick_timer_from_tray(1800, "restart")),
                pystray.MenuItem(t_hour_1, lambda: self.quick_timer_from_tray(3600, "restart"))
            )),
            pystray.MenuItem(lambda item: t_act_res if self.timer_paused else t_act_pau, self.toggle_pause_from_tray, enabled=lambda item: self.timer_running),
            pystray.MenuItem(t_act_cancel, self.reset_timer_from_tray),
            pystray.MenuItem(t_act_s_now, self.immediate_shutdown_from_tray),
            pystray.MenuItem(t_act_r_now, self.immediate_restart_from_tray),
            pystray.MenuItem(t_act_exit, self.quit_app_completely)
        )
        
        self.tray_icon = pystray.Icon("PowerController", image, "Power Controller Active" if "${lang}" == "en" else "전원 제어 전송 대기 중...", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def quick_timer_from_tray(self, seconds, mode):
        def action():
            self.timer_running = False
            self.set_mode(mode)
            self.set_run_type("timer")
            self.start_timer_with_seconds(seconds)
        self.root.after(0, action)

    def toggle_pause_from_tray(self, icon=None, item=None):
        self.root.after(0, self.toggle_pause)

    def reset_timer_from_tray(self, icon=None, item=None):
        self.root.after(0, self.reset_timer)

    def immediate_shutdown_from_tray(self, icon=None, item=None):
        def action():
            ans_title = "Instant Shutdown" if "${lang}" == "en" else "즉시 종료"
            ans_msg = "Shut down PC immediately?" if "${lang}" == "en" else "컴퓨터를 지금 즉시 종료하시겠습니까?"
            ans = messagebox.askyesno(ans_title, ans_msg)
            if ans:
                self.mode = "shutdown"
                self.execute_power_action()
        self.root.after(0, action)

    def immediate_restart_from_tray(self, icon=None, item=None):
        def action():
            ans_title = "Instant Reboot" if "${lang}" == "en" else "즉시 재시작"
            ans_msg = "Reboot PC immediately?" if "${lang}" == "en" else "컴퓨터를 지금 즉시 재시작하시겠습니까?"
            ans = messagebox.askyesno(ans_title, ans_msg)
            if ans:
                self.mode = "restart"
                self.execute_power_action()
        self.root.after(0, action)

    def restore_from_tray(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        
        self.root.after(0, self.root.deiconify)
        self.root.after(10, lambda: self.root.attributes("-topmost", self.always_on_top.get()))

    def quit_app_completely(self, icon=None, item=None):
        self.timer_running = False
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.quit()
        sys.exit(0)
            
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
                value, _ = winreg.QueryValueEx(key, "PowerController")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False

    def toggle_startup(self):
        if not WINDOWS_REG_AVAILABLE:
            err_title = "Error" if "${lang}" == "en" else "오류"
            err_msg = "Auto-launch settings can only be used on Windows OS." if "${lang}" == "en" else "윈도우 환경에서만 자동 실행 설정을 조정할 수 있습니다."
            messagebox.showerror(err_title, err_msg)
            self.auto_start.set(False)
            return

        exe_path = os.path.abspath(sys.argv[0])
        if exe_path.endswith(".py"):
            exe_path = f'"{sys.executable}" "{exe_path}"'
        else:
            exe_path = f'"{exe_path}"'

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE
            )
            reg_title = "Registry Update" if "${lang}" == "en" else "알림"
            if self.auto_start.get():
                winreg.SetValueEx(key, "PowerController", 0, winreg.REG_SZ, exe_path)
                reg_msg = "Successfully registered to launch automatically on Windows startup." if "${lang}" == "en" else "윈도우 시작 시 자동으로 실행되도록 등록되었습니다."
                messagebox.showinfo(reg_title, reg_msg)
            else:
                try:
                    winreg.DeleteValue(key, "PowerController")
                    reg_msg = "Windows start auto-launch disabled successfully." if "${lang}" == "en" else "자동 실행 등록이 해제되었습니다."
                    messagebox.showinfo(reg_title, reg_msg)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            err_title = "Error" if "${lang}" == "en" else "오류"
            err_msg = f"Failed to modify registry value: {e}" if "${lang}" == "en" else f"레지스트리 등록 중 오류가 발생했습니다: {e}"
            messagebox.showerror(err_title, err_msg)
            self.auto_start.set(not self.auto_start.get())

    def execute_power_action(self):
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
            os.system("powershell (Add-Type '[DllImport(\"user32.dll\")]^public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);' -Name a -PassThru)::SendMessage(-1,0x0112,0xF170,2)")
        elif self.mode == "logout":
            os.system("shutdown /l /f")
            
        sys_title = "Power Controller Trigger" if "${lang}" == "en" else "전원 제어 서브시스템"
        sys_msg = "Actions executed. System will perform control sequence." if "${lang}" == "en" else "잠시 후 시스템이 실제로 제어를 개시합니다."
        messagebox.showinfo(sys_title, sys_msg)
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = PowerTimerApp(root)
    root.mainloop()`;

  const pyInstallerCommand = `pip install pyinstaller pystray pillow
python -m PyInstaller --onefile --noconsole --name="${desktopName}" main.py`;

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-850 bg-white/40 dark:bg-gray-900/40 p-4 space-y-4 text-left select-none">
      <div className="flex items-center gap-2 pb-1.5 border-b border-gray-200/50 dark:border-gray-800">
        <Archive className="w-4.5 h-4.5 text-blue-500" />
        <h3 className="font-display font-semibold text-sm text-gray-800 dark:text-gray-100">
          {lang === 'en' 
            ? '🐍 Python Native Packager Suite (.exe portable binary)' 
            : '🐍 파이썬(Python) 기반 단일 실행 파일(.exe) 변환 스위트'}
        </h3>
      </div>

      <div className="space-y-4">
        {/* Dynamic naming for customized installers */}
        <div className="p-3 bg-blue-100/10 border border-blue-500/15 rounded-lg flex items-center justify-between gap-3 flex-wrap">
          <div className="space-y-0.5">
            <span className="text-[10px] uppercase font-bold text-blue-400">
              {lang === 'en' ? 'Target Application Name' : '빌드할 프로그램 이름 설정'}
            </span>
            <input
              type="text"
              id="input-desktop-name"
              value={desktopName}
              onChange={(e) => setDesktopName(e.target.value.replace(/[^a-zA-Z]/g, '') || 'PowerController')}
              className="text-xs bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-855 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-800 dark:text-gray-200"
              placeholder={lang === 'en' ? 'e.g. PowerController' : '예: PowerController'}
            />
          </div>
          <Laptop className="w-8 h-8 text-blue-500/30 flex-shrink-0" />
        </div>

        {/* Informational Warning */}
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 flex gap-2.5">
          <ShieldAlert className="w-4.5 h-4.5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="text-[11px] text-amber-600 dark:text-amber-400 leading-normal">
            <strong>{lang === 'en' ? 'Why Python is safe, lightweight, and superior:' : '왜 파이썬(Python)이 가장 안전하며 가벼울까요?'}</strong>
            <br />
            {lang === 'en' 
              ? 'Traditional solutions like NodeJS Electron pack massive Chromium rendering engines, exceeding 130MB in raw package size. Tkinter based Python processes build elegant 8MB bundles, executing native OS power signals instantaneously.'
              : 'NodeJS 일렉트론(Electron)은 자체 Chromium 브라우저 엔진을 고스란히 끌어안기 때문에 파일 크기가 대략 130MB를 상회하며 저사양 PC에서 구동 지연이 있을 수 있습니다. 반면, Tkinter 라이브러리 기반 파이썬 코드는 단 8MB 내외 크기로 완벽하게 단축 빌드되며 윈도우 OS 시스템 권한 종료 명령을 지연시간 없이 신속하게 실행합니다.'}
          </div>
        </div>

        {/* New Windows Auto Builder Notice */}
        <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 space-y-2">
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <h4 className="text-[11.5px] font-bold text-emerald-600 dark:text-emerald-400 font-sans">
              {lang === 'en' 
                ? '🚀 Dynamic One-Click Portable Compiler Bundle Attached!' 
                : '🚀 윈도우 원클릭 자동 무설치/인스톨 빌더 탑재! (자동 실행 및 마법사 추가)'}
            </h4>
          </div>
          <p className="text-[10.5px] text-gray-500 dark:text-gray-400 leading-relaxed font-sans">
            {lang === 'en'
              ? 'Compile, package start triggers, portable editions, and standard desktop installer setup chains automatically! Export the project via top-right [Settings] > [Export as ZIP] and execute the preconfigured "build.bat" script!'
              : '마우스 더블클릭 한 번으로 시작 프로그램 등록, 무설치 에디션, 그리고 깔끔한 GUI 방식의 설치 디렉토리 설정 및 바탕화면 단축키 마법사(Installer Edition)까지 일괄 컴파일합니다. 프로젝트를 우측 상단 [설정] > [Export as ZIP]으로 다운로드 하시면 자동 컴파일러 스크립트 build.bat가 함께 제공됩니다.'}
          </p>
          <div className="bg-gray-100 dark:bg-gray-950 p-2.5 rounded border border-gray-200 dark:border-gray-900 flex flex-col gap-1 text-[10px] font-mono text-gray-400">
            {lang === 'en' ? (
              <>
                <div>1. Download zip file and extract to your desired drive.</div>
                <div>2. Double click <span className="text-emerald-400 font-bold">build.bat</span> to start compiler.</div>
                <div>3. The automated chain installs required components and finishes building.</div>
                <div>4. Choose either <code>{desktopName}.exe</code> (portable) or <code>{desktopName}_Setup.exe</code> (installer wizard) under <code>dist\</code> directory.</div>
              </>
            ) : (
              <>
                <div>1. 프로젝트 ZIP 다운로드 후 임의의 디렉토리에 압축 해제</div>
                <div>2. 폴더 내 <span className="text-emerald-400 font-bold">"build.bat"</span> 파일을 더블클릭하여 자동 컴파일 시작</div>
                <div>3. 무설치 빌드 및 원클릭 마법사 빌드가 일련의 체인으로 연속 가동</div>
                <div>4. 최후 산출물 디렉토리 <code>dist\</code> 내의 <code>{desktopName}.exe</code> (무설치 포터블) 또는 <code>{desktopName}_Setup.exe</code> (설치 프로그램)를 골라 실행 가능합니다.</div>
              </>
            )}
          </div>
        </div>

        {/* Multi-Platform (PC, Android APK, iPhone iOS) Release Center */}
        <div className="p-3.5 rounded-lg bg-blue-500/10 border border-blue-500/20 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-[12px] font-bold text-blue-600 dark:text-blue-400 flex items-center gap-1.5 font-sans">
              <span>🚀</span>
              {lang === 'en' ? 'Multi-Platform Distribution (PC, Android APK, iPhone iOS)' : '멀티 플랫폼 설치 지원 센터 (PC, 모바일 Android APK, 아이폰 iOS)'}
            </h4>
            <a
              href="https://github.com/AhBiYout/PowerController/releases"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-600 text-white hover:bg-blue-500 transition-colors"
            >
              GitHub Releases
            </a>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 text-[10.5px]">
            {/* PC */}
            <div className="p-2.5 rounded bg-gray-100 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 space-y-1">
              <div className="font-bold text-gray-900 dark:text-gray-100 flex items-center gap-1">
                <span>💻</span> PC (Windows)
              </div>
              <p className="text-gray-500 dark:text-gray-400 text-[10px]">
                {lang === 'en' ? 'Inno Setup Installer (.exe) & Portable Edition' : '원클릭 설치 마법사(.exe) 및 무설치 포터블 에디션'}
              </p>
              <div className="font-mono text-[9px] text-emerald-500 font-semibold">
                build.bat (Inno Setup)
              </div>
            </div>
            {/* Android */}
            <div className="p-2.5 rounded bg-gray-100 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 space-y-1">
              <div className="font-bold text-gray-900 dark:text-gray-100 flex items-center gap-1">
                <span>🤖</span> Android (APK)
              </div>
              <p className="text-gray-500 dark:text-gray-400 text-[10px]">
                {lang === 'en' ? 'Native touch installer (.apk) for remote control' : '원격 전원 제어용 전용 터치 설치 패키지 (.apk)'}
              </p>
              <div className="font-mono text-[9px] text-blue-500 font-semibold">
                PowerController-v{APP_VERSION}.apk
              </div>
            </div>
            {/* iPhone iOS */}
            <div className="p-2.5 rounded bg-gray-100 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 space-y-1">
              <div className="font-bold text-gray-900 dark:text-gray-100 flex items-center gap-1">
                <span>🍏</span> iPhone (iOS)
              </div>
              <p className="text-gray-500 dark:text-gray-400 text-[10px]">
                {lang === 'en' ? 'Sideload .ipa or Safari > [Share] > [Add to Home]' : '사이드로딩 .ipa 패키지 및 Safari 원터치 홈 화면 설치'}
              </p>
              <div className="font-mono text-[9px] text-purple-500 font-semibold">
                PowerController-v{APP_VERSION}.ipa
              </div>
            </div>
          </div>
        </div>

        {/* Step 1: Python Source Code */}
        <div className="space-y-1.5 text-left">
          <div className="flex items-center justify-between text-xs flex-wrap gap-2">
            <span className="font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
              {lang === 'en' ? `1. Python GUI Script (${desktopName}.py)` : `1. 윈도우 무설치 GUI 파이썬 코드 (main.py)`}
            </span>
            <button
              id="btn-copy-python-code"
              onClick={() => handleCopy('pythonCode', pythonScriptCode)}
              className="text-[10px] text-blue-600 dark:text-blue-400 flex items-center gap-1 hover:underline cursor-pointer font-bold"
            >
              {copiedId === 'pythonCode' ? (
                <Check className="w-3 h-3 text-green-500" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
              {lang === 'en' ? 'Copy Entire Source' : '파이썬 코드 전체 복사'}
            </button>
          </div>
          <p className="text-[10px] text-gray-500 leading-normal font-sans">
            {lang === 'en'
              ? `Save this script into a local text file named "main.py" or "${desktopName}.py"`
              : '바탕화면에 메모장이나 VSCode 에디터를 켜고 아래 코드를 붙여넣은 뒤, main.py 로 저장해 주십시오.'}
          </p>
          <pre className="text-[10.5px] font-mono p-3 bg-gray-50 dark:bg-gray-950 rounded-md border border-gray-100 dark:border-gray-900 overflow-x-auto whitespace-pre text-gray-400 max-h-72">
            {pythonScriptCode}
          </pre>
        </div>

        {/* Step 2: Compile Command */}
        <div className="space-y-1.5 pt-2 border-t border-dashed border-gray-200/50 dark:border-gray-800/40 text-left">
          <div className="flex items-center justify-between text-xs flex-wrap gap-2">
            <span className="font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
              {lang === 'en' ? '2. Packaging Terminal Commander (PyInstaller)' : '2. 단일 파일 EXE 컴파일 명령 (PyInstaller)'}
            </span>
            <button
              id="btn-copy-compile-cmd"
              onClick={() => handleCopy('compileCmd', pyInstallerCommand)}
              className="text-[10px] text-teal-600 dark:text-teal-400 flex items-center gap-1 hover:underline cursor-pointer font-bold"
            >
              {copiedId === 'compileCmd' ? (
                <Check className="w-3 h-3 text-green-500" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
              {lang === 'en' ? 'Copy Instructions' : '컴파일 명령 복사'}
            </button>
          </div>
          <p className="text-[10px] text-gray-500 leading-normal font-sans">
            {lang === 'en'
              ? 'Execute these commands in cmd / terminal located in the script directory:'
              : '터미널(명령 프롬프트/PowerShell)을 열고 main.py 가 위치한 경로로 이동 후 아래 명령어를 입력해주십시오:'}
          </p>
          <pre className="text-[11px] font-mono p-2.5 bg-gray-950 text-emerald-400 rounded-md border border-gray-900 overflow-x-auto whitespace-pre no-scrollbar">
            {pyInstallerCommand}
          </pre>
          
          {/* Troubleshooting Section for Windows PATH issue */}
          <div className="p-3 bg-red-500/15 border border-red-500/25 rounded-lg space-y-2 text-left">
            <h4 className="text-[11px] font-bold text-red-500 dark:text-red-400 flex items-center gap-1.5">
              <span>💡</span> 
              {lang === 'en' 
                ? 'Fixing "command not found: pyinstaller" error'
                : '"pyinstaller 용어가 인식되지 않습니다" 오류 발생 시 해결책'}
            </h4>
            <p className="text-[10px] text-gray-500 border-l-2 border-red-500 pl-2 leading-relaxed">
              {lang === 'en'
                ? 'If Pyinstaller terminal commands are not found on your system PATH, invoke via Python directly to bypass system restrictions:'
                : '파이썬 설치 시 환경 변수(PATH)가 자동으로 등록되지 않아 발생하는 일반적인 윈도우 환경 문제입니다. 환경 변수를 수동 정비하지 않는 경우 아래 직접 구동 모듈 쉘을 복사하여 즉각 처방이 가능합니다:'}
            </p>
            <div className="flex items-center justify-between gap-2 p-1.5 bg-gray-900 rounded border border-gray-805">
              <code className="text-[10px] font-mono text-cyan-400">
                python -m PyInstaller --onefile --noconsole --name="{desktopName}" main.py
              </code>
              <button
                type="button"
                onClick={() => handleCopy('tsCmd', `python -m PyInstaller --onefile --noconsole --name="${desktopName}" main.py`)}
                className="text-[9px] bg-gray-800 text-gray-355 hover:text-white px-1.5 py-0.5 rounded cursor-pointer"
              >
                {copiedId === 'tsCmd' ? (lang === 'en' ? 'Copied' : '복사됨!') : (lang === 'en' ? 'Copy' : '복사')}
              </button>
            </div>
            <p className="text-[9px] text-gray-500">
              {lang === 'en'
                ? '※ If python executable fails to invoke, prefix with "py" or supply the full absolute Python directory path.'
                : '※ 만약 python 명령어로 작동되지 않는 경우, 앞에 py를 붙여 py -m PyInstaller ... 로 입력해 주십시오.'}
            </p>
          </div>

          <div className="flex items-start gap-1 p-2 rounded bg-indigo-50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/30 text-left">
            <Sparkles className="w-3.5 h-3.5 text-indigo-500 mt-0.5 flex-shrink-0 animate-pulse" />
            <span className="text-[10px] text-indigo-700 dark:text-indigo-400 leading-relaxed font-sans">
              {lang === 'en'
                ? `Compilation finishes inside your workspace directory "dist" producing standalone portable program "${desktopName}.exe" free of bloat or dependencies!`
                : `빌드가 완료되면 dist 폴더 내부에 다른 패키지 설치 없이 클릭만 하면 단독으로 작동하는 ${desktopName}.exe 가 깔끔하게 출력됩니다.`}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
