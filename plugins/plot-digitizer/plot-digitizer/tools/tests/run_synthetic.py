"""
합성 정답 테스트 — check_extraction.py / check_calibration.py 가 실측 사고 유형을 잡는지.

사용법:
    python tests/run_synthetic.py [-v]      (-v = flag 메시지 전부 출력)

matplotlib 로 참값 매핑(ax.transData)을 아는 그림을 메모리에서 렌더 -> 사고를 재현하는 추출·캘리브
(결함 버전)와 고친 버전(정상)을 각각 만들어 도구에 넣는다. 유형 1~5 는 파일을 쓰지 않고, 유형 6~7 은
임시 폴더에 CSV·calib.json·png 를 써서 읽기/CLI 경로까지 검사한 뒤 지운다.
기대: 결함 -> 해당 flag, 정상 -> flag 0건. 하나라도 어긋나면 종료코드 1.

유형
1 눈금 돌출 오염
2 가파른 구간 삭제 (+ 고립 실제 특징 오탐 가드)
3 로컬/전체 이중 차감
4 끝 눈금-테두리 겹침 (+ 눈금 하나 오검출)
5 polar 지름 끝 돌출 R 과대
6 long CSV (series,x,y) 읽기 — wide 와 같은 flag, 곡선별 x, 행 삭제 gap
7 calib.json 저장·로드·값<->픽셀 왕복, check_calibration --overlay (cartesian·polar, flag 눈금 빨강)
"""
import os
import subprocess
import sys
import tempfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import check_calibration as cc  # noqa: E402
import check_extraction as ce  # noqa: E402
import calib_model as cm  # noqa: E402
from PIL import Image  # noqa: E402

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DPI = 200


# ---------------------------------------------------------------- 렌더·참값 매핑
def render(fig):
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[..., :3].astype(float)
    plt.close(fig)
    return img


def px_of(ax, H, x, y):
    """데이터 -> 전체 이미지 픽셀 (col, row). 픽셀 i 중심 = display i+0.5."""
    d = ax.transData.transform(np.column_stack([np.atleast_1d(x), np.atleast_1d(y)]))
    return d[:, 0] - 0.5, H - d[:, 1] - 0.5


def cart_figure(curves, xlim, ylim, xticks, yticks, figsize=(6, 4), rect=(0.12, 0.12, 0.8, 0.8)):
    fig = plt.figure(figsize=figsize, dpi=DPI)
    ax = fig.add_axes(rect)
    for x, y, color in curves:
        ax.plot(x, y, color=color, lw=1.5)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xticks(xticks)
    ax.set_yticks(yticks)
    ax.tick_params(direction="in", length=6, width=1.0, top=True, right=True)
    fig.canvas.draw()                      # transData 확정
    H = int(fig.get_figheight() * DPI)
    l, b_ = px_of(ax, H, xlim[0], ylim[0])
    r, t = px_of(ax, H, xlim[1], ylim[1])
    box = {"left": float(l[0]), "right": float(r[0]), "top": float(t[0]), "bottom": float(b_[0])}
    xt = [[float(v), float(px_of(ax, H, v, ylim[0])[0][0])] for v in xticks]
    yt = [[float(v), float(px_of(ax, H, xlim[0], v)[1][0])] for v in yticks]
    img = render(fig)
    calib = {"type": "cartesian", "box_px": box, "x_ticks": xt, "y_ticks": yt}
    return img, calib


def inv(calib, axis, px):
    """픽셀 -> 값. 추출 스크립트와 같은 calib_model 변환."""
    if axis == "x":
        return cm.cart_from_px(calib, px, 0.0)[0]
    return cm.cart_from_px(calib, 0.0, px)[1]


def dark(img, thr=100):
    return img.max(axis=2) < thr


def red(img):
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    return (r > 150) & (g < 110) & (b < 110)


def column_median(mask, box, inset, row_offset=0):
    """box 안쪽 inset 만큼 떨어진 영역에서 열마다 mask 픽셀 행의 중앙값 (전체 이미지 행)."""
    c0, c1 = int(np.ceil(box["left"] + inset)), int(np.floor(box["right"] - inset))
    r0, r1 = int(np.ceil(box["top"] + inset)), int(np.floor(box["bottom"] - inset))
    cols, rows = [], []
    for c in range(c0, c1 + 1):
        rr = np.nonzero(mask[r0:r1 + 1, c])[0]
        if len(rr):
            cols.append(c)
            rows.append(np.median(rr) + r0 + row_offset)
    return np.array(cols, float), np.array(rows, float)


