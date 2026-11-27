# PowerController 12대 순수 창작 DLL 명세서 (DLL C ABI Specification)

**버전**: v2.9.2  
**갱신 일자**: 2026-11-26  

---

## 📌 문서 개요
본 문서는 PowerController Suite의 저수준 Windows OS 제어, 암호화, 방화벽 COM 제어, 50~500대 LAN 관제 및 직접 전원 실행을 담당하는 **12대 순수 창작 네이티브 DLL**의 C ABI 익스포트 함수, 파라미터 규격, 반환값, 그리고 `native_bridge.py` 파이썬 바인딩 인터페이스를 정의합니다.

---

## 📜 C ABI 함수 명세 (12대 Pure Custom DLLs)

### [A] `PowerCoreNative.dll` (`native/power_core_native.c`)
하드웨어 RTC 웨이크업, 절전 방지 및 무음 프로세스 트리 제어 엔진

* `BOOL NativeIsHardwareWakeSupported(void)`: ACPI 웨이크업 타이머 생성 가능 여부 반환 (`TRUE`/`FALSE`).
* `BOOL NativeSetHardwareWakeTimer(double seconds)`: `CreateWaitableTimerW` + `SetWaitableTimer(..., fResume=TRUE)`로 절전(S3) 중에도 PC를 깨우는 하드웨어 타이머 등록 (`seconds` 최대 10년 클램핑).
* `BOOL NativeCancelHardwareWakeTimer(void)`: 활성화된 하드웨어 웨이크업 타이머 취소 및 핸들 해제.
* `BOOL NativeSetSleepPrevention(int prevent_sleep, int keep_display)`: `SetThreadExecutionState` 기반 시스템/화면 절전 진입 차단 및 복구.
* `int NativeKillProcessTree(unsigned long root_pid)`: `CreateToolhelp32Snapshot` 단일 스냅샷 + 동적 확장(`realloc` 최대 16,384노드) + 사이클 가드 기반 하위 프로세스 트리 무음 강제 종료.
* `int NativeKillProcessByName(const wchar_t* process_name)`: 실행 파일명 일치 프로세스 일괄 무음 종료(자기 자신 PID 보호).

---

### [B] `NetBeaconEngine.dll` (`native/net_beacon_engine.c`)
Winsock2 비동기 UDP 비콘(Port 9985/9986) 리스너 및 512슬롯 FIFO 링버퍼 엔진

* `BOOL NativeStartBeaconListener(int port)`: 지정 포트(`1..65535`)로 백그라운드 UDP 리스너 스레드 가동 (`g_hBindEvent` 동기화 바인딩 검증).
* `BOOL NativeStopBeaconListener(void)`: 리스너 스레드 종료 및 소켓 자원 회수.
* `int NativeGetBeaconQueueCount(void)`: 512슬롯 링버퍼 내 대기 중인 패킷 수 반환.
* `int NativeGetNextBeaconPacket(char* out_ip, int max_ip_len, int* out_port, char* out_data, int max_data_len)`: 가장 오래된 수신 비콘 패킷 1건을 원자적으로 인출(성공 `1`, 큐 비어있음 `0`).
* `BOOL NativeSendBroadcast(int port, const char* data, int data_len)`: LAN 브로드캐스트(`255.255.255.255`) 및 로컬 루프백(`127.0.0.1`) 동시 UDP 송출.
* `BOOL NativeSendDirect(const char* ip, int port, const char* data, int data_len)`: `inet_pton` 검증된 대상 IP로 유니캐스트 UDP 패킷 송출.

---

### [C] `FirewallNative.dll` (`native/firewall_native.cpp`)
Windows Defender Firewall `INetFwPolicy2` / `INetFwRules` COM 직결 제어기 (per-call `ScopedComInit` RAII)

* `int NativeBatchRegisterSuite(const wchar_t* target_dir, const wchar_t* version_str)`: `PowerController.exe`, `PowerNetworkScheduler.exe` 인/아웃바운드 및 TCP 9988, UDP 9985/9986, 버전 표기 규칙을 0.05초 내 일괄 등록(등록 규칙 수 반환, 실패 시 `-1`).
* `int NativeBatchRemoveSuite(const wchar_t* version_str)`: 등록된 PowerController Suite 방화벽 규칙 일괄 삭제.
* `BOOL NativeAddApplicationRule(const wchar_t* rule_name, const wchar_t* exe_path, int direction)`: 단일 실행 파일 허용 규칙 추가 (`direction`: `1`=Inbound, `2`=Outbound).
* `BOOL NativeAddPortRule(const wchar_t* rule_name, int protocol, const wchar_t* port_str, int direction)`: 단일 포트 허용 규칙 추가 (`protocol`: `6`=TCP, `17`=UDP).
* `BOOL NativeDeleteRule(const wchar_t* rule_name)`: 명칭 기반 방화벽 규칙 삭제.
* `BOOL NativeIsFirewallRulePresent(const wchar_t* rule_name)`: 규칙 등록 여부 즉시 확인.

