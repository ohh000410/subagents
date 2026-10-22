"""CPython 3.12 orchestrator helpers for headless SpaceClaim /RunScript.

Polling stops on a log marker ([GEOM VERDICT] or [FATAL]) or on process exit;
the verdict is then read back from the log. No marker -> FAIL.

    import os, sys
    sys.path.insert(0, os.path.expanduser(r"<PLUGIN_ROOT>\\spaceclaim\\tools"))
    from sc_orchestrate import run, ascii_safe
    res = run(SCRIPT, LOG, OUT, timeout_s=300)
    print(ascii_safe(res["summary"]))
"""
from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path

SC_EXE = r"C:\Program Files\ANSYS Inc\ANSYS Student\v261\scdm\SpaceClaim.exe"
SC_DIR = r"C:\Program Files\ANSYS Inc\ANSYS Student\v261\scdm"
SPEOS_ARGS = [
    "/LicenseFeature=speos_level1",
    r"/AddInManifestFile=C:\Program Files\ANSYS Inc\ANSYS Student\v261\Optical Products\Speos\bin\SpeosSC.Manifest.xml",
    r"/DefaultUserSettingsFile=C:\Program Files\ANSYS Inc\ANSYS Student\v261\Optical Products\Speos\bin\Resources\SPEOS_SCDefaultOptions.config",
]

VERDICT_RE = re.compile(r"\[GEOM VERDICT\] (PASS|FAIL) steps=(\d+) warn=(\d+) fail=(\d+)")
STEP_RE = re.compile(r"\[STEP (PASS|WARN|FAIL)\].*")
FATAL_RE = re.compile(r"\[FATAL\]")


def ascii_safe(s: str) -> str:
    """Bash-tool console is cp949; printing Korean paths can raise UnicodeEncodeError."""
    return s.encode("ascii", "backslashreplace").decode("ascii")


def fail_path(path: Path) -> Path:
    """Same rule as sc_geomcheck.fail_path: model.scdocx -> model_FAIL.scdocx"""
    return path.with_name(path.stem + "_FAIL" + path.suffix)


def parse_log(text: str) -> dict:
    """Read the geometry verdict from log text. Pure function.

    kind: verdict | fatal | no_verdict | empty_log
    """
    steps = [m.group(0).strip() for m in STEP_RE.finditer(text)]
    fatal = bool(FATAL_RE.search(text))
    ms = list(VERDICT_RE.finditer(text))
    res = {"verdict": "FAIL", "kind": "", "steps": None, "warn": None, "fail": None,
           "verdict_line": "", "step_lines": steps, "fatal": fatal}
    if text == "":
        res["kind"] = "empty_log"
    elif fatal:
        res["kind"] = "fatal"
    elif not ms:
        res["kind"] = "no_verdict"
    else:
        m = ms[-1]
        res.update(kind="verdict", verdict=m.group(1), steps=int(m.group(2)),
                   warn=int(m.group(3)), fail=int(m.group(4)), verdict_line=m.group(0))
    return res


def log_has_marker(text: str) -> bool:
    return bool(VERDICT_RE.search(text) or FATAL_RE.search(text))


def _ps(cmd: str, timeout: int = 60) -> str:
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True,
                       timeout=timeout, encoding="utf-8", errors="replace")
    return (r.stdout or "").strip()


def sc_count() -> int:
    """All SpaceClaim processes (seat check). Never used for killing."""
    out = _ps("(Get-Process SpaceClaim -ErrorAction SilentlyContinue | Measure-Object).Count")
    return int(out or 0)


def launcher_count() -> int:
    """AnsysSpeosLauncher processes (SPEOS mode residual measurement only, never killed)."""
    out = _ps("(Get-Process AnsysSpeosLauncher -ErrorAction SilentlyContinue | Measure-Object).Count")
    return int(out or 0)


def compile_check(script: Path) -> str:
    """Hosted IronPython compile check, no SpaceClaim launch. Returns 'COMPILE OK' or the error."""
    cmd = (
        f'$dir = "{SC_DIR}";'
        'Add-Type -Path "$dir\\Microsoft.Scripting.dll";'
        'Add-Type -Path "$dir\\Microsoft.Dynamic.dll";'
        'Add-Type -Path "$dir\\IronPython.dll";'
        '$eng = [IronPython.Hosting.Python]::CreateEngine();'
        f"$src = $eng.CreateScriptSourceFromFile('{script}');"
        'try { $null = $src.Compile(); "COMPILE OK" } catch {'
        ' $e = $_.Exception; while ($e.InnerException) { $e = $e.InnerException };'
        ' $m = $e.Message;'
        ' if ($e -is [Microsoft.Scripting.SyntaxErrorException]) { $m += " LINE " + $e.Line + " COL " + $e.Column };'
        ' $m }'
    )
    return _ps(cmd)


