# [구글 블로그 배포용 문서] PowerController 공식 릴리즈 포스팅

> 본 문서는 **구글 블로그(Blogger: https://ahbiyoutvibe.blogspot.com/)** 포스팅 전용 규격 가이드라인(지정 섹션 순서: 제목 → 본문 → 업데이트 → 앱 그림 → 다운로드 → 버전정보 → 시스템 요구 사항 → 제작자 및 공식 채널 안내 → 전체 업데이트(이전 기록 모두) → 추천 태그)에 맞춰 작성 및 관리되는 공식 배포 문서입니다.

---

## 1. 제목 (Title)

**[공식 배포] PowerController v2.9.1 - 스마트 윈도우 전원 스케줄러 & 무인 설치 자동화 컨트롤러 (종료/재시작/절전/화면끔/원격제어)**

---

## 2. 본문 (Body)

안녕하세요, **PowerController** 공식 개발자 **AhBiYout**입니다.

컴퓨터를 켜둔 채 퇴근하거나 잠들었을 때, 혹은 사내 수십 대의 PC를 정해진 시각에 일괄 종료하고 관리해야 할 때 겪었던 불편함을 완벽하게 해결해 드리는 **PowerController v2.9.1** 정식 버전을 배포합니다.

PowerController는 단순한 타이머 프로그램을 넘어, **윈도우 네이티브 커널 API 및 고성능 C/C++ DLL 아키텍처**와 **현대적인 모던 웹/데스크톱 UI**를 결합하여 설계된 차세대 스마트 전원 관리 솔루션입니다.

### 🌟 핵심 주요 기능
- **⚡ 6대 핵심 전원 관리 모드**: 시스템 종료(Shutdown), 다시 시작(Reboot), 절전 모드(Sleep), 화면 끄기(Monitor Off), 로그아웃(Sign out), 사운드 알람(Alarm) 지원
- **🎛️ 깔끔한 풀다운(드롭다운) UI 인터페이스**: 복잡한 화면 분산을 방지하는 직관적인 풀다운 메뉴 및 기존 6분할 그리드 뷰 상호 전환 토글 지원
- **📌 5종 디자인 상단 고정 컴팩트 위젯**: 네온 링(Neon Ring), 사이버 HUD(Cyber HUD), 슬림 바(Slim Bar), 레트로 LED(Retro LED), 클린 카드(Clean Card) 등 취향에 맞는 항상 위 플로팅 위젯 지원 (부드러운 페이드인 & 스케일 트랜지션 모션 탑재)
- **🔔 Pixabay 선별 7대 프리미엄 사운드 엔진**: 클래식 벨, 마림바, 크리스탈, SF 신스, 웨스트민스터 차임, 경고음, 버블 등 Web Audio / 네이티브 오디오 믹서 통합
- **📊 배터리 텔레메트리 & 스마트 절전**: 60분 배터리 소모 트렌드 Recharts 시각화, 방전 예측 시간 계산, 15% 이하 지속 경고 토스트 및 20% 이하 위젯 저전력 모드
- **🛡️ 11대 순수 창작 저수준 C/C++ 네이티브 DLL**: 하드웨어 웨이크업 타이머(`PowerCoreNative`), 락프리 링버퍼 네트워크 엔진(`NetBeaconEngine`), 방화벽 COM 직결(`FirewallNative`), 캐시 플러시(`DiskFlushNative`), Core Audio 디머(`AudioDimmerNative`), 유휴 시간 정밀 감지(`LowLevelInputIdleNative`) 등 탑재
- **🏢 엔터프라이즈 사내 원격 관제 (PowerNetworkScheduler)**: 동일 네트워크 내 최대 500대 PC 실시간 스캔, 원클릭 원격 즉시 종료/재시작, 스케줄 무선 동기화, Wake-on-LAN(WOL) 매직 패킷 송출
- **⚡ 실행 중인 앱 강제 종료 플래그 (`/f`) 기본 적용**: 미저장 알림 창으로 인한 종료 멈춤 현상을 원천 방지하여 예약 작업의 100% 무인 집행 보장

---

## 3. 업데이트 (Updates - v2.9.1)

최신 **v2.9.1** 버전의 핵심 개선 및 추가 사항입니다:

1. **GitHub Releases 기반 실시간 자동 업데이트 알림 시스템 탑재**
   - 최신 버전 릴리즈 실시간 감지 및 인앱 원클릭 다운로드 팝업(`UpdateModal`) 연동
2. **다중 선택 항목의 풀다운/드롭다운화 (Clean Screen Layout)**
   - 전원 동작 모드, 시간 지연 프리셋, 스케줄러 설정, 위젯 스타일 등 동일 유형 다중 컨트롤을 컴팩트한 풀다운 메뉴로 전면 정돈
3. **상단 고정 컴팩트 위젯 부드러운 페이드인 & 스케일 트랜지션 애니메이션**
   - 모드 전환 시 `cubic-bezier(0.16, 1, 0.3, 1)` 기반 매끄러운 모션 효과 적용
4. **데스크톱 앱 전면 사운드 스튜디오 및 인터랙션 피드백 완성**
   - 7대 테마 선택, 마스터 볼륨(0~100%), 매시 정각 시계탑 차임벨, 카운트다운 틱, 타이머 만료음 완벽 동기화
5. **Recharts 기반 60분 배터리 소모 차트 & 방전 예측 분석 엔진 구축**
   - 실시간 방전 곡선, 잔여 사용 시간 예측, 시간당 소모율, 15% 이하 안전 작동 한계 알림
6. **Inno Setup 6 기반 공식 인스톨러 및 무인 설치(Silent Install) 완비**
   - `/SILENT`, `/VERYSILENT`, `/NORESTART` 완전 지원 및 기존 프로세스 멈춤(Hang) 방지 자동 파일 언락
   - Windows Defender 방화벽 무음 사전 등록(메인, 커맨더 및 전용 포트 TCP 9988 / UDP 9985, 9986)

---

## 4. 앱 그림 (Application Image)

![PowerController Official Emblem Logo](https://raw.githubusercontent.com/AhBiYout-all/PowerController/main/PowerController.png)

*▲ PowerController 공식 풀-프레임 네온 사이언 엠블럼 로고 및 아이콘 디자인*

---

## 5. 다운로드 (Download)

Windows 전용 공식 인스톨러 설치 파일은 GitHub 공식 릴리즈 저장소에서 안전하게 바로 다운로드하실 수 있습니다.

- 📥 **공식 설치 파일 다운로드 (Direct Download)**:  
  **[PowerController_Setup_v2.9.1.exe 다운로드](https://github.com/AhBiYout-all/PowerController/releases/download/v2.9.1/PowerController_Setup_v2.9.1.exe)**

- 🌐 **GitHub 공식 릴리즈 배포 페이지**:  
  [https://github.com/AhBiYout-all/PowerController/releases/tag/v2.9.1](https://github.com/AhBiYout-all/PowerController/releases/tag/v2.9.1)

- 📦 **GitHub 공식 소스코드 저장소**:  
  [https://github.com/AhBiYout-all/PowerController](https://github.com/AhBiYout-all/PowerController)

> **💡 무인 자동 설치 (사내 일괄 배포 관리자용 CLI 옵션)**:  
> `PowerController_Setup_v2.9.1.exe /VERYSILENT /NORESTART`

---

## 6. 버전정보 (Version Information)

| 항목 | 상세 정보 |
| :--- | :--- |
| **소프트웨어 명칭** | **PowerController** |
| **최신 배포 버전** | **v2.9.1** (Semantic Versioning 2.0 준수) |
| **빌드 패키지** | Inno Setup 6 Unpacked Multi-File 공식 인스톨러 |
| **설치 파일명** | `PowerController_Setup_v2.9.1.exe` |
| **라이선스** | MIT License (한국어/영어 공식 고지서 탑재) |
| **단일 버전 원천** | `package.json` (`v2.9.1`) 기준 전 컴포넌트 100% 일치 |

---

## 7. 시스템 요구 사항 (System Requirements)

| 하드웨어 / 소프트웨어 | 최소 사양 | 권장 사양 |
| :--- | :--- | :--- |
| **운영체제 (OS)** | Microsoft Windows 10 (64-bit) | Microsoft Windows 11 (64-bit) 최신 빌드 |
| **프로세서 (CPU)** | Intel Core i3 / AMD Ryzen 3 이상 (1.5 GHz) | Intel Core i5 / AMD Ryzen 5 이상 |
| **메모리 (RAM)** | 2 GB RAM 이상 | 4 GB RAM 이상 |
| **디스크 저장 공간** | 100 MB 이상의 여유 디스크 공간 | 250 MB 이상의 여유 디스크 공간 |
| **디스플레이 해상도** | 1024 x 768 이상 | 1920 x 1080 (Full HD) 이상 |
| **네트워크 환경** | 단독 PC 구동 시 오프라인 가능 | 원격 관제 및 자동 업데이트 확인 시 로컬 LAN / 인터넷 필요 |
| **권한 요구사항** | 일반 사용자 권한 실행 가능 (방화벽 등록 및 설치 시 UAC 관리자 권한) | 관리자 권한 (사내 원격 방화벽 자동 구성용) |

---

## 8. 제작자 및 공식 채널 안내 (Developer & Official Channels)

- 👨‍💻 **개발자**: **AhBiYout**
- 🐙 **GitHub 공식 계정**: **AhBiYout-all** ([https://github.com/AhBiYout-all](https://github.com/AhBiYout-all))
- 📂 **프로젝트 저장소**: **PowerController** ([https://github.com/AhBiYout-all/PowerController](https://github.com/AhBiYout-all/PowerController))
- 📝 **공식 기술 블로그 (Blogger)**: **AhBiYout Vibe** ([https://ahbiyoutvibe.blogspot.com/](https://ahbiyoutvibe.blogspot.com/))
- 🏢 **소속사**: **CISNet**
- 🌐 **소속사 공식 웹사이트**: **[http://www.cisnet.co.kr/](http://www.cisnet.co.kr/)** (https://www.cisnet.co.kr)

---

## 9. 전체 업데이트(이전 기록 모두) (Historical Changelog)

PowerController의 첫 릴리즈부터 현재까지의 전체 누적 패치 이력입니다:

### [v2.9.1] - 2026-10-09
- **GitHub Releases 기반 실시간 자동 업데이트**: 인앱 버전 비교 및 다운로드 팝업(`UpdateModal`) 연동.
- **제작자 및 공식 채널 표준화**: AhBiYout, AhBiYout-all, CISNet, 구글 블로그 전면 동기화.
- **개인정보 및 보안 보호 (PII Shield)**: Git Commit Author 규격화 및 개인정보 누출 차단.
- **GitHub Actions CI/CD 공식 규격 준수**: Node.js 22 LTS 전환 및 Inno Setup 6 자동 빌드 워크플로 구축.
- **Inno Setup 설치 마법사 엔지니어링**: 폴더 풀림 개별 파일 설치, 기존 앱 감지/삭제/덮어쓰기 질의, 무인 설치 스위치, Windows Defender 방화벽 무음 사전 등록(메인, 커맨더 및 포트 9988/9985/9986).
- **풀다운/드롭다운 UI 정돈 시스템**: 다중 선택 컨트롤(전원 모드, 지연 프리셋, 스케줄 타입, 위젯 디자인)을 깔끔한 풀다운으로 통합.
- **컴팩트 위젯 부드러운 애니메이션**: 페이드인 & 스케일 트랜지션 모션 탑재.
- **7대 Pixabay 사운드 테마 & 데스크톱 사운드 스튜디오**: 볼륨 슬라이더, 상황별 사운드 믹서, 정각 차임벨 연동.
- **Recharts 기반 60분 배터리 차트**: 실시간 방전 추세 및 잔여 시간 예측 엔진.
- **11대 순수 창작 저수준 C/C++ 네이티브 DLL 아키텍처 완성**: `DiskFlushNative`, `AudioDimmerNative`, `DisplayDdcNative`, `LowLevelInputIdleNative`, `CommanderTcpDispatcherNative`, `CommanderPingScannerNative` 신규 추가.

### [v2.9.0] - 2026-09-22
- **PowerNetworkScheduler 원격 즉시 실행 제어(Immediate Power Actions)**: 대상 PC 즉시 종료(`Shutdown Now`), 즉시 다시시작(`Reboot Now`) 지원.
- **이중 보안 확인 팝업**: 관리자 실수 방지 확인 다이얼로그 및 비인가 토큰 변조 원천 차단.
- **원격 스케줄러 10대 자주 쓰는 제목 프리셋 탑재**: 심야 자동 종료, 퇴근 시간 전원 끄기 등 원클릭 스마트 자동 채우기.
- **메인 및 커맨더 수신 엔진 동기화**: TCP 9988 및 UDP 9985 양방향 즉시 제어 처리.

### [v2.8.1] - 2026-09-19
- **메인 & 커맨더 Windows 방화벽 규칙 사전 무음 등록 체계 구축**: UAC 경고 팝업 사전 차단 및 원클릭 방화벽 등록기(`Register_Firewall_Rules.bat`) 배포.
- **메인 화면 체크박스 2열 대칭 분할 레이아웃**: 가로폭 475px 최적화 및 시각적 답답함 해소.
- **폰트 크기 최하 10pt 일괄 상향 및 팝업창 자동 크기 조절(Auto-fit)** 구현.

### [v2.8.0] - 2026-09-16
- **배포 인스톨러 Inno Setup 6 전격 전환**: LZMA2 고압축 솔리드 엔진, 네이티브 다국어 설치 마법사.
- **Windows 제어판 공식 등록 및 클린 언인스톨**: 프로그램 추가/제거 정식 등록 및 완벽한 파일 정리.
- **무인 자동 설치(Silent Install) 스위치 지원**: `/SILENT`, `/VERYSILENT`, `/NORESTART` 엔터프라이즈 배포 플래그 지원.
- **Windows 실행 파일 속성 '자세히(Details)' 탭 메타데이터 완전 주입**: 한국어/영어 OS 완벽 매핑.

### [v2.7.0] - 2026-09-16
- **데스크톱 앱 APPDATA 영구 저장 경로 격리 (`%APPDATA%\PowerController`)**: Program Files 권한 에러 및 설정 초기화 문제 원천 해결.
- **미니 위젯 5종 테마 및 동적 리빌드 엔진**: 네온 링, 사이버 HUD, 슬림 바, 레트로 LED, 클린 카드 실시간 전환.
- **매 시 정각 웨스트민스터 차임벨 소리 & 알림 (Hourly Chime)** 탑재.
- **부팅 시 오늘의 예약 작업 자동 점검 및 브리핑 모달 (Startup Tasks Alert)** 추가.

### [v2.6.0] - 2026-09-14
- **실행 중인 프로그램 강제 종료 플래그 (`force_close` / `/f`) 기본 활성화**: 미저장 프로세스로 인한 전원 차단 지연/정지 방지.
- **개발 서버 포트 충돌 방지 및 멀티 포트 환경 구축**: `server.ts` 포트 스왑 지원.

### [v2.5.0] - 2026-09-12
- **컴팩트 위젯 맞춤 커스터마이저 및 실시간 슬라이더 제어**: 가로 너비, 시계/타이머 글자 크기 조절.
- **환경설정 변경 사항 안전 버퍼링 트랜잭션 (Confirm / Cancel)** 도입.
- **스케줄러 사용자 경험 강화**: 기본 전원 행동 지정 및 타임스탬프 원클릭 부착.

### [v2.4.0] - 2026-07-10
- **스케줄러 예약 알람 (Alarm) 행동 완전 통합**.
- **예약작업 전 알림 대기시간 (Grace Warning Duration) 커스텀 제어**: 최소 5초~최대 5분 조절.
- **CLI 기반 무인설치 엔진 도입** 및 Windows 제어판 공식 게시자 정보 표준화.

### [v2.3.0] - 2026-07-08
- **새로운 전원 제어 행동 '예약 사운드 알람(Alarm Mode)' 전격 도입**.
- **반복 챠임벨 및 직관적인 핑크/로즈 테마 경보 모달 설계**.
- **다국어 자동 번역 매핑 보강**.

### [v2.2.0] - 2026-07-08
- **스케줄러 폼 실시간 시각 유효성 피드백 (Visual Validation Cues) 도입**: 오류 필드 적색 하이라이트 및 실시간 초기화.

### [v2.1.0] - 2026-07-06
- **스케줄 공유 배포기 빌더(`schedule_share_builder.py`) 완전 자동화 및 실시간 업데이트**.
- **공유 배포기 생성 위치 '내 문서' 이관 및 자동 폴더 열기**.
- **상단 고정 미니창 현재 시각 표시부 2.5배 확대**.
- **트레이 최소화 백그라운드 루프 최적화 (CPU 점유율 0%)**.

### [v2.0.0] - 2026-06-28 (MAJOR 릴리즈)
- **네트워크 원격 스케줄 전송/수신 서브시스템 탑재**: LAN IP / 포트 9988 기반 무선 규칙 배포 및 백그라운드 리스너 구축.

### [v1.1.0] - 2026-06-28
- **스마트 언인스톨러 통합 빌드 프로세스**: 파일 잠금 해결, 바로가기/레지스트리 정리, 인앱 라이선스 고지서.

### [v1.0.0] - 2026-06-20 (MAJOR 최초 릴리즈)
- **PowerController 하이브리드 자동 전원 컨트롤러 최초 공식 릴리즈**.
- Fluent 다크, 모던 그레이, 클래식 베이지 3종 테마 및 비프/신스/오르골 오디오 피드백 지원.

---

## 10. 추천 태그 (Recommended Tags)

> **태그 규격 준수 안내**: 한글/영어 혼합 구성, 총 17개 (20개 이하 요건 충족), 콤마 포함 총 181자 (200글자 이내 요건 완벽 충족).

#PowerController, #PC종료예약, #윈도우자동종료, #전원스케줄러, #원격종료, #컴퓨터자동종료, #윈도우11, #타이머, #절전모드, #시스템종료, #InnoSetup, #WindowsTimer, #ShutdownTimer, #AutoShutdown, #WakeOnLAN, #AhBiYout, #CISNet