---

### [D] `SysPowerHook.dll` (`native/sys_power_hook.c`)
Windows 세션 변경 알림 훅, 하드웨어 배터리 감시 및 비차단 전원 액션 트리거

* `BOOL NativeStartSessionHook(void)`: `HWND_MESSAGE` + `WTSRegisterSessionNotification` 백그라운드 세션 감시 스레드 시작.
* `BOOL NativeStopSessionHook(void)`: 세션 훅 해제 및 스레드 안전 종료.
* `int NativeGetLastSessionEvent(void)`: 마지막 수신 세션 이벤트 코드 (`7`: `WTS_SESSION_LOCK`, `8`: `WTS_SESSION_UNLOCK`).
* `int NativeGetNextSessionEvent(int* out_event_type, int* out_session_id)`: 64슬롯 큐에서 세션 이벤트 인출 (`1`/`0`).
* `BOOL NativeIsSessionLocked(void)`: 현재 사용자 세션 잠금 상태 여부.
* `BOOL NativeGetBatteryStatus(int* out_ac_status, int* out_battery_flag, int* out_percent, int* out_life_time)`: `GetSystemPowerStatus` 실시간 조회.
* `BOOL NativeIsOnBatteryPower(void)` / `int NativeGetBatteryPercent(void)` / `BOOL NativeIsBatteryCritical(int threshold_percent)`: 배터리 상태/잔량/위험 임계치 판정.
* `BOOL NativeLockWorkStation(void)`: `LockWorkStation()` 네이티브 즉시 호출.
* `BOOL NativeTurnOffMonitor(void)`: `SendMessageTimeoutW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2, SMTO_ABORTIFHUNG | SMTO_BLOCK, 500, ...)` 비차단 모니터 절전 전환.

---

### [E] `ScheduleCrypto.dll` (`native/schedule_crypto.c`)
외부 의존성 없는 순수 C99 SHA-256, HMAC-SHA256, CSPRNG 암호화 봉투 엔진

* `BOOL NativeComputeSHA256(const unsigned char* data, int data_len, char* out_hex, int max_hex_len)`: SHA-256 64자리 16진수 계산.
* `BOOL NativeGenerateHMAC(const char* data, const char* key, char* out_hmac_hex, int max_len)`: HMAC-SHA256 전자 서명 생성.
* `BOOL NativeVerifyScheduleSignature(const char* json_data, const char* signature_hex, const char* master_key)`: `constant_time_compare()` 기반 타이밍 공격 방어 서명 검증.
* `int NativeEncryptSchedule(const char* plaintext, const char* master_key, char* out_b64, int max_out_len)`: `RtlGenRandom` CSPRNG 16바이트 Salt + 32바이트 HMAC + XOR-Sponge 암호문을 Base64 봉투로 출력(바이트 길이 반환, 오류 시 음수).
* `int NativeDecryptSchedule(const char* in_b64, const char* master_key, char* out_plaintext, int max_out_len)`: Base64 디코드 및 상수 시간 HMAC 무결성 검증 후 평문 복원(위변조 시 `-2` 반환).

---

### [F] `DiskFlushNative.dll` (`native/disk_flush_native.c`)
시스템 전원 차단 직전 파일시스템 버퍼 및 레지스트리 하이브 물리 동기화 엔진

* `BOOL NativeFlushSingleDrive(wchar_t drive_letter)`: 지정 논리 드라이브(예: `L'C'`) raw 볼륨 캐시 플러시.
* `BOOL NativeFlushFilePath(const wchar_t* file_path)`: 비관리자 환경에서도 특정 설정 파일 핸들의 버퍼를 물리 디스크로 커밋.
* `int NativeFlushAllVolumes(void)`: 고정/이동식/RAM 드라이브 전체 `FlushFileBuffers` 실행(성공 볼륨 수 반환).
* `BOOL NativePreShutdownSync(void)`: `RegFlushKey(HKEY_CURRENT_USER / HKEY_LOCAL_MACHINE)` + `NativeFlushAllVolumes()` 일괄 실행.

---

### [G] `AudioDimmerNative.dll` (`native/audio_dimmer_native.cpp`)
Windows Core Audio (`IMMDeviceEnumerator`, `IAudioEndpointVolume`) 직결 음량 페이드/음소거 엔진

