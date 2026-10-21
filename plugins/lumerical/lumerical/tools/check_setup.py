# -*- coding: utf-8 -*-
"""check_setup -- FDTD pre-run setup check on the LIVE lumapi session.

Call between save() and run(). Never opens the .fsp separately (lum_fdtd_gui = 1 seat).
Scope: only traps that actually failed in past runs.
FAIL (deterministic) -> raises SetupCheckError (report attached). Others -> WARN only.

    import os, sys
    sys.path.insert(0, os.path.expanduser(r"<PLUGIN_ROOT>\\lumerical\\tools"))
    from check_setup import check_setup

    fdtd.save(fsp_abs_path)
    check_setup(fdtd, intended)          # raises SetupCheckError on FAIL
    fdtd.run()

intended (every key optional):
    {
      "readback": {                       # object -> {property: intended value}
          "FDTD": {"mesh accuracy": 4, "pml profile": 1, "pml layers": 24,
                   "auto shutoff min": 1e-6, "simulation time": 30000e-15},
          "src":  {"angle theta": 30, "polarization angle": 90},
      },
      "band": {"wavelength start": 8e-6, "wavelength stop": 13e-6},
      "case_ids": [...],                  # full sweep grid, for uniqueness
      "engine": "cpu",                    # this workstation has no GPU engine
      "processes": 6,                     # FDTD resource 1 (workstation default)
      "disk_min_gb": 20, "disk_warn_gb": 40,
    }
Returns the report dict: {"verdict", "fsp", "checks": [...]}.
"""
import os
import shutil
import subprocess

import numpy as np

VERDICT_RANK = {"PASS": 0, "WARN": 1, "FAIL": 2}
REL_TOL = 1e-9
ABS_TOL = 1e-15


class SetupCheckError(RuntimeError):
    def __init__(self, report):
        self.report = report
        fails = [c for c in report["checks"] if c["verdict"] == "FAIL"]
        super().__init__("check_setup FAIL: " + "; ".join(
            "%s(%s): %s" % (c["check"], c["target"], c["detail"]) for c in fails))


def _scalar(v):
    if isinstance(v, str):
        return v
    a = np.squeeze(np.asarray(v))
    if a.ndim == 0:
        return a.item()
    return a


def _same(want, got):
    if isinstance(want, str) or isinstance(got, str):
        return str(want).strip().lower() == str(got).strip().lower()
    w = np.asarray(want, dtype=float)
    g = np.asarray(got, dtype=float)
    if w.shape != g.shape and not (w.size == 1 and g.size == 1):
        return False
    return bool(np.all(np.abs(w - g) <= np.maximum(ABS_TOL, REL_TOL * np.abs(w))))


def _have(fdtd, obj, prop):
    """Lumerical haveproperty: 0 = no such property (or no such object)."""
    fdtd.eval('csn_cnt = getnamednumber("%s");' % obj)
    if float(fdtd.getv("csn_cnt")) == 0:
        return 0.0
    fdtd.eval('select("%s"); csn_have = haveproperty("%s"); unselectall;' % (obj, prop))
    return float(fdtd.getv("csn_have"))


def _objects(fdtd):
    """(name, type) of every top-level object."""
    fdtd.eval('selectall; csn_n = getnumber; csn_s = ""; '
              'for(csn_i=1:csn_n){ csn_s = csn_s + get("name",csn_i) + "|" '
              '+ get("type",csn_i) + endl; } unselectall;')
    out = []
    for ln in str(fdtd.getv("csn_s")).splitlines():
        if "|" in ln:
            n, t = ln.split("|", 1)
            out.append((n, t))
    return out


class _Rep:
    def __init__(self):
        self.items = []

    def add(self, check, verdict, target, detail, evidence):
        self.items.append({"check": check, "verdict": verdict, "target": target,
                           "detail": detail, "evidence": evidence})


# --------------------------------------------------------------------------- checks

def _check_saved(fdtd, rep):
    """run() needs an absolute saved path; the .fsp stem also names the _p0.log.
    Source: AGENT.md execution protocol step 2 (unsaved -> "Save as" modal hang)."""
    fn = str(fdtd.currentfilename())
    if not fn or not os.path.isabs(fn):
        rep.add("saved", "FAIL", "-", "session not saved to an absolute .fsp path "
                "(save() before check_setup/run)", "AGENT.md step 2")
        return None
    rep.add("saved", "PASS", os.path.basename(fn), "", "")
    return fn


