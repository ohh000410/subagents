import os, sys
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, grcwa
import checks as C
from meent.main import call_mee

rows = []


def rec(name, line, expect):
    v = line.split()[0]
    rows.append((name, expect, v, "OK" if expect == "any" or v == expect else "MISMATCH"))


nan = float('nan')
print("--- A unit")
rec("A normal", C.result_bounds([.1, .2], [.9, .8], [0, 0.0]), "PASS")
rec("A edge exact", C.result_bounds([1.0], [0.0], [0.0]), "PASS")
rec("A R=1.738 eps=-0.738", C.result_bounds([1.738], [0.0], [-0.738]), "FAIL")
rec("A nan", C.result_bounds([nan], [.5], [.5]), "FAIL")
rec("A eps>1", C.result_bounds([0.0], [0.0], [1.0000001]), "FAIL")
rec("A tol=1e-6 absorbs -1e-9", C.result_bounds([0.5], [0.5], [-1e-9], tol=1e-6), "PASS")
rec("A empty (all points dropped)", C.result_bounds([], [], []), "FAIL")  # 2026-10-22 교차 검토
rec("A tol=nan", C.result_bounds([.1], [.9], [0.0], tol=nan), "FAIL")
print("--- B unit")
used = dict(fto=5, theta_deg=30.000000000000004, pol=0.0, N_z=20, wavelength=3.0)
rec("B match (roundoff theta)", C.requested_vs_used(dict(fto=5, theta_deg=30, pol="TE", N_z=20, wavelength=3.0), used), "PASS")
rec("B int theta 30 vs 29.999999999999996", C.requested_vs_used(dict(theta_deg=30), dict(theta_deg=29.999999999999996)), "PASS")
rec("B fto differs", C.requested_vs_used(dict(fto=6), used), "FAIL")
rec("B theta differs", C.requested_vs_used(dict(theta_deg=30.1), used), "FAIL")
rec("B pol differs", C.requested_vs_used(dict(pol="TM"), used), "FAIL")
rec("B key not readable", C.requested_vs_used(dict(nG=40), used), "FAIL")
rec("B empty request", C.requested_vs_used({}, used), "FAIL")  # 2026-10-22 교차 검토
rec("B fto 7.5 silently cut to 7", C.requested_vs_used(dict(fto=7.5), dict(fto=7)), "FAIL")
rec("B fto 5.0 vs 5", C.requested_vs_used(dict(fto=5.0), used), "PASS")
print("--- C unit")


def mk(svals, ev=0.9):
    return [dict(fto=10 * (i + 1), N_z=20, eps=ev, eps_fto_probe=ev + s, eps_Nz_probe=ev) for i, s in enumerate(svals)]


rec("C tol 2 consecutive", C.convergence_line(mk([.02, .004, .0008, .0005]), 1e-3), "PASS")
rec("C non-monotone single dip", C.convergence_line(mk([.02, .0005, .004, .003]), 1e-3), "FAIL")
rec("C saturated", C.convergence_line(mk([.02, .004, .0021, .003, .0025, .0022]), 1e-3), "WARN")
rec("C still decreasing -> cap", C.convergence_line(mk([.02, .01, .005, .0025]), 1e-3), "FAIL")
rec("C nan -> cap", C.convergence_line(mk([.02, nan]), 1e-3), "FAIL")
rec("C tol met but blas_spread>0.01", C.convergence_line(mk([.0005, .0005]), 1e-3, blas_spread=0.015), "FAIL")
rec("C spread=0 alone gives no PASS", C.convergence_line(mk([.02, .01, .005, .0025]), 1e-3, blas_spread=0.0), "FAIL")
rec("C tol met but blas_spread=nan", C.convergence_line(mk([.0005, .0005]), 1e-3, blas_spread=nan), "FAIL")  # 2026-10-22 교차 검토
print("--- D unit")
rec("D symmetric", C.mirror_fixture([.1, .2], [.1, .2 + 1e-9], 1e-6, [30, 60]), "PASS")
rec("D asymmetric", C.mirror_fixture([.1, .2], [.1, .25], 1e-3, [30, 60]), "FAIL")
rec("D run linear-in-theta", C.mirror_fixture_run(lambda t: 0.1 + 0.01 * t, [10, 20], 1e-3), "FAIL")
rec("D tol=nan", C.mirror_fixture([.1, .2], [.9, .8], nan, [30, 60]), "FAIL")  # 2026-10-22 교차 검토
rec("D empty", C.mirror_fixture([], [], 1e-3), "FAIL")
rec("D theta=0 checks nothing", C.mirror_fixture_run(lambda t: 0.1 + 0.01 * t, [0], 1e-3), "FAIL")

