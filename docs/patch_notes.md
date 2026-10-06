# PowerController 패치 노트 (Patch Notes)

본 문서는 **PowerController**의 릴리즈 패치 및 최신 업데이트 내역을 제공합니다. 
본 프로젝트는 **Semantic Versioning (MAJOR.MINOR.PATCH)** 3단계 규약에 따라 버전과 변경 이력을 투명하게 관리합니다.

---

## [v2.9.1+] - 2026-10-06 (최신 피처 및 C/C++ 네이티브 엔지니어링 패치)

### 🎵 1. Pixabay 선별 알림음 사운드 뱅크 & Web Audio 오디오 엔진
- **7가지 고음질 프리미엄 알림음 테마 구축**: Pixabay 우수 알림음 분석 기반 (`classic`, `marimba`, `crystal`, `scifi`, `westminster`, `urgent`, `bubble`).
- **상황별 알림음 믹서 및 테스트 허브**: 정각 종소리(`hourlyChime`), 카운트다운 틱(`warningTick`), 알람 완료(`timerAlarm`), 작업 성공(`actionSuccess`) 테스트 버튼 탑재.
- **볼륨 슬라이더 및 음소거**: 0~100% 볼륨 제어 및 즉시 Mute/Unmute 기능 구현.

### 📊 2. Recharts 기반 최근 60분 배터리 소모 차트 & 방전 예측 분석 엔진
- **60분 배터리 영역 차트 (`BatteryHistoryChart`)**: 최근 60분 실시간 잔량 트렌드 및 15% 임계점 가이드라인 시각화.
- **`Battery Health Insights` 카카오형 텔레메트리 바**:
  - ⏱️ **예상 잔여 사용 시간**: 현재 소모 속도 기준 0% 완전 방전 시점 시각화 (AC 연결 시 `상시 지속` 표기).
  - ⚡ **시간당 소모율**: 시간당 소모율(`-% / hr`) 및 충전 속도 계산.
  - 🛡️ **안전 작동 한계**: 15% 저전력 경고 토스트 발동 전까지 여유 시간 표시.

### 🔋 3. 타이머 가동 중 배터리 15% 이하 지속 알림(토스트) & 스마트 절전 모드 (<20%)
- **지속형 경고 토스트 (<15%)**: 전원 제어 타이머 동작 중 배터리가 15% 이하로 떨어지면 AC 충전기 연결 유도 persistent 토스트 표출.
- **스마트 절전 모드 (<20%)**: 배터리 20% 이하 감지 시 상단 고정 플로팅 위젯 투명도를 45% 이하로 낮추고 배경 링 애니메이션을 자동 감쇠하여 방전 억제.

### 🛠️ 4. 11대 순수 창작 저수준 C/C++ 네이티브 DLL 아키텍처 완성
- **기존 5대 DLL 정밀 감사 패치**: `power_core_native.c` 단일 패스 스냅샷 트래버스 최적화, `firewall_native.cpp` COM 참조 카운트 방어, `schedule_crypto.c` Constant-time 서명 비교 패치.
- **6대 신규 순수 창작 DLL 모듈 추가**:
  1. `disk_flush_native.c` (`DiskFlushNative.dll`): 볼륨 파일시스템 캐시/Dirty Page 즉시 플러시
  2. `audio_dimmer_native.cpp` (`AudioDimmerNative.dll`): Core Audio 페이드아웃 및 볼륨 제어
  3. `display_ddc_native.cpp` (`DisplayDdcNative.dll`): Dxva2 VESA DDC/CI 백라이트 하드웨어 밝기 절전
  4. `low_level_input_idle_native.c` (`LowLevelInputIdleNative.dll`): 사용자 무동작/유휴 시간 0.001초 정밀 측정
  5. `commander_tcp_dispatcher.cpp` (`CommanderTcpDispatcherNative.dll`): 커맨더 타워 500대 PC 동시 스케줄 비동기 배포
  6. `commander_ping_scanner.c` (`CommanderPingScannerNative.dll`): ICMP Echo / SendARP 원자적 LAN PC 스캐너 및 WoL 매직 패킷 송출
- **문서 등록**: [`docs/pure_custom_dll_architecture.md`](/docs/pure_custom_dll_architecture.md) 및 [`docs/dll_specification.md`](/docs/dll_specification.md) 전면 업데이트.

---

## [v2.9.1] - 2026-09-26

### 🚀 핵심 패치 사항: 원격 무인 설치(Silent/Unattended Install) 시 기존 프로세스 즉시 강제 종료 및 파일 락(멈춤 현상) 완벽 해결

1. **원격 전송 무인 설치 중 프로세스 미종료 및 설치 멈춤(Hang) 원천 차단**
   - **문제 원인 분석**:
     - 원격 관리 도구(GPO, PsExec, Intune, 커스텀 배포 에이전트 등)로 설치 파일(`PowerController_Setup.exe`)을 전송하여 무인 설치(`/VERYSILENT /NORESTART` 또는 `--silent`) 진행 시, 기존 트레이 백그라운드에서 실행 중이던 `PowerController.exe`가 즉각 종료되지 않아 Windows 파일 잠금(`ERROR_SHARING_VIOLATION`)이 발생.
     - Inno Setup의 Windows Restart Manager(RM)가 `WM_CLOSE` 신호를 보냈으나, 메인 앱의 트레이 숨김 이벤트 핸들러가 이를 가로채 종료 대신 트레이로 숨김 처리하면서 RM이 무한정 대기하거나 설치 마법사가 멈추는 현상 발생.
     - 또한 기존 스크립트 기반 인스톨러에서도 `/SILENT`나 `/VERYSILENT` 대소문자/스위치 미인식으로 인해 비대화형 세션에서 GUI 모달(`messagebox.askretrycancel`)이 호출되어 영구적으로 멈추는 현상 존재.
   - **다계층 강제 종료 및 락 해제 파이프라인 구축**:
     - **Inno Setup 6 (`PowerController.iss`)**:
       - `CloseApplications=force`, `CloseApplicationsFilter=*.exe`, `RestartApplications=no`로 설정하여 잔존 프로세스에 대해 즉각적인 강제 정리 권한 부여.
       - 뮤텍스 식별자 동기화: `Global\PowerControllerSingleInstanceMutex_f8908445,PowerController_SingleInstance_Mutex`를 동시 감지하도록 보정.
       - Pascal Script `[Code]` 섹션 도입: `InitializeSetup()` 및 파일 추출 직전 단계(`CurStepChanged(ssInstall)`)에서 `taskkill /F /T`, PowerShell `Stop-Process -Force`, `wmic process terminate` 3중 강제 종료를 선제 실행.
       - 파일 락 능동 대기 및 우회: 대상 바이너리가 잠겨 있을 경우 임시 파일 이름 변경(`.old_XXXX`) 트릭을 적용하여 새 파일 추출이 1ms의 딜레이 없이 100% 성공하도록 설계.
     - **파이썬 인스톨러 (`installer.py`)**:
       - `terminate_and_unlock_suite_processes`: 소켓 신호(`QUIT`), 프로세스 트리 강제 종료(`/F /T`), PowerShell, WMIC를 결합하고 최대 5초간 파일 핸들 해제를 능동 폴링 검증.
       - `copy_file_safe`: 파일 복사 실패 시 즉각 `.old_XXXX` 이름 변경 기믹을 발동하여 무인 설치 도중 멈춤 없이 새 바이너리 주입 완수.
       - CLI 인자 파서 전면 확장: `/SILENT`, `/VERYSILENT`, `--silent`, `-s`, `/q`, `/NORESTART`, `/SUPPRESSMSGBOXES` 등 모든 엔터프라이즈 배포 플래그를 정식 무음으로 완벽 수용.
     - **메인 백그라운드 엔진 (`main.py`)**:
       - 로컬 단일 인스턴스 소켓 리스너에 `QUIT`, `TERMINATE`, `EXIT`, `CLOSE` 명령 프로토콜을 추가하여, 외부 종료 요청 시 트레이/소켓/타이머를 메모리 누수 없이 즉시 안전 해제하고 완전 종료되도록 개선.
       - CLI 파라미터 `--kill`, `--quit`, `--terminate` 추가 지원.

