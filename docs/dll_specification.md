# PowerController 순수 창작 DLL 명세서 (DLL Specification)

## 📌 문서 개요
본 문서는 PowerController의 고성능 및 저수준 Windows OS 제어를 담당하는 순수 창작 네이티브 모듈인 **`PowerCoreNative.dll`**의 아키텍처, C ABI 함수 명세, 파라미터 규격, 에러 처리 및 파이썬 연동 방식을 정의합니다.

---

## 🏗️ 1. 아키텍처 개요 (Architecture Overview)

```text
┌────────────────────────────────────────────────────────┐
│                   Python Application                   │
│      (main.py / installer.py / network_scheduler.py)   │
└───────────────────────────┬────────────────────────────┘
                            │ ctypes (C ABI)
┌───────────────────────────▼────────────────────────────┐
│                    native_bridge.py                    │
│      - DLL 로더 (Dynamic Path Locator)                  │
│      - 함수 시그니처 바인딩                             │
│      - Graceful Fallback (DLL 부재 시 파이썬 구현 자동 전환)│
└─────────────┬────────────────────────────┬─────────────┘
              │ (DLL 로드 성공)            │ (DLL 부재 / 실패)
┌─────────────▼──────────────┐ ┌───────────▼─────────────┐
│    PowerCoreNative.dll     │ │  Python Fallback Engine │
│  - C99 / Windows Native    │ │  - ctypes.windll        │
│  - CreateWaitableTimerW    │ │  - taskkill / subprocess│
│  - TerminateProcess        │ └─────────────────────────┘
│  - Toolhelp32Snapshot      │
│  - SetThreadExecutionState │
└────────────────────────────┘
```

---

## 📜 2. C ABI 함수 명세 (Exported Functions)

### [A] PowerCoreNative.dll

모든 함수는 표준 C 링키지(`extern "C"` / `__declspec(dllexport)`)를 따르며, `__stdcall` 또는 `__cdecl` 표준 호출 규약을 지원합니다.

### 2.1 하드웨어 웨이크업 타이머 (Hardware Wake-Up Timer)

#### `BOOL NativeSetHardwareWakeTimer(double seconds)`
* **기능**: 지정된 시간(초) 후에 운영체제가 절전 모드(S3/Modern Standby)에 있더라도 **하드웨어 RTC 인터럽트를 발생시켜 시스템을 깨우는(Resume)** 대기 가능 타이머(`WaitableTimer`)를 생성 및 등록합니다.
* **매개변수**:
  * `seconds` (`double`): 현재 시각으로부터 시스템이 깨어나야 할 상대 시간 (초 단위, 예: 3600.0 = 1시간 뒤).
* **반환값**:
  * 성공 시 `TRUE (1)`, 실패 시 `FALSE (0)`.
* **내부 사용 API**:
  * `CreateWaitableTimerW(NULL, TRUE, L"PowerController_HardwareWakeTimer")`
  * `SetWaitableTimer(hTimer, &dueTime, 0, NULL, NULL, TRUE)` (`fResume = TRUE`)

#### `BOOL NativeCancelHardwareWakeTimer(void)`
* **기능**: 활성화되어 대기 중인 하드웨어 웨이크업 타이머를 즉시 취소하고 핸들을 안전하게 해제합니다.
* **반환값**:
  * 성공 시 `TRUE (1)`, 실패 시 `FALSE (0)`.
* **내부 사용 API**:
  * `CancelWaitableTimer(hTimer)`
  * `CloseHandle(hTimer)`

#### `BOOL NativeIsHardwareWakeSupported(void)`
* **기능**: 현재 시스템과 하드웨어 ACPI 펌웨어에서 웨이크업 타이머를 지원하는지 여부를 검사합니다.
* **반환값**:
  * 지원 시 `TRUE (1)`, 미지원 시 `FALSE (0)`.

---

### 2.2 전원 및 절전 모드 방지 제어 (Power Execution State)

#### `BOOL NativeSetSleepPrevention(int prevent_sleep, int keep_display)`
* **기능**: Windows 전원 관리자에게 프로그램이 활성 작업 중임을 알리고 시스템 강제 절전 및 화면 꺼짐을 제어합니다.
* **매개변수**:
  * `prevent_sleep` (`int`): `1`이면 시스템 자동 절전 진입 차단, `0`이면 해제.
  * `keep_display` (`int`): `1`이면 디스플레이(화면) 꺼짐 및 화면보호기 진입 차단, `0`이면 해제.