print("--- real: flat n=1.5 interface (slab n=1.5 on n_bot=1.5), meent + grcwa vs Fresnel")
n = 1.5; lam = 3.0; Lx = 7.3


def fres(th, pol):
    ci = np.cos(th); ct = np.sqrt(1 - (np.sin(th) / n) ** 2)
    r = (ci - n * ct) / (ci + n * ct) if pol == "TE" else (n * ci - ct) / (n * ci + ct)
    return abs(r) ** 2


for pol in ("TE", "TM"):
    for thd in (30.0, 50.0):
        th = np.radians(thd); Rf = fres(th, pol)
        req = dict(fto=5, theta_deg=thd, pol=pol, N_z=1, wavelength=lam)
        mee = call_mee(backend=0, n_top=1.0, n_bot=n, theta=th, phi=None, pol=0 if pol == "TE" else 1, fto=(5, 0),
                       period=(Lx, 1.), wavelength=lam, thickness=(1.0,), fourier_type=0)
        mee.ucell = np.full((1, 1, 21), n + 0j)
        res = mee.conv_solve(); R = float(np.real(res.de_ri.sum())); T = float(np.real(res.de_ti.sum())); eps = 1 - R - T
        print(f"meent {pol} {thd}: R={R:.12f} Fresnel={Rf:.12f} dR={R - Rf:.2e}")
        assert abs(R - Rf) < 1e-9
        rec(f"real meent {pol}{thd} A", C.result_bounds(R, T, eps, tol=1e-12), "PASS")
        rec(f"real meent {pol}{thd} A tol=0 (lossless roundoff, informational)", C.result_bounds(R, T, eps), "any")
        rec(f"real meent {pol}{thd} B", C.requested_vs_used(req, C.read_meent(mee)), "PASS")
        rec(f"real meent {pol}{thd} B req fto=7", C.requested_vs_used(dict(req, fto=7), C.read_meent(mee)), "FAIL")
        g0 = grcwa.obj(35, [Lx, 0], [0, 1.], 1 / lam, th, 0., verbose=0)
        g0.Add_LayerUniform(1., 1.); g0.Add_LayerGrid(1., 3, 3); g0.Add_LayerUniform(1., n ** 2); g0.Init_Setup()
        Nx = 2 * int(abs(g0.G[:, 0]).max()) + 1; Ny = 2 * int(abs(g0.G[:, 1]).max()) + 1
        g = grcwa.obj(35, [Lx, 0], [0, 1.], 1 / lam, th, 0., verbose=0)
        g.Add_LayerUniform(1., 1.); g.Add_LayerGrid(1., Nx, Ny); g.Add_LayerUniform(1., n ** 2)
        g.Init_Setup(); g.GridLayer_geteps(np.full(Nx * Ny, n ** 2 + 0j))
        g.MakeExcitationPlanewave(*((0, 0, 1, 0) if pol == "TE" else (1, 0, 0, 0)))
        Rg, Tg = g.RT_Solve(normalize=1, byorder=1); Rg = float(np.real(sum(Rg))); Tg = float(np.real(sum(Tg)))
        print(f"grcwa {pol} {thd}: R={Rg:.12f} dR={Rg - Rf:.2e}")
        assert abs(Rg - Rf) < 1e-9
        rec(f"real grcwa {pol}{thd} A", C.result_bounds(Rg, Tg, 1 - Rg - Tg, tol=1e-12), "PASS")
        rec(f"real grcwa {pol}{thd} B nG=label(actual from Init_Setup)", C.requested_vs_used(dict(nG=g0.nG, theta_deg=thd, pol=pol, wavelength=lam), C.read_grcwa(g)), "PASS")
        rec(f"real grcwa {pol}{thd} B nG=ctor target 35 (actual 31)", C.requested_vs_used(dict(nG=35), C.read_grcwa(g)), "FAIL")
        rec(f"real grcwa {pol}{thd} B wrong pol", C.requested_vs_used(dict(pol="TM" if pol == "TE" else "TE"), C.read_grcwa(g)), "FAIL")

