# PowerController v2.9.1
> **Windows 시스템 전원 자동 오프 제어기 & 사내망 원격 예약 관리 타워**  
> **Smart PC Auto Power & Remote Shutdown Management Center**

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
2. **단일 출처 버전 동기화 (Single Source of Truth, SSOT)**:
   - `package.json`의 버전을 기준으로 소스코드(`src/types.ts`, `main.py`), Inno Setup 스크립트, 패치노트(`docs/PATCHNOTES.md`), Git 커밋 및 태그가 100% 자동 동기화.
3. **Inno Setup 6 공식 설치 마법사 (Windows Installer)**:
   - **폴더 풀림(Unpacked Multi-File) 개별 파일 설치**: 깔끔한 모듈형 파일 트리 구조 설치, 불필요한 개발용 문서 및 포터블 파일 배포 원천 배제.
   - **기존 버전 감지 및 선택 대화상자**: 기존 설치 감지 시 사용자에게 완전 삭제 후 클린 설치(Clean Install) 또는 덮어쓰기(Overwrite/Upgrade) 선택 질의.
   - **무인 설치(Silent Install) 완벽 지원**: `/SILENT`, `/VERYSILENT`, `/SUPPRESSMSGBOXES`, `/clean=1`.
   - **Windows Defender 방화벽 무음 사전 등록**:
     - 기본 이름(`PowerController (Inbound/Outbound)`) 및 버전 명기 이름(`PowerController v2.9.1 (Inbound/Outbound)`) 동시 등록.
     - 통신 포트(TCP 9988, UDP 9985, UDP 9986) 및 커맨더 앱 자동 등록.
4. **오디오 엔진 & 헤더 음소거**:
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
  * `PowerController_Setup_v2.9.1.exe`

---

## 🚀 GitHub 자동 푸시 및 릴리스 배포 (Auto Push & Release)

Windows 환경에서는 루트 경로의 `push_to_github.bat`을 더블 클릭하여 원클릭 자동 배포를 수행할 수 있습니다:

```cmd
push_to_github.bat
```

* **파이프라인 동작 과정**:
  1. `package.json` (또는 `docs/PATCHNOTES.md`)에서 동적으로 앱 버전 `%APP_VER%` 추출.
  2. 개인정보 및 개인 이메일 유출 사전 점검 (`AhBiYout-all <AhBiYout-all@users.noreply.github.com>` 규격 적용).
  3. Git Add -> Commit (`Release v%APP_VER%`) -> Tag (`v%APP_VER%`) -> Remote Push (`main`).
  4. GitHub Actions가 트리거되어 Node.js 22 LTS 환경에서 Inno Setup 인스톨러를 빌드하고, GitHub Releases에 **오직 공식 설치 파일만 첨부**합니다.

---

## 📄 라이선스 (License)

Copyright (c) 2026 **AhBiYout**. All rights reserved.  
본 소프트웨어는 [MIT License](docs/LICENSE_ko.txt)에 따라 자유롭게 사용 및 배포할 수 있습니다.
