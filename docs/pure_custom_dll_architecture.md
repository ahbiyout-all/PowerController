# PowerController 12대 순수 창작 네이티브 DLL 동작원리 및 아키텍처 기술 명세서
# (Pure Custom Native DLL Architecture, Operating Principles & Audit Report)

**문서 버전**: v2.9.2  
**갱신 일자**: 2026-10-17  
**프로젝트**: PowerController Suite (`PowerController.exe`, `PowerNetworkScheduler.exe`, `ApplySharedSchedules.exe`)  
**저작권**: Copyright (c) 2026 AhBiYout. All rights reserved.

---

## 📑 목차 (Table of Contents)

1. [개요 및 순수 창작 DLL 아키텍처 철학](#1-개요-및-순수-창작-dll-아키텍처-철학)
2. [12대 순수 창작 DLL 전체 계층도](#2-12대-순수-창작-dll-전체-계층도)
3. [신규 순수 창작 DLL: `PowerExecNative.dll` 심층 동작 원리](#3-신규-순수-창작-dll-powerexecnativedll-심층-동작-원리)
4. [12대 순수 창작 DLL별 내부 동작 원리 및 핵심 알고리즘](#4-12대-순수-창작-dll별-내부-동작-원리-및-핵심-알고리즘)
5. [기존 11대 DLL & 브리지 전수 감사 · 오류 수정 · 개선 보고서](#5-기존-11대-dll--브리지-전수-감사--오류-수정--개선-보고서)
6. [C ABI 연동 및 Graceful Fallback 이중화 정책](#6-c-abi-연동-및-graceful-fallback-이중화-정책)
7. [12대 DLL 통합 빌드 · 인스톨러 패키징 매트릭스](#7-12대-dll-통합-빌드--인스톨러-패키징-매트릭스)

---

## 1. 개요 및 순수 창작 DLL 아키텍처 철학

PowerController Suite는 윈도우 단일 PC 제어(`PowerController.exe`)부터 50대~254대 컴퓨터실/사내망 원격 관제(`PowerNetworkScheduler.exe`)까지 담당하는 엔터프라이즈 전원 제어 솔루션입니다.  
기존 스크립트/CLI(`shutdown.exe`, `rundll32.exe`, `taskkill.exe`, `netsh.exe`, `arp.exe`, `ping.exe`, `PowerShell.exe`) 방식은 다음과 같은 구조적 한계를 가졌습니다.

1. **서브프로세스 스폰 지연 및 콘솔 깜빡임**: 외부 `.exe` 호출마다 100ms~3,000ms 지연 및 콘솔 창 깜빡임 발생.
2. **GIL 병목 및 블로킹 소켓 문제**: 50대 이상 컴퓨터실 동시 스캔/제어 시 Python 소켓/서브프로세스 오버헤드 누적.
3. **`rundll32.exe powrprof.dll,SetSuspendState` ABI 불일치 결함**: Win32 `SetSuspendState(BOOLEAN, BOOLEAN, BOOLEAN)` 함수는 `rundll32` 콜백 규격(`HWND, HINSTANCE, LPSTR, int`)과 다르기 때문에 스택 해석 오류로 환경에 따라 절전 대신 최대 절전(Hibernate)이 실행되거나 동작이 실패하는 고질적 문제 존재.
4. **외부 런타임/의존성 리스크**: OpenSSL, Visual C++ Redistributable 등의 외부 라이브러리 설치를 강제하면 배포 신뢰성 저하.

이를 근본적으로 해결하기 위해 PowerController는 **표준 C99 / C++ / Win32 API / Windows COM**만 사용하는 **12대 순수 창작 네이티브 DLL** 체계를 구축했습니다.

- **Zero External Dependencies**: Windows 기본 시스템 DLL(`kernel32`, `user32`, `advapi32`, `ws2_32`, `iphlpapi`, `ole32`, `oleaut32`, `wtsapi32`, `dxva2`, `powrprof`)만 동적/정적 링크.
- **Thread-Safe & Loader-Lock Safe**: `DllMain` 내부에서의 COM 초기화/네트워크 블로킹을 전면 금지하고, per-call RAII(`ScopedComInit`, `ScopedAudioCom`), `CRITICAL_SECTION`, `lpvReserved == NULL` 디태치 가드 적용.
- **Graceful Fallback 100% 보장**: 대상 PC 환경이나 권한 제약으로 특정 DLL 로드가 실패하더라도 `native_bridge.py`가 즉시 표준 Python / `ctypes.windll` / CLI 폴백 경로로 투명 전환.

---

## 2. 12대 순수 창작 DLL 전체 계층도

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│                      PowerController Suite (Python / Web / UI)                    │
│        main.py  ·  network_scheduler.py  ·  apply_shared_schedules.py  ·  setup   │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │ ctypes C ABI
┌─────────────────────────────────────────▼─────────────────────────────────────────┐
│                                 native_bridge.py                                  │
│      Dynamic Path Locator · C Signature Validation · Graceful Fallback Engine     │
└──┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬───┘
   │          │          │          │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼          ▼          ▼          ▼
[Core/OS]  [PowerExec] [Session] [DiskFlush] [IdleHook] [Firewall] [Audio/DDC] [Security]
PowerCore  PowerExec   SysPower  DiskFlush   LowLevel   Firewall   AudioDimmer Schedule
Native     Native      Hook      Native      InputIdle  Native     + DisplayDdc Crypto
   │                                                                            ▲
   └────────── [Network & Lab Fleet 50+ Commander] ─────────────────────────────┘
              NetBeaconEngine · CommanderTcpDispatcherNative · CommanderPingScannerNative
```

| # | 파일명 | 바이너리명 | 핵심 OS API / 기술 | 주요 담당 영역 |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `power_core_native.c` | `PowerCoreNative.dll` | `WaitableTimer(fResume)`, `SetThreadExecutionState`, `Toolhelp32` | 하드웨어 RTC 기상, 절전 방지, 무음 프로세스 트리 종료 |
| 2 | `net_beacon_engine.c` | `NetBeaconEngine.dll` | `Winsock2 UDP`, 512슬롯 FIFO 링버퍼 | LAN 자동 탐색 비콘 송수신 (Port 9985/9986) |
| 3 | `firewall_native.cpp` | `FirewallNative.dll` | `INetFwPolicy2`, `INetFwRules` COM + RAII | Windows 방화벽 인/아웃바운드 & 포트 규칙 0.05초 일괄 등록 |
| 4 | `sys_power_hook.c` | `SysPowerHook.dll` | `WTSRegisterSessionNotification`, `SendMessageTimeoutW`, `GetSystemPowerStatus` | 세션 잠금/해제 훅, 배터리 텔레메트리, 즉시 잠금/모니터 오프 |
| 5 | `schedule_crypto.c` | `ScheduleCrypto.dll` | 순수 C99 SHA-256 / HMAC-SHA256, `RtlGenRandom`, XOR-Sponge | 스케줄 무결성 서명, 암호화 봉투(Sealed Envelope) |
| 6 | `disk_flush_native.c` | `DiskFlushNative.dll` | `FlushFileBuffers`, `RegFlushKey`, `GetLogicalDriveStringsW` | 종료/절전 직전 NTFS/FAT 볼륨 캐시 및 레지스트리 하이브 강제 동기화 |
| 7 | `audio_dimmer_native.cpp` | `AudioDimmerNative.dll` | `IMMDeviceEnumerator`, `IAudioEndpointVolume`, QPC 타이머 | 마스터 오디오 S-커브 페이드아웃 및 음소거 |
| 8 | `display_ddc_native.cpp` | `DisplayDdcNative.dll` | `dxva2.dll` VESA DDC/CI (`Set/GetMonitorBrightness`) | 물리 모니터 하드웨어 백라이트 밝기 제어(0~100% 정규화) |
| 9 | `low_level_input_idle_native.c` | `LowLevelInputIdleNative.c` ➔ `.dll` | `GetLastInputInfo`, 32비트 모듈로 감산 | 사용자 무동작 유휴 시간(ms/sec) 정밀 측정 |
| 10 | `commander_tcp_dispatcher.cpp` | `CommanderTcpDispatcherNative.dll` | Winsock2 `FIONBIO` + `select()` + `recv()` ACK | 50~500대 PC 원격 제어 JSON 페이로드 논블로킹 송수신 |
| 11 | `commander_ping_scanner.c` | `CommanderPingScannerNative.dll` | `IcmpSendEcho`, `SendARP`, 32스레드 C 풀, WoL UDP | 컴퓨터실 50~254대 병렬 생존/MAC 스캔 및 매직 패킷 송출 |
| **12** | **`power_exec_native.c`** *(신규)* | **`PowerExecNative.dll`** | `AdjustTokenPrivileges(SE_SHUTDOWN_NAME)`, `InitiateSystemShutdownExW`, `ExitWindowsEx`, `SetSuspendState` | **서브프로세스 없는 Win32 네이티브 전원 실행/취소 엔진** |

---

## 3. 신규 순수 창작 DLL: `PowerExecNative.dll` 심층 동작 원리

### 3.1 창작 배경 및 필요성
기존 `main.py`에서는 시스템 종료, 재시작, 절전, 최대 절전, 로그아웃 수행 시 다음과 같이 외부 프로세스를 호출하고 있었습니다.
- 종료/재시작/로그아웃: `os.system("shutdown /s /f /t 2")` (콘솔 스폰 + 인수 파싱 오버헤드 + 원인 코드 기록 불가)
- 절전(Sleep): `os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")` (`rundll32`가 함수 인자를 잘못 파싱하여 S3 절전 대신 S4 최대 절전으로 진입하거나 실패하는 Windows 고질적 ABI 버그 노출)

### 3.2 내부 동작 메커니즘
1. **프로세스 토큰 권한 상승 (`NativeEnableShutdownPrivilege`)**
   - `OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &hToken)`으로 현재 프로세스 토큰 오픈.
   - `LookupPrivilegeValueW(NULL, SE_SHUTDOWN_NAME, ...)`로 종료 특권 LUID 조회.
   - `AdjustTokenPrivileges` 호출 후 **반환값(`TRUE`)뿐 아니라 `GetLastError() == ERROR_SUCCESS`까지 엄격 검증**하여 `ERROR_NOT_ALL_ASSIGNED` 오탐을 차단.
2. **하드웨어 전원 기능 사전 질의 (`NativeCheckPowerCapabilities`)**
   - `powrprof.dll`을 동적 로드(`LoadLibraryA`)하여 `IsPwrSuspendAllowed()` / `IsPwrHibernateAllowed()` 및 `SE_SHUTDOWN_NAME` 보유 여부를 한 번에 조회.
3. **네이티브 종료/재시작 (`NativeExecuteSystemShutdown`)**
   - `SHTDN_REASON_MAJOR_APPLICATION | SHTDN_REASON_MINOR_MAINTENANCE | SHTDN_REASON_FLAG_PLANNED` 이벤트 로그 사유 코드와 함께 `InitiateSystemShutdownExW`를 호출해 Windows 이벤트 뷰어에 정상 계획 종료로 기록.
   - 세션 정책상 `InitiateSystemShutdownExW`가 거부될 경우 `ExitWindowsEx(EWX_SHUTDOWN | EWX_POWEROFF | EWX_FORCE/EWX_FORCEIFHUNG)`로 2차 네이티브 폴백 수행.
4. **정식 C ABI 절전/최대 절전 (`NativeExecuteSuspendState`)**
   - `SetSuspendState(hibernate, force_critical, FALSE)`를 **정식 `__stdcall` 함수 포인터 C ABI**로 직접 호출.
   - 세 번째 인자 `DisableWakeEvent`를 명시적으로 `FALSE`로 전달하여, `PowerCoreNative.dll`이 예약해 둔 **하드웨어 RTC 웨이크업 타이머(`WaitableTimer`)가 절전 중에도 정상 작동하여 PC를 다시 깨울 수 있도록 보장**.
5. **실행 직전 디스크·레지스트리 무결성 연계 (`main.py` 통합)**
   - `execute_power_action()` 및 원격 `immediate_power` 워커가 `PowerExecNative` 호출 직전에 `DiskFlushNative.dll`의 `pre_shutdown_sync()`를 먼저 실행하여 미기록 파일시스템 버퍼 및 HKCU 설정 손실을 원천 차단.

---

## 4. 12대 순수 창작 DLL별 내부 동작 원리 및 핵심 알고리즘

1. **`PowerCoreNative.dll`**: `CreateWaitableTimerW` + `SetWaitableTimer(..., fResume=TRUE)`로 마더보드 ACPI RTC 인터럽트 기상을 예약하며, `CreateToolhelp32Snapshot` 단일 스냅샷으로 메모리 내 프로세스 트리를 구축해 BFS/DFS(사이클 가드 포함)로 `taskkill.exe` 없이 자식 프로세스까지 무음 종료합니다.
2. **`NetBeaconEngine.dll`**: 전용 워커 스레드 + `500ms SO_RCVTIMEO` 소켓으로 UDP 9986 비콘을 수신하며, 512슬롯 고정 순환 링버퍼에 원자적으로 적재합니다. `g_hBindEvent` 동기화 핸드셰이크를 통해 포트 바인딩 실패 시 즉시 `FALSE`를 반환합니다.
3. **`FirewallNative.cpp`**: `netsh.exe`를 최대 14회 이상 연속 실행하는 대신 `INetFwPolicy2::get_Rules()` COM 컬렉션에 규칙을 직접 추가/삭제합니다. 호출 스레드의 COM 아파트먼트를 훼손하지 않기 위해 함수 진입/퇴출 시 `ScopedComInit` RAII 가드를 사용합니다.
4. **`SysPowerHook.c`**: 숨겨진 메시지 전용 윈도우(`HWND_MESSAGE`)를 백그라운드 스레드 메시지 펌프로 구동해 `WM_WTSSESSION_CHANGE`(`WTS_SESSION_LOCK=7`, `UNLOCK=8`)를 실시간 수집합니다. 모니터 절전 시에는 `SendMessageTimeoutW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2, SMTO_ABORTIFHUNG | SMTO_BLOCK, 500, ...)`를 사용하여 응답 없는 창 때문에 프로그램이 멈추는 현상을 방지합니다.
5. **`ScheduleCrypto.c`**: 외부 라이브러리 없이 표준 C99로 SHA-256과 HMAC-SHA256을 구현하고, Windows `advapi32.dll`의 커널 CSPRNG(`SystemFunction036` / `RtlGenRandom`)로 16바이트 Salt를 생성합니다. 복호화 시에는 상수 시간 비교(`constant_time_compare`)로 HMAC 태그를 검증하여 타이밍 사이드채널 공격을 차단하고, 64바이트 블록 카운터 기반 키스트림 XOR 스펀지로 평문을 암·복호화합니다.
6. **`DiskFlushNative.c`**: `GetLogicalDriveStringsW`로 고정/이동식/RAM 드라이브를 열거해 볼륨 핸들(`\\.\X:`)에 `FlushFileBuffers`를 수행하고, 비관리자 권한에서도 현재 사용자 설정이 손실되지 않도록 `RegFlushKey(HKEY_CURRENT_USER)`와 개별 파일 플러시(`NativeFlushFilePath`)를 지원합니다.
7. **`AudioDimmerNative.cpp`**: `IMMDeviceEnumerator -> GetDefaultAudioEndpoint -> IAudioEndpointVolume` 파이프라인을 페이드 루프 시작 시 **1회만 획득**하고, `QueryPerformanceCounter` 실측 경과 시간 기준 코사인($0.5(1-\cos(\pi t))$) 보간 곡선으로 부드럽게 볼륨을 감쇠합니다.
8. **`DisplayDdcNative.cpp`**: `EnumDisplayMonitors`와 `dxva2.dll`의 `GetMonitorBrightness`를 함께 조회하여 모니터 제조사별 `dwMin..dwMax` 하드웨어 범위를 0~100% 스케일로 정확히 비례 환산해 `SetMonitorBrightness`를 호출합니다.
9. **`LowLevelInputIdleNative.c`**: `GetLastInputInfo`의 마지막 입력 틱(`dwTime`)과 `GetTickCount()` 차이를 부호 없는 32비트 정수 감산(`(DWORD)(currentTick - lii.dwTime)`)으로 계산해 Windows 연속 가동 **49.7일 롤오버(Wrap-around) 경계에서도 0.001초 오차 없이** 유휴 시간을 산출합니다.
10. **`CommanderTcpDispatcherNative.cpp`**: Winsock TCP `connect()`가 `SO_SNDTIMEO`를 무시해 오프라인 PC당 21초씩 멈추는 문제를 피하기 위해, `ioctlsocket(FIONBIO)` 논블로킹 전환 + `select()` + `getsockopt(SO_ERROR)`로 정확한 밀리초 타임아웃(`timeout_ms`)을 보장하며 전송 후 JSON ACK(`NativeSendRuleCommandWithAck`)까지 단일 호출로 수신합니다.
11. **`CommanderPingScannerNative.c`**: 최대 32개 Win32 워커 스레드 풀로 `entries[]` 배열을 분할하여 `IcmpSendEcho` ICMP 응답과 `SendARP` L2 MAC 주소를 병렬 수집합니다. Windows 방화벽이 ICMP Ping을 차단하더라도 동일 서브넷의 ARP 응답이 확인되면 온라인 + MAC 주소를 정확히 식별합니다.

---

## 5. 기존 11대 DLL & 브리지 전수 감사 · 오류 수정 · 개선 보고서

v2.9.2 전수 감사를 통해 기존 11개 C/C++ DLL 소스 및 `native_bridge.py`에서 발견한 메모리, 스레딩, 보안, 네트워크 결함을 모두 수정했습니다.

| 모듈 | 발견된 결함 / 위험 (Audit Finding) | 적용된 수정 및 개선 내용 |
| :--- | :--- | :--- |
| **`schedule_crypto.c`** | ① Base64 디코드 테이블 `memset(dtable, 0x80, 256)`이 `int dtable[256]`(1024바이트)의 첫 64개 원소만 초기화하여 ASCII `>= 64` 문자의 스택 쓰레기값 참조 버그 존재<br>② 미시드 `rand() % 256` 예측 가능 Salt 사용<br>③ `memcmp` HMAC 비교로 타이밍 누출 가능 및 빈 평문 `malloc(0)` 위험 | ① 256개 원소 전체를 `-1`로 초기화 + `len % 4 == 0` 검증<br>② OS CSPRNG `RtlGenRandom`(`advapi32!SystemFunction036`) + QPC/PID/TID SHA-256 엔트로피 폴백 적용<br>③ `constant_time_compare()` 도입 및 빈 평문 방어 |
| **`commander_tcp_dispatcher.cpp`** | ① 블로킹 `connect()`가 `SO_SNDTIMEO`를 무시해 최대 21초 대기하는 동안 호출 함수의 `WaitForSingleObject(2000)`이 먼저 리턴하여 워커 스레드가 해제된 스택 변수(`job`)에 쓰는 **Use-After-Return 메모리 손상 위험** 존재<br>② `inet_addr()` 비표준 처리 및 `WSACleanup()` 누락 | ① 비동기 `FIONBIO` + `connect()` + `select()` 정밀 타임아웃 동기 호출로 구조 전면 개선(스택 UAF 원천 제거)<br>② `inet_pton(AF_INET, ...)` 및 `DLL_PROCESS_DETACH` `WSACleanup()` 추가<br>③ JSON ACK 동시 수신 API `NativeSendRuleCommandWithAck` 신설 |
| **`firewall_native.cpp`** | ① `DllMain` 내부 전역 COM 초기화(Loader Lock 데드락 위험) 및 멀티스레드 호출 시 타 스레드 COM 미초기화 실패<br>② `SysAllocString` NULL 체크 누락 및 `_snwprintf` NUL 미종단 가능성 | ① `DllMain` COM 호출 제거, 호출 스레드별 RAII `ScopedComInit` 적용 (`COINIT_MULTITHREADED` + `RPC_E_CHANGED_MODE` 폴백)<br>② `SysAllocString` NULL 검사, 강제 NUL 종단, 기본 버전 `L"2.9.2"` 반영 |
| **`audio_dimmer_native.cpp`** | ① `DllMain` 전역 COM 초기화 문제<br>② `NativeFadeMasterVolume`이 150회 루프마다 `CoCreateInstance`로 엔드포인트를 재생성하여 COM 부하 및 페이드 시간 편차 발생 | ① per-call RAII `ScopedAudioCom` 전환<br>② 엔드포인트 1회 획득 재사용 + `QueryPerformanceCounter` 실측 경과 시간 코사인 곡선 페이드로 개편 |
| **`net_beacon_engine.c`** | ① `NativeSendDirect`에서 deprecated `inet_addr()` 사용 시 잘못된 IP가 `INADDR_NONE`(`255.255.255.255` 브로드캐스트)으로 오인 전송되는 버그<br>② 리스너 스레드 포트 바인드 실패 시에도 `NativeStartBeaconListener`가 `TRUE` 반환<br>③ 512 슬롯 초과 시 최신 비콘 패킷 드롭 | ① `inet_pton` 엄격 검증 및 포트 범위(`1..65535`) 체크<br>② `g_hBindEvent` 수동 리셋 이벤트로 바인드 성패 동기 검증<br>③ 링버퍼 포화 시 가장 오래된 슬롯을 덮어쓰고 최신 비콘 유지 + `WSACleanup()` 추가 |
| **`sys_power_hook.c`** | ① `NativeTurnOffMonitor`의 `SendMessage(HWND_BROADCAST, ...)`가 응답 없는 창이 하나라도 있으면 영구 블로킹(데드락)<br>② `DLL_PROCESS_DETACH` 시 `lpvReserved != NULL` 프로세스 종료 시점 스레드 대기 위험 | ① `SendMessageTimeoutW(..., SMTO_ABORTIFHUNG | SMTO_BLOCK, 500, ...)` + `SendNotifyMessageW` 폴백 적용<br>② `lpvReserved == NULL` 가드, `RegisterClassExA` 실패 처리 및 `UnregisterClassA` 정리, 64슬롯 큐 덮어쓰기 정책 적용 |
| **`power_core_native.c`** | ① 고정 크기 `allNodes[1024]` 초과 환경(다중 탭 브라우저/대형 서버)에서 프로세스 누락 및 PID 재사용 순환 트리 시 무한 재귀 가능<br>② 자기 자신 프로세스 PID 조기 종료 가능<br>③ 웨이크 타이머 `seconds` 극대값 `LONGLONG` 오버플로우 가능 | ① `realloc` 동적 확장(1024 ➔ 최대 16384개) + `visited[]` 사이클 가드 + 재귀 깊이 64 제한<br>② `GetCurrentProcessId()` 자기 자신 종료 제외<br>③ `seconds` 상한(10년) 클램핑 및 최소 `-1` 단위 보장 |
| **`display_ddc_native.cpp`** | ① 전역 `CRITICAL_SECTION` 미초기화 및 `g_hDxva2Lib` 미해제<br>② 모니터 VESA `dwMin..dwMax` 비선형 범위 무시<br>③ 명세된 `NativeGetHardwareBrightness` 미구현 | ① `EnsureDxvaCS()` + `FreeLibrary` 해제<br>② `GetMonitorBrightness` 기반 동적 범위 스케일링<br>③ `NativeGetHardwareBrightness()` 정식 구현 |
| **`disk_flush_native.c`** | ① 비관리자 환경에서 전체 볼륨 핸들 열기 실패 시 부분 성공 판단 오류 (`flushed > 0`만 검사)<br>② 단일 드라이브/단일 파일 플러시 부재 | ① `NativeFlushSingleDrive`, `NativeFlushFilePath` 추가<br>② `NativePreShutdownSync`가 `HKCU` 레지스트리 플러시 성공도 반영하도록 개선 |
| **`low_level_input_idle_native.c`** | ① `currentTick >= dwTime` 분기 시 49.7일 롤오버 경계에서 `1ms` 오차(`0xFFFFFFFF - dwTime + currentTick`) | ① C 표준 부호 없는 32비트 감산 `(DWORD)(currentTick - lii.dwTime)` 단일식으로 1ms 오차 제거 |
| **`commander_ping_scanner.c`** | ① `NativeSendWakeOnLan` 단독 호출 시 `WSAStartup` 미호출로 인한 `WSANOTINITIALISED (10093)` 실패 버그<br>② C 레벨 다중 PC 일괄 스캔 API 부재 | ① 스레드 안전 `EnsureScanWsa()` + `WSACleanup()` 추가<br>② `NativeSendWakeOnLanEx`(서브넷 브로드캐스트 병행) 및 32스레드 C 풀 `NativeBatchScanLanTargets` 신설 |
| **`native_bridge.py` & 앱 통합** | ① `lock_workstation_fast()` 예외 블록 내 `import os`로 인해 `UnboundLocalError` 발생 잠재 버그<br>② 6개 신규 DLL 및 `PowerExecNative`가 `main.py`, `network_scheduler.py`, `build.bat`, `.iss`, `build_packages.py`에 부분 누락 | ① `import os` 섀도잉 제거 및 전 12개 DLL C ABI 바인딩 완성<br>② `main.py`·`network_scheduler.py`·`installer.py`·`build.bat`·`PowerController.iss`·`build_packages.py`·`scriptGenerators.ts` 전면 통합 |

---

## 6. C ABI 연동 및 Graceful Fallback 이중화 정책

1. **`native_bridge.py` 탐색 우선순위**
   - PyInstaller 실행 디렉터리(`sys.executable` / `_MEIPASS`) ➔ 스크립트 루트 ➔ `native/` ➔ `dist/PowerController/` ➔ `%LOCALAPPDATA%\PowerController` ➔ `%APPDATA%\PowerController` 순서로 DLL 탐색.
2. **상태 자가 진단 (`native_bridge.get_native_modules_status()`)**
   - 런타임에서 12대 DLL 각각의 실제 로드 여부를 `{ "PowerExecNative.dll": True, ... }` 딕셔너리로 즉시 점검 가능.
3. **무중단 이중화 (Graceful Fallback)**
   - 예: Linux 테스트 환경이거나 Windows에서 특정 DLL 파일이 누락된 경우에도 `main.py`와 `network_scheduler.py`는 예외를 삼키고 즉시 Python 소켓 / `ctypes.windll` / CLI 폴백 경로로 작동하여 서비스 중단을 0%로 유지합니다.

---

## 7. 12대 DLL 통합 빌드 · 인스톨러 패키징 매트릭스

| 컴파일 방식 | 실행 스크립트 | 산출 위치 |
| :--- | :--- | :--- |
| **원클릭 통합 빌드 (Windows)** | `build.bat` | 루트, `dist\`, `dist\PowerController\` (12개 DLL 자동 빌드 & 복사) |
| **CI/CD 패키지 빌더 (Python)** | `python scripts/build_packages.py` | 12개 DLL + 3종 EXE + `PowerController_Setup_v2.9.2.exe` |
| **설치 마법사 (Inno Setup 6)** | `PowerController.iss` | `{app}\*.dll` (12개 DLL 전체 Unpacked Multi-File 배포) |

> **참고**: 상세 C ABI 시그니처와 개별 파라미터 규격은 [`docs/dll_specification.md`](./dll_specification.md)를 참조하십시오.
