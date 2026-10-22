"""CPython runner for headless SPEOS /RunScript jobs.

Dependency: spaceclaim/tools/sc_orchestrate.py (same SpaceClaim seat, same rule). Imported, not reimplemented:
compile check -> seat wait (any SpaceClaim, never killed) -> launch with SPEOS_ARGS -> poll for the
script's verdict line -> close only the PID this run launched (wait for self-exit, then -Force).
AnsysSpeosLauncher is only counted before/after (launcher_before/launcher_after), never killed.

The SPEOS script must end with the verdict line sc_orchestrate polls for:
    [GEOM VERDICT] PASS|FAIL steps=N warn=W fail=F       (here: readback + StatusInfo + IsUpToDate steps)
and write [FATAL] on an unhandled exception. Paths reach the script through env vars (/RunScript takes no args).

    import os, sys
    sys.path.insert(0, os.path.expanduser(r"<PLUGIN_ROOT>\\speos\\tools"))
    from speos_run import run_speos
    res = run_speos(SCRIPT, LOG, OUT_SCDOCX, timeout_s=300, env={"SPEOS_LOG": LOG})
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

SC_TOOLS = str(Path(__file__).resolve().parents[2] / "spaceclaim" / "tools")
if SC_TOOLS not in sys.path:
    sys.path.insert(0, SC_TOOLS)
import sc_orchestrate as sco  # noqa: E402
from sc_orchestrate import ascii_safe  # noqa: E402,F401

_SENSOR_FLUX_RE = re.compile(r"<li>Flux:\s*([\d.eE+\-]+)\s*W</li>")


def run_speos(script, log, out, timeout_s: int = 300, env: dict | None = None, seat_wait_s: int = 300) -> dict:
    """sc_orchestrate.run(speos=True). env entries are visible to the child (inherited via os.environ).

    res['kind'] == 'seat_busy' means another SpaceClaim still held the seat after seat_wait_s, so nothing was launched: report it, do not kill it.
    """
    old = {k: os.environ.get(k) for k in (env or {})}
    os.environ.update({k: str(v) for k, v in (env or {}).items()})
    try:
        return sco.run(script, log, out, timeout_s=timeout_s, speos=True, seat_wait_s=seat_wait_s)
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def sensor_flux_w(report_html) -> list[float]:
    """All '<li>Flux: X W</li>' values (one per sensor section) from a SPEOS Report.html."""
    text = Path(report_html).read_text(encoding="utf-8", errors="replace")
    return [float(m.group(1)) for m in _SENSOR_FLUX_RE.finditer(text)]