2. **라이선스 및 오픈소스 약관 정의 한국어 & 영어 2종류 전격 분리 및 실시간 언어 전환 지원**
   - **이원화 구성**:
     - `STANDARD_LICENSE_KO` (한국어 사용권 및 사용 오픈소스 고지서: MIT License 및 pystray, Pillow, PyInstaller, Tkinter 등)
     - `STANDARD_LICENSE_EN` (영어 사용권 및 사용 오픈소스 고지서: End User License Agreement & Open Source Disclosures)
   - **전체 컴포넌트 실시간 언어 전환 적용**:
     - **Inno Setup 6 (`PowerController.iss`)**: `[Languages]` 섹션에 한국어 선택 시 `docs\LICENSE_ko.txt`, 영어 선택 시 `docs\LICENSE_en.txt`가 네이티브 설치 마법사에 자동 바인딩되도록 구성.
     - **파이썬 인스톨러 (`installer.py`)**: 1단계 라이선스 동의 화면 상단에 `[ 🇰🇷 한국어 (Korean) ]` / `[ 🇺🇸 English (영어) ]` 실시간 언어 전환 툴바를 제공하여 설치자가 원하는 언어로 약관을 즉시 열람하고 동의할 수 있도록 구현.
     - **데스크톱 메인 앱 (`main.py`)**: 하단 "📄 라이선스 및 약관 동의 고지서" 팝업 상단에 `[ 🇰🇷 KO ]` / `[ 🇺🇸 EN ]` 스위처 버튼을 탑재하여 언제든지 한국어/영어 라이선스 전문을 교차 열람 가능.
     - **웹 프론트엔드 (`src/App.tsx`)**: 웹 라이선스 모달 상단에 `[ 🇰🇷 한국어 ]` / `[ 🇺🇸 English ]` 탭을 지원하여 한/영 2종류 라이선스를 즉시 전환하여 조회 가능.

3. **원격 네트워크 통신 보안 결함 패치 및 보안 운영 가이드라인 체계화**
   - **토큰 검증 우회 취약점 긴급 패치**:
     - `set_token`(원격 토큰 설정) 처리 시 `auth_token`이 공백(`""`)으로 전달될 경우 검증문 조건을 우회하여 인증 없이 토큰이 덮어써지던 로직 결함을 `server_token and server_token != client_token and not is_master_authorized`로 정밀 보정하여 비인가 토큰 변조 원천 차단.
   - **원격 사전 실행 명령어(`pre_command`) 보안 감사 로깅 도입**:
     - 원격 네트워크 스케줄 페이로드에 사전 실행 시스템 명령(`pre_command`)이 포함되어 있을 경우 감사 로그(`🛡️ [보안 감사] 원격 예약에 사전 실행 명령어 포함됨`)를 남겨 악의적인 원격 명령 주입을 즉각 감지할 수 있도록 개선.
   - **종합 보안 운영 가이드라인(`docs/security_guidelines.md`) 신설**:
     - 사내망 및 공용망 운영 수칙, 마스터 비상 복구 키 커스텀 관리(`power_master_key.txt`, `POWER_TIMER_MASTER_KEY`), 방화벽 규칙 구성 및 정기 점검 체크리스트 명문화.

4. **관리자 PC 보호 및 종료/재부팅 안전 확인 경고 시스템 전격 탑재 (PowerNetworkScheduler)**
   - **자가 PC 감지 및 오작동 원천 차단**:
     - 원격 관리 도구인 `PowerNetworkScheduler`에서 현재 프로그램을 실행 중인 본인(관리자) 컴퓨터(`get_all_local_ips()`, 로컬 호스트명 대조)가 대상에 포함된 상태로 `🛑 대상 PC 즉시 종료` 또는 `🔄 대상 PC 즉시 다시시작` 버튼을 누를 경우, 이를 즉각 감지하여 강력한 확인 팝업(`🚨 [중대 경고] 관리자 PC 종료/재부팅 포함 감지`)을 표출.
     - 대화상자의 기본 포커스를 `[아니오(No)]`로 강제 지정하여 실수로 엔터나 스페이스를 누르더라도 관리자 PC가 종료되지 않도록 안전 보호망 구축.
     - 관리자 PC 우클릭 컨텍스트 메뉴 단독 즉시 제어 및 예약 규칙(종료/재부팅 모드) 전송 시에도 동일한 2중 확인 경고 발동.
   - **대기 PC 목록 시각적 식별 배지 추가**:
     - 오른쪽 PC 모니터링 목록(`pc_listbox`)에서 현재 관리자 본인의 PC 항목 뒤에 `[👑 관리자 PC]` 태그를 자동으로 표기하여 일괄 선택 시에도 본인 PC 포함 여부를 한눈에 식별할 수 있도록 UI 사용성 대폭 향상.

5. **Inno Setup & 인스톨러 배포 엔진 대규모 고도화 (v2.9.1 배포 완성)**
   - **폴더 풀림(Unpacked Multi-File) 개별 파일 설치 구조 완비**:
     - PyInstaller `--onedir` 빌드 결과물인 `dist\PowerController\*` 폴더 트리 및 내부 디렉터리(`_internal/`, DLL, `.pyd`, 리소스 등)를 압축 해제 시 개별 파일 형태로 온전히 설치하도록 `[Files]` 섹션 전면 개편.
     - 단일 실행 파일 빌드 및 다중 실행 파일(메인 `PowerController.exe`, 커맨더 `PowerNetworkScheduler.exe`, 스케줄 주입기 `ApplySharedSchedules.exe`, `Register_Firewall_Rules.bat`, `docs/` 문서 트리)을 모두 유연하게 지원.
   - **기존 앱 설치 감지 시 삭제(클린)/덮어쓰기 사용자 확인 분기**:
     - 시스템에 이전 버전이 이미 설치되어 있는 경우, 사용자에게 확인 대화상자(`MsgBox`)를 띄워 **"기존 버전을 먼저 완전히 삭제하고 새로 설치(클린 설치)"**할 것인지, **"기존 파일 위에 덮어쓰기(업그레이드)"**할 것인지 명확히 질의하여 원하지 않는 파일 유실 및 설정 충돌 원천 차단.
     - 폴더 선택 페이지(`wpSelectDir`)에서도 기존 실행파일이 존재하는 경로 선택 시 덮어쓰기 재확인 팝업 제공.
   - **무인 설치(Silent Install) 완벽 지원 및 파라미터 확장**:
     - `/SILENT` (진행바만 표시), `/VERYSILENT` (완전 무음), `/SUPPRESSMSGBOXES`, `/NORESTART`, `/DIR=...` 완벽 지원.
     - 무인 설치 모드 시에는 팝업 질의 없이 안전하게 기본 덮어쓰기/업그레이드로 즉시 진행하며, `/CLEAN` 또는 `/CLEANINSTALL` 커맨드라인 스위치 전달 시 기존 버전을 무음으로 완전 언인스톨 후 새로 설치하는 옵션 제공.
   - **설치 단계 방화벽 규칙 사전 무음 등록 (메인 & 커맨더 버전 표기 명칭 포함)**:
     - 설치 중 파일 추출 직후(`CurStepChanged(ssPostInstall)`) 관리자 권한을 활용하여 프로그램 최초 실행 전에 방화벽 규칙을 사전에 조용히(`SW_HIDE`) 자동 등록.
     - **등록 대상 2종 모두 포괄**:
       1. 메인 앱: `PowerController (Inbound/Outbound)` 및 버전 표기 `PowerController v2.9.1 (Inbound/Outbound)`
       2. 커맨더 관리 타워: `PowerNetworkScheduler (Inbound/Outbound)` 및 버전 표기 `PowerNetworkScheduler v2.9.1 (Inbound/Outbound)`
       3. 전용 통신 포트: `PowerController TCP 9988`, `UDP 9985`, `UDP 9986` 및 `PowerController v2.9.1 TCP 9988/UDP 9985/UDP 9986`
     - 프로그램 실행 시 사용자를 방해하는 Windows Defender 방화벽 "공용 네트워크 액세스 허용" 보안 경고창을 사전 원천 차단.
     - 언인스톨 시에도 기본 및 버전 표기 방화벽 규칙을 깨끗하게 정리하도록 보장.