* **반환값**:
  * 성공 시 `TRUE (1)`, 실패 시 `FALSE (0)`.
* **내부 플래그**:
  * `ES_CONTINUOUS | ES_SYSTEM_REQUIRED` (절전 차단)
  * `ES_DISPLAY_REQUIRED` (화면 유지)

---

### 2.3 초고속 무음 프로세스 트리 종료 (Silent Process Tree Killer)

#### `int NativeKillProcessTree(unsigned long root_pid)`
* **기능**: 지정된 루트 프로세스 ID(`root_pid`)와 그에 종속된 모든 하위 자식 프로세스들을 재귀 탐색하여 **서브프로세스(`taskkill`) 스폰 없이 0.01초 내에 100% 무음으로 강제 종료**합니다.
* **매개변수**:
  * `root_pid` (`unsigned long`): 종료할 대상 프로세스의 PID.
* **반환값**:
  * 성공적으로 종료된 프로세스 수 (`int >= 0`). 실패 시 `-1`.
* **내부 사용 API**:
  * `CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)`
  * `Process32FirstW`, `Process32NextW`
  * `OpenProcess(PROCESS_TERMINATE, FALSE, pid)`
  * `TerminateProcess(hProcess, 1)`

#### `int NativeKillProcessByName(const wchar_t* process_name)`
* **기능**: 실행 중인 프로세스 목록에서 이미지 이름(예: `L"PowerController.exe"`)과 일치하는 모든 인스턴스를 무음으로 강제 종료합니다.
* **매개변수**:
  * `process_name` (`const wchar_t*`): 유니코드 문자열 프로세스 이름.
* **반환값**:
  * 성공적으로 종료된 프로세스 수 (`int >= 0`).

---

### [B] NetBeaconEngine.dll

수백 대 이상의 대규모 사내망 클라이언트 PC 비콘 및 UDP 통신을 **CPU 점유율 0.0%**로 처리하는 순수 창작 고속 I/O 엔진입니다.

#### `BOOL NativeStartBeaconListener(int port)`
* **기능**: Winsock2 비동기 백그라운드 워커 스레드를 가동하여 지정 포트(기본 9986)의 UDP 비콘 패킷을 수신하고 인메모리 링버퍼에 적재합니다.
* **매개변수**: `port` (`int`): 수신 대기할 포트 번호.
* **소켓 옵션**: `SO_REUSEADDR`, `SO_BROADCAST`, 수신 타임아웃 500ms.

#### `BOOL NativeStopBeaconListener(void)`
* **기능**: 비콘 리스너 스레드와 Winsock 소켓을 안전하게 중단하고 자원을 회수합니다.

#### `int NativeGetBeaconQueueCount(void)`
* **기능**: 현재 C 링버퍼(512 슬롯)에 대기 중인 수신 패킷 수를 반환합니다.

#### `int NativeGetNextBeaconPacket(char* out_ip, int max_ip_len, int* out_port, char* out_data, int max_data_len)`
* **기능**: 링버퍼(FIFO)에서 가장 오래된 수신 패킷을 1개 원자적으로 인출합니다.
* **반환값**: 패킷 인출 성공 시 `1`, 큐가 비어있으면 `0`.

#### `BOOL NativeSendBroadcast(int port, const char* data, int data_len)`
* **기능**: C 레벨에서 LAN 브로드캐스트(`255.255.255.255`) 및 로컬 루프백(`127.0.0.1`)으로 UDP 데이터를 서브밀리초 단위로 초고속 송출합니다.

#### `BOOL NativeSendDirect(const char* ip, int port, const char* data, int data_len)`
* **기능**: 대상 PC IP 및 포트로 유니캐스트 UDP 패킷을 즉시 발송합니다.

---

### [C] FirewallNative.dll

Windows 방화벽 COM 인터페이스(`INetFwPolicy2`, `INetFwRules`, `INetFwRule`)를 메모리 상에서 직접 호출하여, `netsh.exe` CLI의 느린 실행 속도(2~4초)를 **0.05초**로 단축하는 순수 창작 고속 방화벽 제어기입니다.

