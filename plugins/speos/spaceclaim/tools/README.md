# spaceclaim tools

헤드리스 `/RunScript` 작업의 피처별 기하 판정과 orchestrator 공용 함수.

| 파일 | 실행 환경 | 역할 |
|---|---|---|
| `sc_geomcheck.py` | SpaceClaim IronPython 2.7 (+ CPython 시험) | `make_logger` · `snap` · `step_check` · `finish` → `[STEP]`·`[GEOM VERDICT]` 줄 |
| `sc_orchestrate.py` | CPython 3.12 | 컴파일 체크 → 좌석 대기 → launch → 판정 줄 polling → 자기 PID 종료 → 판정 반환 |
| `tests/` | CPython 3.12 | 판정 로직·로그 파싱 단독 시험 + `sc_geomcheck.py` IronPython 컴파일 체크 |

설치 경로는 환경 변수 `AWP_ROOT261`(Ansys 설치 프로그램이 만든다 — Student·정식 판 모두)에서 읽는다(`sc_orchestrate.py` 의 `ANSYS_ROOT`). 없으면 Student 판 기본 `C:\Program Files\ANSYS Inc\ANSYS Student\v261`.

## IronPython script 쪽

`sys.path` 에 `os.environ["SC_TOOLS"]`(이 폴더, `sc_orchestrate.run` 이 넣어 줌)를 추가한 뒤 import 한다. 모듈 최상위 `__file__` 금지.

```python
import sys, math, os
sys.path.insert(0, os.environ["SC_TOOLS"])
import sc_geomcheck as gc
log = gc.make_logger(LOG)            # utf-8, 줄마다 %H:%M:%S

def main():
    gc.init(log)
    ...block...
    s1 = gc.snap(block)              # (V_mm3, nFaces, nVerts, nBodies in part)
    gc.step_check("block", gc.EMPTY, s1, exp_dV=12000.0, exp_dF=6, exp_bodies=1)
    ...hole...
    s2 = gc.snap(part.Bodies[0])
    gc.step_check("hole", s1, s2, exp_dV=-math.pi*16*10, exp_dF=1, exp_bodies=1)
    gc.finish(OUT, DocumentSave.Execute)   # PASS → OUT, FAIL → OUT_FAIL; [GEOM VERDICT] 가 마지막 줄

try:
    main()
except:
    import traceback
    for _l in traceback.format_exception(*sys.exc_info()):
        log(u"%s" % _l)
    log(u"[FATAL] unhandled exception")
```

판정 (`judge`):

| 판정 | 조건 |
|---|---|
| FAIL | 준 기대값과 불일치 — `|dV−exp_dV| > tol`(기본 1e-7 mm³), `dF≠exp_dF`, 단계 후 바디 수 `≠exp_bodies` |
| WARN | 기대값 하나도 없음 / `exp_dV` 없이 `dV≈0`(무동작 의심) / dV·dF·바디 수 불변에 정점 수만 변함(imprint 의심) |
| PASS | 그 외 |

`[GEOM VERDICT] PASS` = step ≥1 이고 FAIL 0. WARN 은 PASS 를 막지 않는다. `exp_bodies` 는 증감이 아니라 단계 후 part 의 바디 수(접촉 솔리드 병합은 체적이 정확한 합이라 바디 수로만 드러남).

FAIL 시 최종 경로에 저장하지 않고 `<name>_FAIL.scdocx` 로 부분 저장한다(본문 "부분 .scdocx 경로 반환" 규칙과 같은 산출물).

## Orchestrator 쪽

```python
import sys, os
sys.path.insert(0, os.path.expanduser(r"<PLUGIN_ROOT>\spaceclaim\tools"))
from sc_orchestrate import run, ascii_safe
res = run(SCRIPT, LOG, OUT, timeout_s=300, speos=False)
print(ascii_safe(res["summary"]))   # 콘솔 cp949
```

- polling 종료: 로그에 `[GEOM VERDICT]` 또는 `[FATAL]` / 프로세스 종료 / timeout. 파일 생성은 종료 조건이 아니다 — 판정 줄이 저장 뒤에 쓰이므로 파일만 보고 멈추면 판정 줄을 놓친다.
- 반환 `verdict`: 로그의 판정 줄이 `PASS` 이면서 steps > 0·fail = 0·`[STEP FAIL]` 줄 없음이고, 이번 실행이 `out` 을 1KB 이상으로 썼고, 자기 PID 가 남지 않았을 때만 PASS. 아니면 FAIL + `problems` = `no_output`(로그는 PASS 인데 이번 실행이 쓴 결과 파일이 없거나 1KB 미만) / `residual`(자기 PID 가 남음). `kind` = `verdict` / `fatal` / `no_verdict`(판정 줄 없음) / `compile_error`(0바이트 로그 = 스크립트가 한 줄도 못 씀) / `seat_busy`(대기 후에도 좌석 점유 → launch 안 함) / `timeout` / `precompile_error`(launch 전 컴파일 체크 실패, 사유 = PowerShell 오류 문구).
- 아무것도 지우지 않는다. 지난 실행의 `out`·`*_FAIL` 은 남고, launch 뒤 바뀐 파일만 이번 결과(`out_new`·`fail_out_new`, summary 의 `out=new|old|no`). 로그만 launch 직전에 비운다 → 끝에 0바이트면 스크립트가 한 줄도 못 씀.
- PowerShell 이 실패하면(종료코드 ≠ 0) 예외로 멈춘다 — 좌석·잔존 프로세스 수를 0 으로 읽지 않는다.
- 다른 SpaceClaim 이 떠 있으면 kill 하지 않고 기다린다. 종료는 자기 PID 만(자체 종료 대기 → Force; headless 는 창이 없어 CloseMainWindow 무효). 대기는 최대 `seat_wait_s`(기본 300 s; 실측 135/240/203 s) 이고 사용자 GUI SpaceClaim 도 좌석으로 센다. 대기 후에도 점유면 launch 하지 않고 바로 `seat_busy`(FAIL) 반환 — 점유 좌석에 띄우면 timeout_s 를 다 쓰고 0바이트 로그로 끝날 뿐이다. 총 소요 ≤ seat_wait_s + timeout_s + ~40 s → Bash timeout 계산에 포함.
- `speos=True` 면 summary 에 `launcher=전->후`(AnsysSpeosLauncher 개수, 측정만). 2026-10-18 실측 1회 0->0.

## 시험

```bash
<python> -m unittest discover -s <PLUGIN_ROOT>/spaceclaim/tools/tests -v
```

실제 SpaceClaim 1회(2026-10-18): 40×30×10 블록 + Ø8 관통 구멍 → `PASS steps=2`, 26 s. 구멍 이론 dV 를 ×1.01 로 틀리게 → `FAIL steps=2 fail=1`, 최종 경로 미저장·`_FAIL` 저장, marker 로 26 s 종료.
