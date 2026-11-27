# PowerController 패치 노트 (Patch Notes)

본 문서는 **PowerController**의 릴리즈 패치 및 최신 업데이트 내역을 제공합니다. 
본 프로젝트는 **Semantic Versioning (MAJOR.MINOR.PATCH)** 3단계 규약에 따라 버전과 변경 이력을 투명하게 관리합니다.

---

## [v2.9.2] - 2026-10-17 (개별 디바이스 제어판, 자동 언어 감지, 4대 테마 고대비 및 전수 감사 픽스)

### 🖥️ 1. 50대 컴퓨터실 통합 원격 제어 타워 (`PowerNetworkScheduler`) & 개별 디바이스 제어판 (`DeviceController`)
- **50대 컴퓨터실 병렬 관제 엔진 & 재시도(`ThreadPoolExecutor` / Bounded Worker)**: `network_scheduler.py`에 최대 24스레드 병렬 TCP/UDP 배치 디스패처, 실시간 진행률 바(`Done / Total · OK · Fail`), 및 실패 PC 원클릭 재시도(`Retry Failed`) 탑재.
- **좌석 배치 그리드 뷰(`5/8/10`열) ↔ 정렬 가능한 상세 목록 뷰**: 웹 대시보드(`Lab Fleet 50` 탭), 데스크톱 네이티브 뷰(`PowerNetworkScheduler.exe`), 독립형 Python 앱 모두에서 단일 로스터 상태 기반 2종 뷰 즉시 전환 및 그룹·상태·키워드 필터 제공.
- **IP 대역 스캐너 · RFC-4180 CSV 좌석 일괄 등록 · 교시별 프로필 & 순차 WOL**: `start_ip–end_ip` IPv4 범위 자동 좌석 배정, `seat_no,ip,mac,hostname,group,row,col,memo` CSV 가져오기/내보내기, 일과·교시별 다중 규칙 번들 일괄 배포, 스위치 과부하 방지 `100ms~1000ms` 순차 WOL 기상 및 15초 실시간 생존·타이머 폴링 지원.
- **독립형 전송기 OS 언어 자동 감지(KO/EN) & 프리-버그 전수 수정**: Windows/Linux OS 로케일 자동 감지 + 상단 `KO | EN | Auto` 실시간 전환 및 `network_pc_groups.json` 저장, 기존 5건의 잠재 결함 수정 및 `main.py` 원격 즉시 제어(`sleep`/`screenoff`/`lock`/`alarm`) + 실시간 타이머 폴링 응답 확장.
- **개별 PC 즉시 원격 제어 패널**: 웹 사이드바/뷰 및 데스크톱 네이티브 뷰(`DeviceController.exe`)에서 등록된 50대 PC별로 **종료(Shutdown), 재시작(Restart), 절전(Sleep), 화면끔(Screen Off), 비상 알람(Alarm)**을 개별 또는 다중 선택하여 즉시 송출.

### 🌐 2. 브라우저/OS 기본 언어 자동 감지 & 동적 다국어 스크립트 생성
- **자동 감지 및 수동 토글 공존 (`src/utils/i18n.ts`)**: 최초 방문 시 `navigator.language` 기반 한국어/영어(`KO`/`EN`) 자동 감지(`auto`), 수동 전환(`manual`) 및 `Auto Reset` 복원 기능 지원.
- **UI & 생성 스크립트 전 영역 실시간 다국어 연동**: 웹 대시보드, 데스크톱 네이티브 뷰뿐만 아니라 `scriptGenerators.ts`에서 생성되는 **Python 제어기 및 Inno Setup 스크립트의 주석과 UI 레이블까지 동적 다국어 갱신**.