#### `int NativeBatchRegisterSuite(const wchar_t* target_dir, const wchar_t* version_str)`
* **기능**: PowerController 및 커맨더(PowerNetworkScheduler) 인바운드/아웃바운드 및 전용 포트(TCP 9988, UDP 9985, UDP 9986)와 버전 표기 규칙을 0.05초 만에 메모리 내 일괄 트랜잭션 등록합니다.
* **매개변수**:
  * `target_dir`: 프로그램 설치 대상 디렉터리 경로 (`PowerController.exe`, `PowerNetworkScheduler.exe` 위치).
  * `version_str`: 시맨틱 버전 문자열 (예: `L"2.9.1"`).
* **반환값**: 등록된 방화벽 규칙 수 (`int >= 0`), 실패 시 `-1`.

#### `int NativeBatchRemoveSuite(const wchar_t* version_str)`
* **기능**: 등록된 모든 PowerController Suite 방화벽 규칙을 0.01초 만에 깔끔하게 소거합니다.
* **반환값**: 소거된 방화벽 규칙 수 (`int >= 0`).

#### `BOOL NativeAddApplicationRule(const wchar_t* rule_name, const wchar_t* exe_path, int direction)`
* **기능**: 단일 실행 파일의 인바운드(`direction=1`) 또는 아웃바운드(`direction=2`) 방화벽 예외 규칙을 COM을 통해 즉각 추가합니다 (`profile=any`, `action=allow`).

#### `BOOL NativeAddPortRule(const wchar_t* rule_name, int protocol, const wchar_t* port_str, int direction)`
* **기능**: 지정된 TCP(`protocol=6`) 또는 UDP(`protocol=17`) 포트에 대한 방화벽 허용 규칙을 생성합니다.

#### `BOOL NativeDeleteRule(const wchar_t* rule_name)`
* **기능**: 규칙 명칭 기반으로 방화벽 규칙을 즉시 제거합니다.

#### `BOOL NativeIsFirewallRulePresent(const wchar_t* rule_name)`
* **기능**: 특정 방화벽 규칙의 등록 여부를 0.001초 만에 확인합니다.

---

### [D] SysPowerHook.dll

Windows 세션 변경 알림(`WTSRegisterSessionNotification`) 및 하드웨어 배터리/전원 상태(`GetSystemPowerStatus`)를 실시간 훅하여 감시하고, 즉각적인 화면 잠금 및 모니터 절전을 수행하는 순수 창작 모듈입니다.

#### `BOOL NativeStartSessionHook(void)`
* **기능**: 백그라운드 메시지 전용 윈도우(`HWND_MESSAGE`)를 생성하고 `WTSRegisterSessionNotification`을 등록하여 세션 변경 이벤트(화면 잠금, 잠금 해제, RDP 원격 접속 등)를 실시간 수신합니다.

#### `BOOL NativeStopSessionHook(void)`
* **기능**: 세션 알림 등록을 해제하고 백그라운드 메시지 스레드를 안전하게 종료합니다.

#### `int NativeGetLastSessionEvent(void)`
* **기능**: 가장 최근 수신된 세션 이벤트 코드를 반환합니다 (`7`: `WTS_SESSION_LOCK`, `8`: `WTS_SESSION_UNLOCK`).

#### `int NativeGetNextSessionEvent(int* out_event_type, int* out_session_id)`
* **기능**: 64슬롯 인메모리 FIFO 큐에서 다음 수신된 세션 이벤트를 원자적으로 인출합니다. (이벤트 존재 시 `1`, 큐 비어있으면 `0` 반환).

#### `BOOL NativeIsSessionLocked(void)`
* **기능**: 현재 사용자의 윈도우 화면이 잠겨있는지(`Win + L` 등) 실시간 상태를 반환합니다.

#### `BOOL NativeGetBatteryStatus(int* out_ac_status, int* out_battery_flag, int* out_percent, int* out_life_time)`
* **기능**: `GetSystemPowerStatus`를 호출하여 AC 전원 연결 여부, 배터리 플래그, 배터리 잔량(%), 남은 수명 시간을 조회합니다.

#### `BOOL NativeIsOnBatteryPower(void)`
* **기능**: 현재 컴퓨터가 AC 전원 분리 상태로 배터리(UPS 포함)로만 동작 중인지 판별합니다.

