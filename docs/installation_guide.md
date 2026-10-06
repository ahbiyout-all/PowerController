# PowerController 설치 및 패키징 가이드 (Inno Setup 6 Packaging Guide)

본 문서는 **PowerController v2.9.1**의 배포용 인스톨러 생성 및 **Inno Setup 6** 기반 소프트웨어 패키징, 레지스트리 자동 등록, 무인 설치(Silent Install), 프로세스 강제 종료 락 해제 및 클린 언인스톨 파이프라인에 대한 엔지니어링 가이드입니다.

---

## 🛠 1. 배포 패키지 아키텍처 (Inno Setup 6 & Python Wizard)

PowerController 배포 시스템은 전 세계 소프트웨어 배포 표준인 **Inno Setup 6 (`PowerController.iss`)** 및 크로스플랫폼 파이썬 셋업 마법사(`installer.py`)를 통해 최고 수준의 설치 안정성과 엔터프라이즈 무인 배포 역량을 제공합니다.

### 🌟 인스톨러 핵심 엔지니어링 특징
1. **극대화된 압축률 (LZMA2/Ultra64 Solid)**: 고효율 압축을 통해 다운로드 크기를 최소화하고 초고속 압축 해제를 실현.
2. **폴더 풀림(Unpacked Multi-File) 개별 파일 설치 구조 (v2.9.1)**:
   - PyInstaller `--onedir` 빌드 결과물인 `dist\PowerController\*` 폴더 트리와 서브디렉터리(`_internal/`, DLL, `.pyd`, 리소스 등)를 압축 해제 시 개별 파일 형태로 온전히 설치하도록 구현.
   - 메인 프로그램뿐만 아니라 커맨더(`PowerNetworkScheduler.exe`), 스케줄 주입기(`ApplySharedSchedules.exe`), `Register_Firewall_Rules.bat`, 다국어 `docs/` 라이선스 문서 트리가 모두 개별 파일로 깨끗하게 전개.
   - **5대 순수 창작 네이티브 DLL 자동 번들링**: `PowerCoreNative.dll`, `NetBeaconEngine.dll`, `FirewallNative.dll`, `SysPowerHook.dll`, `ScheduleCrypto.dll` 및 `native_bridge.py`가 프로그램 디렉터리에 완벽하게 설치.
3. **기존 앱 설치 감지 시 삭제(클린)/덮어쓰기(업그레이드) 사용자 확인 분기 (v2.9.1)**:
   - 시스템에 이전 버전이 이미 설치되어 있는 경우 대화상자를 표출하여 **"기존 버전을 먼저 완전히 삭제하고 새로 설치(Clean Install)"**할 것인지, **"기존 설정 및 파일 위에 덮어쓰기(Overwrite/Upgrade)"**할 것인지 물어보고 진행.
   - 무인 설치(`/SILENT`, `/VERYSILENT`) 시에는 기본적으로 무중단 덮어쓰기로 안전 진행되며, `/CLEAN` 매개변수 전달 시 완전 무음 언인스톨 후 새로 설치.
4. **공식 다국어 및 2종류 라이선스 연동 (v2.9.1)**:
   - 한국어 선택 시 `docs\LICENSE_ko.txt`, 영어 선택 시 `docs\LICENSE_en.txt`가 설치 마법사에 네이티브로 자동 바인딩.
   - 파이썬 셋업 마법사(`installer.py`) 1단계 화면 상단에 `[ 🇰🇷 한국어 ]` / `[ 🇺🇸 English ]` 실시간 언어 전환 툴바 탑재.
5. **원격 무인 설치 시 프로세스 미종료 및 파일 락(Hang) 원천 차단 (v2.9.1)**:
   - 원격 배포 도구(GPO, Intune, PsExec)로 무인 설치(`/VERYSILENT /NORESTART` 또는 `--silent`) 시, 기존 트레이 백그라운드 프로세스가 잡고 있는 파일 락(`ERROR_SHARING_VIOLATION`)을 방지하기 위해 **다계층 강제 종료(`taskkill /F /T`, PowerShell, WMIC, TCP QUIT)** 및 **임시 파일 이름 변경(`.old_XXXX`) 락 우회** 기법을 선제 가동.