m0 = call_mee(backend=0, n_top=1.0, n_bot=n, theta=0.0, phi=None, pol=0, fto=(5, 0), period=(Lx, 1.), wavelength=lam,
              thickness=(1.0,), fourier_type=0)
print("meent theta=0 used (deg):", C.read_meent(m0)["theta_deg"])
rec("real meent theta=0 -> 1e-20 rad within atol", C.requested_vs_used(dict(theta_deg=0.0), C.read_meent(m0)), "PASS")
rec("real meent theta=0 strict atol=0", C.requested_vs_used(dict(theta_deg=0.0), C.read_meent(m0), atol=0, rtol=0), "FAIL")

print("--- real C: meent lossy binary grating path (fto, N_z x1.5 steps with probes)")
ng = 1.5 - 0.1j      # 흡수 매질 예시 값


def solve(fto, nz, thd=30.0, pol=0):
    Nx = 4 * fto + 1; row = np.ones(Nx, complex); row[:Nx // 2] = ng
    uc = np.array([row] * nz + [np.full(Nx, ng)])[:, None, :]
    m = call_mee(backend=0, n_top=1.0, n_bot=1.0, theta=np.radians(thd), phi=None, pol=pol, fto=(fto, 0), period=(7.3, 1.),
                 wavelength=3.0, thickness=tuple([2.0 / nz] * nz + [5.0]), fourier_type=0)
    m.ucell = uc; r = m.conv_solve(); R = float(np.real(r.de_ri.sum())); T = float(np.real(r.de_ti.sum()))
    return R, T, 1 - R - T


path = []; fto, nz = 4, 4
for it in range(5):
    e = solve(fto, nz)[2]; ef = solve(int(round(fto * 1.5)), nz)[2]; ez = solve(fto, int(round(nz * 1.5)))[2]
    path.append(dict(fto=fto, N_z=nz, eps=e, eps_fto_probe=ef, eps_Nz_probe=ez))
    print(it, fto, nz, e, ef - e, ez - e)
    if abs(ef - e) > 1e-3: fto = int(round(fto * 1.5))
    if abs(ez - e) > 1e-3: nz = int(round(nz * 1.5))
R, T, eps = solve(fto, nz)
line = C.convergence_line(path, 1e-3)
rows.append(("real C line emitted (verdict informational)", "any", line.split()[0], "OK" if line.startswith(("PASS", "WARN", "FAIL")) and "stop=" in line else "MISMATCH"))
rec("real A on grating", C.result_bounds(R, T, eps), "PASS")


def solve_sym(thd):
    Nx = 33; row = np.ones(Nx, complex); c = Nx // 2; row[c - 5:c + 6] = ng
    m = call_mee(backend=0, n_top=1.0, n_bot=1.0, theta=np.radians(thd), phi=None, pol=1, fto=(8, 0), period=(7.3, 1.),
                 wavelength=3.0, thickness=(2.0, 5.0), fourier_type=0)
    m.ucell = np.array([row, np.full(Nx, ng)])[:, None, :]; r = m.conv_solve()
    return 1 - float(np.real(r.de_ri.sum())) - float(np.real(r.de_ti.sum()))


rec("real D symmetric bar", C.mirror_fixture_run(solve_sym, [20, 40], 1e-9), "PASS")


def solve_asym(thd):
    Nx = 33; row = np.ones(Nx, complex); row[:12] = ng; row2 = np.roll(row, 6)
    m = call_mee(backend=0, n_top=1.0, n_bot=1.0, theta=np.radians(thd), phi=None, pol=1, fto=(8, 0), period=(7.3, 1.),
                 wavelength=3.0, thickness=(1.0, 1.0, 5.0), fourier_type=0)
    m.ucell = np.array([row, row2, np.full(Nx, ng)])[:, None, :]; r = m.conv_solve()
    return 1 - float(np.real(r.de_ri.sum())) - float(np.real(r.de_ti.sum()))


rec("real D asymmetric (sheared) detected", C.mirror_fixture_run(solve_asym, [20, 40], 1e-6), "FAIL")
print()
print("| test | expect | got | result |")
for r in rows:
    print("|" + "|".join(map(str, r)) + "|")
sys.exit(0 if all(r[3] == "OK" for r in rows) else 1)