def run_extract(x, curves, interp=None, calib=None):
    flags, _ = ce.check(np.asarray(x, float), {k: np.asarray(v, float) for k, v in curves.items()},
                        interp or {}, calib)
    return flags


# ---------------------------------------------------------------- 1 눈금 돌출 오염
def measure_tick_len(img, box, row):
    """y 눈금 행 띠에서 테두리 안쪽으로 dark 픽셀이 사라지는 거리."""
    d = dark(img)
    r = int(round(row))
    c = int(round(box["left"])) + 1
    while d[r - 1:r + 2, c].any():
        c += 1
    return c - box["left"]


def case_tick_protrusion():
    x = np.linspace(0, 10, 600)
    ytrue = lambda xx: 0.7 + 0.2 * np.cos(2 * np.pi * xx / 10)       # 양끝 0.9, 가운데 0.5
    img, calib = cart_figure([(x, ytrue(x), "black")], (0, 10), (0, 1), [0, 2, 4, 6, 8, 10],
                             [0, 0.2, 0.4, 0.6, 0.8, 1.0])
    L = measure_tick_len(img, calib["box_px"], calib["y_ticks"][2][1])
    calib.update(tick_len_px=float(L), tick_sides=["left", "bottom", "right", "top"])
    out = []
    for version, inset in (("결함: inset=테두리 굵기(4 px)", 4.0), (f"정상: inset=실측 눈금 길이 {L:.0f}+3 px", L + 3)):
        cols, rows = column_median(dark(img), calib["box_px"], inset)
        xv, yv = inv(calib, "x", cols), inv(calib, "y", rows)
        err = float(np.max(np.abs(yv - ytrue(xv))))
        flags = run_extract(xv, {"black": yv}, calib=calib)
        out.append((version, flags, f"max|err| {err:.3f}"))
    return out


# ---------------------------------------------------------------- 2 가파른 구간
def resample(xv, yv, grid, half):
    out = np.full(len(grid), np.nan)
    for i, g in enumerate(grid):
        m = np.abs(xv - g) <= half
        if m.any():
            out[i] = np.median(yv[m])
    return out


def local_median_reject(x, y, win=0.15, thr=0.05):
    """실제 쓰던 필터 그대로: 원시 열 산점에서 +-win 안 이웃(자기 제외) 중앙값과 thr 넘게 다르면 제거."""
    keep = np.ones(len(y), bool)
    for i in range(len(y)):
        m = np.abs(x - x[i]) <= win
        m[i] = False
        if m.any() and abs(y[i] - np.median(y[m])) > thr:
            keep[i] = False
    return keep


def case_steep_edge():
    # 페인트 UV 흡수단: 0.07 -> 0.85 를 ~0.12 um 에, 데이터 시작 근처 (실측 사례)
    x = np.linspace(0.22, 2.5, 4000)
    edge = lambda xx: 0.07 + 0.78 / (1 + np.exp(-(xx - 0.38) / 0.027))
    dip = lambda xx: 0.4 - 0.25 * np.exp(-((xx - 1.6) / 0.01) ** 2)   # 실제 좁은 dip (오탐 가드)
    img, calib = cart_figure([(x, edge(x), "red"), (x, dip(x), "blue")], (0.2, 2.5), (0, 1),
                             [0.5, 1.0, 1.5, 2.0, 2.5], [0, 0.2, 0.4, 0.6, 0.8, 1.0])
    blue = (img[..., 2] > 150) & (img[..., 0] < 110) & (img[..., 1] < 110)
    grid = np.round(np.arange(0.23, 2.45 + 1e-9, 0.01), 4)
    raw = {}
    for name, mask in (("edge", red(img)), ("dip", blue)):
        cols, rows = column_median(mask, calib["box_px"], 3)
        raw[name] = (inv(calib, "x", cols), inv(calib, "y", rows))
    xe, ye = raw["edge"]
    keep = local_median_reject(xe, ye)
    edge_ok = resample(xe, ye, grid, 0.005)
    edge_rej = resample(xe[keep], ye[keep], grid, 0.005)
    dip_ok = resample(*raw["dip"], grid, 0.005)
    nan_mask = ~np.isfinite(edge_rej)
    filled = np.interp(grid, grid[~nan_mask], edge_rej[~nan_mask])
    def integ(xx, yy):                    # 가중 평균 (참값 대조용; 빠진 점은 분모에서도 빠짐)
        ok = np.isfinite(yy)
        w = np.exp(-((xx[ok] - 0.6) / 0.4) ** 2)
        return float(np.sum(yy[ok] * w) / np.sum(w))

    truth = integ(grid, edge(grid))
    versions = (
        (f"결함 A: local-median 제거({int((~keep).sum())}열) -> NaN 행", {"edge": edge_rej, "dip": dip_ok}, None),
        ("결함 A': 같은 제거, 행 자체 삭제(곡선 1개 CSV)", {"edge": edge_rej[~nan_mask]}, None, grid[~nan_mask]),
        ("결함 B: 제거 후 보간 메움(_interp)", {"edge": filled, "dip": dip_ok}, {"edge": nan_mask.astype(float)}),
        ("정상: 제거 안 함 (+고립 dip 유지)", {"edge": edge_ok, "dip": dip_ok}, None),
    )
    out = []
    for version, curves, interp, *xg in versions:
        xx = xg[0] if xg else grid
        flags = run_extract(xx, curves, interp, calib)
        note = f"가중 적분 오차 {integ(xx, curves['edge']) - truth:+.4f}"
        if "dip" in curves:
            note += f", 고립 dip flag {sum(f['curve'] == 'dip' for f in flags)}"
        out.append((version, flags, note))
    return out


