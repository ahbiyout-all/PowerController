# PowerController 패치 노트 (Patch Notes)

본 문서는 **PowerController**의 릴리즈 패치 및 최신 업데이트 내역을 제공합니다. 
본 프로젝트는 **Semantic Versioning (MAJOR.MINOR.PATCH)** 3단계 규약에 따라 버전과 변경 이력을 투명하게 관리합니다.

---

## [v2.9.2] - 2026-10-17 (4대 테마 고대비 가독성, 인스톨러 클린설치/덮어쓰기 분기, 방화벽 사전 무음 등록)

### 🎨 1. 4대 테마(다크, 그레이, 화이트, 베이지) 완벽 연동 및 라이트 모드 고대비 가독성 개편
- **전체 컴포넌트 테마 동기화**: `DesktopAppView`, `AdvancedScheduler`, `CommandCopier`, `FavoritesManager`, `StartupTodayTasksModal`, `SmartAdvisorModal` 전반에 화이트(`white`) 및 베이지(`beige`) 테마 정밀 매핑.
- **고대비 시인성 극대화**: 밝은 테마 환경에서 회색/흰색 글씨가 묻히는 문제를 해결하고 고대비 텍스트 컬러(`text-[#0f172a]`, `text-[#2c2217]`) 및 테두리/버튼 호버 스타일 전면 보정.
- **테마 설정 일원화**: 로컬스토리지 `power_theme` 키와 데스크톱 설정 모달의 테마 셀렉터 리스트 완벽 일치.

### 📦 2. Inno Setup 6 인스톨러 폴더 풀림(Unpacked Multi-File) 패키징 및 클린 설치/덮어쓰기 분기
- **폴더 풀림(Unpacked Multi-File) 설치 구현**: PyInstaller `--onedir` 빌드 디렉터리(`dist\PowerController\*`) 트리 및 필수 네이티브 C/C++ DLL들을 개별 파일 구조로 깔끔하게 전개.
- **기존 설치 감지 시 사용자 선택 다이얼로그**:
  - `[예 (Yes)]`: 기존 버전 완전 삭제 후 클린 설치 (Clean Install, 권장)
  - `[아니오 (No)]`: 기존 설정 및 파일 위에 덮어쓰기 (Overwrite / Upgrade)
  - `[취소 (Cancel)]`: 설치 마법사 종료
- **무인 설치(Silent Install) 스위치 고도화**: `/SILENT`, `/VERYSILENT`, `/NORESTART` 완전 지원 및 무인 모드 전용 `/CLEAN=1` 스위치 제공.
- **불필요 파일 배포 제외**: 개발용 마크다운, 스크래치 파일 배포 원천 차단 및 필수 라이선스/에셋만 설치.

### 🛡️ 3. Windows Defender Firewall 사전 무음 등록 (기본 이름 + 버전 표기 이름)
- **인바운드/아웃바운드 및 전용 포트 사전 등록**: 메인(`PowerController.exe`), 커맨더(`PowerNetworkScheduler.exe`), 원격 통신 포트(TCP 9988, UDP 9985, UDP 9986)를 설치 직후(`ssPostInstall`) 무음 자동 등록.
- **버전 표기 명칭 동시 등록**: 기본 이름(`PowerController`)과 버전 정보가 포함된 이름(`PowerController v2.9.2`)을 동시에 등록하여 공용 네트워크 보안 경고창 원천 차단.
- **언인스톨 클린 정리**: 프로그램 제거 시(`usPostUninstall`) 등록된 모든 방화벽 규칙을 자동 소거.

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