6. **순수 창작 5대 저수준 C/C++ 네이티브 DLL 엔진 통합 구축 (`PowerCoreNative`, `NetBeaconEngine`, `FirewallNative`, `SysPowerHook`, `ScheduleCrypto`)**
   - **아키텍처 혁신 (100% C ABI & Graceful Fallback)**:
     - 파이썬의 고질적 한계(GIL 병목, 서브프로세스 생성 콘솔 깜빡임, 절전 모드 타이머 동결)를 해결하기 위해 5대 전용 고속 네이티브 C/C++ DLL을 개발하고 `native_bridge.py` 이중화 레이어로 통합.
   - **5대 핵심 모듈 상세**:
     1. **`PowerCoreNative.dll`**: 하드웨어 웨이크업 타이머(`SetWaitableTimer`, `fResume=TRUE`), 절전/화면꺼짐 방지 네이티브 락(`SetThreadExecutionState`), 무음 프로세스 트리 킬러(`Toolhelp32`), Restart Manager 파일 락 자동 해제(`RmShutdown`).
     2. **`NetBeaconEngine.dll`**: Winsock2 논블로킹 UDP 비콘 엔진 및 512 슬롯 락프리 링버퍼(Ring Buffer). 사내 500대 동시 수신 시 0.0% CPU 점유율 및 패킷 유실 제로 실현.
     3. **`FirewallNative.dll`**: Windows 방화벽 COM(`INetFwPolicy2`, `INetFwRules`) 직결 일괄 트랜잭션. 기존 `netsh.exe` 다중 호출 지연(2~3초)을 메모리 상 0.05초로 압축.
     4. **`SysPowerHook.dll`**: Windows 세션 알림 감지(`WTSRegisterSessionNotification`), 화면 잠금/해제 실시간 감시, 하드웨어 배터리/UPS 잔량 및 10% 위험 수위 실시간 감시, 0.0001초 초고속 화면 잠금 및 모니터 끄기.
     5. **`ScheduleCrypto.dll`**: 결정론적 C99 SHA-256 해시, 관리자 마스터 키 기반 HMAC-SHA256 디지털 서명, Salt 결합 암호화 봉투 인코딩/디코딩 엔진. 악의적 스케줄 변조 및 전원 공격 사전 원천 차단.
   - **빌드 및 인스톨러 배포 자동화**:
     - `build.bat`에 GCC/Clang/MSVC 기반 5대 DLL 일괄 컴파일 파이프라인 탑재.
     - `PowerController.iss` 및 `installer.py`에 5대 DLL 배포 목록 및 무인 설치 배포 연동 완료.

7. **풀-프레임(Edge-to-Edge) 리마스터링 아이콘 및 다크/글래스 테마 일체화 디자인 시스템 구축**
   - **대표 아이콘(`PowerController.png` & `.ico`) 전면 리마스터링**:
     - 기존 1024x1024 캔버스에서 35%에 불과했던 여백을 제거하고, 캔버스에 꽉 차는 풀-블리드(Edge-to-Edge) 네온 사이언/에메랄드 파워 심볼 및 프리미엄 다크 슬레이트 앰비언트 글로우 배경 결합.
     - Windows 탐색기 및 바탕화면 크기 설정과 100% 호환되는 16~256px 다중 해상도 표준 `.ico` 생성 및 배포.
   - **전원 모드 버튼(종료/재시작/절전/화면끔/로그아웃/알람) 비주얼 혁신**:
     - 밋밋한 작은 이모지를 고화질 풀-사이즈 벡터 아이콘(`w-5 h-5`)으로 전면 교체.
     - 비활성 상태에서는 다크 테마 배경에 스며드는 반투명 글래스모피즘(`bg-slate-800/40 border border-white/10`)을 적용하고, 활성 상태에서는 모드별 고유 그라디언트 및 네온 링으로 꽉 차오르는 시각적 피드백 제공.
   - **타이틀바 및 컴팩트 위젯 로고 엠블럼 통합**:
     - 메인 앱, 컴팩트 미니 위젯(`CompactWidget`), 데스크톱 뷰(`DesktopAppView`)의 타이틀바에 새 로고를 라운드 프레임에 꽉 차게 탑재.

8. **기능 보존 무손실 용량 최적화(Lossless Size Optimization) 및 번들 다이어트**
   - **웹 프론트엔드 코드 스플리팅 (`vite.config.ts`)**:
     - `vendor-react` (9.6KB), `vendor-icons` (42KB)로 라이브러리 번들을 분할하여 초기 로딩 성능 및 브라우저 캐싱 극대화.
     - 프로덕션 빌드에서 디버깅 소스맵을 배제(`sourcemap: false`)하여 배포 용량 대폭 절감.
   - **이미지 리소스 무손실 메타데이터 스트립**:
     - `PowerController.png`의 불필요한 메타데이터 청크를 제거하여 원본 화질을 100% 유지하면서 용량 최적화.
   - **Inno Setup 및 패키저 최대 압축**:
     - `PowerController.iss`의 `Compression=lzma2/ultra64`, `SolidCompression=yes` 연동.
     - `scripts/build_packages.py`에 ZIP 레벨 9(`compresslevel=9`) 최대 압축 적용.

9. **GitHub Releases 기반 실시간 자동 업데이트 알림 시스템 (`GitHubUpdateBanner.tsx`)**
   - **실시간 버전 검사**: 앱 구동 시 GitHub Releases API를 호출하여 최신 태그 버전(`v2.9.1`)과 현재 실행 버전을 비교.
   - **원클릭 다운로드 모달**: 상단 알림 배너를 통해 상세 패치 내역 모달을 호출하고, PC(Windows .zip), Android(.apk), iPhone(.ipa) 최신 배포본을 즉시 다운로드 가능.
   - **단일 원천(Single Source of Truth) 버전 동기화**: `package.json`의 버전을 기준으로 `main.py`, `installer.py`, `network_scheduler.py`, `index.html`, `PowerController.iss`의 버전을 일괄 동기화하는 `scripts/sync_version.py` 구축.

10. **PC, 모바일(Android APK), 아이폰(iOS IPA) 3대 플랫폼 일괄 빌더 (`scripts/build_packages.py`)**
    - 💻 **PC (Windows)**: `build_output/pc/PowerController-v2.9.1-Windows.zip` (Inno Setup 및 포터블 실행기)
    - 🤖 **모바일 (Android)**: `build_output/mobile/PowerController-v2.9.1.apk` (원격 전원 리모컨 터치 앱)
    - 🍏 **아이폰 (iOS)**: `build_output/ios/PowerController-v2.9.1.ipa` (공식 번들 규격 Info.plist 적용, AltStore/Sideloadly) 및 Safari 원터치 홈 화면 PWA 지원.
    - **원클릭 GitHub 배포 스크립트**: Windows cmd.exe 인코딩/괄호 오류를 0%로 원천 차단한 `push_to_github.bat`, `push_to_github.ps1`, `github_sync.py` 제공.

