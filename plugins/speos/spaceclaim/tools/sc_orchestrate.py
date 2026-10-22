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

# Install root: the Ansys installer sets AWP_ROOT261 (Student and full editions alike); default = Student path
ANSYS_ROOT = os.environ.get("AWP_ROOT261", r"C:\Program Files\ANSYS Inc\ANSYS Student\v261")
SC_DIR = ANSYS_ROOT + r"\scdm"
SC_EXE = SC_DIR + r"\SpaceClaim.exe"
SPEOS_BIN = ANSYS_ROOT + r"\Optical Products\Speos\bin"
SPEOS_ARGS = [
    "/LicenseFeature=speos_level1",
    "/AddInManifestFile=" + SPEOS_BIN + r"\SpeosSC.Manifest.xml",
    "/DefaultUserSettingsFile=" + SPEOS_BIN + r"\Resources\SPEOS_SCDefaultOptions.config",
]

VERDICT_RE = re.compile(r"\[GEOM VERDICT\] (PASS|FAIL) steps=(\d+) warn=(\d+) fail=(\d+)")
STEP_RE = re.compile(r"\[STEP (PASS|WARN|FAIL)\].*")
FATAL_RE = re.compile(r"\[FATAL\]")

# A saved .scdocx below this size is not a model (agents/spaceclaim.md: .scdocx > 1KB). The check lives here so that
# the run verdict carries it (cross review 2026-10-22: a 10-byte out passed as [ORCH] PASS).
MIN_OUT_BYTES = 1024


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
        n_steps, n_fail = int(m.group(2)), int(m.group(4))
        # The PASS word alone is not trusted: no steps, a fail count or a [STEP FAIL] line make it FAIL
        # (cross review 2026-10-22: "PASS steps=0" and "[STEP FAIL] ... PASS steps=1 fail=1" both passed).
        ok = (m.group(1) == "PASS" and n_steps > 0 and n_fail == 0
              and not any(s.startswith("[STEP FAIL]") for s in steps))
        res.update(kind="verdict", verdict="PASS" if ok else "FAIL", steps=n_steps,
                   warn=int(m.group(3)), fail=n_fail, verdict_line=m.group(0))
    return res


def log_has_marker(text: str) -> bool:
    return bool(VERDICT_RE.search(text) or FATAL_RE.search(text))


def _ps(cmd: str, timeout: int = 60, env: dict | None = None) -> str:
    """PowerShell stdout. A non-zero exit raises with its stderr: empty output used to read as 0 / '' and hid
    the failure (cross review 2026-10-22: a quoted path gave compile_check '' with no reason)."""
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "[Console]::OutputEncoding = [Text.Encoding]::UTF8;" + cmd],
                       capture_output=True, timeout=timeout, encoding="utf-8", errors="replace", env=env)
    if r.returncode != 0:
        raise RuntimeError(f"powershell exit {r.returncode}: {(r.stderr or r.stdout or '').strip()}")
    return (r.stdout or "").strip()


def sc_count() -> int:
    """All SpaceClaim processes (seat check). Never used for killing."""
    return int(_ps("(Get-Process SpaceClaim -ErrorAction SilentlyContinue | Measure-Object).Count"))


def launcher_count() -> int:
    """AnsysSpeosLauncher processes (SPEOS mode residual measurement only, never killed)."""
    return int(_ps("(Get-Process AnsysSpeosLauncher -ErrorAction SilentlyContinue | Measure-Object).Count"))


def compile_check(script: Path) -> str:
    """Hosted IronPython compile check, no SpaceClaim launch. Returns 'COMPILE OK' or the error.

    Paths reach PowerShell through the environment, never inside the command text: a quote in the path broke
    the command and the reason was lost (cross review 2026-10-22)."""
    cmd = (
        "$ErrorActionPreference = 'Stop';"
        "try {"
        ' Add-Type -Path (Join-Path $env:SC_DIR "Microsoft.Scripting.dll");'
        ' Add-Type -Path (Join-Path $env:SC_DIR "Microsoft.Dynamic.dll");'
        ' Add-Type -Path (Join-Path $env:SC_DIR "IronPython.dll");'
        " $eng = [IronPython.Hosting.Python]::CreateEngine();"
        ' $null = $eng.CreateScriptSourceFromFile($env:SC_SCRIPT).Compile(); "COMPILE OK"'
        "} catch {"
        " $e = $_.Exception; while ($e.InnerException) { $e = $e.InnerException };"
        " $m = $e.Message;"
        # by name: the type itself is unknown when the DLLs failed to load
        " if ($e.GetType().FullName -eq 'Microsoft.Scripting.SyntaxErrorException') { $m += ' LINE ' + $e.Line + ' COL ' + $e.Column };"
        " $m }"
    )
    try:
        return _ps(cmd, env=dict(os.environ, SC_DIR=SC_DIR, SC_SCRIPT=str(script)))
    except RuntimeError as e:
        return str(e)


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
    return int(out)


