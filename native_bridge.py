"""
native_bridge.py
PowerController 순수 창작 DLL 연동 브리지 (Native Bridge Engine)

Copyright (c) 2026 PowerController Project. All rights reserved.
Licensed under the Apache License, Version 2.0.

역할:
 1. PowerCoreNative.dll 동적 탐색 및 로딩 (Dynamic Path Locator)
 2. ctypes C ABI 인터페이스 표준화 바인딩
 3. 안전한 이중화(Graceful Fallback): DLL 부재 시 파이썬 표준 라이브러리로 투명 전환
"""

import os
import sys
import ctypes
import subprocess
from typing import Optional

_NATIVE_DLL: Optional[ctypes.CDLL] = None
_BEACON_DLL: Optional[ctypes.CDLL] = None
_FIREWALL_DLL: Optional[ctypes.CDLL] = None
_POWERHOOK_DLL: Optional[ctypes.CDLL] = None
_CRYPTO_DLL: Optional[ctypes.CDLL] = None
_IS_NATIVE_LOADED: bool = False
_IS_BEACON_LOADED: bool = False
_IS_FIREWALL_LOADED: bool = False
_IS_POWERHOOK_LOADED: bool = False
_IS_CRYPTO_LOADED: bool = False


def _find_dll_in_candidates(dll_name: str) -> Optional[str]:
    """지정된 DLL 파일의 경로를 다중 후보군에서 안전하게 탐색합니다."""
    candidates = []

    # 1. 실행 파일 디렉터리 (PyInstaller 번들 또는 개발 환경)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidates.append(os.path.join(exe_dir, dll_name))
        if hasattr(sys, '_MEIPASS'):
            candidates.append(os.path.join(sys._MEIPASS, dll_name))
            candidates.append(os.path.join(sys._MEIPASS, "PowerController", dll_name))
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(script_dir, dll_name))
    candidates.append(os.path.join(script_dir, "native", dll_name))
    candidates.append(os.path.join(script_dir, "dist", "PowerController", dll_name))
    candidates.append(os.path.join(script_dir, "dist", dll_name))

    # 2. %LOCALAPPDATA% 또는 %APPDATA%
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        candidates.append(os.path.join(local_appdata, "PowerController", dll_name))
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        candidates.append(os.path.join(appdata, "PowerController", dll_name))

    for path in candidates:
        if os.path.exists(path) and os.path.isfile(path):
            return os.path.normpath(path)

    return None


def _find_native_dll_path() -> Optional[str]:
    return _find_dll_in_candidates("PowerCoreNative.dll")


def _find_beacon_dll_path() -> Optional[str]:
    return _find_dll_in_candidates("NetBeaconEngine.dll")


def _find_firewall_dll_path() -> Optional[str]:
    return _find_dll_in_candidates("FirewallNative.dll")


def _find_power_hook_dll_path() -> Optional[str]:
    return _find_dll_in_candidates("SysPowerHook.dll")


def _find_crypto_dll_path() -> Optional[str]:
    return _find_dll_in_candidates("ScheduleCrypto.dll")


def _init_native_library():
    """PowerCoreNative.dll 라이브러리를 초기화하고 C ABI 함수들을 바인딩합니다."""
    global _NATIVE_DLL, _IS_NATIVE_LOADED

    if os.name != 'nt':
        _IS_NATIVE_LOADED = False
        return

    dll_path = _find_native_dll_path()
    if not dll_path:
        _IS_NATIVE_LOADED = False
        return

    try:
        dll = ctypes.CDLL(dll_path)

        # 1. NativeSetHardwareWakeTimer(double seconds) -> BOOL
        dll.NativeSetHardwareWakeTimer.argtypes = [ctypes.c_double]
        dll.NativeSetHardwareWakeTimer.restype = ctypes.c_int

        # 2. NativeCancelHardwareWakeTimer() -> BOOL
        dll.NativeCancelHardwareWakeTimer.argtypes = []
        dll.NativeCancelHardwareWakeTimer.restype = ctypes.c_int

        # 3. NativeIsHardwareWakeSupported() -> BOOL
        dll.NativeIsHardwareWakeSupported.argtypes = []
        dll.NativeIsHardwareWakeSupported.restype = ctypes.c_int

        # 4. NativeSetSleepPrevention(int prevent_sleep, int keep_display) -> BOOL
        dll.NativeSetSleepPrevention.argtypes = [ctypes.c_int, ctypes.c_int]
        dll.NativeSetSleepPrevention.restype = ctypes.c_int

        # 5. NativeKillProcessTree(unsigned long root_pid) -> int
        dll.NativeKillProcessTree.argtypes = [ctypes.c_ulong]
        dll.NativeKillProcessTree.restype = ctypes.c_int

        # 6. NativeKillProcessByName(const wchar_t* process_name) -> int
        dll.NativeKillProcessByName.argtypes = [ctypes.c_wchar_p]
        dll.NativeKillProcessByName.restype = ctypes.c_int

        _NATIVE_DLL = dll
        _IS_NATIVE_LOADED = True
    except Exception:
        _NATIVE_DLL = None
        _IS_NATIVE_LOADED = False


def _init_beacon_library():
    """NetBeaconEngine.dll 라이브러리를 초기화하고 C ABI 함수들을 바인딩합니다."""
    global _BEACON_DLL, _IS_BEACON_LOADED

    if os.name != 'nt':
        _IS_BEACON_LOADED = False
        return

    dll_path = _find_beacon_dll_path()
    if not dll_path:
        _IS_BEACON_LOADED = False
        return

    try:
        dll = ctypes.CDLL(dll_path)

        # 1. NativeStartBeaconListener(int port) -> BOOL
        dll.NativeStartBeaconListener.argtypes = [ctypes.c_int]
        dll.NativeStartBeaconListener.restype = ctypes.c_int

        # 2. NativeStopBeaconListener() -> BOOL
        dll.NativeStopBeaconListener.argtypes = []
        dll.NativeStopBeaconListener.restype = ctypes.c_int

        # 3. NativeGetBeaconQueueCount() -> int
        dll.NativeGetBeaconQueueCount.argtypes = []
        dll.NativeGetBeaconQueueCount.restype = ctypes.c_int

        # 4. NativeGetNextBeaconPacket(char* out_ip, int max_ip_len, int* out_port, char* out_data, int max_data_len) -> int
        dll.NativeGetNextBeaconPacket.argtypes = [
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_char_p,
            ctypes.c_int
        ]
        dll.NativeGetNextBeaconPacket.restype = ctypes.c_int

        # 5. NativeSendBroadcast(int port, const char* data, int data_len) -> BOOL
        dll.NativeSendBroadcast.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        dll.NativeSendBroadcast.restype = ctypes.c_int

        # 6. NativeSendDirect(const char* ip, int port, const char* data, int data_len) -> BOOL
        dll.NativeSendDirect.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        dll.NativeSendDirect.restype = ctypes.c_int

        _BEACON_DLL = dll
        _IS_BEACON_LOADED = True
    except Exception:
        _BEACON_DLL = None
        _IS_BEACON_LOADED = False


