"""Per-feature geometry step checks for SpaceClaim /RunScript scripts.

Runs inside SpaceClaim IronPython 2.7 (import via sys.path) and under CPython 3
(unit tests of the judging logic). Rules kept for IronPython:
ASCII-only source, no py3-only syntax, no module-level __file__.

Script-side usage (see README.md):
    import os, sys
    sys.path.insert(0, os.environ["SC_TOOLS"])   # set by sc_orchestrate.run
    import sc_geomcheck as gc
    log = gc.make_logger(LOG)
    gc.init(log)
    b0 = gc.snap(body)          # (V_mm3, nFaces, nVerts, nBodies)
    ... feature ...
    gc.step_check("hole", b0, gc.snap(body), exp_dV=-pi*r*r*h, exp_dF=1, exp_bodies=1)
    gc.finish(OUT, DocumentSave.Execute)   # saves OUT or *_FAIL, logs [GEOM VERDICT] last
"""
import codecs
import time

try:
    _text = unicode  # IronPython 2.7
except NameError:  # CPython 3
    _text = str

# Volume tolerance [mm^3]. Basis: v261 body.Shape.Volume matched theory to
# 3.6e-15 mm^3 (plate + 10 V-grooves) and 1e-11 mm^3 (40x30x10 block + hole);
# memory feedback_sc_geometry_measurement_api.md allows exact tolerance 1e-7.
VOL_TOL_MM3 = 1e-7

# snap() value before the first body exists.
EMPTY = (0.0, 0, 0, 0)

_state = {"log": None, "steps": 0, "warn": 0, "fail": 0}


def make_logger(path):
    """utf-8 append logger with %H:%M:%S prefix (codecs, IronPython-safe)."""
    def log(msg):
        if not isinstance(msg, _text):
            try:
                msg = _text(msg)
            except Exception:
                msg = repr(msg)
        f = codecs.open(path, "a", "utf-8")
        try:
            f.write(u"%s %s\n" % (time.strftime("%H:%M:%S"), msg))
        finally:
            f.close()
    return log


def init(log_func):
    _state["log"] = log_func
    _state["steps"] = 0
    _state["warn"] = 0
    _state["fail"] = 0


def snap(body):
    """(V_mm3, nFaces, nVerts, nBodies) of a DesignBody; nBodies = bodies in its part."""
    shp = body.Shape
    return (shp.Volume * 1e9, shp.Faces.Count, shp.Vertices.Count, len(body.Parent.Bodies))


def judge(before, after, exp_dV=None, exp_dF=None, exp_bodies=None, tol=VOL_TOL_MM3):
    """Pure judging logic. Returns (status, detail). status in PASS/WARN/FAIL.

    exp_dV     expected volume change [mm^3]
    exp_dF     expected face-count change
    exp_bodies expected body count in the part AFTER the step (absolute)
    """
    dV = after[0] - before[0]
    dF = after[1] - before[1]
    dN = after[2] - before[2]
    nb = after[3]
    fails = []
    warns = []
    if exp_dV is None and exp_dF is None and exp_bodies is None:
        warns.append("no expectation")
    if exp_dV is not None:
        err = dV - exp_dV
        if abs(err) > tol:
            fails.append("dV err=%+.3e > tol %.0e" % (err, tol))
    elif abs(dV) <= tol:
        warns.append("dV=0 without exp_dV (no-op?)")
    if exp_dF is not None and dF != exp_dF:
        fails.append("dF %+d != exp %+d" % (dF, exp_dF))
    if exp_bodies is not None and nb != exp_bodies:
        fails.append("bodies %d != exp %d" % (nb, exp_bodies))
    if abs(dV) <= tol and dF == 0 and nb == before[3] and dN != 0:
        warns.append("only vertex count changed (imprint?)")
    if fails:
        status = "FAIL"
    elif warns:
        status = "WARN"
    else:
        status = "PASS"
    detail = "dV=%+.9g mm3 (exp %s) dF=%+d (exp %s) bodies=%d (exp %s) dVerts=%+d V=%.9g" % (
        dV, _fmt(exp_dV), dF, _fmt(exp_dF), nb, _fmt(exp_bodies), dN, after[0])
    reasons = fails + warns
    if reasons:
        detail += " | " + "; ".join(reasons)
    return status, detail


def _fmt(x):
    if x is None:
        return "-"
    if isinstance(x, float):
        return "%+.9g" % x
    return "%s" % x


def step_check(label, before, after, exp_dV=None, exp_dF=None, exp_bodies=None, tol=VOL_TOL_MM3):
    status, detail = judge(before, after, exp_dV, exp_dF, exp_bodies, tol)
    _state["steps"] += 1
    if status == "WARN":
        _state["warn"] += 1
    elif status == "FAIL":
        _state["fail"] += 1
    _state["log"](u"[STEP %s] %s: %s" % (status, label, detail))
    return status


def verdict():
    """PASS iff at least one step ran and none failed."""
    if _state["steps"] > 0 and _state["fail"] == 0:
        return "PASS"
    return "FAIL"


def verdict_line():
    return "[GEOM VERDICT] %s steps=%d warn=%d fail=%d" % (
        verdict(), _state["steps"], _state["warn"], _state["fail"])


def fail_path(path):
    """model.scdocx -> model_FAIL.scdocx"""
    i = path.rfind(".")
    j = max(path.rfind("\\"), path.rfind("/"))
    if i <= j:
        return path + "_FAIL"
    return path[:i] + "_FAIL" + path[i:]


def finish(path, save_func):
    """Save to path (PASS) or fail_path(path) (FAIL), then log [GEOM VERDICT] as the last line.

    The verdict line is written after the save so the orchestrator can stop polling on it.
    """
    v = verdict()
    target = path if v == "PASS" else fail_path(path)
    save_func(target)
    _state["log"](u"[SAVED] %s" % target)
    _state["log"](_text(verdict_line()))
    return v, target
