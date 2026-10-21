# lumerical/tools

lumerical 에이전트 실행 모드 검증 도구. 범위 = memory 에 실패로 기록된 함정만. 판정 PASS / WARN / FAIL.

| 파일 | 시점 | 입력 | 실패 시 |
|---|---|---|---|
| `check_setup.py` | `save()` 뒤, `run()` 앞 | 실행 중 lumapi 세션 handle + `intended` dict | FAIL → `SetupCheckError` (run 금지) |
| `assess_run.py` | run·추출 뒤 | `_p0.log` / `.fsp` / 결과 csv·xlsx·json(l) / 폴더 (lumapi 불필요) | 종료코드 0/1/2 = PASS/WARN/FAIL |

`_p0.log` 의 autoshutoff·완주 판정 파서는 `assess_run.parse_p0_log` 하나뿐이다. 실행 스크립트에 별도 파서를 두지 않는다.
사용법·`intended` 스키마 = 각 파일 docstring. 검사별 근거 memory leaf = 각 검사 함수 주석.