# ---------------------------------------------------------------- 3 로컬/전체 이중 차감
def case_double_subtract():
    x = np.linspace(0, 10, 600)
    ytrue = lambda xx: 0.5 + 0.3 * np.sin(xx)
    # 아래 패널 (다중 패널 그림의 두 번째 패널처럼 box top 이 이미지 중간)
    img, calib = cart_figure([(x, ytrue(x), "red")], (0, 10), (0, 1), [0, 2, 4, 6, 8, 10],
                             [0, 0.2, 0.4, 0.6, 0.8, 1.0], figsize=(6, 8), rect=(0.12, 0.06, 0.8, 0.4))
    box = calib["box_px"]
    top, bottom = int(round(box["top"])), int(round(box["bottom"]))
    sub = red(img)[top:bottom + 1, :]                    # box 로 자른 로컬 배열
    cols = np.arange(int(box["left"]) + 3, int(box["right"]) - 2)
    out = []
    for version, shift in (("결함: 로컬 행을 전체 행 공식에 넣음(box_top 이중 차감)", 0), ("정상: 로컬 행 + box_top", top)):
        xs, ys = [], []
        for c in cols:
            rr = np.nonzero(sub[:, c])[0]
            if len(rr):
                xs.append(inv(calib, "x", c))
                ys.append(inv(calib, "y", float(np.median(rr)) + shift))   # inv 는 전체 행 기준 공식
        xs, ys = np.array(xs, float), np.array(ys, float)
        err = float(np.max(np.abs(ys - ytrue(xs))))
        out.append((version, run_extract(xs, {"red": ys}, calib=calib), f"max|err| {err:.3f}"))
    return out


# ---------------------------------------------------------------- 4 끝 눈금-테두리 겹침
def detect_bottom_ticks(img, box, band, exclude_border_px):
    """결함 탐지기: 바닥 테두리 바로 위 띠에서 세로 dark 획 클러스터, 테두리 근처 클러스터 제외."""
    d = dark(img)
    r1 = int(round(box["bottom"])) - 3
    prof = d[r1 - band:r1, :].sum(axis=0) >= band // 2
    centers = []
    for i0, i1 in ce._runs(prof):
        c = 0.5 * (i0 + i1)
        if c - box["left"] > exclude_border_px and box["right"] - c > exclude_border_px:
            centers.append(c)
    return np.array(centers)


def measure_right_border(img, box):
    d = dark(img)
    r = int(round(0.5 * (box["top"] + box["bottom"])))
    c0 = int(round(box["right"]))
    cs = np.arange(c0 - 4, c0 + 5)
    w = d[r, cs].astype(float)
    return float(np.sum(cs * w) / np.sum(w))


