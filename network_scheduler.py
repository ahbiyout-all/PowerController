import csv
import ipaddress
import locale
import os
import sys
import json
import re
import uuid
import socket
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

try:
    import native_bridge
except ImportError:
    native_bridge = None

# -------------------------------------------------------------------------
# 1. 전역 설정, 다국어 자동 감지(KO/EN) 및 로컬 IP/방화벽 엔진
# -------------------------------------------------------------------------
APP_VERSION = "2.9.2"
DEFAULT_PORT = 9988
DEFAULT_MASTER_RECOVERY_KEY = "PowerRescue#2026!Admin"


def detect_os_lang():
    """OS/시스템 로캘을 자동 감지하여 'ko' 또는 'en'을 반환합니다."""
    candidates = []
    if os.name == "nt":
        try:
            import ctypes
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            primary = lang_id & 0x3FF
            if primary == 0x12:  # LANG_KOREAN
                return "ko"
            if primary == 0x09:  # LANG_ENGLISH
                return "en"
        except Exception:
            pass

    for env_key in ("LC_ALL", "LC_MESSAGES", "LANGUAGE", "LANG"):
        val = os.getenv(env_key, "").strip()
        if val:
            candidates.append(val)

    try:
        loc = locale.getlocale()
        if loc and loc[0]:
            candidates.append(loc[0])
    except Exception:
        pass

    try:
        dloc = locale.getdefaultlocale()
        if dloc and dloc[0]:
            candidates.append(dloc[0])
    except Exception:
        pass

    for item in candidates:
        low = str(item).strip().lower()
        if low.startswith("ko") or "korean" in low:
            return "ko"
        if low.startswith("en") or "english" in low:
            return "en"

    return "en"


# -------------------------------------------------------------------------
# 다국어 UI 사전 (KO / EN)
# -------------------------------------------------------------------------
TR = {
    "window_title": {
        "ko": f"PowerController 50대 컴퓨터실 원격 통합 관제 타워 (v{APP_VERSION})",
        "en": f"PowerController 50-PC Lab Remote Fleet Control Tower (v{APP_VERSION})",
    },
    "header_title": {
        "ko": "⚡ PowerController 컴퓨터실 원격 관제 & 스케줄 타워",
        "en": "⚡ PowerController Lab Fleet Remote Control & Schedule Tower",
    },
    "my_ip": {"ko": "관리자 IP", "en": "Admin IP"},
    "license_btn": {"ko": "📜 라이선스", "en": "📜 License"},
    "lang_auto": {"ko": "자동", "en": "Auto"},
    "lang_manual": {"ko": "수동", "en": "Manual"},
    "sec1_title": {"ko": " 1. 대상 원격 PC & 보안 인증 ", "en": " 1. Target PCs & Security Auth "},
    "target_ip_lbl": {"ko": "대상 IP 주소:", "en": "Target IPs:"},
    "port_lbl": {"ko": "포트:", "en": "Port:"},
    "token_lbl": {"ko": "🔑 보안 토큰:", "en": "🔑 Token:"},
    "show_chk": {"ko": "표시", "en": "Show"},
    "btn_token_quick": {"ko": "🔐 토큰 전송", "en": "🔐 Token"},
    "btn_recovery": {"ko": "🚨 토큰 복구", "en": "🚨 Recovery"},
    "sec_profile_title": {
        "ko": " ★ 컴퓨터실 교시·일과 프로필 일괄 배포 ",
        "en": " ★ Class-Period / Lab Schedule Profiles ",
    },
    "profile_select_lbl": {"ko": "프로필 선택:", "en": "Lab Profile:"},
    "btn_deploy_profile": {"ko": "📡 프로필 일괄 배포", "en": "📡 Deploy Profile"},
    "sec2_title": {"ko": " 2. 개별 전원 제어 & 스케줄 규칙 ", "en": " 2. Single Rule Mode & Schedule Time "},
    "rule_name_lbl": {"ko": "예약 규칙명:", "en": "Rule Label:"},
    "mode_lbl": {"ko": "전원 동작 모드:", "en": "Power Mode:"},
    "force_close_chk": {"ko": "강제 닫기 (/f)", "en": "Force Close (/f)"},
    "exec_time_lbl": {"ko": "실행 시각 (24H):", "en": "Run Time (24H):"},
    "hour_unit": {"ko": "시 ", "en": "h "},
    "min_unit": {"ko": "분", "en": "m"},
    "days_lbl": {"ko": "적용 요일:", "en": "Active Days:"},
    "sec3_title": {"ko": " 3. 사전 경고 & 유예 카운트다운 ", "en": " 3. Pre-Warning & Grace Countdown "},
    "warn_msg_lbl": {"ko": "경고 안내문:", "en": "Warning Text:"},
    "grace_lbl": {"ko": "유예 시간:", "en": "Grace Period:"},
    "allow_delay_chk": {"ko": "10분 연기/취소 허용", "en": "Allow 10m Delay/Cancel"},
    "beep_chk": {"ko": "경고음", "en": "Beep"},
    "sec4_title": {"ko": " 4. 조건부 유휴 & 사전 작업 ", "en": " 4. Idle Condition & Pre-Tasks "},
    "idle_only_chk": {"ko": "유휴 상태일 때만 실행", "en": "Run only when PC idle"},
    "idle_need_lbl": {"ko": "유휴 기준:", "en": "Idle Time:"},
    "clean_temp_chk": {"ko": "실행 전 %TEMP% 임시 파일 정리", "en": "Clean %TEMP% before action"},
    "precmd_lbl": {"ko": "사전 명령어:", "en": "Pre-Command:"},
    "apply_opt_lbl": {"ko": "적용 방식:", "en": "Apply Mode:"},
    "opt_append": {"ko": "추가 (Append)", "en": "Append"},
    "opt_overwrite": {"ko": "덮어쓰기 (Overwrite)", "en": "Overwrite"},
    "btn_send_rule": {"ko": "🚀 선택 PC에 규칙 병렬 전송", "en": "🚀 Push Rule (Parallel)"},
    "btn_clear_all": {"ko": "🗑️ 원격 예약 초기화", "en": "🗑️ Clear Schedules"},
    "sec_imm_title": {
        "ko": " ⚡ 선택 PC 즉시 전원 제어 (병렬 실행) ",
        "en": " ⚡ Immediate Power Control (Parallel) ",
    },
    "btn_imm_shutdown": {"ko": "🛑 즉시 종료", "en": "🛑 Shutdown"},
    "btn_imm_reboot": {"ko": "🔄 재시작", "en": "🔄 Reboot"},
    "btn_imm_sleep": {"ko": "🌙 절전", "en": "🌙 Sleep"},
    "btn_imm_screenoff": {"ko": "📺 화면끔", "en": "📺 Screen Off"},
    "btn_imm_alarm": {"ko": "🔔 알람", "en": "🔔 Alarm"},
    "right_title": {
        "ko": "🖥️ 50대 컴퓨터실 좌석·장비 관제 패널 (Lab Fleet)",
        "en": "🖥️ 50-PC Classroom Fleet & Seat Map Panel",
    },
    "grp_lbl": {"ko": "📁 그룹:", "en": "📁 Group:"},
    "btn_manage_grp": {"ko": "⚙️ 그룹/WOL", "en": "⚙️ Groups"},
    "btn_range_scan": {"ko": "🌐 대역 스캔", "en": "🌐 IP Range"},
    "btn_csv_import": {"ko": "📥 CSV 등록", "en": "📥 CSV Import"},
    "btn_csv_export": {"ko": "📤 CSV 저장", "en": "📤 CSV Export"},
    "search_lbl": {"ko": "검색:", "en": "Search:"},
    "filter_all": {"ko": "전체", "en": "All"},
    "filter_online": {"ko": "온라인", "en": "Online"},
    "filter_offline": {"ko": "오프라인", "en": "Offline"},
    "filter_failed": {"ko": "실패", "en": "Failed"},
    "view_grid": {"ko": "⊞ 좌석 배치", "en": "⊞ Seat Grid"},
    "view_table": {"ko": "☰ 상세 목록", "en": "☰ Table View"},
    "cols_lbl": {"ko": "열:", "en": "Cols:"},
    "autopoll_chk": {"ko": "15초 자동 폴링", "en": "Auto-Poll (15s)"},
    "sel_all_vis": {"ko": "☑️ 표시 전체", "en": "☑️ All Visible"},
    "sel_clear": {"ko": "☐ 해제", "en": "☐ Clear"},
    "sel_online": {"ko": "🟢 온라인", "en": "🟢 Online"},
    "sel_offline": {"ko": "⚪ 오프라인(WOL)", "en": "⚪ Offline(WOL)"},
    "sel_failed": {"ko": "🔴 실패만", "en": "🔴 Failed"},
    "btn_scan": {"ko": "🔍 LAN 스캔", "en": "🔍 LAN Scan"},
    "btn_query": {"ko": "📊 상태 폴링", "en": "📊 Poll Status"},
    "wol_step_lbl": {"ko": "WOL 간격:", "en": "WOL Step:"},
    "btn_group_wol": {"ko": "⚡ 순차 WOL 기상", "en": "⚡ Staggered WOL"},
    "preserve_chk": {"ko": "탐색/오프라인 PC 목록 유지", "en": "Keep scanned & offline roster"},
    "btn_retry_failed": {"ko": "🔁 실패 PC 재시도", "en": "🔁 Retry Failed"},
    "log_title": {"ko": "📋 병렬 전송 · ACK 응답 실시간 콘솔", "en": "📋 Parallel Dispatch & ACK Console"},
    "ready_msg": {
        "ko": f"준비 완료 (v{APP_VERSION}): IP 대역 스캔 또는 CSV 좌석 등록 후 50대 PC를 병렬 관제하십시오.",
        "en": f"Ready (v{APP_VERSION}): Use IP Range Scan or CSV Import to onboard and manage up to 50+ lab PCs.",
    },
}


# -------------------------------------------------------------------------
# 자주 사용하는 스케줄 제목 프리셋 10종 (KO / EN)
# -------------------------------------------------------------------------
POPULAR_SCHEDULE_PRESETS = [
    {
        "title_ko": "심야 PC 자동 종료",
        "title_en": "Midnight PC Auto Shutdown",
        "mode": "shutdown",
        "hour": "23",
        "min": "30",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "idle": False,
        "warn_ko": "심야 업무 종료: 작업 중인 문서를 저장하고 안전하게 PC를 종료합니다.",
        "warn_en": "Night shutdown: Please save open documents before PC powers off.",
    },
    {
        "title_ko": "퇴근·방과후 일괄 종료",
        "title_en": "End-of-Day Lab Shutdown",
        "mode": "shutdown",
        "hour": "18",
        "min": "30",
        "days": [0, 1, 2, 3, 4],
        "idle": False,
        "warn_ko": "일과 종료 안내: 컴퓨터실 모든 PC 전원이 곧 자동 종료됩니다.",
        "warn_en": "End of day: Classroom PCs will automatically shut down shortly.",
    },
    {
        "title_ko": "대용량 다운로드 후 종료",
        "title_en": "Shutdown After Large Download",
        "mode": "shutdown",
        "hour": "02",
        "min": "00",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "idle": True,
        "warn_ko": "대용량 작업 완료 후 미사용 상태를 확인하여 전원을 안전하게 끕니다.",
        "warn_en": "Powering off safely once idle after background transfers complete.",
    },
    {
        "title_ko": "점심시간 빠른 재부팅",
        "title_en": "Lunch Break Quick Reboot",
        "mode": "reboot",
        "hour": "12",
        "min": "40",
        "days": [0, 1, 2, 3, 4],
        "idle": False,
        "warn_ko": "점심시간 시스템 리프레시: 다음 수업을 위해 빠른 재부팅을 진행합니다.",
        "warn_en": "Midday refresh: Quick reboot to keep classroom PCs responsive.",
    },
    {
        "title_ko": "공강/유휴 절전 모드",
        "title_en": "Idle Break Sleep Mode",
        "mode": "sleep",
        "hour": "14",
        "min": "00",
        "days": [0, 1, 2, 3, 4],
        "idle": True,
        "warn_ko": "장시간 미사용 감지: 에너지 절약을 위해 절전 모드로 전환합니다.",
        "warn_en": "Extended inactivity detected: Entering low-power Sleep mode.",
    },
    {
        "title_ko": "새벽 정기 시스템 점검 재시작",
        "title_en": "Early Morning Maintenance Reboot",
        "mode": "reboot",
        "hour": "05",
        "min": "00",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "idle": False,
        "warn_ko": "새벽 정기 점검: 시스템 안정성을 위해 예약 재부팅을 수행합니다.",
        "warn_en": "Scheduled maintenance: Rebooting PCs for daily stability.",
    },
    {
        "title_ko": "수업 시작 준비 알람",
        "title_en": "Class Start Preparation Bell",
        "mode": "alarm",
        "hour": "08",
        "min": "50",
        "days": [0, 1, 2, 3, 4],
        "idle": False,
        "warn_ko": "수업 시작 10분 전 안내: 자리 정돈 및 실습 환경을 확인하세요.",
        "warn_en": "Class begins in 10 minutes: Prepare workstation materials.",
    },
    {
        "title_ko": "야간 미디어 시청 후 종료",
        "title_en": "Late Night Idle Power Off",
        "mode": "shutdown",
        "hour": "01",
        "min": "00",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "idle": True,
        "warn_ko": "야간 미사용 감지: 절전을 위해 PC를 자동 종료합니다.",
        "warn_en": "Nighttime idle detected: Powering off workstation.",
    },
    {
        "title_ko": "쉬는 시간 모니터 일괄 끄기",
        "title_en": "Recess Display Screen Off",
        "mode": "screenoff",
        "hour": "10",
        "min": "50",
        "days": [0, 1, 2, 3, 4],
        "idle": False,
        "warn_ko": "수업 집중 및 절전을 위해 학생용 모니터 화면을 끕니다.",
        "warn_en": "Turning off lab monitors for energy savings / attention.",
    },
    {
        "title_ko": "실습 빌드 완료 후 종료",
        "title_en": "Shutdown After Batch Render",
        "mode": "shutdown",
        "hour": "04",
        "min": "00",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "idle": True,
        "warn_ko": "대용량 실습 작업 완료 후 PC 전원을 안전하게 끕니다.",
        "warn_en": "Lab batch task finished: Shutting down workstation safely.",
    },
]

# -------------------------------------------------------------------------
# 컴퓨터실 교시·일과별 일괄 프로필 4종 (복수 규칙 묶음 배포)
# -------------------------------------------------------------------------
LAB_SCHEDULE_PROFILES = [
    {
        "id": "profile_standard_day",
        "name_ko": "🏫 1. 정규 컴퓨터실 일과 (오전 알람 + 점심 재부팅 + 17:30 일괄 종료)",
        "name_en": "🏫 1. Standard School Lab Day (08:50 Bell + 12:30 Reboot + 17:30 Shutdown)",
        "desc_ko": "수업 준비 알람(08:50), 점심 리프레시 재부팅(12:30), 방과후 일괄 종료(17:30) 3종 규칙 일괄 배포",
        "desc_en": "Deploys 3 weekday rules: 08:50 prep bell, 12:30 lunch reboot, and 17:30 EOD shutdown.",
        "rules": [
            {
                "label": "1교시 수업 준비 알람",
                "mode": "alarm",
                "time": "08:50",
                "days": [0, 1, 2, 3, 4],
                "force_close": False,
                "warning_message": "곧 1교시 수업이 시작됩니다.",
                "grace_period_sec": 5,
                "allow_delay": False,
                "warning_beep": True,
                "idle_only": False,
                "idle_minutes": 15,
                "clean_temp": False,
            },
            {
                "label": "점심시간 랩실 리프레시 재부팅",
                "mode": "reboot",
                "time": "12:30",
                "days": [0, 1, 2, 3, 4],
                "force_close": True,
                "warning_message": "점심시간 초기화: 오후 수업을 위해 PC를 재부팅합니다.",
                "grace_period_sec": 15,
                "allow_delay": True,
                "warning_beep": True,
                "idle_only": False,
                "idle_minutes": 15,
                "clean_temp": True,
            },
            {
                "label": "방과후 컴퓨터실 일괄 종료",
                "mode": "shutdown",
                "time": "17:30",
                "days": [0, 1, 2, 3, 4],
                "force_close": True,
                "warning_message": "방과후 일과 종료: 30초 후 컴퓨터실 PC가 종료됩니다.",
                "grace_period_sec": 30,
                "allow_delay": True,
                "warning_beep": True,
                "idle_only": False,
                "idle_minutes": 15,
                "clean_temp": True,
            },
        ],
    },
    {
        "id": "profile_afterschool_eco",
        "name_ko": "🌙 2. 야간·방과후 절전 & 안전 종료 (18:00 유휴 절전 + 21:30 최종 종료)",
        "name_en": "🌙 2. After-Hours Eco Policy (18:00 Idle Sleep + 21:30 Hard Shutdown)",
        "desc_ko": "방과후 미사용 PC 18:00 절전 전환 + 21:30 잔여 PC 일괄 완전 종료 (임시파일 정리 포함)",
        "desc_en": "Idles inactive lab seats at 18:00 Sleep and forces full EOD shutdown at 21:30.",
        "rules": [
            {
                "label": "방과후 미사용 PC 절전",
                "mode": "sleep",
                "time": "18:00",
                "days": [0, 1, 2, 3, 4],
                "force_close": False,
                "warning_message": "미사용 감지: 절전 모드로 전환됩니다.",
                "grace_period_sec": 15,
                "allow_delay": True,
                "warning_beep": True,
                "idle_only": True,
                "idle_minutes": 20,
                "clean_temp": False,
            },
            {
                "label": "야간 컴퓨터실 최종 종료",
                "mode": "shutdown",
                "time": "21:30",
                "days": [0, 1, 2, 3, 4, 5, 6],
                "force_close": True,
                "warning_message": "야간 보안 소등: 작업을 저장하세요. 곧 전원이 종료됩니다.",
                "grace_period_sec": 30,
                "allow_delay": True,
                "warning_beep": True,
                "idle_only": False,
                "idle_minutes": 15,
                "clean_temp": True,
            },
        ],
    },
    {
        "id": "profile_exam_focus",
        "name_ko": "📝 3. 실기시험·수업 집중 통제 (종료 알림 + 화면 끄기 + 잠금)",
        "name_en": "📝 3. Exam / Class Focus Lockdown (Warn Bell + Screen Off + Lock)",
        "desc_ko": "평가 종료 5분전 알람 후 지정 시각에 화면 일괄 소등 및 워크스테이션 잠금",
        "desc_en": "Plays exam ending bell, then blanks displays and locks seats simultaneously.",
        "rules": [
            {
                "label": "시험 종료 5분 전 알림",
                "mode": "alarm",
                "time": "11:45",
                "days": [0, 1, 2, 3, 4],
                "force_close": False,
                "warning_message": "시험 종료 5분 전입니다. 답안 파일을 저장하십시오.",
                "grace_period_sec": 5,
                "allow_delay": False,
                "warning_beep": True,
                "idle_only": False,
                "idle_minutes": 15,
                "clean_temp": False,
            },
            {
                "label": "시험 종료 화면 잠금",
                "mode": "lock",
                "time": "11:50",
                "days": [0, 1, 2, 3, 4],
                "force_close": False,
                "warning_message": "시험 시간이 종료되어 PC를 잠급니다.",
                "grace_period_sec": 10,
                "allow_delay": False,
                "warning_beep": True,
                "idle_only": False,
                "idle_minutes": 15,
                "clean_temp": False,
            },
        ],
    },
    {
        "id": "profile_weekend_maint",
        "name_ko": "🛠️ 4. 주말 대청소 & 임시파일 초기화 (일 04:00 재부팅 + 04:30 종료)",
        "name_en": "🛠️ 4. Weekend Maintenance & Clean Reset (Sun 04:00 Reboot + 04:30 Off)",
        "desc_ko": "일요일 새벽 %TEMP% 정리 재부팅 후 월요일 수업 전까지 안전 종료 상태로 대기",
        "desc_en": "Sunday 04:00 clean-temp reboot followed by 04:30 safe power off.",
        "rules": [
            {
                "label": "주말 새벽 임시파일 정리 리셋",
                "mode": "reboot",
                "time": "04:00",
                "days": [6],
                "force_close": True,
                "warning_message": "주간 유지보수 리셋을 실행합니다.",
                "grace_period_sec": 10,
                "allow_delay": False,
                "warning_beep": False,
                "idle_only": False,
                "idle_minutes": 15,
                "clean_temp": True,
            },
            {
                "label": "주말 점검 완료 후 안전 종료",
                "mode": "shutdown",
                "time": "04:30",
                "days": [6],
                "force_close": True,
                "warning_message": "점검 완료: 절전을 위해 PC를 종료합니다.",
                "grace_period_sec": 10,
                "allow_delay": False,
                "warning_beep": False,
                "idle_only": False,
                "idle_minutes": 15,
                "clean_temp": True,
            },
        ],
    },
]


