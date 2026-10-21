# -*- coding: utf-8 -*-
"""origin_verify -- in-script read-back checks for Origin 2019 graph builds (COM).

Runs INSIDE the build script, on the live session. Origin quits when a finished script
releases its COM reference, so a separate verifier process cannot see the project, and a
.opju reload is not used (first Load may not answer; "Name Already Used" modal risk).
Scope: only traps recorded as failures in origin-plot memory. Style, colour, line, symbol,
page.width, 3D view and rendered text size are NOT checked here -- those stay with the png.

    import os, sys
    sys.path.insert(0, os.path.expanduser(r"<PLUGIN_ROOT>\\origin-plot\\tools"))
    from origin_verify import open_session, ex, verify, close

    app = open_session()                    # FAIL -> VerifyError (no Origin touched / none left)
    ex(app, ["newbook", ...], "data")       # every LabTalk batch; FAIL -> VerifyError + session closed
    gl = app.FindGraphLayer("[Graph1]1!")
    ex(app, ["layer.x.from=0", ...], "axes", scope=gl)
    verify(app, intended)                   # FAIL -> VerifyError + session closed (nothing saved)
    ... expGraph png, app.Save(r"...") ...
    close(app, saved=r"...\\out.opju")

    # after the script has ended (separate command):
    C:/Python314/python.exe origin_verify.py --after [--wait 30]

intended (every key optional; row/col are 1-based, as col(N)[r]):
    {
      "pages":  ["Book1", "Graph1"],                     # exact set of page short names
      "layers": {"Graph1": 1},                           # GraphPage.Layers.Count
      "axes":   {"[Graph1]1!": {"x": (0, 10), "y": (0, 1)}},   # layer.x/y.from/to
      "legend": {"[Graph1]1!": (2173.4, 712.4)},         # legend.left/top (page units); None = must not exist
      "books":  {"Book1": {"sheet": 1, "shape": (111, 3),
                           "cells": {(2, 1): 4.02, (2, 3): 0.81}}},
      "folders": ["/F1/"],                               # exact set of PE folders below the root
      "page_folders": {"Graph1": "/F1/"},                # PageBase.PEPath below the root
      "ticks":  {"[Graph1]1!": {"min": (4, 4)}},         # see below
    }
ticks: checked by default on EVERY layer of EVERY graph page (no key needed), because style default 5
(ticks inside, none top/right) and a readable axis apply to every graph. Per layer, from LabTalk values:
  - major ticks per axis = multiples of layer.x/y.inc inside [from, to], edge ticks included
    (measured 2026-10-18 against png pixels, 29/29 ranges); must be >= min (default 3 for x and y; the
    minimum Origin's own autoscale produced over 22 ranges, so 4 would fail Origin's own output).
    "min" = int or (x_min, y_min). Counted for linear axes only (layer.x.type == 1); log etc. -> reported
    as not counted (inc semantics not verified there).
  - layer.x/y.ticks & 3 == 1 (inside); layer.x2/y2.ticks & 3 == 0 (none). Measured: 0 none, 1 in, 2 out,
    3 both, higher bits do not change the direction (4 none, 5 in, 8 none, 9 in, 10 out, 12 none).
    Origin's default is x/y 10 (OUT) and x2/y2 5 (IN), so the style line must be sent.
  {"min": ..., "style": False} per layer keeps the count and drops the direction check (overlay layer, polar);
  "ticks": False switches the whole check off (chrome-free line art, 3D, matrix).
Returns the report dict {"verdict", "checks": [...]}; each check carries its memory leaf.
"""
import argparse
import math
import os
import re
import subprocess
import sys
import time

SENTINEL = -987654.0
LEGEND_TOL = 1.0          # page units; legend.left/top store integers (1150.5 -> 1150, 2026-10-18)
REL_TOL = 1e-9
MIN_TICKS = 3             # default per-axis minimum of major ticks (see docstring)
NUMPY_REPR = re.compile(r"\bnp\.\w+\(")