def case_border_tick():
    x = np.linspace(2.6, 16, 600)
    xticks = [4, 6, 8, 10, 12, 14, 16]
    img, calib = cart_figure([(x, 0.5 + 0.3 * np.sin(x), "red")], (2.6, 16), (0, 1), xticks,
                             [0, 0.2, 0.4, 0.6, 0.8, 1.0])
    found = detect_bottom_ticks(img, calib["box_px"], band=8, exclude_border_px=4)
    vals = xticks[:len(found)]
    out = []
    c_def = dict(calib, x_ticks=[[v, p] for v, p in zip(vals, found)])
    c_ok = dict(calib, x_ticks=c_def["x_ticks"] + [[16, measure_right_border(img, calib["box_px"])]])
    for version, c in ((f"결함: 탐지 {len(found)}/7 (16 이 테두리에 가림)", c_def), ("정상: 테두리 = 눈금 16 추가", c_ok)):
        rep, flags = cc.check(c)
        out.append((version, flags, f"x RMS {rep['axes']['x']['rms_px']:.3f} px"))
    # 눈금 하나 오검출 (8 의 픽셀을 +4 px) -> dropped 후보로 보고만, 목록은 그대로
    bad = [list(t) for t in c_ok["x_ticks"]]
    bad[2][1] += 4.0
    rep, flags = cc.check(dict(calib, x_ticks=bad))
    out.append(("결함: 눈금 8 오검출 +4 px", flags, f"dropped 후보 {rep['axes']['x']['dropped_candidates']}, "
                f"눈금 {len(rep['axes']['x']['ticks'])}개 유지"))
    return out


# ---------------------------------------------------------------- 5 polar 지름 끝 돌출
def bilinear(gray, x, y):
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    return (gray[y0, x0] * (1 - fx) * (1 - fy) + gray[y0, x0 + 1] * fx * (1 - fy)
            + gray[y0 + 1, x0] * (1 - fx) * fy + gray[y0 + 1, x0 + 1] * fx * fy)


def case_polar():
    fig = plt.figure(figsize=(7, 4.2), dpi=DPI)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.12, 1.1)
    ax.set_aspect("equal")
    ax.axis("off")
    th = np.linspace(0, np.pi, 721)
    for rv in (0.2, 0.4, 0.6, 0.8):
        ax.plot(rv * np.cos(th), rv * np.sin(th), color="0.6", lw=0.8)
    for deg in range(30, 180, 30):
        ax.plot([0, np.cos(np.radians(deg))], [0, np.sin(np.radians(deg))], color="0.6", lw=0.8)
    ax.plot(np.cos(th), np.sin(th), color="black", lw=1.5)
    ax.plot([-1, 1], [0, 0], color="black", lw=1.5, solid_capstyle="projecting")
    ang = np.linspace(-80, 80, 161)                                   # theta: 0 = 위, + = 오른쪽
    rc = 0.85 * np.cos(np.radians(ang)) ** 0.3
    ax.plot(rc * np.cos(np.radians(90 - ang)), rc * np.sin(np.radians(90 - ang)), color="red", lw=1.5)
    fig.canvas.draw()
    H = int(fig.get_figheight() * DPI)
    c0, r0 = px_of(ax, H, 0, 0)
    c1, _ = px_of(ax, H, 1, 0)
    R_true = float(c1[0] - c0[0])
    img = render(fig)
    gray = img.mean(axis=2)
    d = dark(img, 80)
    # 지름선 = 최장 수평 dark run -> cx (중점), R_diam (반길이), cy (선 세로 폭 중앙)
    best = (0, 0, 0)
    for r in range(d.shape[0]):
        for i0, i1 in ce._runs(d[r]):
            if i1 - i0 > best[2] - best[1]:
                best = (r, i0, i1)
    row, i0, i1 = best
    cx = 0.5 * (i0 + i1)
    R_diam = 0.5 * (i1 - i0)
    cs = int(round(cx - 0.5 * R_diam))
    rr = [r for r in range(row - 6, row + 7) if d[r, cs]]
    cy = 0.5 * (min(rr) + max(rr))
    # 격자 원 반경: 15~165° 광선(살 제외)에서 nominal ±0.05 창 안 어두움 가중 중심
    ring_vals = [0.2, 0.4, 0.6, 0.8, 1.0]
    r_ticks = []
    for v in ring_vals:
        meas = []
        for deg in (15, 45, 75, 105, 135, 165):
            s = np.arange((v - 0.05) * R_diam, (v + 0.05) * R_diam, 0.25)
            px = cx + s * np.cos(np.radians(deg))
            py = cy - s * np.sin(np.radians(deg))
            wgt = np.clip(255 - bilinear(gray, px, py) - 5, 0, None)
            meas.append(float(np.sum(s * wgt) / np.sum(wgt)))
        r_ticks.append([v, float(np.median(meas))])
    rt = np.array(r_ticks)
    R_ring = float(np.sum(rt[:, 0] * rt[:, 1]) / np.sum(rt[:, 0] ** 2))      # 원점 지나는 LSQ
    # 각도 격자(살): r = 0.5 원 위 화면각 ±3° 창 어두움 가중 중심 -> theta 눈금 점
    theta_ticks = []
    for scr in range(30, 180, 30):
        ph = np.radians(np.arange(scr - 3, scr + 3, 0.02))
        rad = 0.5 * R_diam
        px, py = cx + rad * np.cos(ph), cy - rad * np.sin(ph)
        wgt = np.clip(255 - bilinear(gray, px, py) - 5, 0, None)
        phm = float(np.sum(ph * wgt) / np.sum(wgt))
        theta_ticks.append([90 - scr, [cx + rad * np.cos(phm), cy - rad * np.sin(phm)]])
    base = {"type": "polar", "center_px": [cx, cy], "r_min": 0.0, "r_max": 1.0, "theta0_deg": 90,
            "theta_dir": -1, "theta_range": [-90, 90], "r_ticks": r_ticks,
            "theta_ticks": theta_ticks}
    out = []
    for version, R in (("결함: R = 지름선 반길이", R_diam), ("정상: R = 격자 원 LSQ", R_ring)):
        rep, flags = cc.check(dict(base, R_px=R))
        out.append((version, flags, f"R-R_true {R - R_true:+.2f} px, r RMS {rep['r']['rms_px']:.2f} px, "
                    f"theta RMS {rep['theta']['rms_px']:.2f} px"))
    return out


