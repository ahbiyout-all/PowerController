# PowerController 개발 가이드 (Development Documentation)

이 문서는 **PowerController v2.9.1**의 프로젝트 아키텍처, 구성 요소, 네트워크 보안 파이프라인 및 주요 개발 환경 구축 방법을 안내하는 기술 문서입니다. 

---

## 1. 프로젝트 개요 (Overview)

PowerController는 데스크톱 환경에서 컴퓨터의 전원(종료, 재시작, 절전 등)을 스케줄링하고 자동 감시할 수 있는 **하이브리드 데스크톱 웹 애플리케이션**입니다.
*   **프론트엔드**: React 19 + Vite + TypeScript + Tailwind CSS 기반의 반응형 Single Page Application (SPA).
*   **백그라운드 제어 엔진**: Python (Tkinter + Pystray + PIL) 엔진을 활용한 시스템 트레이 실행기 및 실시간 전원 제어 데몬 프로세스.
*   **데이터 지속성 아키텍처**: Windows UAC 제한을 극복하는 `%APPDATA%\PowerController\` 경로 격리 및 자동 마이그레이션 (`get_data_filepath`).
*   **원격 제어 & 보안 파이프라인**: TCP 9988 소켓 인증(`network_auth_token`), 마스터 비상 복구 키(`POWER_TIMER_MASTER_KEY`), 사전 명령어 보안 감사 로깅.
*   **배포 패키징 엔진**: Windows 표준 Inno Setup 6 (`PowerController.iss`) 및 파이썬 인스톨러(`installer.py`) 기반 다계층 강제 종료/파일 락 우회 파이프라인.
*   **라이선스 체계**: 한국어 및 영어 2종류 표준 라이선스(`STANDARD_LICENSE_KO`, `STANDARD_LICENSE_EN`, `docs/LICENSE_ko.txt`, `docs/LICENSE_en.txt`) 지원.
*   **버전 관리 표준**: Semantic Versioning 2.0.0 (MAJOR.MINOR.PATCH) 3단계 규약 준수.

---

## 2. 프로젝트 폴더 구조 (Directory Structure)

```text
├── src/                          # React + TypeScript 프론트엔드 소스코드
│   ├── components/               # 공통 재사용 컴포넌트 폴더
│   │   ├── CompactWidget.tsx     # 5종 디자인 테마 및 반응형 치수를 지원하는 상단고정 위젯
│   │   ├── StartupTodayTasksModal.tsx # 부팅/시작 시 오늘 예약 작업 브리핑 팝업 모달
│   │   ├── PowerSimulator.tsx    # 가상 전원 제어 시뮬레이터 (강제 종료 /f 배지 연동)
│   │   ├── Scheduler.tsx         # 고급 다중 규칙 스케줄러 컴포넌트 (10대 프리셋 연동)
│   │   ├── FavoritesManager.tsx  # 사용자 정의 프리셋 즐겨찾기 매니저
│   │   ├── PowerModeSelector.tsx # 전원 동작(종료/재시작/절전/화면끄기/로그아웃/알람) 선택기
│   │   └── ...
│   ├── types.ts                  # 전체 앱 공용 TypeScript 타입 정의 (DraftSettingsState 등)
│   ├── App.tsx                   # 메인 애플리케이션 상태 관리 및 뷰 조합
│   └── index.css                 # Tailwind CSS 글로벌 스타일시트 및 폰트 정의
├── assets/                       # 프로젝트 정적 자산 및 아이콘 이미지
├── native/                       # 5대 순수 창작 저수준 C/C++ 네이티브 DLL 소스
│   ├── power_core_native.c       # PowerCoreNative.dll (초정밀 타이머, 절전방지락, 무음프로세스킬러)
│   ├── net_beacon_engine.c       # NetBeaconEngine.dll (Winsock2 논블로킹 UDP 비콘 & 512 슬롯 링버퍼)
│   ├── firewall_native.cpp       # FirewallNative.dll (Windows 방화벽 COM 직결 0.05초 일괄 트랜잭션)
│   ├── sys_power_hook.c          # SysPowerHook.dll (세션 알림 감지, 배터리/UPS 위험 감시, 초고속 락)
│   └── schedule_crypto.c         # ScheduleCrypto.dll (C99 SHA-256, HMAC 디지털 서명, Salt 암호화 봉투)
├── docs/                         # 공식 기술 및 사용자 문서 폴더 (SemVer 체계)
│   ├── README.md                 # 문서 허브 및 인덱스 가이드
│   ├── patch_notes.md            # 버전별 상세 패치 내역 및 릴리즈 노트
│   ├── dll_specification.md      # 5대 순수 창작 DLL C ABI 명세 및 컴파일 가이드
│   ├── WorkLog.md                # 5단계 순수 창작 모듈화 로드맵 완료 내역 및 일자별 작업 로그
│   ├── versioning_policy.md      # Semantic Versioning 3단계 규약 및 버전 산정 기준
│   ├── security_guidelines.md    # 네트워크 통신 아키텍처 및 보안 운영 지침
│   ├── desktop_troubleshooting_guide.md # 데스크톱 앱 변경사항 미반영 원인, APPDATA 격리, 빌드 가이드
│   ├── force_close_guide.md      # 강제 종료 플래그(/f) 상세 기술 및 운영 가이드
│   ├── user_guide.md             # 일반 사용자 대상 통합 매뉴얼
│   ├── development.md            # 본 개발자 가이드 문서
│   ├── installation_guide.md     # Inno Setup 6 배포용 인스톨러 및 무인 설치 가이드
│   ├── LICENSE.md                # 오픈소스 라이선스 통합 고지서 (한/영 2종류)
│   ├── LICENSE_ko.txt            # 한국어 표준 라이선스 전문
│   └── LICENSE_en.txt            # 영문 표준 라이선스 전문
├── PowerController.iss           # Inno Setup 6 공식 윈도우 인스톨러 컴파일 스크립트
├── native_bridge.py              # 5대 DLL 동적 바인딩 및 파이썬 Graceful Fallback 이중화 레이어
├── main.py                       # Python 백그라운드 엔진 & 시스템 트레이 메인 스크립트
├── network_scheduler.py          # 독립형 원격 네트워크 스케줄러 (TCP 9988 & 즉시 전원 제어)
├── schedule_share_builder.py     # 스케줄 임베딩 무설치 동기화기 빌더
├── installer.py                  # 파이썬 셋업 마법사 (다계층 강제종료 및 한/영 라이선스 툴바)
├── version_main.txt              # Windows 바이너리 메인 버전 리소스 정의
├── version_network.txt           # Windows 바이너리 네트워크 서브시스템 버전 정의
├── version_setup.txt             # Windows 바이너리 인스톨러 버전 정의
├── build.bat                     # Inno Setup 6 자동 탐색 및 컴파일 통합 배치 파일
├── package.json                  # Node.js 패키지 의존성 및 스크립트
├── tsconfig.json                 # TypeScript 컴파일 옵션 설정
└── vite.config.ts                # Vite 번들러 설정
```

---

## 3. 핵심 아키텍처 및 연동 흐름 (System Architecture)

```
┌─────────────────────────────────────────┐          ┌─────────────────────────────────────────┐
│          React UI (프론트엔드)          │ ◄───────│    Python 데몬 및 트레이 (백그라운드)   │
│  - 실시간 타이머 및 5종 위젯 커스텀      │          │  - 시스템 API 연동 (종료, 재시작, 절전) │
│  - 환경설정 버퍼링 트랜잭션 (적용/취소) │          │  - 256x256 고해상도 트레이 아이콘       │
│  - 정각 알림 (Hourly Chime) 합성음      │          │  - TCP 9988 소켓 수신 서버               │
│  - 시작 시 오늘 예약 브리핑 모달        │          │  - JSON 영구 직렬화 스케줄 감시 데몬    │
└─────────────────────────────────────────┘          └─────────────────────────────────────────┘
```

---

## 4. 프론트엔드 주요 아키텍처 설계

### A. 환경설정 안전 버퍼링 (Settings Transaction Pipeline)
설정 창 조작 중 발생하는 불필요한 상태 전파 및 오작동을 방지하기 위해 `DraftSettingsState` 버퍼링 구조를 채택했습니다:

```typescript
// src/types.ts
export interface DraftSettingsState {
  theme: Theme;
  soundTheme: SoundTheme;
  hourlyChime: boolean;
  startupTasksAlert: boolean;
  widgetDesign: CompactWidgetDesign;
  widgetWidth: number;
  clockFontSize: number;
  timerFontSize: number;
  showCurrentTimeCompact: boolean;
  widgetOpacity: number;
  mainOpacity: number;
  selectedFont: string;
  graceSeconds: number;
  forceCloseEnabled: boolean;
}
```
*   설정 창 진입 시 현재 전역 상태를 복제하여 `draftSettings`를 초기화합니다.
*   `handleConfirmSettings` 호출 시에만 실제 전역 상태(`theme`, `widgetWidth`, `forceCloseEnabled` 등)로 커밋(Commit)되며 `localStorage`에 일괄 저장됩니다.
*   `handleCancelSettings` 호출 시 버퍼를 폐기하여 이전 설정을 100% 안전하게 보존합니다.

### B. 상단 고정 컴팩트 위젯 렌더러 (`CompactWidget.tsx`)
*   `widgetDesign` 속성에 따라 `standard`(네온 링), `cyber`(사이버 HUD), `slim`(슬림 바), `retro`(레트로 LED), `minimal`(클린 카드) 5종의 서로 다른 렌더링 파이프라인을 분기 실행합니다.
*   인라인 스타일을 통해 `widgetWidth`, `clockFontSize`, `timerFontSize`를 실시간으로 가변 바인딩하여 픽셀 단위 렌더링 왜곡 없는 최적의 타이포그래피 비율을 유지합니다.

### C. 사운드 합성 엔진 (Web Audio API & Hourly Chime)
*   외부 오디오 파일 없이 `window.AudioContext`를 사용하여 주파수 오실레이터(`OscillatorNode`)와 게인 엔벨로프(`GainNode`)로 음향을 직접 실시간 합성합니다.
*   **정각 알림 차임벨 (`playHourlyChimeSound`)**:
    *   E5(659.25Hz) ➔ C5(523.25Hz) ➔ D5(587.33Hz) ➔ G4(392.00Hz)로 이어지는 4음계 웨스트민스터 차임 리프를 감쇠 합성하여 재생합니다.

### D. 강제 종료 플래그 (`/f`) 및 프로세스 보호 파이프라인
*   **Python**: `self.force_close_enabled` 변수로 전역 플래그를 관리하며, `shutdown /s /f /t 2` 또는 `shutdown /r /f /t 2` 형태로 시스템 호출을 조립합니다.
*   **React**: 타이머 화면 퀵 체크박스, 환경설정 모달, 가상 시뮬레이터 배지 간의 삼중 동기화 구조를 갖추어 일관된 UX를 제공합니다.

### E. 개발 서버 포트 커스터마이징 및 충돌 방지 (`server.ts`)
*   `process.env.CUSTOM_PORT` 환경변수를 우선 참조하여 포트 3000 충돌 시에도 4000, 5000 등 원하는 포트로 Vite 개발 서버를 즉시 기동할 수 있습니다.
*   `package.json`의 `"dev:4000"`, `"dev:5000"` 스크립트로 원클릭 실행을 지원합니다.

### F. 번들 최적화 및 코드 스플리팅 (`vite.config.ts`)
*   `manualChunks` 설정을 통해 `react`/`react-dom`을 `vendor-react.js`(9.6KB)로, `lucide-react`를 `vendor-icons.js`(42KB)로 독립 분할.
*   프로덕션 번들에서 디버깅 소스맵을 배제(`sourcemap: false`)하여 로딩 속도와 보안성 동시 향상.

### G. 단일 원천(Single Source of Truth) 버전 자동 동기화 (`scripts/sync_version.py`)
*   `package.json`의 `"version"`을 유일한 기준 버전으로 삼아 `main.py`, `installer.py`, `network_scheduler.py`, `index.html`, `PowerController.iss`의 버전을 일괄 정합 동기화.

### H. GitHub Releases 실시간 업데이트 배너 (`GitHubUpdateBanner.tsx`)
*   GitHub REST API(`https://api.github.com/repos/AhBiYout/PowerController/releases/latest`)를 비동기 호출하여 신규 릴리즈 발견 시 상단 알림 바 및 다운로드 모달 렌더링.

---

## 5. 빌드 및 배포 절차

```bash
# 1. 의존성 설치 및 린트 검증
npm install
npm run lint

# 2. 프로덕션 빌드 (Vite SPA + esbuild Server)
npm run build

# 3. 3대 플랫폼(PC Windows, Android APK, iPhone iOS IPA) 일괄 빌드
python scripts/build_packages.py

# 4. Windows Inno Setup 인스톨러 컴파일
build.bat

# 5. GitHub Releases 원클릭 자동 업로드 및 태깅 푸시
push_to_github.bat      # Windows
python github_sync.py   # Python 크로스플랫폼
```

---

## 6. 버전 관리 및 패치노트 자동화 규칙

*   코드 수정 시 **Semantic Versioning** 규칙에 따라 `MAJOR.MINOR.PATCH` 단계를 판별합니다.
*   `package.json`의 버전을 변경한 후 `python scripts/sync_version.py`를 실행하여 프로젝트 전반의 버전 리소스를 일괄 갱신합니다.
*   `docs/patch_notes.md`, `docs/WorkLog.md` 및 `docs/GITHUB_GUIDE.md`의 최신 변경 이력을 상호 동기화합니다.
