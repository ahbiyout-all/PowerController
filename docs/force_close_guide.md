# PowerController 강제 종료 플래그 (/f) 기술 및 운영 가이드 (Force Close Guide)

본 문서는 **PowerController v2.6.0**에 신설된 **실행 중인 프로그램 강제 종료 플래그(`force_close` / Windows `/f` 파라미터)**의 설계 배경, 기술적 동작 원리, 기본 활성화(Default: Enabled) 정책 및 안전 수칙을 기술합니다.

---

## 📌 1. 개요 및 설계 배경 (Overview & Background)

Windows 운영체제에서 `shutdown.exe` 명령어를 호출할 때 기본 동작 방식은 다음과 같습니다:
* 실행 중인 모든 프로세스에 종료(WM_CLOSE / WM_QUERYENDSESSION) 신호를 보냅니다.
* 이때 메모장, 워드, 브라우저 등의 프로그램에 저장되지 않은 문서가 있거나, 특정 백그라운드 프로세스가 응답하지 않으면 윈도우는 **"저장하시겠습니까?"** 또는 **"이 앱이 시스템 종료를 방해하고 있습니다"** 대화상자를 띄우며 종료 카운트다운을 대기하거나 취소합니다.
* 사용자가 컴퓨터 앞을 지키고 있지 않은 상황(퇴근 후 자동 종료, 야간 취침 전 타이머, 원격 관리자 스케줄링 등)에서는 이로 인해 **컴퓨터가 밤새 켜져 있거나 전원 관리가 실패하는 심각한 문제**가 빈번히 발생합니다.

이를 원천 해결하기 위해 시스템 종료 및 재시작 시 **Windows `/f` (Force) 파라미터**를 결합하는 메커니즘을 전면 도입했습니다.

---

## ⚡ 2. 기본 활성화(Default: Enabled) 정책 수립 근거

PowerController는 **"설정된 시간 또는 예약된 시각에 전원 차단을 100% 확실하게 집행한다"**는 신뢰성 최우선 원칙에 따라 다음과 같이 기본값을 책정하였습니다:

1. **기본값**: `True (활성화 상태 / Enabled)`
2. **효과**: 사용자가 프로그램을 처음 설치하거나 별도의 추가 설정을 건드리지 않아도, 지정된 시간이 만료되면 방해 프로그램에 구애받지 않고 안전하고 확실하게 전원 제어가 완료됩니다.
3. **자유로운 제어**: 중요한 미저장 작업을 수동으로 보호하고자 하는 사용자는 메인 화면 또는 환경설정에서 원클릭으로 손쉽게 비활성화(`False`)할 수 있습니다.

---

## 🛠 3. 기술 구현 아키텍처 (Technical Implementation)

### 3.1 Python 데스크톱 엔진 (`main.py`)

#### A. 상태 선언 및 영구 보존
```python
# main.py __init__
self.force_close_enabled = tk.BooleanVar(value=True)  # 기본 활성화 (Default: Enabled)

# load_settings()
self.force_close_enabled.set(settings.get("force_close_enabled", True))

# save_settings()
settings["force_close_enabled"] = bool(self.force_close_enabled.get())
```

#### B. 시스템 명령 실행 분기
```python
# execute_power_action(mode, force_flag)
force = force_flag if force_flag is not None else self.force_close_enabled.get()
force_param = " /f" if force else ""

if mode in ["shutdown", "종료"]:
    cmd = f"shutdown /s{force_param} /t 2"
elif mode in ["restart", "재부팅", "다시 시작"]:
    cmd = f"shutdown /r{force_param} /t 2"
```

#### C. GUI 사용자 인터페이스 연동
* **메인 하단 옵션 바 (`opt_row3`)**: 작업 시작 전 직관적인 `⚡ 강제 닫기 (/f)` 체크박스 제공.
* **환경설정(Preferences) 대화창**: `[8. ⚡ 실행 중인 앱 강제 종료 플래그 (/f)]` 섹션에서 전역 기본 활성화 여부 설정 지원.
* **스케줄러 & 네트워크 수신 연동**: 원격 수신 패킷(`handle_network_client`) 또는 예약 안내 카운트다운(`open_grace_popup`)에 `force_close` 옵션이 동기화됩니다.

---

### 3.2 React 웹 프론트엔드 및 시뮬레이터 (`src/App.tsx`, `PowerSimulator.tsx`)

#### A. 로컬 스토리지 연동 및 상태 관리
* `localStorage` 키 `power_force_close_enabled`를 통해 상태를 브라우저에 지속 보존합니다.
* 초기값이 없을 경우 기본적으로 `true`로 자동 초기화됩니다.

#### B. UI 접근성
1. **타이머 탭 퀵 옵션 바**:
   * 타이머 탭 상단에 핑크/로즈 테마의 `⚡ 실행 중인 앱 강제 종료 (/f)` 체크박스 바를 배치하여 직관성을 극대화했습니다.
   * 현재 상태가 기본 활성화(`Default: Enabled`)인지 비활성화(`Disabled`)인지 보조 텍스트로 명확히 표시합니다.
2. **환경설정 모달 창**:
   * Section 6 `[실행 중인 프로그램 강제 종료 (/f 파라미터)]`에서 기능 설명과 함께 기본 적용 여부를 토글할 수 있습니다.
   * 환경설정 트랜잭션(`Confirm / Cancel`) 파이프라인과 완벽히 동기화됩니다.
3. **가상 전원 시뮬레이터 (`PowerSimulator.tsx`)**:
   * 강제 종료 옵션이 활성화된 상태에서 시뮬레이션 가동 시:
     `⚡ 실행 중인 앱 강제 종료 플래그 (/f) 적용됨` 배지가 시각적으로 점등되어 신뢰감을 부여합니다.

---

## 🔒 4. 보안 및 안전 사용 수칙 (Safety & Precautions)

* **정기적 저장 습관**: `/f` 플래그가 활성화되어 있으면 저장되지 않은 문서 편집 창이 있더라도 즉시 닫힙니다. 퇴근 전이나 장시간 자리 비움 전에는 반드시 작성 중인 중요 문서나 작업물을 저장해 두는 것을 권장합니다.
* **임시 해제**: 만약 특정 날짜에 중요한 렌더링이나 긴급 데이터 저장을 수동으로 확인한 후 종료하고 싶다면, 메인 화면의 `⚡ 강제 닫기 (/f)` 체크를 잠시 해제하십시오.
* **네트워크 원격 전송 시**: 원격 관리자가 다른 PC에 스케줄을 배포할 때도 `force_close: true` 속성이 기본 동봉되어 원격 컴퓨터의 안정적인 종료를 보장합니다.

---

## 🌐 5. 관련 공식 링크
* **공식 블로그**: [https://ahbiyoutvibe.blogspot.com/](https://ahbiyoutvibe.blogspot.com/)
* **공식 게시자**: cisnet.co.kr | **개발자**: AhBiYout
