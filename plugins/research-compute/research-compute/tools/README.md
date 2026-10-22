# research-compute/tools

| 파일 | 용도 |
|---|---|
| `checks.py` | RCWA 계산 뒤 판정 줄 `PASS/WARN/FAIL` — A `result_bounds`(유한값·R,T≥0·0≤eps≤1), B `requested_vs_used`(요청 대 실사용 설정, meent·grcwa·torcwa 되읽기), C `convergence_line`(기존 수렴 규칙의 결과를 한 줄로), D `mirror_fixture`(새 형상 첫 calibration ±θ). 지시 = `../../agents/research-compute.md` 작업 3·5, 기준·함정 = `../references/rcwa_reference_index.md` 「판정 줄」 |
| `tests/test_checks.py` | 단독·실계산 시험: `<python> tests/test_checks.py` (meent·grcwa 필요, 수십 초) |

`references/snippets/` 는 읽기 전용 예시 코드만 둔다(실행 도구는 여기).
