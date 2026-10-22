# origin-plot

논문 형식 그래프를 그립니다.

에이전트 설명(Claude 가 맡길지 고를 때 읽는 글): OriginLab Origin 그래프 생성·스타일링·export 전담 상담·실행 에이전트. Origin(win32com COM) 그래프를 논문 형식으로 그리거나 기존 .opju 스타일을 재현하는 요청, LabTalk/축/범례/심볼 스타일 질문을 처리한다. "오리진으로 그래프 그려줘", "이 논문 그래프 형식 따라해", "opju 스타일 재현", "LabTalk으로 축/범례 설정" 요청 시 사용. 데이터 계산·해석·물리 판단은 관할 외.

## 설치

```
/plugin marketplace add ohh000410/subagents
/plugin install origin-plot@ohh000410-subagents
```

설치하면 에이전트 이름은 `origin-plot:origin-plot` 입니다.

## 필요한 것

- Origin 2019. `originpro` 불가. win32com COM: `app = w32.Dispatch("Origin.ApplicationSI")`
- Python(`<python>`): 이 PC 환경 값(메모리)의 절대경로
- 원본 `.opju`: `app.Load`만. 산출물: 다른 경로, `app.Save(r"...")`, 백슬래시 경로
- 검증 도구: `tools/origin_verify.py` (사용법·`intended` 스키마 = docstring, 검사별 근거 = 보고의 `ref` 칸·각 검사 주석의 references 파일, 개요 `tools/README.md`). 세션 시작·LabTalk 전송·종료는 이 도구로만

도구가 쓰는 Python 패키지: `pywin32`

## 처음 쓸 때

- 에이전트가 환경 값(앱 경로·venv)을 찾지 못하면 묻습니다. 확인한 값은 에이전트 메모리 `~/.claude/agent-memory/origin-plot-origin-plot/` 에 남습니다.
- 도구 설명: `origin-plot/tools/README.md`.

## 들어 있는 것

- `agents/origin-plot.md` — 에이전트 정의(공통 규칙 + 본문)
- `origin-plot/references/` — 5개 파일
- `origin-plot/tools/` — 3개 파일
- `policies/` — 공통 정책(실패 처리, GUI 창 멈춤 대처)
- `LICENSE` — MIT

## 라이선스

이 저장소의 파일(에이전트 지시문·references·도구)은 MIT 라이선스입니다(`LICENSE`). 에이전트가 다루는 앱(Inventor, Ansys SpaceClaim·SPEOS·Lumerical, Origin, PowerPoint)과 도구가 쓰는 Python 패키지는 들어 있지 않으며, 각자의 라이선스로 설치하고 그 약관을 따라야 합니다.
