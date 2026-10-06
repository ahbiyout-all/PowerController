# 🚀 GitHub 원클릭 자동 업로드 및 실시간 릴리스 배포 가이드

본 프로젝트는 **GitHub Releases 기반 실시간 자동 업데이트 시스템** 및 **동적 버전 추출 파이프라인(Single Source of Truth)**을 탑재하여, 코드를 푸시할 때마다 항상 최신 버전 태그와 연동되어 배포됩니다.

---

## 📌 공식 계정 및 원격 저장소 정보

| 항목 | 설정값 | 설명 |
| :--- | :--- | :--- |
| **GitHub 계정 (Username)** | **`ahbiyout-all`** | 사용자 GitHub 계정 ID (Owner) |
| **Git 작성자 이름 (Author)** | **`AhBiYout-all`** | Git 커밋 시 기록되는 공식 사용자 표시명 |
| **Git 등록 이메일 (보안 전용)** | **`ahbiyout-all@users.noreply.github.com`** | 🔒 개인정보 완벽 보호 & 스팸 봇 차단 공식 이메일 |
| **원격 저장소 (Remote URL)** | `https://github.com/ahbiyout-all/PowerController.git` | GitHub 원격 저장소 주소 |
| **기본 브랜치 (Default Branch)** | `main` | 기본 메인 배포 브랜치 |
| **현재 앱 버전 (Dynamic Version)** | **`v2.9.1`** | `package.json`에서 자동 파싱 (Single Source of Truth) |

---

## 🏷️ 소프트웨어 버전 관리(Semantic Versioning) 3단계 원칙

본 프로젝트는 **Semantic Versioning 2.0.0 (MAJOR.MINOR.PATCH)** 규약에 따라 변경 규모에 맞춰 3단계로 명확히 분리하여 버전을 관리합니다:

$$\mathbf{MAJOR}.\mathbf{MINOR}.\mathbf{PATCH}$$

1. **1️⃣ MAJOR (X.0.0)**:
   - **하위 호환성 파괴 (Breaking Changes)** / 대규모 아키텍처 및 통신 프로토콜 개편
   - 승격 시 MINOR, PATCH를 `0`으로 리셋 (예: `v1.9.0` ➔ `v2.0.0`)
2. **2️⃣ MINOR (x.Y.0)**:
   - **하위 호환성 100% 유지** / 신규 주요 기능(Features), 독립 편의 도구, UI 대규모 모듈 추가
   - 승격 시 PATCH를 `0`으로 리셋 (예: `v2.8.0` ➔ `v2.9.0`)
3. **3️⃣ PATCH (x.y.Z)**:
   - **하위 호환성 100% 유지** / 버그 수정(Fixes), 핫픽스, 텍스트 교정, 스타일 미세 조정, 리소스 최적화
   - PATCH 번호만 1 증가 (예: `v2.9.0` ➔ `v2.9.1`)

---

## 🔄 코드 수정 시 "버전 정보 자동 연동" 메커니즘

1. **버전 단일 원천 (Single Source of Truth)**:
   - `package.json`의 `"version"` 필드가 앱 전체의 기준 버전이 됩니다.
   - 프로젝트 내 일괄 동기화 도구 `python scripts/sync_version.py`가 있어 `main.py`, `installer.py`, `network_scheduler.py`, `index.html`, `PowerController.iss`의 버전을 한 번에 동기화할 수 있습니다.
2. **원클릭 스크립트 실행 시 자동 처리 내역**:
   - `push_to_github.bat`, `push_to_github.ps1`, `github_sync.py`가 실행될 때 최신 버전을 자동으로 읽어와 커밋 메시지와 콘솔 타이틀에 반영합니다 (`Release vX.Y.Z`).
   - 로컬 Git 태그를 검사하여 `vX.Y.Z` 태그를 생성 및 갱신합니다.
   - `git push -u origin main --force` 과 동시에 **`git push origin vX.Y.Z --force` 태그까지 GitHub 서버로 안전 전송**합니다.
3. **GitHub Actions 자동 빌드 및 릴리스 (`.github/workflows/release.yml`)**:
   - 코드가 푸시되면 GitHub Windows Runner에서 **PyInstaller 단일 실행파일(.exe)** 및 **Inno Setup 6 정식 설치 프로그램(.exe)**을 즉시 컴파일하고 [GitHub Releases 페이지](https://github.com/ahbiyout-all/PowerController/releases)에 자동 등록합니다!

---

## 🚀 GitHub Releases 기반 "실시간 자동 업데이트 시스템"

1. **웹 대시보드 실시간 업데이트 배너 (`GitHubUpdateBanner.tsx`)**:
   - 앱 구동 시 GitHub Releases API(`https://api.github.com/repos/ahbiyout-all/PowerController/releases/latest`)를 실시간 호출.
   - 현재 실행 중인 앱 버전과 GitHub 상의 최신 태그 버전을 비교.
   - 신규 릴리스 감지 시 **상단 그라디언트 알림 바** 및 **상세 패치 내역 모달**이 표시되며, 원클릭으로 최신 PC 설치/실행 프로그램을 다운로드할 수 있습니다.
2. **데스크톱 앱 (`main.py`) 실시간 조회 엔진**:
   - `main.py`에 내장된 `check_github_update` 루틴이 시작 시 및 설정 화면에서 새 버전을 감지하고 알림 다이얼로그를 띄웁니다.

---

## 💻 PC (Windows) 공식 릴리스 에셋 (Release Assets - 인스톨러 전용)

GitHub Releases에는 사용자가 가장 편리하고 안전하게 설치할 수 있도록 **Inno Setup 6 기반 공식 설치 프로그램(`PowerController_Setup_v2.9.1.exe`) 단독 파일만 빌드 및 배포**됩니다:

| 파일명 | 종류 | 내용 및 특징 |
| :--- | :--- | :--- |
| **`PowerController_Setup_v2.9.1.exe`** | **공식 설치 프로그램 (Installer)** | Inno Setup 6 기반 Windows 표준 설치 마법사<br>• 바탕화면/시작메뉴 바로가기 등록<br>• 제어판/설치된 앱 정식 등록<br>• Windows Defender 방화벽 예외 규칙 무음 자동 등록<br>• 원격 무인 설치(`/VERYSILENT`) 및 파일 락 자동 해제 |

* 불필요한 임시 압축 파일이나 비공식 패키지를 제거하고 오직 신뢰할 수 있는 **정식 인스톨러(.exe) 1개만 깔끔하게 제공**합니다.
* 모바일(스마트폰/태블릿)에서는 웹 브라우저 접속을 통해 모바일 반응형 원격 리모컨(PWA)으로 실시간 PC 전원 제어가 가능합니다.

---

## 🛠️ GitHub 원클릭 배포 실행 방법

1. `push_to_github.bat` 파일을 더블 클릭하여 실행합니다.
2. 커밋 메시지를 입력하거나 엔터(기본 메시지: `Release v2.9.1`)를 누릅니다.
3. 스크립트가 모든 변경 파일을 스테이징, 커밋, 태그 생성 후 GitHub `main` 브랜치로 자동 푸시합니다.
4. GitHub Actions가 클라우드에서 Windows 실행파일(`.exe`)과 설치 프로그램을 자동 빌드하고 Releases 페이지에 등록을 완료합니다.
