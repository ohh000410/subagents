# SPEOS Sim — Sweep 반복

```python
import json, traceback
from openpyxl import load_workbook

def run_one_case(case_params, ...):
    """1 case → 결과 dict 또는 fail dict. raise 하지 않는다."""
    try:
        ...   # SpaceClaim launch + sc_sim.py + Report 파싱
        return {"status": "OK", "flux": flux_val, ...}
    except Exception as e:
        return {"status": "FAIL", "error": str(e), "traceback": traceback.format_exc()}

for case in cases:
    r = run_one_case(case, ...)
    append_row_to_xlsx(xlsx_path, sheet_name, case, r)   # case 직후 기록 (중간 결과 보존)
    if r["status"] == "FAIL": print(f"[case {case}] FAIL: {r['error']}")
```
한 case FAIL = 그 row 만 FAIL, 다음 case 계속. 전부 FAIL → escalate.

## 3D grid — 32k 초과 (sag, angle) 쌍 SKIP

같은 (sag, angle) 은 step 무관 triangle 수 동일.
```python
sag_angle_fail = set()
for sag in SAG_LIST:
    for angle in ANGLE_LIST:
        pair = (sag, angle)
        for step in STEP_LIST:
            if pair in sag_angle_fail:
                append_row_to_xlsx({..., "sim_status": "SKIP", "note": "32k limit"}); continue
            r = run_one_case(sag, angle, step)
            if r["sim_status"] == "FAIL" and "triangle" in r["note"].lower(): sag_angle_fail.add(pair)
```
재시작: xlsx 기존 FAIL row 에서 (sag, angle) 복원 → `sag_angle_fail` 사전 추가.