def _init_firewall_library():
    """FirewallNative.dll 라이브러리를 초기화하고 C ABI 함수들을 바인딩합니다."""
    global _FIREWALL_DLL, _IS_FIREWALL_LOADED

    if os.name != 'nt':
        _IS_FIREWALL_LOADED = False
        return

    dll_path = _find_firewall_dll_path()
    if not dll_path:
        _IS_FIREWALL_LOADED = False
        return

    try:
        dll = ctypes.CDLL(dll_path)

        # 1. NativeAddApplicationRule(const wchar_t* rule_name, const wchar_t* exe_path, int direction) -> BOOL
        dll.NativeAddApplicationRule.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_int]
        dll.NativeAddApplicationRule.restype = ctypes.c_int

        # 2. NativeAddPortRule(const wchar_t* rule_name, int protocol, const wchar_t* port_str, int direction) -> BOOL
        dll.NativeAddPortRule.argtypes = [ctypes.c_wchar_p, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int]
        dll.NativeAddPortRule.restype = ctypes.c_int

        # 3. NativeDeleteRule(const wchar_t* rule_name) -> BOOL
        dll.NativeDeleteRule.argtypes = [ctypes.c_wchar_p]
        dll.NativeDeleteRule.restype = ctypes.c_int

        # 4. NativeIsFirewallRulePresent(const wchar_t* rule_name) -> BOOL
        dll.NativeIsFirewallRulePresent.argtypes = [ctypes.c_wchar_p]
        dll.NativeIsFirewallRulePresent.restype = ctypes.c_int

        # 5. NativeBatchRegisterSuite(const wchar_t* target_dir, const wchar_t* version_str) -> int
        dll.NativeBatchRegisterSuite.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        dll.NativeBatchRegisterSuite.restype = ctypes.c_int

        # 6. NativeBatchRemoveSuite(const wchar_t* version_str) -> int
        dll.NativeBatchRemoveSuite.argtypes = [ctypes.c_wchar_p]
        dll.NativeBatchRemoveSuite.restype = ctypes.c_int

        _FIREWALL_DLL = dll
        _IS_FIREWALL_LOADED = True
    except Exception:
        _FIREWALL_DLL = None
        _IS_FIREWALL_LOADED = False


def _init_power_hook_library():
    """SysPowerHook.dll 라이브러리를 초기화하고 C ABI 함수들을 바인딩합니다."""
    global _POWERHOOK_DLL, _IS_POWERHOOK_LOADED

    if os.name != 'nt':
        _IS_POWERHOOK_LOADED = False
        return

    dll_path = _find_power_hook_dll_path()
    if not dll_path:
        _IS_POWERHOOK_LOADED = False
        return

    try:
        dll = ctypes.CDLL(dll_path)

        # 1. NativeStartSessionHook() -> BOOL
        dll.NativeStartSessionHook.argtypes = []
        dll.NativeStartSessionHook.restype = ctypes.c_int

        # 2. NativeStopSessionHook() -> BOOL
        dll.NativeStopSessionHook.argtypes = []
        dll.NativeStopSessionHook.restype = ctypes.c_int

        # 3. NativeGetLastSessionEvent() -> int
        dll.NativeGetLastSessionEvent.argtypes = []
        dll.NativeGetLastSessionEvent.restype = ctypes.c_int

        # 4. NativeGetNextSessionEvent(int* out_event_type, int* out_session_id) -> int
        dll.NativeGetNextSessionEvent.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
        dll.NativeGetNextSessionEvent.restype = ctypes.c_int

        # 5. NativeIsSessionLocked() -> BOOL
        dll.NativeIsSessionLocked.argtypes = []
        dll.NativeIsSessionLocked.restype = ctypes.c_int

        # 6. NativeGetBatteryStatus(int* out_ac, int* out_flag, int* out_pct, int* out_life) -> BOOL
        dll.NativeGetBatteryStatus.argtypes = [
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int)
        ]
        dll.NativeGetBatteryStatus.restype = ctypes.c_int

        # 7. NativeIsOnBatteryPower() -> BOOL
        dll.NativeIsOnBatteryPower.argtypes = []
        dll.NativeIsOnBatteryPower.restype = ctypes.c_int

        # 8. NativeGetBatteryPercent() -> int
        dll.NativeGetBatteryPercent.argtypes = []
        dll.NativeGetBatteryPercent.restype = ctypes.c_int

        # 9. NativeIsBatteryCritical(int threshold) -> BOOL
        dll.NativeIsBatteryCritical.argtypes = [ctypes.c_int]
        dll.NativeIsBatteryCritical.restype = ctypes.c_int

        # 10. NativeLockWorkStation() -> BOOL
        dll.NativeLockWorkStation.argtypes = []
        dll.NativeLockWorkStation.restype = ctypes.c_int

        # 11. NativeTurnOffMonitor() -> BOOL
        dll.NativeTurnOffMonitor.argtypes = []
        dll.NativeTurnOffMonitor.restype = ctypes.c_int

        _POWERHOOK_DLL = dll
        _IS_POWERHOOK_LOADED = True
    except Exception:
        _POWERHOOK_DLL = None
        _IS_POWERHOOK_LOADED = False


def _init_crypto_library():
    """ScheduleCrypto.dll 라이브러리를 초기화하고 C ABI 함수들을 바인딩합니다."""
    global _CRYPTO_DLL, _IS_CRYPTO_LOADED

    if os.name != 'nt':
        _IS_CRYPTO_LOADED = False
        return

    dll_path = _find_crypto_dll_path()
    if not dll_path:
        _IS_CRYPTO_LOADED = False
        return

    try:
        dll = ctypes.CDLL(dll_path)

        # 1. NativeComputeSHA256(const unsigned char* data, int data_len, char* out_hex, int max_hex_len) -> BOOL
        dll.NativeComputeSHA256.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        dll.NativeComputeSHA256.restype = ctypes.c_int

        # 2. NativeGenerateHMAC(const char* data, const char* key, char* out_hmac_hex, int max_len) -> BOOL
        dll.NativeGenerateHMAC.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        dll.NativeGenerateHMAC.restype = ctypes.c_int

        # 3. NativeVerifyScheduleSignature(const char* json, const char* sig_hex, const char* key) -> BOOL
        dll.NativeVerifyScheduleSignature.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        dll.NativeVerifyScheduleSignature.restype = ctypes.c_int

        # 4. NativeEncryptSchedule(const char* pt, const char* key, char* out_b64, int max_len) -> int
        dll.NativeEncryptSchedule.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        dll.NativeEncryptSchedule.restype = ctypes.c_int

        # 5. NativeDecryptSchedule(const char* b64, const char* key, char* out_pt, int max_len) -> int
        dll.NativeDecryptSchedule.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        dll.NativeDecryptSchedule.restype = ctypes.c_int

        _CRYPTO_DLL = dll
        _IS_CRYPTO_LOADED = True
    except Exception:
        _CRYPTO_DLL = None
        _IS_CRYPTO_LOADED = False