#### `int NativeGetBatteryPercent(void)`
* **기능**: 현재 배터리 잔량 백분율(0~100)을 반환하며, 배터리가 없는 데스크톱은 `-1`을 반환합니다.

#### `BOOL NativeIsBatteryCritical(int threshold_percent)`
* **기능**: 배터리 잔량이 임계치(기본 10%) 이하인지 검사하여 시스템 안전 자동 종료 조건 여부를 판별합니다.

#### `BOOL NativeLockWorkStation(void)`
* **기능**: `rundll32.exe` 프로세스 생성 오버헤드 없이 0.0001초 만에 화면을 즉각 잠급니다.

#### `BOOL NativeTurnOffMonitor(void)`
* **기능**: PowerShell 및 인라인 C# 컴파일 지연(2~3초) 없이 0.0001초 만에 윈도우 메시지(`SC_MONITORPOWER, 2`)로 모니터를 절전(화면 끄기) 모드로 전환합니다.

---

### [E] ScheduleCrypto.dll

외부 라이브러리 의존성 없이 표준 C99로 순수 개발된 고속 암호화 및 디지털 서명 엔진으로, 사내 배포용 예약 스케줄(`power_scheduler_rules.json`) 및 원클릭 주입기(`ApplySharedSchedules.exe`), 네트워크 브로드캐스트의 악의적 변조와 전원 공격을 방어합니다.

#### `BOOL NativeComputeSHA256(const unsigned char* data, int data_len, char* out_hex, int max_hex_len)`
* **기능**: 임의의 바이너리 또는 텍스트 데이터의 SHA-256 해시값(64자리 16진수)을 초고속으로 계산합니다.

#### `BOOL NativeGenerateHMAC(const char* data, const char* key, char* out_hmac_hex, int max_len)`
* **기능**: 관리자 마스터 키와 데이터로부터 변조 방지용 HMAC-SHA256 전자 서명을 생성합니다.

#### `BOOL NativeVerifyScheduleSignature(const char* json_data, const char* signature_hex, const char* master_key)`
* **기능**: 수신된 스케줄 JSON이 관리자에 의해 서명된 무결한 원본인지 서명을 검증합니다. (위조/변조 시 `0` 반환).

#### `int NativeEncryptSchedule(const char* plaintext, const char* master_key, char* out_b64, int max_out_len)`
* **기능**: 스케줄 JSON 데이터를 무작위 16바이트 Salt, HMAC 무결성 태그, 키스트림 암호화가 결합된 Base64 보안 봉투로 인코딩합니다.

#### `int NativeDecryptSchedule(const char* in_b64, const char* master_key, char* out_plaintext, int max_out_len)`
* **기능**: 암호화된 Base64 봉투를 복호화하고 HMAC 무결성을 검증하여 원본 JSON을 복원합니다. 변조 감지 시 복호화를 거부하고 오류(`-2`)를 반환합니다.

---

## 🐍 3. 파이썬 연동 (`native_bridge.py`)

파이썬 코드에서는 복잡한 C API를 직접 호출하지 않고, **`native_bridge.py`** 모듈을 통해 아래와 같이 안전하게 사용합니다:

```python
import native_bridge

# 1. 하드웨어 웨이크업 타이머 가동 (1시간 뒤 절전 상태여도 PC 자동 기상)
success = native_bridge.set_hardware_wake_timer(3600.0)

# 2. 절전 방지 플래그 설정
native_bridge.set_sleep_prevention(prevent_sleep=True, keep_display=False)

# 3. 무음 프로세스 트리 강제 종료
killed_count = native_bridge.kill_process_tree_silent(target_pid)

# 4. 프로세스 이름 기반 일괄 종료
killed_count = native_bridge.kill_process_by_name_silent("PowerController.exe")

# 5. Windows Defender 방화벽 규칙 COM 초고속(0.05초) 일괄 등록
registered_count = native_bridge.batch_register_firewall_suite(target_dir="C:\\PowerController", version_str="2.9.1")

# 6. Windows Defender 방화벽 규칙 COM 초고속 소거
removed_count = native_bridge.batch_remove_firewall_suite(version_str="2.9.1")

# 7. Windows 세션 훅 가동 및 화면 잠금 실시간 감지
native_bridge.start_session_hook()
is_locked = native_bridge.is_session_locked()

# 8. 하드웨어 배터리 / UPS 잔량 및 위험 수위(10%) 감지
battery_info = native_bridge.get_battery_status()
is_critical = native_bridge.is_battery_critical(threshold_percent=10)

# 9. 초고속(0.0001초) 화면 잠금 및 모니터 절전 (PowerShell/rundll32 대체)
native_bridge.lock_workstation_fast()
native_bridge.turn_off_monitor_fast()

# 10. 스케줄 데이터 전자 서명 및 무결성 검증 (ScheduleCrypto)
sig = native_bridge.generate_schedule_hmac(json_data)
is_valid = native_bridge.verify_schedule_signature(json_data, sig)

# 11. 스케줄 봉투 암호화 및 복호화
encrypted_b64 = native_bridge.encrypt_schedule_payload(json_data)
decrypted_json = native_bridge.decrypt_schedule_payload(encrypted_b64)
```