class VerifyError(RuntimeError):
    def __init__(self, report):
        self.report = report
        fails = [c for c in report["checks"] if c["verdict"] == "FAIL"]
        super().__init__("origin_verify FAIL: " + "; ".join(
            "%s(%s): %s" % (c["check"], c["target"], c["detail"]) for c in fails))


def _check(report, check, target, ok, detail, leaf):
    report["checks"].append({"check": check, "target": target,
                             "verdict": "PASS" if ok else "FAIL",
                             "detail": detail, "leaf": leaf})


def _finish(report, app=None):
    report["verdict"] = "FAIL" if any(c["verdict"] == "FAIL" for c in report["checks"]) else "PASS"
    for c in report["checks"]:
        print("[%s] %s %s: %s" % (c["verdict"], c["check"], c["target"], c["detail"]))
    print("origin_verify:", report["verdict"])
    if report["verdict"] == "FAIL":
        if app is not None:
            _abort(app)
        raise VerifyError(report)
    return report


def _abort(app):
    # Leaf: feedback_origin_cleanup_modal_diagnostics -- a crashed script leaves Origin running,
    # and exiting a modified project without IsModified=False pops an unanswerable Save dialog.
    app.IsModified = False
    app.Exit()


def _same(want, got):
    return got is not None and abs(got - want) <= REL_TOL * max(1.0, abs(want))


# ------------------------------------------------------------------ process / session ---
def origin_pids():
    """[(image, pid)] of every running Origin process.
    Leaf: feedback_origin_session_project_reset -- the image shows as ORIGIN~1.EXE or
    Origin96_64.exe depending on launch; /IM matching is unreliable, scan tasklist."""
    out = subprocess.run(["tasklist"], capture_output=True).stdout.decode("cp949", "replace")
    return [(m.group(1), int(m.group(2)))
            for m in re.finditer(r"^(\S*ORIGIN\S*)\s+(\d+)", out, re.I | re.M)]


def open_session(visible=True, ready_timeout=30.0):
    """Dispatch a fresh, ready, empty Origin session or raise VerifyError."""
    import win32com.client as w32
    report = {"checks": []}

    # Leaf: feedback_origin_session_project_reset, feedback_origin_session_exit_and_com_errors --
    # ApplicationSI joins any running instance with all its windows (name-collision modal, builds
    # landing on a leftover graph). One Origin at a time: refuse instead of attaching or killing.
    running = origin_pids()
    _check(report, "serialize", "Origin processes", not running,
           "none running" if not running else "already running %r -- wait for it / run --after" % running,
           "feedback_origin_session_project_reset")
    if running:
        return _finish(report)

    t0 = time.time()
    app = w32.Dispatch("Origin.ApplicationSI")
    if visible:
        app.Visible = 1

    # Leaf: feedback_origin_graph_window_creation (readiness gate), feedback_origin_set_command_reliability
    # (first command of a new session may be void) -- Execute returns True before LabTalk is live,
    # so gate on a value round trip.
    ready = False
    while time.time() - t0 < ready_timeout:
        app.Execute("__ready=1234;")
        if float(app.LTVar("__ready")) == 1234.0:
            ready = True
            break
        time.sleep(0.25)
    _check(report, "ready", "__ready round trip", ready,
           "%.1f s after Dispatch" % (time.time() - t0) if ready else "no round trip in %.0f s" % ready_timeout,
           "feedback_origin_graph_window_creation")

    # Leaf: feedback_origin_session_project_reset -- a truly fresh launch has PageBases.Count == 0.
    n = app.PageBases.Count
    _check(report, "empty", "PageBases.Count", n == 0, "%d" % n, "feedback_origin_session_project_reset")
    if n != 0:
        return _finish(report)      # not ours: do not Exit someone else's project
    _finish(report, app if not ready else None)
    return app


