# plot-digitizer

그래프 이미지에서 수치를 뽑습니다.

에이전트 설명(Claude 가 맡길지 고를 때 읽는 글): 논문·문헌 figure(polar half-circle, cartesian line/scatter)의 곡선을 정량 데이터(angle/x vs value)로 추출하는 에이전트. cross-validation·선행연구 참고값 추출 등 그래프에서 수치를 읽어내야 할 때 use proactively. 이미지가 없거나 저해상도면 원본 PDF에서 직접 고해상도로 확보하고(벡터/raster 구분), half-circle polar는 축 클릭 없이 자동 캘리브(반원 기하 교차검증)를 시도하며, 필요 시 picker 서버로 사용자 클릭 캘리브를 받는다. 항상 csv + 추출 검증 overlay + 캘리브 체크 overlay png를 반환한다. "이 그래프 디지타이즈해줘", "논문 figure 값 추출", "polar plot 곡선 읽어줘" 요청에 호출.

## 설치

```
/plugin marketplace add ohh000410/subagents
/plugin install plot-digitizer@ohh000410-subagents
```

설치하면 에이전트 이름은 `plot-digitizer:plot-digitizer` 입니다. 이 에이전트가 뜰 때만 도는 훅(`hooks/hooks.json`)이 함께 설치되어,
공통 규칙과 본문을 넣습니다.

## 필요한 것

- Windows PowerShell(Windows 에 기본으로 있음) — 위 훅이 씁니다.
- 환경: Python(`<python>`) = 이 PC 환경 값(메모리) — numpy, opencv-python, matplotlib, Pillow

도구·예제 코드가 쓰는 Python 패키지: `matplotlib`, `numpy`, `pillow`, `pymupdf`

## 처음 쓸 때

- 에이전트가 환경 값(앱 경로·venv)을 찾지 못하면 묻습니다. 확인한 값은 에이전트 메모리 `~/.claude/agent-memory/plot-digitizer-plot-digitizer/` 에 남습니다.
- 도구 설명: `plot-digitizer/tools/README.md`.

## 들어 있는 것

- `agents/plot-digitizer.md` — 에이전트 껍데기(이름·설명·도구·모델, 파일 위치·메모리 안내)
- `plot-digitizer/AGENT.md` — 본문. 에이전트가 뜰 때 훅이 공통 계약과 함께 넣는다
- `hooks/` — 그 훅(`plot-digitizer:plot-digitizer` 이 뜰 때만, Windows PowerShell)
- `plot-digitizer/references/` — 2개 파일
- `plot-digitizer/tools/` — 6개 파일
- `policies/` — 공통 계약(훅이 넣음), 공통 정책(실패 처리, GUI 창 멈춤 대처)
- `LICENSE` — MIT

## 라이선스

이 저장소의 파일(에이전트 지시문·references·도구)은 MIT 라이선스입니다(`LICENSE`). 에이전트가 다루는 앱(Inventor, Ansys SpaceClaim·SPEOS·Lumerical, Origin, PowerPoint)과 도구가 쓰는 Python 패키지는 들어 있지 않으며, 각자의 라이선스로 설치하고 그 약관을 따라야 합니다.
