# PowerController v2.9.2
> **Windows 시스템 전원 자동 오프 제어기 & 사내망 원격 예약·디바이스 제어 타워**  
> **Smart PC Auto Power, Device Controller & Remote Shutdown Management Center**

---

## 📌 제작자 및 공식 채널 안내 (Author & Official Channels)

| 구분 | 정보 | 링크 / 주소 |
| :--- | :--- | :--- |
| **개발자 (Author)** | **AhBiYout** | - |
| **GitHub 계정** | **AhBiYout-all** | [https://github.com/AhBiYout-all](https://github.com/AhBiYout-all) |
| **공식 GitHub 저장소** | **PowerController** | [https://github.com/AhBiYout-all/PowerController](https://github.com/AhBiYout-all/PowerController) |
| **공식 구글 블로그** | AhBiYout Tech Blog | [https://ahbiyoutvibe.blogspot.com/](https://ahbiyoutvibe.blogspot.com/) |
| **소속사 (Affiliation)**| (주)씨아이에스넷 (CISNet) | [https://www.cisnet.co.kr](https://www.cisnet.co.kr) |

---

## ✨ 핵심 기능 요약 (Core Features)

1. **GitHub Releases 기반 실시간 자동 업데이트 시스템**:
   - `https://api.github.com/repos/AhBiYout-all/PowerController/releases/latest` API 실시간 폴링.
   - 신규 릴리스 배포 시 상단 알림 배너 및 업데이트 팝업창(`UpdateModal`) 자동 실행.
   - 원클릭 공식 인스톨러 다운로드, 깃허브 경로 확인, 버전 비교, 패치 내역 안내.
2. **50대 컴퓨터실 통합 원격 관제 타워 (`Lab Fleet 50` & `PowerNetworkScheduler`) · 개별 제어판 (`DeviceController`)**:
   - 5/8/10열 좌석 배치 그리드 뷰와 상세 목록 뷰 전환, IP 대역 스캔, RFC-4180 CSV 좌석 일괄 등록, 24스레드 병렬 전송 및 실패 PC 원클릭 재시도, 교시별 프로필 일괄 배포, 순차 Wake-on-LAN(WOL) 기상 및 15초 실시간 생존·타이머 폴링 탑재.
   - 웹·데스크톱 네이티브 뷰·독립형 Python 전송기 모두에서 **종료(Shutdown), 재시작(Restart), 절전(Sleep), 화면끔(Screen Off), 비상 알람(Alarm)**을 개별 또는 일괄 원격 즉시 실행 (TCP 9988).
3. **12대 순수 창작 저수준 C/C++ 네이티브 DLL 엔진 (`PowerExecNative.dll` 포함)**:
   - 외부 런타임 의존성 없는 순수 C99/C++/Win32 COM 기반 12대 DLL(`PowerExecNative`, `PowerCoreNative`, `NetBeaconEngine`, `FirewallNative`, `SysPowerHook`, `ScheduleCrypto`, `DiskFlushNative`, `AudioDimmerNative`, `DisplayDdcNative`, `LowLevelInputIdleNative`, `CommanderTcpDispatcherNative`, `CommanderPingScannerNative`) 및 Python Graceful Fallback 브리지(`native_bridge.py`) 탑재 ([상세 아키텍처](./docs/pure_custom_dll_architecture.md), [C ABI 명세서](./docs/dll_specification.md)).
4. **브라우저/OS 언어 자동 감지 & 동적 다국어 스크립트 생성**:
   - 최초 진입 시 브라우저/OS 언어(`KO`/`EN`)를 자동 감지(`auto` / `manual` 전환 및 `Auto Reset` 지원)하고, 웹 대시보드·데스크톱 네이티브 뷰·독립형 네트워크 스케줄러는 물론 생성되는 **Python/Inno Setup 스크립트 주석 및 레이블까지 동적 다국어 갱신** (`scriptGenerators.ts`).
5. **4대 테마 고대비 가독성 & 5종 컴팩트 플로팅 위젯**:
   - 다크(`dark`), 그레이(`gray`), 화이트(`white`), 베이지(`beige`) 4종 테마 전반(데스크톱 뷰, 컴팩트 위젯, 모달/차트)의 고대비 시인성 완벽 확보.
   - `Standard Neon Ring`, `Cyber HUD`, `Minimal Slim Bar`(플로팅 설정 드로어 포함), `Retro LED`, `Clean Card` 5종 위젯 디자인 실시간 전환.
6. **단일 출처 버전 동기화 (Single Source of Truth, SSOT)**:
   - `package.json`의 버전을 기준으로 소스코드(`src/types.ts`, `main.py`, `network_scheduler.py`, `installer.py`), `index.html`, Inno Setup 스크립트(`PowerController.iss`), 패치노트(`docs/PATCHNOTES.md`), Windows 버전 리소스(`version_*.txt`)가 100% 자동 동기화 (`scripts/sync_version.py`).
7. **Inno Setup 6 표준 6단계 설치 마법사 & 프로그램 추가/제거 정식 등록**:
   - **표준 6단계 설치 흐름**: `기존 실행 앱 강제 종료` → `기존 설치 감지 시 삭제/덮어쓰기 질의` → `라이선스 선언(KO/EN)` → `설치(Unpacked Multi-File & 12대 DLL)` → `완료 화면 바탕화면 바로가기 체크` → `앱 실행`.
   - **Windows 프로그램 추가/제거 정식 등록 및 무인 설치**: `Uninstallable=yes` / `CreateUninstallRegKey=yes` 정식 등록, `/SILENT`, `/VERYSILENT`, `/SUPPRESSMSGBOXES`, `/CLEAN=1` 완벽 지원.
   - **Windows Defender 방화벽 무음 사전 등록**: 메인(`PowerController`), 커맨더(`PowerNetworkScheduler`), 버전 표기 규칙(`PowerController v2.9.2`) 및 통신 포트(TCP 9988, UDP 9985, UDP 9986) 자동 등록·제거.
8. **오디오 엔진 & 헤더 음소거**:
   - Pixabay 선별 7대 프리미엄 사운드 테마(`classic`, `marimba`, `crystal`, `scifi`, `westminster`, `urgent`, `bubble`).
   - 메인 헤더 및 데스크톱 툴바에 전용 **Mute All (음소거 0% / 원복)** 원클릭 토글 탑재.

---

## 🛠️ 개발 및 빌드 환경 (Build & Development)

### 1. 전제 조건 (Prerequisites)
- **Node.js**: v22 LTS (권장) 또는 v24 (GitHub Actions Runner EOL 대응)
- **Python**: v3.11 이상
- **Inno Setup**: v6.2 이상 (`ISCC.exe` 시스템 PATH 등록)

### 2. 로컬 실행 (Run Locally)
```bash
# 의존성 패키지 설치
npm install

# 개발 서버 실행
npm run dev
```

### 3. Windows 공식 설치 파일 패키징 (Build Windows Installer)
```bash
# Windows Inno Setup 6 공식 인스톨러 빌드
python scripts/build_packages.py
```
* 빌드 결과물 (`release_assets/`):
  * `PowerController_Setup_v2.9.2.exe`

---

## 🚀 GitHub 자동 푸시 및 릴리스 배포 (Auto Push & Release)

Windows 환경에서는 루트 경로의 `push_to_github.bat`을 더블 클릭하여 원클릭 자동 배포를 수행할 수 있습니다:

```cmd
push_to_github.bat
```

* **파이프라인 동작 과정**:
  1. `package.json` (또는 `docs/PATCHNOTES.md`)에서 동적으로 앱 버전 `%APP_VER%` 추출.
  2. 개인정보 및 개인 이메일 유출 사전 점검 (`AhBiYout-all <ahbiyout-all@users.noreply.github.com>` 규격 적용).
  3. Git Add -> Commit (`Release v%APP_VER%`) -> Tag (`v%APP_VER%`) -> Remote Push (`main`).
  4. GitHub Actions가 트리거되어 Node.js 22 LTS 환경에서 Inno Setup 인스톨러를 빌드하고, GitHub Releases에 **오직 공식 설치 파일만 첨부**합니다.

---

## 📄 라이선스 (License)

Copyright (c) 2026 **AhBiYout**. All rights reserved.  
본 소프트웨어는 [MIT License](docs/LICENSE_ko.txt)에 따라 자유롭게 사용 및 배포할 수 있습니다.