def _stat(p: Path):
    """(mtime_ns, size) or None -- compared before/after launch to tell this run's files from older ones."""
    if not p.exists():
        return None
    st = p.stat()
    return st.st_mtime_ns, st.st_size


def run(script, log, out, timeout_s: int = 300, speos: bool = False, poll_s: float = 2.0,
        seat_wait_s: int = 300) -> dict:
    """Launch SpaceClaim headless, poll until marker / exit / timeout, close own PID, read verdict.

    PASS only when the log carries [GEOM VERDICT] PASS, this run wrote `out` (>= MIN_OUT_BYTES) and no own
    process is left (otherwise FAIL with problems=no_output|residual). kind:
      verdict | fatal | no_verdict | compile_error (0-byte log: the script never logged)
      | seat_busy (seat still taken after seat_wait_s -> not launched) | timeout | precompile_error
    Nothing is deleted: `out` / `*_FAIL` from an earlier run stay, and only files changed after launch count
    as this run's (out_new / fail_out_new). The log is emptied just before launch -- it is this run's log.
    """
    script, log, out = Path(script), Path(log), Path(out)
    t0 = time.time()
    res = {"script": str(script), "log": str(log), "out": str(out), "fail_out": str(fail_path(out))}

    cc = compile_check(script)
    if cc != "COMPILE OK":
        res.update(verdict="FAIL", kind="precompile_error", detail=cc, elapsed=0.0, residual=0)
        res["summary"] = f"[ORCH] FAIL kind=precompile_error {cc}"
        return res

    # Seat: wait (measured waits 135/240/203 s; any SpaceClaim counts, incl. a GUI one), never kill other instances (spaceclaim agent references/spaceclaim_pitfalls_ironpython.md, leftover processes).
    while sc_count() > 0 and time.time() - t0 < seat_wait_s:
        time.sleep(20)
    seat = sc_count()
    waited = round(time.time() - t0, 1)
    if seat > 0:
        # Launching onto a taken seat only ends in a 0-byte log after timeout_s -- return now.
        res.update(verdict="FAIL", kind="seat_busy", seat_at_launch=seat, seat_wait=waited, elapsed=0.0, residual=0)
        res["summary"] = (f"[ORCH] FAIL kind=seat_busy seat={seat} waited={waited:.0f}s "
                          "(not launched; another SpaceClaim, possibly a GUI one, holds the seat)")
        return res

    # Deleting out / *_FAIL here lost the previous result whenever the new run failed to start or failed
    # (cross review 2026-10-22). Snapshot them instead and judge by change.
    snap0 = {p: _stat(p) for p in (out, fail_path(out))}

    cmd = [SC_EXE] + (SPEOS_ARGS if speos else []) + [
        f"/RunScript={script}", "/ScriptApi=261", "/Headless=True", "/Splash=False", "/ExitAfterScript=True"]
    lau0 = launcher_count() if speos else None
    log.write_text("", encoding="utf-8")   # this run's log: 0 bytes at the end means the script never logged
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
        kind = "compile_error"
    if stop == "timeout" and kind != "verdict" and kind != "fatal":
        kind = "timeout"
    verdict = pr["verdict"] if kind == "verdict" else "FAIL"
    # The log verdict covers the geometry only. PASS also needs a file this run saved and no own process left
    # (review 2026-10-22: the summary said PASS with out=no residual=1).
    fail_out = fail_path(out)
    out_new = out.exists() and _stat(out) != snap0[out]
    fail_out_new = fail_out.exists() and _stat(fail_out) != snap0[fail_out]
    out_size = out.stat().st_size if out.exists() else 0
    problems = ((["no_output"] if verdict == "PASS" and not (out_new and out_size >= MIN_OUT_BYTES) else [])
                + (["residual"] if residual else []))
    if problems:
        verdict = "FAIL"
    res.update(pr)
    res.update(verdict=verdict, kind=kind, problems=problems, stop=stop, seat_at_launch=seat, seat_wait=waited,
               pid=proc.pid, elapsed=round(t_stop, 1), residual=residual,
               out_exists=out.exists(), out_new=out_new, out_size=out_size,
               fail_out_exists=fail_out.exists(), fail_out_new=fail_out_new)
    res.update(launcher_before=lau0, launcher_after=lau1)
    lau = "" if not speos else f" launcher={lau0}->{lau1}"
    age = lambda exists, new: "new" if new else "old" if exists else "no"   # old = left from an earlier run
    res["summary"] = (f"[ORCH] {verdict} kind={kind} stop={stop} t={t_stop:.1f}s "
                      f"{pr['verdict_line'] or '(no verdict line)'} residual={residual}{lau} "
                      f"out={age(res['out_exists'], out_new)} fail_out={age(res['fail_out_exists'], fail_out_new)}"
                      + (f" problems={','.join(problems)}" if problems else ""))
    return res
