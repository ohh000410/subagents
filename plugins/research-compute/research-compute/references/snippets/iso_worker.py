"""
iso_worker.py  (2026-07-10)
단일 meent solve를 '메모리 하드 상한' 격리 안에서 실행.
Job Object로 이 프로세스의 커밋 메모리를 상한(RAM_LIMIT_GB) 이하로 강제 →
near-singular 폭주가 나도 이 프로세스만 죽고 시스템은 안전.
결과(eps/R/T 또는 에러)를 마지막 줄에 JSON으로 출력.

usage: iso_worker.py <fto> <nz> <theta_deg> <backend> <ram_limit_gb>
       backend: 0=CPU, 2=GPU
"""
import sys, os, json, time
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

fto = int(sys.argv[1]); nz = int(sys.argv[2]); theta = float(sys.argv[3])
backend = int(sys.argv[4]); RAM_LIMIT_GB = float(sys.argv[5])
POL_ARG = int(sys.argv[6]) if len(sys.argv) > 6 else 0  # 0=TE, 1=TM

# ── Job Object로 자기 프로세스에 커밋메모리 하드 상한 ──
import win32job, win32api
hJob = win32job.CreateJobObject(None, "")
info = win32job.QueryInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation)
info['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY
info['ProcessMemoryLimit'] = int(RAM_LIMIT_GB * 1024**3)
win32job.SetInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation, info)
win32job.AssignProcessToJobObject(hJob, win32api.GetCurrentProcess())

import numpy as np
import torch
from meent.main import call_mee

LAMBDA = 5.0                                   # 예시 값 — 실제 형상으로 바꾼다
L = 20.0; H = 30.0; TILT = 30.0; TSUB = 5.0
NSTRUCT = 1.5 - 0.1j; NAIR = 1.0 + 0j
SHEAR = H * np.tan(np.radians(TILT))
POL = POL_ARG  # 0=TE, 1=TM


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
    if hasattr(x, "detach"):
        x = x.detach().cpu().numpy()
    return float(np.real(np.sum(x)))


def solve():
    Nx = 4 * fto + 1
    ucell, thick = make_ucell(nz, Nx)
    kw = dict(backend=backend, n_top=1.0, n_bot=1.0,
              theta=np.radians(theta), phi=None, pol=POL,
              fto=(fto, 0), period=(L, 1.0), wavelength=LAMBDA,
              thickness=thick, fourier_type=0)
    if backend != 0:
        kw["device"] = 1
    mee = call_mee(**kw)
    mee.ucell = ucell
    res = mee.conv_solve()
    R = to_float(res.de_ri); T = to_float(res.de_ti)
    return 1.0 - R - T, R, T


if __name__ == "__main__":
    t0 = time.time()
    result = {"fto": fto, "nz": nz, "theta": theta, "backend": backend, "ram_limit_gb": RAM_LIMIT_GB}
    try:
        eps, R, T = solve()
        result.update({"ok": True, "eps": eps, "R": R, "T": T, "dt": round(time.time() - t0, 1)})
    except MemoryError:
        result.update({"ok": False, "err": "MemoryError(RAM 상한 도달=폭주 확인)", "dt": round(time.time() - t0, 1)})
    except RuntimeError as e:
        s = str(e)
        tag = "CUDA_OOM" if "out of memory" in s else "RuntimeError"
        result.update({"ok": False, "err": f"{tag}: {s[:90]}", "dt": round(time.time() - t0, 1)})
    except Exception as e:
        result.update({"ok": False, "err": f"{type(e).__name__}: {str(e)[:90]}", "dt": round(time.time() - t0, 1)})
    print("RESULT_JSON:" + json.dumps(result), flush=True)
