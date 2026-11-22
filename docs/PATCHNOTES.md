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

### 🐛 4. 전 영역 자아성찰(Deep Audit) 버그 수정 및 안정화
- **타이머 카운트다운 및 정시 예약 정확도 개선**: `App.tsx`와 `DesktopAppView.tsx`의 카운트다운 완료·경고음 호출을 React 상태 업데이터 밖의 `useEffect`로 분리하여 StrictMode 이중 실행 방지, `DesktopAppView` 특정 시각 예약(`schedule`) 24시간 롤오버 계산 및 시작 로그 표기 보정.
- **iFrame 안전 UX & UI 다듬기**: 웹 뷰의 네이티브 `confirm()` 호출 제거 및 인앱 토스트 교체, `FavoritesManager` 6모드 그리드 2행 고아 버튼 정렬(`grid-cols-3 sm:grid-cols-6`), `BatteryHistoryChart` 및 `StartupTodayTasksModal` 누락 다국어 문구 현지화.
- **버전 동기화(`sync_version.py`) 및 GitHub 저장소 경로 일원화**: `main.py`의 `GITHUB_REPO_OWNER`를 `AhBiYout-all`로 수정, `sync_version.py`의 `network_scheduler.py`(`APP_VERSION`) 및 `index.html`(`og:title`) 정규식 교정, 배포 스크립트 및 워크플로 버전 기본값을 `v2.9.2`로 통합.

### 📦 5. Inno Setup 6 인스톨러 폴더 풀림(Unpacked Multi-File) & 방화벽 사전 무음 등록
- **폴더 풀림(Unpacked Multi-File) 설치 구현**: PyInstaller `--onedir` 빌드 디렉터리(`dist\PowerController\*`) 트리 및 필수 네이티브 C/C++ DLL들을 개별 파일 구조로 전개, 기존 설치 감지 시 클린 설치(`Clean Install`) / 덮어쓰기 선택 다이얼로그 및 `/SILENT`, `/VERYSILENT`, `/CLEAN=1` 지원.
- **Windows Defender Firewall 사전 무음 등록**: 메인(`PowerController.exe`), 커맨더(`PowerNetworkScheduler.exe`), 전용 포트(TCP 9988, UDP 9985, UDP 9986) 및 버전 표기 명칭(`PowerController v2.9.2`) 동시 등록 및 제거 시 자동 정리.

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
