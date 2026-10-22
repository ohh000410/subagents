# speos

광학 시뮬레이션을 돌리고 정리합니다.

에이전트 설명(Claude 가 맡길지 고를 때 읽는 글): ANSYS SPEOS Direct simulation 상담·실행 에이전트. SPEOS sim 실행(sim 돌려줘·mesh sweep· ellipse_flux 추출)이나 NbRays·mesh·sensor·Report/API 오류를 진단할 때 사용. 상담 모드는 진단(코드·근거만, memory write 금지), 실행 모드는 base.scdocx 기반 Compute→Report 파싱→xlsx 저장까지 수행 후 검증된 함정만 기록. Geometry·FDTD·분석은 관할 외.

## 설치

```
/plugin marketplace add ohh000410/subagents
/plugin install speos@ohh000410-subagents
```

설치하면 에이전트 이름은 `speos:speos` 입니다.

## 필요한 것

| 항목 | 값 |
|---|---|
| 설치 위치 | `%AWP_ROOT261%` — Ansys 설치 프로그램이 만드는 환경 변수 |
| SpaceClaim.exe | `%AWP_ROOT261%\scdm\SpaceClaim.exe` |
| Speos AddIn manifest | `%AWP_ROOT261%\Optical Products\Speos\bin\SpeosSC.Manifest.xml` |
| Speos 기본 설정 | `%AWP_ROOT261%\Optical Products\Speos\bin\Resources\SPEOS_SCDefaultOptions.config` |
| License feature | `speos_level1` (plug-in 모드 필수) |
| 인터프리터 | SpaceClaim 내장 IronPython 2.7 (Python 3 문법 금지) |
| Orchestrator | CPython — Python(`<python>`) = 이 PC 환경 값(메모리) |
| Student 한도 | triangle < 32,000 + face < 300 (scene 합산). 거부 = 예외 아님, `sim.StatusInfo`만. face 한도 LocalMeshing으로 불가 → `speos/references/speos_pitfalls_sim_workflow.md` |

실행 전 설치 경로 존재 확인. 버전 폴더명 상이(v252 등) → 즉시 반환 + 실제 폴더명 보고.

도구·예제 코드가 쓰는 Python 패키지: `openpyxl`

## 처음 쓸 때

- 에이전트가 환경 값(앱 경로·venv)을 찾지 못하면 묻습니다. 확인한 값은 에이전트 메모리 `~/.claude/agent-memory/speos-speos/` 에 남습니다.
- 도구 설명: `speos/tools/README.md`.

## 들어 있는 것

- `agents/speos.md` — 에이전트 정의(공통 규칙 + 본문)
- `speos/references/` — 17개 파일
- `speos/tools/` — 5개 파일
- `spaceclaim/tools/` — 의존 도구(spaceclaim 에이전트의 tools)
- `policies/` — 공통 정책(실패 처리, GUI 창 멈춤 대처)
- `LICENSE` — MIT

## 라이선스

이 저장소의 파일(에이전트 지시문·references·도구)은 MIT 라이선스입니다(`LICENSE`). 에이전트가 다루는 앱(Inventor, Ansys SpaceClaim·SPEOS·Lumerical, Origin, PowerPoint)과 도구가 쓰는 Python 패키지는 들어 있지 않으며, 각자의 라이선스로 설치하고 그 약관을 따라야 합니다.