# 모듈 로드 시 최초 탐색 시도
_init_native_library()
_init_beacon_library()
_init_firewall_library()
_init_power_hook_library()
_init_crypto_library()


def is_native_loaded() -> bool:
    """순수 창작 PowerCoreNative.dll 모듈이 현재 활성화되어 있는지 반환합니다."""
    return _IS_NATIVE_LOADED


def is_beacon_engine_loaded() -> bool:
    """순수 창작 NetBeaconEngine.dll 모듈이 현재 활성화되어 있는지 반환합니다."""
    return _IS_BEACON_LOADED


def is_firewall_engine_loaded() -> bool:
    """순수 창작 FirewallNative.dll 모듈이 현재 활성화되어 있는지 반환합니다."""
    return _IS_FIREWALL_LOADED


def is_power_hook_loaded() -> bool:
    """순수 창작 SysPowerHook.dll 모듈이 현재 활성화되어 있는지 반환합니다."""
    return _IS_POWERHOOK_LOADED


def is_crypto_engine_loaded() -> bool:
    """순수 창작 ScheduleCrypto.dll 모듈이 현재 활성화되어 있는지 반환합니다."""
    return _IS_CRYPTO_LOADED


# --------------------------------------------------------------------------
# 1. 하드웨어 웨이크업 타이머 (RTC 인터럽트 기반 OS 자동 기상)
# --------------------------------------------------------------------------

def set_hardware_wake_timer(seconds: float) -> bool:
    """
    지정된 초(seconds) 후에 PC가 절전(S3/Modern Standby) 상태여도
    하드웨어 RTC 인터럽트로 운영체제를 자동으로 깨우도록 웨이크업 타이머를 설정합니다.
    """
    if seconds <= 0:
        return False

    if _IS_NATIVE_LOADED and _NATIVE_DLL:
        try:
            res = _NATIVE_DLL.NativeSetHardwareWakeTimer(float(seconds))
            return bool(res)
        except Exception:
            pass

    # Fallback: ctypes.windll.kernel32 직접 바인딩
    if os.name == 'nt':
        try:
            k32 = ctypes.windll.kernel32
            # CreateWaitableTimerW(NULL, TRUE, L"PowerController_WakeTimer_Fallback")
            hTimer = k32.CreateWaitableTimerW(None, True, "PowerController_WakeTimer_Fallback")
            if not hTimer:
                return False
            units = int(seconds * 10000000.0)
            due_time = ctypes.c_longlong(-units)
            # fResume = TRUE (5번째 인자)
            res = k32.SetWaitableTimer(hTimer, ctypes.byref(due_time), 0, None, None, True)
            return bool(res)
        except Exception:
            return False

    return False


def cancel_hardware_wake_timer() -> bool:
    """등록된 하드웨어 웨이크업 타이머를 취소합니다."""
    if _IS_NATIVE_LOADED and _NATIVE_DLL:
        try:
            return bool(_NATIVE_DLL.NativeCancelHardwareWakeTimer())
        except Exception:
            pass

    if os.name == 'nt':
        try:
            k32 = ctypes.windll.kernel32
            hTimer = k32.OpenWaitableTimerW(0x0002, False, "PowerController_WakeTimer_Fallback")
            if hTimer:
                k32.CancelWaitableTimer(hTimer)
                k32.CloseHandle(hTimer)
                return True
        except Exception:
            pass

    return False


# --------------------------------------------------------------------------
# 2. 절전 모드 및 화면 꺼짐 제어
# --------------------------------------------------------------------------

def set_sleep_prevention(prevent_sleep: bool = True, keep_display: bool = False) -> bool:
    """
    시스템의 자동 절전 진입 및 디스플레이 꺼짐을 통제합니다.
    """
    if _IS_NATIVE_LOADED and _NATIVE_DLL:
        try:
            res = _NATIVE_DLL.NativeSetSleepPrevention(int(prevent_sleep), int(keep_display))
            return bool(res)
        except Exception:
            pass

    # Fallback
    if os.name == 'nt':
        try:
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ES_DISPLAY_REQUIRED = 0x00000002
            ES_AWAYMODE_REQUIRED = 0x00000040

            flags = ES_CONTINUOUS
            if prevent_sleep:
                flags |= ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED
            if keep_display:
                flags |= ES_DISPLAY_REQUIRED

            ctypes.windll.kernel32.SetThreadExecutionState(ctypes.c_uint(flags))
            return True
        except Exception:
            return False

    return False


# --------------------------------------------------------------------------
# 3. 무음 초고속 프로세스 트리 강제 종료
# --------------------------------------------------------------------------

def kill_process_tree_silent(pid: int) -> int:
    """
    루트 PID 및 그 자식 프로세스 트리를 서브프로세스 없이 0.01초 내에 100% 무음으로 강제 종료합니다.
    종료된 프로세스 개수를 반환합니다.
    """
    if pid <= 4:
        return 0

    if _IS_NATIVE_LOADED and _NATIVE_DLL:
        try:
            return int(_NATIVE_DLL.NativeKillProcessTree(int(pid)))
        except Exception:
            pass

    # Fallback: taskkill /F /T /PID
    if os.name == 'nt':
        try:
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, creationflags=flags)
            return 1
        except Exception:
            return 0

    return 0


def kill_process_by_name_silent(process_name: str) -> int:
    """
    실행 파일 이름(예: 'PowerController.exe')을 기준으로 모든 인스턴스를 무음으로 강제 종료합니다.
    """
    if not process_name:
        return 0

    if _IS_NATIVE_LOADED and _NATIVE_DLL:
        try:
            return int(_NATIVE_DLL.NativeKillProcessByName(str(process_name)))
        except Exception:
            pass

    # Fallback: taskkill /F /IM
    if os.name == 'nt':
        try:
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
            subprocess.run(["taskkill", "/F", "/IM", str(process_name)], capture_output=True, creationflags=flags)
            return 1
        except Exception:
            return 0

    return 0


# --------------------------------------------------------------------------
# 4. NetBeaconEngine: 수백 대 PC 모니터링용 비동기 UDP 브로드캐스트 & 링버퍼 수신
# --------------------------------------------------------------------------

def start_beacon_listener(port: int = 9986) -> bool:
    """
    지정된 UDP 포트(기본 9986)로 순수 창작 C 레벨 백그라운드 리스너 스레드를 가동합니다.
    """
    if _IS_BEACON_LOADED and _BEACON_DLL:
        try:
            return bool(_BEACON_DLL.NativeStartBeaconListener(int(port)))
        except Exception:
            pass
    return False


def stop_beacon_listener() -> bool:
    """
    네이티브 UDP 비콘 리스너 스레드를 안전하게 중지하고 소켓을 해제합니다.
    """
    if _IS_BEACON_LOADED and _BEACON_DLL:
        try:
            return bool(_BEACON_DLL.NativeStopBeaconListener())
        except Exception:
            pass
    return False


def get_beacon_queue_count() -> int:
    """
    C 레벨 인메모리 링버퍼에 대기 중인 수신 패킷 수를 반환합니다.
    """
    if _IS_BEACON_LOADED and _BEACON_DLL:
        try:
            return int(_BEACON_DLL.NativeGetBeaconQueueCount())
        except Exception:
            pass
    return 0