# ---------------------------------------------------------------- 6 long CSV
def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(header) + "\n")
        for r in rows:
            f.write(",".join("" if v is None else v if isinstance(v, str) else f"{v:g}" for v in r) + "\n")


def cli(script, *args):
    r = subprocess.run([sys.executable, os.path.join(TOOLS, script), *args], capture_output=True, text=True,
                       encoding="utf-8")
    return r.returncode, r.stdout


def case_long_csv():
    xa = np.round(np.arange(0, 10.0001, 0.1), 3)
    xb = np.round(np.arange(0, 10.0001, 0.25), 3)                  # 곡선마다 자기 x
    ya, yb = 0.5 + 0.2 * np.sin(xa), 0.4 + 0.1 * np.cos(xb)
    hole = (xa > 4) & (xa < 6)                                      # A 의 4~6 구간 값 없음
    out = []
    with tempfile.TemporaryDirectory() as td:
        pl, pw, pr, pn = (os.path.join(td, n) for n in ("long.csv", "wide.csv", "long_rowdel.csv", "long_ok.csv"))
        # 정상: 곡선마다 다른 x 의 long
        write_csv(pn, ["series", "x", "y"], [("A", a, b) for a, b in zip(xa, ya)] + [("B", a, b) for a, b in zip(xb, yb)])
        series = ce.read_csv(pn)
        flags, _ = ce.check_series(series)
        code, txt = cli("check_extraction.py", pn)
        last = txt.strip().splitlines()[-1]
        good = code == 0 and last == "check_extraction: PASS flag 0건" and [len(v[0]) for v in series.values()] == [len(xa), len(xb)]
        out.append(("정상: long CSV, 곡선마다 다른 x", flags if good else flags + [{"type": "cli", "msg": txt}],
                    f"series {list(series)}, CLI 종료코드 {code}, 끝줄 '{last}'"))
        # 값 없음 구간: wide(공통 x, 빈 칸) vs long(빈 y 행) -> 같은 A flag
        write_csv(pw, ["x", "A"], [(a, None if h else b) for a, b, h in zip(xa, ya, hole)])
        write_csv(pl, ["series", "x", "y"], [("A", a, None if h else b) for a, b, h in zip(xa, ya, hole)]
                  + [("B", a, b) for a, b in zip(xb, yb)])
        fw, _ = ce.check_series(ce.read_csv(pw))
        fl, _ = ce.check_series(ce.read_csv(pl))
        key = lambda fs: sorted((f["type"], f["curve"], f.get("n"), f.get("x0"), f.get("x1")) for f in fs if f["curve"] == "A")
        same = key(fw) == key(fl) and any(f["type"] == "nan_run" for f in fl)
        out.append(("결함: long CSV 값 없음 구간 (wide 와 같은 A flag)", fl if same else [],
                    f"wide A flag {len(key(fw))}건, long A flag {len(key(fl))}건, 동일 {same}"))
        # 행 삭제 -> gap
        write_csv(pr, ["series", "x", "y"], [("A", a, b) for a, b, h in zip(xa, ya, hole) if not h]
                  + [("B", a, b) for a, b in zip(xb, yb)])
        fr, _ = ce.check_series(ce.read_csv(pr))
        code, txt = cli("check_extraction.py", pr)
        out.append(("결함: long CSV 행 삭제 (A 4~6)", fr if code == 1 else [],
                    f"CLI 종료코드 {code}, 끝줄 '{txt.strip().splitlines()[-1]}'"))
    return out