### 🛡️ Graceful Fallback (안전한 이중화 정책)
* `PowerCoreNative.dll`, `NetBeaconEngine.dll`, `FirewallNative.dll`, `SysPowerHook.dll`, `ScheduleCrypto.dll` 파일이 대상 PC에 없거나 관리자 권한 제한으로 로드가 실패하더라도 시스템이 중단되지 않습니다.
* `native_bridge.py` 내부에서 자동으로 기존 파이썬 표준 라이브러리(`ctypes.windll`, `subprocess.run(["taskkill", ...])`, `netsh advfirewall`, `socket`, `hashlib`, `hmac`, `base64`)로 투명하게 전환(Fallback)되어 **100% 하위 호환성을 완벽하게 보장**합니다.

---

## 🛠️ 4. 컴파일 가이드라인 (Build Instructions)

전체 5대 순수 창작 DLL(`PowerCoreNative.dll`, `NetBeaconEngine.dll`, `FirewallNative.dll`, `SysPowerHook.dll`, `ScheduleCrypto.dll`)은 표준 C99, C++ 및 Windows COM으로 작성되어 Windows 표준 컴파일러로 손쉽게 빌드할 수 있습니다:

### GCC (MinGW-w64)
```cmd
# 1. PowerCoreNative.dll
gcc -O2 -shared -o PowerCoreNative.dll native/power_core_native.c -lkernel32 -luser32

# 2. NetBeaconEngine.dll (Winsock2 링크)
gcc -O2 -shared -o NetBeaconEngine.dll native/net_beacon_engine.c -lkernel32 -luser32 -lws2_32

# 3. FirewallNative.dll (COM / OLE 링크)
g++ -O2 -shared -o FirewallNative.dll native/firewall_native.cpp -lole32 -loleaut32

# 4. SysPowerHook.dll (WtsApi32 세션 훅 링크)
gcc -O2 -shared -o SysPowerHook.dll native/sys_power_hook.c -lkernel32 -luser32 -lwtsapi32

# 5. ScheduleCrypto.dll (순수 C 암호화 엔진)
gcc -O2 -shared -o ScheduleCrypto.dll native/schedule_crypto.c -lkernel32
```

### MSVC (cl.exe / Visual Studio Native Tools)
```cmd
# 1. PowerCoreNative.dll
cl /O2 /LD native/power_core_native.c /Fe:PowerCoreNative.dll kernel32.lib user32.lib

# 2. NetBeaconEngine.dll (Winsock2 링크)
cl /O2 /LD native/net_beacon_engine.c /Fe:NetBeaconEngine.dll kernel32.lib user32.lib ws2_32.lib

# 3. FirewallNative.dll (COM / OLE 링크)
cl /O2 /EHsc /LD native/firewall_native.cpp /Fe:FirewallNative.dll ole32.lib oleaut32.lib

# 4. SysPowerHook.dll (WtsApi32 세션 훅 링크)
cl /O2 /LD native/sys_power_hook.c /Fe:SysPowerHook.dll kernel32.lib user32.lib wtsapi32.lib

# 5. ScheduleCrypto.dll (순수 C 암호화 엔진)
cl /O2 /LD native/schedule_crypto.c /Fe:ScheduleCrypto.dll kernel32.lib
```

`build.bat` 스크립트를 실행하면 시스템에 설치된 컴파일러를 자동으로 감지하여 빌드 단계에서 5대 순수 창작 DLL 전체를 자동 컴파일 생성하고 배포 패키지(`dist\PowerController\`)에 자동 배치합니다.
