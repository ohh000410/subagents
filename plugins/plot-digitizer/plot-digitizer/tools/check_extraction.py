"""
추출 CSV 자동 경고 flag. 경고만 출력한다 — 점을 지우거나 고치지 않는다.

사용법:
    python check_extraction.py <extract.csv> [--calib calib.json] [--x COL]
                               [--gap-factor 3] [--near-px 2] [--json]

CSV 형식은 헤더로 자동 감지한다.
- wide: x 열(기본 첫 열; polar 면 각도) + 곡선 열들. 곡선마다 같은 x 행. 빈 칸/nan = 값 없음.
  `<곡선>_interp` 열(0/1)이 있으면 그 곡선의 보간으로 메운 행 표시로 읽는다.
- long: 헤더에 `series` 열이 있으면 long. `series,x,y` (x 열 = `x`, 값 열 = `y`; 없으면 series 다음 두 열.
  `--x` 로 x 열 지정). 곡선마다 자기 x. 선택 열 `interp`(0/1) = 그 행이 보간으로 메운 행.
calib.json 스키마 = calib_model.py docstring. 없으면 범위·눈금 근처 검사는 하지 않는다(보고에 명시).

flag 종류
- empty          : 점 0개 곡선
- gap            : 유효 점 사이 x 간격 > gap_factor * 중앙값 간격 (가파른 구간이 지워진 사례
                   feedback_steep_edge_breaks_local_median_outlier_rejection)
- nan_run        : 값 없음 연속 구간 (edge = CSV 시작/끝에 붙은 구간)
- interp_run     : `_interp` 로 표시된 보간 구간
- out_of_range   : 캘리브 범위 밖 값. cartesian = box 밖 0.5 px 초과, polar = r/theta 범위 밖
                   (로컬/전체 좌표 이중 차감 사례 feedback_local_vs_full_image_row_coordinate_bug)
- near_tick      : 안쪽 눈금 발자국(테두리에서 tick_len_px 안, 눈금 선에서 near_px 안)에 놓인 점.
                   cartesian + calib 의 tick_len_px·tick_sides 가 있을 때만
                   (feedback_tick_protrusion_depth_must_be_measured_not_assumed)

이웃과 값이 튀는 점(고립점)은 flag 하지 않는다 — 실제 데이터일 수 있다
(feedback_isolated_curve_outlier_may_be_real_not_artifact).

종료코드 0 = flag 없음, 1 = flag 있음 (WARN). flag 마다 원본 확인 후 설명하거나 고친다.
마지막 줄 `check_extraction: PASS|WARN flag N건` = 보고에 그대로 옮기는 한 줄 판정.
"""
import argparse
import csv
import json
import sys

import numpy as np

import calib_model as cm


def _num(s):
    s = s.strip()
    return float(s) if s and s.lower() != "nan" else np.nan