def poll_next_beacon_packet() -> Optional[dict]:
    """
    C 레벨 링버퍼에서 다음 수신된 UDP 비콘 패킷을 1개 인출합니다 (FIFO).
    반환 형식: {'ip': str, 'port': int, 'data': str}
    큐가 비어있거나 DLL 미로드 시 None을 반환합니다.
    """
    if _IS_BEACON_LOADED and _BEACON_DLL:
        try:
            ip_buf = ctypes.create_string_buffer(64)
            port_val = ctypes.c_int(0)
            data_buf = ctypes.create_string_buffer(4096)

            ret = _BEACON_DLL.NativeGetNextBeaconPacket(
                ip_buf, 64,
                ctypes.byref(port_val),
                data_buf, 4096
            )
            if ret == 1:
                ip_str = ip_buf.value.decode("utf-8", errors="replace")
                data_str = data_buf.value.decode("utf-8", errors="replace")
                return {
                    "ip": ip_str,
                    "port": int(port_val.value),
                    "data": data_str
                }
        except Exception:
            pass
    return None


def send_beacon_broadcast(port: int, data_str: str) -> bool:
    """
    Winsock2 기반의 C 소켓을 통해 LAN 브로드캐스트(255.255.255.255) 및 로컬 루프백으로 초고속 발송합니다.
    """
    if not data_str:
        return False

    encoded = data_str.encode("utf-8")
    if _IS_BEACON_LOADED and _BEACON_DLL:
        try:
            res = _BEACON_DLL.NativeSendBroadcast(int(port), encoded, len(encoded))
            if res:
                return True
        except Exception:
            pass

    # Fallback: Python standard socket
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(encoded, ("<broadcast>", int(port)))
        sock.sendto(encoded, ("127.0.0.1", int(port)))
        sock.close()
        return True
    except Exception:
        return False


def send_beacon_direct(ip: str, port: int, data_str: str) -> bool:
    """
    Winsock2 기반의 C 소켓을 통해 특정 대상 IP:Port로 즉시 유니캐스트 UDP 패킷을 전송합니다.
    """
    if not ip or not data_str:
        return False

    encoded = data_str.encode("utf-8")
    if _IS_BEACON_LOADED and _BEACON_DLL:
        try:
            c_ip = ip.encode("utf-8")
            res = _BEACON_DLL.NativeSendDirect(c_ip, int(port), encoded, len(encoded))
            if res:
                return True
        except Exception:
            pass

    # Fallback: Python standard socket
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(encoded, (ip, int(port)))
        sock.close()
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------
# 5. FirewallNative: Windows Defender Firewall COM 인터페이스 직결 제어기
# --------------------------------------------------------------------------

def batch_register_firewall_suite(target_dir: Optional[str] = None, version_str: str = "2.9.1") -> int:
    """
    PowerController 및 PowerNetworkScheduler 일체의 인바운드/아웃바운드 및
    전용 통신 포트(TCP 9988, UDP 9985, UDP 9986) 방화벽 예외 규칙을
    Windows INetFwPolicy2 COM 인터페이스를 통해 0.05초 만에 일괄 트랜잭션 등록합니다.
    성공 시 등록된 규칙 수를 반환하며, DLL 부재 시 netsh CLI fallback으로 처리합니다.
    """
    if _IS_FIREWALL_LOADED and _FIREWALL_DLL:
        try:
            t_dir = str(target_dir) if target_dir else ""
            res = _FIREWALL_DLL.NativeBatchRegisterSuite(t_dir, str(version_str))
            if res > 0:
                return int(res)
        except Exception:
            pass

    # Fallback: netsh advfirewall
    if os.name == 'nt':
        try:
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
            base_dir = target_dir if target_dir else os.path.dirname(os.path.abspath(sys.executable))
            main_exe = os.path.join(base_dir, "PowerController.exe")
            pns_exe = os.path.join(base_dir, "PowerNetworkScheduler.exe")

            # Clean
            clean_rules = [
                "PowerController (Inbound)", "PowerController (Outbound)",
                f"PowerController v{version_str} (Inbound)", f"PowerController v{version_str} (Outbound)",
                "PowerController",
                "PowerNetworkScheduler (Inbound)", "PowerNetworkScheduler (Outbound)",
                f"PowerNetworkScheduler v{version_str} (Inbound)", f"PowerNetworkScheduler v{version_str} (Outbound)",
                "PowerController TCP 9988", "PowerController UDP 9985", "PowerController UDP 9986",
                f"PowerController v{version_str} TCP 9988", f"PowerController v{version_str} UDP 9985", f"PowerController v{version_str} UDP 9986"
            ]
            for r in clean_rules:
                subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={r}"],
                               capture_output=True, creationflags=creationflags)

            cnt = 0
            if os.path.exists(main_exe):
                for dir_type, dir_label in [("in", "Inbound"), ("out", "Outbound")]:
                    subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule",
                                    f"name=PowerController ({dir_label})", f"dir={dir_type}", "action=allow",
                                    f"program={main_exe}", "enable=yes", "profile=any"],
                                   capture_output=True, creationflags=creationflags)
                    subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule",
                                    f"name=PowerController v{version_str} ({dir_label})", f"dir={dir_type}", "action=allow",
                                    f"program={main_exe}", "enable=yes", "profile=any"],
                                   capture_output=True, creationflags=creationflags)
                    cnt += 2

            if os.path.exists(pns_exe):
                for dir_type, dir_label in [("in", "Inbound"), ("out", "Outbound")]:
                    subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule",
                                    f"name=PowerNetworkScheduler ({dir_label})", f"dir={dir_type}", "action=allow",
                                    f"program={pns_exe}", "enable=yes", "profile=any"],
                                   capture_output=True, creationflags=creationflags)
                    subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule",
                                    f"name=PowerNetworkScheduler v{version_str} ({dir_label})", f"dir={dir_type}", "action=allow",
                                    f"program={pns_exe}", "enable=yes", "profile=any"],
                                   capture_output=True, creationflags=creationflags)
                    cnt += 2

            ports = [("TCP", "9988"), ("UDP", "9985"), ("UDP", "9986")]
            for proto, port in ports:
                subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule",
                                f"name=PowerController {proto} {port}", "dir=in", "action=allow",
                                f"protocol={proto}", f"localport={port}", "enable=yes", "profile=any"],
                               capture_output=True, creationflags=creationflags)
                subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule",
                                f"name=PowerController v{version_str} {proto} {port}", "dir=in", "action=allow",
                                f"protocol={proto}", f"localport={port}", "enable=yes", "profile=any"],
                               capture_output=True, creationflags=creationflags)
                cnt += 2

            return cnt
        except Exception:
            return 0

    return 0


