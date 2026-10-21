"""CPython 3.12: run sc_lambert_smoke.py and compare Report.html flux with the closed form.

    py -V:Astral/CPython3.12.13 run_lambert_smoke.py <work_dir> [nbrays]
Closed form: Lambertian point source (flux 1 W) at h=50 mm, square sensor half width 100 mm:
  F = (1/pi) * integral h^2/(h^2+x^2+y^2)^2 dA   (10 mm source size neglected)
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from speos_run import run_speos, sensor_flux_w, ascii_safe, sco  # noqa: E402

HERE = Path(__file__).resolve().parent


def closed_form(h=50.0, half=100.0, n=1000):
    d = half / n   # midpoint rule on one quadrant, x4
    s = 0.0
    for i in range(n):
        x = (i + 0.5) * d
        for j in range(n):
            y = (j + 0.5) * d
            s += h * h / (h * h + x * x + y * y) ** 2
    return 4 * s * d * d / math.pi


def main():
    work = Path(sys.argv[1]).resolve()
    nb = int(sys.argv[2]) if len(sys.argv) > 2 else 200000
    work.mkdir(parents=True, exist_ok=True)
    log, out = work / "smoke.log", work / "scene" / "lambert.scdocx"
    res = run_speos(HERE / "sc_lambert_smoke.py", log, out, timeout_s=300,
                    env={"SPEOS_LOG": log, "SPEOS_OUT": out, "SPEOS_NBRAYS": nb})
    print(ascii_safe(res["summary"]))
    print("seat_at_launch =", res.get("seat_at_launch"), "pid =", res.get("pid"))
    rep = out.parent / "SPEOS output files" / out.stem / "Lambert_Direct.Report.html"
    flux = sensor_flux_w(rep) if rep.exists() else []
    ref = closed_form()
    print(f"report={'yes' if rep.exists() else 'no'} sensor_flux={flux} closed_form={ref:.4f}")
    ok = res["verdict"] == "PASS" and len(flux) == 1 and flux[0] > 0 and abs(flux[0] - ref) / ref < 0.02
    print(f"remaining SpaceClaim={sco.sc_count()} AnsysSpeosLauncher={sco.launcher_count()}")
    print("[SMOKE]", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
