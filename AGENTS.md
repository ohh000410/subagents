# AGENTS.md

AI 에이전트용 설치·사용 안내. 사람용 소개는 `README.md`.
이 저장소는 Claude Code 플러그인 마켓플레이스 `ohh000410-subagents` 이고, 플러그인 하나 = 서브에이전트 하나다.

## 고르기

| 사용자가 하려는 일 | 플러그인 | 필요한 앱 |
|---|---|---|
| 문서 사진 → 스캔본·PDF | `doc-scan` | 없음 |
| 그래프 이미지 → 수치 | `plot-digitizer` | 웹 브라우저 |
| PowerPoint 도형 그림 | `pptx-figure` | PowerPoint |
| Origin 그래프 | `origin-plot` | Origin 2019 |
| 부품 3D 모델·2D 도면 | `inventor` | Inventor 2027 |
| SPEOS·ANSYS 용 형상 | `spaceclaim` | SpaceClaim v261 |
| SPEOS 광학 시뮬레이션 | `speos` | SPEOS v261 |
| Lumerical FDTD·RCWA·STACK | `lumerical` | Lumerical v242 |
| Python RCWA·산란·열전달 계산 | `research-compute` | 없음 |

모두 Python 을 쓴다(SpaceClaim·SPEOS 의 실행 스크립트는 CPython 3.12). 앱의 검증한 판·설치 경로와 Python 패키지는 `plugins/<플러그인>/README.md` 의 "필요한 것".

## 설치

1. 설치할 플러그인과 범위(모든 프로젝트 = `user`, 이 프로젝트만 = `project`)를 사용자에게 확인한다.
2. `claude plugin marketplace add ohh000410/subagents` (Claude Code 대화 안에서는 `/plugin marketplace add ohh000410/subagents`)
3. 플러그인마다 `claude plugin install <플러그인>@ohh000410-subagents` — 이 프로젝트만이면 `--scope project`
4. `claude plugin details <플러그인>@ohh000410-subagents` 로 에이전트 1개가 잡혔는지 확인한다.
5. `plugins/<플러그인>/README.md` 의 "필요한 것"에 적힌 앱과 경로가 이 PC 에 있는지 확인하고, 없거나 다르면 사용자에게 알린다.
6. 에이전트는 새 세션부터 보인다. 이름은 `<플러그인>:<플러그인>` (예: `inventor:inventor`).

## 쓰기

- 할 일을 그 에이전트에게 맡긴다. 실행을 명시하지 않으면 상담 모드(읽기·진단만)다.
- 첫 실행 때 에이전트가 환경 값(앱 경로·venv)을 확인해 자기 메모리에 남긴다. 확인할 수 없으면 사용자에게 묻는다.
- 앱 라이선스와 약관은 사용자 몫이다(`README.md` 의 라이선스 절).

## 지우기

`claude plugin uninstall <플러그인>@ohh000410-subagents` — 모두 지웠으면 `claude plugin marketplace remove ohh000410-subagents`. 에이전트 메모리(`~/.claude/agent-memory/<플러그인>-<플러그인>/`)는 남으니 필요 없으면 지운다.