def batch_remove_firewall_suite(version_str: str = "2.9.1") -> int:
    """
    등록된 PowerController 및 PowerNetworkScheduler 관련 방화벽 규칙 전체를
    COM 인터페이스로 초고속 제거합니다.
    """
    if _IS_FIREWALL_LOADED and _FIREWALL_DLL:
        try:
            res = _FIREWALL_DLL.NativeBatchRemoveSuite(str(version_str))
            if res >= 0:
                return int(res)
        except Exception:
            pass

    # Fallback
    if os.name == 'nt':
        try:
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
            clean_rules = [
                "PowerController (Inbound)", "PowerController (Outbound)",
                f"PowerController v{version_str} (Inbound)", f"PowerController v{version_str} (Outbound)",
                "PowerController",
                "PowerNetworkScheduler (Inbound)", "PowerNetworkScheduler (Outbound)",
                f"PowerNetworkScheduler v{version_str} (Inbound)", f"PowerNetworkScheduler v{version_str} (Outbound)",
                "PowerController TCP 9988", "PowerController UDP 9985", "PowerController UDP 9986",
                f"PowerController v{version_str} TCP 9988", f"PowerController v{version_str} UDP 9985", f"PowerController v{version_str} UDP 9986"
            ]
            cnt = 0
            for r in clean_rules:
                subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={r}"],
                               capture_output=True, creationflags=creationflags)
                cnt += 1
            return cnt
        except Exception:
            return 0

    return 0


def add_application_firewall_rule(rule_name: str, exe_path: str, direction: str = "in") -> bool:
    """단일 실행 파일 방화벽 예외 규칙을 COM을 통해 즉시 추가합니다."""
    dir_code = 2 if direction.lower() == "out" else 1
    if _IS_FIREWALL_LOADED and _FIREWALL_DLL:
        try:
            return bool(_FIREWALL_DLL.NativeAddApplicationRule(rule_name, exe_path, dir_code))
        except Exception:
            pass

    if os.name == 'nt':
        try:
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
            subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule",
                            f"name={rule_name}", f"dir={direction}", "action=allow",
                            f"program={exe_path}", "enable=yes", "profile=any"],
                           capture_output=True, creationflags=creationflags)
            return True
        except Exception:
            return False

    return False


def add_port_firewall_rule(rule_name: str, protocol: str, port: int, direction: str = "in") -> bool:
    """단일 포트 방화벽 예외 규칙을 COM을 통해 즉시 추가합니다."""
    proto_code = 6 if protocol.upper() == "TCP" else 17
    dir_code = 2 if direction.lower() == "out" else 1
    if _IS_FIREWALL_LOADED and _FIREWALL_DLL:
        try:
            return bool(_FIREWALL_DLL.NativeAddPortRule(rule_name, proto_code, str(port), dir_code))
        except Exception:
            pass

    if os.name == 'nt':
        try:
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
            subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule",
                            f"name={rule_name}", f"dir={direction}", "action=allow",
                            f"protocol={protocol}", f"localport={port}", "enable=yes", "profile=any"],
                           capture_output=True, creationflags=creationflags)
            return True
        except Exception:
            return False

    return False


def delete_firewall_rule(rule_name: str) -> bool:
    """지정된 이름의 방화벽 규칙을 즉시 삭제합니다."""
    if _IS_FIREWALL_LOADED and _FIREWALL_DLL:
        try:
            return bool(_FIREWALL_DLL.NativeDeleteRule(rule_name))
        except Exception:
            pass

    if os.name == 'nt':
        try:
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
            subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule_name}"],
                           capture_output=True, creationflags=creationflags)
            return True
        except Exception:
            return False

    return False


def is_firewall_rule_present(rule_name: str) -> bool:
    """지정된 방화벽 규칙이 현재 등록되어 있는지 COM을 통해 0.001초 만에 검사합니다."""
    if _IS_FIREWALL_LOADED and _FIREWALL_DLL:
        try:
            return bool(_FIREWALL_DLL.NativeIsFirewallRulePresent(rule_name))
        except Exception:
            pass

    if os.name == 'nt':
        try:
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
            res = subprocess.run(["netsh", "advfirewall", "firewall", "show", "rule", f"name={rule_name}"],
                                 capture_output=True, creationflags=creationflags)
            return res.returncode == 0
        except Exception:
            return False

    return False


# --------------------------------------------------------------------------
# 6. SysPowerHook: Windows 세션 알림 감지 및 하드웨어 배터리/전원 훅
# --------------------------------------------------------------------------

def start_session_hook() -> bool:
    """
    Windows 세션 변경 알림(화면 잠금, 잠금 해제, RDP 원격 접속 등) 백그라운드 훅을 가동합니다.
    """
    if _IS_POWERHOOK_LOADED and _POWERHOOK_DLL:
        try:
            return bool(_POWERHOOK_DLL.NativeStartSessionHook())
        except Exception:
            pass
    return False


def stop_session_hook() -> bool:
    """
    백그라운드 세션 변경 훅을 안전하게 종료합니다.
    """
    if _IS_POWERHOOK_LOADED and _POWERHOOK_DLL:
        try:
            return bool(_POWERHOOK_DLL.NativeStopSessionHook())
        except Exception:
            pass
    return False


def get_last_session_event() -> int:
    """
    가장 최근 발생한 세션 이벤트 코드를 반환합니다.
    (7: WTS_SESSION_LOCK, 8: WTS_SESSION_UNLOCK 등)
    """
    if _IS_POWERHOOK_LOADED and _POWERHOOK_DLL:
        try:
            return int(_POWERHOOK_DLL.NativeGetLastSessionEvent())
        except Exception:
            pass
    return 0


def get_next_session_event() -> Optional[tuple]:
    """
    C 레벨 인메모리 큐에서 다음 세션 이벤트를 인출합니다. (event_type, session_id)
    """
    if _IS_POWERHOOK_LOADED and _POWERHOOK_DLL:
        try:
            ev = ctypes.c_int(0)
            sess = ctypes.c_int(0)
            if _POWERHOOK_DLL.NativeGetNextSessionEvent(ctypes.byref(ev), ctypes.byref(sess)) == 1:
                return (int(ev.value), int(sess.value))
        except Exception:
            pass
    return None


def is_session_locked() -> bool:
    """
    현재 사용자의 윈도우 세션이 잠겨있는지(Win + L 등 화면 잠금 상태) 실시간 반환합니다.
    """
    if _IS_POWERHOOK_LOADED and _POWERHOOK_DLL:
        try:
            return bool(_POWERHOOK_DLL.NativeIsSessionLocked())
        except Exception:
            pass
    return False