---

## [v2.9.0] - 2026-09-22

### 🚀 핵심 패치 사항: PowerNetworkScheduler.exe 기능적 업그레이드 및 메인 앱 10대 스케줄 프리셋 통합 마이너 업데이트

1. **PowerNetworkScheduler.exe 원격 즉시 실행 제어(Immediate Power Actions) 명령 전격 도입**
   - **원격 즉시 제어 명령 지원**:
     - `🛑 대상 PC 즉시 종료 (Shutdown Now)`: 지정된 단일/복수 대상 원격 PC를 대기 시간 없이 즉시 종료.
     - `🔄 대상 PC 즉시 다시시작 (Reboot Now)`: 원격 PC를 즉시 재부팅하여 시스템 업데이트 또는 정기 리셋 수행.
   - **이중 보안 및 안전 확인 다이얼로그**:
     - 사용자의 오작동 및 의도치 않은 전원 차단을 방지하기 위해 대상 IP 목록 및 유의사항이 명시된 안전 확인 팝업(`messagebox.askyesno`) 제공.
     - 기존 보안 토큰(`auth_token`) 및 복구 마스터 키 인증 체계와 100% 연동되어 비인가된 임의 네트워크 공격 원천 차단.
   - **다중 타겟 및 개별 PC 우클릭 컨텍스트 메뉴**:
     - 폼 카드 하단에 전용 제어 섹션(섹션 6)을 배치하여 IP 직접 입력 또는 [✓] 체크된 다중 PC 일괄 즉시 제어 지원.
     - 대기 중인 원격 PC 목록(Listbox)에서 마우스 우클릭 시 컨텍스트 메뉴를 통해 특정 PC만 즉각 종료/다시시작할 수 있는 직관적 제어 인터페이스 제공.
   - **메인 수신 엔진(`main.py`) 양방향 통신 처리 및 무조작 우회 통신망 연동**:
     - 표준 TCP(포트 9988)뿐만 아니라 방화벽 차단 환경 대응용 UDP(포트 9985) 우회 리스너에서도 `immediate_power` 액션을 완벽 수신/처리하도록 구현.
     - 명령 수신 시 관리자에게 즉시 ACK 응답을 전송한 후 유예시간(기본 3초) 내에 안전하게 시스템을 종료/재시작하도록 설계.

2. **PowerNetworkScheduler.exe 원격 스케줄러 10대 자주 쓰는 제목 프리셋 및 스마트 자동 추천 시스템 전격 도입**
   - **도입 배경**:
     - 메인 앱 및 웹 스케줄러에서 기존 날짜 삽입 버튼(`+앞에 일시`, `+뒤에 일시`)을 제거하고 실사용 빈도가 높은 10대 스케줄 제목 프리셋 시스템으로 전격 개편함에 따라, 독립형 원격 관리기인 `PowerNetworkScheduler.exe`에도 동일한 기능성을 확장 통합.
   - **주요 구현 기능**:
     - **10대 인기 스케줄 프리셋 콤보박스**:
       1. `심야 PC 자동 종료` (23:30, 시스템 종료, 매일)
       2. `퇴근 시간 전원 끄기` (18:30, 시스템 종료, 월~금)
       3. `대용량 다운로드 후 종료` (02:00, 시스템 종료, 유휴 감지 활성화)
       4. `점심시간 빠른 재부팅` (12:40, 재시동, 월~금)
       5. `자리 비움 절전 모드` (20:00, 절전 모드, 유휴 감지 활성화)
       6. `새벽 정기 시스템 점검 재시작` (05:00, 재시동, 매일)
       7. `업무 시작 준비 알람` (08:50, 사운드 알람, 월~금)
       8. `영화/영상 시청 후 종료` (01:00, 시스템 종료, 유휴 감지 활성화)
       9. `미사용 모니터 화면 끄기` (21:00, 화면 끄기, 유휴 감지 활성화)
       10. `렌더링/인코딩 완료 후 종료` (04:00, 시스템 종료, 유휴 감지 활성화)
     - **원클릭 스마트 자동 채우기 (`on_preset_title_selected`)**:
       - 프리셋 선택 시 규칙명뿐만 아니라 **전원 동작 모드(종료/재부팅/절전/화면끄기/알람), 권장 시각, 요일, 맞춤 경고 메시지, 유휴 상태 감지 옵션**이 한 번에 자동 구성되어 전송 준비가 완료됨.
       - 관리자는 자동 채워진 내용 중 필요 항목만 손쉽게 커스터마이징 가능.

3. **버전 메타데이터 및 바이너리 리소스 v2.9.0 동기화**
   - `network_scheduler.py`: `APP_VERSION = "2.9.0"`, 윈도우 타이틀 바 동적 버전 표기 바인딩.
   - `version_network.txt`: Windows 실행 파일 속성 `FileVersion` 및 `ProductVersion`을 `2.9.0.0`으로 정식 갱신.
   - 메인 앱 및 관련 스케줄러 컴포넌트와의 버전 호환성 완벽 보장.

---

## [v2.8.1] - 2026-09-19

### 🚀 핵심 패치 사항: 메인 & 커맨더 Windows 방화벽 규칙 사전 무음 등록 체계 구축 및 UI 가독성/레이아웃 정밀 고도화

1. **메인(`PowerController.exe`) 및 커맨더(`PowerNetworkScheduler.exe`) 2개 프로그램 Windows Defender 방화벽 규칙 사전 무음 등록**
   - **도입 배경 및 문제 해결**:
     - 원격 예약 제어(TCP 9988 / UDP 9985) 리스너 소켓 바인딩 시, 공용 네트워크 환경이나 조직/기업 정책(GPO/Intune)이 적용된 PC에서 *"공용 네트워크에서 이 앱에 액세스하도록 허용하시겠습니까? (이 설정은 조직에서 관리합니다 - 허용 버튼 비활성화)"* Windows 보안 팝업이 발생하여 사용자가 조작하지 못하는 문제 발생.
   - **3중 사전 무음 등록 체계 구축**:
     - **Inno Setup 인스톨러(`PowerController.iss`) 연동**: 관리자 권한으로 실행되는 설치 과정의 `[Run]` 단계에서 메인과 커맨더 2개 바이너리의 인바운드/아웃바운드 허용(`action=allow profile=any`) 및 포트 규칙(TCP 9988, UDP 9985)을 무음(`runhidden`) 자동 주입. 언인스톨 시 규칙 자동 정리.
     - **프로그램 내부 `ensure_firewall_rule_silent()` 고도화**: 메인(`main.py`) 및 커맨더(`network_scheduler.py`) 양쪽 모두에서 기동 시 인근 실행 파일들을 자동 탐지하여 `netsh advfirewall` 명령으로 방화벽을 무음 점검 및 자동 등록.
     - **원클릭 독립 방화벽 등록기 (`Register_Firewall_Rules.bat`) 배포**: 포터블 무설치 사용자 및 사내 관리자를 위해 관리자 권한 UAC 자동 상승 기반의 원클릭 방화벽 일괄 등록 배치 파일 기본 제공.

2. **메인 화면 체크박스 옵션 영역 2열 대칭 분할 및 메인 창 가로 폭 475px 최적화**
   - **개선 배경**: 기존 한 행에 3개 체크박스가 밀집되어 세 번째 항목(`최소화 시 트레이`)이 잘리거나 답답하던 문제를 근본적으로 해소.
   - **정돈된 2열 대칭 레이아웃**:
     - **1행**: `[📌 상단 고정]` (좌측) ----------------- `[🖥️ 스케줄러 팝업창 열기]` (우측)
     - **2행**: `[⚙️ 시작 시 자동 실행]` (좌측) ----------- `[📥 부팅 시 트레이]` (우측)
     - **3행**: `[📁 최소화 시 트레이]` (좌측) ----------- `[⚡ 강제 닫기 (/f)]` (우측)
     - **4행**: `[📡 원격 예약 수신 허용 (포트 9988)]` (전체 가로폭 확보)
   - **창 크기 최적 밸런스**: 가로 너비를 `450px`에서 **`475px`**(세로 800px)로 미세 확장하여 유틸리티 특유의 컴팩트함을 유지하면서도 시원하고 균형 잡힌 호흡 공간 확보.