def ensure_firewall_rule_silent():
    """Windows Defender Firewall 예외 규칙을 무음(백그라운드) 등록하여 인바운드/공용 네트워크 차단 및 팝업 방지"""
    if os.name == "nt":
        try:
            exe_path = sys.executable if getattr(sys, "frozen", False) else sys.executable
            app_dir = os.path.dirname(os.path.abspath(exe_path))
            main_exe = os.path.join(app_dir, "PowerController.exe")
            fw_bat = os.path.join(app_dir, "Register_Firewall_Rules.bat")

            if native_bridge and native_bridge.is_firewall_engine_loaded():
                try:
                    reg_cnt = native_bridge.batch_register_firewall_suite(app_dir, APP_VERSION)
                    if reg_cnt > 0:
                        return
                except Exception:
                    pass

            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

            is_admin = False
            try:
                import ctypes
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                pass

            for rname, prog in [
                ("PowerNetworkScheduler (Inbound)", exe_path),
                (f"PowerNetworkScheduler v{APP_VERSION} (Inbound)", exe_path),
            ]:
                subprocess.run(
                    [
                        "netsh", "advfirewall", "firewall", "add", "rule",
                        f"name={rname}", "dir=in", "action=allow",
                        f"program={prog}", "enable=yes", "profile=any",
                    ],
                    capture_output=True,
                    creationflags=creationflags,
                )
            for rname, prog in [
                ("PowerNetworkScheduler (Outbound)", exe_path),
                (f"PowerNetworkScheduler v{APP_VERSION} (Outbound)", exe_path),
            ]:
                subprocess.run(
                    [
                        "netsh", "advfirewall", "firewall", "add", "rule",
                        f"name={rname}", "dir=out", "action=allow",
                        f"program={prog}", "enable=yes", "profile=any",
                    ],
                    capture_output=True,
                    creationflags=creationflags,
                )

            if os.path.exists(main_exe):
                for direction, d_label in [("in", "Inbound"), ("out", "Outbound")]:
                    for rn in [f"PowerController ({d_label})", f"PowerController v{APP_VERSION} ({d_label})"]:
                        subprocess.run(
                            [
                                "netsh", "advfirewall", "firewall", "add", "rule",
                                f"name={rn}", f"dir={direction}", "action=allow",
                                f"program={main_exe}", "enable=yes", "profile=any",
                            ],
                            capture_output=True,
                            creationflags=creationflags,
                        )

            for p_name, proto, port in [
                ("PowerController TCP 9988", "TCP", "9988"),
                (f"PowerController v{APP_VERSION} TCP 9988", "TCP", "9988"),
                ("PowerController UDP 9985", "UDP", "9985"),
                (f"PowerController v{APP_VERSION} UDP 9985", "UDP", "9985"),
                ("PowerController UDP 9986", "UDP", "9986"),
                (f"PowerController v{APP_VERSION} UDP 9986", "UDP", "9986"),
            ]:
                subprocess.run(
                    [
                        "netsh", "advfirewall", "firewall", "add", "rule",
                        f"name={p_name}", "dir=in", "action=allow",
                        f"protocol={proto}", f"localport={port}", "enable=yes", "profile=any",
                    ],
                    capture_output=True,
                    creationflags=creationflags,
                )

            if not is_admin:
                chk = subprocess.run(
                    ["netsh", "advfirewall", "firewall", "show", "rule", "name=PowerNetworkScheduler (Inbound)"],
                    capture_output=True,
                    creationflags=creationflags,
                    text=True,
                    errors="ignore",
                )
                rule_missing = (
                    "No rules match" in chk.stdout
                    or "규칙이 없습니다" in chk.stdout
                    or chk.returncode != 0
                )
                if rule_missing and os.path.exists(fw_bat):
                    subprocess.run(
                        [
                            "powershell", "-NoProfile", "-WindowStyle", "Hidden",
                            "-Command", f"Start-Process '{fw_bat}' -Verb RunAs",
                        ],
                        creationflags=creationflags,
                    )
        except Exception:
            pass


