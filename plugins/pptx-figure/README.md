# pptx-figure

PowerPoint 도형으로 그림을 그립니다.

에이전트 설명(Claude 가 맡길지 고를 때 읽는 글): PowerPoint 네이티브 도형으로 그림을 만드는 상담·실행 에이전트. python-pptx 로 개념도·모식도·단면도를 그리거나 논문 figure 의 **요소 하나**를 도형으로 재현하고, 편집 가능한 .pptx 와 원본 대조 결과를 반환한다. 여러 요소를 한 그림으로 합치는 것은 호출자(메인 세션)가 한다. "PPT 도형으로 그려줘", "이 논문 그림 재현해줘", "개념도 파워포인트로", "figure 따라 그려줘", 불리언 병합·3D 돌출·투명도·그라디언트 등 PPT 도형 기능 질문에 사용한다. 데이터 플롯(→ origin-plot)·3D 모델링·물리 해석은 관할 외.

## 설치

```
/plugin marketplace add ohh000410/subagents
/plugin install pptx-figure@ohh000410-subagents
```

설치하면 에이전트 이름은 `pptx-figure:pptx-figure` 입니다.

## 필요한 것

- Python(`<python>`): 이 PC 환경 값(메모리)의 절대경로 (python-pptx·pywin32 가 있는 것)
- 도형 생성 python-pptx / 병합·3D 되읽기·PNG export COM. COM: `pres.Close()` → 직접 띄운 PowerPoint 만 `app.Quit()`(이미 떠 있던 것은 둠) → 프로세스 잔존 확인

도구·예제 코드가 쓰는 Python 패키지: `numpy`, `pillow`, `python-pptx`, `pywin32`, `scipy`

## 처음 쓸 때

- 에이전트가 환경 값(앱 경로·venv)을 찾지 못하면 묻습니다. 확인한 값은 에이전트 메모리 `~/.claude/agent-memory/pptx-figure-pptx-figure/` 에 남습니다.

## 들어 있는 것

- `agents/pptx-figure.md` — 에이전트 정의(공통 규칙 + 본문)
- `pptx-figure/references/` — 6개 파일
- `policies/` — 공통 정책(실패 처리, GUI 창 멈춤 대처)
- `LICENSE` — MIT

## 라이선스

이 저장소의 파일(에이전트 지시문·references·도구)은 MIT 라이선스입니다(`LICENSE`). 에이전트가 다루는 앱(Inventor, Ansys SpaceClaim·SPEOS·Lumerical, Origin, PowerPoint)과 도구가 쓰는 Python 패키지는 들어 있지 않으며, 각자의 라이선스로 설치하고 그 약관을 따라야 합니다.