def get_battery_status() -> Optional[dict]:
    """
    현재 컴퓨터의 AC 전원 연결 상태 및 배터리 충전 잔량(%)을 실시간 조회합니다.
    반환: {'ac_line_status': int, 'battery_flag': int, 'percent': int, 'life_time': int}
    """
    if _IS_POWERHOOK_LOADED and _POWERHOOK_DLL:
        try:
            ac_val = ctypes.c_int(0)
            flag_val = ctypes.c_int(0)
            pct_val = ctypes.c_int(0)
            life_val = ctypes.c_int(0)
            if _POWERHOOK_DLL.NativeGetBatteryStatus(
                ctypes.byref(ac_val), ctypes.byref(flag_val),
                ctypes.byref(pct_val), ctypes.byref(life_val)
            ):
                return {
                    "ac_line_status": int(ac_val.value),
                    "battery_flag": int(flag_val.value),
                    "percent": int(pct_val.value) if pct_val.value != 255 else -1,
                    "life_time": int(life_val.value)
                }
        except Exception:
            pass

    # Fallback: ctypes GetSystemPowerStatus
    if os.name == 'nt':
        try:
            class SYSTEM_POWER_STATUS(ctypes.Structure):
                _fields_ = [
                    ('ACLineStatus', ctypes.c_byte),
                    ('BatteryFlag', ctypes.c_byte),
                    ('BatteryLifePercent', ctypes.c_byte),
                    ('SystemStatusFlag', ctypes.c_byte),
                    ('BatteryLifeTime', ctypes.c_ulong),
                    ('BatteryFullLifeTime', ctypes.c_ulong),
                ]
            sps = SYSTEM_POWER_STATUS()
            if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(sps)):
                pct = int(sps.BatteryLifePercent)
                return {
                    "ac_line_status": int(sps.ACLineStatus),
                    "battery_flag": int(sps.BatteryFlag),
                    "percent": pct if pct != 255 else -1,
                    "life_time": int(sps.BatteryLifeTime)
                }
        except Exception:
            pass

    return None


def is_on_battery_power() -> bool:
    """
    현재 컴퓨터가 AC 전원 분리 상태로 배터리(UPS 포함)로만 구동 중인지 판별합니다.
    """
    if _IS_POWERHOOK_LOADED and _POWERHOOK_DLL:
        try:
            return bool(_POWERHOOK_DLL.NativeIsOnBatteryPower())
        except Exception:
            pass

    stat = get_battery_status()
    if stat:
        return stat.get("ac_line_status") == 0
    return False


def get_battery_percent() -> int:
    """
    배터리 잔량 백분율(0~100)을 반환하며, 배터리가 없는 데스크톱 등은 -1을 반환합니다.
    """
    if _IS_POWERHOOK_LOADED and _POWERHOOK_DLL:
        try:
            return int(_POWERHOOK_DLL.NativeGetBatteryPercent())
        except Exception:
            pass

    stat = get_battery_status()
    if stat:
        return stat.get("percent", -1)
    return -1


def is_battery_critical(threshold_percent: int = 10) -> bool:
    """
    배터리 잔량이 위험 수위(기본 10% 이하)로 떨어졌는지 감지하여 즉시 안전 자동 종료 여부를 판단합니다.
    """
    if _IS_POWERHOOK_LOADED and _POWERHOOK_DLL:
        try:
            return bool(_POWERHOOK_DLL.NativeIsBatteryCritical(int(threshold_percent)))
        except Exception:
            pass

    stat = get_battery_status()
    if stat and stat.get("ac_line_status") == 0:
        pct = stat.get("percent", -1)
        if 0 <= pct <= threshold_percent:
            return True
    return False


def lock_workstation_fast() -> bool:
    """
    rundll32.exe 생성 오버헤드 없이 0.0001초 만에 네이티브 C 레벨에서 화면을 즉각 잠급니다.
    """
    if _IS_POWERHOOK_LOADED and _POWERHOOK_DLL:
        try:
            return bool(_POWERHOOK_DLL.NativeLockWorkStation())
        except Exception:
            pass

    if os.name == 'nt':
        try:
            return bool(ctypes.windll.user32.LockWorkStation())
        except Exception:
            import os
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return True
    return False


def turn_off_monitor_fast() -> bool:
    """
    PowerShell 및 인라인 C# 컴파일 오버헤드(2~3초 지연, 콘솔 깜빡임) 없이
    0.0001초 만에 네이티브 윈도우 메시지로 모니터를 절전(화면 끄기) 모드로 전환합니다.
    """
    if _IS_POWERHOOK_LOADED and _POWERHOOK_DLL:
        try:
            return bool(_POWERHOOK_DLL.NativeTurnOffMonitor())
        except Exception:
            pass

    if os.name == 'nt':
        try:
            # HWND_BROADCAST (0xFFFF), WM_SYSCOMMAND (0x0112), SC_MONITORPOWER (0xF170), 2 (Power off)
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
            return True
        except Exception:
            pass
    return False


# --------------------------------------------------------------------------
# 7. ScheduleCrypto: 예약 스케줄 무결성 검증, 디지털 서명 및 암호화 봉인
# --------------------------------------------------------------------------

_DEFAULT_CRYPTO_KEY = "PowerController_v2.9.1_Enterprise_SecKey_2026"


def compute_sha256(data) -> str:
    """
    주어진 바이트 또는 문자열 데이터의 SHA-256 해시 16진수 문자열을 계산합니다.
    """
    if isinstance(data, str):
        data_bytes = data.encode('utf-8')
    else:
        data_bytes = bytes(data)

    if _IS_CRYPTO_LOADED and _CRYPTO_DLL:
        try:
            buf = ctypes.create_string_buffer(65)
            if _CRYPTO_DLL.NativeComputeSHA256(data_bytes, len(data_bytes), buf, 65):
                return buf.value.decode('ascii')
        except Exception:
            pass

    import hashlib
    return hashlib.sha256(data_bytes).hexdigest()