def _check_gpu_only(fdtd, rep, engine):
    """GPU-only FDTD settings on the CPU engine: run() returns normally (Local Computer)
    or hangs >55 min (MS-MPI); only the _p0.log says why."""
    ev = ""
    if engine != "cpu":
        return
    if _have(fdtd, "FDTD", "express mode"):
        v = _scalar(fdtd.getnamed("FDTD", "express mode"))
        if float(v) != 0.0:
            rep.add("gpu_only", "FAIL", "FDTD", "express mode=%s on CPU engine" % v, ev)
        else:
            rep.add("gpu_only", "PASS", "FDTD", "express mode=0", "")
    if _have(fdtd, "FDTD", "pml termination"):
        v = str(_scalar(fdtd.getnamed("FDTD", "pml termination")))
        if v.strip().lower() != "pmc":
            rep.add("gpu_only", "FAIL", "FDTD",
                    "pml termination=%s; CPU supports only 'pmc'" % v, ev)
        else:
            rep.add("gpu_only", "PASS", "FDTD", "pml termination=pmc", "")


def _check_source_band(fdtd, rep, band):
    """Per-source override vs global source band. addplane() defaults to
    'override global source settings'=1 with its own 400-700 nm range, so
    setglobalsource() alone does not move the source; monitors sample the GLOBAL band."""
    ev = ""
    g0 = float(_scalar(fdtd.getglobalsource("wavelength start")))
    g1 = float(_scalar(fdtd.getglobalsource("wavelength stop")))
    if band:
        w0, w1 = band["wavelength start"], band["wavelength stop"]
        if not (_same(w0, g0) and _same(w1, g1)):
            rep.add("source_band", "FAIL", "global source",
                    "global band %.6g-%.6g m != intended %.6g-%.6g m (monitors sample global)"
                    % (g0, g1, w0, w1), ev)
        else:
            rep.add("source_band", "PASS", "global source", "", "")
    srcs = [n for n, t in _objects(fdtd) if t.endswith("Source")]
    if not srcs:
        rep.add("source_band", "WARN", "-", "no top-level source object found", ev)
    for s in srcs:
        if not _have(fdtd, s, "override global source settings"):
            continue
        ov = float(_scalar(fdtd.getnamed(s, "override global source settings")))
        if ov:
            l0 = float(_scalar(fdtd.getnamed(s, "wavelength start")))
            l1 = float(_scalar(fdtd.getnamed(s, "wavelength stop")))
        else:
            l0, l1 = g0, g1
        bad = []
        if not (_same(l0, g0) and _same(l1, g1)):
            bad.append("source band %.6g-%.6g m != global %.6g-%.6g m (override=%d)"
                       % (l0, l1, g0, g1, ov))
        if band and not (_same(band["wavelength start"], l0)
                         and _same(band["wavelength stop"], l1)):
            bad.append("source band %.6g-%.6g m != intended %.6g-%.6g m"
                       % (l0, l1, band["wavelength start"], band["wavelength stop"]))
        if bad:
            rep.add("source_band", "FAIL", s, "; ".join(bad), ev)
        else:
            rep.add("source_band", "PASS", s, "%.6g-%.6g m override=%d" % (l0, l1, ov), "")
    if not band:
        rep.add("source_band", "WARN", "-", "no intended band given; only source vs global "
                "consistency checked", ev)


def _check_readback(fdtd, rep, readback):
    """intended value == getnamed readback. Silent clamps seen: mesh accuracy >8 -> 8;
    pml profile=2 raises layers 24 -> 32; layers >64 -> 64 and
    layers-before-profile reset."""
    ev = ""
    for obj, props in (readback or {}).items():
        for prop, want in props.items():
            tgt = "%s.%s" % (obj, prop)
            if not _have(fdtd, obj, prop):
                rep.add("readback", "FAIL", tgt, "object or property not found", ev)
                continue
            got = _scalar(fdtd.getnamed(obj, prop))
            if _same(want, got):
                rep.add("readback", "PASS", tgt, "%r" % (got,), "")
            else:
                rep.add("readback", "FAIL", tgt, "intended %r, readback %r" % (want, got), ev)
    # WARN: profile=2 without an intended layer count -> layers silently >= 32
    fd = (readback or {}).get("FDTD", {})
    if "pml layers" not in fd and _have(fdtd, "FDTD", "pml profile"):
        prof = _scalar(fdtd.getnamed("FDTD", "pml profile"))
        if not isinstance(prof, str) and float(prof) == 2.0:
            rep.add("readback", "WARN", "FDTD.pml layers",
                    "pml profile=2 and no intended layers: actual layers=%s"
                    % _scalar(fdtd.getnamed("FDTD", "pml layers")),
                    "")


