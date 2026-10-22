# SpaceClaim launch 모드 + orchestrator

## 모드 1 — 일반 SpaceClaim

```python
cmd = [r"C:\Program Files\ANSYS Inc\ANSYS Student\v261\scdm\SpaceClaim.exe",
       f"/RunScript={SCRIPT}", "/ScriptApi=261", "/Headless=True", "/Splash=False", "/ExitAfterScript=True"]
```
표준 API 만 (SketchCircle, SketchLine, RevolveEdges, NurbsCurve, DesignCurve). `SpeosDes.*` → NameError. cold start ~20초.

v261: `/Headless=True` 를 빼거나 `/Headless=False` 를 줘도 `/RunScript` 는 실행되고 `/ExitAfterScript=True` 로 스스로 끝난다(2026-10-22 실측: 로그 줄 27~28초, 종료 30~31초 — 헤드리스와 같다). 화면 세션에서는 모달 창이 실제로 뜰 수 있어 창 감시를 함께 둔다.

## 모드 2 — SPEOS plug-in (launcher 우회)

```python
cmd = [r"C:\Program Files\ANSYS Inc\ANSYS Student\v261\scdm\SpaceClaim.exe",
       "/LicenseFeature=speos_level1",
       r"/AddInManifestFile=C:\Program Files\ANSYS Inc\ANSYS Student\v261\Optical Products\Speos\bin\SpeosSC.Manifest.xml",
       r"/DefaultUserSettingsFile=C:\Program Files\ANSYS Inc\ANSYS Student\v261\Optical Products\Speos\bin\Resources\SPEOS_SCDefaultOptions.config",
       f"/RunScript={SCRIPT}", "/ScriptApi=261", "/Headless=True", "/Splash=False", "/ExitAfterScript=True"]
```
`SpeosDes.*` 사용 가능. cold start ~30초. `AnsysSpeosLauncher.exe` 는 인자를 받지 않는다 — 위 인자는 launcher 가 SpaceClaim 을 띄울 때 쓰는 명령줄 그대로.

## Orchestrator 템플릿 (CPython 3.12)

공용 함수는 `../tools/sc_orchestrate.py`(사용법·판정 규칙 `../tools/README.md`). orchestrator 는 경로만 정하고 `run` 을 부른다.

```python
from __future__ import annotations
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.expanduser(r"<PLUGIN_ROOT>\spaceclaim\tools"))
from sc_orchestrate import run, ascii_safe

HERE   = Path(__file__).parent
SCRIPT = HERE / "sc_<name>.py"
OUT    = HERE / "<name>.scdocx"      # FAIL 이면 <name>_FAIL.scdocx
LOG    = HERE / "<name>.log"

res = run(SCRIPT, LOG, OUT, timeout_s=300, speos=False)
print(ascii_safe(res["summary"]))     # 콘솔 cp949 → ASCII 화
for l in res.get("step_lines", []):
    print("   ", ascii_safe(l))
sys.exit(0 if res["verdict"] == "PASS" else 1)
```

`run` 의 순서:

1. hosted IronPython 컴파일 체크 — 실패 시 launch 없이 `precompile_error`
2. 다른 SpaceClaim 이 0 이 될 때까지 최대 `seat_wait_s`(기본 300 s) 대기(kill 금지 — 공유 좌석, 사용자 GUI SpaceClaim 도 센다). 대기 후에도 점유면 launch 하지 않고 `seat_busy`(FAIL) 반환
3. OUT·`_FAIL`·LOG 삭제 후 LOG 를 빈 파일로 생성 → `Popen`(stdout=PIPE 금지, `gui_modal_deadlock.md`)
4. polling 종료: 로그에 `[GEOM VERDICT]` 또는 `[FATAL]` / 프로세스 종료 / timeout. 파일 생성은 종료 조건이 아니다(판정 줄이 저장 뒤에 쓰임)
5. 자기 PID 만 종료: 자체 종료 대기 → `-Force` (headless 는 창이 없어 `CloseMainWindow()` 무효, `policies/gui_modal_deadlock.md`)
6. 로그를 정규식으로 읽어 `verdict`·`kind` 반환. 판정 줄 없으면 FAIL, 0바이트 로그는 `compile_error`(launch 시 다른 SpaceClaim 있었으면 `seat_contention`)

- 정상 종료 script: `/ExitAfterScript=True` 로 marker 후 ~2초에 자체 종료(v261 실측). exception 으로 끝난 script 는 hang 가능 → 5 단계의 PID 종료가 처리
- 정리 대상: 자기가 띄운 `SpaceClaim` PID. SPEOS 모드의 `AnsysSpeosLauncher` 는 `speos=True` 일 때 `run` 이 launch 전·종료 후 개수를 `launcher=전->후` 로 보고(정리는 안 함). 2026-10-18 실측 1회: 0->0, +5초 뒤에도 0. `SpeosRPC_Server` 는 PySpeos 용, 무관
