"""
gpu_test.py — meent GPU(backend=2, device='cuda') 실행 검증 + CPU 대비 속도.
형상(경사 격자)·재질·수렴점은 예시 값 — 실제 형상으로 바꾸고, 교차검증 기준값은 따로 대조한다.
"""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import time
import numpy as np
from meent.main import call_mee

LAMBDA = 5.0                                   # 예시 값
L = 20.0; H = 30.0; TILT = 30.0; TSUB = 5.0
NSTRUCT = 1.5 - 0.1j; NAIR = 1.0 + 0j
SHEAR = H * np.tan(np.radians(TILT))
THETA = 30.0; FTO = 20; NZ = 40


def xr_range(z):
    t = z / H
    return SHEAR * t, L - (L - SHEAR) * t


def make_ucell(Nz, Nx):
    layers = []
    dz = H / Nz
    for i in reversed(range(Nz)):
        zmid = (i + 0.5) * dz
        xl, xr = xr_range(zmid)
        frac = (xr - xl) / L
        row = np.full(Nx, NAIR, dtype=complex)
        if frac >= 1.0 - 1e-9:
            row[:] = NSTRUCT
        elif frac > 1e-9:
            dx = L / Nx
            xl_m, xr_m = xl % L, xr % L
            for j in range(Nx):
                xi = (j + 0.5) * dx
                if xl_m <= xr_m:
                    if xl_m <= xi < xr_m:
                        row[j] = NSTRUCT
                else:
                    if xi >= xl_m or xi < xr_m:
                        row[j] = NSTRUCT
        layers.append(row)
    layers.append(np.full(Nx, NSTRUCT, dtype=complex))
    ucell = np.array(layers)[:, np.newaxis, :]
    thick = tuple([dz] * Nz + [TSUB])
    return ucell, thick


def to_float(x):
    """torch tensor / numpy 모두 float으로."""
    if hasattr(x, "detach"):
        x = x.detach().cpu().numpy()
    return float(np.real(np.sum(x)))


def solve(backend, device):
    Nx = 4 * FTO + 1
    ucell, thick = make_ucell(NZ, Nx)
    kw = dict(backend=backend, n_top=1.0, n_bot=1.0,
              theta=np.radians(THETA), phi=None, pol=0,
              fto=(FTO, 0), period=(L, 1.0), wavelength=LAMBDA,
              thickness=thick, fourier_type=0)
    if backend != 0:
        kw["device"] = device
    mee = call_mee(**kw)
    mee.ucell = ucell
    t0 = time.time()
    res = mee.conv_solve()
    dt = time.time() - t0
    R = to_float(res.de_ri)
    T = to_float(res.de_ti)
    return 1.0 - R - T, dt


if __name__ == "__main__":
    print(f"example grating +{THETA}deg TE, fto_half={FTO}, N_z={NZ}\n")

    eps_cpu, t_cpu = solve(0, "cpu")
    print(f"[CPU  numpy ] eps={eps_cpu:.5f}  time={t_cpu:.1f}s")

    eps_gpu, t_gpu = solve(2, 1)   # device=1 (정수) — meent setter가 'cuda' 문자열 거부하는 버그 우회
    print(f"[GPU  torch ] eps={eps_gpu:.5f}  time={t_gpu:.1f}s")

    print(f"\n  eps match: |d|={abs(eps_cpu-eps_gpu):.6f}")
    print(f"  speed    : GPU/CPU = {t_gpu/t_cpu:.2f}x  ({'GPU faster' if t_gpu<t_cpu else 'CPU faster/equal'})")