def _check_disk(rep, fsp, min_gb, warn_gb):
    """Free disk on C: and on the .fsp drive. A near-full C: turned a write hiccup into
    a 6 h hung engine pileup."""
    ev = ""
    drives = ["C:\\"]
    if fsp:
        d = os.path.splitdrive(fsp)[0].upper() + "\\"
        if d not in drives:
            drives.append(d)
    for d in drives:
        free = shutil.disk_usage(d).free / 1e9
        if free < min_gb:
            rep.add("disk_free", "FAIL", d, "%.1f GB free < %.0f GB" % (free, min_gb), ev)
        elif free < warn_gb:
            rep.add("disk_free", "WARN", d, "%.1f GB free < %.0f GB" % (free, warn_gb), ev)
        else:
            rep.add("disk_free", "PASS", d, "%.1f GB free" % free, "")


def _check_case_ids(rep, case_ids, fsp):
    """case_id names both <case_id>.fsp and <case_id>_p0.log; collisions share a log."""
    ev = ""
    if case_ids is None:
        return
    seen, dup = set(), set()
    for c in case_ids:
        (dup if c in seen else seen).add(c)
    if dup:
        rep.add("case_id_unique", "FAIL", "sweep",
                "duplicate case_id: %s" % ", ".join(sorted(map(str, dup)))[:300], ev)
    else:
        rep.add("case_id_unique", "PASS", "sweep", "%d unique" % len(seen), "")
    if fsp:
        stem = os.path.splitext(os.path.basename(fsp))[0]
        if stem not in seen:
            rep.add("case_id_unique", "WARN", stem, "current .fsp stem not in case_ids", ev)


def _check_preset(fdtd, rep, processes):
    """'job launching preset' persists in the user config across sessions; 'Local
    Computer' silently drops production to one process. Workstation default =
    'Remote: Microsoft MPI'."""
    ev = ""
    p = str(_scalar(fdtd.getresource("FDTD", 1, "job launching preset")))
    if p.strip().lower() == "local computer":
        rep.add("launch_preset", "FAIL", "FDTD resource 1",
                "job launching preset = 'Local Computer' (restore 'Remote: Microsoft MPI')", ev)
    else:
        rep.add("launch_preset", "PASS", "FDTD resource 1", p, "")
    # Switching preset to Local Computer and back left processes=1 (measured 2026-10-17,
    # v242) -> single-process production with the preset looking correct.
    n = int(float(_scalar(fdtd.getresource("FDTD", 1, "processes"))))
    if n != int(processes):
        rep.add("launch_preset", "WARN", "FDTD resource 1",
                "processes=%d (expected %d)" % (n, int(processes)), ev)
    else:
        rep.add("launch_preset", "PASS", "FDTD resource 1", "processes=%d" % n, "")


def _check_orphans(rep):
    """Engines alive before run() = orphans from a killed controller."""
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq fdtd-engine*"],
                         capture_output=True, text=True, errors="replace").stdout
    n = sum(1 for ln in out.splitlines() if ln.lower().startswith("fdtd-engine"))
    if n:
        rep.add("orphan_engines", "WARN", "tasklist",
                "%d fdtd-engine process(es) already running before run()" % n,
                "")
    else:
        rep.add("orphan_engines", "PASS", "tasklist", "", "")


# --------------------------------------------------------------------------- entry

def check_setup(fdtd, intended=None, raise_on_fail=True, verbose=True):
    intended = intended or {}
    rep = _Rep()
    fsp = _check_saved(fdtd, rep)
    _check_gpu_only(fdtd, rep, intended.get("engine", "cpu"))
    _check_source_band(fdtd, rep, intended.get("band"))
    _check_readback(fdtd, rep, intended.get("readback"))
    _check_disk(rep, fsp, intended.get("disk_min_gb", 20.0), intended.get("disk_warn_gb", 40.0))
    _check_case_ids(rep, intended.get("case_ids"), fsp)
    _check_preset(fdtd, rep, intended.get("processes", 6))
    _check_orphans(rep)
    verdict = "PASS"
    for it in rep.items:
        if VERDICT_RANK[it["verdict"]] > VERDICT_RANK[verdict]:
            verdict = it["verdict"]
    report = {"verdict": verdict, "fsp": fsp, "checks": rep.items}
    if verbose:
        print(summarize(report), flush=True)
    if raise_on_fail and verdict == "FAIL":
        raise SetupCheckError(report)
    return report


def summarize(report):
    lines = ["check_setup: %s" % report["verdict"]]
    for it in report["checks"]:
        if it["verdict"] != "PASS":
            lines.append("%s %-15s %s  %s  [%s]" % (it["verdict"], it["check"], it["target"],
                                                     it["detail"], it["evidence"]))
    n = {}
    for it in report["checks"]:
        n[it["verdict"]] = n.get(it["verdict"], 0) + 1
    lines.append("counts: " + ", ".join("%s=%d" % kv for kv in sorted(n.items())))
    return "\n".join(lines).encode("ascii", "backslashreplace").decode("ascii")