### 🎨 3. 4대 테마(다크, 그레이, 화이트, 베이지) 완벽 연동 및 컴팩트 위젯 고대비 개편
- **전체 컴포넌트 테마 동기화**: `DesktopAppView`, `CompactWidget`, `AdvancedScheduler`, `CommandCopier`, `FavoritesManager`, `StartupTodayTasksModal`, `SmartAdvisorModal` 전반에 화이트(`white`) 및 베이지(`beige`) 테마 정밀 매핑.
- **고대비 시인성 극대화**: 밝은 테마 환경에서 하드코딩된 어두운 카드/텍스트(`bg-[#18181b]`, `text-slate-200` 등)가 묻히거나 반전되는 문제를 전면 교정하고 고대비 텍스트 컬러(`text-[#0f172a]`, `text-[#2c2217]`) 및 패널/입력창 토큰 적용.
- **`CompactWidget` 슬림 바(`minimal_bar`) 설정 드로어 복구**: 슬림 바 위젯에서도 설정 버튼 클릭 시 플로팅 설정 드로어가 정상 렌더링되도록 수정하고 `App.tsx`의 위젯 디자인 식별자(`cyber_hud`, `minimal_bar`, `retro_led`, `clean_card`) 및 레거시 마이그레이션 일원화.

### 🐛 4. 전 영역 자아성찰(Deep Audit) 1·2차 버그 수정 및 안정화
- **타이머 카운트다운·스레드 안전성·리소스 누수 교정**: `App.tsx`와 `DesktopAppView.tsx`의 카운트다운 완료·경고음 호출 분리, `App.tsx` `navigator.getBattery()` `levelchange`/`chargingchange` 리스너 참조 동일성 보장으로 해제 누수 제거, `network_scheduler.py` 백그라운드 스레드(`_execute_parallel_batch`, `_scan_ip_list`, `_poll_all_known_silent`) 공유 딕셔너리 갱신의 Tkinter `root.after(0, ...)` 메인 스레드 마샬링 및 0초 도달 시 `timer_running=False` 전환, `LabNetworkFleetPanel.tsx` RFC-4180 CSV 파서/IPv4 검증 및 오프라인 대상 우선 WOL 정렬 적용.
- **iFrame 안전 UX & UI 다듬기**: 웹 뷰의 네이티브 `confirm()` 호출 제거 및 인앱 토스트 교체, `FavoritesManager` 6모드 그리드 2행 고아 버튼 정렬(`grid-cols-3 sm:grid-cols-6`), `BatteryHistoryChart` 및 `StartupTodayTasksModal` 누락 다국어 문구 현지화.
- **버전 동기화(`sync_version.py`) 및 빌드·릴리즈 스크립트 SSOT 일원화**: `main.py`의 `GITHUB_REPO_OWNER`를 `AhBiYout-all`로 수정, `scripts/build_packages.py` 및 `scripts/clean_github_release_assets.py`가 실행 작업 디렉터리에 관계없이 `ROOT_DIR/package.json`을 읽도록 수정(미존재 `apply_shared_schedules.py` 참조 제거), `build.bat`이 `package.json` SSOT를 최우선 참조하도록 개선.

### 📦 5. Inno Setup 6 표준 설치 흐름 · 프로그램 추가/제거 정식 등록 · 방화벽 무음 등록
- **표준 설치 진행 순서 구현 (`PowerController.iss` & `scriptGenerators.ts`)**: `기존 실행 중인 앱 강제 종료` → `기존 설치 감지 시 삭제(클린 설치)/덮어쓰기 질의` → `라이선스 선언(KO/EN)` → `설치(Unpacked Multi-File)` → `완료 화면(wpFinished) 바탕화면 바로가기 체크` → `앱 바로 실행` 순서로 정밀 구성.
- **Windows 프로그램 추가/제거 정식 등록 & 레거시 키 정리**: `Uninstallable=yes`, `CreateUninstallRegKey=yes`, `UninstallDisplayName`, `UninstallDisplayIcon`, `UninstallFilesDir` 명시 및 레거시 Python 설치 키 중복 정리.
- **Windows Defender Firewall 사전 무음 등록**: 메인(`PowerController.exe`), 커맨더(`PowerNetworkScheduler.exe`), 전용 포트(TCP 9988, UDP 9985, UDP 9986) 및 버전 표기 명칭(`PowerController v2.9.2`) 동시 등록 및 제거 시 자동 정리.

