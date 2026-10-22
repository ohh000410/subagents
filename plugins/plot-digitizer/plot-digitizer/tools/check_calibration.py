"""
캘리브 눈금별 재투영 오차 보고. 보고만 한다 — 눈금을 자동 제외하거나 캘리브를 고치지 않는다.

사용법:
    python check_calibration.py <calib.json> [--tol-px 1.0] [--json] [--overlay <원본 이미지> <출력 png>]

calib.json 스키마 = calib_model.py docstring (cartesian 선형 축 / polar radial 선형).

보고 항목
- 눈금마다 값 -> 픽셀 재투영 오차(px) = (추출에 쓴 변환으로 투영한 픽셀) - (측정 눈금 픽셀), 축별 RMS
- 눈금 LSQ 재적합과 leave-one-out(LOO) 잔차. |LOO| 최대 눈금을 하나씩 빼며 다시 계산해 |LOO| > tol 이
  남지 않을 때까지 뺀 눈금 = dropped 후보(순위). 보고만 하고 캘리브·눈금 목록은 그대로 둔다
- cartesian: 테두리가 끝 눈금에서 한 간격 더 간 위치에 있으면 = 테두리에 가려 빠진 눈금 후보
- polar: 쓴 R_px 와 격자 원 LSQ R 의 차이, 각도 눈금의 접선 방향 오차(px)

--overlay: 원본 이미지 위에 눈금별 재투영 위치를 그려 캘리브 체크 overlay png 를 쓴다 (도구 부산물, 항상 쓴다).
- cartesian: 재투영 눈금선(마젠타, 전체 길이) + 값 라벨, 측정 눈금(녹색 점, 테두리 위), box(청록)
- polar: 재투영 격자 원·각도선(마젠타) + 값 라벨, 측정 반경/각도 점(녹색), R_px 원(청록), 중심(+)
- flag 눈금(재투영 오차 > tol, dropped 후보, 테두리에 가린 끝 눈금 후보)은 빨강
- 좌측 상단 = 마지막 요약 줄과 같은 문구

종료코드 0 = flag 없음, 1 = flag 있음 (WARN), 2 = 검사한 눈금 0개 (FAIL — 검사한 것이 없음).
마지막 줄 `check_calibration: PASS|WARN|FAIL N tick, RMS x px`
= 보고에 그대로 옮기는 한 줄 판정 (N = 검사한 눈금 수, RMS = 그 눈금들의 재투영 오차 RMS).
검사한 눈금 = 재투영 오차가 유한한 눈금. NaN 좌표·NaN 변환식의 눈금은 `nonfinite` flag 로 빠진다
(nan 은 "> tol" 이 거짓이라 PASS 로 나갔다, 2026-10-22 교차 검토).
한 축(polar 는 r)의 눈금이 없으면(키 없음·빈 목록 같음) 그 축은 `no_ticks` flag (WARN).
cartesian 축이 변환식(x_map/y_map) 없이 눈금 2개 이하면 그 축은 `no_dof` flag (WARN) 로 검사에서 빠진다 —
눈금으로 맞춘 직선이 그 눈금을 지나 오차가 늘 0 이라, 값을 잘못 넣어도 PASS 였다(2026-10-22 교차 검토).

tol 1.0 px 근거: 격자 원 LSQ 잔차 <= 0.08 px, 지름선 끝 돌출로 인한 R 과대 2.5~3 px
(references/calibration_extraction.md 「반원 polar 캘리브」). 1 px 는 둘 사이를 가른다.
"""
import argparse
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

import calib_model as cm

# 끝 눈금 = 테두리 판정 허용폭: 눈금 간격의 15% (references/calibration_extraction.md 「데카르트 눈금 검출」)
BORDER_TICK_FRAC = 0.15


def _loo(values, px):
    """눈금 하나씩 빼고 직선 재적합 -> 뺀 눈금의 예측 오차. 눈금 < 3 이면 None."""
    n = len(values)
    if n < 3:
        return None
    out = np.empty(n)
    for i in range(n):
        m = np.arange(n) != i
        a, b = cm.lsq_line(values[m], px[m])
        out[i] = a * values[i] + b - px[i]
    return out


def _ticks(c, key):
    """눈금 목록 -> (n, 2) 배열. 키 없음과 빈 목록은 같은 '눈금 없음'(빈 목록은 IndexError 로 죽었다)."""
    return np.asarray(c.get(key) or [], float).reshape(-1, 2)


