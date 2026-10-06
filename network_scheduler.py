import os
import sys
import json
import re
import uuid
import socket
import subprocess
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog

try:
    import native_bridge
except ImportError:
    native_bridge = None

# -------------------------------------------------------------------------
# 1. 전역 설정 및 로컬 IP 감지 & 방화벽 사전 등록
# -------------------------------------------------------------------------
APP_VERSION = "2.9.1"
DEFAULT_PORT = 9988

# -------------------------------------------------------------------------
# 자주 사용하는 스케줄 제목 프리셋 10종 (메인 앱 변경점 통합 및 동작 자동 추천)
# -------------------------------------------------------------------------
POPULAR_SCHEDULE_PRESETS = [
    {
        "title": "심야 PC 자동 종료",
        "mode": "shutdown",
        "hour": "23",
        "min": "30",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "idle": False,
        "warn": "심야 업무 종료: 작업 중인 문서를 저장하고 안전하게 PC를 종료합니다."
    },
    {
        "title": "퇴근 시간 전원 끄기",
        "mode": "shutdown",
        "hour": "18",
        "min": "30",
        "days": [0, 1, 2, 3, 4],
        "idle": False,
        "warn": "퇴근 시간 안내: 일과 종료에 따라 PC 전원이 자동으로 종료됩니다."
    },
    {
        "title": "대용량 다운로드 후 종료",
        "mode": "shutdown",
        "hour": "02",
        "min": "00",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "idle": True,
        "warn": "대용량 다운로드 완료 후 미사용 상태를 확인하여 전원을 안전하게 끕니다."
    },
    {
        "title": "점심시간 빠른 재부팅",
        "mode": "reboot",
        "hour": "12",
        "min": "40",
        "days": [0, 1, 2, 3, 4],
        "idle": False,
        "warn": "점심시간 시스템 리프레시: 메모리 최적화를 위해 빠른 재부팅을 진행합니다."
    },
    {
        "title": "자리 비움 절전 모드",
        "mode": "sleep",
        "hour": "20",
        "min": "00",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "idle": True,
        "warn": "장시간 미사용 감지: 에너지 절약을 위해 절전 모드로 전환합니다."
    },
    {
        "title": "새벽 정기 시스템 점검 재시작",
        "mode": "reboot",
        "hour": "05",
        "min": "00",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "idle": False,
        "warn": "새벽 정기 점검: 시스템 안정성을 위해 예약 재부팅을 수행합니다."
    },
    {
        "title": "업무 시작 준비 알람",
        "mode": "alarm",
        "hour": "08",
        "min": "50",
        "days": [0, 1, 2, 3, 4],
        "idle": False,
        "warn": "업무 준비 알림: 곧 일과가 시작됩니다. 준비된 작업을 확인하세요."
    },
    {
        "title": "영화/영상 시청 후 종료",
        "mode": "shutdown",
        "hour": "01",
        "min": "00",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "idle": True,
        "warn": "야간 미디어 시청 완료: 절전을 위해 PC를 자동 종료합니다."
    },
    {
        "title": "미사용 모니터 화면 끄기",
        "mode": "screenoff",
        "hour": "21",
        "min": "00",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "idle": True,
        "warn": "모니터 번인 방지 및 절전을 위해 디스플레이 화면을 끕니다."
    },
    {
        "title": "렌더링/인코딩 완료 후 종료",
        "mode": "shutdown",
        "hour": "04",
        "min": "00",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "idle": True,
        "warn": "대용량 작업(인코딩/렌더링) 처리 후 PC 전원을 안전하게 끕니다."
    }
]


def ensure_firewall_rule_silent():
    """Windows Defender Firewall 예외 규칙을 무음(백그라운드) 등록하여 인바운드/공용 네트워크 차단 및 팝업 방지 (기본 및 버전 표기)"""
    if os.name == 'nt':
        try:
            exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.executable
            app_dir = os.path.dirname(os.path.abspath(exe_path))
            main_exe = os.path.join(app_dir, "PowerController.exe")
            fw_bat = os.path.join(app_dir, "Register_Firewall_Rules.bat")
            
            # [0] 순수 창작 FirewallNative.dll COM 직결 일괄 등록 (0.05초 만에 메모리 내 완수)
            if native_bridge and native_bridge.is_firewall_engine_loaded():
                try:
                    reg_cnt = native_bridge.batch_register_firewall_suite(app_dir, APP_VERSION)
                    if reg_cnt > 0:
                        return
                except Exception:
                    pass

            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)

            # 관리자 권한 확인
            is_admin = False
            try:
                import ctypes
                is_admin = (ctypes.windll.shell32.IsUserAnAdmin() != 0)
            except Exception:
                pass
            
            # [1] 커맨더 본체 (PowerNetworkScheduler.exe) 방화벽 등록 (기본 및 버전 표기)
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 "name=PowerNetworkScheduler (Inbound)", "dir=in", "action=allow", 
                 f"program={exe_path}", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 "name=PowerNetworkScheduler (Outbound)", "dir=out", "action=allow", 
                 f"program={exe_path}", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 f"name=PowerNetworkScheduler v{APP_VERSION} (Inbound)", "dir=in", "action=allow", 
                 f"program={exe_path}", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 f"name=PowerNetworkScheduler v{APP_VERSION} (Outbound)", "dir=out", "action=allow", 
                 f"program={exe_path}", "enable=yes", "profile=any"],
                capture_output=True,
                creationflags=creationflags
            )
            
            # [2] 동일 폴더의 메인 앱 (PowerController.exe) 방화벽 등록 (기본 및 버전 표기)
            if os.path.exists(main_exe):
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule", 
                     "name=PowerController (Inbound)", "dir=in", "action=allow", 
                     f"program={main_exe}", "enable=yes", "profile=any"],
                    capture_output=True,
                    creationflags=creationflags
                )
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule", 
                     "name=PowerController (Outbound)", "dir=out", "action=allow", 
                     f"program={main_exe}", "enable=yes", "profile=any"],
                    capture_output=True,
                    creationflags=creationflags
                )
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule", 
                     f"name=PowerController v{APP_VERSION} (Inbound)", "dir=in", "action=allow", 
                     f"program={main_exe}", "enable=yes", "profile=any"],
                    capture_output=True,
                    creationflags=creationflags
                )
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule", 
                     f"name=PowerController v{APP_VERSION} (Outbound)", "dir=out", "action=allow", 
                     f"program={main_exe}", "enable=yes", "profile=any"],
                    capture_output=True,
                    creationflags=creationflags
                )
            
            # [3] 전용 포트 허용 규칙 (TCP 9988, UDP 9985, UDP 9986)
            for p_name, proto, port in [
                ("PowerController TCP 9988", "TCP", "9988"),
                (f"PowerController v{APP_VERSION} TCP 9988", "TCP", "9988"),
                ("PowerController UDP 9985", "UDP", "9985"),
                (f"PowerController v{APP_VERSION} UDP 9985", "UDP", "9985"),
                ("PowerController UDP 9986", "UDP", "9986"),
                (f"PowerController v{APP_VERSION} UDP 9986", "UDP", "9986"),
            ]:
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule", 
                     f"name={p_name}", "dir=in", "action=allow", 
                     f"protocol={proto}", f"localport={port}", "enable=yes", "profile=any"],
                    capture_output=True,
                    creationflags=creationflags
                )

            # [4] 비관리자 실행 시 규칙 누락 여부 검사 및 1회 권한 승격(UAC) 연동
            if not is_admin:
                chk = subprocess.run(
                    ["netsh", "advfirewall", "firewall", "show", "rule", "name=PowerNetworkScheduler (Inbound)"],
                    capture_output=True,
                    creationflags=creationflags,
                    text=True,
                    errors="ignore"
                )
                rule_missing = ("No rules match" in chk.stdout or "규칙이 없습니다" in chk.stdout or chk.returncode != 0)
                if rule_missing and os.path.exists(fw_bat):
                    subprocess.run(
                        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", f"Start-Process '{fw_bat}' -Verb RunAs"],
                        creationflags=creationflags
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

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass

    return ips


def is_local_admin_ip(ip):
    """주어진 IP가 현재 관리자 PC의 자체 IP인지 판별합니다."""
    if not ip:
        return False
    return ip.strip() in get_all_local_ips()


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
        os.makedirs(os.path.dirname(appdata_path), exist_ok=True)
        return appdata_path


GROUPS_CONFIG_FILE = get_data_filepath("network_pc_groups.json")


def get_local_mac():
    """로컬 컴퓨터의 대표 MAC 주소를 16진수 문자열로 반환합니다."""
    try:
        node = uuid.getnode()
        mac = ':'.join(['{:02x}'.format((node >> i) & 0xff) for i in range(0, 48, 8)][::-1])
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
        match = re.search(r'([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})', res)
        if match:
            candidate = match.group(1).replace('-', ':').upper()
            if candidate != "00:00:00:00:00:00":
                return candidate
    except Exception:
        pass
    return ""


def send_wol_magic_packet(mac_address, target_ip=None, port=9):
    """
    Wake-on-LAN (WOL) Magic Packet 전송
    표준 매직 패킷: 6바이트의 0xFF + 16번 반복되는 6바이트의 MAC 주소 (총 102바이트)
    """
    if not mac_address:
        return {"success": False, "message": "MAC 주소가 등록되어 있지 않습니다."}
        
    clean_mac = re.sub(r'[^0-9a-fA-F]', '', mac_address)
    if len(clean_mac) != 12:
        return {
            "success": False,
            "message": f"올바르지 않은 MAC 주소 형식입니다: '{mac_address}' (12자리 16진수 필요)"
        }

    mac_bytes = bytes.fromhex(clean_mac)
    magic_packet = b'\xff' * 6 + mac_bytes * 16

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    destinations = [("255.255.255.255", port), ("255.255.255.255", 7)]
    if target_ip and target_ip != "127.0.0.1":
        parts = target_ip.split('.')
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

    formatted_mac = ":".join([clean_mac[i:i+2].upper() for i in range(0, 12, 2)])
    return {
        "success": True,
        "mac": formatted_mac,
        "message": f"매직 패킷 브로드캐스트 전송 성공 ({sent_routes}개 경로)"
    }


def extract_ip_from_list_item(text):
    """목록 항목 문자열에서 IPv4 주소만을 정확하게 추출합니다."""
    if not text:
        return ""
    match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)
    if match:
        return match.group(0)
    return ""


# -------------------------------------------------------------------------
# 2. 송신용 클라이언트 함수 및 방화벽 우회 비콘 동기화 허브
# -------------------------------------------------------------------------
DISCOVERED_CLIENTS = {}
PENDING_RESPONSES = {}
GLOBAL_APP_INSTANCE = None
_hub_started = False


def start_scheduler_sync_hub():
    """방화벽 '허용'이 비활성화된 클라이언트의 자동 비콘 및 ACK를 수신하는 UDP 허브 (순수 창작 NetBeaconEngine 연동)"""
    global _hub_started
    if _hub_started:
        return
    _hub_started = True

    # 1. 순수 창작 C 레벨 NetBeaconEngine 가동 우선 시도 (500대 이상 PC 감시 시 CPU 0.0%)
    if native_bridge and native_bridge.is_beacon_engine_loaded():
        if native_bridge.start_beacon_listener(9986):
            def native_hub_dispatcher():
                while True:
                    pkt = native_bridge.poll_next_beacon_packet()
                    if pkt:
                        try:
                            msg = json.loads(pkt["data"])
                            addr = (pkt["ip"], pkt["port"])

                            # 1. 클라이언트 비콘 폴링 수신
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
                                    "bypass_ready": True
                                }
                                if GLOBAL_APP_INSTANCE:
                                    try:
                                        GLOBAL_APP_INSTANCE.root.after(
                                            0,
                                            lambda ip=c_ip, h=c_host, m=c_mac: GLOBAL_APP_INSTANCE.on_beacon_pc_discovered(ip, h, m)
                                        )
                                    except Exception:
                                        pass

                            # 2. 클라이언트 ACK 응답 수신
                            if "reply_to" in msg or "success" in msg:
                                c_ip = addr[0]
                                if c_ip in PENDING_RESPONSES:
                                    PENDING_RESPONSES[c_ip]["resp"] = msg
                                    PENDING_RESPONSES[c_ip]["event"].set()
                                for pending_ip, p_data in list(PENDING_RESPONSES.items()):
                                    if not p_data["event"].is_set():
                                        p_data["resp"] = msg
                                        p_data["event"].set()
                        except Exception:
                            pass
                    else:
                        time.sleep(0.01)

            t_native = threading.Thread(target=native_hub_dispatcher, daemon=True)
            t_native.start()
            return

    # 2. Fallback: Python 표준 소켓 허브 워커
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

                # 1. 클라이언트 비콘 폴링 수신
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
                        "bypass_ready": True
                    }
                    if GLOBAL_APP_INSTANCE:
                        try:
                            GLOBAL_APP_INSTANCE.root.after(
                                0,
                                lambda ip=c_ip, h=c_host, m=c_mac: GLOBAL_APP_INSTANCE.on_beacon_pc_discovered(ip, h, m)
                            )
                        except Exception:
                            pass

                # 2. 클라이언트 ACK 응답 수신
                if "reply_to" in msg or "success" in msg:
                    c_ip = addr[0]
                    if c_ip in PENDING_RESPONSES:
                        PENDING_RESPONSES[c_ip]["resp"] = msg
                        PENDING_RESPONSES[c_ip]["event"].set()
                    for pending_ip, p_data in list(PENDING_RESPONSES.items()):
                        if not p_data["event"].is_set():
                            p_data["resp"] = msg
                            p_data["event"].set()
            except Exception:
                time.sleep(0.1)

    t = threading.Thread(target=hub_worker, daemon=True)
    t.start()


def send_via_bypass_channel(ip, payload):
    """
    클라이언트 PC의 방화벽 '허용' 버튼이 비활성화되었거나 인바운드가 차단된 환경에서도
    클라이언트가 무조작으로 토큰/명령을 수신할 수 있도록 역방향 UDP 및 브로드캐스트 채널을 통해 전송합니다.
    """
    evt = threading.Event()
    PENDING_RESPONSES[ip] = {"resp": None, "event": evt}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(2.2)

    # 순수 창작 ScheduleCrypto 전자 서명(HMAC-SHA256) 자동 부착
    if "signature" not in payload and native_bridge:
        try:
            raw_to_sign = json.dumps({k: v for k, v in payload.items() if k != "signature"}, sort_keys=True, ensure_ascii=False)
            payload["signature"] = native_bridge.generate_schedule_hmac(raw_to_sign)
        except Exception:
            pass

    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    target_addr = (ip, 9985)
    if ip in DISCOVERED_CLIENTS and "addr" in DISCOVERED_CLIENTS[ip]:
        target_addr = DISCOVERED_CLIENTS[ip]["addr"]

    # 순수 창작 NetBeaconEngine 고속 C 소켓 발송 시도
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

    # 1. 클라이언트가 응답을 송신 소켓(sock)으로 직접 회신한 경우 수신
    try:
        resp_data, _ = sock.recvfrom(8192)
        if resp_data:
            resp = json.loads(resp_data.decode("utf-8"))
            sock.close()
            msg = resp.get("message", "성공")
            resp["message"] = f"{msg} (🛡️ 방화벽 무조작 우회 통과)"
            return resp
    except Exception:
        pass

    # 2. 허브 리스너를 통해 ACK가 도착한 경우 보조 확인
    signaled = evt.wait(timeout=0.3)
    sock.close()

    if signaled and PENDING_RESPONSES.get(ip, {}).get("resp"):
        resp = PENDING_RESPONSES[ip]["resp"]
        msg = resp.get("message", "성공")
        resp["message"] = f"{msg} (🛡️ 방화벽 무조작 우회 통과)"
        return resp

    return {
        "success": False,
        "message": f"클라이언트({ip}) 응답 없음 (방화벽 및 네트워크 수신 대기 초과)"
    }