### ⚙️ 6. 12대 순수 창작 네이티브 DLL 고도화 · 전수 감사 패치 · `PowerExecNative.dll` 신설
- **신규 12번째 순수 창작 DLL `PowerExecNative.dll` (`native/power_exec_native.c`)**: `SE_SHUTDOWN_NAME` 프로세스 토큰 특권 획득 후 `InitiateSystemShutdownExW` / `ExitWindowsEx` 및 정식 C ABI `SetSuspendState`(기존 `rundll32` 스택 ABI 결함 해소)를 직접 호출하여 서브프로세스 없이 종료·재시작·절전(S3)·최대 절전(S4)·로그아웃 실행 및 `DiskFlushNative` 캐시 플러시 연계.
- **기존 11대 DLL 1·2차 전수 감사 및 결함 수정**:
  - `AudioDimmerNative.dll` & `FirewallNative.dll`: **손상된 Windows SDK COM GUID (`CLSID_MMDeviceEnumerator`, `IID_INetFwPolicy2`, `CLSID_NetFwRule`, `IID_INetFwRule`) 공식 값 정밀 복원**, `DllMain` 전역 COM 제거 및 per-call RAII(`ScopedComInit`/`ScopedAudioCom`) 전환, Audio QPC 단일 엔드포인트 페이드 최적화.
  - `ScheduleCrypto.dll`: Base64 디코드 테이블 256원소 전체 초기화, 비최종 4문자 블록 내 `'='` 포함 등 잘못된 Base64 패딩 엄격 거부, OS CSPRNG(`RtlGenRandom`) 솔트 적용, `constant_time_compare` HMAC 검증.
  - `CommanderTcpDispatcherNative.dll` & `CommanderPingScannerNative.dll`: 비동기 `FIONBIO` + `select()` 타임아웃으로 스택 UAF 크래시 원천 제거, `NativeSendRuleCommandWithAck` 신설, 스레드 안전 `WSAStartup`, `NativeSendWakeOnLanEx` 및 32스레드 C 풀 `NativeBatchScanLanTargets` 병렬 스캐너 신설.
  - `PowerCoreNative.c`, `SysPowerHook.c`, `NetBeaconEngine.c`, `DisplayDdcNative.dll`, `LowLevelInputIdleNative.dll`, `DiskFlushNative.dll`: `PowerCoreNative` `DLL_PROCESS_DETACH` `lpvReserved == NULL` 가드로 프로세스 종료 데드락 방지, `SysPowerHook` 타임아웃/초기화 실패 시 워커 스레드 핸들 누수 및 `g_WorkerThreadId` 정리, `inet_pton` 전환, `SendMessageTimeoutW` 데드락 방지, 동적 프로세스 트리 확장·사이클 가드, VESA min/max 정규화 및 `NativeGetHardwareBrightness` 구현, 32비트 롤오버 오차 제거.
- **통합 빌드 및 브리지 일원화**: `native_bridge.py`(`encrypt_schedule_payload` 내 섀도우 `import os` 제거, `set_hardware_brightness` 및 Core Audio·Idle 래퍼 완비), `main.py`, `network_scheduler.py`, `schedule_share_builder.py`(무음 프로세스 종료 연계), `installer.py`, `build.bat`, `PowerController.iss`, `scripts/build_packages.py`, `scriptGenerators.ts`에 12대 DLL 컴파일·번들·호출 파이프라인 완비 및 `docs/pure_custom_dll_architecture.md` · `docs/dll_specification.md` 상세 기술 등록.

---

## [v2.9.1] - 2026-10-09 (GitHub 릴리스 자동화, 실시간 자동 업데이트 및 크로스 플랫폼 패키징)

