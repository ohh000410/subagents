# GUI 모달 교착 — 비대화형 세션 공통 정책

GUI 앱을 COM/배치로 자동화하는 모든 에이전트 공통.

## 원리

에이전트의 Bash는 비대화형이다(stdin이 null). GUI 앱이 모달을 띄우면 아무도 응답할 수 없어 세션이 timeout까지 멈춘다. 앱은 정상(`Responding=True`, CPU idle)이라 크래시로 안 보인다. **재시도·sleep으로 풀리지 않는다** — 모달은 결정론적으로 다시 뜬다. 원인을 제거한다.

## 층 1 — 종료 시 저장 프롬프트

dirty 상태로 닫지 않는다. 앱마다 관용구가 다르고, 비슷해 보이는 대안이 무언실패한다.

| 앱 | 검증된 관용구 | 비고 |
|---|---|---|
| Origin | `app.IsModified = False` → `app.Exit()` | LabTalk `doc.Modified=0;`은 True를 반환하고도 무효, `doc -s;`는 원본을 덮어씀 — 둘 다 금지 |
| Inventor | `doc.Close(True)` → `app.Quit()` | 인자는 `SkipSave`. `Close(False)`는 "Save changes?" 모달 |
| SpaceClaim / SPEOS | `/ExitAfterScript=True` → 기다린다 | 모달 자체가 없다. 스크립트 실행 중 끊어야 하면 `Stop-Process -Id <자기 PID> -Force`만 듣는다(headless라 `CloseMainWindow()` 무효) |

## 층 1 밖 — 배수되지 않은 stdout 파이프

모달이 아닌데 모달처럼 보이는 교착. `subprocess.Popen(..., stdout=PIPE)`로 GUI 앱을 띄우고 파이프를 읽지 않으면 앱이 64 KB를 채우는 순간 write에서 블록된다. SpaceClaim은 assembly 로딩 중 `FILENAME:` 수천 줄을 뱉어 초기화 도중에 걸린다.

증상은 층 1과 같다(CPU idle, 창 없음). 구별 지점은 **`communicate()`가 파이프를 비우는 시점에 갑자기 진행된다**는 것.
→ **GUI 앱 launch에 `stdout=PIPE`를 쓰지 않는다.** 파일 핸들로 리다이렉트한다(init 40~180분 → 35초).

## 층 2 — 작업 중 명령이 띄우는 모달

층 1은 종료 시 프롬프트만 막는다. 위험군은 **파일 경로를 인자로 받는 저장·열기·내보내기 계열**(Origin `save`·`open`·`exp*`, 경로를 받는 X-function). 미검증 명령은 본 작업에 섞지 말고 격리해서 먼저 시험한다.

## hang 진단 — 모달인가, 연산 중인가

1. CPU 사용률을 간격을 두고 2회 측정 — 변화 없으면 연산 중이 아니다
2. launch에 `stdout=PIPE`를 썼는지 본다
3. `Get-Process` → `Responding` 확인
4. `EnumWindows`로 해당 PID의 top-level 창 나열

**창이 안 잡혀도 모달이 아니라고 단정하지 않는다** — Inventor에서 `EnumWindows`가 대화상자를 못 찾은 전례가 있다. 후보: `IsWindowEnabled(main_hwnd) == False`(모달이 뜨면 부모가 비활성화).

## 모달 탐지 — 워치독

```python
import win32gui, win32process
def windows_of(pid):
    """대상 PID의 보이는 top-level 창 전부. 클래스 필터를 걸지 않는다."""
    out = []
    def cb(h, _):
        if not win32gui.IsWindowVisible(h):
            return
        _, p = win32process.GetWindowThreadProcessId(h)
        if p == pid:
            out.append((win32gui.GetClassName(h), win32gui.GetWindowText(h)))
    win32gui.EnumWindows(cb, None)
    return out
```

검증 상태: 표준 대화상자(`#32770`)는 1.5초 내 탐지 확인. Inventor 실제 모달(PDF 저장 때 한글 노트 글꼴 경고)은 `EnumWindows` 가 1.4초 안에 `#32770` 을 찾았고 메인 창은 비활성이었다(2026-10-22). Origin 실제 모달 탐지는 미검증(재현 조건 불명).

**탐지되면 곧바로 실패로 판정한다.** 창 제목과 마지막 진행 마커를 함께 기록하고 프로세스를 종료한 뒤 반환한다. **자동으로 닫고 계속하지 않는다** — 원인을 모른 채 넘어가면 다음 실행에서 같은 자리에 걸린다.

## 원칙

예방이 수습에 우선한다. `-Force` 강제 종료는 이미 멈춘 세션을 치우는 최후 수단이다. 새로 확인된 종료 관용구·무언실패 대안·위험 명령은 각 에이전트의 agent-memory에 기록한다.