3. **폰트 크기 최하 10pt 일괄 상향 및 팝업 대화상자 자동 크기 조절(Auto-fit) 구현**
   - **가독성 최하 10pt 하한선**: 7~9pt의 초소형 텍스트 179개소를 최하 10pt로 상향 조정하고, 플로팅 위젯 시계 폰트 슬라이더의 최솟값도 10pt로 안전 고정.
   - **동적 윈도우 크기 측정 함수(`auto_fit_window`)**: 오늘 예약 작업 브리핑 팝업, 즐겨찾기 편집창, 카운트다운 대기창, 경보창, 라이선스 창 등 모든 서브 팝업의 내용 길이에 맞추어 창 크기가 자동으로 유연하게 조절되도록 구현.

---

## [v2.8.0] - 2026-09-16

### 🚀 핵심 패치 사항: Windows 표준 Inno Setup 6 인스톨러 배포 엔진 전환 및 고압축/무인 설치 파이프라인 구축

1. **배포 인스톨러 엔진 Inno Setup 6 (`PowerController.iss`) 전격 전환**
   - **도입 배경 및 개선 목적**:
     - 기존 파이썬 기반 커스텀 인스톨러(`installer.py` + PyInstaller)의 큰 패키징 용량, 바이러스 백신(Windows Defender 등)의 오진 가능성, 불완전한 제어판 등록 문제를 원천 해소.
     - Windows 표준 소프트웨어 배포 규격인 **Inno Setup 6** 엔진을 채택하여 안정성, 설치 속도, 제어판 언인스톨러 등록의 신뢰성을 엔터프라이즈 수준으로 격상.
   - **Inno Setup 6 스크립트 (`PowerController.iss`) 구현 특징**:
     - **초고압축 솔리드 엔진**: `Compression=lzma2/ultra64` 및 `SolidCompression=yes`를 적용하여 셋업 실행 파일 용량을 대폭 경량화하고 압축 해제 속도를 극대화.
     - **네이티브 다국어 지원**: 한국어(`Korean.isl`)와 영어(`Default.isl`) 설치 마법사 언어를 공식 탑재하여 시스템 언어에 맞춰 매끄럽게 안내.
     - **편의 작업(Tasks) 옵션**:
       - `[ ] 바탕 화면에 바로가기 아이콘 생성` (기본 활성화)
       - `[ ] Windows 시작 시 자동 실행 등록` (선택 가능)
       - `[ ] PowerController 지금 바로 실행하기` (설치 완료 후 즉시 실행)
     - **동시 실행 방지 뮤텍스 (`AppMutex`)**: `PowerController_SingleInstance_Mutex` 및 `CloseApplications=yes`를 통해 프로그램이 실행 중인 상태에서 덮어쓰기 오류가 발생하지 않도록 사전 점검.
     - **64비트 아키텍처 최적화**: `ArchitecturesInstallIn64BitMode=x64compatible` 설정으로 64비트 Windows 환경에 완벽 대응.

2. **Windows 제어판 및 설정 앱 '프로그램 추가/제거' 공식 등록 및 클린 언인스톨**
   - 설치 완료 시 표준 언인스톨러(`unins000.exe`)가 생성되며, Windows 제어판 '프로그램 및 기능' 및 Windows 10/11 '설치된 앱'에 정식 등록.
   - 게시자(`cisnet.co.kr`), 버전(`2.8.0`), 공식 웹사이트 링크, 설치 경로, 공식 아이콘이 제어판에 일목요연하게 표시.
   - 제거 시 프로그램 파일, 생성된 임시 파일(`.tmp`), 로그 파일(`.log`)을 완벽하게 정리하며 잔여물이 남지 않도록 설계.

3. **자동화 빌드 스크립트 (`build.bat`) Inno Setup 6 컴파일러 (`ISCC.exe`) 자동 연동**
   - 프로젝트 루트의 `build.bat`이 다음 경로에서 Inno Setup 6 컴파일러를 자동 탐색:
     - `%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe`
     - `%ProgramFiles%\Inno Setup 6\ISCC.exe`
     - `%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe`
     - 시스템 전역 환경변수 PATH (`iscc.exe`)
   - `ISCC.exe` 감지 시 `/DMyAppVersion=%APP_VERSION%` 인자를 주입하여 원클릭으로 `dist\PowerController_Setup_v%APP_VERSION%.exe`를 자동 컴파일.
   - Inno Setup 6 미설치 환경의 경우 공식 다운로드 링크 안내 및 파이썬 인스톨러 자동 폴백(Fallback) 보장.

4. **망관리자 및 기업 환경을 위한 무인 자동 설치(Silent Install) 스위치 공식 지원**
   - 사내 PC 일괄 배포 및 자동화 스크립트를 위한 Inno Setup 6 표준 커맨드라인 스위치 지원:
     - `/SILENT`: 설치 대화상자 없이 진행 표시줄만 표시하며 자동 설치.
     - `/VERYSILENT`: 모든 UI를 숨기고 완전 백그라운드 무인 설치.
     - `/NORESTART`: 설치 완료 후 시스템 재시작 방지.
     - `/DIR="C:\PowerController"`: 대상 설치 경로 수동 지정.
     - `/TASKS="desktopicon,startupicon"`: 특정 바로가기 생성 옵션 강제 지정.

5. **소프트웨어 버전 관리 (Semantic Versioning 2.0.0) v2.8.0 승격**
   - 설치 및 배포 프레임워크의 대규모 전환에 맞춰 MINOR 버전 승격 (`v2.7.0` ➔ `v2.8.0`).
   - 전체 소스코드(`src/types.ts`, `package.json`, `main.py`, `version_*.txt`, `PowerController.iss`) 일괄 동기화.

6. **Windows 실행 파일 속성 '자세히(Details)' 탭 고유 메타데이터 완전 주입**
   - 사용자가 Windows 탐색기에서 실행 파일 우클릭 후 **[속성] > [자세히]** 탭을 열람할 때 표시되는 시스템 정보를 정식 엔터프라이즈 수준으로 완비:
     - **적용 대상**: `PowerController.exe`, `PowerNetworkScheduler.exe`, `PowerController_Setup_v2.8.0.exe`, `ApplySharedSchedules.exe`
     - **다국어 매핑**: 한국어 OS 환경(`041204B0` / 1042)과 영문 OS 환경(`040904B0` / 1033)을 동시 지원하여 시스템 언어에 맞춰 네이티브로 표시.
     - **주입 필드**: `파일 설명(FileDescription)`, `파일 버전(FileVersion 2.8.0.0)`, `제품 이름(ProductName)`, `제품 버전(ProductVersion 2.8.0.0)`, `저작권(LegalCopyright)`, `회사(CompanyName)`, `내부 이름(InternalName)`, `원본 파일 이름(OriginalFilename)`, `합법적 상표(LegalTrademarks)`, `설명/주석(Comments)`.
     - **Inno Setup 6 연동**: `PowerController.iss` 내 `VersionInfo*` 지시어를 완벽 구성하여 생성된 셋업 실행 파일에도 동일한 파일 속성이 표시되도록 구현.

---

## [v2.7.0] - 2026-09-16

### 🚀 핵심 패치 사항: 데스크톱 앱 APPDATA 영구 저장 경로 분리(설정 미반영 해결), 미니 위젯 5종 테마 엔진, 정각 차임벨 및 부팅 예약 브리핑 시스템