def _tick_table(values, px, pred, flags, label, tol):
    a_fit, b_fit = cm.lsq_line(values, px)
    fit_res = a_fit * values + b_fit - px
    loo = _loo(values, px)
    err = pred - px
    rows = []
    for i in range(len(values)):
        rows.append({"value": float(values[i]), "px": float(px[i]), "err_px": float(err[i]),
                     "fit_res_px": float(fit_res[i]),
                     "loo_px": None if loo is None else float(loo[i])})
        if not np.isfinite(err[i]):
            flags.append({"type": "nonfinite", "axis": label, "value": float(values[i]),
                          "msg": f"{label} 눈금 {values[i]:g}: 재투영 오차 {err[i]} - 눈금 좌표나 변환식에 NaN/inf, 검사 못 함"})
        elif not abs(err[i]) <= tol:
            flags.append({"type": "reproj", "axis": label, "value": float(values[i]),
                          "msg": f"{label} 눈금 {values[i]:g}: 재투영 오차 {err[i]:+.2f} px > {tol} px"})
    cand, rms_rest = _dropped_candidates(values, px, tol)
    for k, (i, r) in enumerate(cand, 1):
        flags.append({"type": "dropped_candidate", "axis": label, "value": float(values[i]), "rank": k,
                      "msg": f"{label} 눈금 {values[i]:g}: LOO 잔차 {r:+.2f} px > {tol} px -> dropped 후보 {k}순위 "
                             f"(자동 제외 안 함, 원본 확인. 후보 빼면 재적합 RMS {rms_rest:.3f} px)"})
    rms = float(np.sqrt(np.mean(err ** 2)))
    return {"ticks": rows, "rms_px": rms, "fit": {"a": a_fit, "b": b_fit},
            "fit_rms_px": float(np.sqrt(np.mean(fit_res ** 2))),
            "dropped_candidates": [float(values[i]) for i, _ in cand]}


def _dropped_candidates(values, px, tol):
    """|LOO| 최대 눈금을 하나씩 빼며 다시 LOO -> 최대가 tol 이하가 될 때까지. 보고용 목록만 만든다.
    나쁜 눈금 하나가 직선을 끌어 좋은 눈금의 LOO 까지 tol 을 넘기는 것을 구분하기 위함."""
    idx = np.arange(len(values))
    cand = []
    while len(idx) >= 3:
        loo = _loo(values[idx], px[idx])
        j = int(np.argmax(np.abs(loo)))
        if abs(loo[j]) <= tol:
            break
        cand.append((int(idx[j]), float(loo[j])))
        idx = np.delete(idx, j)
    a, b = cm.lsq_line(values[idx], px[idx])
    return cand, float(np.sqrt(np.mean((a * values[idx] + b - px[idx]) ** 2)))


def _border_tick(values, px, a, b, border_lo, border_hi, label, flags):
    """끝 눈금이 테두리와 겹쳐 눈금 목록에서 빠졌는지."""
    order = np.argsort(px)
    v, p = values[order], px[order]
    step_v = float(np.median(np.diff(v)))       # px 오름차순 기준 값 간격 (y 축이면 음수)
    step_px = abs(a * step_v)
    notes = []
    for border, end_v, sgn, side in ((border_lo, v[0], -1, "low-px"), (border_hi, v[-1], +1, "high-px")):
        end_px = a * end_v + b
        nxt_v = end_v + sgn * step_v
        nxt_px = a * nxt_v + b
        if abs(border - end_px) <= BORDER_TICK_FRAC * step_px:
            notes.append(f"{label} {side} 테두리 = 끝 눈금 {end_v:g} (목록에 있음)")
        elif abs(border - nxt_px) <= BORDER_TICK_FRAC * step_px:
            flags.append({"type": "border_tick_missing", "axis": label, "value": float(nxt_v),
                          "msg": f"{label} {side} 테두리({border:.1f} px)가 끝 눈금 {end_v:g} 에서 한 간격 "
                                 f"뒤({nxt_px:.1f} px) = 눈금 {nxt_v:g} 가 테두리에 가려 목록에서 빠졌을 후보"})
    return notes


def check_cartesian(c, tol):
    flags, report = [], {"type": "cartesian", "axes": {}, "notes": []}
    box = c.get("box_px")
    for axis in ("x", "y"):
        t = _ticks(c, f"{axis}_ticks")
        if not len(t):
            flags.append({"type": "no_ticks", "axis": axis, "msg": f"{axis}: 눈금 없음 - 이 축은 검사하지 못함"})
            continue
        a, b, src = cm.axis_map(c, axis)
        tab = _tick_table(t[:, 0], t[:, 1], a * t[:, 0] + b, flags, axis, tol)
        tab["map"] = {"a": a, "b": b, "source": src}
        tab["checked"] = not (src == "tick_lsq" and len(t) < 3)
        if not tab["checked"]:
            flags.append({"type": "no_dof", "axis": axis,
                          "msg": f"{axis}: 눈금 {len(t)}개로 맞춘 직선은 재투영 오차가 늘 0 - 이 축은 검사하지 못함 "
                                 f"(눈금 3개 이상 또는 독립 변환식 {axis}_map)"})
        report["axes"][axis] = tab
        if box is not None and len(t) >= 2:
            lo, hi = (box["left"], box["right"]) if axis == "x" else (box["top"], box["bottom"])
            report["notes"] += _border_tick(t[:, 0], t[:, 1], a, b, lo, hi, axis, flags)
    return report, flags


