# inventor/tools

| 파일 | 용도 |
|---|---|
| `step_check.py` | 피처 단계 판정 `[STEP PASS/WARN/FAIL]`(체적·면 수 전후, 이론 dV, base extrude bbox)·체적 되읽기 헬퍼(`CacheResultsOnCompute=False`). 지시 = `../AGENT.md` 절차 2·5, 판단 기준·함정 = `../references/inventor_ipt_modeling.md` 「피처 단계 검증」 |
| `inventor_session.py` | `launch()` = 이미 떠 있으면 거부(PID·창 제목), 아니면 기동 후 자기 PID 반환. `kill_own(pid)` = 자기 PID 만 종료. 이름 일괄 종료 금지 |
| `tests/test_step_check.py` | 단독 시험(Inventor 불필요): `python -m unittest discover -s tests` |
| `tests/live_step_check_inventor.py` | Inventor 실측 시험(수동 실행, 끝나면 프로세스 0 확인) |