### 🚀 1. GitHub Releases 기반 실시간 자동 업데이트 시스템 구축
- **실시간 버전 비교 & 자동 알림 팝업**:
  - `https://api.github.com/repos/AhBiYout-all/PowerController/releases/latest` API 실시간 통신 연동.
  - 새 버전 감지 시 상단 그래디언트 배너 및 인터랙티브 업데이트 안내 팝업창(`UpdateModal`) 자동 실행.
  - 팝업창 구성: Windows 공식 설치 프로그램 다운로드 버튼, 깃허브 저장소 및 릴리스 경로, 현재 버전(`v2.9.1`) vs 최신 릴리스 버전 비교 카드, 상세 패치 노트, 제작자(`AhBiYout`) 및 공식 채널(구글 블로그, 소속사) 카드.

### 🌐 2. 제작자 및 공식 채널 표준화
- **개발자명**: `AhBiYout`
- **GitHub 공식 계정**: `AhBiYout-all` (`https://github.com/AhBiYout-all`)
- **기본 저장소**: `https://github.com/AhBiYout-all/PowerController`
- **공식 구글 블로그**: `https://ahbiyoutvibe.blogspot.com/`
- **소속사**: `https://www.cisnet.co.kr`

### 🔒 3. 개인정보 및 보안 보호 (PII Shield)
- 깃허브 업로드 시 개인 이메일 및 개인 식별 정보(PII) 절대 노출 금지.
- Git Commit Author를 `AhBiYout-all <AhBiYout-all@users.noreply.github.com>`으로 규격화.
- `.gitignore` 하드닝: 임시 파일, 개인 환경설정 파일, 포터블 바이너리, 로그, 비밀 키 누출 차단.

### ⚙️ 4. GitHub Actions CI/CD 워크플로 공식 규격 준수 (Node.js 22 LTS / 24 전환)
- **Node.js 20 EOL 대응**: GitHub Actions 러너에서 Node.js 20 사용이 공식 중단(Deprecated)됨에 따라 최신 **Node.js 22 LTS** 환경으로 완전 전환.
- **Windows 공식 인스톨러 자동 빌드**:
  - Inno Setup 6 기반 폴더 풀림(Unpacked Multi-File) 공식 인스톨러 (`PowerController_Setup_v2.9.1.exe`) 자동 컴파일 및 릴리스 배포.
- **릴리스 자산 정제 정책**: 릴리스 자산(Release Assets)에는 오직 순수 **공식 인스톨러 파일만 첨부**하고, 불필요한 zip/포터블/개발문서 파일은 자동 제외.

### 💿 5. Inno Setup 설치 마법사 엔지니어링 표준화
- **폴더 풀림(Unpacked Multi-File) 개별 파일 설치**:
  - 압축 단일 파일이 아닌 시스템 친화적인 개별 파일 설치 구조 구현.
  - 불필요한 개발용 문서 및 포터블 파일 배포 제외.
- **기존 앱 감지 및 삭제/덮어쓰기 질의**:
  - 기존 설치본 발견 시 사용자에게 클린 설치(완전 삭제 후 설치) 또는 덮어쓰기(업그레이드) 선택 다이얼로그 표시.
- **무인 설치(Silent Install) 완벽 지원**:
  - `/SILENT`, `/VERYSILENT`, `/NORESTART`, `/SUPPRESSMSGBOXES` 스위치 지원.
  - 사내 원격 배포 시 백그라운드 무인 설치 완료.
- **Windows Defender 방화벽 무음 사전 등록**:
  - 기본 이름(`PowerController (Inbound/Outbound)`) 및 버전 명기 이름(`PowerController v2.9.1 (Inbound/Outbound)`) 동시 등록.
  - 커맨더 앱(`PowerNetworkScheduler`) 및 전용 통신 포트(TCP 9988, UDP 9985, UDP 9986) 등록.
  - 프로그램 삭제 시 방화벽 규칙 자동 소거.

---

## [v2.9.0] - 2026-10-06 (C/C++ 네이티브 엔지니어링 및 효과음 엔진)
- 7대 Pixabay 프리미엄 사운드 테마(`classic`, `marimba`, `crystal`, `scifi`, `westminster`, `urgent`, `bubble`)
- 상황별 사운드 믹서 및 데스크톱 전용 사운드 스튜디오
- 헤더 Mute All (즉시 0% 음소거 / 원복) 토글