def check_polar(c, tol):
    flags, report = [], {"type": "polar", "notes": []}
    t = _ticks(c, "r_ticks")
    if not len(t):
        flags.append({"type": "no_ticks", "axis": "r", "msg": "r: 격자 원 눈금 없음 - 반경은 검사하지 못함"})
    else:
        v, r = t[:, 0], t[:, 1]
        pred = cm.polar_r_px(c, v)
        tab = _tick_table(v, r, pred, flags, "r", tol)
        # r_px = a*v + b 재적합 -> r_max 에서의 반경
        a, b = tab["fit"]["a"], tab["fit"]["b"]
        R_fit = a * c["r_max"] + b
        tab["R_used_px"] = float(c["R_px"])
        tab["R_fit_px"] = float(R_fit)
        tab["r_min_offset_fit_px"] = float(a * c["r_min"] + b)
        report["r"] = tab
        report["notes"].append(f"R_used {c['R_px']:.2f} px vs 격자 원 LSQ R {R_fit:.2f} px "
                               f"(차 {c['R_px'] - R_fit:+.2f} px, r_min 위치 {a * c['r_min'] + b:+.2f} px)")
    if c.get("theta_ticks"):
        cx, cy = c["center_px"]
        rows, errs = [], []
        for deg, (x, y) in c["theta_ticks"]:
            phi_meas = np.degrees(np.arctan2(cy - y, x - cx))
            d = (phi_meas - cm.polar_screen_deg(c, deg) + 180.0) % 360.0 - 180.0
            rad = float(np.hypot(x - cx, y - cy))
            e = float(np.radians(d) * rad)          # 접선 방향 px
            rows.append({"value": deg, "px": [x, y], "err_deg": float(d), "err_px": e})
            errs.append(e)
            if not np.isfinite(e):
                flags.append({"type": "nonfinite", "axis": "theta", "value": deg,
                              "msg": f"theta 눈금 {deg:g}°: 접선 오차 {e} - 좌표나 중심에 NaN/inf, 검사 못 함"})
            elif not abs(e) <= tol:
                flags.append({"type": "reproj", "axis": "theta", "value": deg,
                              "msg": f"theta 눈금 {deg:g}°: 접선 오차 {e:+.2f} px ({d:+.3f}°) > {tol} px"})
        report["theta"] = {"ticks": rows, "rms_px": float(np.sqrt(np.mean(np.square(errs))))}
    return report, flags


def check(c, tol=1.0):
    return check_cartesian(c, tol) if c["type"] == "cartesian" else check_polar(c, tol)


def _errs(report):
    """검사한 눈금의 재투영 오차 = 유한한 것만, 자유도 0 인 축(no_dof) 제외."""
    errs = []
    for tab in list(report.get("axes", {}).values()) + [report[k] for k in ("r", "theta") if k in report]:
        if tab.get("checked", True):
            errs += [row["err_px"] for row in tab["ticks"] if np.isfinite(row["err_px"])]
    return errs


def summary(report, flags):
    """`check_calibration: PASS|WARN|FAIL N tick, RMS x px` — 검사한 눈금 재투영 오차 기준.
    검사한 눈금 0개 = FAIL: 검사한 것이 없는데 PASS 로 나갔다(2026-10-22 외부 검토·교차 검토)."""
    errs = _errs(report)
    rms = float(np.sqrt(np.mean(np.square(errs)))) if errs else float("nan")
    verdict = "FAIL" if not errs else "WARN" if flags else "PASS"
    return f"check_calibration: {verdict} {len(errs)} tick, RMS {rms:.3f} px"


MAGENTA, GREEN, CYAN, RED = (255, 0, 255), (0, 200, 0), (0, 200, 255), (255, 0, 0)


