# PowerController 공식 문서 저장소 (Documentation Hub)

본 디렉토리(`docs/`)는 **PowerController v2.9.1**의 시스템 아키텍처, 사용자 매뉴얼, 설치 및 패키징 가이드, GitHub CI/CD 자동 배포 가이드, 3단계 버전 관리 정책(SemVer), 보안 지침 및 상세 패치 노트를 보관하는 종합 기술 문서 저장소입니다.

---

## 📚 문서 색인 (Documentation Index)

| 문서명 | 파일 링크 | 주요 내용 및 대상 |
| :--- | :--- | :--- |
| **버전 관리 정책 (Versioning Policy)** | [`versioning_policy.md`](./versioning_policy.md) | **Semantic Versioning 2.0.0 (MAJOR.MINOR.PATCH) 3단계 원칙** 및 Single Source of Truth 동기화 규칙 |
| **패치 노트 (Patch Notes)** | [`patch_notes.md`](./patch_notes.md) | 버전별 변경 이력, 신규 기능(Features) 및 버그 수정(Fixes) 상세 기록 |
| **GitHub 배포 & CI/CD 가이드** | [`GITHUB_GUIDE.md`](./GITHUB_GUIDE.md) | GitHub 원클릭 업로드(`push_to_github.bat`), 동적 버전 연동, GitHub Actions CI/CD 자동 릴리즈 |
| **사용자 가이드 (User Manual)** | [`user_guide.md`](./user_guide.md) | 일반 사용자를 위한 기능 안내 (타이머, 스케줄러, 위젯 커스터마이징, 네트워크 전송, 모바일 원격 제어 등) |
| **설치 및 패키징 가이드 (Installation)** | [`installation_guide.md`](./installation_guide.md) | Inno Setup 6 배포용 인스톨러 컴파일, PC 배포 패키지 빌더, 무인 설치/제거 안내 |
| **개발자 가이드 (Development)** | [`development.md`](./development.md) | 시스템 아키텍처, Vite 번들 최적화, 컴포넌트 구조, 테마 시스템 및 개발 환경 구축 가이드 |
| **순수 창작 DLL 명세서 (DLL Specification)** | [`dll_specification.md`](./dll_specification.md) | 5대 순수 창작 DLL (PowerCoreNative, NetBeaconEngine, FirewallNative, SysPowerHook, ScheduleCrypto) 명세 |
| **보안 가이드라인 (Security Guidelines)** | [`security_guidelines.md`](./security_guidelines.md) | 네트워크 통신 아키텍처, 취약점 대응 이력, 사내망 운영 보안 지침 및 토큰 복구 절차 |
| **작업 로그 및 로드맵 (WorkLog)** | [`WorkLog.md`](./WorkLog.md) | 일자별 개발 기록, 최적화 작업 내역 및 로드맵 완수 기록 |
| **데스크톱 문제 해결 가이드** | [`desktop_troubleshooting_guide.md`](./desktop_troubleshooting_guide.md) | 데스크톱 앱 변경사항 미반영 원인 분석, APPDATA 저장소 분리, `build.bat` 컴파일 절차 |
| **강제 종료 가이드 (Force Close Guide)** | [`force_close_guide.md`](./force_close_guide.md) | 실행 중인 프로그램 강제 종료 플래그(`/f`) 동작 원리, 기본 활성화 정책 및 안전 수칙 |
| **오픈소스 라이선스 (License)** | [`LICENSE.md`](./LICENSE.md) | MIT 라이선스 및 법적 저작권 고지 (Copyright (c) 2026 AhBiYout) |

---

## 🏷️ 소프트웨어 버전 관리 3단계 원칙 (Semantic Versioning)

PowerController 프로젝트는 코드 변경의 성격과 규모에 따라 버전을 3단계로 엄격히 분리하여 관리하며, `package.json`을 단일 원천(Single Source of Truth)으로 삼아 전체 구성 요소의 버전을 일괄 동기화합니다:

$$\mathbf{MAJOR}.\mathbf{MINOR}.\mathbf{PATCH}$$

1. **1️⃣ MAJOR (X.0.0)**: 하위 호환성이 깨지는 대규모 아키텍처/데이터 스키마/네트워크 프로토콜 파괴적 변경 (예: `v1.0.0` ➔ `v2.0.0`)
2. **2️⃣ MINOR (x.Y.0)**: 하위 호환성을 100% 유지하며 새로운 주요 기능(Features), 독립 편의 도구, UI 대규모 모듈 추가 (예: `v2.8.0` ➔ `v2.9.0`)
3. **3️⃣ PATCH (x.y.Z)**: 하위 호환성을 100% 유지하며 버그 수정(Fixes), 핫픽스, 텍스트 교정, 스타일 미세 조정, 리소스 최적화 (예: `v2.9.0` ➔ `v2.9.1`)

* **버전 일괄 동기화 도구**: `python scripts/sync_version.py`
* **원클릭 GitHub 푸시 & 릴리스 도구**: `push_to_github.bat` / `github_sync.py`

---

## 💻 공식 배포 패키지 (Windows PC)

| 플랫폼 | 배포 파일 형태 | 구성 내용 |
| :--- | :--- | :--- |
| 💻 **PC (Windows)** | `PowerController-v2.9.1-Windows.zip` / `.exe` 인스톨러 | Inno Setup 인스톨러 빌드 소스(`.iss`), Python 네이티브 백그라운드 엔진, 웹 대시보드 산출물, 5대 네이티브 DLL 및 방화벽 설정 스크립트 |

* 모바일(스마트폰/태블릿)에서는 웹 브라우저를 통해 실시간 원격 제어 대시보드(PWA)로 접속하여 침대나 외부에서 내 PC를 원격으로 켜고(WOL) 끌 수 있습니다.

---

## 🌐 공식 프로젝트 정보
* **GitHub 원격 저장소**: [https://github.com/AhBiYout/PowerController.git](https://github.com/AhBiYout/PowerController.git)
* **GitHub 계정 (Owner)**: `AhBiYout`
* **공식 사용자 표시명 (Git Author)**: `AhBiYout-all`
* **보안 전용 이메일**: `AhBiYout@users.noreply.github.com`
* **공식 블로그**: [https://ahbiyoutvibe.blogspot.com/](https://ahbiyoutvibe.blogspot.com/)
* **공식 게시자**: cisnet.co.kr | 저작권자: AhBiYout