def ex(app, stmts, tag, scope=None):
    """Execute LabTalk statements as one batch with a progress counter.
    Raises VerifyError naming the first statement that stopped the batch."""
    if isinstance(stmts, str):
        stmts = [stmts]
    scope = scope or app
    report = {"checks": []}

    # Leaf: feedback_origin_numpy_float64_repr_labtalk_trap -- "%r" of a numpy scalar sends
    # "np.float64(x)". 2026-10-18: LabTalk evaluates it to a missing value, the statement
    # returns True and the batch runs on (legend.left became 0), so the counter cannot see it.
    poisoned = [s for s in stmts if NUMPY_REPR.search(s)]
    _check(report, "numpy repr", tag, not poisoned,
           "clean" if not poisoned else "numpy repr in %r -- cast to float before formatting" % poisoned[0],
           "feedback_origin_numpy_float64_repr_labtalk_trap")
    if poisoned:
        return _finish(report, app)

    # Leaf: feedback_origin_cleanup_modal_diagnostics -- Origin gives no error text; a counter
    # interleaved with the statements shows how far the batch got.
    parts = ["__k=0;"]
    for i, s in enumerate(stmts):
        parts.append(s if s.rstrip().endswith(";") else s + ";")
        parts.append("__k=%d;" % (i + 1))
    scope.Execute(" ".join(parts))
    k = int(float(app.LTVar("__k")))
    ok = k == len(stmts)
    if ok:
        return k
    _check(report, "batch", tag, False, "stopped at #%d: %s" % (k, stmts[k]),
           "feedback_origin_cleanup_modal_diagnostics")
    return _finish(report, app)


def _num(app, scope, expr, pre=""):
    # Leaf: feedback_origin_property_readback_sentinel -- reading a property that does not exist
    # leaves the variable untouched without error; a surviving sentinel means "not there".
    # `pre` (e.g. a range declaration) runs in the same batch, before the sentinel.
    scope.Execute("%s __v=%r; __v=%s;" % (pre, SENTINEL, expr))
    v = float(app.LTVar("__v"))
    return None if v == SENTINEL else v


def major_ticks(lo, hi, inc):
    """Major ticks Origin draws on a linear axis: multiples of inc (from 0, not from `from`) in [lo, hi].
    Leaf: feedback_origin_merge3_axis_and_legend (anchor at multiples of inc);
    measured 2026-10-18: matches png tick pixels for 29/29 ranges, incl. manual from/to with auto inc."""
    lo, hi = min(lo, hi), max(lo, hi)
    return max(0, math.floor(hi / inc + 1e-9) - math.ceil(lo / inc - 1e-9) + 1)


def _graph_layers(app):
    """[(layer name like '[Graph1]1!', page name)] for every layer of every graph page."""
    out = []
    for i in range(app.GraphPages.Count):
        gp = app.GraphPages(i)
        out += [("[%s]%d!" % (gp.Name, j + 1), gp.Name) for j in range(gp.Layers.Count)]
    return out


def _folders(folder, root_len, acc):
    for i in range(folder.Folders.Count):
        f = folder.Folders(i)
        acc.append(f.PEPath[root_len:])
        _folders(f, root_len, acc)
    return acc


