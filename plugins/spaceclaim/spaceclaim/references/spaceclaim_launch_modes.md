# SpaceClaim launch 모드 + orchestrator

## 모드 1 — 일반 SpaceClaim

```python
ROOT = os.environ["AWP_ROOT261"]   # Ansys 설치 프로그램이 만든다
cmd = [ROOT + r"\scdm\SpaceClaim.exe",
       f"/RunScript={SCRIPT}", "/ScriptApi=261", "/Headless=True", "/Splash=False", "/ExitAfterScript=True"]
```
표준 API 만 (SketchCircle, SketchLine, RevolveEdges, NurbsCurve, DesignCurve). `SpeosDes.*` → NameError. cold start ~20초.

v261: `/Headless=True` 를 빼거나 `/Headless=False` 를 줘도 `/RunScript` 는 실행되고 `/ExitAfterScript=True` 로 스스로 끝남(실측: 로그 줄 27~28초, 종료 30~31초 — 헤드리스와 같음). 화면 세션에서는 모달 창이 실제로 뜰 수 있어 창 감시를 함께 둠.

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

## Orchestrator 템플릿 (CPython)

공용 함수는 `../tools/sc_orchestrate.py`(사용법·판정 규칙 `../tools/README.md`). orchestrator 는 경로만 정하고 `run` 을 부름.

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
2. 다른 SpaceClaim 이 0 이 될 때까지 최대 `seat_wait_s`(기본 300 s) 대기(kill 금지 — 공유 좌석, 사용자 GUI SpaceClaim 도 셈). 대기 후에도 점유면 launch 하지 않고 `seat_busy`(FAIL) 반환
3. OUT·`_FAIL` 의 상태(수정 시각·크기)를 적어 두고 LOG 만 비운 뒤 `Popen`(stdout=PIPE 금지, `gui_modal_deadlock.md`). 지난 결과는 지우지 않음 — 지우면 새 실행이 실패할 때 지난 결과까지 사라졌음
4. polling 종료: 로그에 `[GEOM VERDICT]` 또는 `[FATAL]` / 프로세스 종료 / timeout. 파일 생성은 종료 조건이 아님(판정 줄이 저장 뒤에 쓰임)
5. 자기 PID 만 종료: 자체 종료 대기 → `-Force` (headless 는 창이 없어 `CloseMainWindow()` 무효, `policies/gui_modal_deadlock.md`)
6. 로그를 정규식으로 읽어 `verdict`·`kind` 반환. 판정 줄 없으면 FAIL, 판정 줄이 PASS 여도 steps 0·fail > 0·`[STEP FAIL]` 줄이면 FAIL, 0바이트 로그는 `compile_error`. PASS 는 이번 실행이 OUT 을 1KB 이상으로 썼을 때만(OUT 상태가 3 단계와 달라야 함)

- 정상 종료 script: `/ExitAfterScript=True` 로 marker 후 ~2초에 자체 종료(v261 실측). exception 으로 끝난 script 는 hang 가능 → 5 단계의 PID 종료가 처리
- 정리 대상: 자기가 띄운 `SpaceClaim` PID. SPEOS 모드의 `AnsysSpeosLauncher` 는 `speos=True` 일 때 `run` 이 launch 전·종료 후 개수를 `launcher=전->후` 로 보고(정리는 안 함). 2026-10-18 실측 1회: 0->0, +5초 뒤에도 0. `SpeosRPC_Server` 는 PySpeos 용, 무관