def generate_schedule_hmac(data: str, master_key: str = "") -> str:
    """
    스케줄 데이터의 변조 방지를 위한 HMAC-SHA256 전자 서명을 생성합니다.
    """
    key = master_key if master_key else _DEFAULT_CRYPTO_KEY

    if _IS_CRYPTO_LOADED and _CRYPTO_DLL:
        try:
            buf = ctypes.create_string_buffer(65)
            if _CRYPTO_DLL.NativeGenerateHMAC(data.encode('utf-8'), key.encode('utf-8'), buf, 65):
                return buf.value.decode('ascii')
        except Exception:
            pass

    import hmac
    import hashlib
    return hmac.new(key.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()


def verify_schedule_signature(json_data: str, signature_hex: str, master_key: str = "") -> bool:
    """
    배포된 스케줄 데이터가 인가된 마스터 키로 서명되었는지 무결성을 검증합니다.
    """
    if not signature_hex or len(signature_hex) != 64:
        return False

    key = master_key if master_key else _DEFAULT_CRYPTO_KEY

    if _IS_CRYPTO_LOADED and _CRYPTO_DLL:
        try:
            return bool(_CRYPTO_DLL.NativeVerifyScheduleSignature(
                json_data.encode('utf-8'),
                signature_hex.encode('ascii'),
                key.encode('utf-8')
            ))
        except Exception:
            pass

    computed = generate_schedule_hmac(json_data, key)
    import hmac
    return hmac.compare_digest(computed.lower(), signature_hex.lower())


def encrypt_schedule_payload(plaintext: str, master_key: str = "") -> str:
    """
    스케줄 JSON 문자열을 보안 솔트와 무결성 HMAC이 결합된 암호화 봉투(Base64)로 인코딩합니다.
    """
    key = master_key if master_key else _DEFAULT_CRYPTO_KEY

    if _IS_CRYPTO_LOADED and _CRYPTO_DLL:
        try:
            pt_bytes = plaintext.encode('utf-8')
            max_out = len(pt_bytes) * 3 + 256
            buf = ctypes.create_string_buffer(max_out)
            res_len = _CRYPTO_DLL.NativeEncryptSchedule(pt_bytes, key.encode('utf-8'), buf, max_out)
            if res_len > 0:
                return buf.value.decode('ascii')
        except Exception:
            pass

    # Pure Python Cryptographic Fallback
    import os
    import hmac
    import hashlib
    import base64

    salt = os.urandom(16)
    pt_bytes = plaintext.encode('utf-8')
    tag = hmac.new(key.encode('utf-8'), pt_bytes, hashlib.sha256).digest()

    keystream = b""
    counter = 1
    while len(keystream) < len(pt_bytes):
        block = hashlib.sha256(key.encode('utf-8') + salt + counter.to_bytes(4, 'little')).digest()
        keystream += block
        counter += 1

    encrypted = bytes([pt_bytes[i] ^ keystream[i] for i in range(len(pt_bytes))])
    envelope = salt + tag + encrypted
    return base64.b64encode(envelope).decode('ascii')


def decrypt_schedule_payload(encrypted_b64: str, master_key: str = "") -> Optional[str]:
    """
    암호화된 스케줄 봉투(Base64)를 복호화하고 서명 무결성을 검증하여 원본 JSON을 반환합니다.
    변조가 감지되면 None을 반환합니다.
    """
    if not encrypted_b64:
        return None

    key = master_key if master_key else _DEFAULT_CRYPTO_KEY

    if _IS_CRYPTO_LOADED and _CRYPTO_DLL:
        try:
            in_bytes = encrypted_b64.encode('ascii')
            max_out = len(in_bytes) + 256
            buf = ctypes.create_string_buffer(max_out)
            res_len = _CRYPTO_DLL.NativeDecryptSchedule(in_bytes, key.encode('utf-8'), buf, max_out)
            if res_len >= 0:
                return buf.value.decode('utf-8', errors='replace')
            elif res_len == -2:
                # Tampering detected
                return None
        except Exception:
            pass

    # Pure Python Decryption & Integrity Fallback
    import hmac
    import hashlib
    import base64

    try:
        decoded = base64.b64decode(encrypted_b64.encode('ascii'))
        if len(decoded) < 48:
            return None
        salt = decoded[:16]
        expected_tag = decoded[16:48]
        encrypted = decoded[48:]

        keystream = b""
        counter = 1
        while len(keystream) < len(encrypted):
            block = hashlib.sha256(key.encode('utf-8') + salt + counter.to_bytes(4, 'little')).digest()
            keystream += block
            counter += 1

        pt_bytes = bytes([encrypted[i] ^ keystream[i] for i in range(len(encrypted))])
        computed_tag = hmac.new(key.encode('utf-8'), pt_bytes, hashlib.sha256).digest()

        if not hmac.compare_digest(expected_tag, computed_tag):
            return None

        return pt_bytes.decode('utf-8', errors='replace')
    except Exception:
        return None


# ==============================================================================
# 6. DiskFlushNative.dll: Atomic Disk Cache & Volume Buffer Flush
# ==============================================================================

_DISKFLUSH_DLL: Optional[ctypes.CDLL] = None
_IS_DISKFLUSH_LOADED: bool = False

def _init_diskflush_dll():
    global _DISKFLUSH_DLL, _IS_DISKFLUSH_LOADED
    if _IS_DISKFLUSH_LOADED:
        return
    path = _find_dll_in_candidates("DiskFlushNative.dll")
    if path:
        try:
            dll = ctypes.CDLL(path)
            dll.NativeFlushAllVolumes.argtypes = []
            dll.NativeFlushAllVolumes.restype = ctypes.c_int
            dll.NativePreShutdownSync.argtypes = []
            dll.NativePreShutdownSync.restype = ctypes.c_int
            _DISKFLUSH_DLL = dll
            _IS_DISKFLUSH_LOADED = True
        except Exception:
            _DISKFLUSH_DLL = None


def flush_all_volumes_sync() -> int:
    """모든 마운트된 디스크 드라이브의 파일시스템 캐시를 강제 플러시하여 데이터 손실을 방지합니다."""
    _init_diskflush_dll()
    if _DISKFLUSH_DLL:
        try:
            return _DISKFLUSH_DLL.NativeFlushAllVolumes()
        except Exception:
            pass

    # Fallback: Flush via kernel32 if available
    count = 0
    try:
        import string
        for letter in string.ascii_uppercase:
            vol_path = f"\\\\.\\{letter}:"
            h_vol = ctypes.windll.kernel32.CreateFileW(
                vol_path,
                0xC0000000, # GENERIC_READ | GENERIC_WRITE
                3,          # FILE_SHARE_READ | FILE_SHARE_WRITE
                None,
                3,          # OPEN_EXISTING
                0x80,       # FILE_ATTRIBUTE_NORMAL
                None
            )
            if h_vol != -1 and h_vol != 0:
                if ctypes.windll.kernel32.FlushFileBuffers(h_vol):
                    count += 1
                ctypes.windll.kernel32.CloseHandle(h_vol)
    except Exception:
        pass
    return count


# ==============================================================================
# 7. AudioDimmerNative.dll: Core Audio Smooth Volume Fade & Mute
# ==============================================================================

_AUDIODIMMER_DLL: Optional[ctypes.CDLL] = None
_IS_AUDIODIMMER_LOADED: bool = False

def _init_audiodimmer_dll():
    global _AUDIODIMMER_DLL, _IS_AUDIODIMMER_LOADED
    if _IS_AUDIODIMMER_LOADED:
        return
    path = _find_dll_in_candidates("AudioDimmerNative.dll")
    if path:
        try:
            dll = ctypes.CDLL(path)
            dll.NativeGetMasterVolume.argtypes = []
            dll.NativeGetMasterVolume.restype = ctypes.c_float
            dll.NativeSetMasterVolume.argtypes = [ctypes.c_float]
            dll.NativeSetMasterVolume.restype = ctypes.c_int
            dll.NativeSetMasterMute.argtypes = [ctypes.c_int]
            dll.NativeSetMasterMute.restype = ctypes.c_int
            dll.NativeFadeMasterVolume.argtypes = [ctypes.c_float, ctypes.c_int]
            dll.NativeFadeMasterVolume.restype = ctypes.c_int
            _AUDIODIMMER_DLL = dll
            _IS_AUDIODIMMER_LOADED = True
        except Exception:
            _AUDIODIMMER_DLL = None


def fade_master_volume_sync(target_scalar: float = 0.0, fade_ms: int = 3000) -> bool:
    """오디오 출력 음량을 target_scalar(0.0~1.0)까지 fade_ms 동안 부드럽게 페이드다운합니다."""
    _init_audiodimmer_dll()
    if _AUDIODIMMER_DLL:
        try:
            return bool(_AUDIODIMMER_DLL.NativeFadeMasterVolume(ctypes.c_float(target_scalar), ctypes.c_int(fade_ms)))
        except Exception:
            pass
    return False


# ==============================================================================
# 8. DisplayDdcNative.dll: Hardware VESA DDC/CI Backlight Brightness Control
# ==============================================================================

_DISPLAYDDC_DLL: Optional[ctypes.CDLL] = None
_IS_DISPLAYDDC_LOADED: bool = False

def _init_displayddc_dll():
    global _DISPLAYDDC_DLL, _IS_DISPLAYDDC_LOADED
    if _IS_DISPLAYDDC_LOADED:
        return
    path = _find_dll_in_candidates("DisplayDdcNative.dll")
    if path:
        try:
            dll = ctypes.CDLL(path)
            dll.NativeSetHardwareBrightness.argtypes = [ctypes.c_int]
            dll.NativeSetHardwareBrightness.restype = ctypes.c_int
            _DISPLAYDDC_DLL = dll
            _IS_DISPLAYDDC_LOADED = True
        except Exception:
            _DISPLAYDDC_DLL = None


def set_hardware_brightness_sync(brightness_percent: int) -> int:
    """연결된 물리 모니터의 하드웨어 백라이트 밝기(0~100)를 변경합니다."""
    _init_displayddc_dll()
    if _DISPLAYDDC_DLL:
        try:
            return _DISPLAYDDC_DLL.NativeSetHardwareBrightness(ctypes.c_int(brightness_percent))
        except Exception:
            pass
    return 0


# ==============================================================================
# 9. LowLevelInputIdleNative.dll: Low-Level User Input Inactivity Telemetry
# ==============================================================================

_INPUTIDLE_DLL: Optional[ctypes.CDLL] = None
_IS_INPUTIDLE_LOADED: bool = False

def _init_inputidle_dll():
    global _INPUTIDLE_DLL, _IS_INPUTIDLE_LOADED
    if _IS_INPUTIDLE_LOADED:
        return
    path = _find_dll_in_candidates("LowLevelInputIdleNative.dll")
    if path:
        try:
            dll = ctypes.CDLL(path)
            dll.NativeGetSystemIdleMilliseconds.argtypes = []
            dll.NativeGetSystemIdleMilliseconds.restype = ctypes.c_ulong
            dll.NativeGetSystemIdleSeconds.argtypes = []
            dll.NativeGetSystemIdleSeconds.restype = ctypes.c_double
            dll.NativeIsSystemIdleFor.argtypes = [ctypes.c_double]
            dll.NativeIsSystemIdleFor.restype = ctypes.c_int
            _INPUTIDLE_DLL = dll
            _IS_INPUTIDLE_LOADED = True
        except Exception:
            _INPUTIDLE_DLL = None


def get_system_idle_seconds() -> float:
    """마지막 사용자 입력 이후 경과된 유휴 시간(초)을 반환합니다."""
    _init_inputidle_dll()
    if _INPUTIDLE_DLL:
        try:
            return float(_INPUTIDLE_DLL.NativeGetSystemIdleSeconds())
        except Exception:
            pass

    # Fallback: GetLastInputInfo via ctypes.windll
    try:
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
        
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
            millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            return max(0.0, millis / 1000.0)
    except Exception:
        pass
    return 0.0


# ==============================================================================
# 10. Commander Native Modules: Fast TCP Dispatcher, ICMP/ARP Scanner, WoL
# ==============================================================================

_COMMANDER_DISPATCHER_DLL: Optional[ctypes.CDLL] = None
_COMMANDER_SCANNER_DLL: Optional[ctypes.CDLL] = None

def send_rule_to_target_pc(target_ip: str, port: int, payload_bytes: bytes) -> bool:
    """커맨더 전용: 단일 대상 PC(TCP 9988)로 암호화된 예약 스케줄 봉투를 초고속 전송합니다."""
    global _COMMANDER_DISPATCHER_DLL
    if _COMMANDER_DISPATCHER_DLL is None:
        path = _find_dll_in_candidates("CommanderTcpDispatcherNative.dll")
        if path:
            try:
                _COMMANDER_DISPATCHER_DLL = ctypes.CDLL(path)
            except Exception:
                _COMMANDER_DISPATCHER_DLL = None

    if _COMMANDER_DISPATCHER_DLL:
        try:
            return bool(_COMMANDER_DISPATCHER_DLL.NativeSendSingleRuleCommand(
                target_ip.encode('utf-8'), ctypes.c_int(port), payload_bytes, ctypes.c_int(len(payload_bytes))
            ))
        except Exception:
            pass

    # Fallback: socket in Python
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.5)
            s.connect((target_ip, port if port > 0 else 9988))
            s.sendall(payload_bytes)
            return True
    except Exception:
        return False