# ------------------------------------------------------------------------------ verify ---
def verify(app, intended):
    report = {"checks": []}

    # Leaf: feedback_origin_session_project_reset, feedback_origin_project_explorer_folders --
    # a non-empty start or a name collision gives auto-renamed pages (Book1A ...), silently.
    if "pages" in intended:
        got = sorted(app.PageBases(i).Name for i in range(app.PageBases.Count))
        want = sorted(intended["pages"])
        _check(report, "pages", "project", got == want, "want %s got %s" % (want, got),
               "feedback_origin_session_project_reset")

    # Leaf: feedback_origin_graph_window_creation -- bare plotxy on an active graph adds a layer
    # to it instead of a new window, %H still looks right.
    for g, n in intended.get("layers", {}).items():
        gp = app.GraphPages(g)
        got = None if gp is None else gp.Layers.Count
        _check(report, "layers", g, got == n, "want %d got %s" % (n, got),
               "feedback_origin_graph_window_creation")

    # Leaf: feedback_origin_titles_autoscale_manual_legend -- every plotxy re-autoscales;
    # ranges set before the last plot are lost.
    for lay, ax in intended.get("axes", {}).items():
        gl = app.FindGraphLayer(lay)
        for a, (lo, hi) in sorted(ax.items()):
            got = (None, None) if gl is None else (_num(app, gl, "layer.%s.from" % a),
                                                   _num(app, gl, "layer.%s.to" % a))
            ok = _same(float(lo), got[0]) and _same(float(hi), got[1])
            _check(report, "axis %s" % a, lay, ok, "want %.12g..%.12g got %s..%s" % (lo, hi, got[0], got[1]),
                   "feedback_origin_titles_autoscale_manual_legend")

    # Leaf: feedback_origin_legend_background_order_and_curve_clearance -- position silently
    # shifted after background=0; feedback_origin_numpy_float64_repr_labtalk_trap -- position
    # never applied; feedback_origin_titles_autoscale_manual_legend -- auto legend comes back.
    for lay, pos in intended.get("legend", {}).items():
        gl = app.FindGraphLayer(lay)
        left = None if gl is None else _num(app, gl, "legend.left")
        top = None if gl is None else _num(app, gl, "legend.top")
        if pos is None:
            _check(report, "legend absent", lay, gl is not None and left is None,
                   "legend.left=%s" % left, "feedback_origin_titles_autoscale_manual_legend")
        else:
            ok = (left is not None and top is not None and
                  abs(left - pos[0]) <= LEGEND_TOL and abs(top - pos[1]) <= LEGEND_TOL)
            _check(report, "legend pos", lay, ok, "want (%.1f, %.1f) got (%s, %s)" % (pos[0], pos[1], left, top),
                   "feedback_origin_legend_background_order_and_curve_clearance")

    # Leaf: feedback_origin_putworksheet_row_major_order -- a list of columns lands as rows,
    # PutWorksheet still returns True. Read through a range: no window activation needed.
    for bk, spec in intended.get("books", {}).items():
        sh = spec.get("sheet", 1)
        if "shape" in spec:
            nc = _num(app, app, "__s.ncols", "range __s=[%s]%s!;" % (bk, sh))
            nr = None
            if nc is not None:
                sizes = [_num(app, app, "__c.getsize()", "range __c=[%s]%s!col(%d);" % (bk, sh, c))
                         for c in range(1, int(nc) + 1)]
                nr = max(s for s in sizes if s is not None) if any(s is not None for s in sizes) else None
            got = (None if nr is None else int(nr), None if nc is None else int(nc))
            _check(report, "shape", bk, got == tuple(spec["shape"]), "want %s got %s (rows, cols)" % (tuple(spec["shape"]), got),
                   "feedback_origin_putworksheet_row_major_order")
        for (r, c), want in sorted(spec.get("cells", {}).items()):
            got = _num(app, app, "__c[%d]" % r, "range __c=[%s]%s!col(%d);" % (bk, sh, c))
            _check(report, "cell", "%s col(%d)[%d]" % (bk, c, r), _same(float(want), got),
                   "want %.12g got %s" % (want, got), "feedback_origin_putworksheet_row_major_order")

    # Leaf: feedback_origin_project_explorer_folders -- Folder.Destroy() is a silent no-op,
    # pe_move onto the wrong parent and wrapped appends leave folders behind.
    if "folders" in intended or "page_folders" in intended:
        root = app.RootFolder
        rl = len(root.PEPath) - 1
        if "folders" in intended:
            got = sorted(_folders(root, rl, []))
            want = sorted(intended["folders"])
            _check(report, "folders", "project", got == want, "want %s got %s" % (want, got),
                   "feedback_origin_project_explorer_folders")
        names = {app.PageBases(i).Name: app.PageBases(i) for i in range(app.PageBases.Count)}
        for pg, want in intended.get("page_folders", {}).items():
            got = names[pg].PEPath[rl:] if pg in names else None
            _check(report, "page folder", pg, got == want, "want %s got %s" % (want, got),
                   "feedback_origin_project_explorer_folders")

    # Leaf: feedback_origin_tick_count_and_direction -- 2026-10-18 a graph with 2 major x ticks
    # (manual from/to 0.3..2.5, inc left at the autoscale value 1) passed a png glance. Counts come
    # from from/to/inc, direction from layer.*.ticks & 3 (1 in, 2 out); default is OUT.
    tk = intended.get("ticks", {})
    if tk is not False:
        found = _graph_layers(app)
        for lay in tk:
            if lay not in [n for n, _ in found]:
                _check(report, "ticks", lay, False, "layer not found among %s" % [n for n, _ in found],
                       "feedback_origin_tick_count_and_direction")
        for lay, _pg in found:
            spec = tk.get(lay, {})
            mn = spec.get("min", MIN_TICKS)
            mn = {"x": mn, "y": mn} if isinstance(mn, int) else {"x": mn[0], "y": mn[1]}
            gl = app.FindGraphLayer(lay)
            for a in ("x", "y"):
                v = {k: _num(app, gl, "layer.%s.%s" % (a, k)) for k in ("from", "to", "inc", "type")}
                if None in v.values() or v["inc"] <= 0:
                    _check(report, "ticks %s count" % a, lay, False, "unreadable %s" % v,
                           "feedback_origin_tick_count_and_direction")
                elif v["type"] != 1:
                    _check(report, "ticks %s count" % a, lay, True,
                           "not counted: axis type %g is not linear" % v["type"],
                           "feedback_origin_tick_count_and_direction")
                else:
                    n = major_ticks(v["from"], v["to"], v["inc"])
                    _check(report, "ticks %s count" % a, lay, n >= mn[a],
                           "%d major ticks in %.6g..%.6g step %.6g, need >= %d" % (n, v["from"], v["to"], v["inc"], mn[a]),
                           "feedback_origin_tick_count_and_direction")
            if spec.get("style", True):
                for a, want in (("x", 1), ("y", 1), ("x2", 0), ("y2", 0)):
                    t = _num(app, gl, "layer.%s.ticks" % a)
                    got = None if t is None else int(t) & 3
                    _check(report, "ticks %s dir" % a, lay, got == want,
                           "layer.%s.ticks=%s -> direction %s, want %d (0 none, 1 in, 2 out, 3 both)" % (a, t, got, want),
                           "feedback_origin_tick_count_and_direction")

    return _finish(report, app)


