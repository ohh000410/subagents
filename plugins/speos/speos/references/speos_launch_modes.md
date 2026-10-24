# SpaceClaim launch 모드 + orchestrator

## 모드 1 — 일반 SpaceClaim

```python
ROOT = os.environ["AWP_ROOT261"]   # Ansys 설치 프로그램이 만든다
cmd = [ROOT + r"\scdm\SpaceClaim.exe",
       f"/RunScript={SCRIPT}", "/ScriptApi=261", "/Headless=True", "/Splash=False", "/ExitAfterScript=True"]
```
표준 API 만 (SketchCircle, SketchLine, RevolveEdges, NurbsCurve, DesignCurve). `SpeosDes.*` → NameError. cold start ~20초.

v261: `/Headless=True` 를 빼거나 `/Headless=False` 를 줘도 `/RunScript` 는 실행되고 `/ExitAfterScript=True` 로 스스로 끝남(실측: 로그 줄 27~28초, 종료 30~31초 — 헤드리스와 같음). 화면 세션에서는 모달 창이 실제로 뜰 수 있어 창 감시를 함께 둠(아래 「화면 모드의 경고 창」).

## 모드 2 — SPEOS plug-in (launcher 우회)

```python
ROOT = os.environ["AWP_ROOT261"]
cmd = [ROOT + r"\scdm\SpaceClaim.exe",
       "/LicenseFeature=speos_level1",
       "/AddInManifestFile=" + ROOT + r"\Optical Products\Speos\bin\SpeosSC.Manifest.xml",
       "/DefaultUserSettingsFile=" + ROOT + r"\Optical Products\Speos\bin\Resources\SPEOS_SCDefaultOptions.config",
       f"/RunScript={SCRIPT}", "/ScriptApi=261", "/Headless=True", "/Splash=False", "/ExitAfterScript=True"]
```
`SpeosDes.*` 사용 가능. cold start ~30초. `AnsysSpeosLauncher.exe` 는 인자를 받지 않음 — 위 인자는 launcher 가 SpaceClaim 을 띄울 때 쓰는 명령줄 그대로.

## Orchestrator (CPython) — spaceclaim 과 같은 좌석·같은 규칙

SpaceClaim 좌석은 spaceclaim 에이전트와 공유. 이름 일괄 종료(`Get-Process SpaceClaim, AnsysSpeosLauncher | Stop-Process`)는 다른 세션의 작업을 끊으므로 금지.
`tools/speos_run.py` 의 `run_speos()` 가 `spaceclaim/tools/sc_orchestrate.run(speos=True)` 를 import 해 그대로 씀(따로 구현하지 않음):
컴파일 체크 → 좌석 대기(다른 SpaceClaim 이 떠 있으면 최대 300 s 대기, 죽이지 않음) → 모드 2 launch → script 의 판정 줄 polling → **자기가 띄운 PID 만** 종료(자연 종료 30 s 대기 후 `-Force`) → 잔여·`AnsysSpeosLauncher` 개수 측정(종료 안 함).

- script 마지막 줄 = `[GEOM VERDICT] PASS|FAIL steps=N warn=W fail=F`(sc_orchestrate 가 polling 하는 줄. SPEOS 에서는 되읽기·StatusInfo·IsUpToDate 단계 판정), 예외 = `[FATAL]`. Compute 이후에 씀.
- `/RunScript` 는 인자를 못 받음 → 경로는 `run_speos(..., env={...})` 로 child 환경변수 전달.
- 좌석 대기 후에도 다른 SpaceClaim 이 남아 있으면 launch 하지 않고 `kind=seat_busy`(FAIL) 로 반환됨 → 보고하고 죽이지 않음.
- `AnsysSpeosLauncher` 잔존(`launcher_after > launcher_before`)은 측정만 하고 보고. 이름으로 죽이지 않음.
- 예: `tools/smoke/run_lambert_smoke.py`(10×10 mm Lambertian 1 W → 50 mm 위 200×200 mm 센서, 해석 ≈0.831 W). 자세한 내용 `tools/README.md`.
- stdout 은 PIPE 로 받지 않음(gui_modal_deadlock.md). Report.html 이 보여도 즉시 죽이지 않고 script 자연 종료를 기다림(close_pid 가 30 s 대기).

## 화면 모드(`/Headless=True` 없이)의 경고 창

- 시뮬레이션 경고가 'Simulation warning' 창으로 뜨고, 닫을 때까지 `sim.Compute()` 가 멈춤(9분 34초 관측, Report 는 창을 닫은 뒤에 써졌음). headless 는 같은 경고를 조용히 넘김.
- 관측된 원인: `BodyCrossingIrradianceSensor` — SensorIrradiance 는 전역 z=0 평면에 고정이라 z=0 에서 시작하는 body 와 맞닿음. 원인을 고침: body 를 z=0 에서 띄움.
- 감지: `(Get-Process -Id <pid>).MainWindowTitle` 에 'warning'·'error' 가 보이면 실패로 처리. 자동으로 닫고 계속하지 않음.
- 경고 이름이 남는 세션 로그: `%APPDATA%/Ansys/v261/Optical Products/SpaceClaim_<pid>.log`. `OPTElementNotFound ... ContainBodyItf` 'critical' 줄은 정상 실행에도 나옴.