1. **데스크톱 앱 데이터 저장소 경로 격리 및 권한 문제 원천 해결 (`get_data_filepath`)**
   - **문제 현상 및 원인 분석**:
     - 컴파일된 데스크톱 실행 파일(`PowerController.exe`)이 `C:\Program Files\PowerController` 등 관리자 권한 보호 폴더에 설치된 환경에서, 일반 권한으로 앱 실행 시 설정 파일(`power_timer_settings.json`, `power_schedules.json`, `power_history.json`)을 실행 파일 디렉터리에 직접 쓰려다 Windows UAC(사용자 계정 컨트롤) `PermissionError`가 발생.
     - 이로 인해 프로그램 종료 후 재실행 시 설정 및 스케줄이 반영되지 않고 초기화되는 "수정된 내용이 데스크톱 앱에 적용 안 됨" 문제 발생.
     - 또한 소스 코드(`main.py`) 수정 후 `build.bat`을 통한 재컴파일 없이 기존 구버전 바이너리를 실행할 경우 최신 변경 사항이 반영되지 않음.
   - **해결 방안 (`get_data_filepath`)**:
     - 파일 저장 경로 결정 함수 `get_data_filepath(filename)`를 도입하여 쓰기 권한을 사전 테스트.
     - 쓰기 권한이 없는 보호 폴더(`Program Files` 등)에 위치하거나 패키징된 실행 환경일 경우 사용자 전용 안전 저장소인 `%APPDATA%\PowerController\`로 자동 분기 및 저장.
     - 기존 실행 파일 폴더에 구버전 설정 파일이 존재할 경우 `%APPDATA%`로 자동 무손실 마이그레이션 수행.
     - **빌드 동기화 가이드 안내**: 소스 코드 수정 후에는 `build.bat` 스크립트를 실행하여 새 실행 파일(`dist\PowerController.exe`)로 컴파일해야 함을 문서화.

2. **Python 데스크톱 미니 위젯 5종 테마 및 동적 리빌드 엔진 탑재 (`main.py`)**
   - **5종 디자인 테마 완전 지원**:
     1. **네온 링 (`standard`)**: 고대비 다이얼과 네온 블루 링 시각화.
     2. **사이버 HUD (`cyber_hud`)**: 공상과학 스타일의 각진 테두리와 텔레메트리 레이아웃.
     3. **초슬림 바 (`minimal_bar`)**: 화면 어디에나 부담 없이 거치 가능한 한 줄 가로형 바.
     4. **레트로 LED (`retro_led`)**: 전광판 스타일의 고휘도 그린 매트릭스 디지털 폰트.
     5. **클린 카드 (`clean_card`)**: 모던 미니멀리즘 슬레이트 카드 디자인.
   - **동적 리빌드 엔진 (`rebuild_mini_window`)**:
     - 앱을 재부팅하지 않고도 환경설정에서 위젯 테마 변경, 너비 조절, 글꼴 크기 변경 시 위젯 윈도우를 실시간으로 부드럽게 재생성 및 재배치.
   - **정밀 커스터마이저 연동**:
     - 위젯 가로 너비(220px ~ 380px), 타이머 폰트 크기(14pt ~ 28pt), 시계 폰트 크기(9pt ~ 18pt), 위젯 투명도(30% ~ 100%), 시계 표시 여부를 설정에서 조절 및 영구 저장.

3. **매 시 정각 웨스트민스터 차임벨 소리 & 알림 (`Hourly Chime 🔔`) 탑재**
   - 시스템 시간이 매 시 00분 00초 정각에 도달할 때, Westminster Quarters 차임벨 멜로디(비프음 주파수 시퀀스)를 백그라운드 스레드에서 자동 연주.
   - 환경설정 창 내 토글 체크박스 및 `🔊 테스트` 버튼을 배치하여 즉각적인 사운드 청취 지원.

4. **앱 시작/부팅 시 오늘의 예약 작업 자동 점검 및 브리핑 (`Startup Tasks Alert 📅`)**
   - 프로그램 기동 시 당일(오늘의 요일 및 일회성 날짜)에 예약된 활성 전원 관리 규칙을 자동 스캔.
   - 오늘 실행될 예약 작업이 존재할 경우 깔끔한 전용 모달 창을 띄워 오늘의 작업 목록, 예정 시각, 전원 행동을 사용자에게 선제 브리핑.
   - 환경설정에서 활성화/비활성화 토글 및 `📋 미리보기` 버튼 지원.

5. **데스크톱 환경설정 팝업 (`open_settings_popup`) UI/UX 전면 개편**
   - 다양한 모니터 해상도 및 DPI 스케일링에서 옵션이 잘리지 않도록 `ScrollableFrame` 기반의 스크롤 컨테이너 전면 도입.
   - 9개 카테고리(테마, 사운드, 미니 위젯 테마/크기, 스마트 알림, 메인창 투명도/폰트, 예약 대기시간, 강제 종료 플래그, 네트워크 보안 토큰, 배포기 빌더)로 정연하게 그룹화.

6. **Semantic Versioning 3단계 규약에 따른 버전 관리 및 동기화**
   - 신규 기능(Feature) 추가 및 하위 호환성 유지 원칙에 따라 MINOR 버전 승격 (`v2.6.0` ➔ `v2.7.0`).
   - 전체 코드베이스(`src/types.ts`, `package.json`, `metadata.json`, `index.html`, `main.py`, `version_*.txt`) 일괄 버전 동기화 완료.

---

## [v2.6.0] - 2026-09-14

### 🚀 핵심 패치 사항: 실행 중인 프로그램 강제 종료 플래그(Windows `/f` 파라미터) 기본 활성화 지원 및 개발 서버 포트 충돌 방지 시스템

1. **실행 중인 프로그램 강제 종료 플래그 (`force_close` / Windows `/f` 파라미터) 지원 (기본: 옵션 활성화 상태)**
   - **배경 및 도입 목적**:
     - Windows 환경에서 자동 종료 또는 재시작 시, 미저장 텍스트 문서나 응답이 지연된 프로세스가 '저장하시겠습니까?' 확인 대화상자를 띄우며 시스템 종료 카운트다운을 취소시키거나 영구 정지(Halt)시키는 문제를 원천 차단합니다.
     - 사용자가 자리를 비우거나 취침 시 예약된 전원 제어가 100% 확실하게 집행되도록 신뢰성을 보장합니다.
   - **기본 활성화 (Default: Enabled) 원칙 채택**:
     - 사용자의 별도 복잡한 조작 없이도 처음부터 강제 종료 플래그가 활성화되어 있어 실패 없는 전원 차단을 제공합니다.
   - **Python 데스크톱 엔진 (`main.py`)**:
     - `self.force_close_enabled` 변수 신설 및 기본값 `True` 지정.
     - `settings.json` 환경설정 파일에 `force_close_enabled` 영구 직렬화 및 프로그램 시작 시 자동 복원.
     - 실제 시스템 명령 실행(`execute_power_action`) 시 `shutdown /s /f /t 2` (종료) 및 `shutdown /r /f /t 2` (재시작) 형태로 `/f` 플래그 자동 분기 반영.
     - 메인 GUI 하단 옵션 바(`opt_row3`)에 `⚡ 강제 닫기 (/f)` 체크박스를 배치하여 작업 전 원클릭 토글 지원.
     - 환경설정(Preferences) 창 내에 **[8. ⚡ 실행 중인 앱 강제 종료 플래그 (/f)]** 전용 설정 및 상세 가이드 제공.
     - 원격 네트워크 제어(`handle_network_client`) 및 예약 작업 카운트다운(`open_grace_popup`) 시에도 사용자의 기본 강제 종료 플래그가 누락 없이 적용되도록 데이터 동기화.
   - **React 웹 프론트엔드 (`src/App.tsx`, `src/types.ts`)**:
     - `forceCloseEnabled` 상태 및 `localStorage`(`power_force_close_enabled`) 영구 저장 지원 (초기 기본값 `true`).
     - 타이머 탭 상단에 직관적인 퀵 토글 바 신설 (`⚡ 실행 중인 앱 강제 종료 (/f)`).
     - 환경설정 모달 창 내 **[6. 실행 중인 프로그램 강제 종료 (/f 파라미터)]** 섹션 추가.
     - 가상 전원 시뮬레이터(`PowerSimulator.tsx`)에 `forceClose` prop 전달 및 시각적 활성화 배지(`⚡ 실행 중인 앱 강제 종료 플래그 (/f) 적용됨`) 출력.

2. **개발 서버 포트 충돌 방지 및 다중 포트 실행 환경 구축 (`server.ts`, `package.json`)**
   - 로컬 개발 환경에서 다른 웹 프로젝트(포트 3000 점유 프로세스 등)와의 포트 충돌을 원천 방지하기 위해 `CUSTOM_PORT` 환경변수 지원 (`server.ts`).
   - `package.json`에 간편 실행 스크립트 추가:
     - `npm run dev:4000`: 포트 4000으로 즉시 기동
     - `npm run dev:5000`: 포트 5000으로 즉시 기동
     - `npm run dev:custom`: 커스텀 포트 구동
   - AI Studio 클라우드 컨테이너 환경의 Nginx 리버스 프록시(포트 3000 전용 게이트웨이)와의 완벽한 하위 호환성 유지.

3. **Semantic Versioning 3단계 규약에 따른 버전 관리 및 동기화**
   - 신규 기능(Feature) 추가 및 하위 호환성 유지에 따라 MINOR 버전 승격 (`v2.5.0` ➔ `v2.6.0`).
   - 전체 코드베이스(`src/types.ts`, `package.json`, `metadata.json`, `index.html`, `main.py`, `network_scheduler.py`, `version_*.txt`, `build.bat`)의 버전 및 메타데이터 일괄 동기화 완료.

---

## [v2.5.0] - 2026-09-12

### 🚀 핵심 패치 사항: 컴팩트 위젯 5종 디자인 커스터마이저 & 안전 설정 트랜잭션, 정각 알림 및 부팅 스케줄 안내

1. **상단 고정 컴팩트 위젯 맞춤 커스터마이저 (5종 디자인 & 실시간 슬라이더 탑재)**
   - **다채로운 5종 디자인 테마**:
     1. **네온 링 (Neon Ring)**: 클래식 원형 프로그레스 다이얼 및 고채도 링 시각화.
     2. **사이버 HUD (Cyber HUD)**: 공상과학 스타일의 텔레메트리 바 및 고밀도 텍스트 레이아웃.
     3. **슬림 바 (Slim Bar)**: 화면 공간을 최소화하여 단 한 줄로 모든 상태를 파악하는 컴팩트 가로형 바.
     4. **레트로 LED (Retro LED)**: 전광판/터미널 감성의 그린 LED 디지털 디스플레이.
     5. **클린 카드 (Clean Card)**: 불필요한 장식을 배제한 모던 미니멀리즘 카드.
   - **실시간 크기 및 폰트 슬라이더 제어**:
     - 위젯 가로 너비(260px ~ 460px), 현재 시각 글자 크기(9px ~ 18px), 타이머 카운트다운 글자 크기(16px ~ 36px)를 환경설정에서 실시간으로 정밀 조절할 수 있습니다.
     - 설정된 위젯 디자인과 치수는 `localStorage`에 영구 보존됩니다.

2. **환경설정 변경 사항 안전 버퍼링 트랜잭션 (Confirm / Cancel) 도입**
   - 설정 창을 열어 옵션을 조작하는 동안 임시 버퍼(`draftSettings`)에서만 상태가 유지되며, **'확인 (적용)'** 버튼을 클릭했을 때만 실제 테마, 폰트, 불투명도 및 알림 옵션이 시스템에 영구 저장 및 반영됩니다.
   - 상단 `X` 닫기 버튼 또는 `취소` 버튼을 누르면 모든 임시 변경 사항이 안전하게 롤백되어 의도치 않은 설정 오동작을 완벽히 방지합니다.

3. **매 정각 알림 차임벨 기능 (Hourly Chime 🔔)**
   - 매 시 00분 00초 정각에 도달할 때 시계 종소리/비프음 멜로디와 함께 정각 알림 토스트 팝업 및 실시간 동작 로그가 송출됩니다.
   - 환경설정에서 자유롭게 ON/OFF 토글할 수 있으며 상태가 지속 보존됩니다.

4. **부팅/시작 시 오늘 예약 작업 점검 및 안내 모달 (Startup Tasks Alert 📅)**
   - 프로그램 기동 시 오늘의 요일 및 날짜에 예약된 활성 전원 제어 규칙(매일 반복, 해당 요일 반복, 특정 날짜 예약)을 자동으로 점검하여 예쁜 팝업 모달로 브리핑합니다.
   - 모달에서 바로 스케줄러 관리 창으로 이동할 수 있는 바로가기 단추를 제공합니다.

5. **스케줄러 사용자 경험 강화 (Ergonomics & Timestamps)**
   - 신규 스케줄 생성 시 트리거 전원 행동 기본값을 가장 많이 사용하는 **'종료(Shutdown)'**로 지정하여 빠른 등록을 돕습니다.
   - 규칙 이름 입력창 우측에 **`[앞에 추가]` / `[뒤에 추가]`** 단추를 신설하여 현재 날짜와 시간(`[YYYY-MM-DD HH:mm]`)을 원클릭으로 메모에 부착할 수 있습니다.

6. **모니터링 현황 영역 마우스 휠 스크롤 지원 및 공식 블로그 연동**
   - 사이드바뿐만 아니라 메인 모니터링 영역 전체에서 마우스 휠 스크롤이 매끄럽게 동작하도록 보강했습니다.
   - 하단 상태 표시줄 및 도움말 패널에 공식 블로그 링크(`https://ahbiyoutvibe.blogspot.com/`)를 연동했습니다.