def close(app, saved=None):
    """Exit without a save prompt; if `saved` is given, the file must exist and be non-empty."""
    report = {"checks": []}
    if saved is not None:
        ok = os.path.isfile(saved) and os.path.getsize(saved) > 0
        _check(report, "saved", saved, ok, "%d bytes" % os.path.getsize(saved) if ok else "missing/empty",
               "feedback_origin_save_and_append_failures")
    _abort(app)
    return _finish(report)


# ----------------------------------------------------------------------- after the run ---
def _windows_of(pid):
    # Policy gui_modal_deadlock.md watchdog: visible top-level windows of the PID, no class filter.
    import win32gui
    import win32process
    out = []

    def cb(h, _):
        if win32gui.IsWindowVisible(h) and win32process.GetWindowThreadProcessId(h)[1] == pid:
            out.append((win32gui.GetClassName(h), win32gui.GetWindowText(h)))
    win32gui.EnumWindows(cb, None)
    return out


def after(wait=30.0):
    """Run after the build script ended: no Origin process (hence no modal) may remain.
    Leaf: feedback_origin_session_project_reset -- Exit() can leave the process >12 s; wait first."""
    t0 = time.time()
    left = origin_pids()
    while left and time.time() - t0 < wait:
        time.sleep(1.0)
        left = origin_pids()
    report = {"checks": []}
    detail = "gone after %.0f s" % (time.time() - t0) if not left else "; ".join(
        "pid %d windows %s" % (pid, [(c, t.encode("ascii", "replace").decode()) for c, t in _windows_of(pid)])
        for _img, pid in left)
    # No kill option: any Origin found here may be the user's own window (2026-10-18 audit) -- report only.
    _check(report, "no Origin left", "tasklist", not left, detail, "feedback_origin_session_project_reset")
    try:
        _finish(report)
    except VerifyError:
        return 2
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--after", action="store_true", required=True,
                    help="check that no Origin process / modal remains after a build script")
    ap.add_argument("--wait", type=float, default=30.0)
    a = ap.parse_args()
    sys.exit(after(a.wait))