def draw_overlay(c, report, flags, image_path, out_path, text=None):
    """재투영 눈금 위치를 원본 이미지에 그려 png 로 저장. flag 눈금은 빨강."""
    im = Image.open(image_path).convert("RGB")
    d = ImageDraw.Draw(im)
    bad = {(f["axis"], round(f["value"], 9)) for f in flags if "axis" in f and "value" in f}
    isbad = lambda axis, v: (axis, round(float(v), 9)) in bad
    if c["type"] == "cartesian":
        b = c["box_px"]
        d.rectangle([b["left"], b["top"], b["right"], b["bottom"]], outline=CYAN)
        for axis in ("x", "y"):
            for row in report.get("axes", {}).get(axis, {}).get("ticks", []):
                v, meas = row["value"], row["px"]
                pred = meas + row["err_px"]
                col = RED if isbad(axis, v) else MAGENTA
                if axis == "x":
                    d.line([(pred, b["top"]), (pred, b["bottom"])], fill=col)
                    d.ellipse([meas - 3, b["bottom"] - 3, meas + 3, b["bottom"] + 3], fill=GREEN)
                    d.text((pred + 2, b["bottom"] + 4), f"{v:g}", fill=col)
                else:
                    d.line([(b["left"], pred), (b["right"], pred)], fill=col)
                    d.ellipse([b["left"] - 3, meas - 3, b["left"] + 3, meas + 3], fill=GREEN)
                    d.text((b["left"] + 4, pred - 12), f"{v:g}", fill=col)
    else:
        cx, cy = c["center_px"]
        scr = np.radians(cm.polar_screen_deg(c, np.linspace(*sorted(c["theta_range"]), 361)))
        d.line([(cx - 8, cy), (cx + 8, cy)], fill=CYAN)
        d.line([(cx, cy - 8), (cx, cy + 8)], fill=CYAN)
        r_rows = report.get("r", {}).get("ticks", [])
        for rad, col in [(c["R_px"], CYAN)] + [(cm.polar_r_px(c, row["value"]), RED if isbad("r", row["value"]) else MAGENTA)
                                                for row in r_rows]:
            d.line(list(zip(cx + rad * np.cos(scr), cy - rad * np.sin(scr))), fill=col)
        ph0 = np.radians(cm.polar_screen_deg(c, min(c["theta_range"])))     # r 측정점·라벨은 theta_range 시작 방향에 표시
        for row in r_rows:
            x, y = cx + row["px"] * np.cos(ph0), cy - row["px"] * np.sin(ph0)
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=GREEN)
            d.text((x + 3, y - 12), f"{row['value']:g}", fill=RED if isbad("r", row["value"]) else MAGENTA)
        for row in report.get("theta", {}).get("ticks", []):
            ph = np.radians(cm.polar_screen_deg(c, row["value"]))
            x, y = row["px"]
            col = RED if isbad("theta", row["value"]) else MAGENTA
            d.line([(cx, cy), (cx + c["R_px"] * np.cos(ph), cy - c["R_px"] * np.sin(ph))], fill=col)
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=GREEN)
            d.text((cx + (c["R_px"] + 4) * np.cos(ph), cy - (c["R_px"] + 4) * np.sin(ph)), f"{row['value']:g}", fill=col)
    d.text((6, 6), text or summary(report, flags), fill=RED if flags else GREEN)
    im.save(out_path)


def _print(report, flags, tol):
    print(f"[calib] type={report['type']} tol={tol} px")
    for name, tab in list(report.get("axes", {}).items()) + [(k, report[k]) for k in ("r", "theta") if k in report]:
        extra = ""
        if "map" in tab:
            extra = f" map={tab['map']['source']} a={tab['map']['a']:.4f} b={tab['map']['b']:.2f}"
        print(f"  [{name}] RMS {tab['rms_px']:.3f} px{extra}")
        for row in tab["ticks"]:
            loo = row.get("loo_px")
            loo_s = "" if loo is None else f"  LOO {loo:+.3f}"
            print(f"    {row['value']:>10g}  err {row['err_px']:+.3f} px{loo_s}")
    for n in report["notes"]:
        print(f"  note: {n}")
    for f in flags:
        print(f"WARN [{f['type']}] {f['msg']}")
    print(summary(report, flags))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("calib")
    ap.add_argument("--tol-px", type=float, default=1.0)
    ap.add_argument("--json", action="store_true", help="보고를 JSON 으로 출력")
    ap.add_argument("--overlay", nargs=2, metavar=("IMAGE", "OUT_PNG"), help="재투영 눈금 overlay png 를 쓴다")
    args = ap.parse_args()
    c = cm.load(args.calib)
    report, flags = check(c, args.tol_px)
    if args.overlay:
        draw_overlay(c, report, flags, *args.overlay)
    if args.json:
        print(json.dumps({"report": report, "flags": flags}, ensure_ascii=False, indent=1))
    else:
        _print(report, flags, args.tol_px)
    sys.exit(2 if not _errs(report) else 1 if flags else 0)


if __name__ == "__main__":
    main()