# ---------------------------------------------------------------- 7 calib.json·변환 왕복·overlay
def colored(img, x, y, color, tol=30):
    """(x, y) 3x3 이웃에 color(+-tol) 픽셀이 있는지."""
    xi, yi = int(round(x)), int(round(y))
    win = img[yi - 1:yi + 2, xi - 1:xi + 2].reshape(-1, 3).astype(int)
    return bool((np.abs(win - np.array(color)) <= tol).all(axis=1).any())


def overlay_run(td, img, calib, tag):
    """png + calib.json 저장 -> CLI --overlay 실행 -> (종료코드, 끝줄, overlay 배열, 로드한 calib)."""
    ip, cp, op = (os.path.join(td, f"{tag}{e}") for e in (".png", ".json", "_ov.png"))
    Image.fromarray(img.astype(np.uint8)).save(ip)
    cm.save(cp, calib)
    code, txt = cli("check_calibration.py", cp, "--overlay", ip, op)
    return code, txt.strip().splitlines()[-1], np.asarray(Image.open(op).convert("RGB")), cm.load(cp)


def overlay_verdict(flags, ok_expected, marks):
    """정상 = flag 0건이어야 OK (overlay 가 틀리면 flag 를 얹어 MISS). 결함 = overlay 가 맞을 때만 flag 유지."""
    if ok_expected:
        return flags if marks else flags + [{"type": "overlay_fail", "msg": "overlay 표시·종료코드·끝줄 불일치"}]
    return flags if marks else []


