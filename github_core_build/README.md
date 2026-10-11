# GitHub Core Build Management (`github_core_build/`)

본 디렉터리는 **깃허브(GitHub)에 업로드할 때 프로젝트 실제 빌드에 필요한 핵심 파일만 필터링하여 안전하게 관리 및 배포**하기 위해 구성된 전용 관리 디렉터리입니다.

---

## 🎯 주요 목적 및 정책

1. **빌드 핵심 파일 무결성 보장**:
   * Windows x64 데스크톱 앱(PyInstaller), Native C/C++ DLL 엔진, 웹 대시보드(Vite + React), Inno Setup 설치 프로그램 패키징 및 GitHub Actions CI/CD 실행에 필요한 필수 파일만 선별하여 관리합니다.
2. **불필요한 파일 및 개인정보 차단**:
   * 로컬 테스트 데이터(`power_*.json`, `sidebar_theme_config.json`, `power_master_key.txt`), 임시 파일, 개인 이메일, 빌드 캐시(`.pyc`, `node_modules`, `build/`, `dist/`)의 GitHub 업로드를 사전에 완벽히 차단합니다.
3. **규약 준수**:
   * 제작자 및 개발자 정보: `AhBiYout`
   * GitHub 개발자 계정: `AhBiYout-all` (`https://github.com/AhBiYout-all`)
   * 공식 블로그: `https://ahbiyoutvibe.blogspot.com/`
   * 소속 회사: CISNet (`https://www.cisnet.co.kr`)
   * 보안 이메일: `AhBiYout-all@users.noreply.github.com`
   * GitHub Releases 첨부물: Windows 공식 설치 파일(`PowerController_Setup_v*.exe`)만 릴리스 자산으로 업로드.

---

## 📂 파일 구성 안내

* `CORE_FILES_MANIFEST.txt`: GitHub 업로드 및 CI/CD 빌드에 필요한 필수 핵심 파일/디렉터리 목록 명세서 (화이트리스트).
* `verify_core_files.py`: 핵심 파일의 실제 존재 여부 및 불필요한 파일/개인 이메일 노출 여부를 자동 전수 감사하는 정밀 검증 스크립트.
* `push_core_to_github.bat`: 검증된 핵심 파일만 선별하여 GitHub 저장소(`https://github.com/AhBiYout-all/PowerController`)로 자동 커밋/태깅/푸시하는 Windows 배치 스크립트.
* `stage_core_files.py`: 배포 전 전용 배포 스테이징 디렉터리를 생성하여 핵심 파일만 정제 복사하는 유틸리티.

---

## 🚀 사용 방법

### Windows 개발 환경에서 핵심 파일 전용 GitHub 푸시 실행:
```cmd
github_core_build\push_core_to_github.bat
```
또는 루트 디렉터리의 통합 자동 스크립트 실행:
```cmd
push_to_github.bat
```

### 사전 검증 스크립트 단독 실행:
```cmd
python github_core_build\verify_core_files.py
```
모든 검증을 통과해야만 GitHub 푸시 및 태그 생성이 진행됩니다.