* `float NativeGetMasterVolume(void)`: 현재 기본 출력 장치 마스터 볼륨 스칼라(`0.0~1.0`, 실패 시 `-1.0`).
* `BOOL NativeSetMasterVolume(float level_scalar)`: 즉시 볼륨 설정(`0.0~1.0` 클램핑).
* `BOOL NativeSetMasterMute(BOOL mute)`: 즉시 음소거/해제 토글.
* `BOOL NativeFadeMasterVolume(float target_scalar, int fade_ms)`: 단일 엔드포인트 COM 재사용 + `QueryPerformanceCounter` 기반 코사인 커브 부드러운 페이드 전환.

---

### [H] `DisplayDdcNative.dll` (`native/display_ddc_native.cpp`)
Dxva2.dll VESA DDC/CI 물리 모니터 백라이트 밝기 제어기

* `int NativeSetHardwareBrightness(int brightness_percent)`: 연결된 모든 물리 모니터의 VESA min/max 범위에 맞추어 백라이트 밝기(`0~100%`) 설정(성공 모니터 수 반환).
* `int NativeGetHardwareBrightness(void)`: 첫 번째 물리 모니터의 현재 하드웨어 밝기(`0~100%`, 미지원 시 `-1`) 조회.

---

### [I] `LowLevelInputIdleNative.dll` (`native/low_level_input_idle_native.c`)
Win32 `GetLastInputInfo` 기반 32비트 롤오버 안전 유휴 시간 측정기

* `DWORD NativeGetSystemIdleMilliseconds(void)`: `(DWORD)(GetTickCount() - lii.dwTime)` 모듈로 감산으로 49.7일 오버플로우 오차 없는 유휴 밀리초 반환.
* `double NativeGetSystemIdleSeconds(void)`: 경과 유휴 시간(초) 반환.
* `BOOL NativeIsSystemIdleFor(double target_seconds)`: 지정 유휴 기준 초과 여부 판별.

---

### [J] `CommanderTcpDispatcherNative.dll` (`native/commander_tcp_dispatcher.cpp`)
커맨더 전용 논블로킹 Winsock2 TCP/UDP 페이로드 및 ACK 송수신 엔진

* `int NativeSendRuleCommandWithAck(const char* ip, int port, const char* payload, int payload_len, int timeout_ms, char* out_ack_buf, int max_ack_len)`: `FIONBIO` + `select()` 정밀 타임아웃으로 TCP 연결/전송 및 JSON ACK 수신(수신 바이트 수 `>= 0`, 오류/타임아웃 `-1`).
* `BOOL NativeSendSingleRuleCommand(const char* ip, int port, const char* payload, int payload_len)`: 기본 `1500ms` 타임아웃 단일 대상 송신.
* `BOOL NativeBroadcastCommandFast(int port, const char* payload, int payload_len)`: LAN UDP 브로드캐스트 초고속 송출.

---

### [K] `CommanderPingScannerNative.dll` (`native/commander_ping_scanner.c`)
커맨더 전용 32스레드 병렬 ICMP Echo + `SendARP` 스캐너 및 Wake-on-LAN 송출기

* `BOOL NativePingSingleTarget(const char* ip_str, DWORD timeout_ms, DWORD* out_rtt_ms)`: `IcmpSendEcho` 단일 IP 생존 및 RTT(ms) 측정.
* `BOOL NativeSendArpProbe(const char* ip_str, char* out_mac_str, int max_mac_len)`: `SendARP`로 L2 MAC 주소(`XX:XX:XX:XX:XX:XX`) 즉시 조회.
* `int NativeBatchScanLanTargets(TargetPcStatus* entries, int count, DWORD timeout_ms)`: 최대 32개 Win32 워커 스레드로 `entries[]` 배열(`ip`, `is_online`, `round_trip_ms`, `mac_address`)을 병렬 스캔(온라인 호스트 수 반환).
* `BOOL NativeSendWakeOnLanEx(const char* mac_hex_str, const char* broadcast_ip, int port)`: 전역 브로드캐스트 + 지정 서브넷 브로드캐스트로 102바이트 WoL 매직 패킷 송출.
* `BOOL NativeSendWakeOnLan(const char* mac_hex_str, int port)`: 기본 WoL 매직 패킷 브로드캐스트 송출.

---

### [L] `PowerExecNative.dll` (`native/power_exec_native.c`) *(신규)*
Win32 토큰 특권(`SE_SHUTDOWN_NAME`) 획득 및 서브프로세스 없는 OS 전원 실행 엔진