6. **Windows 제어판 및 설정 앱 완벽 연동**: 표준 `unins000.exe`가 생성되어 제어판 '프로그램 추가/제거' 및 Windows 10/11 '설치된 앱'에 정식 아이콘, 버전, 게시자(`cisnet.co.kr`), 설치 위치, 링크가 깔끔하게 등록.
7. **Windows Defender Firewall 사전 무음 등록 (메인 & 커맨더 버전 표기 명칭 포함, v2.9.1)**:
   - 프로그램 실행 전 설치 단계(`ssPostInstall`)에서 관리자 권한을 활용하여 **메인(`PowerController.exe`) 및 커맨더(`PowerNetworkScheduler.exe`) 2개 프로그램 모두**와 전용 통신 포트(TCP 9988, UDP 9985, UDP 9986)를 Windows 방화벽에 사전에 조용히(`SW_HIDE`) 자동 등록.
   - 버전 정보가 붙은 이름(`PowerController v2.9.1`, `PowerNetworkScheduler v2.9.1`)도 함께 등록하여 첫 실행 시 공용 네트워크 보안 경고창이 일절 뜨지 않도록 사전 원천 차단.

---

## 🚀 2. 인스톨러 컴파일 및 빌드 방법

### 빌드 전제 조건
* **Windows OS 환경**
* **Python 3.8+** 및 필수 라이브러리: `pip install pyinstaller pystray pillow`
* **Inno Setup 6**: [공식 다운로드 페이지 (https://jrsoftware.org/isdl.php)](https://jrsoftware.org/isdl.php)에서 무료 다운로드 및 설치
  *(기본 설치 경로: `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`)*

### 방법 A: 통합 빌드 스크립트 (`build.bat`) 사용 (가장 추천)
프로젝트 루트 폴더에서 `build.bat`을 실행합니다.

```text
===============================================================================
           PowerController - Automated Build & Packaging Suite
                  Publisher: cisnet.co.kr | Author: AhBiYout
===============================================================================
[*] Target Version Detected: v2.8.0
[*] Semantic Version Rule: MAJOR.MINOR.PATCH

 [SELECT BUILD OPTION]
 1. Build Application and Inno Setup 6 Installer (App + Setup Wizard)
 2. Build Standalone Network Remote Scheduler (PowerNetworkScheduler.exe)
 3. Build One-Click Offline Schedule Share Injector (ApplySharedSchedules.exe)
 4. Build All Components at Once (All-in-One Complete Suite)
 5. Clean Temporary Build Files and Artifacts (build/, dist/, *.spec)
 6. Exit Builder
===============================================================================
```

* 콘솔에서 `1` (기본값) 또는 `4` (전체 빌드)를 선택하면:
  1. `PyInstaller`를 통해 독립 앱 폴더(`dist\PowerController\`)를 컴파일합니다.
  2. 시스템에 설치된 `ISCC.exe`를 자동 탐지합니다.
  3. `PowerController.iss` 스크립트를 컴파일하여 최종 인스톨러인 **`dist\PowerController_Setup_v2.9.1.exe`**를 원클릭으로 생성합니다.

### 방법 B: Inno Setup 컴파일러 CLI 직접 실행
이미 `dist\PowerController\` 앱 폴더가 생성되어 있다면, 명령 프롬프트(CMD)에서 직접 인스톨러를 컴파일할 수 있습니다:
```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DMyAppVersion=2.9.1 PowerController.iss
```

---

## 📦 3. Inno Setup 6 스크립트 (`PowerController.iss`) 구성 내역

* **`[Setup]` 섹션**:
  * `AppId`: 고유 GUID (`{5A8C9B23-7F12-4D39-8C92-E6B3C0F59871}`) 부여로 중복/충돌 방지.
  * `DefaultDirName={autopf}\PowerController`: 64비트 Windows의 경우 `C:\Program Files\PowerController`에 자동 설치.
  * `Compression=lzma2/ultra64` 및 `SolidCompression=yes`: 최상급 압축 효율.
  * `AppMutex=PowerController_SingleInstance_Mutex`: 설치/업그레이드 중 인스턴스 충돌 방지.
* **`[Languages]` 섹션**:
  * 한국어(`compiler:Languages\Korean.isl`) 및 영어(`compiler:Default.isl`) 내장.
* **`[Tasks]` 섹션**:
  * `desktopicon`: 바탕 화면에 바로가기 아이콘 생성 (기본 체크).
  * `startupicon`: Windows 시작 시 자동 실행 등록 (선택 옵션).
* **`[Run]` 섹션**:
  * `Flags: nowait postinstall skipifsilent`: 설치 완료 화면에서 "PowerController 지금 바로 실행하기" 옵션 제공.

---

## 🤫 4. CLI 무인 자동 설치 (Silent & Unattended Installation)

사내 망관리자, 그룹 정책(GPO), 또는 배치 스크립트를 통해 사용자 개입 없이 백그라운드에서 자동으로 프로그램을 배포할 수 있습니다.

### 1) 진행 표시줄만 표시하는 자동 설치 (`/SILENT`)
```cmd
PowerController_Setup_v2.9.1.exe /SILENT /NORESTART
```

### 2) 화면 표시가 전혀 없는 완전 무인 설치 (`/VERYSILENT`)
```cmd
PowerController_Setup_v2.9.1.exe /VERYSILENT /NORESTART
```

### 3) 사용자 정의 설치 디렉터리 지정 (`/DIR`)
```cmd
PowerController_Setup_v2.9.1.exe /VERYSILENT /DIR="D:\Tools\PowerController"
```

### 4) 바로가기 및 시작 프로그램 옵션 지정 (`/TASKS`)
```cmd
# 바탕화면 바로가기만 생성하고 시작 프로그램 등록은 제외
PowerController_Setup_v2.9.1.exe /VERYSILENT /TASKS="desktopicon"

# 바탕화면 바로가기 및 시작 프로그램 둘 다 자동 등록
PowerController_Setup_v2.9.1.exe /VERYSILENT /TASKS="desktopicon,startupicon"
```

### 5) 설치 로그 파일 기록 (`/LOG`)
```cmd
PowerController_Setup_v2.9.1.exe /VERYSILENT /LOG="C:\Temp\powercontroller_install.log"
```

### 6) 기존 버전 완전 삭제 후 무인 클린 재설치 (`/CLEAN=1`)
```cmd
# 기존에 설치된 이전 버전을 백그라운드에서 완전히 삭제 후 깨끗하게 새로 설치
PowerController_Setup_v2.9.1.exe /VERYSILENT /NORESTART /CLEAN=1
```

---

## 🗑️ 5. 클린 언인스톨 및 무인 제거 (Silent Uninstallation)

PowerController가 설치되면 설치 디렉터리에 공식 제거 도구인 **`unins000.exe`**가 자동 생성됩니다.

### 1) 제어판을 통한 일반 제거
* Windows 설정 > 앱 > **설치된 앱** 또는 **제어판 > 프로그램 추가/제거**에서 `PowerController`를 찾아 [제거]를 클릭합니다.

### 2) CLI 무인 자동 제거 (Silent Uninstall)
```cmd
# 대화상자 없이 자동 언인스톨 수행
"C:\Program Files\PowerController\unins000.exe" /SILENT

# 완전 무인 백그라운드 언인스톨 수행
"C:\Program Files\PowerController\unins000.exe" /VERYSILENT
```
언인스톨 시 프로그램 실행 파일, 생성된 임시 파일(`.tmp`), 로그 파일(`.log`)이 완벽하게 제거되며, 사용자의 고유 설정(`%APPDATA%\PowerController`)은 보존되어 추후 재설치 시에도 기존 설정을 안전하게 이어서 사용할 수 있습니다.

---

## 🏷️ 6. Windows 파일 속성 '자세히' 탭 메타데이터 명세 (File Properties Details)

Windows 탐색기에서 생성된 실행 파일(`.exe`)을 마우스 우클릭한 후 **[속성] > [자세히]** 탭을 클릭했을 때 표시되는 정식 파일 리소스 메타데이터 명세입니다. 다국어(한국어 1042 / 영어 1033)를 완벽 지원합니다.

### 📌 1) 메인 애플리케이션: `PowerController.exe` (`version_main.txt`)

| 속성 항목 (Property) | 한국어 환경 (041204B0) | 영문 환경 (040904B0) |
| :--- | :--- | :--- |
| **파일 설명 (File description)** | `PowerController - 스마트 시스템 전원 및 자동 종료 예약 제어기` | `PowerController - Smart Shutdown & Power Management Agent` |
| **형식 (Type)** | `응용 프로그램 (.exe)` | `Application (.exe)` |
| **파일 버전 (File version)** | `2.9.1.0` | `2.9.1.0` |
| **제품 이름 (Product name)** | `PowerController - 스마트 시스템 전원 제어기` | `PowerController - Smart Shutdown Agent` |
| **제품 버전 (Product version)** | `2.9.1.0` | `2.9.1.0` |
| **저작권 (Copyright)** | `Copyright (c) 2026 AhBiYout. All rights reserved.` | `Copyright (c) 2026 AhBiYout. All rights reserved.` |
| **언어 (Language)** | `한국어(대한민국)` [0412] / `영어(미국)` [0409] | `English (United States)` / `Korean` |
| **원본 파일 이름 (Original filename)** | `PowerController.exe` | `PowerController.exe` |
| **내부 이름 (Internal name)** | `PowerController` | `PowerController` |
| **회사 (Company)** | `cisnet.co.kr` | `cisnet.co.kr` |
| **합법적 상표 (Legal trademarks)** | `PowerController™ (AhBiYout)` | `PowerController is a trademark of AhBiYout.` |
| **설명 / 주석 (Comments)** | `Windows 시스템 전원 자동 종료, 재시작, 절전, 정각 알림(Hourly Chime), 부팅 브리핑, 스케줄러, 상단고정 미니 위젯 5종 테마 및 원격 네트워크 제어를 지원하는 고성능 스마트 전원 관리 유틸리티입니다.` | `Smart Windows Power & Shutdown Controller with Mini Widget, Hourly Chime, Scheduler and Remote Network Manager.` |

### 📌 2) Inno Setup 6 설치 관리자: `PowerController_Setup_v2.9.1.exe` (`PowerController.iss`)

| 속성 항목 (Property) | 설정 값 (Value) |
| :--- | :--- |
| **파일 설명 (File description)** | `PowerController - 스마트 시스템 전원 및 자동 종료 예약 제어기 설치 마법사` |
| **형식 (Type)** | `응용 프로그램 (.exe)` |
| **파일 버전 (File version)** | `2.9.1.0` |
| **제품 이름 (Product name)** | `PowerController - Smart Shutdown Agent` |
| **제품 버전 (Product version)** | `2.9.1.0` |
| **저작권 (Copyright)** | `Copyright (c) 2026 AhBiYout. All rights reserved.` |
| **원본 파일 이름 (Original filename)** | `PowerController_Setup_v2.9.1.exe` |
| **회사 (Company)** | `cisnet.co.kr` |

### 📌 3) 원격 네트워크 스케줄러: `PowerNetworkScheduler.exe` (`version_network.txt`)

| 속성 항목 (Property) | 한국어 환경 (041204B0) | 영문 환경 (040904B0) |
| :--- | :--- | :--- |
| **파일 설명 (File description)** | `PowerController - 독립형 원격 네트워크 스케줄 관리기` | `PowerController - Standalone Network Remote Scheduler` |
| **파일 버전 (File version)** | `2.9.1.0` | `2.9.1.0` |
| **제품 이름 (Product name)** | `PowerController - 원격 네트워크 스케줄 관리기` | `PowerController - Network Remote Scheduler` |
| **제품 버전 (Product version)** | `2.9.1.0` | `2.9.1.0` |
| **저작권 (Copyright)** | `Copyright (c) 2026 AhBiYout. All rights reserved.` | `Copyright (c) 2026 AhBiYout. All rights reserved.` |
| **원본 파일 이름 (Original filename)** | `PowerNetworkScheduler.exe` | `PowerNetworkScheduler.exe` |
| **내부 이름 (Internal name)** | `PowerNetworkScheduler` | `PowerNetworkScheduler` |
| **회사 (Company)** | `cisnet.co.kr` | `cisnet.co.kr` |
| **설명 / 주석 (Comments)** | `로컬 네트워크(LAN) 상의 PC들에 전원 종료/재시작 스케줄 규칙을 원격으로 전송하고 동기화하는 독립 실행 도구입니다.` | `Standalone tool to broadcast and synchronize power management schedules over local network PCs.` |

### 📌 4) 오프라인 스케줄 주입기: `ApplySharedSchedules.exe` (`version_share.txt`)

| 속성 항목 (Property) | 한국어 환경 (041204B0) | 영문 환경 (040904B0) |
| :--- | :--- | :--- |
| **파일 설명 (File description)** | `PowerController - 원클릭 오프라인 스케줄 공유 주입기` | `PowerController - One-Click Offline Schedule Injector` |
| **파일 버전 (File version)** | `2.9.1.0` | `2.9.1.0` |
| **제품 이름 (Product name)** | `PowerController - 스케줄 주입기` | `PowerController - Schedule Injector` |
| **제품 버전 (Product version)** | `2.9.1.0` | `2.9.1.0` |
| **저작권 (Copyright)** | `Copyright (c) 2026 AhBiYout. All rights reserved.` | `Copyright (c) 2026 AhBiYout. All rights reserved.` |
| **원본 파일 이름 (Original filename)** | `ApplySharedSchedules.exe` | `ApplySharedSchedules.exe` |
| **내부 이름 (Internal name)** | `ApplySharedSchedules` | `ApplySharedSchedules` |
| **회사 (Company)** | `cisnet.co.kr` | `cisnet.co.kr` |
| **설명 / 주석 (Comments)** | `마스터 전원 관리 스케줄 규칙을 내장하여 다른 PC에 원클릭으로 주입하고 자동 동기화하는 도구입니다.` | `One-click portable utility with embedded schedule rules to automatically configure remote/offline computers.` |

---

## 🛡️ 7. 포터블(무설치) 환경을 위한 원클릭 방화벽 등록 도구 (`Register_Firewall_Rules.bat`)

인스톨러를 거치지 않고 압축 파일(.zip)을 해제하여 사용하는 포터블 환경이거나, 회사/학교 등 엄격한 네트워크 보안 정책 환경에서 방화벽 예외를 사전에 수동 승인하고자 할 때 사용하는 스크립트입니다.

### 📌 동작 방식
1. **관리자 권한(Elevation) 자동 요청**: 일반 사용자로 실행 시 자동으로 UAC 관리자 권한 확인 창을 호출합니다.
2. **2종 프로그램 및 전용 포트 일괄 등록**:
   * `PowerController.exe`: Inbound & Outbound 규칙 (`profile=any`)
   * `PowerNetworkScheduler.exe`: Inbound & Outbound 규칙 (`profile=any`)
   * `TCP 9988`: 원격 스케줄 제어 수신 포트
   * `UDP 9985`: 로컬 LAN 자동 탐색 브로드캐스트 포트
3. **사용 방법**:
   * 프로그램 폴더에 위치한 `Register_Firewall_Rules.bat` 파일을 마우스 우클릭 후 **[관리자 권한으로 실행]**을 선택합니다.
   * 1~2초 이내에 모든 규칙이 자동으로 등록되며, 이후 메인 및 커맨더 앱을 실행할 때 "공용 네트워크 액세스 허용" 보안 팝업이 일절 발생하지 않습니다.

---

## 💻 8. PC (Windows) 패키지 빌더 및 GitHub Actions CI/CD 자동 배포 (`scripts/build_packages.py`)

### 1) PC (Windows) 공식 패키징 파이프라인
프로젝트에 내장된 패키저(`python scripts/build_packages.py`)를 통해 PC (Windows) 배포 파일을 신속하고 안전하게 생성합니다:

| 대상 플랫폼 | 산출물 경로 | 용량 | 패키지 구성 및 설치 방식 |
| :--- | :--- | :--- | :--- |
| 💻 **PC (Windows)** | `build_output/pc/PowerController-v2.9.1-Windows.zip` | 약 4.0MB | Inno Setup 설치 마법사 소스(`.iss`), Python 메인 엔진, 5대 네이티브 DLL, 웹 대시보드 산출물, 방화벽 등록 스크립트 |

* 모바일(스마트폰/태블릿)에서는 웹 브라우저 접속을 통해 실시간 반응형 원격 리모컨(PWA)으로 침대나 외부에서 PC 전원을 원격으로 제어할 수 있습니다.

### 2) 배포 파일 크기 무손실 최적화 (Size Dieting)
* **Inno Setup**: `Compression=lzma2/ultra64`, `SolidCompression=yes`를 적용하여 원본 바이너리를 30~40% 추가 압축.
* **ZIP 패키저**: Python zlib 최고 압축률인 `compresslevel=9`를 적용하여 전송 용량 최소화.
* **Vite Web Bundle**: `manualChunks`를 통해 `vendor-react`(9.6KB) 및 `vendor-icons`(42KB)로 청크 분할 및 프로덕션 소스맵 배제.

### 3) GitHub Actions CI/CD 자동 릴리스 워크플로 (Node.js 22 LTS)
* **`.github/workflows/release.yml`**:
  * GitHub의 최신 정책에 따라 **Node.js 22 LTS** 런타임 적용 완료 (Node 20 EOL 경고 원천 차단).
  * `git tag -a v2.9.1` 푸시 시 Windows Runner에서 자동 빌드 수행 후 [GitHub Releases](https://github.com/ahbiyout-all/PowerController/releases)에 자동 등록.

### 4) GitHub 원클릭 자동 동기화 및 릴리스 도구
* **`push_to_github.bat`** (Windows 원클릭 실행 - 원격 히스토리 `--force` 자동 동기화 및 태그 갱신 내장 ⭐)
* **`github_sync.py`** (Python 기반 크로스플랫폼 동기화 엔진)
* **`push_to_github.ps1`** (PowerShell 전용) / **`push_to_github.sh`** (Mac / Linux 전용)
* 실행 시 `package.json`의 버전(`v2.9.1`)을 자동으로 파싱하여 Git 태그(`v2.9.1`) 생성 및 GitHub Releases로 즉시 자동 전송됩니다.




