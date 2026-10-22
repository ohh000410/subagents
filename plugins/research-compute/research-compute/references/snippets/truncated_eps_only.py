"""
truncated_eps_only.py  (2026-07-09)
유효 유전율(Fourier-truncated eps) 맵만 그린다. solve/field 전혀 없음 (순수 FFT).
meent가 실제 계산에 쓰는 유효 유전율 = ucell을 fto_half 차수로 truncation한 분포.

air buffer 포함 통합 도메인:
  [top air] + [wedge] + [substrate] + [bot air]  (z=0 @ top, 아래로 증가; 두께 = 아래 파라미터)

편광별 fto_half 는 다를 수 있다 (형상은 편광 무관이나 truncation 차수만 다름).
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── 파라미터 (예시 값 — 실제 형상으로 바꾼다) ──
LAMBDA_UM  = 5.0
L_UM       = 20.0
H_UM       = 30.0
THETA_TILT = 30.0
T_SUB      = 5.0

D_TOP_AIR    = 10.0
D_BOT_AIR    = 5.0
N_SUBDIV_TOP = 3
N_SUBDIV_BOT = 1

RES_X = 200
RES_Z = 10

N_STRUCT_MEENT = 1.5 - 0.1j
N_AIR        = 1.0 + 0j
SHEAR        = H_UM * np.tan(np.radians(THETA_TILT))

N_Z = 40  # wedge staircase 층 수 (형상 정의용, solve 아님)

OUT_DIR = r"<존재하지 않음: 2026-08-14 삭제. 새 출력 경로를 지정할 것>"


def _struct_xrange(z_um):
    t  = z_um / H_UM
    xl = SHEAR * t
    xr = L_UM - (L_UM - SHEAR) * t
    return xl, xr


def make_ucell_and_thick(N_z, Nx):
    layers_n, layers_dz, layer_types = [], [], []
    dz_top   = D_TOP_AIR / N_SUBDIV_TOP
    dz_bot   = D_BOT_AIR / N_SUBDIV_BOT
    dz_wedge = H_UM / N_z

    for _ in range(N_SUBDIV_TOP):
        layers_n.append(np.full(Nx, N_AIR, dtype=complex))
        layers_dz.append(dz_top); layer_types.append('top_air')

    for i in reversed(range(N_z)):
        z_mid = (i + 0.5) * dz_wedge
        xl, xr = _struct_xrange(z_mid)
        frac = (xr - xl) / L_UM
        row = np.full(Nx, N_AIR, dtype=complex)
        if frac >= 1.0 - 1e-9:
            row[:] = N_STRUCT_MEENT
        elif frac > 1e-9:
            dx = L_UM / Nx
            xl_m, xr_m = xl % L_UM, xr % L_UM
            if xl_m <= xr_m:
                for j in range(Nx):
                    xi = (j + 0.5) * dx
                    if xl_m <= xi < xr_m:
                        row[j] = N_STRUCT_MEENT
            else:
                for j in range(Nx):
                    xi = (j + 0.5) * dx
                    if xi >= xl_m or xi < xr_m:
                        row[j] = N_STRUCT_MEENT
        layers_n.append(row)
        layers_dz.append(dz_wedge); layer_types.append('wedge')

    layers_n.append(np.full(Nx, N_STRUCT_MEENT, dtype=complex))
    layers_dz.append(T_SUB); layer_types.append('substrate')

    for _ in range(N_SUBDIV_BOT):
        layers_n.append(np.full(Nx, N_AIR, dtype=complex))
        layers_dz.append(dz_bot); layer_types.append('bot_air')

    ucell = np.array(layers_n)[:, np.newaxis, :]
    return ucell, tuple(layers_dz), layer_types


def make_z_coords(thickness):
    z_coords = []
    z_cum = 0.0
    for dz in thickness:
        for k in range(RES_Z):
            z_coords.append(z_cum + (k + 0.5) / RES_Z * dz)
        z_cum += dz
    return np.array(z_coords)


def make_truncated_eps_zx(ucell, Nx, fto_x, N_layers_total):
    """meent dfs2d 역함수: eps_row FFT -> fto_x 차수만 유지 -> IFFT 재구성."""
    eps_trunc = np.zeros((N_layers_total * RES_Z, RES_X), dtype=complex)
    for li in range(N_layers_total):
        eps_row = ucell[li, 0, :] ** 2
        E = np.fft.fft(eps_row) / Nx
        E_pad = np.zeros(RES_X, dtype=complex)
        E_pad[0 : fto_x + 1]   = E[0 : fto_x + 1]
        E_pad[RES_X - fto_x :] = E[Nx - fto_x : Nx]
        eps_recon = np.fft.ifft(E_pad) * RES_X
        eps_trunc[li * RES_Z : (li + 1) * RES_Z, :] = eps_recon[np.newaxis, :]
    return eps_trunc


def run(pol_name, fto_half):
    Nx = 4 * fto_half + 1
    ucell, thickness, layer_types = make_ucell_and_thick(N_Z, Nx)
    N_layers = ucell.shape[0]
    z_coords = make_z_coords(thickness)
    x_coords = np.linspace(0, L_UM, RES_X, endpoint=False)

    eps_trunc = make_truncated_eps_zx(ucell, Nx, fto_half, N_layers)

    # 구간 경계 z (라벨용)
    z_cum, bounds = 0.0, {}
    for dz, t in zip(thickness, layer_types):
        bounds.setdefault(t, z_cum); z_cum += dz
    z_wedge_start = D_TOP_AIR
    z_sub_start   = D_TOP_AIR + H_UM
    z_bot_start   = D_TOP_AIR + H_UM + T_SUB

    fig, axes = plt.subplots(1, 2, figsize=(11, 8))
    fig.suptitle(f"Fourier-truncated effective permittivity - {pol_name} "
                 f"(fto_half={fto_half}, no solve)\n"
                 f"structure eps={N_STRUCT_MEENT**2:.3f}, air=1 | domain: air{D_TOP_AIR:g}+wedge{H_UM:g}+sub{T_SUB:g}+air{D_BOT_AIR:g}",
                 fontsize=10)

    X, Z = np.meshgrid(x_coords, z_coords)

    for ax, data, title, cmap in [
        (axes[0], eps_trunc.real, "Re(eps_truncated)", "viridis"),
        (axes[1], eps_trunc.imag, "Im(eps_truncated)  (air~0, absorbing<0, ringing visible)", "RdBu"),
    ]:
        vmax = np.abs(data).max()
        pm = ax.pcolormesh(X, Z, data, shading='nearest', cmap=cmap,
                           vmin=(-vmax if cmap == "RdBu" else None),
                           vmax=(vmax if cmap == "RdBu" else None))
        plt.colorbar(pm, ax=ax, fraction=0.046)
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("x [um]"); ax.set_ylabel("z [um] (0=top air)")
        for zb, lab in [(z_wedge_start, 'wedge'), (z_sub_start, 'substrate'), (z_bot_start, 'bot air')]:
            ax.axhline(zb, color='gray', lw=0.6, ls=':')
        ax.invert_yaxis()

    plt.tight_layout()
    out = os.path.join(OUT_DIR, f"eff_permittivity_{pol_name}.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ringing 진단
    im = eps_trunc.imag
    struct_im = (N_STRUCT_MEENT**2).imag
    print(f"[{pol_name}] fto_half={fto_half}  N_layers={N_layers}  "
          f"Re range [{eps_trunc.real.min():.3f}, {eps_trunc.real.max():.3f}]  "
          f"Im range [{im.min():.3f}, {im.max():.3f}]  (structure Im={struct_im:.3f})")
    print(f"  saved: {out}")
    return out


if __name__ == "__main__":
    print("effective permittivity (truncated eps) only - no solve/field (pure FFT)")
    run("TE", 20)
    run("TM", 20)
    print("Done.")