def send_payload_over_network(ip, port, payload):
    """지정된 원격 IP/Port로 JSON 페이로드를 전송하고 응답 ACK를 반환합니다."""
    # 1. 우선 표준 TCP 연결 시도 (1.2초 빠른 타임아웃)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.2)
        sock.connect((ip, port))
        sock.sendall(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        resp_data = sock.recv(4096)
        sock.close()
        if resp_data:
            return json.loads(resp_data.decode("utf-8"))
    except Exception:
        pass

    # 2. 클라이언트의 '허용' 버튼 비활성화 / 방화벽 차단 시 무조작 우회 채널로 자동 전송
    return send_via_bypass_channel(ip, payload)


def send_rule_over_network(ip, port, rule_data, overwrite, auth_token=""):
    """스케줄 규칙 등록 페이로드를 조립하여 전송합니다."""
    payload = {
        "action": "register_schedule",
        "auth_token": auth_token,
        "overwrite": overwrite,
        # 1. 동작 모드 및 강제 종료 플래그
        "label": rule_data.get("label", "원격 자동 제어"),
        "type": "daily" if len(rule_data.get("days", [])) == 7 else "weekly",
        "mode": rule_data.get("mode", "shutdown"),
        "time": rule_data.get("time", "23:00"),
        "days": rule_data.get("days", [0, 1, 2, 3, 4, 5, 6]),
        "interval_min": 0,
        "force_close": rule_data.get("force_close", True),
        # 2. 사전 알림 및 유예 카운트다운
        "warning_message": rule_data.get("warning_message", ""),
        "grace_period_sec": rule_data.get("grace_period_sec", 10),
        "allow_delay": rule_data.get("allow_delay", True),
        "warning_beep": rule_data.get("warning_beep", True),
        # 3. 조건부 유휴 시간 감지 트리거
        "idle_only": rule_data.get("idle_only", False),
        "idle_minutes": rule_data.get("idle_minutes", 15),
        # 4. 사전 작업 자동화
        "clean_temp": rule_data.get("clean_temp", False),
        "pre_command": rule_data.get("pre_command", "")
    }
    return send_payload_over_network(ip, port, payload)


def send_clear_schedules(ip, port, auth_token=""):
    """원격 대상 컴퓨터의 스케줄을 전체 초기화(삭제)합니다."""
    payload = {
        "action": "clear_schedules",
        "auth_token": auth_token
    }
    return send_payload_over_network(ip, port, payload)


def query_remote_status(ip, port, auth_token=""):
    """원격 대상 컴퓨터의 현재 등록된 규칙 수 및 수신 상태를 조회합니다."""
    payload = {
        "action": "query_status",
        "auth_token": auth_token
    }
    return send_payload_over_network(ip, port, payload)


def send_immediate_power_action(ip, port, power_cmd="shutdown", force=True, grace_period_sec=3, auth_token=""):
    """
    원격 대상 컴퓨터에 즉시 전원 실행 명령(종료 또는 다시 시작)을 전송합니다.
    power_cmd: 'shutdown' (시스템 종료) 또는 'reboot' (다시 시작)
    """
    payload = {
        "action": "immediate_power",
        "power_cmd": power_cmd,
        "force": force,
        "grace_period_sec": grace_period_sec,
        "auth_token": auth_token
    }
    return send_payload_over_network(ip, port, payload)


def send_verify_token(ip, port, auth_token=""):
    """원격 대상 컴퓨터에 보안 인증 토큰만 전송하여 인증 검증을 요청합니다."""
    payload = {
        "action": "verify_token",
        "auth_token": auth_token
    }
    return send_payload_over_network(ip, port, payload)


def send_set_remote_token(ip, port, current_auth_token="", new_token=""):
    """원격 대상 컴퓨터에 보안 인증 토큰을 전송하여 클라이언트에 등록/저장합니다."""
    payload = {
        "action": "set_token",
        "auth_token": current_auth_token,
        "new_token": new_token
    }
    return send_payload_over_network(ip, port, payload)


DEFAULT_MASTER_RECOVERY_KEY = "PowerRescue#2026!Admin"

def get_master_recovery_key():
    """
    관리자가 보안 인증 토큰을 분실하였을 때 사용하는 마스터 비상 복구 키 반환.
    환경변수 POWER_TIMER_MASTER_KEY 또는 power_master_key.txt 파일이 있으면 최우선 적용합니다.
    """
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
    """
    보안 토큰을 분실한 관리자를 위해 마스터 복구 키를 사용하여
    원격 클라이언트의 보안 토큰을 강제로 재설정하거나 초기화(공백)합니다.
    """
    payload = {
        "action": "emergency_reset_token",
        "master_key": master_key,
        "new_token": new_token
    }
    return send_payload_over_network(ip, port, payload)


def send_query_remote_token(ip, port, master_key):
    """
    마스터 복구 키를 사용하여 원격 클라이언트에 현재 설정된 기존 토큰을 확인(읽어오기)합니다.
    """
    payload = {
        "action": "query_token",
        "master_key": master_key
    }
    return send_payload_over_network(ip, port, payload)


def extract_ip_from_list_item(text):
    """목록 항목 문자열에서 IPv4 주소를 안전하게 추출합니다."""
    if not text:
        return ""
    m = re.search(r'(\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b)', text)
    return m.group(1) if m else ""


# -------------------------------------------------------------------------
# 3. 통합 컨트롤 타워 UI 클래스 (Tkinter)
# -------------------------------------------------------------------------
class NetworkSchedulerApp:
    def __init__(self, root):
        global GLOBAL_APP_INSTANCE
        GLOBAL_APP_INSTANCE = self

        self.root = root
        self.root.title(f"PowerController 네트워크 스케줄 전송 및 그룹 관리 도구 (v{APP_VERSION})")
        self.root.geometry("1020x720")
        self.root.resizable(True, True)
        self.root.minsize(920, 620)
        
        # 윈도우 방화벽 인바운드/아웃바운드 차단 및 팝업 방지 무음 등록
        ensure_firewall_rule_silent()

        # 방화벽 무조작 우회 통신을 위한 자동 동기화 허브 백그라운드 구동
        start_scheduler_sync_hub()

        self.last_scanned_active_ips = set()
        self.load_pc_groups_data()

        self.setup_styles()
        self.create_layout()

        self.refresh_group_combobox()
        self.refresh_pc_listbox()

    def setup_styles(self):
        self.bg_color = "#1e1e24"
        self.card_color = "#2a2a35"
        self.subcard_color = "#23232c"
        self.text_color = "#f3f4f6"
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
        style.configure("SubCardLabel.TLabel", background=self.subcard_color, foreground=self.text_color, font=("Arial", 8))
        style.configure("Title.TLabel", background=self.bg_color, foreground=self.text_color, font=("Arial", 13, "bold"))
        
        style.configure("TButton", background=self.accent_color, foreground="white", font=("Arial", 9, "bold"), borderwidth=0)
        style.map("TButton", background=[("active", "#2563eb"), ("disabled", "#4b5563")])
        
        style.configure("Green.TButton", background=self.accent_green, foreground="white", font=("Arial", 10, "bold"), borderwidth=0)
        style.map("Green.TButton", background=[("active", "#059669")])
        
        style.configure("Red.TButton", background=self.accent_red, foreground="white", font=("Arial", 9, "bold"), borderwidth=0)
        style.map("Red.TButton", background=[("active", "#dc2626")])

        style.configure("Orange.TButton", background=self.accent_orange, foreground="white", font=("Arial", 9, "bold"), borderwidth=0)
        style.map("Orange.TButton", background=[("active", "#d97706")])

        style.configure("Purple.TButton", background="#8b5cf6", foreground="white", font=("Arial", 9, "bold"), borderwidth=0)
        style.map("Purple.TButton", background=[("active", "#7c3aed")])

        style.configure("Teal.TButton", background="#0d9488", foreground="white", font=("Arial", 9, "bold"), borderwidth=0)
        style.map("Teal.TButton", background=[("active", "#0f766e")])

    def create_layout(self):
        # 상단 타이틀 바
        header_frame = tk.Frame(self.root, bg=self.bg_color, pady=10)
        header_frame.pack(fill="x")
        
        title_lbl = ttk.Label(header_frame, text="⚡ PowerController 네트워크 원격 스케줄러 & 관리 타워", style="Title.TLabel")
        title_lbl.pack(side="left", padx=16)

        local_ip_lbl = ttk.Label(header_frame, text=f"내 IP: {get_local_ip()}", foreground="#9ca3af", font=("Arial", 8))
        local_ip_lbl.pack(side="right", padx=16)

        btn_license = tk.Button(
            header_frame,
            text="📜 라이선스 (License)",
            font=("Arial", 8, "bold"),
            bg="#374151",
            fg="#e5e7eb",
            activebackground="#4b5563",
            activeforeground="white",
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
            command=self.show_license_dialog
        )
        btn_license.pack(side="right", padx=(0, 8))
        
        # 메인 좌우 2분할 레이아웃
        main_content_frame = tk.Frame(self.root, bg=self.bg_color)
        main_content_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        
        # ==================== [왼쪽: 스케줄 및 정책 구성 카드] ====================
        left_container = tk.Frame(main_content_frame, bg=self.bg_color)
        left_container.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # 스크롤 가능한 캔버스 영역
        canvas = tk.Canvas(left_container, bg=self.bg_color, highlightthickness=0)
        v_scroll = tk.Scrollbar(left_container, orient="vertical", command=canvas.yview)
        form_card = ttk.Frame(canvas, style="Card.TFrame", padding=12)

        form_card.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=form_card, anchor="nw")
        
        def on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)
        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=v_scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

        # ------------------ 섹션 1: 대상 IP 및 보안 인증 ------------------
        sec1_frame = tk.LabelFrame(form_card, text=" 1. 대상 원격 PC 및 보안 인증 ", bg=self.card_color, fg="#60a5fa", font=("Arial", 9, "bold"), padx=8, pady=6)
        sec1_frame.pack(fill="x", pady=(0, 8))

        # IP
        f_ip = tk.Frame(sec1_frame, bg=self.card_color)
        f_ip.pack(fill="x", pady=2)
        tk.Label(
            f_ip,
            text="대상 IP 주소:",
            bg=self.card_color,
            fg="#93c5fd",
            font=("Arial", 9, "bold"),
            width=14,
            anchor="w"
        ).pack(side="left")
        self.entry_ip = tk.Entry(
            f_ip,
            bg="#111827",
            fg="#38bdf8",
            readonlybackground="#1e293b",
            disabledbackground="#1e293b",
            disabledforeground="#38bdf8",
            insertbackground="#38bdf8",
            selectbackground="#2563eb",
            selectforeground="#ffffff",
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightcolor="#38bdf8",
            highlightbackground="#374151",
            font=("Arial", 9, "bold")
        )
        self.entry_ip.insert(0, "192.168.0.")
        self.entry_ip.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Port & Token
        f_pt = tk.Frame(sec1_frame, bg=self.card_color)
        f_pt.pack(fill="x", pady=2)
        ttk.Label(f_pt, text="포트 (Port):", style="CardLabel.TLabel", width=14).pack(side="left")
        self.entry_port = tk.Entry(f_pt, bg="#1f2937", fg="white", insertbackground="white", relief="flat", width=8)
        self.entry_port.insert(0, str(DEFAULT_PORT))
        self.entry_port.pack(side="left", padx=(4, 15))

        ttk.Label(f_pt, text="🔑 보안 토큰(비번):", style="CardLabel.TLabel").pack(side="left")
        self.entry_token = tk.Entry(f_pt, bg="#1f2937", fg="#fbbf24", insertbackground="white", relief="flat", width=14, show="*")
        self.entry_token.pack(side="left", padx=(4, 5))

        self.show_token_var = tk.BooleanVar(value=False)
        def toggle_token_show():
            self.entry_token.config(show="" if self.show_token_var.get() else "*")
        chk_show_token = tk.Checkbutton(
            f_pt, text="표시", variable=self.show_token_var, command=toggle_token_show,
            bg=self.card_color, fg="#9ca3af", selectcolor="#1f2937", activebackground=self.card_color,
            font=("Arial", 7)
        )
        chk_show_token.pack(side="left", padx=(0, 6))

        self.btn_send_token_quick = ttk.Button(
            f_pt, text="🔐 토큰만 전송", style="Purple.TButton", command=self.on_send_token_only_click
        )
        self.btn_send_token_quick.pack(side="left", padx=(2, 0))

        self.btn_emergency_recovery = ttk.Button(
            f_pt, text="🚨 토큰 분실 복구", style="Red.TButton", command=self.on_emergency_recovery_click
        )
        self.btn_emergency_recovery.pack(side="left", padx=(4, 0))

        # ------------------ 섹션 2: 전원 동작 및 시간 설정 (1. 모드 확장) ------------------
        sec2_frame = tk.LabelFrame(form_card, text=" 2. 전원 제어 방식 및 스케줄 시각 ", bg=self.card_color, fg="#60a5fa", font=("Arial", 9, "bold"), padx=8, pady=6)
        sec2_frame.pack(fill="x", pady=(0, 8))

        f_lbl_header = tk.Frame(sec2_frame, bg=self.card_color)
        f_lbl_header.pack(fill="x", pady=(2, 0))
        ttk.Label(f_lbl_header, text="예약 규칙명 (메모):", style="CardLabel.TLabel").pack(side="left")
        
        # 10대 자주 쓰는 제목 프리셋 선택 콤보박스 (메인 앱 변경점 통합)
        self.preset_combo = ttk.Combobox(
            f_lbl_header,
            values=["📋 자주 쓰는 제목 (10개 선택)..."] + [f"{i+1}. {p['title']}" for i, p in enumerate(POPULAR_SCHEDULE_PRESETS)],
            state="readonly",
            width=28
        )
        self.preset_combo.current(0)
        self.preset_combo.pack(side="right")
        self.preset_combo.bind("<<ComboboxSelected>>", self.on_preset_title_selected)

        f_lbl = tk.Frame(sec2_frame, bg=self.card_color)
        f_lbl.pack(fill="x", pady=2)
        self.entry_label = tk.Entry(f_lbl, bg="#1f2937", fg="white", insertbackground="white", relief="flat")
        self.entry_label.insert(0, "심야 PC 자동 종료")
        self.entry_label.pack(side="left", fill="x", expand=True, padx=(4, 0))

        f_mode = tk.Frame(sec2_frame, bg=self.card_color)
        f_mode.pack(fill="x", pady=2)
        ttk.Label(f_mode, text="전원 동작 모드:", style="CardLabel.TLabel", width=14).pack(side="left")
        
        # 1. 8대 전원 및 동작 모드 확장
        self.mode_keys = ["shutdown", "reboot", "sleep", "hibernate", "lock", "screenoff", "logout", "alarm"]
        self.combo_mode = ttk.Combobox(
            f_mode, 
            values=[
                "🔴 시스템 종료 (shutdown)",
                "🔄 다시 시작 (reboot)",
                "🌙 절전 모드 (sleep)",
                "💤 최대 절전 (hibernate)",
                "🔒 화면 잠금 (lock)",
                "🖥️ 화면 끄기 (screenoff)",
                "🚪 로그아웃 (logout)",
                "⏰ 사운드 알람 (alarm)"
            ],
            state="readonly",
            width=22
        )
        self.combo_mode.current(0)
        self.combo_mode.pack(side="left", padx=(4, 15))

        # 강제 종료 여부 체크박스
        self.force_close_var = tk.BooleanVar(value=True)
        chk_force = tk.Checkbutton(
            f_mode, text="응용 프로그램 강제 닫기 (/f)", variable=self.force_close_var,
            bg=self.card_color, fg=self.text_color, selectcolor="#1f2937", activebackground=self.card_color,
            font=("Arial", 8)
        )
        chk_force.pack(side="left")

        # 시간 및 요일
        f_time = tk.Frame(sec2_frame, bg=self.card_color)
        f_time.pack(fill="x", pady=2)
        ttk.Label(f_time, text="실행 시각 (24H):", style="CardLabel.TLabel", width=14).pack(side="left")
        self.entry_hour = tk.Entry(f_time, bg="#1f2937", fg="white", insertbackground="white", relief="flat", width=4, justify="center")
        self.entry_hour.insert(0, "23")
        self.entry_hour.pack(side="left", padx=(4, 0))
        ttk.Label(f_time, text="시 ", style="CardLabel.TLabel").pack(side="left")
        self.entry_min = tk.Entry(f_time, bg="#1f2937", fg="white", insertbackground="white", relief="flat", width=4, justify="center")
        self.entry_min.insert(0, "45")
        self.entry_min.pack(side="left")
        ttk.Label(f_time, text="분", style="CardLabel.TLabel").pack(side="left")

        # 요일 선택
        f_days = tk.Frame(sec2_frame, bg=self.card_color)
        f_days.pack(fill="x", pady=3)
        ttk.Label(f_days, text="적용 요일:", style="CardLabel.TLabel", width=14).pack(side="left")
        self.day_vars = []
        for name in ["월", "화", "수", "목", "금", "토", "일"]:
            var = tk.BooleanVar(value=True)
            self.day_vars.append(var)
            chk = tk.Checkbutton(
                f_days, text=name, variable=var, bg=self.card_color, fg=self.text_color,
                selectcolor="#1f2937", activebackground=self.card_color, font=("Arial", 8)
            )
            chk.pack(side="left", padx=1)

        # ------------------ 섹션 3: 사전 알림 및 유예 카운트다운 ------------------
        sec3_frame = tk.LabelFrame(form_card, text=" 3. 사전 경고 알림 & 카운트다운 유예 정책 ", bg=self.card_color, fg="#60a5fa", font=("Arial", 9, "bold"), padx=8, pady=6)
        sec3_frame.pack(fill="x", pady=(0, 8))

        f_warn_msg = tk.Frame(sec3_frame, bg=self.card_color)
        f_warn_msg.pack(fill="x", pady=2)
        ttk.Label(f_warn_msg, text="경고 안내문:", style="CardLabel.TLabel", width=14).pack(side="left")
        self.entry_warn_msg = tk.Entry(f_warn_msg, bg="#1f2937", fg="white", insertbackground="white", relief="flat")
        self.entry_warn_msg.insert(0, "관리자 예약 종료 안내: 작업 중인 문서를 안전하게 저장하십시오.")
        self.entry_warn_msg.pack(side="left", fill="x", expand=True, padx=(4, 0))

        f_grace_opts = tk.Frame(sec3_frame, bg=self.card_color)
        f_grace_opts.pack(fill="x", pady=3)
        ttk.Label(f_grace_opts, text="유예 시간(초):", style="CardLabel.TLabel", width=14).pack(side="left")
        self.combo_grace = ttk.Combobox(f_grace_opts, values=["5초", "10초", "30초", "60초", "120초"], state="readonly", width=8)
        self.combo_grace.current(1)
        self.combo_grace.pack(side="left", padx=(4, 15))

        self.allow_delay_var = tk.BooleanVar(value=True)
        chk_delay = tk.Checkbutton(
            f_grace_opts, text="사용자 10분 연기 및 취소 허용", variable=self.allow_delay_var,
            bg=self.card_color, fg=self.text_color, selectcolor="#1f2937", activebackground=self.card_color,
            font=("Arial", 8)
        )
        chk_delay.pack(side="left", padx=(0, 10))

        self.warning_beep_var = tk.BooleanVar(value=True)
        chk_beep = tk.Checkbutton(
            f_grace_opts, text="경고음 재생", variable=self.warning_beep_var,
            bg=self.card_color, fg=self.text_color, selectcolor="#1f2937", activebackground=self.card_color,
            font=("Arial", 8)
        )
        chk_beep.pack(side="left")

        # ------------------ 섹션 4: 조건부 트리거 및 사전 작업 자동화 ------------------
        sec4_frame = tk.LabelFrame(form_card, text=" 4. 조건부 유휴 감지 & 사전 작업 자동화 ", bg=self.card_color, fg="#60a5fa", font=("Arial", 9, "bold"), padx=8, pady=6)
        sec4_frame.pack(fill="x", pady=(0, 8))

        # 유휴 시간 감지
        f_idle = tk.Frame(sec4_frame, bg=self.card_color)
        f_idle.pack(fill="x", pady=2)
        self.idle_only_var = tk.BooleanVar(value=False)
        chk_idle = tk.Checkbutton(
            f_idle, text="사용자 PC 유휴(미사용) 상태일 때만 실행", variable=self.idle_only_var,
            bg=self.card_color, fg=self.text_color, selectcolor="#1f2937", activebackground=self.card_color,
            font=("Arial", 8, "bold")
        )
        chk_idle.pack(side="left")

        ttk.Label(f_idle, text="필요 유휴 시간:", style="CardLabel.TLabel").pack(side="left", padx=(15, 4))
        self.combo_idle_min = ttk.Combobox(f_idle, values=["5분", "10분", "15분", "30분", "60분"], state="readonly", width=6)
        self.combo_idle_min.current(2)
        self.combo_idle_min.pack(side="left")

        # 사전 정리 및 명령어
        f_clean = tk.Frame(sec4_frame, bg=self.card_color)
        f_clean.pack(fill="x", pady=2)
        self.clean_temp_var = tk.BooleanVar(value=False)
        chk_clean = tk.Checkbutton(
            f_clean, text="종료 전 %TEMP% 임시 파일 자동 정리", variable=self.clean_temp_var,
            bg=self.card_color, fg=self.text_color, selectcolor="#1f2937", activebackground=self.card_color,
            font=("Arial", 8)
        )
        chk_clean.pack(side="left")

        f_precmd = tk.Frame(sec4_frame, bg=self.card_color)
        f_precmd.pack(fill="x", pady=2)
        ttk.Label(f_precmd, text="사전 실행 명령어:", style="CardLabel.TLabel", width=14).pack(side="left")
        self.entry_precmd = tk.Entry(f_precmd, bg="#1f2937", fg="#a7f3d0", insertbackground="white", relief="flat")
        self.entry_precmd.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # ------------------ 섹션 5: 전송 및 원격 제어 버튼 영역 ------------------
        f_ops = tk.Frame(form_card, bg=self.card_color)
        f_ops.pack(fill="x", pady=(4, 0))

        ttk.Label(f_ops, text="규칙 적용 옵션:", style="CardLabel.TLabel").pack(side="left")
        self.apply_option = tk.StringVar(value="append")
        rb_app = tk.Radiobutton(
            f_ops, text="추가 (Append)", variable=self.apply_option, value="append",
            bg=self.card_color, fg=self.text_color, selectcolor="#1f2937", activebackground=self.card_color, font=("Arial", 8)
        )
        rb_app.pack(side="left", padx=5)
        rb_ovw = tk.Radiobutton(
            f_ops, text="덮어쓰기 (Overwrite)", variable=self.apply_option, value="overwrite",
            bg=self.card_color, fg=self.text_color, selectcolor="#1f2937", activebackground=self.card_color, font=("Arial", 8)
        )
        rb_ovw.pack(side="left", padx=5)

        # 액션 버튼 모음
        btn_action_frame = tk.Frame(form_card, bg=self.card_color)
        btn_action_frame.pack(fill="x", pady=(10, 0))

        btn_send = ttk.Button(btn_action_frame, text="🚀 원격 컴퓨터로 예약 규칙 전송 (Send)", style="Green.TButton", command=self.on_send_click)
        btn_send.pack(side="left", fill="x", expand=True, padx=(0, 4))

        btn_send_token = ttk.Button(btn_action_frame, text="🔐 보안 토큰만 전송 (Token)", style="Purple.TButton", command=self.on_send_token_only_click)
        btn_send_token.pack(side="left", padx=(0, 4))

        btn_recovery = ttk.Button(btn_action_frame, text="🚨 토큰 분실 복구", style="Red.TButton", command=self.on_emergency_recovery_click)
        btn_recovery.pack(side="left", padx=(0, 4))

        btn_clear = ttk.Button(btn_action_frame, text="🗑️ 원격 예약 전체 초기화 (Clear All)", style="Red.TButton", command=self.on_clear_remote_click)
        btn_clear.pack(side="right")

        # ------------------ 섹션 6: ⚡ 원격 PC 즉시 실행 제어 (Immediate Power Actions) ------------------
        sec_immediate = tk.LabelFrame(
            form_card, 
            text=" ⚡ 원격 PC 즉시 실행 제어 (Immediate Power Actions) ", 
            bg=self.card_color, 
            fg="#f87171", 
            font=("Arial", 9, "bold"), 
            padx=8, 
            pady=6
        )
        sec_immediate.pack(fill="x", pady=(10, 0))

        f_imm_btns = tk.Frame(sec_immediate, bg=self.card_color)
        f_imm_btns.pack(fill="x")

        self.btn_imm_shutdown = tk.Button(
            f_imm_btns,
            text="🛑 대상 PC 즉시 종료 (Shutdown Now)",
            font=("Arial", 9, "bold"),
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.on_immediate_power_click("shutdown")
        )
        self.btn_imm_shutdown.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_imm_reboot = tk.Button(
            f_imm_btns,
            text="🔄 대상 PC 즉시 다시시작 (Reboot Now)",
            font=("Arial", 9, "bold"),
            bg="#d97706",
            fg="white",
            activebackground="#b45309",
            activeforeground="white",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.on_immediate_power_click("reboot")
        )
        self.btn_imm_reboot.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # ==================== [오른쪽: 활성 PC 감지, 그룹화 & WOL 및 ACK 로그] ====================
        right_frame = tk.Frame(main_content_frame, bg=self.bg_color, width=380)
        right_frame.pack(side="right", fill="both", padx=(8, 0))
        right_frame.pack_propagate(False)
        
        ttk.Label(right_frame, text="📡 대기 PC 및 그룹 관리 (Remote PCs & Groups)", style="TLabel", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 4))
        
        # 1. 그룹 선택 바 & 관리 버튼
        f_group_bar = tk.Frame(right_frame, bg=self.bg_color)
        f_group_bar.pack(fill="x", pady=(0, 4))
        
        ttk.Label(f_group_bar, text="📁 그룹:", style="TLabel", font=("Arial", 8, "bold")).pack(side="left", padx=(0, 4))
        self.selected_group_var = tk.StringVar(value="📁 전체 PC (All)")
        self.combo_group = ttk.Combobox(f_group_bar, textvariable=self.selected_group_var, state="readonly", font=("Arial", 8), width=18)
        self.combo_group.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.combo_group.bind("<<ComboboxSelected>>", self.on_group_filter_changed)
        
        self.btn_manage_group = ttk.Button(f_group_bar, text="⚙️ 그룹 관리", style="TButton", command=self.open_group_manager)
        self.btn_manage_group.pack(side="right")

        # 2. 그룹 일괄 선택 및 그룹 WOL 원격 부팅 버튼 바
        f_group_actions = tk.Frame(right_frame, bg=self.bg_color)
        f_group_actions.pack(fill="x", pady=(0, 4))

        self.btn_select_group = tk.Button(
            f_group_actions, text="☑️ 그룹 선택", font=("Arial", 8, "bold"),
            bg="#374151", fg="white", activebackground="#4b5563", activeforeground="white",
            relief="flat", padx=6, pady=3, cursor="hand2", command=self.select_all_in_current_group
        )
        self.btn_select_group.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.btn_deselect_all = tk.Button(
            f_group_actions, text="☐ 전체 해제", font=("Arial", 8),
            bg="#374151", fg="#d1d5db", activebackground="#4b5563", activeforeground="white",
            relief="flat", padx=6, pady=3, cursor="hand2", command=self.deselect_all_pcs
        )
        self.btn_deselect_all.pack(side="left", padx=(2, 2))

        self.btn_group_wol = tk.Button(
            f_group_actions, text="⚡ 그룹 WOL 부팅", font=("Arial", 8, "bold"),
            bg="#059669", fg="white", activebackground="#047857", activeforeground="white",
            relief="flat", padx=6, pady=3, cursor="hand2", command=self.on_group_wol_click
        )
        self.btn_group_wol.pack(side="right", fill="x", expand=True, padx=(2, 0))

        # 3. PC 탐색 검색 버튼 및 상태 조회 버튼
        btn_box = tk.Frame(right_frame, bg=self.bg_color)
        btn_box.pack(fill="x", pady=(0, 4))
        
        self.btn_scan = ttk.Button(btn_box, text="🔍 대기 PC 검색", style="TButton", command=self.discover_waiting_pcs)
        self.btn_scan.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_query = ttk.Button(btn_box, text="📊 상태 조회", style="Orange.TButton", command=self.on_query_status_click)
        self.btn_query.pack(side="right", padx=(3, 0))

        # 4. 중복 스캔 시 기존 PC 검색결과 유지 옵션 체크박스
        self.preserve_scanned_pcs = tk.BooleanVar(value=True)
        self.chk_preserve = tk.Checkbutton(
            right_frame,
            text="기존 탐색 및 오프라인 등록 PC 유지",
            variable=self.preserve_scanned_pcs,
            bg=self.bg_color,
            fg=self.text_color,
            selectcolor="#111827",
            activebackground=self.bg_color,
            activeforeground=self.text_color,
            font=("Arial", 8)
        )
        self.chk_preserve.pack(fill="x", pady=(0, 4))
        
        # 5. Listbox & Scrollbar
        list_container = tk.Frame(right_frame, bg=self.bg_color, height=180)
        list_container.pack(fill="x", pady=(0, 6))
        
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side="right", fill="y")
        
        self.pc_listbox = tk.Listbox(
            list_container, bg="#111827", fg="#10b981", selectbackground=self.accent_color,
            selectforeground="white", relief="flat", yscrollcommand=scrollbar.set,
            font=("Courier", 8, "bold"), highlightthickness=0, height=8
        )
        self.pc_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.pc_listbox.yview)
        
        self.pc_listbox.bind("<ButtonRelease-1>", self.on_pc_click)
        self.pc_listbox.bind("<Double-Button-1>", self.on_pc_double_click)

        # 6. 우클릭 컨텍스트 메뉴 (WOL, 그룹 이동, PC 정보 편집, 즉시 제어)
        self.pc_context_menu = tk.Menu(self.root, tearoff=0, bg="#1f2937", fg="white", activebackground="#3b82f6", activeforeground="white")
        self.pc_context_menu.add_command(label="⚡ 이 PC 원격 부팅 (Wake-on-LAN)", command=self.on_context_menu_wol)
        
        self.group_submenu = tk.Menu(self.pc_context_menu, tearoff=0, bg="#1f2937", fg="white", activebackground="#3b82f6", activeforeground="white")
        self.pc_context_menu.add_cascade(label="📁 그룹 지정 / 이동 (Assign Group)", menu=self.group_submenu)
        
        self.pc_context_menu.add_command(label="✏️ PC 정보 및 MAC 주소 편집...", command=self.on_context_menu_edit_pc)
        self.pc_context_menu.add_separator()
        self.pc_context_menu.add_command(label="🛑 이 PC 즉시 종료 (Shutdown Now)", command=lambda: self.on_context_menu_power("shutdown"))
        self.pc_context_menu.add_command(label="🔄 이 PC 즉시 다시시작 (Reboot Now)", command=lambda: self.on_context_menu_power("reboot"))
        self.pc_context_menu.add_separator()
        self.pc_context_menu.add_command(label="📊 이 PC 상태 조회", command=self.on_query_status_click)
        self.pc_context_menu.add_command(label="🗑️ 이 PC 스케줄 전체 초기화", command=self.on_clear_remote_click)
        self.pc_context_menu.add_command(label="❌ 목록/그룹에서 제거", command=self.on_context_menu_remove_pc)
        self.pc_listbox.bind("<Button-3>", self.show_pc_context_menu)

        # 통신 ACK 및 활동 로그 콘솔
        ttk.Label(right_frame, text="📋 전송 및 통신 응답 로그 (ACK Log)", style="TLabel", font=("Arial", 8, "bold")).pack(anchor="w", pady=(4, 2))
        self.log_text = scrolledtext.ScrolledText(
            right_frame, bg="#111827", fg="#d1d5db", insertbackground="white",
            relief="flat", font=("Courier", 8), height=10
        )
        self.log_text.pack(fill="both", expand=True)

        # 안내문
        self.log_append(f"💡 준비 완료 (v{APP_VERSION}): 대기 PC를 검색하거나 IP를 입력하여 전송하십시오.")

    def on_preset_title_selected(self, event=None):
        """자주 사용하는 스케줄 제목 10종 중 하나를 선택했을 때 제목, 전원 모드, 시각, 요일, 경고문을 자동 설정합니다."""
        idx = self.preset_combo.current()
        if idx > 0:
            preset = POPULAR_SCHEDULE_PRESETS[idx - 1]
            self.entry_label.delete(0, tk.END)
            self.entry_label.insert(0, preset["title"])
            
            # 1. 추천 전원 동작 모드 동기화
            mode_idx = 0
            for i, k in enumerate(self.mode_keys):
                if k == preset.get("mode"):
                    mode_idx = i
                    break
            self.combo_mode.current(mode_idx)
            
            # 2. 추천 시각 동기화
            if "hour" in preset:
                self.entry_hour.delete(0, tk.END)
                self.entry_hour.insert(0, preset["hour"])
            if "min" in preset:
                self.entry_min.delete(0, tk.END)
                self.entry_min.insert(0, preset["min"])
                
            # 3. 요일 동기화
            if "days" in preset and hasattr(self, 'day_vars'):
                for day_i, var in enumerate(self.day_vars):
                    var.set(day_i in preset["days"])
                
            # 4. 추천 경고 안내문 동기화
            if "warn" in preset and hasattr(self, 'entry_warn_msg'):
                self.entry_warn_msg.delete(0, tk.END)
                self.entry_warn_msg.insert(0, preset["warn"])
                
            # 5. 추천 유휴 상태 설정 동기화
            if "idle" in preset and hasattr(self, 'idle_only_var'):
                self.idle_only_var.set(preset["idle"])
                
            self.log_append(f"📋 프리셋 적용: '{preset['title']}' (모드: {preset.get('mode')}, 시각: {preset.get('hour')}:{preset.get('min')})")
            self.preset_combo.current(0)

    def log_append(self, msg):
        """오른쪽 로그 창에 타임스탬프와 함께 출력합니다."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)

    # -------------------------------------------------------------------------
    # PC 그룹 및 WOL (Wake-on-LAN) 데이터 관리 메서드
    # -------------------------------------------------------------------------
    def load_pc_groups_data(self):
        """저장된 PC 그룹 및 개별 PC(IP, MAC, 호스트명, 그룹, 메모) 정보를 로드합니다."""
        self.groups_list = [
            {"id": "all", "name": "📁 전체 PC (All)", "is_system": True},
            {"id": "default", "name": "🏢 기본 그룹 (Default)", "is_system": False}
        ]
        self.pc_records = {}
        self.pc_checked_status = {}

        if os.path.exists(GROUPS_CONFIG_FILE):
            try:
                with open(GROUPS_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    loaded_groups = data.get("groups", [])
                    if loaded_groups:
                        # 'all' 시스템 그룹 보장
                        has_all = any(g.get("id") == "all" for g in loaded_groups)
                        if not has_all:
                            loaded_groups.insert(0, {"id": "all", "name": "📁 전체 PC (All)", "is_system": True})
                        self.groups_list = loaded_groups
                    loaded_pcs = data.get("pcs", {})
                    if isinstance(loaded_pcs, dict):
                        self.pc_records = loaded_pcs
            except Exception as e:
                pass

    def save_pc_groups_data(self):
        """PC 그룹 목록과 PC 상세 정보를 JSON 파일에 저장합니다."""
        try:
            data = {
                "groups": self.groups_list,
                "pcs": self.pc_records
            }
            with open(GROUPS_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass

    def get_group_by_id(self, gid):
        for g in self.groups_list:
            if g.get("id") == gid:
                return g
        return None

    def get_group_by_name(self, name):
        for g in self.groups_list:
            if g.get("name") == name or g.get("name").split(" (")[0] == name:
                return g
        return None

    def get_current_selected_group_id(self):
        sel_name = self.selected_group_var.get()
        g = self.get_group_by_name(sel_name)
        return g["id"] if g else "all"

    def refresh_group_combobox(self):
        """그룹 콤보박스의 목록과 표시 텍스트를 갱신합니다."""
        names = []
        for g in self.groups_list:
            gid = g["id"]
            if gid == "all":
                cnt = len(self.pc_records)
            else:
                cnt = sum(1 for p in self.pc_records.values() if p.get("group") == gid)
            names.append(f"{g['name']} ({cnt}대)")

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

    def refresh_pc_listbox(self):
        """현재 선택된 그룹 필터와 체크 상태에 맞게 오른쪽 PC 목록창을 다시 그립니다."""
        self.pc_listbox.delete(0, tk.END)
        cur_gid = self.get_current_selected_group_id()

        # 표시할 PC IP 집합: 등록된 레코드 + 최근 스캔/비콘 감지된 IP
        all_candidate_ips = set(self.pc_records.keys())
        if self.preserve_scanned_pcs.get():
            all_candidate_ips.update(self.last_scanned_active_ips)
            all_candidate_ips.update(DISCOVERED_CLIENTS.keys())

        # 그룹 필터 적용
        display_ips = []
        for ip in all_candidate_ips:
            rec = self.pc_records.get(ip, {})
            pc_gid = rec.get("group", "default")
            if cur_gid == "all" or pc_gid == cur_gid:
                display_ips.append(ip)

        display_ips = sorted(display_ips, key=lambda x: [int(p) for p in x.split('.') if p.isdigit()] if '.' in x else [0])

        if not display_ips:
            if cur_gid == "all":
                self.pc_listbox.insert(tk.END, "❌ 감지되거나 등록된 PC 없음")
                self.pc_listbox.insert(tk.END, "   [🔍 대기 PC 검색]을 누르거나")
                self.pc_listbox.insert(tk.END, "   [⚙️ 그룹 관리]에서 PC를 추가하세요.")
            else:
                grp = self.get_group_by_id(cur_gid)
                grp_title = grp['name'] if grp else cur_gid
                self.pc_listbox.insert(tk.END, f"❌ '{grp_title}' 그룹에 속한 PC가 없습니다.")
                self.pc_listbox.insert(tk.END, "   PC를 우클릭하여 이 그룹으로 지정하세요.")
        else:
            for ip in display_ips:
                is_checked = self.pc_checked_status.get(ip, False)
                chk_mark = "[✓]" if is_checked else "[ ]"

                rec = self.pc_records.get(ip, {})
                hostname = rec.get("hostname") or DISCOVERED_CLIENTS.get(ip, {}).get("hostname", "") or DISCOVERED_CLIENTS.get(ip, {}).get("device", "")
                mac = rec.get("mac") or DISCOVERED_CLIENTS.get(ip, {}).get("mac", "")

                # WOL 지원 태그
                wol_tag = " ⚡WOL" if mac else ""
                
                # 방화벽 우회 비콘 활성 여부
                is_live = ip in self.last_scanned_active_ips or (time.time() - DISCOVERED_CLIENTS.get(ip, {}).get("last_seen", 0) < 90)
                status_icon = "🟢" if is_live else "⚪"

                # 호스트명 표시
                host_tag = f" ({hostname})" if hostname else ""

                # 전체 보기 모드일 때 소속 그룹 뱃지
                group_tag = ""
                if cur_gid == "all":
                    pc_gid = rec.get("group", "default")
                    g_info = self.get_group_by_id(pc_gid)
                    if g_info and pc_gid != "default":
                        group_tag = f" [{g_info['name'].split(' (')[0]}]"

                # 관리자 PC 식별 태그
                is_admin_pc = is_local_admin_ip(ip) or (bool(hostname) and hostname.strip().upper() == socket.gethostname().upper())
                admin_tag = " [👑 관리자 PC]" if is_admin_pc else ""

                item_line = f"{chk_mark} {status_icon} 🖥️ {ip}{host_tag}{admin_tag}{group_tag}{wol_tag}"
                self.pc_listbox.insert(tk.END, item_line)

    def on_group_filter_changed(self, event=None):
        """그룹 콤보박스 변경 시 목록 새로고침 및 IP 입력창 갱신"""
        self.refresh_pc_listbox()
        self.update_entry_ip_from_checked()

    def select_all_in_current_group(self):
        """현재 선택된 그룹 내의 모든 PC를 일괄 체크합니다."""
        cur_gid = self.get_current_selected_group_id()
        selected_count = 0
        for i in range(self.pc_listbox.size()):
            text = self.pc_listbox.get(i)
            ip = extract_ip_from_list_item(text)
            if ip:
                self.pc_checked_status[ip] = True
                selected_count += 1
        self.refresh_pc_listbox()
        self.update_entry_ip_from_checked()
        grp_name = self.selected_group_var.get().split(" (")[0]
        self.log_append(f"☑️ '{grp_name}' 내 PC {selected_count}대 일괄 선택 완료")

    def deselect_all_pcs(self):
        """모든 PC의 체크를 해제합니다."""
        self.pc_checked_status.clear()
        self.refresh_pc_listbox()
        self.update_entry_ip_from_checked()
        self.log_append("☐ 모든 PC 선택 해제됨")

    def update_entry_ip_from_checked(self):
        """체크된 PC들의 IP 목록을 대상 IP 텍스트 박스에 동기화합니다."""
        checked = [ip for ip, checked in self.pc_checked_status.items() if checked]
        self.entry_ip.config(state="normal")
        self.entry_ip.delete(0, tk.END)
        if checked:
            self.entry_ip.insert(0, ", ".join(sorted(checked)))
            self.entry_ip.config(
                state="readonly",
                readonlybackground="#1e293b",
                fg="#38bdf8",
                disabledforeground="#38bdf8"
            )
        else:
            self.entry_ip.config(
                state="normal",
                bg="#111827",
                fg="#38bdf8"
            )

    def discover_waiting_pcs(self):
        """로컬 네트워크의 활성 PC를 탐색하고 그룹/비콘 레코드에 자동 편입합니다."""
        self.btn_scan.config(state="disabled", text="🔍 검색 중...")
        self.pc_listbox.delete(0, tk.END)
        self.pc_listbox.insert(tk.END, "🔍 로컬 네트워크 및 대기 PC 탐색 중...")
        
        def scan_thread():
            local_ip = get_local_ip()
            if local_ip == "127.0.0.1":
                local_ip_base = "192.168.0."
            else:
                parts = local_ip.split('.')
                local_ip_base = ".".join(parts[:3]) + "."
                
            port = DEFAULT_PORT
            try:
                port = int(self.entry_port.get().strip())
            except Exception:
                pass
                
            active_ips = []
            lock = threading.Lock()
            threads = []
            
            def check_single_ip(ip_addr):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.3)
                    res = s.connect_ex((ip_addr, port))
                    if res == 0:
                        with lock:
                            if ip_addr not in active_ips:
                                active_ips.append(ip_addr)
                    s.close()
                except Exception:
                    pass
                    
            for i in range(1, 255):
                target_ip = f"{local_ip_base}{i}"
                t = threading.Thread(target=check_single_ip, args=(target_ip,), daemon=True)
                threads.append(t)
                t.start()
                if len(threads) >= 40:
                    for th in threads:
                        th.join()
                    threads = []
                    
            for th in threads:
                th.join()
                
            if "127.0.0.1" not in active_ips:
                check_single_ip("127.0.0.1")

            # 방화벽 우회 비콘을 수신한 클라이언트 PC들도 active_ips에 즉시 병합
            for c_ip, info in list(DISCOVERED_CLIENTS.items()):
                if time.time() - info.get("last_seen", 0) < 90:
                    with lock:
                        if c_ip not in active_ips:
                            active_ips.append(c_ip)

            # 발견된 IP들을 pc_records 및 last_scanned_active_ips에 등록
            new_registered = False
            for ip in active_ips:
                self.last_scanned_active_ips.add(ip)
                beacon_info = DISCOVERED_CLIENTS.get(ip, {})
                beacon_mac = beacon_info.get("mac", "")
                beacon_host = beacon_info.get("hostname", "") or beacon_info.get("device", "")

                if ip not in self.pc_records:
                    # 신규 발견된 PC 등록
                    arp_mac = beacon_mac or get_mac_from_arp(ip)
                    self.pc_records[ip] = {
                        "hostname": beacon_host or f"PC-{ip.split('.')[-1]}",
                        "mac": arp_mac or "",
                        "group": "default",
                        "memo": "자동 검색 감지"
                    }
                    new_registered = True
                else:
                    # 기존 레코드에 MAC 또는 호스트명이 없었으면 보완
                    if beacon_mac and not self.pc_records[ip].get("mac"):
                        self.pc_records[ip]["mac"] = beacon_mac
                        new_registered = True
                    if beacon_host and not self.pc_records[ip].get("hostname"):
                        self.pc_records[ip]["hostname"] = beacon_host
                        new_registered = True

            if new_registered:
                self.save_pc_groups_data()
            
            def update_ui():
                self.btn_scan.config(state="normal", text="🔍 대기 PC 검색")
                self.refresh_group_combobox()
                self.refresh_pc_listbox()
                self.log_append(f"스캔 완료: 총 {len(active_ips)}대의 활성 PC가 응답했습니다.")
                
            self.root.after(0, update_ui)
            
        threading.Thread(target=scan_thread, daemon=True).start()

    def on_beacon_pc_discovered(self, c_ip, hostname, mac):
        """비콘 수신 허브에서 클라이언트 PC 감지 시 UI 및 레코드를 안전하게 실시간 갱신합니다."""
        self.last_scanned_active_ips.add(c_ip)
        updated = False
        if c_ip not in self.pc_records:
            self.pc_records[c_ip] = {
                "hostname": hostname or f"PC-{c_ip.split('.')[-1]}",
                "mac": mac or get_mac_from_arp(c_ip),
                "group": "default",
                "memo": "실시간 비콘 감지"
            }
            updated = True
        else:
            if mac and not self.pc_records[c_ip].get("mac"):
                self.pc_records[c_ip]["mac"] = mac
                updated = True
            if hostname and not self.pc_records[c_ip].get("hostname"):
                self.pc_records[c_ip]["hostname"] = hostname
                updated = True

        if updated:
            self.save_pc_groups_data()
            self.refresh_group_combobox()

        self.refresh_pc_listbox()

    def on_pc_click(self, event):
        """목록에서 PC 클릭 시 체크박스 상태 토글 및 IP 입력창 반영"""
        try:
            index = self.pc_listbox.index(f"@{event.x},{event.y}")
            if index < 0 or index >= self.pc_listbox.size():
                return
            
            bbox = self.pc_listbox.bbox(index)
            if not bbox or not (bbox[1] <= event.y <= bbox[1] + bbox[3]):
                return
                
            text = self.pc_listbox.get(index)
            ip = extract_ip_from_list_item(text)
            if not ip:
                return

            # 체크 상태 반전 토글
            is_checked = self.pc_checked_status.get(ip, False)
            self.pc_checked_status[ip] = not is_checked

            self.refresh_pc_listbox()
            self.update_entry_ip_from_checked()
        except Exception:
            pass

    def on_pc_double_click(self, event):
        """PC 항목 더블 클릭 시 PC 정보 및 MAC 주소 편집 창 열기"""
        try:
            index = self.pc_listbox.index(f"@{event.x},{event.y}")
            if index < 0 or index >= self.pc_listbox.size():
                return
            text = self.pc_listbox.get(index)
            ip = extract_ip_from_list_item(text)
            if ip:
                self.open_edit_pc_dialog(ip=ip)
        except Exception:
            pass

    def get_target_ips(self):
        """체크된 IP 목록 또는 텍스트 입력 IP 목록을 파싱하여 반환합니다."""
        checked = [ip for ip, chk in self.pc_checked_status.items() if chk]
        if checked:
            return checked

        self.entry_ip.config(state="normal")
        raw = self.entry_ip.get().strip()
        if not raw or raw == "192.168.0." or "일괄" in raw:
            return None
        if "," in raw:
            parsed = [x.strip() for x in raw.split(",") if x.strip() and x.strip() != "192.168.0."]
            return parsed if parsed else None
        return [raw]

    def check_admin_pc_in_targets(self, target_ips):
        """
        선택된 대상 IP들 중 현재 실행 중인 관리자 PC가 포함되어 있는지 판별합니다.
        반환값: (포함여부: bool, 관리자_IP: str, 관리자_호스트명: str)
        """
        if not target_ips:
            return False, "", ""

        local_ips = get_all_local_ips()
        my_hostname = socket.gethostname().upper()

        for ip in target_ips:
            ip_clean = ip.strip()
            if ip_clean in local_ips:
                client_info = DISCOVERED_CLIENTS.get(ip_clean, {})
                hname = client_info.get("hostname") or socket.gethostname()
                return True, ip_clean, hname

            # 호스트명 대조
            client_info = DISCOVERED_CLIENTS.get(ip_clean, {})
            c_host = (client_info.get("hostname") or "").strip().upper()
            if c_host and c_host == my_hostname:
                return True, ip_clean, c_host

        return False, "", ""

    def show_pc_context_menu(self, event):
        """오른쪽 PC 목록에서 마우스 우클릭 시 동적 그룹 메뉴 및 WOL 컨텍스트 팝업을 엽니다."""
        try:
            index = self.pc_listbox.index(f"@{event.x},{event.y}")
            if index >= 0 and index < self.pc_listbox.size():
                text = self.pc_listbox.get(index)
                ip = extract_ip_from_list_item(text)
                if ip:
                    self.pc_listbox.selection_clear(0, tk.END)
                    self.pc_listbox.selection_set(index)
                    self.pc_listbox.activate(index)

                    # 동적 소속 그룹 메뉴 구성
                    self.group_submenu.delete(0, tk.END)
                    current_pc_gid = self.pc_records.get(ip, {}).get("group", "default")
                    
                    for g in self.groups_list:
                        if g.get("id") == "all":
                            continue
                        gid = g["id"]
                        gname = g["name"]
                        prefix = "✓ " if gid == current_pc_gid else "   "
                        self.group_submenu.add_command(
                            label=f"{prefix}{gname}",
                            command=lambda target_ip=ip, target_gid=gid: self.move_pc_to_group(target_ip, target_gid)
                        )
                    self.group_submenu.add_separator()
                    self.group_submenu.add_command(
                        label="➕ 새 그룹 생성 및 이동...",
                        command=lambda target_ip=ip: self.create_group_and_move_pc(target_ip)
                    )

                    self.pc_context_menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            pass
        finally:
            self.pc_context_menu.grab_release()

    def on_context_menu_power(self, action_type="shutdown"):
        """우클릭한 특정 PC에 대해 단독으로 즉시 종료 또는 다시시작 명령을 전송합니다."""
        sel = self.pc_listbox.curselection()
        if not sel:
            return
        text = self.pc_listbox.get(sel[0])
        ip = extract_ip_from_list_item(text)
        if not ip:
            return

        is_reboot = (action_type == "reboot")
        cmd_kr = "다시 시작" if is_reboot else "시스템 종료"
        cmd_eng = "Reboot" if is_reboot else "Shutdown"
        
        port_str = self.entry_port.get().strip()
        auth_token = self.entry_token.get().strip()
        try:
            port = int(port_str)
        except ValueError:
            port = DEFAULT_PORT

        has_admin, admin_ip, admin_host = self.check_admin_pc_in_targets([ip])
        if has_admin:
            confirm_title = f"🚨 [중대 경고] 본인(관리자) PC 즉시 {cmd_kr} 시도"
            confirm_msg = (
                f"⚠️ [현재 사용 중인 관리자 PC 우클릭 제어 경고]\n\n"
                f"선택하신 컴퓨터는 현재 PowerNetworkScheduler를 실행 중인\n"
                f"본인(관리자) 컴퓨터 [{ip} ({admin_host})] 입니다!\n\n"
                f"관리자 PC가 {cmd_kr}되면 실행 중인 모든 원격 관리 작업이 즉시 중단됩니다.\n\n"
                f"정말로 본인(관리자) PC를 즉시 {cmd_kr}({cmd_eng})하시겠습니까?"
            )
            if not messagebox.askyesno(confirm_title, confirm_msg, icon="warning", default="no"):
                self.log_append(f"⛔ 관리자 PC 보호: 관리자 PC 우클릭 즉시 {cmd_kr} 명령이 취소되었습니다.")
                return
        else:
            confirm_msg = (
                f"⚡ [단독 PC 원격 즉시 {cmd_kr} 경고]\n\n"
                f"대상 PC: {ip} (포트: TCP {port})\n\n"
                f"해당 컴퓨터에 즉시 '{cmd_kr}({cmd_eng})' 명령을 전송하시겠습니까?\n"
                f"※ 저장되지 않은 작업 데이터가 손실될 수 있습니다."
            )
            if not messagebox.askyesno(f"⚠️ 원격 즉시 {cmd_kr} 확인", confirm_msg, icon="warning"):
                return

        self.log_append(f"⚡ [{ip}] 원격 즉시 {cmd_kr} 명령 전송 중...")

        def worker():
            try:
                resp = send_immediate_power_action(
                    ip=ip,
                    port=port,
                    power_cmd=action_type,
                    force=True,
                    grace_period_sec=3,
                    auth_token=auth_token
                )
                if resp.get("success"):
                    msg = resp.get("message", "명령 정상 수신")
                    dev = resp.get("device", "")
                    dev_str = f" [{dev}]" if dev else ""
                    self.log_append(f"✅ [{ip}]{dev_str} 즉시 {cmd_kr} 성공: {msg}")
                    self.root.after(0, lambda: messagebox.showinfo(
                        f"즉시 {cmd_kr} 성공",
                        f"대상 PC ({ip})에 즉시 '{cmd_kr}' 명령이 성공적으로 전송되었습니다."
                    ))
                else:
                    err = resp.get("message", "응답 없음")
                    self.log_append(f"❌ [{ip}] 즉시 {cmd_kr} 실패: {err}")
                    self.root.after(0, lambda: messagebox.showwarning(
                        f"즉시 {cmd_kr} 실패",
                        f"대상 PC ({ip}) 즉시 {cmd_kr} 실패:\n{err}"
                    ))
            except Exception as ex:
                self.log_append(f"❌ [{ip}] 즉시 {cmd_kr} 통신 에러: {ex}")

        threading.Thread(target=worker, daemon=True).start()

    # -------------------------------------------------------------------------
    # WOL (Wake-on-LAN) 및 그룹 관리 액션 메서드
    # -------------------------------------------------------------------------
    def on_group_wol_click(self):
        """현재 선택된 그룹 내의 모든 PC 또는 체크된 PC들에게 Wake-on-LAN 패킷을 일괄 전송합니다."""
        cur_gid = self.get_current_selected_group_id()
        grp_info = self.get_group_by_id(cur_gid)
        grp_name = grp_info["name"].split(" (")[0] if grp_info else "선택 그룹"

        # 대상 PC 결정: 체크된 PC가 있으면 체크된 PC들, 없으면 현재 그룹 내 모든 PC
        checked_ips = [ip for ip, chk in self.pc_checked_status.items() if chk]
        if checked_ips:
            target_ips = checked_ips
            target_desc = f"선택된 {len(target_ips)}대의 PC"
        else:
            target_ips = []
            for ip, pc in self.pc_records.items():
                if cur_gid == "all" or pc.get("group", "default") == cur_gid:
                    target_ips.append(ip)
            target_desc = f"'{grp_name}' 그룹 내 {len(target_ips)}대의 PC"

        if not target_ips:
            messagebox.showwarning(
                "WOL 대상 없음",
                f"WOL(원격 부팅) 명령을 전송할 PC가 없습니다.\n먼저 PC를 등록하거나 그룹을 선택하십시오."
            )
            return

        # MAC 주소가 등록되어 있는지 확인
        wol_targets = []
        missing_mac_ips = []
        for ip in target_ips:
            mac = self.pc_records.get(ip, {}).get("mac", "")
            if not mac:
                mac = get_mac_from_arp(ip)
                if mac and ip in self.pc_records:
                    self.pc_records[ip]["mac"] = mac
                    self.save_pc_groups_data()
            if mac:
                wol_targets.append((ip, mac, self.pc_records.get(ip, {}).get("hostname", "")))
            else:
                missing_mac_ips.append(ip)

        confirm_msg = (
            f"⚡ [그룹 원격 부팅 (Wake-on-LAN) 전송 확인]\n\n"
            f"대상: {target_desc}\n"
            f"WOL 전송 가능: {len(wol_targets)}대 (MAC 등록 완료)\n"
        )
        if missing_mac_ips:
            confirm_msg += f"⚠️ MAC 주소 미등록(제외): {len(missing_mac_ips)}대 ({', '.join(missing_mac_ips[:3])}...)\n"
        confirm_msg += "\n지금 Magic Packet(WOL)을 브로드캐스트 전송하시겠습니까?"

        if not messagebox.askyesno("⚡ 그룹 WOL 부팅 확인", confirm_msg):
            return

        if not wol_targets:
            messagebox.showerror(
                "WOL 전송 불가",
                "등록된 MAC 주소가 없어 WOL 패킷을 전송할 수 없습니다.\n"
                "[⚙️ 그룹 관리] 또는 우클릭 [PC 정보 및 MAC 주소 편집]에서 MAC 주소를 입력하십시오."
            )
            return

        self.log_append(f"⚡ {target_desc} ({len(wol_targets)}대) 그룹 WOL 원격 부팅 전송 시작...")

        def wol_worker():
            success_cnt = 0
            fail_cnt = 0
            for ip, mac, host in wol_targets:
                host_str = f" ({host})" if host else ""
                ok = send_wol_magic_packet(mac, ip=ip)
                if ok:
                    success_cnt += 1
                    self.log_append(f"⚡ WOL 패킷 전송 성공 -> {ip}{host_str} [MAC: {mac}]")
                else:
                    fail_cnt += 1
                    self.log_append(f"❌ WOL 패킷 전송 실패 -> {ip}{host_str} [MAC: {mac}]")
                time.sleep(0.05)

            self.root.after(0, lambda: messagebox.showinfo(
                "⚡ 그룹 WOL 전송 완료",
                f"그룹 Wake-on-LAN 패킷 전송이 완료되었습니다!\n\n"
                f"✅ 성공: {success_cnt}대\n"
                f"❌ 실패: {fail_cnt}대\n\n"
                f"※ 대상 PC 메인보드 BIOS/UEFI의 'Wake on LAN' 설정이 활성화되어 있어야 켜집니다."
            ))

        threading.Thread(target=wol_worker, daemon=True).start()

    def on_context_menu_wol(self):
        """우클릭한 특정 PC 단독으로 Wake-on-LAN 매직 패킷을 전송합니다."""
        sel = self.pc_listbox.curselection()
        if not sel:
            return
        text = self.pc_listbox.get(sel[0])
        ip = extract_ip_from_list_item(text)
        if not ip:
            return
        self.on_single_pc_wol(ip)

    def on_single_pc_wol(self, ip, parent=None):
        """단일 PC에 대해 MAC 주소를 확인/해결하고 WOL 패킷을 전송합니다."""
        owner = parent or self.root
        rec = self.pc_records.get(ip, {})
        mac = rec.get("mac", "")
        if not mac:
            # ARP 캐시 조회 시도
            mac = get_mac_from_arp(ip)
            if mac:
                rec["mac"] = mac
                self.pc_records[ip] = rec
                self.save_pc_groups_data()

        if not mac:
            # 수동 입력 대화상자 호출
            prompt_mac = self.prompt_text_dialog(
                "WOL MAC 주소 필요",
                f"PC [{ip}]의 MAC 물리 주소가 등록되어 있지 않습니다.\nMAC 주소를 입력하세요 (예: 00:11:22:33:44:55):",
                parent=owner
            )
            if not prompt_mac:
                return
            mac = prompt_mac.strip()
            rec["mac"] = mac
            self.pc_records[ip] = rec
            self.save_pc_groups_data()
            self.refresh_pc_listbox()

        host = rec.get("hostname", "")
        host_str = f" ({host})" if host else ""

        if not messagebox.askyesno(
            "⚡ 원격 부팅 (WOL) 전송",
            f"대상 PC: {ip}{host_str}\nMAC 주소: {mac}\n\n해당 컴퓨터를 원격 부팅하기 위한 WOL 매직 패킷을 전송하시겠습니까?",
            parent=owner
        ):
            return

        ok = send_wol_magic_packet(mac, ip=ip)
        if ok:
            self.log_append(f"⚡ [{ip}] 원격 부팅(WOL) 패킷 브로드캐스트 전송 성공 [MAC: {mac}]")
            messagebox.showinfo("WOL 전송 성공", f"PC [{ip}]로 원격 부팅 Magic Packet을 전송했습니다.\n(MAC: {mac})", parent=owner)
        else:
            self.log_append(f"❌ [{ip}] 원격 부팅(WOL) 패킷 전송 실패")
            messagebox.showerror("WOL 전송 실패", f"WOL 매직 패킷 전송에 실패했습니다.\nMAC 주소 형식({mac})을 확인하십시오.", parent=owner)

    def move_pc_to_group(self, ip, group_id):
        """지정한 PC를 특정 그룹으로 이동/재지정합니다."""
        if ip not in self.pc_records:
            self.pc_records[ip] = {
                "hostname": f"PC-{ip.split('.')[-1]}",
                "mac": get_mac_from_arp(ip) or "",
                "group": group_id,
                "memo": ""
            }
        else:
            self.pc_records[ip]["group"] = group_id

        self.save_pc_groups_data()
        self.refresh_group_combobox()
        self.refresh_pc_listbox()
        grp_info = self.get_group_by_id(group_id)
        grp_nm = grp_info["name"].split(" (")[0] if grp_info else group_id
        self.log_append(f"📁 [{ip}] PC 소속 그룹 변경 -> '{grp_nm}'")

    def create_group_and_move_pc(self, ip):
        """새 그룹명을 입력받아 생성한 뒤 해당 PC를 즉시 이동시킵니다."""
        name = self.prompt_text_dialog("새 그룹 생성", "추가할 새 그룹명을 입력하세요:\n(예: 101호실, 마케팅팀, 회의실 PC)")
        if name and name.strip():
            clean = name.strip()
            gid = f"grp_{int(time.time()*1000)}"
            self.groups_list.append({"id": gid, "name": f"🏫 {clean}", "is_system": False})
            self.move_pc_to_group(ip, gid)

    def on_context_menu_edit_pc(self):
        """우클릭한 PC의 정보 수정 대화상자를 엽니다."""
        sel = self.pc_listbox.curselection()
        if not sel:
            return
        text = self.pc_listbox.get(sel[0])
        ip = extract_ip_from_list_item(text)
        if ip:
            self.open_edit_pc_dialog(ip=ip)

    def on_context_menu_remove_pc(self):
        """우클릭한 PC를 관리 목록/그룹에서 완전히 삭제합니다."""
        sel = self.pc_listbox.curselection()
        if not sel:
            return
        text = self.pc_listbox.get(sel[0])
        ip = extract_ip_from_list_item(text)
        if not ip:
            return

        if messagebox.askyesno("PC 제거 확인", f"PC [{ip}]을(를) 목록 및 그룹에서 제거하시겠습니까?"):
            if ip in self.pc_records:
                del self.pc_records[ip]
            if ip in self.pc_checked_status:
                del self.pc_checked_status[ip]
            if ip in self.last_scanned_active_ips:
                self.last_scanned_active_ips.discard(ip)
            self.save_pc_groups_data()
            self.refresh_group_combobox()
            self.refresh_pc_listbox()
            self.update_entry_ip_from_checked()
            self.log_append(f"🗑️ [{ip}] PC가 목록에서 제거되었습니다.")

    # -------------------------------------------------------------------------
    # 모달 대화상자: 그룹 및 WOL 관리 센터, PC 편집, 텍스트 프롬프트
    # -------------------------------------------------------------------------
    def open_group_manager(self):
        """원격 PC 그룹 및 WOL (Wake-on-LAN) 관리자 모달 대화상자"""
        dlg = tk.Toplevel(self.root)
        dlg.title("📁 원격 PC 그룹 & WOL (Wake-on-LAN) 관리자")
        dlg.geometry("840x580")
        dlg.minsize(760, 500)
        dlg.configure(bg=self.bg_color)
        dlg.transient(self.root)
        dlg.grab_set()

        try:
            x = self.root.winfo_x() + max(0, (self.root.winfo_width() - 840) // 2)
            y = self.root.winfo_y() + max(0, (self.root.winfo_height() - 580) // 2)
            dlg.geometry(f"+{x}+{y}")
        except Exception:
            pass

        # 1. 상단 헤더
        hdr_frame = tk.Frame(dlg, bg=self.card_color, padx=16, pady=12)
        hdr_frame.pack(fill="x", pady=(0, 8))
        tk.Label(
            hdr_frame, text="📁 원격 PC 그룹화 & Wake-on-LAN(WOL) 통합 관리 센터",
            font=("Arial", 12, "bold"), bg=self.card_color, fg=self.text_color
        ).pack(anchor="w")
        tk.Label(
            hdr_frame,
            text="원격 PC들을 부서/강의실별로 그룹화하고, MAC 주소를 등록하여 '그룹 일괄 원격 부팅(WOL)' 및 '스케줄 제어'를 수행합니다.",
            font=("Arial", 8), bg=self.card_color, fg="#9ca3af"
        ).pack(anchor="w", pady=(2, 0))

        # 2. 메인 컨텐츠 영역
        body_frame = tk.Frame(dlg, bg=self.bg_color, padx=12)
        body_frame.pack(fill="both", expand=True)

        # 2-1. 좌측: 그룹 관리 패널
        left_p = tk.Frame(body_frame, bg=self.card_color, width=250, padx=8, pady=8)
        left_p.pack(side="left", fill="y", padx=(0, 6))
        left_p.pack_propagate(False)

        tk.Label(left_p, text="🏷️ 그룹 목록 (Groups)", font=("Arial", 9, "bold"), bg=self.card_color, fg=self.text_color).pack(anchor="w", pady=(0, 4))

        grp_listbox_frame = tk.Frame(left_p, bg=self.card_color)
        grp_listbox_frame.pack(fill="both", expand=True, pady=(0, 6))

        grp_scroll = tk.Scrollbar(grp_listbox_frame)
        grp_scroll.pack(side="right", fill="y")
        grp_listbox = tk.Listbox(
            grp_listbox_frame, bg="#111827", fg="#f3f4f6", selectbackground=self.accent_color,
            selectforeground="white", relief="flat", font=("Arial", 9, "bold"),
            yscrollcommand=grp_scroll.set, highlightthickness=0
        )
        grp_listbox.pack(side="left", fill="both", expand=True)
        grp_scroll.config(command=grp_listbox.yview)

        f_grp_btns = tk.Frame(left_p, bg=self.card_color)
        f_grp_btns.pack(fill="x")

        def populate_groups():
            grp_listbox.delete(0, tk.END)
            for g in self.groups_list:
                gid = g["id"]
                if gid == "all":
                    cnt = len(self.pc_records)
                else:
                    cnt = sum(1 for p in self.pc_records.values() if p.get("group") == gid)
                grp_listbox.insert(tk.END, f"{g['name']} ({cnt}대)")

        def on_add_group():
            name = self.prompt_text_dialog("새 그룹 추가", "추가할 그룹명을 입력하세요:\n(예: 1강의실, 사무실, 회의실, 전산실)", parent=dlg)
            if name and name.strip():
                clean_name = name.strip()
                if any(g["name"] == clean_name or g["name"].endswith(clean_name) for g in self.groups_list):
                    messagebox.showwarning("중복 그룹명", "이미 존재하는 그룹명입니다.", parent=dlg)
                    return
                gid = f"grp_{int(time.time()*1000)}"
                self.groups_list.append({"id": gid, "name": f"🏫 {clean_name}", "is_system": False})
                self.save_pc_groups_data()
                populate_groups()
                self.refresh_group_combobox()
                self.refresh_pc_listbox()

        def on_rename_group():
            sel = grp_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            target_g = self.groups_list[idx]
            if target_g.get("is_system"):
                messagebox.showwarning("변경 불가", "전체 PC 시스템 그룹은 이름을 변경할 수 없습니다.", parent=dlg)
                return
            current_raw = target_g["name"].replace("🏫 ", "").replace("🏢 ", "")
            new_name = self.prompt_text_dialog("그룹 이름 변경", "새로운 그룹명을 입력하세요:", initial_val=current_raw, parent=dlg)
            if new_name and new_name.strip():
                target_g["name"] = f"🏫 {new_name.strip()}"
                self.save_pc_groups_data()
                populate_groups()
                self.refresh_group_combobox()
                self.refresh_pc_listbox()

        def on_delete_group():
            sel = grp_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            target_g = self.groups_list[idx]
            if target_g.get("is_system") or target_g["id"] == "default":
                messagebox.showwarning("삭제 불가", "기본 그룹 또는 시스템 그룹은 삭제할 수 없습니다.", parent=dlg)
                return
            gid = target_g["id"]
            if not messagebox.askyesno("그룹 삭제 확인", f"'{target_g['name']}' 그룹을 삭제하시겠습니까?\n이 그룹에 속한 PC들은 '기본 그룹'으로 자동 이동됩니다.", parent=dlg):
                return
            for pc in self.pc_records.values():
                if pc.get("group") == gid:
                    pc["group"] = "default"
            self.groups_list = [g for g in self.groups_list if g["id"] != gid]
            self.save_pc_groups_data()
            populate_groups()
            self.refresh_group_combobox()
            self.refresh_pc_listbox()
            populate_pcs_for_current_group()

        btn_add_g = tk.Button(f_grp_btns, text="➕ 새 그룹", bg="#374151", fg="white", font=("Arial", 8, "bold"), relief="flat", pady=3, command=on_add_group)
        btn_add_g.pack(side="left", fill="x", expand=True, padx=(0, 2))
        btn_ren_g = tk.Button(f_grp_btns, text="✏️ 수정", bg="#374151", fg="white", font=("Arial", 8), relief="flat", pady=3, command=on_rename_group)
        btn_ren_g.pack(side="left", fill="x", expand=True, padx=(2, 2))
        btn_del_g = tk.Button(f_grp_btns, text="🗑️ 삭제", bg="#dc2626", fg="white", font=("Arial", 8), relief="flat", pady=3, command=on_delete_group)
        btn_del_g.pack(side="right", fill="x", expand=True, padx=(2, 0))

        # 2-2. 우측: 선택 그룹 내 PC 목록 & WOL 관리 패널
        right_p = tk.Frame(body_frame, bg=self.card_color, padx=8, pady=8)
        right_p.pack(side="right", fill="both", expand=True)

        lbl_cur_grp = tk.Label(right_p, text="💻 등록된 PC 목록 및 WOL(원격 부팅) 상태", font=("Arial", 9, "bold"), bg=self.card_color, fg=self.text_color)
        lbl_cur_grp.pack(anchor="w", pady=(0, 4))

        tree_frame = tk.Frame(right_p, bg=self.card_color)
        tree_frame.pack(fill="both", expand=True, pady=(0, 6))

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")

        cols = ("ip", "host", "mac", "wol_status", "group", "memo")
        pc_tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            yscrollcommand=tree_scroll.set, selectmode="browse"
        )
        pc_tree.heading("ip", text="IP 주소")
        pc_tree.heading("host", text="호스트명 / 별칭")
        pc_tree.heading("mac", text="MAC 주소 (WOL)")
        pc_tree.heading("wol_status", text="WOL 부팅")
        pc_tree.heading("group", text="소속 그룹")
        pc_tree.heading("memo", text="메모")

        pc_tree.column("ip", width=105, anchor="center")
        pc_tree.column("host", width=110, anchor="w")
        pc_tree.column("mac", width=135, anchor="center")
        pc_tree.column("wol_status", width=75, anchor="center")
        pc_tree.column("group", width=105, anchor="w")
        pc_tree.column("memo", width=95, anchor="w")

        pc_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.config(command=pc_tree.yview)

        def get_current_selected_gid_in_dialog():
            sel = grp_listbox.curselection()
            if not sel:
                return "all"
            idx = sel[0]
            if idx < len(self.groups_list):
                return self.groups_list[idx]["id"]
            return "all"

        def populate_pcs_for_current_group():
            for row in pc_tree.get_children():
                pc_tree.delete(row)
            gid = get_current_selected_gid_in_dialog()
            for ip, pc in sorted(self.pc_records.items()):
                pc_gid = pc.get("group", "default")
                if gid == "all" or pc_gid == gid:
                    mac = pc.get("mac", "")
                    wol_st = "⚡가능" if mac else "미등록"
                    grp_info = self.get_group_by_id(pc_gid)
                    grp_nm = grp_info["name"].split(" (")[0] if grp_info else pc_gid
                    pc_tree.insert("", tk.END, values=(
                        ip,
                        pc.get("hostname", ""),
                        mac if mac else "(미등록)",
                        wol_st,
                        grp_nm,
                        pc.get("memo", "")
                    ))

        def on_group_select(evt):
            populate_pcs_for_current_group()

        grp_listbox.bind("<<ListboxSelect>>", on_group_select)

        # PC 액션 버튼 바
        f_pc_actions = tk.Frame(right_p, bg=self.card_color)
        f_pc_actions.pack(fill="x", pady=(2, 0))

        def on_add_pc():
            gid = get_current_selected_gid_in_dialog()
            target_gid = "default" if gid == "all" else gid
            self.open_edit_pc_dialog(ip="", default_group=target_gid, parent=dlg, on_saved=lambda: (populate_pcs_for_current_group(), populate_groups()))

        def on_edit_pc():
            sel = pc_tree.selection()
            if not sel:
                messagebox.showwarning("선택 필요", "수정할 PC를 목록에서 선택하십시오.", parent=dlg)
                return
            item = pc_tree.item(sel[0])
            ip = item["values"][0]
            self.open_edit_pc_dialog(ip=ip, parent=dlg, on_saved=lambda: (populate_pcs_for_current_group(), populate_groups()))

        def on_delete_pc():
            sel = pc_tree.selection()
            if not sel:
                messagebox.showwarning("선택 필요", "삭제할 PC를 목록에서 선택하십시오.", parent=dlg)
                return
            item = pc_tree.item(sel[0])
            ip = item["values"][0]
            if messagebox.askyesno("PC 삭제 확인", f"PC [{ip}]을(를) 목록에서 삭제하시겠습니까?", parent=dlg):
                if ip in self.pc_records:
                    del self.pc_records[ip]
                self.save_pc_groups_data()
                populate_pcs_for_current_group()
                populate_groups()
                self.refresh_pc_listbox()

        def on_wol_selected_pc():
            sel = pc_tree.selection()
            if not sel:
                messagebox.showwarning("선택 필요", "WOL 원격 부팅을 전송할 PC를 선택하십시오.", parent=dlg)
                return
            item = pc_tree.item(sel[0])
            ip = item["values"][0]
            self.on_single_pc_wol(ip, parent=dlg)
            populate_pcs_for_current_group()

        def on_scan_arp_all():
            found_count = 0
            for ip, pc in self.pc_records.items():
                if not pc.get("mac"):
                    arp_m = get_mac_from_arp(ip)
                    if arp_m:
                        pc["mac"] = arp_m
                        found_count += 1
            if found_count > 0:
                self.save_pc_groups_data()
                populate_pcs_for_current_group()
                self.refresh_pc_listbox()
                messagebox.showinfo("ARP 스캔 완료", f"ARP 캐시 테이블에서 {found_count}대의 MAC 주소를 성공적으로 자동 수집했습니다!", parent=dlg)
            else:
                messagebox.showinfo("ARP 스캔 결과", "새로 감지된 추가 MAC 주소가 없습니다.\n(해당 PC가 한 번이라도 네트워크 패킷을 주고받은 적이 있어야 ARP 테이블에 기록됩니다.)", parent=dlg)

        btn_add_pc = tk.Button(f_pc_actions, text="➕ PC 등록", bg="#3b82f6", fg="white", font=("Arial", 8, "bold"), relief="flat", padx=6, pady=4, cursor="hand2", command=on_add_pc)
        btn_add_pc.pack(side="left", padx=(0, 2))

        btn_edit_pc = tk.Button(f_pc_actions, text="✏️ 정보 수정", bg="#374151", fg="white", font=("Arial", 8), relief="flat", padx=6, pady=4, cursor="hand2", command=on_edit_pc)
        btn_edit_pc.pack(side="left", padx=(2, 2))

        btn_del_pc = tk.Button(f_pc_actions, text="🗑️ PC 삭제", bg="#374151", fg="#f87171", font=("Arial", 8), relief="flat", padx=6, pady=4, cursor="hand2", command=on_delete_pc)
        btn_del_pc.pack(side="left", padx=(2, 2))

        btn_scan_arp = tk.Button(f_pc_actions, text="🔍 ARP MAC 수집", bg="#374151", fg="#60a5fa", font=("Arial", 8), relief="flat", padx=6, pady=4, cursor="hand2", command=on_scan_arp_all)
        btn_scan_arp.pack(side="left", padx=(2, 2))

        btn_wol_pc = tk.Button(f_pc_actions, text="⚡ 선택 PC WOL 부팅", bg="#059669", fg="white", font=("Arial", 8, "bold"), relief="flat", padx=8, pady=4, cursor="hand2", command=on_wol_selected_pc)
        btn_wol_pc.pack(side="right")

        pc_tree.bind("<Double-1>", lambda e: on_edit_pc())

        # 3. 하단 닫기 바
        b_bar = tk.Frame(dlg, bg=self.bg_color, pady=8, padx=12)
        b_bar.pack(fill="x")
        btn_close = tk.Button(
            b_bar, text="💾 저장 및 닫기 (Close)", bg="#4b5563", fg="white",
            font=("Arial", 9, "bold"), relief="flat", padx=16, pady=5, cursor="hand2",
            command=dlg.destroy
        )
        btn_close.pack(side="right")

        # 초기 데이터 로드
        populate_groups()
        grp_listbox.selection_set(0)
        populate_pcs_for_current_group()

    def open_edit_pc_dialog(self, ip="", default_group="default", parent=None, on_saved=None):
        """개별 PC의 IP, 호스트명, MAC 주소(WOL), 소속 그룹, 메모를 편집/등록하는 대화상자"""
        owner = parent or self.root
        d = tk.Toplevel(owner)
        is_new = not bool(ip)
        d.title("➕ 새 PC 등록" if is_new else f"✏️ PC 정보 및 MAC 주소 편집 [{ip}]")
        d.geometry("460x390")
        d.configure(bg=self.bg_color)
        d.transient(owner)
        d.grab_set()
        d.resizable(False, False)

        try:
            x = owner.winfo_x() + max(0, (owner.winfo_width() - 460) // 2)
            y = owner.winfo_y() + max(0, (owner.winfo_height() - 390) // 2)
            d.geometry(f"+{x}+{y}")
        except Exception:
            pass

        rec = self.pc_records.get(ip, {})
        cur_host = rec.get("hostname", "")
        cur_mac = rec.get("mac", "") or get_mac_from_arp(ip)
        cur_group = rec.get("group", default_group)
        cur_memo = rec.get("memo", "")

        f = tk.Frame(d, bg=self.bg_color, padx=18, pady=16)
        f.pack(fill="both", expand=True)

        # IP 주소
        tk.Label(f, text="IP 주소 (필수):", bg=self.bg_color, fg=self.text_color, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", pady=4)
        e_ip = tk.Entry(
            f,
            bg="#111827",
            fg="#60a5fa",
            readonlybackground="#111827",
            disabledbackground="#111827",
            disabledforeground="#60a5fa",
            insertbackground="white",
            font=("Arial", 10, "bold")
        )
        e_ip.grid(row=0, column=1, sticky="ew", pady=4, columnspan=2)
        if ip:
            e_ip.insert(0, ip)
            e_ip.config(state="readonly")

        # 호스트명 / 별칭
        tk.Label(f, text="호스트명 / 별칭:", bg=self.bg_color, fg=self.text_color, font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=4)
        e_host = tk.Entry(f, bg="#111827", fg="white", insertbackground="white", font=("Arial", 10))
        e_host.grid(row=1, column=1, sticky="ew", pady=4, columnspan=2)
        if cur_host:
            e_host.insert(0, cur_host)

        # MAC 주소
        tk.Label(f, text="MAC 주소 (WOL):", bg=self.bg_color, fg=self.text_color, font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="w", pady=4)
        e_mac = tk.Entry(f, bg="#111827", fg="#10b981", insertbackground="white", font=("Arial", 10, "bold"))
        e_mac.grid(row=2, column=1, sticky="ew", pady=4)
        if cur_mac:
            e_mac.insert(0, cur_mac)

        def on_auto_arp_detect():
            target_ip = e_ip.get().strip()
            if not target_ip:
                messagebox.showwarning("IP 필요", "먼저 IP 주소를 입력하십시오.", parent=d)
                return
            detected_mac = get_mac_from_arp(target_ip)
            if not detected_mac:
                beacon = DISCOVERED_CLIENTS.get(target_ip, {})
                detected_mac = beacon.get("mac", "")
            if detected_mac:
                e_mac.delete(0, tk.END)
                e_mac.insert(0, detected_mac)
                messagebox.showinfo("MAC 감지 성공", f"MAC 주소를 자동으로 발견했습니다:\n{detected_mac}", parent=d)
            else:
                messagebox.showwarning("MAC 감지 실패", f"[{target_ip}]에 대한 ARP MAC 주소를 찾지 못했습니다.\n대상 PC가 켜져 있을 때 한 번 스캔하거나 수동으로 입력하십시오.", parent=d)

        btn_arp = tk.Button(f, text="🔍 ARP 감지", bg="#374151", fg="white", font=("Arial", 8), relief="flat", padx=6, command=on_auto_arp_detect)
        btn_arp.grid(row=2, column=2, sticky="w", padx=(4, 0))

        # 소속 그룹
        tk.Label(f, text="소속 그룹:", bg=self.bg_color, fg=self.text_color, font=("Arial", 9)).grid(row=3, column=0, sticky="w", pady=4)
        group_choices = [g["name"] for g in self.groups_list if g["id"] != "all"]
        combo_g = ttk.Combobox(f, values=group_choices, state="readonly", font=("Arial", 9))
        combo_g.grid(row=3, column=1, sticky="ew", pady=4, columnspan=2)
        
        # 기본 선택
        matched_g = self.get_group_by_id(cur_group)
        if matched_g and matched_g["name"] in group_choices:
            combo_g.set(matched_g["name"])
        elif group_choices:
            combo_g.set(group_choices[0])

        # 메모
        tk.Label(f, text="메모 / 비고:", bg=self.bg_color, fg=self.text_color, font=("Arial", 9)).grid(row=4, column=0, sticky="w", pady=4)
        e_memo = tk.Entry(f, bg="#111827", fg="white", insertbackground="white", font=("Arial", 10))
        e_memo.grid(row=4, column=1, sticky="ew", pady=4, columnspan=2)
        if cur_memo:
            e_memo.insert(0, cur_memo)

        f.columnconfigure(1, weight=1)

        # WOL 테스트 전송 버튼
        def on_test_wol():
            test_mac = e_mac.get().strip()
            test_ip = e_ip.get().strip()
            if not test_mac:
                messagebox.showwarning("MAC 필요", "테스트할 MAC 주소를 입력하십시오.", parent=d)
                return
            ok = send_wol_magic_packet(test_mac, ip=test_ip)
            if ok:
                messagebox.showinfo("WOL 테스트", f"Magic Packet을 성공적으로 전송했습니다!\nMAC: {test_mac}", parent=d)
            else:
                messagebox.showerror("WOL 테스트 실패", "WOL 패킷 전송에 실패했습니다. MAC 주소 형식을 확인하세요.", parent=d)

        btn_test_wol = tk.Button(f, text="⚡ 이 MAC 주소로 WOL 즉시 테스트 전송", bg="#0d9488", fg="white", font=("Arial", 8, "bold"), relief="flat", pady=4, command=on_test_wol)
        btn_test_wol.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 10))

        # 저장 / 취소 버튼 바
        b_box = tk.Frame(f, bg=self.bg_color)
        b_box.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(4, 0))

        def on_save():
            save_ip = e_ip.get().strip()
            if not save_ip:
                messagebox.showwarning("입력 오류", "IP 주소를 입력하십시오.", parent=d)
                return
            save_host = e_host.get().strip()
            save_mac = e_mac.get().strip()
            sel_g_name = combo_g.get()
            g_obj = self.get_group_by_name(sel_g_name)
            save_gid = g_obj["id"] if g_obj else "default"
            save_memo = e_memo.get().strip()

            self.pc_records[save_ip] = {
                "hostname": save_host,
                "mac": save_mac,
                "group": save_gid,
                "memo": save_memo
            }
            self.save_pc_groups_data()
            self.refresh_group_combobox()
            self.refresh_pc_listbox()
            self.log_append(f"💾 [{save_ip}] PC 정보 저장 완료 (MAC: {save_mac or '미등록'}, 그룹: {sel_g_name})")
            if on_saved:
                on_saved()
            d.destroy()

        btn_cancel = tk.Button(b_box, text="취소", bg="#4b5563", fg="white", font=("Arial", 9), relief="flat", padx=12, pady=4, command=d.destroy)
        btn_cancel.pack(side="right", padx=(6, 0))

        btn_ok = tk.Button(b_box, text="💾 저장 (Save)", bg=self.accent_color, fg="white", font=("Arial", 9, "bold"), relief="flat", padx=16, pady=4, command=on_save)
        btn_ok.pack(side="right")

    def prompt_text_dialog(self, title, prompt_msg, initial_val="", parent=None):
        """사용자 정의 깔끔한 텍스트 입력 모달 대화상자"""
        owner = parent or self.root
        d = tk.Toplevel(owner)
        d.title(title)
        d.geometry("380x170")
        d.configure(bg=self.bg_color)
        d.transient(owner)
        d.grab_set()
        d.resizable(False, False)

        try:
            x = owner.winfo_x() + max(0, (owner.winfo_width() - 380) // 2)
            y = owner.winfo_y() + max(0, (owner.winfo_height() - 170) // 2)
            d.geometry(f"+{x}+{y}")
        except Exception:
            pass

        tk.Label(d, text=prompt_msg, bg=self.bg_color, fg=self.text_color, font=("Arial", 9), justify="left").pack(anchor="w", padx=16, pady=(16, 8))
        e = tk.Entry(d, bg="#111827", fg="white", insertbackground="white", font=("Arial", 10), relief="flat")
        e.pack(fill="x", padx=16, pady=(0, 16))
        if initial_val:
            e.insert(0, initial_val)
        e.focus_set()

        val = [None]
        def ok(event=None):
            val[0] = e.get().strip()
            d.destroy()

        def cancel(event=None):
            d.destroy()

        e.bind("<Return>", ok)
        e.bind("<Escape>", cancel)

        btn_f = tk.Frame(d, bg=self.bg_color)
        btn_f.pack(fill="x", padx=16)
        tk.Button(btn_f, text="취소", bg="#4b5563", fg="white", font=("Arial", 9), relief="flat", padx=10, pady=3, command=cancel).pack(side="right", padx=(4, 0))
        tk.Button(btn_f, text="확인", bg=self.accent_color, fg="white", font=("Arial", 9, "bold"), relief="flat", padx=14, pady=3, command=ok).pack(side="right")

        owner.wait_window(d)
        return val[0]

    def show_license_dialog(self):
        """한국어 및 영어 2종류 표준 라이선스 및 오픈소스 고지 대화상자 (모달)"""
        lic_win = tk.Toplevel(self.root)
        lic_win.title("사용권 계약 및 오픈소스 라이선스 약관 고지 (License Notice)")
        lic_win.configure(bg="#111827")
        lic_win.transient(self.root)
        lic_win.grab_set()

        window_width = 540
        window_height = 460
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        lic_win.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        lic_win.resizable(False, False)

        # 라이선스 텍스트 로드 (docs/ 우선, 실패 시 installer/내장 fallback)
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

        if not lic_ko or not lic_en:
            try:
                from installer import STANDARD_LICENSE_KO, STANDARD_LICENSE_EN
                if not lic_ko:
                    lic_ko = STANDARD_LICENSE_KO
                if not lic_en:
                    lic_en = STANDARD_LICENSE_EN
            except Exception:
                pass

        current_lic_lang = "ko"

        # 상단 헤더
        hdr = tk.Frame(lic_win, bg="#111827")
        hdr.pack(fill="x", padx=16, pady=(12, 6))

        title_lbl = tk.Label(
            hdr,
            text="📜 라이선스 및 사용권 약관 고지",
            font=("Arial", 10, "bold"),
            fg=self.accent_blue,
            bg="#111827"
        )
        title_lbl.pack(side="left")

        # 언어 전환 버튼
        btn_frame = tk.Frame(hdr, bg="#111827")
        btn_frame.pack(side="right")

        # 텍스트 영역
        text_frame = tk.Frame(lic_win, bg="#111827")
        text_frame.pack(fill="both", expand=True, padx=16, pady=4)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        txt_widget = tk.Text(
            text_frame,
            wrap="word",
            yscrollcommand=scrollbar.set,
            bg="#1f2937",
            fg="#f3f4f6",
            font=("Arial", 9),
            relief="flat",
            padx=10,
            pady=10
        )
        txt_widget.insert("1.0", lic_ko)
        txt_widget.config(state="disabled")
        txt_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=txt_widget.yview)

        def switch_lang(lang_code):
            nonlocal current_lic_lang
            current_lic_lang = lang_code
            txt_widget.config(state="normal")
            txt_widget.delete("1.0", "end")
            txt_widget.insert("1.0", lic_ko if lang_code == "ko" else lic_en)
            txt_widget.config(state="disabled")
            txt_widget.yview_moveto(0.0)

            title_lbl.config(
                text="📜 라이선스 및 사용권 약관 고지" if lang_code == "ko" else "📜 License & Terms Notice"
            )
            btn_ko.config(
                bg=self.accent_blue if lang_code == "ko" else "#374151",
                fg="white" if lang_code == "ko" else "#9ca3af"
            )
            btn_en.config(
                bg=self.accent_blue if lang_code == "en" else "#374151",
                fg="white" if lang_code == "en" else "#9ca3af"
            )
            btn_close.config(
                text="확인" if lang_code == "ko" else "Close"
            )

        btn_en = tk.Button(
            btn_frame,
            text="🇺🇸 English",
            font=("Arial", 8, "bold"),
            bg="#374151",
            fg="#9ca3af",
            relief="flat",
            padx=7,
            pady=1,
            cursor="hand2",
            command=lambda: switch_lang("en")
        )
        btn_en.pack(side="right", padx=(2, 0))

        btn_ko = tk.Button(
            btn_frame,
            text="🇰🇷 한국어",
            font=("Arial", 8, "bold"),
            bg=self.accent_blue,
            fg="white",
            relief="flat",
            padx=7,
            pady=1,
            cursor="hand2",
            command=lambda: switch_lang("ko")
        )
        btn_ko.pack(side="right", padx=(0, 2))

        # 하단 닫기 버튼
        btn_close = tk.Button(
            lic_win,
            text="확인",
            font=("Arial", 9, "bold"),
            bg=self.accent_blue,
            fg="white",
            relief="flat",
            padx=20,
            pady=4,
            cursor="hand2",
            command=lic_win.destroy
        )
        btn_close.pack(pady=(6, 12))

    def on_immediate_power_click(self, action_type="shutdown"):
        """
        입력된 IP 또는 체크된 모든 대상 PC들에 대해 즉시 '종료' 또는 '다시시작' 명령을 전송합니다.
        action_type: 'shutdown' (시스템 종료) 또는 'reboot' (다시 시작)
        """
        target_ips = self.get_target_ips()
        if not target_ips:
            messagebox.showerror(
                "대상 미지정",
                "원격 제어할 대상 컴퓨터의 IP 주소를 입력하거나\n오른쪽 대기 PC 목록에서 [✓] 체크하십시오."
            )
            return

        is_reboot = (action_type == "reboot")
        cmd_kr = "다시 시작" if is_reboot else "시스템 종료"
        cmd_eng = "Reboot" if is_reboot else "Shutdown"
        port_str = self.entry_port.get().strip()
        auth_token = self.entry_token.get().strip()

        try:
            port = int(port_str)
        except ValueError:
            port = DEFAULT_PORT

        targets_display = ", ".join(target_ips)
        if len(target_ips) > 5:
            targets_display = f"{', '.join(target_ips[:5])} 외 {len(target_ips) - 5}대 (총 {len(target_ips)}대)"

        # [핵심] 관리자 PC 포함 여부 검사 및 강력 경고
        has_admin, admin_ip, admin_host = self.check_admin_pc_in_targets(target_ips)
        if has_admin:
            admin_warn_title = f"🚨 [중대 경고] 관리자 PC가 {cmd_kr} 대상에 포함되어 있습니다!"
            admin_warn_msg = (
                f"⚠️ [현재 작업 중인 관리자 PC 감지]\n\n"
                f"현재 PowerNetworkScheduler를 실행 중인 본인(관리자) 컴퓨터가\n"
                f"원격 즉시 {cmd_kr} 대상 목록에 포함되어 있습니다!\n\n"
                f"  ▶ 관리자 PC: {admin_ip} ({admin_host})\n"
                f"  ▶ 실행 명령: 원격 즉시 {cmd_kr} ({cmd_eng})\n"
                f"  ▶ 전체 대상: {targets_display}\n\n"
                f"※ 관리자 PC가 {cmd_kr}되면 현재 관리 세션 및 네트워크 제어가 즉시 중단되며,\n"
                f"   저장되지 않은 작업 데이터가 손실될 수 있습니다.\n\n"
                f"정말로 본인(관리자) PC를 포함하여 즉시 {cmd_kr}를 진행하시겠습니까?"
            )
            if not messagebox.askyesno(admin_warn_title, admin_warn_msg, icon="warning", default="no"):
                self.log_append(f"⛔ 관리자 PC 보호: 관리자 PC({admin_ip})가 포함되어 있어 즉시 {cmd_kr} 명령이 취소되었습니다.")
                return
        else:
            # 안전 확인 다이얼로그 (실수 방지)
            confirm_title = f"⚠️ 원격 즉시 {cmd_kr} 실행 확인"
            confirm_msg = (
                f"⚡ [원격 즉시 {cmd_kr} 명령 경고]\n\n"
                f"대상 PC: {targets_display}\n"
                f"포트: TCP {port}\n\n"
                f"정말로 대상 컴퓨터에 즉시 '{cmd_kr}({cmd_eng})' 명령을 전송하시겠습니까?\n\n"
                f"※ 저장되지 않은 작업 데이터가 손실될 수 있습니다."
            )

            if not messagebox.askyesno(confirm_title, confirm_msg, icon="warning"):
                self.log_append(f"취소됨: 즉시 {cmd_kr} 명령 전송이 취소되었습니다.")
                return

        self.log_append(f"⚡ 즉시 {cmd_kr} 명령 전송 시작 (총 {len(target_ips)}대 대상)...")

        def worker():
            success_count = 0
            fail_count = 0
            for ip in target_ips:
                try:
                    resp = send_immediate_power_action(
                        ip=ip,
                        port=port,
                        power_cmd=action_type,
                        force=True,
                        grace_period_sec=3,
                        auth_token=auth_token
                    )
                    if resp.get("success"):
                        success_count += 1
                        msg = resp.get("message", "명령 정상 수신")
                        dev = resp.get("device", "")
                        dev_str = f" [{dev}]" if dev else ""
                        self.log_append(f"✅ [{ip}]{dev_str} 즉시 {cmd_kr} 성공: {msg}")
                    else:
                        fail_count += 1
                        err = resp.get("message", "응답 없음")
                        self.log_append(f"❌ [{ip}] 즉시 {cmd_kr} 실패: {err}")
                except Exception as ex:
                    fail_count += 1
                    self.log_append(f"❌ [{ip}] 즉시 {cmd_kr} 에러: {ex}")

            summary_msg = f"⚡ 즉시 {cmd_kr} 전송 완료: 성공 {success_count}대 / 실패 {fail_count}대"
            self.log_append(summary_msg)
            if success_count > 0:
                self.root.after(0, lambda: messagebox.showinfo(
                    f"즉시 {cmd_kr} 전송 결과",
                    f"총 {len(target_ips)}대 중 {success_count}대에 즉시 '{cmd_kr}' 명령이 성공적으로 전송되었습니다."
                ))
            else:
                self.root.after(0, lambda: messagebox.showwarning(
                    f"즉시 {cmd_kr} 전송 실패",
                    f"대상 PC들에 즉시 '{cmd_kr}' 명령을 전송하지 못했습니다.\n(보안 토큰 불일치 또는 원격 수신 대기 상태를 확인하십시오.)"
                ))

        threading.Thread(target=worker, daemon=True).start()

    def on_send_click(self):
        target_ips = self.get_target_ips()
        if not target_ips:
            messagebox.showerror("입력 에러", "올바른 원격 컴퓨터 IP 주소를 입력하거나 오른쪽 목록에서 전송할 PC를 체크하십시오.")
            return

        port_str = self.entry_port.get().strip()
        auth_token = self.entry_token.get().strip()
        label = self.entry_label.get().strip()
        hour_str = self.entry_hour.get().strip()
        min_str = self.entry_min.get().strip()
        
        mode_idx = self.combo_mode.current()
        selected_mode = self.mode_keys[mode_idx]
        active_days = [i for i, var in enumerate(self.day_vars) if var.get()]
        overwrite = (self.apply_option.get() == "overwrite")
        
        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("입력 에러", "포트 번호는 반드시 숫자여야 합니다.")
            return
            
        if not label:
            messagebox.showerror("입력 에러", "예약 규칙 이름을 지정해 주십시오.")
            return
            
        try:
            h = int(hour_str)
            m = int(min_str)
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError()
        except ValueError:
            messagebox.showerror("입력 에러", "시간 설정을 시(0~23) 및 분(0~59) 범위로 올바르게 입력해 주십시오.")
            return
            
        if not active_days:
            messagebox.showerror("요일 미선택", "적어도 하나 이상의 요일을 활성화해야 예약 등록이 가능합니다.")
            return
            
        # 유예 초 파싱
        grace_str = self.combo_grace.get().replace("초", "").strip()
        try:
            grace_period_sec = int(grace_str)
        except:
            grace_period_sec = 10

        # 유휴 분 파싱
        idle_min_str = self.combo_idle_min.get().replace("분", "").strip()
        try:
            idle_minutes = int(idle_min_str)
        except:
            idle_minutes = 15

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
            "pre_command": self.entry_precmd.get().strip()
        }

        # [관리자 PC 예약 종료/재부팅 안전 확인]
        if selected_mode in ("shutdown", "reboot"):
            has_admin, admin_ip, admin_host = self.check_admin_pc_in_targets(target_ips)
            if has_admin:
                mode_kr = "시스템 종료" if selected_mode == "shutdown" else "다시 시작"
                admin_warn_title = f"⚠️ [주의] 관리자 PC 예약 {mode_kr} 규칙 전송"
                admin_warn_msg = (
                    f"⚠️ [관리자 PC 스케줄 대상 포함]\n\n"
                    f"현재 작업 중인 본인(관리자) PC [{admin_ip} ({admin_host})]가\n"
                    f"예약 {mode_kr} 규칙 전송 대상에 포함되어 있습니다!\n\n"
                    f"  • 예약 시간: {rule_data['time']}\n"
                    f"  • 동작 모드: {mode_kr}\n\n"
                    f"지정된 시간에 관리자 PC도 자동으로 {mode_kr}됩니다.\n\n"
                    f"정말로 본인(관리자) PC에 이 예약 스케줄을 함께 적용하시겠습니까?"
                )
                if not messagebox.askyesno(admin_warn_title, admin_warn_msg, icon="warning", default="no"):
                    self.log_append(f"⛔ 관리자 PC 보호: 관리자 PC({admin_ip}) 예약 {mode_kr} 전송이 취소되었습니다.")
                    return
        
        def run_send():
            self.root.config(cursor="watch")
            results = []
            success_count = 0
            fail_count = 0
            
            self.log_append(f"전송 시작: {len(target_ips)}대 PC로 [{label}] 전송")

            for target_ip in target_ips:
                resp = send_rule_over_network(target_ip, port, rule_data, overwrite, auth_token)
                if resp.get("success", False):
                    success_count += 1
                    active_count = resp.get("count", "?")
                    results.append(f"✅ {target_ip}: 성공 (등록 후 총 {active_count}개 규칙)")
                    self.log_append(f"✅ {target_ip} 전송 성공 (현재 규칙: {active_count}개)")
                else:
                    fail_count += 1
                    err_msg = resp.get("message", "응답 없음")
                    results.append(f"❌ {target_ip}: 실패 ({err_msg})")
                    self.log_append(f"❌ {target_ip} 실패: {err_msg}")
                    
            self.root.config(cursor="")
            mode_txt = "덮어쓰기" if overwrite else "추가"
            summary = "\n".join(results)
            
            if fail_count == 0:
                messagebox.showinfo(
                    "전송 완료", 
                    f"성공적으로 모든 컴퓨터에 예약 규칙이 전송되었습니다!\n\n"
                    f"총 전송 대상: {len(target_ips)}대 ({mode_txt})\n\n"
                    f"[결과]\n{summary}"
                )
            elif success_count > 0:
                messagebox.showwarning(
                    "일부 전송 실패", 
                    f"일부 컴퓨터로의 전송에 실패했습니다.\n\n"
                    f"성공: {success_count}대, 실패: {fail_count}대\n\n"
                    f"[결과]\n{summary}"
                )
            else:
                messagebox.showerror(
                    "전송 실패", 
                    f"모든 원격 컴퓨터로의 전송에 실패했습니다.\n\n"
                    f"[결과]\n{summary}"
                )
                
        threading.Thread(target=run_send, daemon=True).start()

    def on_clear_remote_click(self):
        """대상 PC의 모든 스케줄을 원격 삭제(초기화)합니다."""
        target_ips = self.get_target_ips()
        if not target_ips:
            messagebox.showerror("입력 에러", "원격 예약을 초기화할 대상 IP를 지정하거나 목록에서 체크하십시오.")
            return

        if not messagebox.askyesno("원격 예약 전체 초기화 확인", f"선택한 {len(target_ips)}대의 원격 PC에 등록된 모든 예약 규칙을 삭제(초기화)하시겠습니까?"):
            return

        port_str = self.entry_port.get().strip()
        auth_token = self.entry_token.get().strip()
        try:
            port = int(port_str)
        except:
            port = DEFAULT_PORT

        def run_clear():
            self.root.config(cursor="watch")
            results = []
            for target_ip in target_ips:
                resp = send_clear_schedules(target_ip, port, auth_token)
                if resp.get("success", False):
                    results.append(f"✅ {target_ip}: 초기화 완료")
                    self.log_append(f"🗑️ {target_ip} 원격 예약 초기화 완료")
                else:
                    err_msg = resp.get("message", "응답 없음")
                    results.append(f"❌ {target_ip}: 실패 ({err_msg})")
                    self.log_append(f"❌ {target_ip} 초기화 실패: {err_msg}")
            self.root.config(cursor="")
            messagebox.showinfo("원격 초기화 결과", "\n".join(results))

        threading.Thread(target=run_clear, daemon=True).start()

    def on_query_status_click(self):
        """대상 PC의 상태 및 등록된 규칙 수를 조회합니다."""
        target_ips = self.get_target_ips()
        if not target_ips:
            messagebox.showerror("입력 에러", "상태를 조회할 대상 IP를 선택하거나 입력하십시오.")
            return

        port_str = self.entry_port.get().strip()
        auth_token = self.entry_token.get().strip()
        try:
            port = int(port_str)
        except:
            port = DEFAULT_PORT

        def run_query():
            self.root.config(cursor="watch")
            results = []
            for target_ip in target_ips:
                resp = query_remote_status(target_ip, port, auth_token)
                if resp.get("success", False):
                    cnt = resp.get("count", 0)
                    dev = resp.get("device", "PowerPC")
                    results.append(f"✅ {target_ip} [{dev}]: 수신 대기 중 (등록 규칙 {cnt}개)")
                    self.log_append(f"📊 {target_ip} 상태: 정상 수신 대기 중, 등록된 규칙 {cnt}개")
                else:
                    err = resp.get("message", "응답 없음")
                    results.append(f"❌ {target_ip}: 통신 불가 ({err})")
                    self.log_append(f"❌ {target_ip} 상태 조회 실패: {err}")
            self.root.config(cursor="")
            messagebox.showinfo("원격 PC 상태 조회 결과", "\n".join(results))

        threading.Thread(target=run_query, daemon=True).start()

    def on_send_token_only_click(self):
        """대상 PC에 예약 규칙 없이 보안 인증 토큰만 단독 전송합니다."""
        target_ips = self.get_target_ips()
        if not target_ips:
            messagebox.showerror("입력 에러", "보안 토큰을 전송할 대상 IP를 지정하거나 오른쪽 목록에서 체크하십시오.")
            return

        port_str = self.entry_port.get().strip()
        auth_token = self.entry_token.get().strip()
        try:
            port = int(port_str)
        except:
            port = DEFAULT_PORT

        # 모달 선택 다이얼로그 (토큰 검증 확인 vs 원격 등록 적용)
        token_dialog = tk.Toplevel(self.root)
        token_dialog.title("🔐 보안 인증 토큰 전송")
        token_dialog.geometry("490x300")
        token_dialog.resizable(False, False)
        token_dialog.configure(bg=self.card_color)
        token_dialog.transient(self.root)
        token_dialog.grab_set()

        # 화면 중앙 배치
        self.root.update_idletasks()
        rx = self.root.winfo_x()
        ry = self.root.winfo_y()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        x = rx + (rw // 2) - 245
        y = ry + (rh // 2) - 150
        token_dialog.geometry(f"+{max(0, x)}+{max(0, y)}")

        f_diag = tk.Frame(token_dialog, bg=self.card_color, padx=18, pady=16)
        f_diag.pack(fill="both", expand=True)

        tk.Label(
            f_diag, 
            text="🔐 보안 인증 토큰 단독 전송", 
            font=("Arial", 12, "bold"), 
            fg="#fbbf24", 
            bg=self.card_color
        ).pack(anchor="w", pady=(0, 6))

        token_display = auth_token if auth_token else "(공백 - 토큰 미설정 상태)"
        ip_preview = ", ".join(target_ips[:3]) + (f" 외 {len(target_ips)-3}대" if len(target_ips) > 3 else "")
        desc_txt = (
            f"• 대상 PC : {len(target_ips)}대 ({ip_preview})\n"
            f"• 전송 토큰: {token_display}\n"
            f"• 대상 포트: {port}\n\n"
            "원격 컴퓨터로 전송할 토큰 작업 모드를 선택하십시오:"
        )
        tk.Label(
            f_diag, 
            text=desc_txt, 
            font=("Arial", 9), 
            fg=self.text_color, 
            bg=self.card_color,
            justify="left"
        ).pack(anchor="w", pady=(0, 12))

        def execute_token_action(mode):
            token_dialog.destroy()
            self.root.config(cursor="watch")

            def run_thread():
                results = []
                mode_desc = "인증 검증" if mode == "verify" else "원격 등록/적용"
                self.log_append(f"🔐 보안 토큰 전송 시작 (모드: {mode_desc}, 대상: {len(target_ips)}대)")
                for target_ip in target_ips:
                    if mode == "verify":
                        resp = send_verify_token(target_ip, port, auth_token)
                    else:
                        resp = send_set_remote_token(target_ip, port, current_auth_token=auth_token, new_token=auth_token)

                    if resp.get("success", False):
                        dev = resp.get("device", "PowerPC")
                        msg = resp.get("message", "성공")
                        results.append(f"✅ {target_ip} [{dev}]: {msg}")
                        self.log_append(f"✅ {target_ip} 토큰 전송 성공: {msg}")
                    else:
                        err = resp.get("message", "응답 없음")
                        results.append(f"❌ {target_ip}: {err}")
                        self.log_append(f"❌ {target_ip} 토큰 전송 실패: {err}")

                self.root.config(cursor="")
                title = "보안 토큰 인증 검증 결과" if mode == "verify" else "원격 보안 토큰 등록 결과"
                messagebox.showinfo(title, "\n".join(results))

            threading.Thread(target=run_thread, daemon=True).start()

        btn_frame = tk.Frame(f_diag, bg=self.card_color)
        btn_frame.pack(fill="x", pady=(4, 0))

        btn_verify = ttk.Button(
            btn_frame, 
            text="🔍 1. 보안 토큰 일치 인증 검증 (Verify Token)", 
            style="Green.TButton", 
            command=lambda: execute_token_action("verify")
        )
        btn_verify.pack(fill="x", pady=(0, 6))

        btn_set = ttk.Button(
            btn_frame, 
            text="📥 2. 원격 PC에 보안 토큰 저장 및 적용 (Set Token)", 
            style="Purple.TButton", 
            command=lambda: execute_token_action("set")
        )
        btn_set.pack(fill="x", pady=(0, 8))

        btn_cancel = ttk.Button(
            btn_frame, 
            text="취소 (Cancel)", 
            style="TButton", 
            command=token_dialog.destroy
        )
        btn_cancel.pack(fill="x")

    def on_emergency_recovery_click(self):
        """
        보안 인증 토큰 분실 시 비상 복구 센터 팝업 대화상자를 엽니다.
        1) 마스터 복구 키를 이용한 원격 토큰 조회 및 강제 재설정/초기화
        2) PowerShell / CLI 원격 일괄 초기화 스크립트 복사
        3) 단계별 분실 대처 매뉴얼 제공
        """
        # 대상 IP 수집
        target_ips = []
        for ip, var in self.client_checkboxes.items():
            if var.get():
                target_ips.append(ip)
        if not target_ips:
            direct_ip = self.entry_ip.get().strip()
            if direct_ip and direct_ip != "192.168.0.":
                target_ips.append(direct_ip)

        port_str = self.entry_port.get().strip()
        try:
            port = int(port_str)
        except Exception:
            port = DEFAULT_PORT

        diag = tk.Toplevel(self.root)
        diag.title("🚨 보안 토큰 분실 비상 복구 센터 (Emergency Token Recovery)")
        diag.geometry("630x550")
        diag.resizable(False, False)
        diag.configure(bg=self.card_color)
        diag.transient(self.root)
        diag.grab_set()

        # 화면 중앙 정렬
        self.root.update_idletasks()
        rx = self.root.winfo_x()
        ry = self.root.winfo_y()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        x = rx + (rw // 2) - 315
        y = ry + (rh // 2) - 275
        diag.geometry(f"+{max(0, x)}+{max(0, y)}")

        # 헤더 카드
        f_head = tk.Frame(diag, bg="#1e293b", padx=16, pady=12)
        f_head.pack(fill="x")

        tk.Label(
            f_head,
            text="🚨 관리자 보안 토큰 분실 비상 복구 센터",
            font=("Arial", 12, "bold"),
            fg="#f87171",
            bg="#1e293b"
        ).pack(anchor="w")

        tk.Label(
            f_head,
            text="원격 PC에 등록된 보안 토큰을 잃어버린 경우 아래 3가지 수단으로 안전하게 복구합니다.",
            font=("Arial", 9),
            fg="#cbd5e1",
            bg="#1e293b"
        ).pack(anchor="w", pady=(2, 0))

        # 탭 전환 바 (Tab Switcher Bar)
        tab_bar = tk.Frame(diag, bg="#0f172a", padx=6, pady=6)
        tab_bar.pack(fill="x")

        tab_container = tk.Frame(diag, bg=self.card_color, padx=16, pady=12)
        tab_container.pack(fill="both", expand=True)

        frame_tab1 = tk.Frame(tab_container, bg=self.card_color)
        frame_tab2 = tk.Frame(tab_container, bg=self.card_color)
        frame_tab3 = tk.Frame(tab_container, bg=self.card_color)

        btn_t1 = tk.Button(tab_bar, text="🔑 1. 마스터 키 원격 복구", font=("Arial", 9, "bold"), bg="#3b82f6", fg="white", relief="flat", padx=10, pady=4)
        btn_t2 = tk.Button(tab_bar, text="💻 2. 파워쉘 일괄 초기화 스크립트", font=("Arial", 9), bg="#1e293b", fg="#94a3b8", relief="flat", padx=10, pady=4)
        btn_t3 = tk.Button(tab_bar, text="📖 3. 상황별 복구 가이드", font=("Arial", 9), bg="#1e293b", fg="#94a3b8", relief="flat", padx=10, pady=4)

        btn_t1.pack(side="left", padx=2)
        btn_t2.pack(side="left", padx=2)
        btn_t3.pack(side="left", padx=2)

        def show_tab(idx):
            frame_tab1.pack_forget()
            frame_tab2.pack_forget()
            frame_tab3.pack_forget()
            btn_t1.configure(bg="#1e293b", fg="#94a3b8", font=("Arial", 9))
            btn_t2.configure(bg="#1e293b", fg="#94a3b8", font=("Arial", 9))
            btn_t3.configure(bg="#1e293b", fg="#94a3b8", font=("Arial", 9))

            if idx == 1:
                frame_tab1.pack(fill="both", expand=True)
                btn_t1.configure(bg="#3b82f6", fg="white", font=("Arial", 9, "bold"))
            elif idx == 2:
                frame_tab2.pack(fill="both", expand=True)
                btn_t2.configure(bg="#3b82f6", fg="white", font=("Arial", 9, "bold"))
            else:
                frame_tab3.pack(fill="both", expand=True)
                btn_t3.configure(bg="#3b82f6", fg="white", font=("Arial", 9, "bold"))

        btn_t1.configure(command=lambda: show_tab(1))
        btn_t2.configure(command=lambda: show_tab(2))
        btn_t3.configure(command=lambda: show_tab(3))

        # =====================================================================
        # 탭 1: 마스터 비상 복구 키로 원격 복구
        # =====================================================================
        tk.Label(
            frame_tab1,
            text="마스터 비상 복구 키로 원격 클라이언트 제어권을 즉시 복구합니다.",
            font=("Arial", 9, "bold"),
            fg="#60a5fa",
            bg=self.card_color
        ).pack(anchor="w", pady=(0, 6))

        # 대상 IP 안내
        target_disp = ", ".join(target_ips) if target_ips else "(선택된 IP 없음 - 오른쪽 목록이나 IP입력란 확인)"
        lbl_target_info = tk.Label(
            frame_tab1,
            text=f"• 대상 PC : {len(target_ips)}대 [{target_disp}]\n• 통신 포트: TCP {port} (방화벽 차단 시 UDP 9985 무조작 자동 우회)",
            font=("Arial", 8),
            fg="#94a3b8",
            bg=self.card_color,
            justify="left"
        )
        lbl_target_info.pack(anchor="w", pady=(0, 8))

        # 마스터 복구 키 입력 프레임
        f_mkey = tk.Frame(frame_tab1, bg=self.card_color)
        f_mkey.pack(fill="x", pady=(0, 6))
        tk.Label(f_mkey, text="마스터 비상 복구 키:", font=("Arial", 9, "bold"), fg="#f87171", bg=self.card_color, width=17, anchor="w").pack(side="left")
        entry_mkey = tk.Entry(f_mkey, bg="#0f172a", fg="#fca5a5", insertbackground="white", relief="flat", font=("Arial", 9, "bold"))
        entry_mkey.insert(0, get_master_recovery_key())
        entry_mkey.pack(side="left", fill="x", expand=True, padx=(0, 6))

        show_mkey_var = tk.BooleanVar(value=True)
        def toggle_mkey():
            entry_mkey.config(show="" if show_mkey_var.get() else "*")
        tk.Checkbutton(f_mkey, text="표시", variable=show_mkey_var, command=toggle_mkey, bg=self.card_color, fg="#94a3b8", selectcolor="#0f172a", activebackground=self.card_color, font=("Arial", 7)).pack(side="left")

        # 새로 설정할 토큰 입력 필드
        f_ntok = tk.Frame(frame_tab1, bg=self.card_color)
        f_ntok.pack(fill="x", pady=(0, 6))
        tk.Label(f_ntok, text="새 보안 토큰(선택):", font=("Arial", 9, "bold"), fg="#fbbf24", bg=self.card_color, width=17, anchor="w").pack(side="left")
        entry_ntok = tk.Entry(f_ntok, bg="#0f172a", fg="#fde68a", insertbackground="white", relief="flat", font=("Arial", 9, "bold"))
        entry_ntok.insert(0, self.entry_token.get().strip())
        entry_ntok.pack(side="left", fill="x", expand=True)

        tk.Label(
            frame_tab1,
            text="※ 비워둘 경우 원격 PC의 보안 토큰이 삭제(초기화/공백)되어 누구나 제어 가능해집니다.",
            font=("Arial", 8),
            fg="#94a3b8",
            bg=self.card_color
        ).pack(anchor="w", pady=(0, 10))

        # 작업 실행 버튼들
        def run_query_token_task():
            if not target_ips:
                messagebox.showerror("에러", "원격 대상 IP가 지정되지 않았습니다.", parent=diag)
                return
            mkey = entry_mkey.get().strip()
            if not mkey:
                messagebox.showerror("에러", "마스터 복구 키를 입력하십시오.", parent=diag)
                return

            self.root.config(cursor="watch")
            self.log(f"🚨 [마스터 복구] {len(target_ips)}대 원격 PC로부터 보안 토큰 읽어오기 시도 중...")

            def worker():
                results = []
                recovered_tokens = []
                for ip in target_ips:
                    resp = send_query_remote_token(ip, port, mkey)
                    ok = resp.get("success", False)
                    msg = resp.get("message", "응답 없음")
                    tok = resp.get("token", "")
                    dev = resp.get("device", ip)
                    results.append((ip, ok, msg, tok, dev))
                    if ok:
                        recovered_tokens.append(tok)

                def on_done():
                    self.root.config(cursor="")
                    succ_cnt = sum(1 for r in results if r[1])
                    for ip, ok, msg, tok, dev in results:
                        self.log(f"  [{ip}] {dev}: {msg}")

                    if succ_cnt > 0:
                        first_tok = recovered_tokens[0]
                        prompt_msg = f"총 {succ_cnt}대 PC로부터 토큰 조회를 완료했습니다.\n\n"
                        prompt_msg += f"• 확인된 기존 보안 토큰: '{first_tok}'" if first_tok else "• 확인된 상태: 토큰 미설정(공백)"
                        prompt_msg += "\n\n이 토큰을 현재 관리자 스케줄러의 보안 토큰 입력창에 채우시겠습니까?"
                        if messagebox.askyesno("토큰 복구 성공", prompt_msg, parent=diag):
                            self.entry_token.delete(0, tk.END)
                            self.entry_token.insert(0, first_tok)
                            self.log(f"✅ 복구된 보안 토큰 '{first_tok}'이 관리자 입력창에 자동 적용되었습니다.")
                            diag.destroy()
                    else:
                        messagebox.showerror("토큰 조회 실패", f"토큰 조회에 실패했습니다:\n{results[0][2]}", parent=diag)

                self.root.after(0, on_done)

            threading.Thread(target=worker, daemon=True).start()

        def run_force_reset_task(clear_mode=False):
            if not target_ips:
                messagebox.showerror("에러", "원격 대상 IP가 지정되지 않았습니다.", parent=diag)
                return
            mkey = entry_mkey.get().strip()
            if not mkey:
                messagebox.showerror("에러", "마스터 복구 키를 입력하십시오.", parent=diag)
                return

            new_val = "" if clear_mode else entry_ntok.get().strip()
            desc = "토큰 완전 삭제(초기화/공백)" if not new_val else f"새 토큰 '{new_val}'(으)로 강제 재설정"
            if not messagebox.askyesno("비상 강제 재설정", f"선택된 {len(target_ips)}대 원격 PC의 보안 토큰을\n[{desc}] 하시겠습니까?\n\n마스터 비상 복구 키 인증으로 기존 분실 토큰을 덮어씁니다.", parent=diag):
                return

            self.root.config(cursor="watch")
            self.log(f"🚨 [마스터 복구] {len(target_ips)}대 원격 PC로 보안 토큰 강제 덮어쓰기 전송 중... ({desc})")

            def worker():
                results = []
                for ip in target_ips:
                    resp = send_emergency_reset_token(ip, port, mkey, new_val)
                    ok = resp.get("success", False)
                    msg = resp.get("message", "응답 없음")
                    results.append((ip, ok, msg))

                def on_done():
                    self.root.config(cursor="")
                    succ_cnt = sum(1 for r in results if r[1])
                    for ip, ok, msg in results:
                        self.log(f"  [{ip}]: {msg}")

                    if succ_cnt > 0:
                        self.entry_token.delete(0, tk.END)
                        self.entry_token.insert(0, new_val)
                        messagebox.showinfo("복구 완료", f"총 {succ_cnt}/{len(target_ips)}대 원격 PC의 보안 토큰이 {desc}되었습니다.\n\n관리자 입력창에도 새 토큰이 반영되었습니다.", parent=diag)
                        diag.destroy()
                    else:
                        messagebox.showerror("복구 실패", f"토큰 강제 재설정에 실패했습니다:\n{results[0][2]}", parent=diag)

                self.root.after(0, on_done)

            threading.Thread(target=worker, daemon=True).start()

        btn_query_tok = ttk.Button(
            frame_tab1,
            text="🔍 방법 1: 원격 PC의 기존 보안 토큰 읽어오기 (조회)",
            style="Purple.TButton",
            command=run_query_token_task
        )
        btn_query_tok.pack(fill="x", pady=(0, 6))

        btn_override_tok = ttk.Button(
            frame_tab1,
            text="⚡ 방법 2: 마스터 키로 새 보안 토큰 강제 덮어쓰기 (재설정)",
            style="Green.TButton",
            command=lambda: run_force_reset_task(False)
        )
        btn_override_tok.pack(fill="x", pady=(0, 6))

        btn_clear_tok = ttk.Button(
            frame_tab1,
            text="🗑️ 방법 3: 원격 보안 토큰 완전 삭제 (초기화 - 공백)",
            style="Red.TButton",
            command=lambda: run_force_reset_task(True)
        )
        btn_clear_tok.pack(fill="x")

        # =====================================================================
        # 탭 2: 파워쉘 / 배치 원격 일괄 스크립트 (AD, Intune, PsExec)
        # =====================================================================
        tk.Label(
            frame_tab2,
            text="네트워크 포트가 닫혀있거나 사내 전체 PC를 일괄 초기화할 때 사용합니다.",
            font=("Arial", 9, "bold"),
            fg="#60a5fa",
            bg=self.card_color
        ).pack(anchor="w", pady=(0, 6))

        # PowerShell
        ps_box = tk.LabelFrame(frame_tab2, text=" 💻 PowerShell 원클릭 초기화 명령 (AD GPO / PsExec / Intune) ", bg=self.card_color, fg="#38bdf8", font=("Arial", 8, "bold"), padx=8, pady=6)
        ps_box.pack(fill="x", pady=(0, 8))

        ps_cmd = 'powershell -ExecutionPolicy Bypass -Command "$f=[Environment]::GetFolderPath(\'ApplicationData\')+\'\\PowerController\\power_timer_settings.json\'; if(Test-Path $f){$s=Get-Content $f -Raw|ConvertFrom-Json; $s.network_auth_token=\'\'; $s|ConvertTo-Json|Set-Content $f -Encoding UTF8; Write-Host \'TOKEN RESET SUCCESS\'}"'
        txt_ps = tk.Text(ps_box, height=3, bg="#0f172a", fg="#a5f3fc", relief="flat", font=("Consolas", 8), wrap="char")
        txt_ps.insert("1.0", ps_cmd)
        txt_ps.configure(state="disabled")
        txt_ps.pack(fill="x", pady=(0, 4))

        def copy_ps():
            self.root.clipboard_clear()
            self.root.clipboard_append(ps_cmd)
            messagebox.showinfo("복사 완료", "파워쉘 1-줄 초기화 명령어가 클립보드에 복사되었습니다.\n\nActive Directory GPO 또는 원격 파워쉘에서 실행하십시오.", parent=diag)

        tk.Button(ps_box, text="📋 파워쉘 명령어 복사", font=("Arial", 8, "bold"), bg="#0284c7", fg="white", relief="flat", padx=8, pady=2, command=copy_ps).pack(anchor="e")

        # CLI 명령
        cli_box = tk.LabelFrame(frame_tab2, text=" ⚙️ PowerTimer CLI 명령줄 직접 초기화 ", bg=self.card_color, fg="#fbbf24", font=("Arial", 8, "bold"), padx=8, pady=6)
        cli_box.pack(fill="x", pady=(0, 6))

        cli_cmd = "PowerTimer.exe --reset-token   (또는 python main.py --reset-token)"
        txt_cli = tk.Text(cli_box, height=2, bg="#0f172a", fg="#fde68a", relief="flat", font=("Consolas", 8))
        txt_cli.insert("1.0", cli_cmd)
        txt_cli.configure(state="disabled")
        txt_cli.pack(fill="x", pady=(0, 4))

        def copy_cli():
            self.root.clipboard_clear()
            self.root.clipboard_append("PowerTimer.exe --reset-token")
            messagebox.showinfo("복사 완료", "CLI 초기화 명령어가 클립보드에 복사되었습니다.", parent=diag)

        tk.Button(cli_box, text="📋 CLI 명령어 복사", font=("Arial", 8, "bold"), bg="#d97706", fg="white", relief="flat", padx=8, pady=2, command=copy_cli).pack(anchor="e")

        # =====================================================================
        # 탭 3: 상황별 복구 가이드
        # =====================================================================
        guide_txt = scrolledtext.ScrolledText(
            frame_tab3,
            bg="#0f172a",
            fg=self.text_color,
            font=("Arial", 9),
            relief="flat",
            wrap="word",
            padx=10,
            pady=8
        )
        guide_txt.pack(fill="both", expand=True)

        manual_content = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "  🚨 보안 토큰(비밀번호) 분실 시 상황별 대처 매뉴얼\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "■ 상황 1: 관리자가 기존 토큰을 기억하지 못하지만 원격 네트워크는 연결된 경우\n"
            "  1. 본 복구 센터의 [1. 마스터 키 원격 복구] 탭으로 이동합니다.\n"
            "  2. '방법 1: 기존 보안 토큰 읽어오기 (조회)'를 클릭합니다.\n"
            "  3. 마스터 비상 복구 키(기본값: PowerRescue#2026!Admin) 인증을 통해\n"
            "     클라이언트에 저장된 기존 토큰을 화면에 즉시 조회하여 불러옵니다.\n"
            "  4. 또는 '방법 2: 새 보안 토큰으로 강제 재설정'을 클릭하여\n"
            "     기존 토큰을 몰라도 원하는 새 토큰으로 원격 덮어쓰기합니다.\n\n"
            "■ 상황 2: 클라이언트 PC를 직접 방문하거나 원격 데스크톱(RDP)으로 접속 가능한 경우\n"
            "  1. 클라이언트 PC에서 PowerTimer 창을 엽니다.\n"
            "  2. [환경설정] 탭 -> [8. 원격 예약 수신 & 보안 토큰] 섹션으로 이동합니다.\n"
            "  3. '보안 인증 토큰' 입력란에 현재 설정된 토큰이 표시되어 있으므로 [📋 복사]를\n"
            "     누르거나, [🔄 토큰 초기화] 버튼을 눌러 공백으로 초기화합니다.\n\n"
            "■ 상황 3: Active Directory / 기업 도메인 사내 PC 일괄 초기화가 필요한 경우\n"
            "  1. [2. 파워쉘 일괄 초기화 스크립트] 탭의 명령어를 복사합니다.\n"
            "  2. Active Directory의 그룹 정책(GPO) 컴퓨터 시작 스크립트로 배포하거나,\n"
            "     PsExec, Intune 또는 원격 배치 파일을 실행합니다.\n"
            "  3. 사내 모든 PC의 power_timer_settings.json 파일 내 보안 토큰이\n"
            "     1초 만에 일괄 초기화됩니다.\n\n"
            "■ 상황 4: 마스터 비상 복구 키를 조직 전용 키로 변경하고 싶은 경우\n"
            "  1. 환경변수 'POWER_TIMER_MASTER_KEY'에 커스텀 키를 지정하거나,\n"
            "  2. 프로그램 폴더 내 'power_master_key.txt' 파일에 마스터 키를 적어두면\n"
            "     해당 키로 마스터 복구 권한이 적용됩니다.\n"
        )
        guide_txt.insert("1.0", manual_content)
        guide_txt.configure(state="disabled")

        # 초기 탭 표시
        show_tab(1)


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
    
    def on_window_exit():
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_window_exit)
    root.mainloop()