def get_local_ip():
    """현재 컴퓨터의 LAN(Local Area Network) IP 주소를 감지합니다."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_all_local_ips():
    """현재 컴퓨터(관리자 PC)의 모든 활성 IPv4 주소 집합을 반환합니다."""
    ips = {"127.0.0.1", "localhost", "0.0.0.0"}
    try:
        primary = get_local_ip()
        if primary and primary != "127.0.0.1":
            ips.add(primary)
    except Exception:
        pass

    try:
        host_name = socket.gethostname()
        ips.add(socket.gethostbyname(host_name))
        addr_infos = socket.getaddrinfo(host_name, None, socket.AF_INET)
        for item in addr_infos:
            addr = item[4][0]
            if addr:
                ips.add(addr)
    except Exception:
        pass

    return ips


def is_local_admin_ip(ip):
    """주어진 IP가 현재 관리자 PC의 자체 IP인지 판별합니다."""
    if not ip:
        return False
    return ip.strip() in get_all_local_ips()


if getattr(sys, "frozen", False):
    SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_data_filepath(filename):
    """안전한 설정 저장 경로 반환 (%APPDATA%/PowerController 폴백)."""
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
        os.makedirs(os.path.dirname(appdata_path), exist_ok=True)
        return appdata_path


GROUPS_CONFIG_FILE = get_data_filepath("network_pc_groups.json")


def get_local_mac():
    """로컬 컴퓨터의 대표 MAC 주소를 16진수 문자열로 반환합니다."""
    try:
        node = uuid.getnode()
        mac = ":".join(["{:02x}".format((node >> i) & 0xFF) for i in range(0, 48, 8)][::-1])
        return mac.upper()
    except Exception:
        return ""


def get_mac_from_arp(ip):
    """지정된 IP의 MAC 주소를 OS ARP 캐시 테이블에서 실시간 조회합니다."""
    if not ip or ip in ["127.0.0.1", "localhost"]:
        return get_local_mac()
    try:
        if os.path.exists("/proc/net/arp"):
            with open("/proc/net/arp", "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 4 and parts[0] == ip:
                        candidate = parts[3].upper()
                        if candidate != "00:00:00:00:00:00" and len(candidate) == 17:
                            return candidate
    except Exception:
        pass
    try:
        cmd = f"arp -a {ip}" if os.name == "nt" else f"arp -n {ip}"
        res = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
        match = re.search(
            r"([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})",
            res,
        )
        if match:
            candidate = match.group(1).replace("-", ":").upper()
            if candidate != "00:00:00:00:00:00":
                return candidate
    except Exception:
        pass
    return ""


def send_wol_magic_packet(mac_address, target_ip=None, port=9, **kwargs):
    """
    Wake-on-LAN (WOL) Magic Packet 전송
    표준 매직 패킷: 6바이트 0xFF + 16회 반복 6바이트 MAC (102바이트)
    """
    if target_ip is None and "ip" in kwargs:
        target_ip = kwargs.get("ip")
    if not mac_address:
        return {"success": False, "message": "MAC 주소가 등록되어 있지 않습니다."}

    clean_mac = re.sub(r"[^0-9a-fA-F]", "", mac_address)
    if len(clean_mac) != 12:
        return {
            "success": False,
            "message": f"올바르지 않은 MAC 주소 형식입니다: '{mac_address}' (12자리 16진수 필요)",
        }

    mac_bytes = bytes.fromhex(clean_mac)
    magic_packet = b"\xff" * 6 + mac_bytes * 16

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    destinations = [("255.255.255.255", port), ("255.255.255.255", 7)]
    if target_ip and target_ip != "127.0.0.1":
        parts = target_ip.split(".")
        if len(parts) == 4:
            subnet_broadcast = ".".join(parts[:3]) + ".255"
            destinations.append((subnet_broadcast, port))
            destinations.append((subnet_broadcast, 7))
            destinations.append((target_ip, port))

    sent_routes = 0
    for dst_ip, dst_port in destinations:
        try:
            sock.sendto(magic_packet, (dst_ip, dst_port))
            sent_routes += 1
        except Exception:
            pass
    sock.close()

    formatted_mac = ":".join([clean_mac[i : i + 2].upper() for i in range(0, 12, 2)])
    return {
        "success": sent_routes > 0,
        "mac": formatted_mac,
        "message": f"매직 패킷 브로드캐스트 전송 성공 ({sent_routes}개 경로)",
    }


def extract_ip_from_list_item(text):
    """목록 항목 문자열에서 IPv4 주소만을 정확하게 추출합니다."""
    if not text:
        return ""
    match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
    return match.group(0) if match else ""


def expand_ipv4_range(start_ip_str, end_ip_str, limit=256):
    """시작 IP부터 종료 IP까지 IPv4 주소 리스트를 안전하게 생성합니다."""
    start_addr = ipaddress.IPv4Address(start_ip_str.strip())
    end_addr = ipaddress.IPv4Address(end_ip_str.strip())
    if int(end_addr) < int(start_addr):
        raise ValueError("End IP must be >= Start IP")
    count = int(end_addr) - int(start_addr) + 1
    if count > limit:
        raise ValueError(f"Range exceeds limit of {limit} hosts ({count})")
    return [str(ipaddress.IPv4Address(int(start_addr) + i)) for i in range(count)]


def format_seat_no(index_1based, prefix="", width=2):
    """1-based 좌석 번호를 '01' 또는 'A-01' 형식으로 포맷합니다."""
    num_str = str(index_1based).zfill(width)
    return f"{prefix}{num_str}" if prefix else num_str


def ip_sort_key(ip):
    """IPv4 옥텟 기준 정렬 키."""
    try:
        return tuple(int(p) for p in ip.split("."))
    except Exception:
        return (999, 999, 999, 999)


def parse_lab_roster_csv(csv_text):
    """
    RFC-4180 CSV 문자열에서 50대 컴퓨터실 좌석·장비 목록을 파싱합니다.
    지원 컬럼: seat_no(seat), ip, mac, hostname, group, row, col, memo
    """
    rows = []
    reader = csv.DictReader(csv_text.splitlines())
    if not reader.fieldnames:
        return rows

    norm_map = {}
    for fn in reader.fieldnames:
        k = fn.strip().lower().lstrip("\ufeff")
        norm_map[fn] = k

    for idx, raw_row in enumerate(reader, start=1):
        norm = {norm_map.get(k, k): (v or "").strip() for k, v in raw_row.items() if k is not None}
        ip = norm.get("ip") or norm.get("ip_address") or norm.get("host_ip") or ""
        if not ip:
            continue
        try:
            ipaddress.IPv4Address(ip)
        except Exception:
            continue
        seat_no = norm.get("seat_no") or norm.get("seat") or format_seat_no(idx)
        mac = norm.get("mac") or norm.get("mac_address") or ""
        hostname = norm.get("hostname") or norm.get("host") or norm.get("pc_name") or f"LAB-{seat_no}"
        group = norm.get("group") or "default"
        try:
            row_num = int(norm.get("row") or 0)
        except Exception:
            row_num = 0
        try:
            col_num = int(norm.get("col") or 0)
        except Exception:
            col_num = 0
        memo = norm.get("memo") or norm.get("note") or ""
        rows.append(
            {
                "ip": ip,
                "seat_no": seat_no,
                "mac": mac.upper(),
                "hostname": hostname,
                "group": group,
                "row": row_num,
                "col": col_num,
                "memo": memo,
            }
        )
    return rows


# -------------------------------------------------------------------------
# 2. 송신용 클라이언트 함수 및 방화벽 우회 비콘 동기화 허브
# -------------------------------------------------------------------------
DISCOVERED_CLIENTS = {}
PENDING_RESPONSES = {}
PENDING_LOCK = threading.Lock()
GLOBAL_APP_INSTANCE = None
_hub_started = False


def start_scheduler_sync_hub():
    """방화벽 우회 비콘 및 ACK를 수신하는 UDP 허브 (순수 창작 NetBeaconEngine 연동)"""
    global _hub_started
    if _hub_started:
        return
    _hub_started = True

    def _handle_incoming_beacon(msg, addr):
        if msg.get("type") == "client_sync_poll":
            c_ip = msg.get("client_ip", addr[0])
            c_host = msg.get("hostname", "PowerPC")
            c_mac = msg.get("mac", "")
            DISCOVERED_CLIENTS[c_ip] = {
                "addr": addr,
                "last_seen": time.time(),
                "hostname": c_host,
                "mac": c_mac,
                "has_token": msg.get("has_token", False),
                "rules_count": msg.get("rules_count", 0),
                "timer_running": msg.get("timer_running", False),
                "remaining_seconds": msg.get("remaining_seconds", 0),
                "active_mode": msg.get("active_mode", ""),
                "bypass_ready": True,
            }
            if GLOBAL_APP_INSTANCE:
                try:
                    GLOBAL_APP_INSTANCE.root.after(
                        0,
                        lambda ip=c_ip, h=c_host, m=c_mac, info=dict(DISCOVERED_CLIENTS[c_ip]): GLOBAL_APP_INSTANCE.on_beacon_pc_discovered(
                            ip, h, m, info
                        ),
                    )
                except Exception:
                    pass

        if "reply_to" in msg or "success" in msg:
            c_ip = addr[0]
            with PENDING_LOCK:
                if c_ip in PENDING_RESPONSES:
                    PENDING_RESPONSES[c_ip]["resp"] = msg
                    PENDING_RESPONSES[c_ip]["event"].set()
                else:
                    for pending_ip, p_data in list(PENDING_RESPONSES.items()):
                        if not p_data["event"].is_set():
                            p_data["resp"] = msg
                            p_data["event"].set()
                            break

    if native_bridge and native_bridge.is_beacon_engine_loaded():
        if native_bridge.start_beacon_listener(9986):
            def native_hub_dispatcher():
                while True:
                    pkt = native_bridge.poll_next_beacon_packet()
                    if pkt:
                        try:
                            msg = json.loads(pkt["data"])
                            addr = (pkt["ip"], pkt["port"])
                            _handle_incoming_beacon(msg, addr)
                        except Exception:
                            pass
                    else:
                        time.sleep(0.01)

            threading.Thread(target=native_hub_dispatcher, daemon=True).start()
            return

    def hub_worker():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except Exception:
                pass
        try:
            sock.bind(("", 9986))
        except Exception:
            return

        while True:
            try:
                data, addr = sock.recvfrom(8192)
                if not data:
                    continue
                msg = json.loads(data.decode("utf-8"))
                _handle_incoming_beacon(msg, addr)
            except Exception:
                time.sleep(0.1)

    threading.Thread(target=hub_worker, daemon=True).start()


def send_via_bypass_channel(ip, payload):
    """방화벽 차단 시 역방향 UDP 및 브로드캐스트 채널을 통해 전송합니다."""
    evt = threading.Event()
    with PENDING_LOCK:
        PENDING_RESPONSES[ip] = {"resp": None, "event": evt}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(2.0)

    if "signature" not in payload and native_bridge:
        try:
            raw_to_sign = json.dumps(
                {k: v for k, v in payload.items() if k != "signature"},
                sort_keys=True,
                ensure_ascii=False,
            )
            payload["signature"] = native_bridge.generate_schedule_hmac(raw_to_sign)
        except Exception:
            pass

    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    target_addr = (ip, 9985)
    if ip in DISCOVERED_CLIENTS and "addr" in DISCOVERED_CLIENTS[ip]:
        target_addr = DISCOVERED_CLIENTS[ip]["addr"]

    if native_bridge and native_bridge.is_beacon_engine_loaded():
        try:
            payload_str = json.dumps(payload, ensure_ascii=False)
            native_bridge.send_beacon_direct(ip, target_addr[1], payload_str)
            if target_addr[1] != 9985:
                native_bridge.send_beacon_direct(ip, 9985, payload_str)
            if ip not in ["127.0.0.1", "localhost"]:
                native_bridge.send_beacon_broadcast(9985, payload_str)
        except Exception:
            pass

    try:
        sock.sendto(data_bytes, target_addr)
        if target_addr[1] != 9985:
            sock.sendto(data_bytes, (ip, 9985))
        if ip in ["127.0.0.1", "localhost"]:
            sock.sendto(data_bytes, ("127.0.0.1", 9985))
        else:
            sock.sendto(data_bytes, ("<broadcast>", 9985))
    except Exception:
        pass

    try:
        resp_data, _ = sock.recvfrom(8192)
        if resp_data:
            resp = json.loads(resp_data.decode("utf-8"))
            sock.close()
            msg = resp.get("message", "OK")
            resp["message"] = f"{msg} (UDP Bypass)"
            return resp
    except Exception:
        pass

    signaled = evt.wait(timeout=0.3)
    sock.close()

    with PENDING_LOCK:
        saved = PENDING_RESPONSES.pop(ip, None)

    if signaled and saved and saved.get("resp"):
        resp = saved["resp"]
        msg = resp.get("message", "OK")
        resp["message"] = f"{msg} (UDP Bypass)"
        return resp

    return {
        "success": False,
        "message": f"No response from {ip} (timeout / offline)",
    }


def send_payload_over_network(ip, port, payload, tcp_timeout=1.1):
    """지정된 원격 IP/Port로 JSON 페이로드를 전송하고 응답 ACK 및 지연시간(ms)을 반환합니다."""
    t0 = time.monotonic()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(tcp_timeout)
        sock.connect((ip, port))
        sock.sendall(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        resp_data = sock.recv(4096)
        sock.close()
        if resp_data:
            resp = json.loads(resp_data.decode("utf-8"))
            resp["latency_ms"] = max(1, int((time.monotonic() - t0) * 1000))
            return resp
    except Exception:
        pass

    resp = send_via_bypass_channel(ip, payload)
    resp["latency_ms"] = max(1, int((time.monotonic() - t0) * 1000))
    return resp


def send_rule_over_network(ip, port, rule_data, overwrite, auth_token=""):
    """스케줄 규칙 등록 페이로드를 조립하여 전송합니다."""
    payload = {
        "action": "register_schedule",
        "auth_token": auth_token,
        "overwrite": overwrite,
        "label": rule_data.get("label", "원격 자동 제어"),
        "type": "daily" if len(rule_data.get("days", [])) == 7 else "weekly",
        "mode": rule_data.get("mode", "shutdown"),
        "time": rule_data.get("time", "23:00"),
        "days": rule_data.get("days", [0, 1, 2, 3, 4, 5, 6]),
        "interval_min": 0,
        "force_close": rule_data.get("force_close", True),
        "warning_message": rule_data.get("warning_message", ""),
        "grace_period_sec": rule_data.get("grace_period_sec", 10),
        "allow_delay": rule_data.get("allow_delay", True),
        "warning_beep": rule_data.get("warning_beep", True),
        "idle_only": rule_data.get("idle_only", False),
        "idle_minutes": rule_data.get("idle_minutes", 15),
        "clean_temp": rule_data.get("clean_temp", False),
        "pre_command": rule_data.get("pre_command", ""),
    }
    return send_payload_over_network(ip, port, payload)


def send_clear_schedules(ip, port, auth_token=""):
    return send_payload_over_network(ip, port, {"action": "clear_schedules", "auth_token": auth_token})


def query_remote_status(ip, port, auth_token=""):
    return send_payload_over_network(ip, port, {"action": "query_status", "auth_token": auth_token}, tcp_timeout=0.9)


def send_immediate_power_action(ip, port, power_cmd="shutdown", force=True, grace_period_sec=3, auth_token=""):
    payload = {
        "action": "immediate_power",
        "power_cmd": power_cmd,
        "force": force,
        "grace_period_sec": grace_period_sec,
        "auth_token": auth_token,
    }
    return send_payload_over_network(ip, port, payload)


def send_verify_token(ip, port, auth_token=""):
    return send_payload_over_network(ip, port, {"action": "verify_token", "auth_token": auth_token})


def send_set_remote_token(ip, port, current_auth_token="", new_token=""):
    return send_payload_over_network(
        ip, port, {"action": "set_token", "auth_token": current_auth_token, "new_token": new_token}
    )


def get_master_recovery_key():
    env_key = os.getenv("POWER_TIMER_MASTER_KEY", "").strip()
    if env_key:
        return env_key
    try:
        if os.path.exists("power_master_key.txt"):
            with open("power_master_key.txt", "r", encoding="utf-8") as f:
                c = f.read().strip()
                if c:
                    return c
    except Exception:
        pass
    return DEFAULT_MASTER_RECOVERY_KEY


def send_emergency_reset_token(ip, port, master_key, new_token=""):
    return send_payload_over_network(
        ip, port, {"action": "emergency_reset_token", "master_key": master_key, "new_token": new_token}
    )


def send_query_remote_token(ip, port, master_key):
    return send_payload_over_network(
        ip, port, {"action": "query_token", "master_key": master_key}
    )


# -------------------------------------------------------------------------
# 3. 통합 50대 컴퓨터실 컨트롤 타워 UI 클래스 (Tkinter)
# -------------------------------------------------------------------------
class NetworkSchedulerApp:
    def __init__(self, root):
        global GLOBAL_APP_INSTANCE
        GLOBAL_APP_INSTANCE = self

        self.root = root
        self.root.geometry("1240x800")
        self.root.resizable(True, True)
        self.root.minsize(1060, 680)

        ensure_firewall_rule_silent()
        start_scheduler_sync_hub()

        self.last_scanned_active_ips = set()
        self.pc_live_telemetry = {}  # ip -> {status, latency_ms, rules_count, timer_running, remaining_seconds, active_mode, last_ack, last_err}
        self.failed_targets = []
        self.batch_in_progress = False
        self.grid_cols = 5
        self.view_mode = "grid"  # "grid" or "table"
        self.status_filter = "all"  # "all" | "online" | "offline" | "failed"
        self.sort_col = "seat"
        self.sort_reverse = False
        self.grid_tile_widgets = {}

        self.load_pc_groups_data()

        # OS 언어 자동 감지 & 저장된 수동 설정 반영
        self.detected_os_lang = detect_os_lang()
        pref = getattr(self, "lang_pref", {})
        if isinstance(pref, dict) and pref.get("mode") == "manual" and pref.get("lang") in ("ko", "en"):
            self.lang_mode = "manual"
            self.lang = pref["lang"]
        else:
            self.lang_mode = "auto"
            self.lang = self.detected_os_lang

        self.setup_styles()
        self.create_layout()
        self.apply_language()

        self.refresh_group_combobox()
        self.refresh_pc_roster_view()
        self.schedule_tick_loops()

    def t(self, key):
        entry = TR.get(key)
        if isinstance(entry, dict):
            return entry.get(self.lang, entry.get("en", key))
        return key

    def L(self, ko_text, en_text):
        return ko_text if self.lang == "ko" else en_text

    def setup_styles(self):
        self.bg_color = "#131722"
        self.card_color = "#1c2233"
        self.subcard_color = "#181d2b"
        self.input_bg = "#0f131d"
        self.text_color = "#f3f4f6"
        self.subtext_color = "#9ca3af"
        self.accent_color = "#3b82f6"
        self.accent_green = "#10b981"
        self.accent_red = "#ef4444"
        self.accent_orange = "#f59e0b"

        self.root.configure(bg=self.bg_color)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=self.bg_color)
        style.configure("Card.TFrame", background=self.card_color, relief="flat")
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Arial", 9))
        style.configure("CardLabel.TLabel", background=self.card_color, foreground=self.text_color, font=("Arial", 9))
        style.configure("Title.TLabel", background=self.bg_color, foreground=self.text_color, font=("Arial", 12, "bold"))

        style.configure("TButton", background=self.accent_color, foreground="white", font=("Arial", 9, "bold"), borderwidth=0)
        style.map("TButton", background=[("active", "#2563eb"), ("disabled", "#4b5563")])

        style.configure("Green.TButton", background=self.accent_green, foreground="white", font=("Arial", 9, "bold"), borderwidth=0)
        style.map("Green.TButton", background=[("active", "#059669"), ("disabled", "#4b5563")])

        style.configure("Red.TButton", background=self.accent_red, foreground="white", font=("Arial", 9, "bold"), borderwidth=0)
        style.map("Red.TButton", background=[("active", "#dc2626"), ("disabled", "#4b5563")])

        style.configure("Orange.TButton", background=self.accent_orange, foreground="white", font=("Arial", 9, "bold"), borderwidth=0)
        style.map("Orange.TButton", background=[("active", "#d97706"), ("disabled", "#4b5563")])

        style.configure("Purple.TButton", background="#8b5cf6", foreground="white", font=("Arial", 9, "bold"), borderwidth=0)
        style.map("Purple.TButton", background=[("active", "#7c3aed"), ("disabled", "#4b5563")])

        style.configure("Teal.TButton", background="#0d9488", foreground="white", font=("Arial", 9, "bold"), borderwidth=0)
        style.map("Teal.TButton", background=[("active", "#0f766e"), ("disabled", "#4b5563")])

        style.configure(
            "Fleet.Treeview",
            background="#0f131d",
            foreground="#e5e7eb",
            fieldbackground="#0f131d",
            rowheight=24,
            font=("Consolas", 8),
            borderwidth=0,
        )
        style.configure(
            "Fleet.Treeview.Heading",
            background="#1e293b",
            foreground="#cbd5e1",
            font=("Arial", 8, "bold"),
            relief="flat",
        )
        style.map("Fleet.Treeview", background=[("selected", "#1d4ed8")], foreground=[("selected", "white")])

        style.configure("Fleet.Horizontal.TProgressbar", troughcolor="#0f131d", background="#10b981", thickness=8)

    def create_layout(self):
        # -----------------------------------------------------------------
        # Top Header Bar with Locale Auto-Detect Switcher
        # -----------------------------------------------------------------
        header_frame = tk.Frame(self.root, bg=self.bg_color, pady=8)
        header_frame.pack(fill="x")

        self.title_lbl = ttk.Label(header_frame, text="", style="Title.TLabel")
        self.title_lbl.pack(side="left", padx=14)

        self.local_ip_lbl = ttk.Label(header_frame, text="", foreground="#9ca3af", font=("Consolas", 8, "bold"))
        self.local_ip_lbl.pack(side="right", padx=14)

        self.btn_license = tk.Button(
            header_frame,
            text="",
            font=("Arial", 8, "bold"),
            bg="#374151",
            fg="#e5e7eb",
            activebackground="#4b5563",
            activeforeground="white",
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
            command=self.show_license_dialog,
        )
        self.btn_license.pack(side="right", padx=(0, 8))

        # Language Switcher (KO / EN / Auto)
        lang_bar = tk.Frame(header_frame, bg="#1e293b", padx=2, pady=2)
        lang_bar.pack(side="right", padx=(0, 8))

        self.btn_lang_ko = tk.Button(
            lang_bar,
            text="KO",
            font=("Arial", 8, "bold"),
            relief="flat",
            padx=6,
            pady=1,
            cursor="hand2",
            command=lambda: self.set_language("ko", manual=True),
        )
        self.btn_lang_ko.pack(side="left")

        self.btn_lang_en = tk.Button(
            lang_bar,
            text="EN",
            font=("Arial", 8, "bold"),
            relief="flat",
            padx=6,
            pady=1,
            cursor="hand2",
            command=lambda: self.set_language("en", manual=True),
        )
        self.btn_lang_en.pack(side="left", padx=(2, 2))

        self.btn_lang_auto = tk.Button(
            lang_bar,
            text="Auto",
            font=("Arial", 7, "bold"),
            relief="flat",
            padx=6,
            pady=1,
            cursor="hand2",
            command=self.reset_language_auto,
        )
        self.btn_lang_auto.pack(side="left")

        # -----------------------------------------------------------------
        # Main Split Content: Left (Rules & Actions) + Right (50-PC Lab Fleet)
        # -----------------------------------------------------------------
        main_content_frame = tk.Frame(self.root, bg=self.bg_color)
        main_content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # ==================== [LEFT: Rule & Profile Deployment] ====================
        left_container = tk.Frame(main_content_frame, bg=self.bg_color, width=510)
        left_container.pack(side="left", fill="y", padx=(0, 8))
        left_container.pack_propagate(False)

        canvas = tk.Canvas(left_container, bg=self.bg_color, highlightthickness=0)
        v_scroll = tk.Scrollbar(left_container, orient="vertical", command=canvas.yview)
        form_card = ttk.Frame(canvas, style="Card.TFrame", padding=10)

        form_card.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=form_card, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.configure(yscrollcommand=v_scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

        # --- Section 1: Target IP & Auth ---
        self.sec1_frame = tk.LabelFrame(
            form_card, text="", bg=self.card_color, fg="#60a5fa", font=("Arial", 9, "bold"), padx=8, pady=6
        )
        self.sec1_frame.pack(fill="x", pady=(0, 7))

        f_ip = tk.Frame(self.sec1_frame, bg=self.card_color)
        f_ip.pack(fill="x", pady=2)
        self.lbl_target_ip = tk.Label(
            f_ip, text="", bg=self.card_color, fg="#93c5fd", font=("Arial", 8, "bold"), width=12, anchor="w"
        )
        self.lbl_target_ip.pack(side="left")
        self.entry_ip = tk.Entry(
            f_ip,
            bg=self.input_bg,
            fg="#38bdf8",
            readonlybackground="#1e293b",
            disabledbackground="#1e293b",
            disabledforeground="#38bdf8",
            insertbackground="#38bdf8",
            selectbackground="#2563eb",
            selectforeground="#ffffff",
            relief="solid",
            bd=1,
            font=("Consolas", 9, "bold"),
        )
        self.entry_ip.insert(0, "192.168.0.")
        self.entry_ip.pack(side="left", fill="x", expand=True, padx=(4, 0))

        f_pt = tk.Frame(self.sec1_frame, bg=self.card_color)
        f_pt.pack(fill="x", pady=3)
        self.lbl_port = ttk.Label(f_pt, text="", style="CardLabel.TLabel")
        self.lbl_port.pack(side="left")
        self.entry_port = tk.Entry(f_pt, bg=self.input_bg, fg="white", insertbackground="white", relief="flat", width=6)
        self.entry_port.insert(0, str(DEFAULT_PORT))
        self.entry_port.pack(side="left", padx=(4, 10))

        self.lbl_token = ttk.Label(f_pt, text="", style="CardLabel.TLabel")
        self.lbl_token.pack(side="left")
        self.entry_token = tk.Entry(f_pt, bg=self.input_bg, fg="#fbbf24", insertbackground="white", relief="flat", width=11, show="*")
        self.entry_token.pack(side="left", padx=(4, 4))

        self.show_token_var = tk.BooleanVar(value=False)
        self.chk_show_token = tk.Checkbutton(
            f_pt,
            text="",
            variable=self.show_token_var,
            command=lambda: self.entry_token.config(show="" if self.show_token_var.get() else "*"),
            bg=self.card_color,
            fg="#9ca3af",
            selectcolor=self.input_bg,
            activebackground=self.card_color,
            font=("Arial", 7),
        )
        self.chk_show_token.pack(side="left", padx=(0, 4))

        self.btn_send_token_quick = ttk.Button(
            f_pt, text="", style="Purple.TButton", command=self.on_send_token_only_click
        )
        self.btn_send_token_quick.pack(side="left", padx=(2, 0))

        self.btn_emergency_recovery = ttk.Button(
            f_pt, text="", style="Red.TButton", command=self.on_emergency_recovery_click
        )
        self.btn_emergency_recovery.pack(side="left", padx=(4, 0))

        # --- NEW Section: Class-Period Lab Schedule Profile Bundle ---
        self.sec_profile_frame = tk.LabelFrame(
            form_card, text="", bg=self.card_color, fg="#34d399", font=("Arial", 9, "bold"), padx=8, pady=6
        )
        self.sec_profile_frame.pack(fill="x", pady=(0, 7))

        f_prof_row = tk.Frame(self.sec_profile_frame, bg=self.card_color)
        f_prof_row.pack(fill="x")
        self.lbl_profile_sel = ttk.Label(f_prof_row, text="", style="CardLabel.TLabel")
        self.lbl_profile_sel.pack(side="left")

        self.combo_profile = ttk.Combobox(f_prof_row, state="readonly", font=("Arial", 8))
        self.combo_profile.pack(side="left", fill="x", expand=True, padx=4)
        self.combo_profile.bind("<<ComboboxSelected>>", self.on_profile_selected)

        self.btn_deploy_profile = ttk.Button(
            f_prof_row, text="", style="Teal.TButton", command=self.on_deploy_lab_profile_click
        )
        self.btn_deploy_profile.pack(side="right")

        self.lbl_profile_desc = tk.Label(
            self.sec_profile_frame,
            text="",
            bg=self.card_color,
            fg="#9ca3af",
            font=("Arial", 8),
            anchor="w",
            justify="left",
            wraplength=465,
        )
        self.lbl_profile_desc.pack(fill="x", pady=(4, 0))

        # --- Section 2: Power Mode & Single Schedule Time ---
        self.sec2_frame = tk.LabelFrame(
            form_card, text="", bg=self.card_color, fg="#60a5fa", font=("Arial", 9, "bold"), padx=8, pady=6
        )
        self.sec2_frame.pack(fill="x", pady=(0, 7))

        f_lbl_header = tk.Frame(self.sec2_frame, bg=self.card_color)
        f_lbl_header.pack(fill="x", pady=(1, 2))
        self.lbl_rule_name = ttk.Label(f_lbl_header, text="", style="CardLabel.TLabel")
        self.lbl_rule_name.pack(side="left")

        self.preset_combo = ttk.Combobox(f_lbl_header, state="readonly", width=28, font=("Arial", 8))
        self.preset_combo.pack(side="right")
        self.preset_combo.bind("<<ComboboxSelected>>", self.on_preset_title_selected)

        f_lbl = tk.Frame(self.sec2_frame, bg=self.card_color)
        f_lbl.pack(fill="x", pady=2)
        self.entry_label = tk.Entry(f_lbl, bg=self.input_bg, fg="white", insertbackground="white", relief="flat")
        self.entry_label.insert(0, "심야 PC 자동 종료" if self.lang == "ko" else "Midnight PC Auto Shutdown")
        self.entry_label.pack(side="left", fill="x", expand=True)

        f_mode = tk.Frame(self.sec2_frame, bg=self.card_color)
        f_mode.pack(fill="x", pady=2)
        self.lbl_mode = ttk.Label(f_mode, text="", style="CardLabel.TLabel", width=13)
        self.lbl_mode.pack(side="left")

        self.mode_keys = ["shutdown", "reboot", "sleep", "hibernate", "lock", "screenoff", "logout", "alarm"]
        self.combo_mode = ttk.Combobox(f_mode, state="readonly", width=23, font=("Arial", 8))
        self.combo_mode.pack(side="left", padx=(2, 8))

        self.force_close_var = tk.BooleanVar(value=True)
        self.chk_force = tk.Checkbutton(
            f_mode,
            text="",
            variable=self.force_close_var,
            bg=self.card_color,
            fg=self.text_color,
            selectcolor=self.input_bg,
            activebackground=self.card_color,
            font=("Arial", 8),
        )
        self.chk_force.pack(side="left")

        f_time = tk.Frame(self.sec2_frame, bg=self.card_color)
        f_time.pack(fill="x", pady=2)
        self.lbl_exec_time = ttk.Label(f_time, text="", style="CardLabel.TLabel", width=13)
        self.lbl_exec_time.pack(side="left")
        self.entry_hour = tk.Entry(f_time, bg=self.input_bg, fg="white", insertbackground="white", relief="flat", width=4, justify="center")
        self.entry_hour.insert(0, "23")
        self.entry_hour.pack(side="left", padx=(2, 0))
        self.lbl_hour_unit = ttk.Label(f_time, text="", style="CardLabel.TLabel")
        self.lbl_hour_unit.pack(side="left")
        self.entry_min = tk.Entry(f_time, bg=self.input_bg, fg="white", insertbackground="white", relief="flat", width=4, justify="center")
        self.entry_min.insert(0, "45")
        self.entry_min.pack(side="left")
        self.lbl_min_unit = ttk.Label(f_time, text="", style="CardLabel.TLabel")
        self.lbl_min_unit.pack(side="left")

        f_days = tk.Frame(self.sec2_frame, bg=self.card_color)
        f_days.pack(fill="x", pady=2)
        self.lbl_days = ttk.Label(f_days, text="", style="CardLabel.TLabel", width=13)
        self.lbl_days.pack(side="left")
        self.day_vars = []
        self.day_chks = []
        for _ in range(7):
            var = tk.BooleanVar(value=True)
            self.day_vars.append(var)
            chk = tk.Checkbutton(
                f_days,
                text="",
                variable=var,
                bg=self.card_color,
                fg=self.text_color,
                selectcolor=self.input_bg,
                activebackground=self.card_color,
                font=("Arial", 8),
            )
            chk.pack(side="left", padx=1)
            self.day_chks.append(chk)

        # --- Section 3: Warning & Grace Countdown ---
        self.sec3_frame = tk.LabelFrame(
            form_card, text="", bg=self.card_color, fg="#60a5fa", font=("Arial", 9, "bold"), padx=8, pady=6
        )
        self.sec3_frame.pack(fill="x", pady=(0, 7))

        f_warn_msg = tk.Frame(self.sec3_frame, bg=self.card_color)
        f_warn_msg.pack(fill="x", pady=2)
        self.lbl_warn_msg = ttk.Label(f_warn_msg, text="", style="CardLabel.TLabel", width=13)
        self.lbl_warn_msg.pack(side="left")
        self.entry_warn_msg = tk.Entry(f_warn_msg, bg=self.input_bg, fg="white", insertbackground="white", relief="flat")
        self.entry_warn_msg.insert(
            0,
            "관리자 예약 종료 안내: 작업 중인 문서를 안전하게 저장하십시오."
            if self.lang == "ko"
            else "Admin Schedule Notice: Save open files before power action.",
        )
        self.entry_warn_msg.pack(side="left", fill="x", expand=True, padx=(2, 0))

        f_grace_opts = tk.Frame(self.sec3_frame, bg=self.card_color)
        f_grace_opts.pack(fill="x", pady=2)
        self.lbl_grace = ttk.Label(f_grace_opts, text="", style="CardLabel.TLabel", width=13)
        self.lbl_grace.pack(side="left")
        self.combo_grace = ttk.Combobox(f_grace_opts, state="readonly", width=7)
        self.combo_grace.pack(side="left", padx=(2, 10))

        self.allow_delay_var = tk.BooleanVar(value=True)
        self.chk_delay = tk.Checkbutton(
            f_grace_opts,
            text="",
            variable=self.allow_delay_var,
            bg=self.card_color,
            fg=self.text_color,
            selectcolor=self.input_bg,
            activebackground=self.card_color,
            font=("Arial", 8),
        )
        self.chk_delay.pack(side="left", padx=(0, 8))

        self.warning_beep_var = tk.BooleanVar(value=True)
        self.chk_beep = tk.Checkbutton(
            f_grace_opts,
            text="",
            variable=self.warning_beep_var,
            bg=self.card_color,
            fg=self.text_color,
            selectcolor=self.input_bg,
            activebackground=self.card_color,
            font=("Arial", 8),
        )
        self.chk_beep.pack(side="left")

        # --- Section 4: Idle & Pre-Task Automation ---
        self.sec4_frame = tk.LabelFrame(
            form_card, text="", bg=self.card_color, fg="#60a5fa", font=("Arial", 9, "bold"), padx=8, pady=6
        )
        self.sec4_frame.pack(fill="x", pady=(0, 7))

        f_idle = tk.Frame(self.sec4_frame, bg=self.card_color)
        f_idle.pack(fill="x", pady=2)
        self.idle_only_var = tk.BooleanVar(value=False)
        self.chk_idle = tk.Checkbutton(
            f_idle,
            text="",
            variable=self.idle_only_var,
            bg=self.card_color,
            fg=self.text_color,
            selectcolor=self.input_bg,
            activebackground=self.card_color,
            font=("Arial", 8, "bold"),
        )
        self.chk_idle.pack(side="left")

        self.lbl_idle_need = ttk.Label(f_idle, text="", style="CardLabel.TLabel")
        self.lbl_idle_need.pack(side="left", padx=(10, 4))
        self.combo_idle_min = ttk.Combobox(f_idle, state="readonly", width=6)
        self.combo_idle_min.pack(side="left")

        f_clean = tk.Frame(self.sec4_frame, bg=self.card_color)
        f_clean.pack(fill="x", pady=2)
        self.clean_temp_var = tk.BooleanVar(value=False)
        self.chk_clean = tk.Checkbutton(
            f_clean,
            text="",
            variable=self.clean_temp_var,
            bg=self.card_color,
            fg=self.text_color,
            selectcolor=self.input_bg,
            activebackground=self.card_color,
            font=("Arial", 8),
        )
        self.chk_clean.pack(side="left")

        f_precmd = tk.Frame(self.sec4_frame, bg=self.card_color)
        f_precmd.pack(fill="x", pady=2)
        self.lbl_precmd = ttk.Label(f_precmd, text="", style="CardLabel.TLabel", width=13)
        self.lbl_precmd.pack(side="left")
        self.entry_precmd = tk.Entry(f_precmd, bg=self.input_bg, fg="#a7f3d0", insertbackground="white", relief="flat")
        self.entry_precmd.pack(side="left", fill="x", expand=True, padx=(2, 0))

        # --- Section 5: Rule Dispatch Options & Action Buttons ---
        f_ops = tk.Frame(form_card, bg=self.card_color)
        f_ops.pack(fill="x", pady=(4, 0))
        self.lbl_apply_opt = ttk.Label(f_ops, text="", style="CardLabel.TLabel")
        self.lbl_apply_opt.pack(side="left")
        self.apply_option = tk.StringVar(value="append")
        self.rb_app = tk.Radiobutton(
            f_ops,
            text="",
            variable=self.apply_option,
            value="append",
            bg=self.card_color,
            fg=self.text_color,
            selectcolor=self.input_bg,
            activebackground=self.card_color,
            font=("Arial", 8),
        )
        self.rb_app.pack(side="left", padx=4)
        self.rb_ovw = tk.Radiobutton(
            f_ops,
            text="",
            variable=self.apply_option,
            value="overwrite",
            bg=self.card_color,
            fg=self.text_color,
            selectcolor=self.input_bg,
            activebackground=self.card_color,
            font=("Arial", 8),
        )
        self.rb_ovw.pack(side="left", padx=4)

        btn_action_frame = tk.Frame(form_card, bg=self.card_color)
        btn_action_frame.pack(fill="x", pady=(8, 0))
        self.btn_send_rule = ttk.Button(
            btn_action_frame, text="", style="Green.TButton", command=self.on_send_click
        )
        self.btn_send_rule.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_clear_all = ttk.Button(
            btn_action_frame, text="", style="Red.TButton", command=self.on_clear_remote_click
        )
        self.btn_clear_all.pack(side="right")

        # --- Section 6: Parallel Immediate Power Actions ---
        self.sec_immediate = tk.LabelFrame(
            form_card, text="", bg=self.card_color, fg="#f87171", font=("Arial", 9, "bold"), padx=8, pady=6
        )
        self.sec_immediate.pack(fill="x", pady=(8, 0))

        f_imm_btns = tk.Frame(self.sec_immediate, bg=self.card_color)
        f_imm_btns.pack(fill="x")

        self.btn_imm_shutdown = tk.Button(
            f_imm_btns,
            text="",
            font=("Arial", 8, "bold"),
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            relief="flat",
            padx=6,
            pady=5,
            cursor="hand2",
            command=lambda: self.on_immediate_power_click("shutdown"),
        )
        self.btn_imm_shutdown.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_imm_reboot = tk.Button(
            f_imm_btns,
            text="",
            font=("Arial", 8, "bold"),
            bg="#d97706",
            fg="white",
            activebackground="#b45309",
            activeforeground="white",
            relief="flat",
            padx=6,
            pady=5,
            cursor="hand2",
            command=lambda: self.on_immediate_power_click("reboot"),
        )
        self.btn_imm_reboot.pack(side="left", fill="x", expand=True, padx=2)

        self.btn_imm_sleep = tk.Button(
            f_imm_btns,
            text="",
            font=("Arial", 8, "bold"),
            bg="#4f46e5",
            fg="white",
            activebackground="#4338ca",
            activeforeground="white",
            relief="flat",
            padx=6,
            pady=5,
            cursor="hand2",
            command=lambda: self.on_immediate_power_click("sleep"),
        )
        self.btn_imm_sleep.pack(side="left", fill="x", expand=True, padx=2)

        self.btn_imm_screenoff = tk.Button(
            f_imm_btns,
            text="",
            font=("Arial", 8, "bold"),
            bg="#334155",
            fg="white",
            activebackground="#1e293b",
            activeforeground="white",
            relief="flat",
            padx=6,
            pady=5,
            cursor="hand2",
            command=lambda: self.on_immediate_power_click("screenoff"),
        )
        self.btn_imm_screenoff.pack(side="left", fill="x", expand=True, padx=2)

        self.btn_imm_alarm = tk.Button(
            f_imm_btns,
            text="",
            font=("Arial", 8, "bold"),
            bg="#be185d",
            fg="white",
            activebackground="#9d174d",
            activeforeground="white",
            relief="flat",
            padx=6,
            pady=5,
            cursor="hand2",
            command=lambda: self.on_immediate_power_click("alarm"),
        )
        self.btn_imm_alarm.pack(side="left", fill="x", expand=True, padx=(3, 0))

        # ==================== [RIGHT: 50-PC Lab Fleet Control Tower] ====================
        right_frame = tk.Frame(main_content_frame, bg=self.bg_color)
        right_frame.pack(side="right", fill="both", expand=True, padx=(4, 0))

        # Top Fleet Summary + Controls
        f_right_hdr = tk.Frame(right_frame, bg=self.bg_color)
        f_right_hdr.pack(fill="x", pady=(0, 4))
        self.lbl_right_title = ttk.Label(f_right_hdr, text="", style="TLabel", font=("Arial", 10, "bold"))
        self.lbl_right_title.pack(side="left")
        self.lbl_fleet_kpi = tk.Label(
            f_right_hdr,
            text="",
            bg="#1e293b",
            fg="#38bdf8",
            font=("Consolas", 8, "bold"),
            padx=8,
            pady=2,
        )
        self.lbl_fleet_kpi.pack(side="right")

        # Row 1: Group + Onboarding Toolbar (IP Range Scan, CSV Import/Export, Group Manager)
        f_group_bar = tk.Frame(right_frame, bg=self.bg_color)
        f_group_bar.pack(fill="x", pady=(0, 4))

        self.lbl_group = ttk.Label(f_group_bar, text="", style="TLabel", font=("Arial", 8, "bold"))
        self.lbl_group.pack(side="left", padx=(0, 4))

        self.selected_group_var = tk.StringVar(value="")
        self.combo_group = ttk.Combobox(f_group_bar, textvariable=self.selected_group_var, state="readonly", font=("Arial", 8), width=20)
        self.combo_group.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.combo_group.bind("<<ComboboxSelected>>", self.on_group_filter_changed)

        self.btn_range_scan = ttk.Button(f_group_bar, text="", style="Teal.TButton", command=self.open_ip_range_scan_dialog)
        self.btn_range_scan.pack(side="left", padx=2)

        self.btn_csv_import = ttk.Button(f_group_bar, text="", style="TButton", command=self.import_csv_roster)
        self.btn_csv_import.pack(side="left", padx=2)

        self.btn_csv_export = ttk.Button(f_group_bar, text="", style="Purple.TButton", command=self.export_csv_roster)
        self.btn_csv_export.pack(side="left", padx=2)

        self.btn_manage_group = ttk.Button(f_group_bar, text="", style="TButton", command=self.open_group_manager)
        self.btn_manage_group.pack(side="right", padx=(2, 0))

        # Row 2: Search + Status Filter + Grid/Table View Mode + Cols + Auto-Poll
        f_filter_bar = tk.Frame(right_frame, bg=self.card_color, padx=6, pady=4)
        f_filter_bar.pack(fill="x", pady=(0, 4))

        self.lbl_search = tk.Label(f_filter_bar, text="", bg=self.card_color, fg="#9ca3af", font=("Arial", 8))
        self.lbl_search.pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_pc_roster_view())
        self.entry_search = tk.Entry(
            f_filter_bar,
            textvariable=self.search_var,
            bg=self.input_bg,
            fg="white",
            insertbackground="white",
            relief="flat",
            width=14,
            font=("Consolas", 8),
        )
        self.entry_search.pack(side="left", padx=(3, 6))

        self.status_filter_btns = {}
        for st_key in ("all", "online", "offline", "failed"):
            btn = tk.Button(
                f_filter_bar,
                text=st_key,
                font=("Arial", 7, "bold"),
                relief="flat",
                padx=6,
                pady=2,
                cursor="hand2",
                command=lambda k=st_key: self.set_status_filter(k),
            )
            btn.pack(side="left", padx=1)
            self.status_filter_btns[st_key] = btn

        self.auto_poll_var = tk.BooleanVar(value=False)
        self.chk_auto_poll = tk.Checkbutton(
            f_filter_bar,
            text="",
            variable=self.auto_poll_var,
            bg=self.card_color,
            fg="#34d399",
            selectcolor=self.input_bg,
            activebackground=self.card_color,
            font=("Arial", 8, "bold"),
            command=self.on_toggle_auto_poll,
        )
        self.chk_auto_poll.pack(side="right", padx=(4, 0))

        # View switcher + Cols
        self.lbl_cols = tk.Label(f_filter_bar, text="", bg=self.card_color, fg="#9ca3af", font=("Arial", 8))
        self.lbl_cols.pack(side="right", padx=(4, 2))
        self.combo_cols = ttk.Combobox(f_filter_bar, values=["5", "8", "10"], state="readonly", width=3, font=("Arial", 8))
        self.combo_cols.set("5")
        self.combo_cols.pack(side="right", padx=(0, 4))
        self.combo_cols.bind("<<ComboboxSelected>>", self.on_grid_cols_changed)

        self.btn_view_table = tk.Button(
            f_filter_bar,
            text="",
            font=("Arial", 8, "bold"),
            relief="flat",
            padx=6,
            pady=2,
            cursor="hand2",
            command=lambda: self.set_view_mode("table"),
        )
        self.btn_view_table.pack(side="right", padx=1)

        self.btn_view_grid = tk.Button(
            f_filter_bar,
            text="",
            font=("Arial", 8, "bold"),
            relief="flat",
            padx=6,
            pady=2,
            cursor="hand2",
            command=lambda: self.set_view_mode("grid"),
        )
        self.btn_view_grid.pack(side="right", padx=1)

        # Row 3: Quick Select + LAN Scan + Poll Status + Staggered WOL Bar
        f_actions_top = tk.Frame(right_frame, bg=self.bg_color)
        f_actions_top.pack(fill="x", pady=(0, 4))

        self.btn_sel_all = tk.Button(
            f_actions_top, text="", font=("Arial", 8, "bold"), bg="#334155", fg="white", relief="flat", padx=6, pady=3, cursor="hand2",
            command=self.select_all_visible,
        )
        self.btn_sel_all.pack(side="left", padx=(0, 2))

        self.btn_sel_clear = tk.Button(
            f_actions_top, text="", font=("Arial", 8), bg="#1e293b", fg="#cbd5e1", relief="flat", padx=6, pady=3, cursor="hand2",
            command=self.deselect_all_pcs,
        )
        self.btn_sel_clear.pack(side="left", padx=2)

        self.btn_sel_online = tk.Button(
            f_actions_top, text="", font=("Arial", 8), bg="#064e3b", fg="#6ee7b7", relief="flat", padx=6, pady=3, cursor="hand2",
            command=self.select_online_visible,
        )
        self.btn_sel_online.pack(side="left", padx=2)

        self.btn_sel_offline = tk.Button(
            f_actions_top, text="", font=("Arial", 8), bg="#312e81", fg="#c7d2fe", relief="flat", padx=6, pady=3, cursor="hand2",
            command=self.select_offline_visible,
        )
        self.btn_sel_offline.pack(side="left", padx=2)

        self.btn_sel_failed = tk.Button(
            f_actions_top, text="", font=("Arial", 8), bg="#7f1d1d", fg="#fecaca", relief="flat", padx=6, pady=3, cursor="hand2",
            command=self.select_failed_only,
        )
        self.btn_sel_failed.pack(side="left", padx=2)

        self.btn_query = ttk.Button(f_actions_top, text="", style="Orange.TButton", command=self.on_query_status_click)
        self.btn_query.pack(side="right", padx=(2, 0))

        self.btn_scan = ttk.Button(f_actions_top, text="", style="TButton", command=self.discover_waiting_pcs)
        self.btn_scan.pack(side="right", padx=2)

        # Row 4: Staggered WOL & Roster Keep Option
        f_wol_bar = tk.Frame(right_frame, bg=self.bg_color)
        f_wol_bar.pack(fill="x", pady=(0, 4))

        self.preserve_scanned_pcs = tk.BooleanVar(value=True)
        self.chk_preserve = tk.Checkbutton(
            f_wol_bar,
            text="",
            variable=self.preserve_scanned_pcs,
            bg=self.bg_color,
            fg=self.text_color,
            selectcolor=self.input_bg,
            activebackground=self.bg_color,
            activeforeground=self.text_color,
            font=("Arial", 8),
        )
        self.chk_preserve.pack(side="left")

        self.btn_group_wol = tk.Button(
            f_wol_bar,
            text="",
            font=("Arial", 8, "bold"),
            bg="#059669",
            fg="white",
            activebackground="#047857",
            activeforeground="white",
            relief="flat",
            padx=8,
            pady=3,
            cursor="hand2",
            command=self.on_group_wol_click,
        )
        self.btn_group_wol.pack(side="right", padx=(4, 0))

        self.combo_wol_step = ttk.Combobox(
            f_wol_bar, values=["100ms", "250ms", "500ms", "1000ms"], state="readonly", width=7, font=("Arial", 8)
        )
        self.combo_wol_step.current(1)
        self.combo_wol_step.pack(side="right", padx=(2, 4))

        self.lbl_wol_step = ttk.Label(f_wol_bar, text="", style="TLabel", font=("Arial", 8))
        self.lbl_wol_step.pack(side="right")

        # -----------------------------------------------------------------
        # DUAL ROSTER VIEW AREA (Seat Map Grid Canvas <-> Detailed Treeview)
        # -----------------------------------------------------------------
        self.roster_container = tk.Frame(right_frame, bg="#0b0f19", bd=1, relief="solid")
        self.roster_container.pack(fill="both", expand=True, pady=(0, 4))

        # View A: Seat Map Grid Canvas
        self.grid_frame = tk.Frame(self.roster_container, bg="#0b0f19")
        self.grid_canvas = tk.Canvas(self.grid_frame, bg="#0b0f19", highlightthickness=0)
        self.grid_scroll = tk.Scrollbar(self.grid_frame, orient="vertical", command=self.grid_canvas.yview)
        self.grid_inner = tk.Frame(self.grid_canvas, bg="#0b0f19", padx=6, pady=6)
        self.grid_inner.bind("<Configure>", lambda e: self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all")))
        self.grid_win_id = self.grid_canvas.create_window((0, 0), window=self.grid_inner, anchor="nw")
        self.grid_canvas.bind("<Configure>", self._on_grid_canvas_resize)
        self.grid_canvas.configure(yscrollcommand=self.grid_scroll.set)
        self.grid_canvas.pack(side="left", fill="both", expand=True)
        self.grid_scroll.pack(side="right", fill="y")

        # View B: Detailed Table View (Treeview)
        self.table_frame = tk.Frame(self.roster_container, bg="#0f131d")
        t_scroll_y = ttk.Scrollbar(self.table_frame, orient="vertical")
        t_scroll_y.pack(side="right", fill="y")
        cols = ("sel", "seat", "ip", "host", "mac", "group", "status", "timer", "rules", "ack")
        self.fleet_tree = ttk.Treeview(
            self.table_frame,
            columns=cols,
            show="headings",
            style="Fleet.Treeview",
            yscrollcommand=t_scroll_y.set,
            selectmode="browse",
        )
        t_scroll_y.config(command=self.fleet_tree.yview)
        col_widths = {
            "sel": (34, "center"),
            "seat": (56, "center"),
            "ip": (108, "w"),
            "host": (95, "w"),
            "mac": (115, "center"),
            "group": (80, "w"),
            "status": (70, "center"),
            "timer": (68, "center"),
            "rules": (44, "center"),
            "ack": (110, "w"),
        }
        for c, (w, anc) in col_widths.items():
            self.fleet_tree.column(c, width=w, minwidth=30, anchor=anc)
            self.fleet_tree.heading(c, text=c.upper(), command=lambda col=c: self.on_tree_sort(col))

        self.fleet_tree.pack(side="left", fill="both", expand=True)
        self.fleet_tree.bind("<ButtonRelease-1>", self.on_tree_click)
        self.fleet_tree.bind("<Double-Button-1>", self.on_tree_double_click)
        self.fleet_tree.bind("<Button-3>", self.show_tree_context_menu)

        # Shared Context Menu for both Seat Map Grid and Table
        self.pc_context_menu = tk.Menu(self.root, tearoff=0, bg="#1f2937", fg="white", activebackground="#3b82f6", activeforeground="white")
        self.group_submenu = tk.Menu(self.pc_context_menu, tearoff=0, bg="#1f2937", fg="white", activebackground="#3b82f6", activeforeground="white")
        self._context_target_ip = ""

        # Row 5: Batch Progress Bar + One-Click Retry Failed
        f_prog = tk.Frame(right_frame, bg=self.card_color, padx=8, pady=5)
        f_prog.pack(fill="x", pady=(0, 4))

        self.lbl_batch_status = tk.Label(
            f_prog, text="Idle", bg=self.card_color, fg="#cbd5e1", font=("Consolas", 8, "bold"), anchor="w"
        )
        self.lbl_batch_status.pack(side="left", fill="x", expand=True)

        self.btn_retry_failed = tk.Button(
            f_prog,
            text="🔁 Retry Failed (0)",
            font=("Arial", 8, "bold"),
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
            state="disabled",
            command=self.on_retry_failed_click,
        )
        self.btn_retry_failed.pack(side="right", padx=(6, 0))

        self.progress_bar = ttk.Progressbar(
            right_frame, style="Fleet.Horizontal.TProgressbar", orient="horizontal", mode="determinate", maximum=100, value=0
        )
        self.progress_bar.pack(fill="x", pady=(0, 4))

        # Row 6: ACK Console Log
        self.lbl_log_title = ttk.Label(right_frame, text="", style="TLabel", font=("Arial", 8, "bold"))
        self.lbl_log_title.pack(anchor="w", pady=(0, 2))
        self.log_text = scrolledtext.ScrolledText(
            right_frame,
            bg="#0b0f19",
            fg="#d1d5db",
            insertbackground="white",
            relief="flat",
            font=("Consolas", 8),
            height=7,
        )
        self.log_text.pack(fill="x")

        self.set_view_mode(self.view_mode, initial=True)
        self.log_append(self.t("ready_msg"))

    # ---------------------------------------------------------------------
    # Multi-Language Switching & Live Widget Re-translation
    # ---------------------------------------------------------------------
    def set_language(self, lang_code, manual=True):
        self.lang = "ko" if lang_code == "ko" else "en"
        self.lang_mode = "manual" if manual else "auto"
        self.save_pc_groups_data()
        self.apply_language()
        self.refresh_group_combobox()
        self.refresh_pc_roster_view()

    def reset_language_auto(self):
        self.detected_os_lang = detect_os_lang()
        self.set_language(self.detected_os_lang, manual=False)
        self.log_append(
            self.L(
                f"🌐 OS 언어 자동 감지 복원: {self.lang.upper()}",
                f"🌐 Restored OS auto-detected language: {self.lang.upper()}",
            )
        )

    def apply_language(self):
        self.root.title(self.t("window_title"))
        self.title_lbl.config(text=self.t("header_title"))
        self.local_ip_lbl.config(text=f"{self.t('my_ip')}: {get_local_ip()}")
        self.btn_license.config(text=self.t("license_btn"))

        # Language switcher highlight
        self.btn_lang_ko.config(
            bg="#2563eb" if self.lang == "ko" else "#0f172a",
            fg="white" if self.lang == "ko" else "#94a3b8",
        )
        self.btn_lang_en.config(
            bg="#2563eb" if self.lang == "en" else "#0f172a",
            fg="white" if self.lang == "en" else "#94a3b8",
        )
        self.btn_lang_auto.config(
            text=f"{self.t('lang_auto')}({self.detected_os_lang.upper()})" if self.lang_mode == "auto" else self.t("lang_manual"),
            bg="#059669" if self.lang_mode == "auto" else "#334155",
            fg="white" if self.lang_mode == "auto" else "#cbd5e1",
        )

        self.sec1_frame.config(text=self.t("sec1_title"))
        self.lbl_target_ip.config(text=self.t("target_ip_lbl"))
        self.lbl_port.config(text=self.t("port_lbl"))
        self.lbl_token.config(text=self.t("token_lbl"))
        self.chk_show_token.config(text=self.t("show_chk"))
        self.btn_send_token_quick.config(text=self.t("btn_token_quick"))
        self.btn_emergency_recovery.config(text=self.t("btn_recovery"))

        # Profiles
        self.sec_profile_frame.config(text=self.t("sec_profile_title"))
        self.lbl_profile_sel.config(text=self.t("profile_select_lbl"))
        self.btn_deploy_profile.config(text=self.t("btn_deploy_profile"))
        prof_names = [p["name_ko"] if self.lang == "ko" else p["name_en"] for p in LAB_SCHEDULE_PROFILES]
        cur_p_idx = max(0, self.combo_profile.current())
        self.combo_profile["values"] = prof_names
        if cur_p_idx < len(prof_names):
            self.combo_profile.current(cur_p_idx)
        self.on_profile_selected()

        # Section 2
        self.sec2_frame.config(text=self.t("sec2_title"))
        self.lbl_rule_name.config(text=self.t("rule_name_lbl"))
        preset_header = "📋 자주 쓰는 제목 프리셋 (10종)..." if self.lang == "ko" else "📋 Quick Title Presets (10)..."
        preset_vals = [preset_header] + [
            f"{i+1}. {p['title_ko'] if self.lang == 'ko' else p['title_en']}"
            for i, p in enumerate(POPULAR_SCHEDULE_PRESETS)
        ]
        self.preset_combo["values"] = preset_vals
        self.preset_combo.current(0)

        self.lbl_mode.config(text=self.t("mode_lbl"))
        mode_vals = (
            [
                "🔴 시스템 종료 (shutdown)",
                "🔄 다시 시작 (reboot)",
                "🌙 절전 모드 (sleep)",
                "💤 최대 절전 (hibernate)",
                "🔒 화면 잠금 (lock)",
                "🖥️ 화면 끄기 (screenoff)",
                "🚪 로그아웃 (logout)",
                "⏰ 사운드 알람 (alarm)",
            ]
            if self.lang == "ko"
            else [
                "🔴 Shutdown (shutdown)",
                "🔄 Reboot (reboot)",
                "🌙 Sleep (sleep)",
                "💤 Hibernate (hibernate)",
                "🔒 Lock Screen (lock)",
                "🖥️ Screen Off (screenoff)",
                "🚪 Sign Out (logout)",
                "⏰ Sound Alarm (alarm)",
            ]
        )
        cur_m_idx = max(0, self.combo_mode.current())
        self.combo_mode["values"] = mode_vals
        if cur_m_idx < len(mode_vals):
            self.combo_mode.current(cur_m_idx)

        self.chk_force.config(text=self.t("force_close_chk"))
        self.lbl_exec_time.config(text=self.t("exec_time_lbl"))
        self.lbl_hour_unit.config(text=self.t("hour_unit"))
        self.lbl_min_unit.config(text=self.t("min_unit"))
        self.lbl_days.config(text=self.t("days_lbl"))
        day_names = ["월", "화", "수", "목", "금", "토", "일"] if self.lang == "ko" else ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for chk, nm in zip(self.day_chks, day_names):
            chk.config(text=nm)

        # Section 3
        self.sec3_frame.config(text=self.t("sec3_title"))
        self.lbl_warn_msg.config(text=self.t("warn_msg_lbl"))
        self.lbl_grace.config(text=self.t("grace_lbl"))
        grace_vals = ["5초", "10초", "30초", "60초", "120초"] if self.lang == "ko" else ["5s", "10s", "30s", "60s", "120s"]
        g_idx = max(0, self.combo_grace.current() if self.combo_grace.current() >= 0 else 1)
        self.combo_grace["values"] = grace_vals
        self.combo_grace.current(min(g_idx, len(grace_vals) - 1))
        self.chk_delay.config(text=self.t("allow_delay_chk"))
        self.chk_beep.config(text=self.t("beep_chk"))

        # Section 4
        self.sec4_frame.config(text=self.t("sec4_title"))
        self.chk_idle.config(text=self.t("idle_only_chk"))
        self.lbl_idle_need.config(text=self.t("idle_need_lbl"))
        idle_vals = ["5분", "10분", "15분", "30분", "60분"] if self.lang == "ko" else ["5m", "10m", "15m", "30m", "60m"]
        i_idx = max(0, self.combo_idle_min.current() if self.combo_idle_min.current() >= 0 else 2)
        self.combo_idle_min["values"] = idle_vals
        self.combo_idle_min.current(min(i_idx, len(idle_vals) - 1))
        self.chk_clean.config(text=self.t("clean_temp_chk"))
        self.lbl_precmd.config(text=self.t("precmd_lbl"))

        # Section 5 & Immediate
        self.lbl_apply_opt.config(text=self.t("apply_opt_lbl"))
        self.rb_app.config(text=self.t("opt_append"))
        self.rb_ovw.config(text=self.t("opt_overwrite"))
        self.btn_send_rule.config(text=self.t("btn_send_rule"))
        self.btn_clear_all.config(text=self.t("btn_clear_all"))

        self.sec_immediate.config(text=self.t("sec_imm_title"))
        self.btn_imm_shutdown.config(text=self.t("btn_imm_shutdown"))
        self.btn_imm_reboot.config(text=self.t("btn_imm_reboot"))
        self.btn_imm_sleep.config(text=self.t("btn_imm_sleep"))
        self.btn_imm_screenoff.config(text=self.t("btn_imm_screenoff"))
        self.btn_imm_alarm.config(text=self.t("btn_imm_alarm"))

        # Right panel
        self.lbl_right_title.config(text=self.t("right_title"))
        self.lbl_group.config(text=self.t("grp_lbl"))
        self.btn_manage_group.config(text=self.t("btn_manage_grp"))
        self.btn_range_scan.config(text=self.t("btn_range_scan"))
        self.btn_csv_import.config(text=self.t("btn_csv_import"))
        self.btn_csv_export.config(text=self.t("btn_csv_export"))
        self.lbl_search.config(text=self.t("search_lbl"))
        self.chk_auto_poll.config(text=self.t("autopoll_chk"))
        self.lbl_cols.config(text=self.t("cols_lbl"))
        self.btn_view_grid.config(text=self.t("view_grid"))
        self.btn_view_table.config(text=self.t("view_table"))

        for st_key, btn in self.status_filter_btns.items():
            btn.config(text=self.t(f"filter_{st_key}"))
        self._update_status_filter_styles()
        self._update_view_mode_styles()

        self.btn_sel_all.config(text=self.t("sel_all_vis"))
        self.btn_sel_clear.config(text=self.t("sel_clear"))
        self.btn_sel_online.config(text=self.t("sel_online"))
        self.btn_sel_offline.config(text=self.t("sel_offline"))
        self.btn_sel_failed.config(text=self.t("sel_failed"))
        if not self.batch_in_progress:
            self.btn_scan.config(text=self.t("btn_scan"))
        self.btn_query.config(text=self.t("btn_query"))
        self.chk_preserve.config(text=self.t("preserve_chk"))
        self.lbl_wol_step.config(text=self.t("wol_step_lbl"))
        self.btn_group_wol.config(text=self.t("btn_group_wol"))
        self.lbl_log_title.config(text=self.t("log_title"))
        self._update_retry_button()

        # Table Headings
        headings = (
            {
                "sel": "✓",
                "seat": "좌석",
                "ip": "IP 주소",
                "host": "호스트명",
                "mac": "MAC (WOL)",
                "group": "그룹",
                "status": "상태",
                "timer": "타이머",
                "rules": "규칙",
                "ack": "최근 응답",
            }
            if self.lang == "ko"
            else {
                "sel": "✓",
                "seat": "Seat",
                "ip": "IP Address",
                "host": "Hostname",
                "mac": "MAC (WOL)",
                "group": "Group",
                "status": "Status",
                "timer": "Timer",
                "rules": "Rules",
                "ack": "Last ACK",
            }
        )
        for col_id, txt in headings.items():
            self.fleet_tree.heading(col_id, text=txt)

    def on_profile_selected(self, event=None):
        idx = self.combo_profile.current()
        if 0 <= idx < len(LAB_SCHEDULE_PROFILES):
            prof = LAB_SCHEDULE_PROFILES[idx]
            desc = prof["desc_ko"] if self.lang == "ko" else prof["desc_en"]
            self.lbl_profile_desc.config(text=desc)

    def on_preset_title_selected(self, event=None):
        idx = self.preset_combo.current()
        if idx > 0:
            preset = POPULAR_SCHEDULE_PRESETS[idx - 1]
            self.entry_label.delete(0, tk.END)
            self.entry_label.insert(0, preset["title_ko"] if self.lang == "ko" else preset["title_en"])
            for i, k in enumerate(self.mode_keys):
                if k == preset.get("mode"):
                    self.combo_mode.current(i)
                    break
            self.entry_hour.delete(0, tk.END)
            self.entry_hour.insert(0, preset["hour"])
            self.entry_min.delete(0, tk.END)
            self.entry_min.insert(0, preset["min"])
            for d_i, var in enumerate(self.day_vars):
                var.set(d_i in preset["days"])
            self.entry_warn_msg.delete(0, tk.END)
            self.entry_warn_msg.insert(0, preset["warn_ko"] if self.lang == "ko" else preset["warn_en"])
            self.idle_only_var.set(preset["idle"])
            self.preset_combo.current(0)

    def log_append(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")

        def _do_insert():
            self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
            self.log_text.see(tk.END)

        try:
            self.root.after(0, _do_insert)
        except Exception:
            pass

    # ---------------------------------------------------------------------
    # PC Groups & Lab Roster Persistence
    # ---------------------------------------------------------------------
    def load_pc_groups_data(self):
        self.groups_list = [
            {"id": "all", "name": "📁 전체 PC (All)", "is_system": True},
            {"id": "default", "name": "🏫 기본 그룹 (Default)", "is_system": False},
        ]
        self.pc_records = {}
        self.pc_checked_status = {}
        self.lang_pref = {}

        if os.path.exists(GROUPS_CONFIG_FILE):
            try:
                with open(GROUPS_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                loaded_groups = data.get("groups", [])
                if loaded_groups:
                    if not any(g.get("id") == "all" for g in loaded_groups):
                        loaded_groups.insert(0, {"id": "all", "name": "📁 전체 PC (All)", "is_system": True})
                    self.groups_list = loaded_groups
                loaded_pcs = data.get("pcs", {})
                if isinstance(loaded_pcs, dict):
                    self.pc_records = loaded_pcs
                self.lang_pref = data.get("lang_pref", {})
            except Exception:
                pass

    def save_pc_groups_data(self):
        try:
            data = {
                "groups": self.groups_list,
                "pcs": self.pc_records,
                "lang_pref": {
                    "mode": getattr(self, "lang_mode", "auto"),
                    "lang": getattr(self, "lang", "ko"),
                },
            }
            os.makedirs(os.path.dirname(GROUPS_CONFIG_FILE), exist_ok=True)
            with open(GROUPS_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_group_by_id(self, gid):
        for g in self.groups_list:
            if g.get("id") == gid:
                return g
        return None

    def get_group_by_name(self, name):
        for g in self.groups_list:
            if g.get("name") == name or g.get("name", "").split(" (")[0] == name:
                return g
        return None

    def get_current_selected_group_id(self):
        sel_name = self.selected_group_var.get()
        g = self.get_group_by_name(sel_name)
        return g["id"] if g else "all"

    def refresh_group_combobox(self):
        unit = "대" if self.lang == "ko" else " PCs"
        names = []
        for g in self.groups_list:
            gid = g["id"]
            cnt = len(self.pc_records) if gid == "all" else sum(1 for p in self.pc_records.values() if p.get("group") == gid)
            names.append(f"{g['name']} ({cnt}{unit})")

        cur_val = self.selected_group_var.get()
        self.combo_group["values"] = names
        matched = False
        if cur_val:
            prefix = cur_val.split(" (")[0]
            for n in names:
                if n.startswith(prefix):
                    self.selected_group_var.set(n)
                    matched = True
                    break
        if not matched and names:
            self.selected_group_var.set(names[0])

    def _get_pc_status_state(self, ip):
        """Returns ('failed'|'online'|'offline', telemetry_dict)"""
        tele = self.pc_live_telemetry.get(ip, {})
        if ip in self.failed_targets or tele.get("status") == "failed":
            return "failed", tele
        beacon = DISCOVERED_CLIENTS.get(ip, {})
        beacon_fresh = bool(beacon) and (time.time() - beacon.get("last_seen", 0) < 90)
        if tele.get("status") == "online" or ip in self.last_scanned_active_ips or beacon_fresh:
            return "online", tele
        return "offline", tele

    def _get_visible_ips(self):
        cur_gid = self.get_current_selected_group_id()
        all_ips = set(self.pc_records.keys())
        if self.preserve_scanned_pcs.get():
            all_ips.update(self.last_scanned_active_ips)
            all_ips.update(DISCOVERED_CLIENTS.keys())

        q = self.search_var.get().strip().lower()
        filtered = []
        for ip in all_ips:
            rec = self.pc_records.get(ip, {})
            pc_gid = rec.get("group", "default")
            if cur_gid != "all" and pc_gid != cur_gid:
                continue

            st, tele = self._get_pc_status_state(ip)
            if self.status_filter != "all" and st != self.status_filter:
                continue

            if q:
                host = (rec.get("hostname") or DISCOVERED_CLIENTS.get(ip, {}).get("hostname", "")).lower()
                seat = str(rec.get("seat_no", "")).lower()
                memo = str(rec.get("memo", "")).lower()
                if q not in ip.lower() and q not in host and q not in seat and q not in memo:
                    continue

            filtered.append(ip)

        def _row_sort_val(ip_item):
            rec = self.pc_records.get(ip_item, {})
            st, tele = self._get_pc_status_state(ip_item)
            if self.sort_col == "seat":
                seat_raw = str(rec.get("seat_no", ""))
                m = re.search(r"(\d+)", seat_raw)
                return (0, int(m.group(1)), seat_raw, ip_sort_key(ip_item)) if m else (1, 9999, seat_raw, ip_sort_key(ip_item))
            if self.sort_col == "ip":
                return ip_sort_key(ip_item)
            if self.sort_col == "host":
                return (rec.get("hostname") or "").lower()
            if self.sort_col == "mac":
                return (rec.get("mac") or "").lower()
            if self.sort_col == "status":
                return {"online": 0, "failed": 1, "offline": 2}.get(st, 3)
            if self.sort_col == "rules":
                return tele.get("rules_count", 0)
            if self.sort_col == "timer":
                return tele.get("remaining_seconds", 0)
            return ip_sort_key(ip_item)

        filtered.sort(key=_row_sort_val, reverse=self.sort_reverse)
        return filtered

    def set_status_filter(self, st_key):
        self.status_filter = st_key
        self._update_status_filter_styles()
        self.refresh_pc_roster_view()

    def _update_status_filter_styles(self):
        colors = {
            "all": "#2563eb",
            "online": "#059669",
            "offline": "#475569",
            "failed": "#dc2626",
        }
        for k, btn in self.status_filter_btns.items():
            active = k == self.status_filter
            btn.config(
                bg=colors.get(k, "#2563eb") if active else "#0f172a",
                fg="white" if active else "#94a3b8",
            )

    def set_view_mode(self, mode, initial=False):
        self.view_mode = mode
        if mode == "grid":
            self.table_frame.pack_forget()
            self.grid_frame.pack(fill="both", expand=True)
        else:
            self.grid_frame.pack_forget()
            self.table_frame.pack(fill="both", expand=True)
        self._update_view_mode_styles()
        if not initial:
            self.refresh_pc_roster_view()

    def _update_view_mode_styles(self):
        self.btn_view_grid.config(
            bg="#2563eb" if self.view_mode == "grid" else "#0f172a",
            fg="white" if self.view_mode == "grid" else "#94a3b8",
        )
        self.btn_view_table.config(
            bg="#2563eb" if self.view_mode == "table" else "#0f172a",
            fg="white" if self.view_mode == "table" else "#94a3b8",
        )

    def on_grid_cols_changed(self, event=None):
        try:
            self.grid_cols = int(self.combo_cols.get())
        except Exception:
            self.grid_cols = 5
        self.refresh_pc_roster_view()

    def _on_grid_canvas_resize(self, event):
        self.grid_canvas.itemconfig(self.grid_win_id, width=event.width)

    def refresh_pc_roster_view(self):
        visible_ips = self._get_visible_ips()

        # KPI counts across full candidate roster
        all_candidates = set(self.pc_records.keys())
        if self.preserve_scanned_pcs.get():
            all_candidates.update(self.last_scanned_active_ips)
            all_candidates.update(DISCOVERED_CLIENTS.keys())
        online_c = sum(1 for ip in all_candidates if self._get_pc_status_state(ip)[0] == "online")
        fail_c = len([ip for ip in self.failed_targets if ip in all_candidates])
        chk_c = sum(1 for ip in all_candidates if self.pc_checked_status.get(ip, False))
        self.lbl_fleet_kpi.config(
            text=f"Total {len(all_candidates)} · Online {online_c} · Sel {chk_c} · Fail {fail_c}"
        )

        # Render Active View
        if self.view_mode == "grid":
            self._render_seat_grid(visible_ips)
        else:
            self._render_fleet_table(visible_ips)

        self._update_retry_button()

    def _format_rem_timer(self, tele):
        if tele.get("timer_running") and tele.get("remaining_seconds", 0) > 0:
            sec = int(tele["remaining_seconds"])
            m, s = divmod(sec, 60)
            h, m = divmod(m, 60)
            return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
        return "-"

    def _render_seat_grid(self, visible_ips):
        for child in self.grid_inner.winfo_children():
            child.destroy()
        self.grid_tile_widgets.clear()

        if not visible_ips:
            empty_msg = (
                "표시할 PC가 없습니다. [🌐 대역 스캔], [📥 CSV 등록] 또는 [🔍 LAN 스캔]으로 컴퓨터실 PC를 등록하십시오."
                if self.lang == "ko"
                else "No PCs match filter. Use [🌐 IP Range], [📥 CSV Import], or [🔍 LAN Scan] to onboard PCs."
            )
            tk.Label(
                self.grid_inner,
                text=empty_msg,
                bg="#0b0f19",
                fg="#94a3b8",
                font=("Arial", 9),
                pady=40,
                wraplength=480,
            ).pack(fill="both", expand=True)
            return

        cols = max(3, min(10, self.grid_cols))
        for c in range(cols):
            self.grid_inner.columnconfigure(c, weight=1, uniform="seatcol")

        for idx, ip in enumerate(visible_ips):
            r = idx // cols
            c = idx % cols
            rec = self.pc_records.get(ip, {})
            st, tele = self._get_pc_status_state(ip)
            checked = self.pc_checked_status.get(ip, False)

            seat_no = rec.get("seat_no") or format_seat_no(idx + 1)
            host = rec.get("hostname") or DISCOVERED_CLIENTS.get(ip, {}).get("hostname", "") or f"PC-{ip.split('.')[-1]}"
            mac = rec.get("mac") or DISCOVERED_CLIENTS.get(ip, {}).get("mac", "")
            rules_cnt = tele.get("rules_count", DISCOVERED_CLIENTS.get(ip, {}).get("rules_count", 0))
            timer_str = self._format_rem_timer(tele)
            is_self = is_local_admin_ip(ip)

            if checked:
                tile_bg = "#1e3a5f"
                border_col = "#38bdf8"
            elif st == "failed":
                tile_bg = "#35161b"
                border_col = "#ef4444"
            elif st == "online":
                tile_bg = "#122620"
                border_col = "#10b981"
            else:
                tile_bg = "#171c28"
                border_col = "#334155"

            tile = tk.Frame(
                self.grid_inner,
                bg=tile_bg,
                highlightbackground=border_col,
                highlightthickness=2 if checked else 1,
                padx=5,
                pady=4,
                cursor="hand2",
            )
            tile.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)

            # Top row: Seat badge + Status text
            top = tk.Frame(tile, bg=tile_bg)
            top.pack(fill="x")
            chk_glyph = "☑" if checked else "☐"
            seat_lbl = tk.Label(
                top,
                text=f"{chk_glyph} #{seat_no}" + (" 👑" if is_self else ""),
                bg=tile_bg,
                fg="#f8fafc" if checked else "#e2e8f0",
                font=("Consolas", 8, "bold"),
            )
            seat_lbl.pack(side="left")

            st_color = "#34d399" if st == "online" else ("#f87171" if st == "failed" else "#94a3b8")
            st_short = "ON" if st == "online" else ("ERR" if st == "failed" else "OFF")
            st_lbl = tk.Label(top, text=st_short, bg=tile_bg, fg=st_color, font=("Consolas", 7, "bold"))
            st_lbl.pack(side="right")

            ip_lbl = tk.Label(tile, text=ip, bg=tile_bg, fg="#93c5fd", font=("Consolas", 8, "bold"), anchor="w")
            ip_lbl.pack(fill="x")

            meta_bits = []
            if host:
                meta_bits.append(host[:11])
            if timer_str != "-":
                meta_bits.append(f"⏱{timer_str}")
            elif rules_cnt:
                meta_bits.append(f"R:{rules_cnt}")
            elif mac:
                meta_bits.append("WOL")
            meta_lbl = tk.Label(
                tile,
                text=" · ".join(meta_bits) if meta_bits else "-",
                bg=tile_bg,
                fg="#cbd5e1" if timer_str != "-" else "#94a3b8",
                font=("Arial", 7),
                anchor="w",
            )
            meta_lbl.pack(fill="x")

            for w in (tile, top, seat_lbl, st_lbl, ip_lbl, meta_lbl):
                w.bind("<Button-1>", lambda e, target_ip=ip: self.toggle_pc_selection(target_ip))
                w.bind("<Double-Button-1>", lambda e, target_ip=ip: self.open_edit_pc_dialog(ip=target_ip))
                w.bind("<Button-3>", lambda e, target_ip=ip: self.show_context_menu_for_ip(e, target_ip))

    def _render_fleet_table(self, visible_ips):
        for item in self.fleet_tree.get_children():
            self.fleet_tree.delete(item)

        for idx, ip in enumerate(visible_ips):
            rec = self.pc_records.get(ip, {})
            st, tele = self._get_pc_status_state(ip)
            checked = self.pc_checked_status.get(ip, False)

            chk_mark = "✓" if checked else ""
            seat_no = rec.get("seat_no") or format_seat_no(idx + 1)
            hostname = rec.get("hostname") or DISCOVERED_CLIENTS.get(ip, {}).get("hostname", "") or f"PC-{ip.split('.')[-1]}"
            if is_local_admin_ip(ip):
                hostname = f"👑 {hostname}"
            mac = rec.get("mac") or DISCOVERED_CLIENTS.get(ip, {}).get("mac", "") or "-"
            gid = rec.get("group", "default")
            g_obj = self.get_group_by_id(gid)
            g_name = g_obj["name"].split(" (")[0] if g_obj else gid

            if st == "online":
                st_disp = self.L("🟢 온라인", "🟢 Online")
            elif st == "failed":
                st_disp = self.L("🔴 실패", "🔴 Failed")
            else:
                st_disp = self.L("⚪ 오프라인", "⚪ Offline")

            timer_str = self._format_rem_timer(tele)
            rules_cnt = tele.get("rules_count", DISCOVERED_CLIENTS.get(ip, {}).get("rules_count", 0))
            lat = tele.get("latency_ms")
            if st == "failed" and tele.get("last_err"):
                ack_str = str(tele["last_err"])[:28]
            elif lat:
                ack_str = f"{lat}ms"
            elif tele.get("last_ack"):
                ack_str = str(tele["last_ack"])[:28]
            else:
                ack_str = "-"

            self.fleet_tree.insert(
                "",
                tk.END,
                iid=ip,
                values=(chk_mark, seat_no, ip, hostname, mac, g_name, st_disp, timer_str, rules_cnt, ack_str),
            )

    def toggle_pc_selection(self, ip):
        self.pc_checked_status[ip] = not self.pc_checked_status.get(ip, False)
        self.refresh_pc_roster_view()
        self.update_entry_ip_from_checked()

    def on_tree_sort(self, col):
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col
            self.sort_reverse = False
        self.refresh_pc_roster_view()

    def on_tree_click(self, event):
        row_id = self.fleet_tree.identify_row(event.y)
        if row_id and row_id in self.pc_records or row_id in self.last_scanned_active_ips or row_id in DISCOVERED_CLIENTS:
            self.toggle_pc_selection(row_id)

    def on_tree_double_click(self, event):
        row_id = self.fleet_tree.identify_row(event.y)
        if row_id:
            self.open_edit_pc_dialog(ip=row_id)

    def show_tree_context_menu(self, event):
        row_id = self.fleet_tree.identify_row(event.y)
        if row_id:
            self.fleet_tree.selection_set(row_id)
            self.show_context_menu_for_ip(event, row_id)

    def show_context_menu_for_ip(self, event, ip):
        self._context_target_ip = ip
        self.pc_context_menu.delete(0, tk.END)
        self.group_submenu.delete(0, tk.END)

        cur_gid = self.pc_records.get(ip, {}).get("group", "default")
        for g in self.groups_list:
            if g.get("id") == "all":
                continue
            gid = g["id"]
            prefix = "✓ " if gid == cur_gid else "   "
            self.group_submenu.add_command(
                label=f"{prefix}{g['name']}",
                command=lambda target_ip=ip, target_gid=gid: self.move_pc_to_group(target_ip, target_gid),
            )
        self.group_submenu.add_separator()
        self.group_submenu.add_command(
            label=self.L("➕ 새 그룹 생성 및 이동...", "➕ Create Group & Move..."),
            command=lambda target_ip=ip: self.create_group_and_move_pc(target_ip),
        )

        self.pc_context_menu.add_command(
            label=self.L(f"⚡ [{ip}] 원격 부팅 (WOL)", f"⚡ Wake [{ip}] (WOL)"),
            command=lambda target_ip=ip: self.on_single_pc_wol(target_ip),
        )
        self.pc_context_menu.add_cascade(
            label=self.L("📁 소속 그룹 이동", "📁 Move to Group"), menu=self.group_submenu
        )
        self.pc_context_menu.add_command(
            label=self.L("✏️ PC 정보 · 좌석 · MAC 편집...", "✏️ Edit PC / Seat / MAC..."),
            command=lambda target_ip=ip: self.open_edit_pc_dialog(ip=target_ip),
        )
        self.pc_context_menu.add_separator()
        self.pc_context_menu.add_command(
            label=self.L("🛑 즉시 종료 (Shutdown)", "🛑 Shutdown Now"),
            command=lambda target_ip=ip: self.on_context_menu_power(target_ip, "shutdown"),
        )
        self.pc_context_menu.add_command(
            label=self.L("🔄 즉시 재시작 (Reboot)", "🔄 Reboot Now"),
            command=lambda target_ip=ip: self.on_context_menu_power(target_ip, "reboot"),
        )
        self.pc_context_menu.add_command(
            label=self.L("🌙 절전 모드 (Sleep)", "🌙 Sleep"),
            command=lambda target_ip=ip: self.on_context_menu_power(target_ip, "sleep"),
        )
        self.pc_context_menu.add_command(
            label=self.L("📺 화면 끄기 (Screen Off)", "📺 Screen Off"),
            command=lambda target_ip=ip: self.on_context_menu_power(target_ip, "screenoff"),
        )
        self.pc_context_menu.add_separator()
        self.pc_context_menu.add_command(
            label=self.L("📊 이 PC 상태 조회", "📊 Query PC Status"),
            command=lambda target_ip=ip: self._run_parallel_query([target_ip]),
        )
        self.pc_context_menu.add_command(
            label=self.L("❌ 목록에서 제거", "❌ Remove from Roster"),
            command=lambda target_ip=ip: self.remove_single_pc(target_ip),
        )
        try:
            self.pc_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.pc_context_menu.grab_release()

    def on_group_filter_changed(self, event=None):
        self.refresh_pc_roster_view()
        self.update_entry_ip_from_checked()

    def select_all_visible(self):
        vis = self._get_visible_ips()
        for ip in vis:
            self.pc_checked_status[ip] = True
        self.refresh_pc_roster_view()
        self.update_entry_ip_from_checked()
        self.log_append(self.L(f"☑️ 표시된 PC {len(vis)}대 일괄 선택됨", f"☑️ Selected {len(vis)} visible PC(s)"))

    def select_online_visible(self):
        vis = [ip for ip in self._get_visible_ips() if self._get_pc_status_state(ip)[0] == "online"]
        for ip in vis:
            self.pc_checked_status[ip] = True
        self.refresh_pc_roster_view()
        self.update_entry_ip_from_checked()
        self.log_append(self.L(f"🟢 온라인 PC {len(vis)}대 선택됨", f"🟢 Selected {len(vis)} online PC(s)"))

    def select_offline_visible(self):
        vis = [ip for ip in self._get_visible_ips() if self._get_pc_status_state(ip)[0] == "offline"]
        for ip in vis:
            self.pc_checked_status[ip] = True
        self.refresh_pc_roster_view()
        self.update_entry_ip_from_checked()
        self.log_append(self.L(f"⚪ 오프라인(WOL 대상) PC {len(vis)}대 선택됨", f"⚪ Selected {len(vis)} offline PC(s)"))

    def select_failed_only(self):
        self.pc_checked_status.clear()
        for ip in self.failed_targets:
            self.pc_checked_status[ip] = True
        self.refresh_pc_roster_view()
        self.update_entry_ip_from_checked()
        self.log_append(self.L(f"🔴 실패 PC {len(self.failed_targets)}대 재선택됨", f"🔴 Selected {len(self.failed_targets)} failed PC(s)"))

    def deselect_all_pcs(self):
        self.pc_checked_status.clear()
        self.refresh_pc_roster_view()
        self.update_entry_ip_from_checked()

    def update_entry_ip_from_checked(self):
        checked = sorted([ip for ip, chk in self.pc_checked_status.items() if chk], key=ip_sort_key)
        self.entry_ip.config(state="normal")
        self.entry_ip.delete(0, tk.END)
        if checked:
            self.entry_ip.insert(0, ", ".join(checked))
            self.entry_ip.config(state="readonly", readonlybackground="#1e293b", fg="#38bdf8", disabledforeground="#38bdf8")
        else:
            self.entry_ip.config(state="normal", bg=self.input_bg, fg="#38bdf8")

    def get_target_ips(self):
        checked = sorted([ip for ip, chk in self.pc_checked_status.items() if chk], key=ip_sort_key)
        if checked:
            return checked
        self.entry_ip.config(state="normal")
        raw = self.entry_ip.get().strip()
        if not raw or raw == "192.168.0.":
            return None
        parsed = [x.strip() for x in raw.split(",") if x.strip() and x.strip() != "192.168.0."]
        return parsed if parsed else None

    def check_admin_pc_in_targets(self, target_ips):
        if not target_ips:
            return False, "", ""
        local_ips = get_all_local_ips()
        my_hostname = socket.gethostname().upper()
        for ip in target_ips:
            ip_clean = ip.strip()
            if ip_clean in local_ips:
                c_host = DISCOVERED_CLIENTS.get(ip_clean, {}).get("hostname") or socket.gethostname()
                return True, ip_clean, c_host
            c_host = (DISCOVERED_CLIENTS.get(ip_clean, {}).get("hostname") or "").strip().upper()
            if c_host and c_host == my_hostname:
                return True, ip_clean, c_host
        return False, "", ""

    # ---------------------------------------------------------------------
    # Bounded Parallel Batch Execution Engine & Retry Failed (N)
    # ---------------------------------------------------------------------
    def _update_progress_ui(self, done, total, ok_cnt, fail_cnt, label):
        pct = int((done / total) * 100) if total > 0 else 0
        self.progress_bar["value"] = pct
        self.lbl_batch_status.config(
            text=f"{label}: {done}/{total} · OK {ok_cnt} · Fail {fail_cnt}"
        )

    def _update_retry_button(self):
        cnt = len(self.failed_targets)
        self.btn_retry_failed.config(
            text=f"{self.t('btn_retry_failed')} ({cnt})",
            state="normal" if cnt > 0 and not self.batch_in_progress else "disabled",
            bg="#dc2626" if cnt > 0 else "#334155",
        )

    def _execute_parallel_batch(self, label, target_ips, worker_fn, retry_payload_desc=None, on_complete=None):
        """
        Bounded ThreadPoolExecutor(max_workers=24) 일괄 전송 + 실시간 진행률 + 실패 목록 추적
        worker_fn(ip) -> (success: bool, telemetry_update: dict, log_line: str)
        """
        if not target_ips:
            return

        self.batch_in_progress = True
        self.last_batch_context = {
            "label": label,
            "worker_fn": worker_fn,
            "desc": retry_payload_desc or label,
        }
        total = len(target_ips)
        self._update_progress_ui(0, total, 0, 0, label)
        self._update_retry_button()
        self.root.config(cursor="watch")

        def coordinator():
            done = 0
            ok_cnt = 0
            fail_cnt = 0
            new_failed = []
            max_workers = min(24, max(4, total))

            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                future_map = {pool.submit(worker_fn, ip): ip for ip in target_ips}
                for fut in as_completed(future_map):
                    ip = future_map[fut]
                    done += 1
                    try:
                        success, t_upd, log_msg = fut.result()
                    except Exception as ex:
                        success = False
                        t_upd = {"status": "failed", "last_err": str(ex)}
                        log_msg = f"❌ [{ip}] {ex}"

                    if success:
                        ok_cnt += 1
                        self.last_scanned_active_ips.add(ip)
                    else:
                        fail_cnt += 1
                        new_failed.append(ip)

                    cur = self.pc_live_telemetry.get(ip, {})
                    cur.update(t_upd)
                    self.pc_live_telemetry[ip] = cur
                    if log_msg:
                        self.log_append(log_msg)

                    self.root.after(
                        0,
                        lambda d=done, t=total, o=ok_cnt, f=fail_cnt, lb=label: self._update_progress_ui(d, t, o, f, lb),
                    )

            def finish():
                self.batch_in_progress = False
                self.failed_targets = sorted(new_failed, key=ip_sort_key)
                self.root.config(cursor="")
                self.refresh_pc_roster_view()
                if on_complete:
                    on_complete(ok_cnt, fail_cnt, new_failed)

            self.root.after(0, finish)

        threading.Thread(target=coordinator, daemon=True).start()

    def on_retry_failed_click(self):
        if not self.failed_targets or not getattr(self, "last_batch_context", None):
            return
        retry_ips = list(self.failed_targets)
        ctx = self.last_batch_context
        self.log_append(
            self.L(
                f"🔁 실패한 {len(retry_ips)}대 PC에 대해 [{ctx['label']}] 원클릭 재시도를 시작합니다...",
                f"🔁 Retrying [{ctx['label']}] for {len(retry_ips)} failed PC(s)...",
            )
        )
        self._execute_parallel_batch(f"Retry {ctx['label']}", retry_ips, ctx["worker_fn"])

    # ---------------------------------------------------------------------
    # Live Discovery, IP Range Scan & Periodic Polling (15s)
    # ---------------------------------------------------------------------
    def discover_waiting_pcs(self):
        self.btn_scan.config(state="disabled", text=self.L("🔍 스캔 중...", "🔍 Scanning..."))
        local_ip = get_local_ip()
        local_base = "192.168.0." if local_ip == "127.0.0.1" else ".".join(local_ip.split(".")[:3]) + "."
        candidates = [f"{local_base}{i}" for i in range(1, 255)]
        if "127.0.0.1" not in candidates:
            candidates.append("127.0.0.1")
        self._scan_ip_list(candidates, auto_register_all=False, target_group="default", seat_prefix="", start_seat=len(self.pc_records) + 1)

    def _scan_ip_list(self, ip_list, auto_register_all=False, target_group="default", seat_prefix="", start_seat=1, cols=10):
        try:
            port = int(self.entry_port.get().strip())
        except Exception:
            port = DEFAULT_PORT
        auth_token = self.entry_token.get().strip()

        def scan_thread():
            active_ips = []
            lock = threading.Lock()

            def probe(ip_addr):
                t0 = time.monotonic()
                ok = False
                resp = None
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.35)
                    if s.connect_ex((ip_addr, port)) == 0:
                        ok = True
                    s.close()
                except Exception:
                    pass
                if ok:
                    resp = query_remote_status(ip_addr, port, auth_token)
                beacon = DISCOVERED_CLIENTS.get(ip_addr)
                if not ok and beacon and (time.time() - beacon.get("last_seen", 0) < 90):
                    ok = True
                if ok:
                    lat = (resp or {}).get("latency_ms") or max(1, int((time.monotonic() - t0) * 1000))
                    with lock:
                        active_ips.append((ip_addr, resp or {}, lat))

            with ThreadPoolExecutor(max_workers=32) as pool:
                list(pool.map(probe, ip_list))

            active_ip_set = {x[0] for x in active_ips}
            changed = False

            # Register responding PCs or entire planned range
            ordered_register = ip_list if auto_register_all else sorted(active_ip_set, key=ip_sort_key)
            for idx, ip in enumerate(ordered_register):
                seat_idx = start_seat + idx
                beacon_info = DISCOVERED_CLIENTS.get(ip, {})
                resp_info = next((r for (rip, r, _) in active_ips if rip == ip), {})
                mac = resp_info.get("mac") or beacon_info.get("mac") or (get_mac_from_arp(ip) if ip in active_ip_set else "")
                host = resp_info.get("device") or beacon_info.get("hostname") or f"LAB-{format_seat_no(seat_idx)}"

                if ip not in self.pc_records:
                    self.pc_records[ip] = {
                        "hostname": host,
                        "mac": mac,
                        "group": target_group,
                        "seat_no": format_seat_no(seat_idx, prefix=seat_prefix),
                        "row": (idx // cols) + 1,
                        "col": (idx % cols) + 1,
                        "memo": "Range Scan" if auto_register_all else "LAN Scan",
                    }
                    changed = True
                else:
                    if mac and not self.pc_records[ip].get("mac"):
                        self.pc_records[ip]["mac"] = mac
                        changed = True
                    if resp_info.get("device") and self.pc_records[ip].get("hostname", "").startswith(("PC-", "LAB-")):
                        self.pc_records[ip]["hostname"] = resp_info["device"]
                        changed = True

                if ip in active_ip_set:
                    self.last_scanned_active_ips.add(ip)
                    lat = next((l for (rip, _, l) in active_ips if rip == ip), 1)
                    self.pc_live_telemetry[ip] = {
                        "status": "online",
                        "latency_ms": lat,
                        "rules_count": resp_info.get("count", beacon_info.get("rules_count", 0)),
                        "timer_running": resp_info.get("timer_running", beacon_info.get("timer_running", False)),
                        "remaining_seconds": resp_info.get("remaining_seconds", beacon_info.get("remaining_seconds", 0)),
                        "active_mode": resp_info.get("active_mode", beacon_info.get("active_mode", "")),
                        "last_ack": datetime.now().strftime("%H:%M:%S"),
                    }

            if changed:
                self.save_pc_groups_data()

            def done_ui():
                self.btn_scan.config(state="normal", text=self.t("btn_scan"))
                self.refresh_group_combobox()
                self.refresh_pc_roster_view()
                self.log_append(
                    self.L(
                        f"🔍 스캔 완료: {len(ip_list)}개 주소 중 {len(active_ip_set)}대 온라인 응답",
                        f"🔍 Scan complete: {len(active_ip_set)} online out of {len(ip_list)} probed.",
                    )
                )

            self.root.after(0, done_ui)

        threading.Thread(target=scan_thread, daemon=True).start()

    def on_beacon_pc_discovered(self, c_ip, hostname, mac, info=None):
        self.last_scanned_active_ips.add(c_ip)
        updated = False
        if c_ip not in self.pc_records:
            seat_num = len(self.pc_records) + 1
            self.pc_records[c_ip] = {
                "hostname": hostname or f"PC-{c_ip.split('.')[-1]}",
                "mac": mac or get_mac_from_arp(c_ip),
                "group": "default",
                "seat_no": format_seat_no(seat_num),
                "row": ((seat_num - 1) // 10) + 1,
                "col": ((seat_num - 1) % 10) + 1,
                "memo": "Beacon Auto",
            }
            updated = True
        else:
            if mac and not self.pc_records[c_ip].get("mac"):
                self.pc_records[c_ip]["mac"] = mac
                updated = True
            if hostname and not self.pc_records[c_ip].get("hostname"):
                self.pc_records[c_ip]["hostname"] = hostname
                updated = True

        if info:
            cur = self.pc_live_telemetry.get(c_ip, {})
            cur.update(
                {
                    "status": "online",
                    "rules_count": info.get("rules_count", cur.get("rules_count", 0)),
                    "timer_running": info.get("timer_running", cur.get("timer_running", False)),
                    "remaining_seconds": info.get("remaining_seconds", cur.get("remaining_seconds", 0)),
                    "active_mode": info.get("active_mode", cur.get("active_mode", "")),
                    "last_ack": datetime.now().strftime("%H:%M:%S"),
                }
            )
            self.pc_live_telemetry[c_ip] = cur

        if updated:
            self.save_pc_groups_data()
            self.refresh_group_combobox()
        self.refresh_pc_roster_view()

    def on_toggle_auto_poll(self):
        if self.auto_poll_var.get():
            self.log_append(self.L("📡 50대 실시간 15초 자동 상태 폴링 활성화됨", "📡 15s live telemetry polling enabled."))
            self._poll_all_known_silent()

    def _poll_all_known_silent(self):
        if self.batch_in_progress:
            return
        targets = list(self.pc_records.keys())
        if not targets:
            return
        try:
            port = int(self.entry_port.get().strip())
        except Exception:
            port = DEFAULT_PORT
        auth_token = self.entry_token.get().strip()

        def poll_worker():
            def check_one(ip):
                resp = query_remote_status(ip, port, auth_token)
                return ip, resp

            with ThreadPoolExecutor(max_workers=min(24, max(4, len(targets)))) as pool:
                for ip, resp in pool.map(check_one, targets):
                    if resp.get("success"):
                        self.last_scanned_active_ips.add(ip)
                        self.pc_live_telemetry[ip] = {
                            "status": "online",
                            "latency_ms": resp.get("latency_ms", 1),
                            "rules_count": resp.get("count", 0),
                            "timer_running": resp.get("timer_running", False),
                            "remaining_seconds": resp.get("remaining_seconds", 0),
                            "active_mode": resp.get("active_mode", ""),
                            "last_ack": datetime.now().strftime("%H:%M:%S"),
                        }
                    else:
                        cur = self.pc_live_telemetry.get(ip, {})
                        cur["status"] = "offline"
                        self.pc_live_telemetry[ip] = cur
            self.root.after(0, self.refresh_pc_roster_view)

        threading.Thread(target=poll_worker, daemon=True).start()

    def schedule_tick_loops(self):
        self._tick_counter = 0

        def _tick():
            self._tick_counter += 1
            # Decrement live active remote timers locally for smooth 1s updates
            timer_changed = False
            for ip, tele in self.pc_live_telemetry.items():
                if tele.get("timer_running") and tele.get("remaining_seconds", 0) > 0:
                    tele["remaining_seconds"] = max(0, tele["remaining_seconds"] - 1)
                    timer_changed = True
            if timer_changed and not self.batch_in_progress:
                self.refresh_pc_roster_view()

            if self._tick_counter % 15 == 0 and self.auto_poll_var.get():
                self._poll_all_known_silent()

            self.root.after(1000, _tick)

        self.root.after(1000, _tick)

    # ---------------------------------------------------------------------
    # Onboarding Dialogs: IP Range Scan + RFC-4180 CSV Import & Export
    # ---------------------------------------------------------------------
    def open_ip_range_scan_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title(self.L("🌐 IP 대역 스캔 & 좌석 자동 번호 부여", "🌐 IP Range Scan & Auto Seat Mapping"))
        dlg.geometry("460x350")
        dlg.resizable(False, False)
        dlg.configure(bg=self.card_color)
        dlg.transient(self.root)
        dlg.grab_set()

        local_ip = get_local_ip()
        prefix = "192.168.0." if local_ip == "127.0.0.1" else ".".join(local_ip.split(".")[:3]) + "."

        f = tk.Frame(dlg, bg=self.card_color, padx=16, pady=14)
        f.pack(fill="both", expand=True)

        tk.Label(
            f,
            text=self.L("컴퓨터실 대역의 시작~종료 IP를 지정하면 최대 50~254대를 병렬 스캔합니다.", "Specify Start–End IPv4 range to probe & auto-assign lab seat numbers."),
            bg=self.card_color,
            fg="#93c5fd",
            font=("Arial", 8, "bold"),
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        grid_f = tk.Frame(f, bg=self.card_color)
        grid_f.pack(fill="x")

        tk.Label(grid_f, text=self.L("시작 IP:", "Start IP:"), bg=self.card_color, fg=self.text_color, font=("Arial", 9)).grid(row=0, column=0, sticky="w", pady=4)
        e_start = tk.Entry(grid_f, bg=self.input_bg, fg="white", insertbackground="white", font=("Consolas", 9))
        e_start.insert(0, f"{prefix}101")
        e_start.grid(row=0, column=1, sticky="ew", pady=4, padx=(6, 0))

        tk.Label(grid_f, text=self.L("종료 IP:", "End IP:"), bg=self.card_color, fg=self.text_color, font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=4)
        e_end = tk.Entry(grid_f, bg=self.input_bg, fg="white", insertbackground="white", font=("Consolas", 9))
        e_end.insert(0, f"{prefix}150")
        e_end.grid(row=1, column=1, sticky="ew", pady=4, padx=(6, 0))

        tk.Label(grid_f, text=self.L("좌석 접두어:", "Seat Prefix:"), bg=self.card_color, fg=self.text_color, font=("Arial", 9)).grid(row=2, column=0, sticky="w", pady=4)
        e_prefix = tk.Entry(grid_f, bg=self.input_bg, fg="white", insertbackground="white", font=("Consolas", 9))
        e_prefix.insert(0, "LAB-")
        e_prefix.grid(row=2, column=1, sticky="ew", pady=4, padx=(6, 0))

        tk.Label(grid_f, text=self.L("소속 그룹:", "Target Group:"), bg=self.card_color, fg=self.text_color, font=("Arial", 9)).grid(row=3, column=0, sticky="w", pady=4)
        grp_choices = [g["name"] for g in self.groups_list if g["id"] != "all"]
        cb_grp = ttk.Combobox(grid_f, values=grp_choices, state="readonly", font=("Arial", 9))
        if grp_choices:
            cb_grp.current(0)
        cb_grp.grid(row=3, column=1, sticky="ew", pady=4, padx=(6, 0))

        register_all_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            f,
            text=self.L("미응답(전원 꺼짐) PC도 WOL 대비용으로 전체 좌석 대장에 미리 등록", "Pre-register offline seats as well for WOL readiness"),
            variable=register_all_var,
            bg=self.card_color,
            fg=self.text_color,
            selectcolor=self.input_bg,
            activebackground=self.card_color,
            font=("Arial", 8),
        ).pack(anchor="w", pady=(10, 10))

        grid_f.columnconfigure(1, weight=1)

        def on_start_scan():
            try:
                ip_list = expand_ipv4_range(e_start.get(), e_end.get(), limit=254)
            except Exception as ex:
                messagebox.showerror("IP Range Error", str(ex), parent=dlg)
                return
            g_obj = self.get_group_by_name(cb_grp.get())
            gid = g_obj["id"] if g_obj else "default"
            s_pref = e_prefix.get().strip()
            reg_all = register_all_var.get()
            dlg.destroy()
            self.log_append(
                self.L(
                    f"🌐 대역 스캔 시작: {ip_list[0]} ~ {ip_list[-1]} ({len(ip_list)}대)",
                    f"🌐 Range scan started: {ip_list[0]} ~ {ip_list[-1]} ({len(ip_list)} hosts)",
                )
            )
            self._scan_ip_list(ip_list, auto_register_all=reg_all, target_group=gid, seat_prefix=s_pref, start_seat=1, cols=self.grid_cols)

        b_row = tk.Frame(f, bg=self.card_color)
        b_row.pack(fill="x", pady=(6, 0))
        tk.Button(b_row, text=self.L("취소", "Cancel"), bg="#475569", fg="white", relief="flat", padx=12, pady=4, command=dlg.destroy).pack(side="right", padx=(6, 0))
        tk.Button(b_row, text=self.L("🔍 대역 스캔 실행", "🔍 Run Range Scan"), bg="#0d9488", fg="white", font=("Arial", 9, "bold"), relief="flat", padx=14, pady=4, command=on_start_scan).pack(side="right")

    def import_csv_roster(self):
        path = filedialog.askopenfilename(
            parent=self.root,
            title=self.L("CSV 컴퓨터실 좌석 목록 불러오기", "Import Lab Roster CSV"),
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()
            rows = parse_lab_roster_csv(content)
            if not rows:
                messagebox.showwarning(
                    self.L("CSV 오류", "CSV Error"),
                    self.L("유효한 IP 컬럼(ip)을 찾지 못했습니다.", "No valid 'ip' rows found in CSV."),
                )
                return

            imported = 0
            for idx, r in enumerate(rows, start=1):
                grp_id = r["group"] or "default"
                if grp_id != "default" and not self.get_group_by_id(grp_id):
                    # Try matching group by name or create one
                    by_name = self.get_group_by_name(grp_id)
                    if by_name:
                        grp_id = by_name["id"]
                    else:
                        new_gid = f"grp_{re.sub(r'[^a-zA-Z0-9_]', '_', grp_id)}"
                        if not self.get_group_by_id(new_gid):
                            self.groups_list.append({"id": new_gid, "name": f"🏫 {grp_id}", "is_system": False})
                        grp_id = new_gid

                self.pc_records[r["ip"]] = {
                    "hostname": r["hostname"],
                    "mac": r["mac"],
                    "group": grp_id,
                    "seat_no": r["seat_no"] or format_seat_no(idx),
                    "row": r["row"] or ((idx - 1) // self.grid_cols) + 1,
                    "col": r["col"] or ((idx - 1) % self.grid_cols) + 1,
                    "memo": r["memo"],
                }
                imported += 1

            self.save_pc_groups_data()
            self.refresh_group_combobox()
            self.refresh_pc_roster_view()
            self.log_append(self.L(f"📥 CSV에서 {imported}대 좌석·MAC 정보 일괄 등록 완료", f"📥 Imported {imported} PC(s) from CSV."))
            messagebox.showinfo(
                self.L("CSV 등록 완료", "CSV Import Complete"),
                self.L(f"총 {imported}대의 PC 좌석·MAC 매핑이 등록되었습니다.", f"Successfully imported {imported} lab PCs."),
            )
        except Exception as ex:
            messagebox.showerror("CSV Import Error", str(ex))

    def export_csv_roster(self):
        if not self.pc_records:
            messagebox.showwarning(self.L("내보낼 PC 없음", "No PCs"), self.L("등록된 PC가 없습니다.", "Roster is empty."))
            return
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title=self.L("CSV 좌석 목록 내보내기", "Export Lab Roster CSV"),
            defaultextension=".csv",
            initialfile="powercontroller_lab_roster.csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["seat_no", "ip", "mac", "hostname", "group", "row", "col", "memo"])
                for idx, (ip, rec) in enumerate(sorted(self.pc_records.items(), key=lambda kv: ip_sort_key(kv[0])), start=1):
                    writer.writerow([
                        rec.get("seat_no") or format_seat_no(idx),
                        ip,
                        rec.get("mac", ""),
                        rec.get("hostname", ""),
                        rec.get("group", "default"),
                        rec.get("row", ""),
                        rec.get("col", ""),
                        rec.get("memo", ""),
                    ])
            self.log_append(self.L(f"📤 CSV 저장 완료: {os.path.basename(path)}", f"📤 Exported roster CSV: {os.path.basename(path)}"))
            messagebox.showinfo(self.L("내보내기 완료", "Export Complete"), path)
        except Exception as ex:
            messagebox.showerror("CSV Export Error", str(ex))

    # ---------------------------------------------------------------------
    # Batch & Lab Profile Deployment Commands
    # ---------------------------------------------------------------------
    def on_deploy_lab_profile_click(self):
        target_ips = self.get_target_ips()
        if not target_ips:
            messagebox.showerror(
                self.L("대상 미지정", "No Targets"),
                self.L("오른쪽 관제 패널에서 대상 PC를 1대 이상 선택하십시오.", "Select at least one target PC in the fleet panel."),
            )
            return

        p_idx = self.combo_profile.current()
        if p_idx < 0 or p_idx >= len(LAB_SCHEDULE_PROFILES):
            return
        prof = LAB_SCHEDULE_PROFILES[p_idx]
        rules = prof["rules"]
        prof_name = prof["name_ko"] if self.lang == "ko" else prof["name_en"]

        if not messagebox.askyesno(
            self.L("교시·일과 프로필 일괄 배포", "Deploy Lab Profile Bundle"),
            self.L(
                f"대상 PC {len(target_ips)}대에 프로필 [{prof_name}] ({len(rules)}개 규칙 묶음)을 일괄 배포하시겠습니까?\n※ 기존 규칙은 덮어쓰기로 깔끔히 통일됩니다.",
                f"Deploy [{prof_name}] ({len(rules)} rules) to {len(target_ips)} PCs?\nExisting schedules will be replaced cleanly.",
            ),
        ):
            return

        try:
            port = int(self.entry_port.get().strip())
        except Exception:
            port = DEFAULT_PORT
        auth_token = self.entry_token.get().strip()

        def deploy_one_pc(ip):
            last_resp = {"success": False, "message": "Empty"}
            for r_i, rule in enumerate(rules):
                overwrite = r_i == 0
                last_resp = send_rule_over_network(ip, port, rule, overwrite, auth_token)
                if not last_resp.get("success"):
                    err = last_resp.get("message", "No response")
                    return False, {"status": "failed", "last_err": err}, f"❌ [{ip}] 프로필 배포 실패 ({rule['label']}): {err}"
            cnt = last_resp.get("count", len(rules))
            lat = last_resp.get("latency_ms", 1)
            return (
                True,
                {"status": "online", "rules_count": cnt, "latency_ms": lat, "last_ack": f"Profile({cnt})"},
                f"✅ [{ip}] 프로필 배포 완료 ({cnt} rules, {lat}ms)",
            )

        self.log_append(self.L(f"📡 [{prof_name}] {len(target_ips)}대 일괄 배포 시작...", f"📡 Deploying profile to {len(target_ips)} PC(s)..."))
        self._execute_parallel_batch("Lab Profile", target_ips, deploy_one_pc)

    def on_send_click(self):
        target_ips = self.get_target_ips()
        if not target_ips:
            messagebox.showerror(
                self.L("입력 에러", "Input Error"),
                self.L("대상 IP를 입력하거나 오른쪽 패널에서 PC를 체크하십시오.", "Enter target IPs or select PCs from the roster."),
            )
            return

        try:
            port = int(self.entry_port.get().strip())
            h = int(self.entry_hour.get().strip())
            m = int(self.entry_min.get().strip())
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError()
        except Exception:
            messagebox.showerror(self.L("입력 에러", "Input Error"), self.L("포트 및 시(0~23)/분(0~59)을 올바르게 확인하십시오.", "Check port and time (0-23 / 0-59)."))
            return

        label = self.entry_label.get().strip()
        if not label:
            messagebox.showerror(self.L("입력 에러", "Input Error"), self.L("예약 규칙 이름을 입력하십시오.", "Enter a schedule rule label."))
            return

        active_days = [i for i, var in enumerate(self.day_vars) if var.get()]
        if not active_days:
            messagebox.showerror(self.L("요일 미선택", "No Days"), self.L("요일을 1개 이상 선택하십시오.", "Select at least one day."))
            return

        selected_mode = self.mode_keys[max(0, self.combo_mode.current())]
        overwrite = self.apply_option.get() == "overwrite"
        auth_token = self.entry_token.get().strip()

        grace_digits = re.sub(r"\D", "", self.combo_grace.get())
        grace_period_sec = int(grace_digits) if grace_digits else 10
        idle_digits = re.sub(r"\D", "", self.combo_idle_min.get())
        idle_minutes = int(idle_digits) if idle_digits else 15

        rule_data = {
            "label": label,
            "mode": selected_mode,
            "time": f"{h:02d}:{m:02d}",
            "days": active_days,
            "force_close": self.force_close_var.get(),
            "warning_message": self.entry_warn_msg.get().strip(),
            "grace_period_sec": grace_period_sec,
            "allow_delay": self.allow_delay_var.get(),
            "warning_beep": self.warning_beep_var.get(),
            "idle_only": self.idle_only_var.get(),
            "idle_minutes": idle_minutes,
            "clean_temp": self.clean_temp_var.get(),
            "pre_command": self.entry_precmd.get().strip(),
        }

        if selected_mode in ("shutdown", "reboot"):
            has_admin, admin_ip, admin_host = self.check_admin_pc_in_targets(target_ips)
            if has_admin:
                if not messagebox.askyesno(
                    self.L("⚠️ 관리자 PC 포함 경고", "⚠️ Admin PC Included"),
                    self.L(
                        f"본인(관리자) PC [{admin_ip} ({admin_host})]가 대상에 포함되어 있습니다.\n계속 전송하시겠습니까?",
                        f"Your local Admin PC [{admin_ip} ({admin_host})] is included in targets.\nContinue anyway?",
                    ),
                    icon="warning",
                    default="no",
                ):
                    return

        def send_one(ip):
            resp = send_rule_over_network(ip, port, rule_data, overwrite, auth_token)
            if resp.get("success"):
                cnt = resp.get("count", "?")
                lat = resp.get("latency_ms", 1)
                return (
                    True,
                    {"status": "online", "rules_count": cnt if isinstance(cnt, int) else 1, "latency_ms": lat, "last_ack": f"Rule({cnt})"},
                    f"✅ [{ip}] {label} -> OK ({cnt} rules, {lat}ms)",
                )
            err = resp.get("message", "No response")
            return False, {"status": "failed", "last_err": err}, f"❌ [{ip}] {err}"

        self.log_append(self.L(f"🚀 [{label}] {len(target_ips)}대 병렬 전송 시작...", f"🚀 Parallel push [{label}] -> {len(target_ips)} PC(s)..."))
        self._execute_parallel_batch("Push Rule", target_ips, send_one)

    def on_clear_remote_click(self):
        target_ips = self.get_target_ips()
        if not target_ips:
            messagebox.showerror(self.L("입력 에러", "Input Error"), self.L("초기화할 대상 PC를 선택하십시오.", "Select target PCs to clear."))
            return
        if not messagebox.askyesno(
            self.L("원격 예약 초기화 확인", "Confirm Clear All"),
            self.L(f"선택된 {len(target_ips)}대 PC의 모든 예약 규칙을 초기화하시겠습니까?", f"Clear all scheduled rules on {len(target_ips)} PC(s)?"),
        ):
            return
        try:
            port = int(self.entry_port.get().strip())
        except Exception:
            port = DEFAULT_PORT
        auth_token = self.entry_token.get().strip()

        def clear_one(ip):
            resp = send_clear_schedules(ip, port, auth_token)
            if resp.get("success"):
                lat = resp.get("latency_ms", 1)
                return True, {"status": "online", "rules_count": 0, "latency_ms": lat, "last_ack": "Cleared"}, f"🗑️ [{ip}] Cleared ({lat}ms)"
            err = resp.get("message", "No response")
            return False, {"status": "failed", "last_err": err}, f"❌ [{ip}] Clear failed: {err}"

        self._execute_parallel_batch("Clear Rules", target_ips, clear_one)

    def on_query_status_click(self):
        target_ips = self.get_target_ips()
        if not target_ips:
            target_ips = self._get_visible_ips()
        if not target_ips:
            messagebox.showerror(self.L("대상 없음", "No Targets"), self.L("조회할 PC가 없습니다.", "No target PCs available."))
            return
        self._run_parallel_query(target_ips)

    def _run_parallel_query(self, target_ips):
        try:
            port = int(self.entry_port.get().strip())
        except Exception:
            port = DEFAULT_PORT
        auth_token = self.entry_token.get().strip()

        def query_one(ip):
            resp = query_remote_status(ip, port, auth_token)
            if resp.get("success"):
                cnt = resp.get("count", 0)
                lat = resp.get("latency_ms", 1)
                return (
                    True,
                    {
                        "status": "online",
                        "rules_count": cnt,
                        "latency_ms": lat,
                        "timer_running": resp.get("timer_running", False),
                        "remaining_seconds": resp.get("remaining_seconds", 0),
                        "active_mode": resp.get("active_mode", ""),
                        "last_ack": f"Poll {cnt}R/{lat}ms",
                    },
                    f"📊 [{ip}] Online · Rules {cnt} · {lat}ms",
                )
            err = resp.get("message", "Offline")
            return False, {"status": "failed", "last_err": err}, f"❌ [{ip}] {err}"

        self.log_append(self.L(f"📊 {len(target_ips)}대 상태 병렬 폴링 중...", f"📊 Polling status on {len(target_ips)} PC(s)..."))
        self._execute_parallel_batch("Poll Status", target_ips, query_one)

    def on_immediate_power_click(self, action_type="shutdown"):
        target_ips = self.get_target_ips()
        if not target_ips:
            messagebox.showerror(self.L("대상 미지정", "No Targets"), self.L("제어할 대상 PC를 선택하십시오.", "Select target PCs first."))
            return

        action_labels = {
            "shutdown": (self.L("시스템 종료", "Shutdown"), "Shutdown"),
            "reboot": (self.L("다시 시작", "Reboot"), "Reboot"),
            "sleep": (self.L("절전 모드", "Sleep"), "Sleep"),
            "screenoff": (self.L("화면 끄기", "Screen Off"), "Screen Off"),
            "alarm": (self.L("비상 알람", "Alarm"), "Alarm"),
        }
        cmd_disp, cmd_eng = action_labels.get(action_type, ("Action", action_type))

        if action_type in ("shutdown", "reboot", "sleep"):
            has_admin, admin_ip, admin_host = self.check_admin_pc_in_targets(target_ips)
            if has_admin:
                if not messagebox.askyesno(
                    self.L(f"🚨 관리자 PC 즉시 {cmd_disp} 경고", f"🚨 Admin PC {cmd_eng} Warning"),
                    self.L(
                        f"관리자 본인 PC [{admin_ip} ({admin_host})]가 대상에 포함되었습니다!\n정말 즉시 [{cmd_disp}]를 실행하시겠습니까?",
                        f"Admin PC [{admin_ip} ({admin_host})] is included!\nProceed with immediate {cmd_eng}?",
                    ),
                    icon="warning",
                    default="no",
                ):
                    return
            else:
                if not messagebox.askyesno(
                    self.L(f"⚠️ 원격 즉시 {cmd_disp} 확인", f"⚠️ Confirm Immediate {cmd_eng}"),
                    self.L(
                        f"선택된 {len(target_ips)}대 PC에 즉시 [{cmd_disp}] 명령을 전송하시겠습니까?",
                        f"Dispatch immediate [{cmd_eng}] to {len(target_ips)} PC(s)?",
                    ),
                    icon="warning",
                ):
                    return

        try:
            port = int(self.entry_port.get().strip())
        except Exception:
            port = DEFAULT_PORT
        auth_token = self.entry_token.get().strip()

        def power_one(ip):
            resp = send_immediate_power_action(
                ip=ip, port=port, power_cmd=action_type, force=True, grace_period_sec=3, auth_token=auth_token
            )
            if resp.get("success"):
                lat = resp.get("latency_ms", 1)
                return True, {"status": "online", "latency_ms": lat, "last_ack": f"{cmd_eng} OK"}, f"✅ [{ip}] {cmd_disp} OK ({lat}ms)"
            err = resp.get("message", "No response")
            return False, {"status": "failed", "last_err": err}, f"❌ [{ip}] {cmd_disp} failed: {err}"

        self.log_append(self.L(f"⚡ {len(target_ips)}대에 즉시 [{cmd_disp}] 병렬 전송...", f"⚡ Dispatching [{cmd_eng}] to {len(target_ips)} PC(s)..."))
        self._execute_parallel_batch(f"Immediate {cmd_eng}", target_ips, power_one)

    def on_context_menu_power(self, ip, action_type="shutdown"):
        try:
            port = int(self.entry_port.get().strip())
        except Exception:
            port = DEFAULT_PORT
        auth_token = self.entry_token.get().strip()

        if action_type in ("shutdown", "reboot", "sleep"):
            if not messagebox.askyesno(
                self.L("⚠️ 단독 즉시 제어", "⚠️ Single PC Power Action"),
                self.L(f"대상 PC [{ip}]에 즉시 '{action_type}' 명령을 전송하시겠습니까?", f"Send '{action_type}' immediately to [{ip}]?"),
                icon="warning",
            ):
                return

        def worker():
            resp = send_immediate_power_action(ip, port, power_cmd=action_type, force=True, grace_period_sec=3, auth_token=auth_token)
            if resp.get("success"):
                self.log_append(f"✅ [{ip}] {action_type} -> OK")
            else:
                self.log_append(f"❌ [{ip}] {action_type} -> {resp.get('message', 'Error')}")

        threading.Thread(target=worker, daemon=True).start()

    # ---------------------------------------------------------------------
    # Staggered WOL (Wake-on-LAN) & Group Management
    # ---------------------------------------------------------------------
    def on_group_wol_click(self):
        cur_gid = self.get_current_selected_group_id()
        checked_ips = sorted([ip for ip, chk in self.pc_checked_status.items() if chk], key=ip_sort_key)
        if checked_ips:
            target_ips = checked_ips
        else:
            target_ips = [
                ip for ip, pc in sorted(self.pc_records.items(), key=lambda kv: ip_sort_key(kv[0]))
                if cur_gid == "all" or pc.get("group", "default") == cur_gid
            ]

        if not target_ips:
            messagebox.showwarning(self.L("WOL 대상 없음", "No WOL Targets"), self.L("PC를 먼저 등록하거나 선택하십시오.", "Select or onboard PCs first."))
            return

        wol_targets = []
        missing_mac = []
        for ip in target_ips:
            mac = self.pc_records.get(ip, {}).get("mac", "") or get_mac_from_arp(ip)
            if mac:
                wol_targets.append((ip, mac))
            else:
                missing_mac.append(ip)

        if not wol_targets:
            messagebox.showerror(
                self.L("WOL 전송 불가", "No MAC Registered"),
                self.L("선택된 PC에 등록된 MAC 주소가 없습니다. CSV 또는 PC 편집으로 MAC을 입력하십시오.", "None of the selected PCs have MAC addresses."),
            )
            return

        step_ms_str = re.sub(r"\D", "", self.combo_wol_step.get())
        step_sec = (int(step_ms_str) if step_ms_str else 250) / 1000.0

        if not messagebox.askyesno(
            self.L("⚡ 순차 WOL 기상 확인", "⚡ Confirm Staggered WOL"),
            self.L(
                f"총 {len(wol_targets)}대에 {int(step_sec*1000)}ms 간격으로 순차 WOL 패킷을 송출합니다.\n(MAC 미등록 제외: {len(missing_mac)}대)\n계속하시겠습니까?",
                f"Send staggered WOL magic packets to {len(wol_targets)} PC(s) at {int(step_sec*1000)}ms intervals?\n(Missing MAC skipped: {len(missing_mac)})\nContinue?",
            ),
        ):
            return

        self.log_append(self.L(f"⚡ 순차 WOL 기상 시작 ({len(wol_targets)}대, 간격 {int(step_sec*1000)}ms)...", f"⚡ Staggered WOL started ({len(wol_targets)} PCs, step {int(step_sec*1000)}ms)..."))

        def wol_worker():
            ok_cnt = 0
            fail_cnt = 0
            total = len(wol_targets)
            for idx, (ip, mac) in enumerate(wol_targets, start=1):
                res = send_wol_magic_packet(mac, target_ip=ip)
                is_ok = res.get("success", False) if isinstance(res, dict) else bool(res)
                if is_ok:
                    ok_cnt += 1
                    self.log_append(f"⚡ WOL [{idx}/{total}] -> {ip} [{mac}] OK")
                else:
                    fail_cnt += 1
                    self.log_append(f"❌ WOL [{idx}/{total}] -> {ip} [{mac}] FAIL")
                self.root.after(
                    0, lambda i=idx, t=total, o=ok_cnt, f=fail_cnt: self._update_progress_ui(i, t, o, f, "Staggered WOL")
                )
                if idx < total:
                    time.sleep(step_sec)

            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    self.L("⚡ 순차 WOL 완료", "⚡ Staggered WOL Complete"),
                    self.L(f"전송 완료: 성공 {ok_cnt}대 / 실패 {fail_cnt}대", f"Completed: {ok_cnt} succeeded / {fail_cnt} failed"),
                ),
            )

        threading.Thread(target=wol_worker, daemon=True).start()

    def on_single_pc_wol(self, ip, parent=None):
        owner = parent or self.root
        rec = self.pc_records.get(ip, {})
        mac = rec.get("mac", "") or get_mac_from_arp(ip)
        if not mac:
            prompt_mac = self.prompt_text_dialog(
                self.L("WOL MAC 주소 필요", "MAC Address Required"),
                self.L(f"PC [{ip}]의 MAC 주소를 입력하세요 (예: 00:11:22:33:44:55):", f"Enter MAC address for [{ip}] (e.g. 00:11:22:33:44:55):"),
                parent=owner,
            )
            if not prompt_mac:
                return
            mac = prompt_mac.strip().upper()
            rec["mac"] = mac
            self.pc_records[ip] = rec
            self.save_pc_groups_data()
            self.refresh_pc_roster_view()

        res = send_wol_magic_packet(mac, target_ip=ip)
        ok = res.get("success", False) if isinstance(res, dict) else bool(res)
        if ok:
            self.log_append(f"⚡ [{ip}] WOL OK [MAC: {mac}]")
            messagebox.showinfo(self.L("WOL 전송 성공", "WOL Sent"), f"[{ip}] -> MAC: {mac}", parent=owner)
        else:
            self.log_append(f"❌ [{ip}] WOL FAIL [MAC: {mac}]")
            messagebox.showerror(self.L("WOL 실패", "WOL Failed"), res.get("message", "Invalid MAC"), parent=owner)

    def move_pc_to_group(self, ip, group_id):
        if ip not in self.pc_records:
            self.pc_records[ip] = {
                "hostname": f"PC-{ip.split('.')[-1]}",
                "mac": get_mac_from_arp(ip) or "",
                "group": group_id,
                "seat_no": format_seat_no(len(self.pc_records) + 1),
                "memo": "",
            }
        else:
            self.pc_records[ip]["group"] = group_id
        self.save_pc_groups_data()
        self.refresh_group_combobox()
        self.refresh_pc_roster_view()

    def create_group_and_move_pc(self, ip):
        name = self.prompt_text_dialog(self.L("새 그룹 생성", "New Group"), self.L("새 그룹명을 입력하세요:", "Enter group name:"))
        if name and name.strip():
            gid = f"grp_{int(time.time() * 1000)}"
            self.groups_list.append({"id": gid, "name": f"🏫 {name.strip()}", "is_system": False})
            self.move_pc_to_group(ip, gid)

    def remove_single_pc(self, ip):
        if messagebox.askyesno(self.L("PC 제거", "Remove PC"), self.L(f"[{ip}]을(를) 목록에서 제거하시겠습니까?", f"Remove [{ip}] from roster?")):
            self.pc_records.pop(ip, None)
            self.pc_checked_status.pop(ip, None)
            self.last_scanned_active_ips.discard(ip)
            if ip in self.failed_targets:
                self.failed_targets.remove(ip)
            self.save_pc_groups_data()
            self.refresh_group_combobox()
            self.refresh_pc_roster_view()
            self.update_entry_ip_from_checked()

    # ---------------------------------------------------------------------
    # Group Manager & Edit PC / Seat Dialogs
    # ---------------------------------------------------------------------
    def open_group_manager(self):
        dlg = tk.Toplevel(self.root)
        dlg.title(self.L("📁 원격 PC 그룹 & WOL 관리 센터", "📁 Lab Groups & WOL Manager"))
        dlg.geometry("840x560")
        dlg.configure(bg=self.bg_color)
        dlg.transient(self.root)
        dlg.grab_set()

        body_frame = tk.Frame(dlg, bg=self.bg_color, padx=12, pady=10)
        body_frame.pack(fill="both", expand=True)

        left_p = tk.Frame(body_frame, bg=self.card_color, width=230, padx=8, pady=8)
        left_p.pack(side="left", fill="y", padx=(0, 6))
        left_p.pack_propagate(False)

        tk.Label(left_p, text=self.L("🏷️ 그룹 목록", "🏷️ Groups"), font=("Arial", 9, "bold"), bg=self.card_color, fg=self.text_color).pack(anchor="w", pady=(0, 4))
        grp_listbox = tk.Listbox(left_p, bg=self.input_bg, fg="#f3f4f6", selectbackground=self.accent_color, relief="flat", font=("Arial", 9, "bold"), highlightthickness=0)
        grp_listbox.pack(fill="both", expand=True, pady=(0, 6))

        def populate_groups():
            grp_listbox.delete(0, tk.END)
            for g in self.groups_list:
                gid = g["id"]
                cnt = len(self.pc_records) if gid == "all" else sum(1 for p in self.pc_records.values() if p.get("group") == gid)
                grp_listbox.insert(tk.END, f"{g['name']} ({cnt})")

        f_grp_btns = tk.Frame(left_p, bg=self.card_color)
        f_grp_btns.pack(fill="x")

        def on_add_group():
            name = self.prompt_text_dialog(self.L("새 그룹", "New Group"), self.L("그룹명을 입력하세요:", "Enter group name:"), parent=dlg)
            if name and name.strip():
                gid = f"grp_{int(time.time() * 1000)}"
                self.groups_list.append({"id": gid, "name": f"🏫 {name.strip()}", "is_system": False})
                self.save_pc_groups_data()
                populate_groups()
                self.refresh_group_combobox()

        def on_del_group():
            sel = grp_listbox.curselection()
            if not sel:
                return
            tg = self.groups_list[sel[0]]
            if tg.get("is_system") or tg["id"] == "default":
                return
            for pc in self.pc_records.values():
                if pc.get("group") == tg["id"]:
                    pc["group"] = "default"
            self.groups_list = [g for g in self.groups_list if g["id"] != tg["id"]]
            self.save_pc_groups_data()
            populate_groups()
            self.refresh_group_combobox()
            self.refresh_pc_roster_view()
            populate_pcs()

        tk.Button(f_grp_btns, text=self.L("➕ 추가", "➕ Add"), bg="#2563eb", fg="white", relief="flat", font=("Arial", 8, "bold"), pady=3, command=on_add_group).pack(side="left", fill="x", expand=True, padx=(0, 2))
        tk.Button(f_grp_btns, text=self.L("🗑️ 삭제", "🗑️ Delete"), bg="#dc2626", fg="white", relief="flat", font=("Arial", 8), pady=3, command=on_del_group).pack(side="right", fill="x", expand=True, padx=(2, 0))

        right_p = tk.Frame(body_frame, bg=self.card_color, padx=8, pady=8)
        right_p.pack(side="right", fill="both", expand=True)

        pc_tree = ttk.Treeview(right_p, columns=("seat", "ip", "host", "mac", "group", "memo"), show="headings", style="Fleet.Treeview")
        for cid, txt, w in [
            ("seat", "Seat", 55),
            ("ip", "IP", 105),
            ("host", "Hostname", 110),
            ("mac", "MAC (WOL)", 130),
            ("group", "Group", 90),
            ("memo", "Memo", 90),
        ]:
            pc_tree.heading(cid, text=txt)
            pc_tree.column(cid, width=w, anchor="w")
        pc_tree.pack(fill="both", expand=True, pady=(0, 6))

        def cur_gid():
            sel = grp_listbox.curselection()
            if not sel:
                return "all"
            return self.groups_list[sel[0]]["id"]

        def populate_pcs():
            for r in pc_tree.get_children():
                pc_tree.delete(r)
            gid = cur_gid()
            for idx, (ip, pc) in enumerate(sorted(self.pc_records.items(), key=lambda kv: ip_sort_key(kv[0])), start=1):
                if gid == "all" or pc.get("group", "default") == gid:
                    g_obj = self.get_group_by_id(pc.get("group", "default"))
                    g_nm = g_obj["name"].split(" (")[0] if g_obj else "default"
                    pc_tree.insert("", tk.END, values=(pc.get("seat_no") or format_seat_no(idx), ip, pc.get("hostname", ""), pc.get("mac") or "-", g_nm, pc.get("memo", "")))

        grp_listbox.bind("<<ListboxSelect>>", lambda e: populate_pcs())

        f_act = tk.Frame(right_p, bg=self.card_color)
        f_act.pack(fill="x")

        def on_add_pc():
            g = cur_gid()
            self.open_edit_pc_dialog(ip="", default_group="default" if g == "all" else g, parent=dlg, on_saved=lambda: (populate_pcs(), populate_groups()))

        def on_edit_pc():
            sel = pc_tree.selection()
            if sel:
                ip = pc_tree.item(sel[0])["values"][1]
                self.open_edit_pc_dialog(ip=ip, parent=dlg, on_saved=lambda: (populate_pcs(), populate_groups()))

        def on_arp_all():
            found = 0
            for ip, pc in self.pc_records.items():
                if not pc.get("mac"):
                    m = get_mac_from_arp(ip)
                    if m:
                        pc["mac"] = m
                        found += 1
            if found:
                self.save_pc_groups_data()
                populate_pcs()
                self.refresh_pc_roster_view()
            messagebox.showinfo("ARP Scan", f"Collected {found} MAC address(es).", parent=dlg)

        tk.Button(f_act, text=self.L("➕ PC 등록", "➕ Add PC"), bg="#2563eb", fg="white", relief="flat", font=("Arial", 8, "bold"), padx=8, pady=4, command=on_add_pc).pack(side="left", padx=2)
        tk.Button(f_act, text=self.L("✏️ 수정", "✏️ Edit"), bg="#334155", fg="white", relief="flat", font=("Arial", 8), padx=8, pady=4, command=on_edit_pc).pack(side="left", padx=2)
        tk.Button(f_act, text=self.L("🔍 ARP 수집", "🔍 Collect ARP"), bg="#334155", fg="#60a5fa", relief="flat", font=("Arial", 8), padx=8, pady=4, command=on_arp_all).pack(side="left", padx=2)
        tk.Button(f_act, text=self.L("닫기", "Close"), bg="#475569", fg="white", relief="flat", font=("Arial", 8, "bold"), padx=12, pady=4, command=dlg.destroy).pack(side="right")

        populate_groups()
        grp_listbox.selection_set(0)
        populate_pcs()

    def open_edit_pc_dialog(self, ip="", default_group="default", parent=None, on_saved=None):
        owner = parent or self.root
        d = tk.Toplevel(owner)
        d.title(self.L("➕ 새 PC/좌석 등록" if not ip else f"✏️ 좌석·PC 편집 [{ip}]", "➕ Add Seat/PC" if not ip else f"✏️ Edit Seat/PC [{ip}]"))
        d.geometry("460x420")
        d.configure(bg=self.bg_color)
        d.transient(owner)
        d.grab_set()
        d.resizable(False, False)

        rec = self.pc_records.get(ip, {})
        f = tk.Frame(d, bg=self.bg_color, padx=18, pady=14)
        f.pack(fill="both", expand=True)

        tk.Label(f, text=self.L("IP 주소:", "IP Address:"), bg=self.bg_color, fg=self.text_color, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", pady=4)
        e_ip = tk.Entry(f, bg=self.input_bg, fg="#60a5fa", readonlybackground=self.input_bg, insertbackground="white", font=("Consolas", 10, "bold"))
        e_ip.grid(row=0, column=1, sticky="ew", pady=4, columnspan=2)
        if ip:
            e_ip.insert(0, ip)
            e_ip.config(state="readonly")

        tk.Label(f, text=self.L("좌석 번호:", "Seat No:"), bg=self.bg_color, fg=self.text_color, font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="w", pady=4)
        e_seat = tk.Entry(f, bg=self.input_bg, fg="white", insertbackground="white", font=("Consolas", 10))
        e_seat.insert(0, rec.get("seat_no") or format_seat_no(len(self.pc_records) + 1))
        e_seat.grid(row=1, column=1, sticky="ew", pady=4, columnspan=2)

        tk.Label(f, text=self.L("호스트명:", "Hostname:"), bg=self.bg_color, fg=self.text_color, font=("Arial", 9)).grid(row=2, column=0, sticky="w", pady=4)
        e_host = tk.Entry(f, bg=self.input_bg, fg="white", insertbackground="white", font=("Arial", 10))
        e_host.insert(0, rec.get("hostname", ""))
        e_host.grid(row=2, column=1, sticky="ew", pady=4, columnspan=2)

        tk.Label(f, text="MAC (WOL):", bg=self.bg_color, fg=self.text_color, font=("Arial", 9, "bold")).grid(row=3, column=0, sticky="w", pady=4)
        e_mac = tk.Entry(f, bg=self.input_bg, fg="#10b981", insertbackground="white", font=("Consolas", 10, "bold"))
        e_mac.insert(0, rec.get("mac", "") or get_mac_from_arp(ip))
        e_mac.grid(row=3, column=1, sticky="ew", pady=4)

        def on_arp():
            tip = e_ip.get().strip()
            m = get_mac_from_arp(tip) or DISCOVERED_CLIENTS.get(tip, {}).get("mac", "")
            if m:
                e_mac.delete(0, tk.END)
                e_mac.insert(0, m)
            else:
                messagebox.showwarning("ARP", self.L("ARP MAC을 찾지 못했습니다.", "MAC not found in ARP cache."), parent=d)

        tk.Button(f, text="🔍 ARP", bg="#334155", fg="white", relief="flat", padx=8, command=on_arp).grid(row=3, column=2, padx=(4, 0))

        tk.Label(f, text=self.L("소속 그룹:", "Group:"), bg=self.bg_color, fg=self.text_color, font=("Arial", 9)).grid(row=4, column=0, sticky="w", pady=4)
        group_choices = [g["name"] for g in self.groups_list if g["id"] != "all"]
        combo_g = ttk.Combobox(f, values=group_choices, state="readonly", font=("Arial", 9))
        combo_g.grid(row=4, column=1, sticky="ew", pady=4, columnspan=2)
        matched_g = self.get_group_by_id(rec.get("group", default_group))
        if matched_g and matched_g["name"] in group_choices:
            combo_g.set(matched_g["name"])
        elif group_choices:
            combo_g.set(group_choices[0])

        tk.Label(f, text=self.L("메모:", "Memo:"), bg=self.bg_color, fg=self.text_color, font=("Arial", 9)).grid(row=5, column=0, sticky="w", pady=4)
        e_memo = tk.Entry(f, bg=self.input_bg, fg="white", insertbackground="white", font=("Arial", 10))
        e_memo.insert(0, rec.get("memo", ""))
        e_memo.grid(row=5, column=1, sticky="ew", pady=4, columnspan=2)

        f.columnconfigure(1, weight=1)

        def on_save():
            save_ip = e_ip.get().strip()
            if not save_ip:
                return
            g_obj = self.get_group_by_name(combo_g.get())
            self.pc_records[save_ip] = {
                "seat_no": e_seat.get().strip() or format_seat_no(len(self.pc_records) + 1),
                "hostname": e_host.get().strip() or f"PC-{save_ip.split('.')[-1]}",
                "mac": e_mac.get().strip().upper(),
                "group": g_obj["id"] if g_obj else "default",
                "memo": e_memo.get().strip(),
            }
            self.save_pc_groups_data()
            self.refresh_group_combobox()
            self.refresh_pc_roster_view()
            if on_saved:
                on_saved()
            d.destroy()

        b_box = tk.Frame(f, bg=self.bg_color)
        b_box.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        tk.Button(b_box, text=self.L("취소", "Cancel"), bg="#475569", fg="white", relief="flat", padx=12, pady=4, command=d.destroy).pack(side="right", padx=(6, 0))
        tk.Button(b_box, text=self.L("💾 저장", "💾 Save"), bg=self.accent_color, fg="white", font=("Arial", 9, "bold"), relief="flat", padx=16, pady=4, command=on_save).pack(side="right")

    def prompt_text_dialog(self, title, prompt_msg, initial_val="", parent=None):
        owner = parent or self.root
        d = tk.Toplevel(owner)
        d.title(title)
        d.geometry("380x165")
        d.configure(bg=self.bg_color)
        d.transient(owner)
        d.grab_set()
        d.resizable(False, False)

        tk.Label(d, text=prompt_msg, bg=self.bg_color, fg=self.text_color, font=("Arial", 9), justify="left").pack(anchor="w", padx=16, pady=(14, 6))
        e = tk.Entry(d, bg=self.input_bg, fg="white", insertbackground="white", font=("Arial", 10), relief="flat")
        e.pack(fill="x", padx=16, pady=(0, 14))
        if initial_val:
            e.insert(0, initial_val)
        e.focus_set()

        val = [None]

        def ok(event=None):
            val[0] = e.get().strip()
            d.destroy()

        e.bind("<Return>", ok)
        e.bind("<Escape>", lambda ev: d.destroy())

        btn_f = tk.Frame(d, bg=self.bg_color)
        btn_f.pack(fill="x", padx=16)
        tk.Button(btn_f, text=self.L("취소", "Cancel"), bg="#4b5563", fg="white", relief="flat", padx=10, pady=3, command=d.destroy).pack(side="right", padx=(4, 0))
        tk.Button(btn_f, text=self.L("확인", "OK"), bg=self.accent_color, fg="white", font=("Arial", 9, "bold"), relief="flat", padx=14, pady=3, command=ok).pack(side="right")
        owner.wait_window(d)
        return val[0]

    def show_license_dialog(self):
        lic_win = tk.Toplevel(self.root)
        lic_win.title(self.L("사용권 계약 및 오픈소스 라이선스 고지", "License & Open Source Notice"))
        lic_win.configure(bg="#111827")
        lic_win.transient(self.root)
        lic_win.grab_set()
        lic_win.geometry("540x460")
        lic_win.resizable(False, False)

        lic_ko = ""
        lic_en = ""
        for p in ["docs/LICENSE_ko.txt", os.path.join(SCRIPT_DIR, "docs", "LICENSE_ko.txt")]:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        lic_ko = f.read()
                    break
                except Exception:
                    pass
        for p in ["docs/LICENSE_en.txt", os.path.join(SCRIPT_DIR, "docs", "LICENSE_en.txt")]:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        lic_en = f.read()
                    break
                except Exception:
                    pass

        hdr = tk.Frame(lic_win, bg="#111827")
        hdr.pack(fill="x", padx=16, pady=(12, 6))
        title_lbl = tk.Label(hdr, text="📜 License", font=("Arial", 10, "bold"), fg=self.accent_color, bg="#111827")
        title_lbl.pack(side="left")

        txt_widget = scrolledtext.ScrolledText(
            lic_win, wrap="word", bg="#1f2937", fg="#f3f4f6", font=("Arial", 9), relief="flat", padx=10, pady=10
        )
        txt_widget.pack(fill="both", expand=True, padx=16, pady=4)

        def switch_lang(lc):
            txt_widget.config(state="normal")
            txt_widget.delete("1.0", "end")
            txt_widget.insert("1.0", (lic_ko if lc == "ko" else lic_en) or "MIT License - Copyright (c) 2026 AhBiYout")
            txt_widget.config(state="disabled")
            title_lbl.config(text="📜 라이선스 및 사용권 약관" if lc == "ko" else "📜 License & Terms Notice")

        tk.Button(hdr, text="English", bg="#374151", fg="white", relief="flat", padx=7, command=lambda: switch_lang("en")).pack(side="right", padx=2)
        tk.Button(hdr, text="한국어", bg=self.accent_color, fg="white", relief="flat", padx=7, command=lambda: switch_lang("ko")).pack(side="right", padx=2)
        switch_lang(self.lang)
        tk.Button(lic_win, text=self.L("확인", "Close"), bg=self.accent_color, fg="white", font=("Arial", 9, "bold"), relief="flat", padx=20, pady=4, command=lic_win.destroy).pack(pady=(6, 12))

    def on_send_token_only_click(self):
        target_ips = self.get_target_ips()
        if not target_ips:
            messagebox.showerror(self.L("입력 에러", "Input Error"), self.L("보안 토큰을 전송할 대상 IP를 선택하십시오.", "Select target PCs first."))
            return
        try:
            port = int(self.entry_port.get().strip())
        except Exception:
            port = DEFAULT_PORT
        auth_token = self.entry_token.get().strip()

        token_dialog = tk.Toplevel(self.root)
        token_dialog.title(self.L("🔐 보안 토큰 병렬 전송", "🔐 Dispatch Security Token"))
        token_dialog.geometry("460x260")
        token_dialog.resizable(False, False)
        token_dialog.configure(bg=self.card_color)
        token_dialog.transient(self.root)
        token_dialog.grab_set()

        f_diag = tk.Frame(token_dialog, bg=self.card_color, padx=18, pady=16)
        f_diag.pack(fill="both", expand=True)
        tk.Label(f_diag, text=self.L(f"대상: {len(target_ips)}대 PC / 포트: {port}", f"Targets: {len(target_ips)} PCs / Port: {port}"), bg=self.card_color, fg=self.text_color, font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 12))

        def run_mode(mode):
            token_dialog.destroy()

            def tok_worker(ip):
                resp = send_verify_token(ip, port, auth_token) if mode == "verify" else send_set_remote_token(ip, port, auth_token, auth_token)
                if resp.get("success"):
                    return True, {"status": "online", "latency_ms": resp.get("latency_ms", 1), "last_ack": "Token OK"}, f"✅ [{ip}] Token {mode} OK"
                err = resp.get("message", "No response")
                return False, {"status": "failed", "last_err": err}, f"❌ [{ip}] Token {mode} fail: {err}"

            self._execute_parallel_batch(f"Token {mode}", target_ips, tok_worker)

        ttk.Button(f_diag, text=self.L("🔍 1. 보안 토큰 검증 (Verify)", "🔍 1. Verify Token"), style="Green.TButton", command=lambda: run_mode("verify")).pack(fill="x", pady=(0, 8))
        ttk.Button(f_diag, text=self.L("📥 2. 보안 토큰 원격 저장 (Set)", "📥 2. Set Remote Token"), style="Purple.TButton", command=lambda: run_mode("set")).pack(fill="x", pady=(0, 8))
        ttk.Button(f_diag, text=self.L("취소", "Cancel"), style="TButton", command=token_dialog.destroy).pack(fill="x")

    def on_emergency_recovery_click(self):
        target_ips = self.get_target_ips() or []
        try:
            port = int(self.entry_port.get().strip())
        except Exception:
            port = DEFAULT_PORT

        diag = tk.Toplevel(self.root)
        diag.title(self.L("🚨 보안 토큰 분실 비상 복구 센터", "🚨 Emergency Token Recovery"))
        diag.geometry("600x460")
        diag.resizable(False, False)
        diag.configure(bg=self.card_color)
        diag.transient(self.root)
        diag.grab_set()

        f_head = tk.Frame(diag, bg="#1e293b", padx=16, pady=10)
        f_head.pack(fill="x")
        tk.Label(f_head, text=self.L("🚨 마스터 비상 복구 키로 보안 토큰 복구/재설정", "🚨 Recover or Reset Security Token via Master Key"), font=("Arial", 11, "bold"), fg="#f87171", bg="#1e293b").pack(anchor="w")

        body = tk.Frame(diag, bg=self.card_color, padx=16, pady=12)
        body.pack(fill="both", expand=True)

        tk.Label(body, text=self.L(f"대상 PC: {len(target_ips)}대 | 포트: {port}", f"Target PCs: {len(target_ips)} | Port: {port}"), bg=self.card_color, fg="#94a3b8", font=("Arial", 9)).pack(anchor="w", pady=(0, 8))

        f_m = tk.Frame(body, bg=self.card_color)
        f_m.pack(fill="x", pady=4)
        tk.Label(f_m, text=self.L("마스터 복구 키:", "Master Key:"), bg=self.card_color, fg="#fca5a5", width=16, anchor="w").pack(side="left")
        entry_mkey = tk.Entry(f_m, bg=self.input_bg, fg="#fca5a5", insertbackground="white", relief="flat")
        entry_mkey.insert(0, get_master_recovery_key())
        entry_mkey.pack(side="left", fill="x", expand=True)

        f_n = tk.Frame(body, bg=self.card_color)
        f_n.pack(fill="x", pady=4)
        tk.Label(f_n, text=self.L("새 보안 토큰:", "New Token:"), bg=self.card_color, fg="#fde68a", width=16, anchor="w").pack(side="left")
        entry_ntok = tk.Entry(f_n, bg=self.input_bg, fg="#fde68a", insertbackground="white", relief="flat")
        entry_ntok.insert(0, self.entry_token.get().strip())
        entry_ntok.pack(side="left", fill="x", expand=True)

        def run_query():
            if not target_ips:
                messagebox.showerror("Error", self.L("대상 IP를 선택하세요.", "Select targets first."), parent=diag)
                return
            mkey = entry_mkey.get().strip()
            diag.destroy()

            def q_worker(ip):
                resp = send_query_remote_token(ip, port, mkey)
                if resp.get("success"):
                    tok = resp.get("token", "")
                    return True, {"status": "online", "last_ack": f"Tok:{tok or '(empty)'}"}, f"✅ [{ip}] Recovered token: '{tok}'"
                return False, {"status": "failed", "last_err": resp.get("message", "Error")}, f"❌ [{ip}] {resp.get('message', 'Error')}"

            self._execute_parallel_batch("Query Token", target_ips, q_worker)

        def run_reset(clear=False):
            if not target_ips:
                messagebox.showerror("Error", self.L("대상 IP를 선택하세요.", "Select targets first."), parent=diag)
                return
            mkey = entry_mkey.get().strip()
            ntok = "" if clear else entry_ntok.get().strip()
            diag.destroy()

            def r_worker(ip):
                resp = send_emergency_reset_token(ip, port, mkey, ntok)
                if resp.get("success"):
                    return True, {"status": "online", "last_ack": "Token Reset"}, f"✅ [{ip}] Token reset OK"
                return False, {"status": "failed", "last_err": resp.get("message", "Error")}, f"❌ [{ip}] {resp.get('message', 'Error')}"

            self._execute_parallel_batch("Reset Token", target_ips, r_worker)

        ttk.Button(body, text=self.L("🔍 1. 기존 보안 토큰 조회", "🔍 1. Query Existing Token"), style="Purple.TButton", command=run_query).pack(fill="x", pady=(14, 6))
        ttk.Button(body, text=self.L("⚡ 2. 새 보안 토큰 강제 재설정", "⚡ 2. Force Set New Token"), style="Green.TButton", command=lambda: run_reset(False)).pack(fill="x", pady=(0, 6))
        ttk.Button(body, text=self.L("🗑️ 3. 원격 보안 토큰 완전 초기화", "🗑️ 3. Clear Remote Token"), style="Red.TButton", command=lambda: run_reset(True)).pack(fill="x")


# -------------------------------------------------------------------------
# 4. 실행 엔트리포인트
# -------------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.option_add("*Font", "Arial 9")
    except Exception:
        pass

    app = NetworkSchedulerApp(root)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
