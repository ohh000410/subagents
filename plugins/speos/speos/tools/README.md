# speos tools

헤드리스 SPEOS `/RunScript` 실행 도구. **의존: `spaceclaim/tools/sc_orchestrate.py`**(같은 SpaceClaim 좌석·같은 규칙 — 복제하지 않고 import).

| 파일 | 실행 환경 | 역할 |
|---|---|---|
| `speos_run.py` | CPython | `run_speos(script, log, out, timeout_s, env)` = `sc_orchestrate.run(speos=True)` + env 전달. `sensor_flux_w(report_html)` |
| `smoke/sc_lambert_smoke.py` | SpaceClaim IronPython 2.7 | 10x10 mm Lambertian 1 W 소스(z=50) → 200x200 mm 조도 센서(z=0), 되읽기 13단계, 마지막 줄 `[GEOM VERDICT]` |
| `smoke/run_lambert_smoke.py` | CPython | 위 script 실행 + Report.html flux vs 해석값(약 0.831 W) 비교 |

## 규칙(sc_orchestrate 와 동일)

- 실행 전 compile check. 다른 SpaceClaim 이 떠 있으면 최대 300 s **대기**(죽이지 않음). 대기 후에도 남으면 launch 하지 않고 `kind=seat_busy`(FAIL) 로 바로 반환.
- 종료는 자기가 띄운 PID 만(자연 종료 30 s 대기 → `-Force`). 이름으로 SpaceClaim·AnsysSpeosLauncher 일괄 종료 금지. `AnsysSpeosLauncher` 는 `launcher_before/after` 로 측정만.
- script 는 Compute 이후 마지막 줄에 `[GEOM VERDICT] PASS|FAIL steps=N warn=W fail=F`(SPEOS 에서는 되읽기·StatusInfo·IsUpToDate 판정), 예외는 `[FATAL]`. 경로는 env 변수로 받음.

## 사용

```
<python> -I tools/smoke/run_lambert_smoke.py <work_dir> [nbrays]
```
한 줄 판정 예(2026-10-18): `[ORCH] PASS kind=verdict ... t=50.0s steps=13 fail=0 residual=0 launcher=0->0`, flux 0.8302 W vs 해석 0.8310 W(-0.1 %), `[SMOKE] PASS`.