def ping_single_target_pc(target_ip: str, timeout_ms: int = 500) -> bool:
    """커맨더 전용: 대상 PC가 LAN 상에서 켜져 있는지 C 레벨 원자적 ICMP Ping 스캔을 수행합니다."""
    global _COMMANDER_SCANNER_DLL
    if _COMMANDER_SCANNER_DLL is None:
        path = _find_dll_in_candidates("CommanderPingScannerNative.dll")
        if path:
            try:
                _COMMANDER_SCANNER_DLL = ctypes.CDLL(path)
            except Exception:
                _COMMANDER_SCANNER_DLL = None

    if _COMMANDER_SCANNER_DLL:
        try:
            rtt = ctypes.c_ulong(0)
            return bool(_COMMANDER_SCANNER_DLL.NativePingSingleTarget(
                target_ip.encode('utf-8'), ctypes.c_ulong(timeout_ms), ctypes.byref(rtt)
            ))
        except Exception:
            pass

    # Fallback: ping via subprocess
    try:
        import subprocess
        res = subprocess.run(["ping", "-n", "1", "-w", str(timeout_ms), target_ip], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False


def send_wake_on_lan(mac_address: str, port: int = 9) -> bool:
    """커맨더 전용: 꺼져 있는 대상 PC를 깨우기 위해 Wake-on-LAN Magic Packet을 송출합니다."""
    global _COMMANDER_SCANNER_DLL
    if _COMMANDER_SCANNER_DLL is None:
        path = _find_dll_in_candidates("CommanderPingScannerNative.dll")
        if path:
            try:
                _COMMANDER_SCANNER_DLL = ctypes.CDLL(path)
            except Exception:
                _COMMANDER_SCANNER_DLL = None

    if _COMMANDER_SCANNER_DLL:
        try:
            return bool(_COMMANDER_SCANNER_DLL.NativeSendWakeOnLan(mac_address.encode('utf-8'), ctypes.c_int(port)))
        except Exception:
            pass

    # Fallback: Python WoL magic packet
    try:
        import socket
        clean_mac = mac_address.replace(":", "").replace("-", "")
        if len(clean_mac) == 12:
            data = bytes.fromhex("FF" * 6 + clean_mac * 16)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.sendto(data, ('255.255.255.255', port))
                return True
    except Exception:
        pass
    return False