def read_csv(path, xcol=None):
    """CSV -> {곡선: (x, y, interp 또는 None)}. 헤더에 series 열이 있으면 long, 없으면 wide."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    head, body = [h.strip() for h in rows[0]], [r for r in rows[1:] if any(s.strip() for s in r)]
    if "series" in head:
        return _read_long(head, body, xcol)
    xcol = head[0] if xcol is None else xcol
    cols = {h: np.array([_num(r[i]) if i < len(r) else np.nan for r in body]) for i, h in enumerate(head)}
    x = cols.pop(xcol)
    order = np.argsort(x, kind="stable")
    x = x[order]
    cols = {k: v[order] for k, v in cols.items()}
    interp = {k[:-len("_interp")]: v for k, v in cols.items() if k.endswith("_interp")}
    curves = {k: v for k, v in cols.items() if not k.endswith("_interp")}
    return {k: (x, v, interp.get(k)) for k, v in curves.items()}


def _read_long(head, body, xcol):
    rest = [h for h in head if h not in ("series", "interp")]
    xcol = xcol or ("x" if "x" in head else rest[0])
    ycol = "y" if "y" in head else [h for h in rest if h != xcol][0]
    ix, iy, isr = head.index(xcol), head.index(ycol), head.index("series")
    ii = head.index("interp") if "interp" in head else None
    names = list(dict.fromkeys(r[isr].strip() for r in body))
    out = {}
    for name in names:
        rs = [r for r in body if r[isr].strip() == name]
        x = np.array([_num(r[ix]) for r in rs])
        y = np.array([_num(r[iy]) if iy < len(r) else np.nan for r in rs])
        ip = None if ii is None else np.array([_num(r[ii]) if ii < len(r) else np.nan for r in rs])
        order = np.argsort(x, kind="stable")
        out[name] = (x[order], y[order], None if ip is None else ip[order])
    return out


def _runs(mask):
    """True 연속 구간 [(i0, i1), ...] (i1 포함)."""
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def check_curve(name, x, y, interp, gap_factor):
    flags = []
    ok = np.isfinite(y) & np.isfinite(x)
    if not ok.any():
        return [{"type": "empty", "curve": name, "msg": f"{name}: 점 0개"}]
    xv = x[ok]
    if len(xv) >= 3:
        dx = np.diff(xv)
        med = float(np.median(dx))
        for i in np.nonzero(dx > gap_factor * med)[0]:
            flags.append({"type": "gap", "curve": name, "x0": float(xv[i]), "x1": float(xv[i + 1]),
                          "msg": f"{name}: 빈 구간 x {xv[i]:g} ~ {xv[i + 1]:g} "
                                 f"(간격 {dx[i]:g} = 중앙값 {med:g} 의 {dx[i] / med:.1f}배)"})
    n = len(y)
    for i0, i1 in _runs(~np.isfinite(y)):
        where = "edge" if i0 == 0 or i1 == n - 1 else "interior"
        flags.append({"type": "nan_run", "curve": name, "x0": float(x[i0]), "x1": float(x[i1]),
                      "n": i1 - i0 + 1, "where": where,
                      "msg": f"{name}: 값 없음 {i1 - i0 + 1}행 x {x[i0]:g} ~ {x[i1]:g} ({where})"})
    if interp is not None:
        for i0, i1 in _runs(np.nan_to_num(interp) != 0):
            flags.append({"type": "interp_run", "curve": name, "x0": float(x[i0]), "x1": float(x[i1]),
                          "n": i1 - i0 + 1,
                          "msg": f"{name}: 보간으로 메운 {i1 - i0 + 1}행 x {x[i0]:g} ~ {x[i1]:g}"})
    return flags


def _span_msg(xs):
    return f"x {np.min(xs):g} ~ {np.max(xs):g}"


def check_range_cartesian(c, name, x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    col, row = cm.cart_to_px(c, x[ok], y[ok])
    b = c["box_px"]
    out = (col < b["left"] - 0.5) | (col > b["right"] + 0.5) | (row < b["top"] - 0.5) | (row > b["bottom"] + 0.5)
    if not out.any():
        return []
    yo = y[ok][out]
    return [{"type": "out_of_range", "curve": name, "n": int(out.sum()),
             "msg": f"{name}: box 밖 {int(out.sum())}점 / {int(ok.sum())} ({_span_msg(x[ok][out])}, "
                    f"y {yo.min():g} ~ {yo.max():g})"}]


def check_range_polar(c, name, theta, r):
    ok = np.isfinite(theta) & np.isfinite(r)
    t, v = theta[ok], r[ok]
    half_px = 0.5 * (c["r_max"] - c["r_min"]) / c["R_px"]      # 0.5 px 를 값으로
    lo_t, hi_t = sorted(c["theta_range"])
    out = (v < c["r_min"] - half_px) | (v > c["r_max"] + half_px) | (t < lo_t) | (t > hi_t)
    if not out.any():
        return []
    return [{"type": "out_of_range", "curve": name, "n": int(out.sum()),
             "msg": f"{name}: r/theta 범위 밖 {int(out.sum())}점 / {int(ok.sum())} "
                    f"(theta {t[out].min():g} ~ {t[out].max():g}, r {v[out].min():g} ~ {v[out].max():g})"}]


def check_near_tick(c, name, x, y, near_px):
    ok = np.isfinite(x) & np.isfinite(y)
    xs, ys = x[ok], y[ok]
    col, row = cm.cart_to_px(c, xs, ys)
    b, L, sides = c["box_px"], float(c["tick_len_px"]), c["tick_sides"]
    zone = {"left": col - b["left"] <= L + near_px, "right": b["right"] - col <= L + near_px,
            "top": row - b["top"] <= L + near_px, "bottom": b["bottom"] - row <= L + near_px}
    flags = []
    for side in sides:
        axis, coord = ("y", row) if side in ("left", "right") else ("x", col)
        for tv, tpx in c.get(f"{axis}_ticks", []):
            hit = zone[side] & (np.abs(coord - tpx) <= near_px)
            if hit.any():
                flags.append({"type": "near_tick", "curve": name, "side": side, "tick": tv, "n": int(hit.sum()),
                              "msg": f"{name}: {side} {axis} 눈금 {tv:g} 발자국 안 {int(hit.sum())}점 "
                                     f"({_span_msg(xs[hit])}) - 눈금 돌출 오염 후보, 곡선이 실제로 지나는지 원본 확인"})
    return flags


def check(x, curves, interp, calib=None, gap_factor=3.0, near_px=2.0):
    """wide: 모든 곡선이 같은 x. long 은 check_series."""
    return check_series({k: (x, y, interp.get(k)) for k, y in curves.items()}, calib, gap_factor, near_px)


def check_series(series, calib=None, gap_factor=3.0, near_px=2.0):
    """series = {곡선: (x, y, interp 또는 None)}."""
    flags, notes = [], []
    if calib is None:
        notes.append("calib 없음: 범위·눈금 근처 검사 안 함")
    elif calib["type"] == "cartesian" and "tick_len_px" not in calib:
        notes.append("tick_len_px 없음: 눈금 근처 검사 안 함 (돌출 길이는 실측해서 넣는다)")
    elif calib["type"] == "polar":
        notes.append("polar: 눈금 근처 검사 없음 (cartesian 전용)")
    for name, (x, y, interp) in series.items():
        flags += check_curve(name, x, y, interp, gap_factor)
        if calib is None:
            continue
        if calib["type"] == "cartesian":
            flags += check_range_cartesian(calib, name, x, y)
            if "tick_len_px" in calib:
                flags += check_near_tick(calib, name, x, y, near_px)
        else:
            flags += check_range_polar(calib, name, x, y)
    return flags, notes


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--calib")
    ap.add_argument("--x", help="x(각도) 열 이름. 기본 첫 열")
    ap.add_argument("--gap-factor", type=float, default=3.0)
    ap.add_argument("--near-px", type=float, default=2.0)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    series = read_csv(args.csv, args.x)
    calib = cm.load(args.calib) if args.calib else None
    flags, notes = check_series(series, calib, args.gap_factor, args.near_px)
    if args.json:
        print(json.dumps({"flags": flags, "notes": notes}, ensure_ascii=False, indent=1))
    else:
        print(f"[extract] {args.csv}  curves={len(series)} rows={sum(len(v[0]) for v in series.values())}")
        for n in notes:
            print(f"  note: {n}")
        for f in flags:
            print(f"WARN [{f['type']}] {f['msg']}")
        print(f"check_extraction: {'WARN' if flags else 'PASS'} flag {len(flags)}건")
    sys.exit(1 if flags else 0)


if __name__ == "__main__":
    main()