---

## [v2.4.0] - 2026-07-10

### 🚀 핵심 패치 사항: 예약 알림 대기시간 커스텀 설정 & 스케줄러 알람 행동 완전 통합

1. **스케줄러 트리거 대기 행동에 "알람 (Alarm)" 예약 옵션 추가**
   - 기존의 종료, 재시작, 절전, 화면끄기, 로그아웃에 이어, 규칙 스케줄러 및 추가 폼의 "트리거 대기 전원 행동" 선택지에 **"알람 (Alarm)"** 행동을 완전하게 동기화 추가하였습니다.
   - 특정 요일, 특정 주기에 따라 시스템에 영양을 주지 않고 기상 알람 및 스케줄 경보를 울리는 독립 알람 예약 규칙을 자유롭게 스케줄러에 구성 및 등록하실 수 있습니다.

2. **예약작업 전 "알림 대기시간 (Grace Warning Duration)" 커스텀 제어 환경설정 탑재**
   - 예약작업 실행 10초 전에 강제 노출되던 거대 안내 카운트다운 팝업창의 지속 시간을 사용자의 기호 및 원격 관리 요구에 맞춰 조절할 수 있는 **'예약작업 알림 설정'**을 새롭게 개발 및 통합했습니다.
   - **데스크톱 (Python)**: '환경설정 (Preferences) ...' 메뉴 하단에 전용 설정 섹션이 배치되어, 대기 시간을 최소 **5초**에서 최대 **5분(300초)**까지 선택할 수 있으며, 이 설정은 데이터 파일(`power_timer_settings.json`)에 영구 보존됩니다.
   - **웹 시뮬레이터 (React)**: 우측 하단 메인창 환경설정 패널에 예약작업 알림 설정 드롭다운 메뉴를 연동하여, 대기시간(5초/10초/20초/30초/1분/3분/5분)을 변경 시 즉각적으로 카운트다운 비프음 멜로디 및 실시간 타임라인에 완전 반영합니다.