def close_pid(pid: int, wait_s: int = 30) -> int:
    """Close only our own PID: wait for self-exit, then -Force (headless has no window, so
    CloseMainWindow does nothing: policies/gui_modal_deadlock.md). Returns 1 if the PID is still alive afterwards, else 0."""
    out = _ps(
        f"$deadline = (Get-Date).AddSeconds({wait_s});"
        f"while ((Get-Process -Id {pid} -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline) {{ Start-Sleep -Milliseconds 500 }};"
        f"$p = Get-Process -Id {pid} -ErrorAction SilentlyContinue;"
        "if ($p) {"
        f" Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 1 }};"
        f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue | Measure-Object).Count",
        timeout=wait_s + 30)
    return int(out or 0)


def run(script, log, out, timeout_s: int = 300, speos: bool = False, poll_s: float = 2.0,
        seat_wait_s: int = 300) -> dict:
    """Launch SpaceClaim headless, poll until marker / exit / timeout, close own PID, read verdict.

    PASS only when the log carries [GEOM VERDICT] PASS. kind:
      verdict | fatal | no_verdict | compile_error (0-byte log, no other SpaceClaim at launch)
      | seat_busy (seat still taken after seat_wait_s -> not launched)
      | seat_contention (0-byte log, another SpaceClaim appeared at launch) | timeout | precompile_error
    """
    script, log, out = Path(script), Path(log), Path(out)
    t0 = time.time()
    res = {"script": str(script), "log": str(log), "out": str(out), "fail_out": str(fail_path(out))}

    cc = compile_check(script)
    if cc != "COMPILE OK":
        res.update(verdict="FAIL", kind="precompile_error", detail=cc, elapsed=0.0, residual=0)
        res["summary"] = f"[ORCH] FAIL kind=precompile_error {cc}"
        return res

    # Seat: wait (measured waits 135/240/203 s; any SpaceClaim counts, incl. a GUI one), never kill other instances (references/spaceclaim_pitfalls_ironpython.md, leftover processes).
    while sc_count() > 0 and time.time() - t0 < seat_wait_s:
        time.sleep(20)
    seat = sc_count()
    waited = round(time.time() - t0, 1)
    if seat > 0:
        # Launching onto a taken seat only ends in a 0-byte log after timeout_s (seat_contention) -- return now.
        res.update(verdict="FAIL", kind="seat_busy", seat_at_launch=seat, seat_wait=waited, elapsed=0.0, residual=0)
        res["summary"] = (f"[ORCH] FAIL kind=seat_busy seat={seat} waited={waited:.0f}s "
                          "(not launched; another SpaceClaim, possibly a GUI one, holds the seat)")
        return res

    for p in (out, fail_path(out), log):
        if p.exists():
            p.unlink()
    log.touch()   # pre-created: 0 bytes at the end means the script never logged

    cmd = [SC_EXE] + (SPEOS_ARGS if speos else []) + [
        f"/RunScript={script}", "/ScriptApi=261", "/Headless=True", "/Splash=False", "/ExitAfterScript=True"]
    lau0 = launcher_count() if speos else None
    t1 = time.time()
    # SC_TOOLS = this folder: IronPython scripts import sc_geomcheck from os.environ["SC_TOOLS"]
    env = dict(os.environ, SC_TOOLS=str(Path(__file__).resolve().parent))
    proc = subprocess.Popen(cmd, env=env)   # no stdout=PIPE (gui_modal_deadlock)
    stop = "timeout"
    while time.time() - t1 < timeout_s:
        if log_has_marker(log.read_text(encoding="utf-8", errors="replace")):
            stop = "marker"
            break
        if proc.poll() is not None:
            stop = "exited"
            break
        time.sleep(poll_s)
    t_stop = time.time() - t1
    residual = close_pid(proc.pid)
    lau1 = launcher_count() if speos else None   # AnsysSpeosLauncher: measured, not cleaned

    text = log.read_text(encoding="utf-8", errors="replace")
    pr = parse_log(text)
    kind = pr["kind"]
    if kind == "empty_log":
        kind = "compile_error" if seat == 0 else "seat_contention"
    if stop == "timeout" and kind != "verdict" and kind != "fatal":
        kind = "timeout"
    verdict = pr["verdict"] if kind == "verdict" else "FAIL"
    res.update(pr)
    res.update(verdict=verdict, kind=kind, stop=stop, seat_at_launch=seat, seat_wait=waited, pid=proc.pid,
               elapsed=round(t_stop, 1), residual=residual,
               out_exists=out.exists(), out_size=out.stat().st_size if out.exists() else 0,
               fail_out_exists=fail_path(out).exists())
    res.update(launcher_before=lau0, launcher_after=lau1)
    lau = "" if not speos else f" launcher={lau0}->{lau1}"
    res["summary"] = (f"[ORCH] {verdict} kind={kind} stop={stop} t={t_stop:.1f}s "
                      f"{pr['verdict_line'] or '(no verdict line)'} residual={residual}{lau} "
                      f"out={'yes' if res['out_exists'] else 'no'} fail_out={'yes' if res['fail_out_exists'] else 'no'}")
    return res
