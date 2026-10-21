# SpaceClaim launch 모드 + orchestrator

## 모드 1 — 일반 SpaceClaim

```python
cmd = [r"C:\Program Files\ANSYS Inc\ANSYS Student\v261\scdm\SpaceClaim.exe",
       f"/RunScript={SCRIPT}", "/ScriptApi=261", "/Headless=True", "/Splash=False", "/ExitAfterScript=True"]
```
표준 API 만 (SketchCircle, SketchLine, RevolveEdges, NurbsCurve, DesignCurve). `SpeosDes.*` → NameError. cold start ~20초.

## 모드 2 — SPEOS plug-in (launcher 우회)

```python
cmd = [r"C:\Program Files\ANSYS Inc\ANSYS Student\v261\scdm\SpaceClaim.exe",
       "/LicenseFeature=speos_level1",
       r"/AddInManifestFile=C:\Program Files\ANSYS Inc\ANSYS Student\v261\Optical Products\Speos\bin\SpeosSC.Manifest.xml",
       r"/DefaultUserSettingsFile=C:\Program Files\ANSYS Inc\ANSYS Student\v261\Optical Products\Speos\bin\Resources\SPEOS_SCDefaultOptions.config",
       f"/RunScript={SCRIPT}", "/ScriptApi=261", "/Headless=True", "/Splash=False", "/ExitAfterScript=True"]
```
`SpeosDes.*` 사용 가능. cold start ~30초. `AnsysSpeosLauncher.exe` 는 인자를 받지 않는다 — 위 인자는 launcher 가 SpaceClaim 을 띄울 때 쓰는 명령줄 그대로.

## Orchestrator (CPython 3.12) — spaceclaim 과 같은 좌석·같은 규칙

SpaceClaim 좌석은 spaceclaim 에이전트와 공유한다. 이름 일괄 종료(`Get-Process SpaceClaim, AnsysSpeosLauncher | Stop-Process`)는 다른 세션의 작업을 끊으므로 금지.
`tools/speos_run.py` 의 `run_speos()` 가 `spaceclaim/tools/sc_orchestrate.run(speos=True)` 를 import 해 그대로 쓴다(복제 없음):
컴파일 체크 → 좌석 대기(다른 SpaceClaim 이 떠 있으면 최대 300 s 대기, 죽이지 않음) → 모드 2 launch → script 의 판정 줄 polling → **자기가 띄운 PID 만** 종료(자연 종료 30 s 대기 후 `-Force`) → 잔여·`AnsysSpeosLauncher` 개수 측정(종료 안 함).

- script 마지막 줄 = `[GEOM VERDICT] PASS|FAIL steps=N warn=W fail=F`(sc_orchestrate 가 polling 하는 줄. SPEOS 에서는 되읽기·StatusInfo·IsUpToDate 단계 판정), 예외 = `[FATAL]`. Compute 이후에 쓴다.
- `/RunScript` 는 인자를 못 받는다 → 경로는 `run_speos(..., env={...})` 로 child 환경변수 전달.
- 좌석 대기 후에도 다른 SpaceClaim 이 남아 있으면 launch 하지 않고 `kind=seat_busy`(FAIL) 로 반환된다 → 보고하고 죽이지 않는다.
- `AnsysSpeosLauncher` 잔존(`launcher_after > launcher_before`)은 측정만 하고 보고한다. 이름으로 죽이지 않는다.
- 예: `tools/smoke/run_lambert_smoke.py`(10×10 mm Lambertian 1 W → 50 mm 위 200×200 mm 센서, 해석 ≈0.831 W). 자세한 내용 `tools/README.md`.
- stdout 은 PIPE 로 받지 않는다(gui_modal_deadlock.md). Report.html 이 보여도 즉시 죽이지 않고 script 자연 종료를 기다린다(close_pid 가 30 s 대기).