* `BOOL NativeEnableShutdownPrivilege(void)`: `OpenProcessToken` + `AdjustTokenPrivileges(SE_SHUTDOWN_NAME)` + `GetLastError() == ERROR_SUCCESS` 엄격 검증.
* `BOOL NativeCheckPowerCapabilities(int* out_can_suspend, int* out_can_hibernate, int* out_has_shutdown_priv)`: ACPI S3/S4 지원 여부 및 종료 특권 보유 여부 조회.
* `BOOL NativeExecuteSystemShutdown(BOOL reboot, BOOL force, DWORD timeout_sec, const wchar_t* reason)`: `InitiateSystemShutdownExW` (실패 시 `ExitWindowsEx` 폴백) 기반 OS 종료/재시작.
* `BOOL NativeExecuteSuspendState(BOOL hibernate, BOOL force_critical)`: 정식 C ABI `SetSuspendState(hibernate, force_critical, FALSE)` 호출로 `rundll32` 스택 손상 없이 절전(S3)/최대 절전(S4) 진입(RTC 웨이크업 타이머 활성 유지).
* `BOOL NativeExecuteLogoff(BOOL force)`: `ExitWindowsEx(EWX_LOGOFF | ...)` 기반 로그아웃.
* `BOOL NativeAbortSystemShutdown(void)`: 진행 중인 `InitiateSystemShutdownExW` 카운트다운 즉시 취소.

---

## 🐍 파이썬 통합 브리지 (`native_bridge.py`)

```python
import native_bridge

# 1. 12대 DLL 런타임 로드 현황 진단
status_map = native_bridge.get_native_modules_status()

# 2. 종료/절전 직전 디스크 & 레지스트리 물리 동기화 + 네이티브 OS 전원 실행
native_bridge.pre_shutdown_sync()
native_bridge.execute_system_shutdown(reboot=False, force=True, timeout_sec=2)
native_bridge.execute_suspend_state(hibernate=False, force_critical=True)
native_bridge.execute_logoff(force=True)

# 3. 컴퓨터실 50~254대 C 스레드풀 일괄 ICMP/ARP 스캔 및 논블로킹 TCP ACK 전송
scan_map = native_bridge.batch_scan_lan_targets(["192.168.0.10", "192.168.0.11"], timeout_ms=280)
ack_bytes = native_bridge.send_payload_with_ack("192.168.0.10", 9988, b'{"action":"query_status"}', timeout_ms=900)
mac = native_bridge.resolve_mac_via_arp("192.168.0.10")

# 4. 방화벽 COM 일괄 등록 / 유휴 감시 / 디스플레이 DDC / 오디오 페이드
native_bridge.batch_register_firewall_suite("C:\\Program Files\\PowerController", "2.9.2")
idle_sec = native_bridge.get_system_idle_seconds()
native_bridge.set_hardware_brightness(25)
native_bridge.fade_master_volume_sync(0.0, 500)
```

---

## 🛠️ 12대 DLL 수동 컴파일 명령 (MinGW-w64)

```cmd
gcc -O2 -shared -o PowerCoreNative.dll            native/power_core_native.c           -lkernel32 -luser32
gcc -O2 -shared -o NetBeaconEngine.dll            native/net_beacon_engine.c           -lkernel32 -luser32 -lws2_32
g++ -O2 -shared -o FirewallNative.dll             native/firewall_native.cpp           -lole32 -loleaut32
gcc -O2 -shared -o SysPowerHook.dll               native/sys_power_hook.c              -lkernel32 -luser32 -lwtsapi32
gcc -O2 -shared -o ScheduleCrypto.dll             native/schedule_crypto.c             -lkernel32 -ladvapi32
gcc -O2 -shared -o DiskFlushNative.dll            native/disk_flush_native.c           -lkernel32 -ladvapi32
g++ -O2 -shared -o AudioDimmerNative.dll          native/audio_dimmer_native.cpp       -lkernel32 -lole32
g++ -O2 -shared -o DisplayDdcNative.dll           native/display_ddc_native.cpp        -lkernel32 -luser32 -ldxva2
gcc -O2 -shared -o LowLevelInputIdleNative.dll    native/low_level_input_idle_native.c -lkernel32 -luser32
g++ -O2 -shared -o CommanderTcpDispatcherNative.dll native/commander_tcp_dispatcher.cpp -lkernel32 -lws2_32
gcc -O2 -shared -o CommanderPingScannerNative.dll native/commander_ping_scanner.c      -lkernel32 -lws2_32 -liphlpapi
gcc -O2 -shared -o PowerExecNative.dll            native/power_exec_native.c           -lkernel32 -luser32 -ladvapi32 -lpowrprof
```
> 루트 `build.bat` 또는 `python scripts/build_packages.py` 실행 시 시스템에 설치된 `gcc`/`clang`/`cl`을 자동 감지하여 12대 DLL 전체를 빌드·복사한 뒤 `PowerController.iss` 인스톨러에 번들링합니다.