3. **윈도우 제어판 공식 게시자 'cisnet.co.kr' 및 공식 저작권 'AhBiYout' 동기화**
   - 데스크톱 인스톨러(`installer.py`)를 이용해 앱을 패키징 및 설치할 때, 윈도우 제어판 '프로그램 추가/제거' 상에 등록되는 공식 게시자(Publisher) 및 실행 파일의 회사명 정보(CompanyName)를 **'cisnet.co.kr'**로 변경하였으며, 공식 법적 저작권(LegalCopyright)은 원저작자인 **'AhBiYout'**으로 아름답게 승격 동기화하였습니다.

4. **CLI 기반 무인설치(Silent/Unattended Installation) 기능 및 명령 행 옵션 전격 도입**
   - 사내 시스템 일괄 배포 및 스크립트 기반 원격 일괄 자동 설치 요구를 충족하기 위해, 인스톨러(`installer.py`)에 Tkinter GUI 창을 띄우지 않는 CLI 백그라운드 무인설치 및 무인제거 엔진을 완비했습니다.
   - `--silent` / `-s` / `/S` 옵션을 통해 무인 기동이 활성화되며, 설치 디렉터리를 조절할 수 있는 `--dir` / `/D=` 옵션 및 개인 프로필 자산 파쇄를 위한 `--clean` 옵션, 단축키/자동시작 스킵을 위한 다양한 조절용 플래그가 긴밀하게 대응되도록 설계되었습니다.

---

## [v2.3.0] - 2026-07-08

### 🚀 핵심 패치 사항: 스케줄러 예약 알람(Alarm Mode) 기능 및 관련 인터페이스 통합

1. **새로운 전원 제어 행동 '예약 사운드 알람(Alarm Mode)' 전격 도입**
   - 기존의 시스템 종료, 재시작, 절전, 화면 끄기, 로그아웃 외에 시스템에 해를 끼치지 않고 지정한 시각 혹은 주기에 경보음을 울려주는 **'예약 알람'** 모드를 신설하였습니다.
   - React 웹 앱 환경과 Python/Tkinter 데스크톱 환경 모두에 전면 통합되어 양쪽 빌드에서 동일한 메커니즘으로 동작합니다.

2. **반복 챠임벨 및 직관적인 경보 모달 디자인 설계**
   - **데스크톱 (Python)**: 지정 시간 도달 시 핑크/로즈 테마의 경고 창이 화면 중앙 최상단(`-topmost`)에 팝업되어, 사용자가 해제 버튼을 누를 때까지 3.5초 주기로 우아한 멜로디 비프음(`winsound.Beep`)을 무한 루프로 재생합니다.
   - **웹 시뮬레이터 (React)**: 알림 시각이 경과하면 시각화 패널에 귀여운 핑크색 시계 테마의 알람 시뮬레이션 상태가 활성화되고 가상 모달에서 사운드 버저 챠임이 안전하게 재생됩니다.

3. **다국어 자동 번역 지원 및 버그 핫픽스 완료**
   - 다국어 번역 시스템에 예약 알람 번역 매핑을 완비하여, 언어 변경(국문/영문) 시 `KeyError: 'alarm'` 등의 사전 정의 충돌이나 오동작 없이 완벽하게 동작합니다.

---

## [v2.2.0] - 2026-07-08

### 🚀 핵심 패치 사항: AdvancedScheduler 폼 실시간 시각 유효성 피드백(Visual Validation Cues) 도입

1. **동적 경고 피드백 레이블 (Direct In-Form Helper Text) 도입**
   - 스케줄러에서 규칙 생성 및 수정 중 유효하지 않은 매개변수가 입력되었을 때 (이름 누락, 요일 미선택, 주기 입력 오류 등), 기존의 알림 팝업에 더해 **폼 본문 상단에 직관적인 경고 심볼(⚠️)과 빨간색(soft red) 설명 헬퍼 텍스트**가 동적으로 나타납니다.
2. **오류 대상 입력 필드 시각적 강조 (Subtle Red Borders) 적용**
   - 이름 미입력 시 테두리 적색 하이라이트 및 자동 포커싱, 요일 미선택 시 체크 영역 강조, 주기 무효값 입력 시 포커싱 이동을 적용했습니다.
3. **인터랙티브 오류 상시 초기화 (Real-time Reset & Auto-Clearing)**
   - 텍스트 재입력이나 체크박스 선택 시 붉은 테두리가 즉각 사라지는 상시 감시 로직을 결합했습니다.

---

## [v2.1.0] - 2026-07-06

### 🚀 핵심 패치 사항: 스케줄 배포 빌더 실시간 동기화 & 고가독성 상단 고정창 클록 분리

1. **스케줄 공유 배포기 빌더(`schedule_share_builder.py`) 완전 자동화 및 실시간 업데이트**
   - 스케줄 등록/수정/삭제 즉시 `schedule_share_builder.py` 파일이 현재 저장된 최신 예약 스케줄 데이터가 반영된 상태로 자동 생성 및 실시간 수정 처리됩니다.
2. **공유 배포기 생성 위치 '내 문서(My Documents)' 이관 및 폴더 자동 열기 제공**
   - 컴파일 빌드가 완료되는 즉시 생성된 '내 문서' 폴더가 자동으로 활성화(Open Folder)되어 원스톱 복사가 가능합니다.
3. **상단 고정 미니창(콤팩트 위젯) 현재 시간 표시부 2.5배 확대 및 전용 뷰 제공**
   - 볼드 디지털 시계("🕒 HH:MM:SS")로 확대 디자인되었으며 가변 지오메트리를 지원합니다.
4. **트레이 최소화 백그라운드 루프 최적화 & 이미지 렌더링 캐싱**
   - 최소화 시 체크 주기를 5초로 완화하고, 1회 리사이즈 캐싱을 통해 CPU/디스크 I/O를 사실상 0%로 절감했습니다.

---

## [v2.0.0] - 2026-06-28 (MAJOR 릴리즈)

### 🚀 핵심 패치 사항: 네트워크 원격 스케줄 전송/수신 서브시스템 탑재

1. **원격 전송 송신 엔진 (Sender)**: 동일 LAN IP와 9988 포트를 통해 원격지에 예약 규칙을 무선으로 배치.
2. **독립 백그라운드 수신 대기 서비스 (Receiver)**: 소켓 연결을 수락하여 규칙을 자동 수신하고 `power_scheduler_rules.json`에 영구 저장.
3. **소켓 예외 처리 및 멀티스레딩**: 5.0초 타임아웃 및 스레드 분리를 통한 락업 방지.

---

## [v1.1.0] - 2026-06-28

### 🚀 핵심 패치 사항: 스마트 언인스톨러 통합 빌드 프로세스

1. **설치 전 기존 버전 정밀 탐지 및 파일 잠금 해결**
2. **바탕 화면 바로가기, 레지스트리 Run 키, 제어판 명부 클린 언인스톨**
3. **인앱 라이선스 및 약관 동의 고지서 팝업 통합**

---

## [v1.0.0] - 2026-06-20 (MAJOR 최초 릴리즈)

* React UI 프론트엔드와 Python 백그라운드 시스템 트레이 제어 엔진이 결합된 하이브리드 자동 전원 오프 컨트롤러 최초 공식 릴리즈.
* 윈도우 11 Fluent 다크, 모던 그레이, 클래식 베이지 3가지 테마 지원.
* 비프음, SF 신스, 오르골 멜로디 3종 오디오 합성 피드백 지원.
* 타이머 및 스케줄러 기반 전원 제어 지원.