def case_calib_json():
    out = []
    with tempfile.TemporaryDirectory() as td:
        # cartesian: 정상 / 눈금 6 을 +4 px (로드한 calib 로 재투영 위치 확인)
        x = np.linspace(0, 10, 300)
        img, calib = cart_figure([(x, 0.5 + 0.3 * np.sin(x), "red")], (0, 10), (0, 1), [0, 2, 4, 6, 8, 10],
                                 [0, 0.2, 0.4, 0.6, 0.8, 1.0])
        bad = dict(calib, x_ticks=[[v, p + (4.0 if v == 6 else 0.0)] for v, p in calib["x_ticks"]])
        for tag, c, ok_expected in (("cart_ok", calib, True), ("cart_bad", bad, False)):
            code, line, ov, loaded = overlay_run(td, img, c, tag)
            rep, flags = cc.check(loaded)
            b = loaded["box_px"]
            marks = code == (0 if ok_expected else 1) and line == cc.summary(rep, flags)
            for v, _p in loaded["x_ticks"]:
                pred = float(cm.to_px(loaded, v, 0.0)[0])
                want = (255, 0, 0) if (not ok_expected and v == 6) else (255, 0, 255)
                marks &= colored(ov, pred, b["top"] + 8, want)
            label = "정상: calib.json -> --overlay (cartesian)" if ok_expected else \
                "결함: calib.json -> --overlay (cartesian), 눈금 6 +4 px 는 빨강"
            out.append((label, overlay_verdict(flags, ok_expected, marks),
                        f"종료코드 {code}, 끝줄 '{line}', overlay 표시 {bool(marks)}"))
        # 값<->픽셀 왕복: cartesian (tick LSQ, given map), polar (theta_dir -1, +1)
        vals = np.array([[0.3, 0.1], [4.2, 0.77], [9.9, 0.99]])
        cg = dict(calib, x_map={"a": 110.9, "b": -133.4}, y_map={"a": -940.0, "b": 1020.5})
        e1 = max(float(np.max(np.abs(np.column_stack(cm.from_px(c, *cm.to_px(c, vals[:, 0], vals[:, 1]))) - vals)))
                 for c in (cm.load(os.path.join(td, "cart_ok.json")), cg))
        e2 = 0.0
        for dirn in (-1, 1):
            cp_ = {"type": "polar", "center_px": [600.0, 640.0], "R_px": 580.0, "r_min": 0.0, "r_max": 1.0,
                   "theta0_deg": 90, "theta_dir": dirn, "theta_range": [-90, 90]}
            tv = np.array([-85.0, -30.0, 0.0, 44.0, 89.0])
            rv = np.array([0.05, 0.3, 0.5, 0.9, 1.0])
            th, r = cm.from_px(cp_, *cm.to_px(cp_, tv, rv))
            e2 = max(e2, float(np.max(np.abs(th - tv))), float(np.max(np.abs(r - rv))))
        out.append(("정상: 값<->픽셀 왕복 (cartesian tick LSQ·given map, polar dir ±1)",
                    [{"type": "roundtrip", "msg": f"{e1:g} {e2:g}"}] if max(e1, e2) > 1e-9 else [],
                    f"max 왕복 오차 cartesian {e1:.1e}, polar {e2:.1e}"))
        # polar overlay (빈 이미지 위): 정상 / R 1% 과대
        cx, cy, R = 600.0, 640.0, 580.0
        pol = {"type": "polar", "center_px": [cx, cy], "R_px": R, "r_min": 0.0, "r_max": 1.0, "theta0_deg": 90,
               "theta_dir": -1, "theta_range": [-90, 90],
               "r_ticks": [[v, v * R] for v in (0.2, 0.4, 0.6, 0.8, 1.0)],
               "theta_ticks": [[float(a), [cx + 0.5 * R * np.sin(np.radians(a)), cy - 0.5 * R * np.cos(np.radians(a))]]
                               for a in (-60, -30, 0, 30, 60)]}
        blank = np.full((700, 1200, 3), 255.0)
        for tag, c, ok_expected in (("pol_ok", pol, True), ("pol_bad", dict(pol, R_px=R * 1.01), False)):
            code, line, ov, loaded = overlay_run(td, blank, c, tag)
            rep, flags = cc.check(loaded)
            want = (255, 0, 255) if ok_expected else (255, 0, 0)
            ring = cm.to_px(loaded, 0.0, 0.6)                 # theta 0 = 위, r 0.6 의 재투영 위치
            marks = code == (0 if ok_expected else 1) and line == cc.summary(rep, flags) \
                and colored(ov, ring[0], ring[1], want)
            label = "정상: calib.json -> --overlay (polar)" if ok_expected else \
                "결함: calib.json -> --overlay (polar), R +1% 격자 원 빨강"
            out.append((label, overlay_verdict(flags, ok_expected, marks),
                        f"종료코드 {code}, 끝줄 '{line}', overlay 표시 {bool(marks)}"))
    return out


# ---------------------------------------------------------------- 판정·표
CASES = [
    ("1 눈금 돌출 오염", case_tick_protrusion, {"near_tick"}),
    ("2 가파른 구간 삭제", case_steep_edge, {"gap", "nan_run", "interp_run"}),
    ("3 로컬/전체 이중 차감", case_double_subtract, {"out_of_range"}),
    ("4 끝 눈금-테두리 겹침", case_border_tick, {"border_tick_missing", "dropped_candidate"}),
    ("5 polar 지름 끝 돌출 R 과대", case_polar, {"reproj"}),
    ("6 long CSV", case_long_csv, {"gap", "nan_run"}),
    ("7 calib.json·overlay", case_calib_json, {"reproj", "dropped_candidate"}),
]


VERBOSE = "-v" in sys.argv


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bad = 0
    print("| 유형 | 버전 | flag | 판정 | 참값 대조 |")
    print("|---|---|---|---|---|")
    for title, fn, expect in CASES:
        for version, flags, note in fn():
            types = sorted({f["type"] for f in flags})
            if version.startswith("정상"):
                ok = not flags
            else:
                ok = bool(set(types) & expect)
            bad += not ok
            shown = ", ".join(f"{t}×{sum(f['type'] == t for f in flags)}" for t in types) or "0건"
            print(f"| {title} | {version} | {shown} | {'OK' if ok else 'MISS'} | {note} |")
            if not ok or VERBOSE:
                for f in flags:
                    print(f"    {f['msg']}")
    print(f"\nMISS {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
