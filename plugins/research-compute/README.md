# research-compute

RCWA·산란·원거리장 복사 열전달.

에이전트 설명(Claude 가 맡길지 고를 때 읽는 글): Python 기반 RCWA, TMM/Fresnel, Mie·core-shell 산란, 원거리장 복사 열전달 계산을 수행하고 수렴·cross-check까지 검증하는 에이전트. FDTD와 Lumerical RCWA·STACK은 관할 밖이다.

## 설치

```
/plugin marketplace add ohh000410/subagents
/plugin install research-compute@ohh000410-subagents
```

설치하면 에이전트 이름은 `research-compute:research-compute` 입니다.

## 필요한 것

앱·라이브러리는 에이전트 본문(`agents/research-compute.md`)을 보세요.

도구가 쓰는 Python 패키지: `grcwa`, `meent`, `numpy`

## 처음 쓸 때

- 에이전트가 환경 값(앱 경로·venv)을 찾지 못하면 묻습니다. 확인한 값은 에이전트 메모리 `~/.claude/agent-memory/research-compute-research-compute/` 에 남습니다.
- 도구 설명: `research-compute/tools/README.md`.

## 들어 있는 것

- `agents/research-compute.md` — 에이전트 정의(공통 규칙 + 본문)
- `research-compute/references/` — 12개 파일
- `research-compute/tools/` — 3개 파일
- `policies/` — 공통 정책(실패 처리, GUI 창 멈춤 대처)
- `LICENSE` — MIT

## 라이선스

이 저장소의 파일(에이전트 지시문·references·도구)은 MIT 라이선스입니다(`LICENSE`). 에이전트가 다루는 앱(Inventor, Ansys SpaceClaim·SPEOS·Lumerical, Origin, PowerPoint)과 도구가 쓰는 Python 패키지는 들어 있지 않으며, 각자의 라이선스로 설치하고 그 약관을 따라야 합니다.
