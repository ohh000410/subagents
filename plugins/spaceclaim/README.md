# spaceclaim

SPEOS·ANSYS 용 형상을 만듭니다.

에이전트 설명(Claude 가 맡길지 고를 때 읽는 글): SpaceClaim 3D geometry(.scdocx/.step) 에이전트. SPEOS·ANSYS로 넘길 형상과 광학 곡면(NURBS 등)을 만들거나 SpaceClaim API·IronPython·geometry 오류를 진단할 때 사용. 상담 모드는 진단(코드·근거만, memory write 금지), 실행 모드는 .scdocx/.step 생성→검증까지 수행 후 검증된 함정만 기록. 일반 기계 부품 모델링과 2D 도면·PDF는 inventor 담당.

## 설치

```
/plugin marketplace add ohh000410/subagents
/plugin install spaceclaim@ohh000410-subagents
```

설치하면 에이전트 이름은 `spaceclaim:spaceclaim` 입니다. 이 에이전트가 뜰 때만 도는 훅(`hooks/hooks.json`)이 함께 설치되어,
공통 규칙과 본문을 넣습니다.

## 필요한 것

- Windows PowerShell(Windows 에 기본으로 있음) — 위 훅이 씁니다.
| 항목 | 값 |
|---|---|
| 설치 위치 | `%AWP_ROOT261%` — Ansys 설치 프로그램이 만드는 환경 변수 |
| SpaceClaim.exe | `%AWP_ROOT261%\scdm\SpaceClaim.exe` |
| Speos AddIn manifest | `%AWP_ROOT261%\Optical Products\Speos\bin\SpeosSC.Manifest.xml` |
| ScriptApi | V261 (`/ScriptApi=261`) |
| 인터프리터 | IronPython 2.7 (Python 3 문법 금지) |
| Orchestrator | CPython — Python(`<python>`) = 이 PC 환경 값(메모리) |

실행 전 설치 경로 존재 확인. 버전 폴더명 상이(v252 등) → 즉시 반환 + 실제 폴더명 보고.

## 처음 쓸 때

- 에이전트가 환경 값(앱 경로·venv)을 찾지 못하면 묻습니다. 확인한 값은 에이전트 메모리 `~/.claude/agent-memory/spaceclaim-spaceclaim/` 에 남습니다.
- 도구 설명: `spaceclaim/tools/README.md`.

## 들어 있는 것

- `agents/spaceclaim.md` — 에이전트 껍데기(이름·설명·도구·모델, 파일 위치·메모리 안내)
- `spaceclaim/AGENT.md` — 본문. 에이전트가 뜰 때 훅이 공통 계약과 함께 넣는다
- `hooks/` — 그 훅(`spaceclaim:spaceclaim` 이 뜰 때만, Windows PowerShell)
- `spaceclaim/references/` — 11개 파일
- `spaceclaim/tools/` — 5개 파일
- `policies/` — 공통 계약(훅이 넣음), 공통 정책(실패 처리, GUI 창 멈춤 대처)
- `LICENSE` — MIT

## 라이선스

이 저장소의 파일(에이전트 지시문·references·도구)은 MIT 라이선스입니다(`LICENSE`). 에이전트가 다루는 앱(Inventor, Ansys SpaceClaim·SPEOS·Lumerical, Origin, PowerPoint)과 도구가 쓰는 Python 패키지는 들어 있지 않으며, 각자의 라이선스로 설치하고 그 약관을 따라야 합니다.
