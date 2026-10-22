"""
캘리브 JSON 저장·로더 + 값<->픽셀 변환. 추출 스크립트 / check_calibration.py / check_extraction.py 공용.

calib.json = 캘리브 산출물 (agents/plot-digitizer.md 절차 3). 눈금 측정·변환식 확정 시점에 `save` 로 쓰고,
추출 스크립트는 `load` 후 `from_px`(픽셀 -> 값) 로 변환한다. 검사 도구는 같은 파일의 `to_px` 로 재투영하므로
추출과 검사가 같은 변환을 쓴다. 사용:
    sys.path.insert(0, os.path.expanduser("<PLUGIN_ROOT>/plot-digitizer/tools"))
    import calib_model as cm
    cm.save("calib.json", calib)                  # 캘리브 확정 직후
    c = cm.load("calib.json")                     # 추출 스크립트
    x, y = cm.from_px(c, col, row)                # cartesian: (x, y) / polar: (theta, r)

픽셀 좌표 = 원본 전체 이미지 기준 (col 오른쪽 +, row 아래 +). box 로 자른 로컬 좌표를 넣지 않는다.

cartesian (선형 축만):
{
  "type": "cartesian",
  "box_px":  {"left": 101.5, "right": 1650.5, "top": 80.5, "bottom": 1020.5},  # 테두리 선 중심
  "x_ticks": [[4, 310.2], [6, 532.0], ...],      # [눈금 값, 눈금 픽셀(col)]
  "y_ticks": [[0.2, 832.4], ...],                # [눈금 값, 눈금 픽셀(row)]
  "x_map":  {"a": 110.9, "b": -133.4},           # 선택. 추출에 실제로 쓴 px = a*v + b
  "y_map":  {"a": -940.0, "b": 1020.5},          #   없으면 눈금 LSQ 직선이 추출 변환이다
  "tick_len_px": 15,                             # 선택. 실측한 안쪽 눈금 돌출 길이 (추정 금지)
  "tick_sides": ["left", "bottom", "right", "top"]  # tick_len_px 와 함께. 안쪽 눈금이 있는 변
}

polar (반원·전원 공통, radial 선형):
{
  "type": "polar",
  "center_px": [cx, cy],
  "R_px": 660.5,                 # r_max 에 해당하는 반경(px) — 추출에 실제로 쓴 값
  "r_min": 0.0, "r_max": 1.0,    # r_px = R_px * (v - r_min) / (r_max - r_min)
  "theta0_deg": 90, "theta_dir": -1,  # 화면 각도(+x 기준 반시계, y 위) = theta0_deg + theta_dir * theta
  "theta_range": [-90, 90],
  "r_ticks": [[0.2, 132.1], ...],          # [격자 원 값, 측정 반경 px]
  "theta_ticks": [[30, [x, y]], ...]       # 선택. [각도 값, 그 각도 격자선 위 측정 점 px]
}
"""
import json

import numpy as np


def load(path):
    with open(path, encoding="utf-8") as f:
        c = json.load(f)
    if c["type"] not in ("cartesian", "polar"):
        raise ValueError(f"calib type must be 'cartesian' or 'polar', got {c['type']!r}")
    return c


def save(path, c):
    """calib dict -> calib.json. 검증은 load 와 같은 type 확인만."""
    if c["type"] not in ("cartesian", "polar"):
        raise ValueError(f"calib type must be 'cartesian' or 'polar', got {c['type']!r}")

    def conv(o):                       # 측정 코드가 넘기는 numpy 값
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, np.generic):
            return o.item()
        raise TypeError(type(o))

    with open(path, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=1, default=conv)


def lsq_line(values, px):
    """px = a*v + b 최소제곱."""
    v = np.asarray(values, float)
    A = np.vstack([v, np.ones_like(v)]).T
    (a, b), *_ = np.linalg.lstsq(A, np.asarray(px, float), rcond=None)
    return float(a), float(b)


def axis_map(c, axis):
    """cartesian 축 axis('x'|'y') 의 추출 변환 (a, b, 출처)."""
    key = f"{axis}_map"
    if key in c:
        return float(c[key]["a"]), float(c[key]["b"]), "given"
    t = np.asarray(c[f"{axis}_ticks"], float)
    a, b = lsq_line(t[:, 0], t[:, 1])
    return a, b, "tick_lsq"


def cart_to_px(c, x, y):
    ax, bx, _ = axis_map(c, "x")
    ay, by, _ = axis_map(c, "y")
    return ax * np.asarray(x, float) + bx, ay * np.asarray(y, float) + by


def polar_r_px(c, v):
    return c["R_px"] * (np.asarray(v, float) - c["r_min"]) / (c["r_max"] - c["r_min"])


def polar_screen_deg(c, theta):
    return c["theta0_deg"] + c["theta_dir"] * np.asarray(theta, float)


def cart_from_px(c, col, row):
    """cart_to_px 의 역변환 -> (x, y)."""
    ax, bx, _ = axis_map(c, "x")
    ay, by, _ = axis_map(c, "y")
    return (np.asarray(col, float) - bx) / ax, (np.asarray(row, float) - by) / ay


def polar_to_px(c, theta, r):
    """(theta, r) 값 -> 원본 이미지 (col, row)."""
    cx, cy = c["center_px"]
    rad = polar_r_px(c, r)
    phi = np.radians(polar_screen_deg(c, theta))
    return cx + rad * np.cos(phi), cy - rad * np.sin(phi)


def polar_from_px(c, col, row):
    """polar_to_px 의 역변환 -> (theta, r). theta 는 theta_range 가운데 ±180° 안으로 접는다 —
    시작값에서 접으면 반원 -90° 끝 바로 아래 점이 +270° 로 튀어 엉뚱한 빈 구간이 생겼다(2026-10-22 교차 검토).
    전원(0~360)은 예전과 같다."""
    cx, cy = c["center_px"]
    dx, dy = np.asarray(col, float) - cx, cy - np.asarray(row, float)
    r = c["r_min"] + np.hypot(dx, dy) / c["R_px"] * (c["r_max"] - c["r_min"])
    mid = 0.5 * sum(c["theta_range"])
    raw = c["theta_dir"] * (np.degrees(np.arctan2(dy, dx)) - c["theta0_deg"])
    theta = mid + (raw - mid + 180.0) % 360.0 - 180.0
    return theta, r


def to_px(c, a, b):
    """값 -> 픽셀 (col, row). cartesian (x, y) / polar (theta, r)."""
    return cart_to_px(c, a, b) if c["type"] == "cartesian" else polar_to_px(c, a, b)


def from_px(c, col, row):
    """픽셀 -> 값. cartesian (x, y) / polar (theta, r)."""
    return cart_from_px(c, col, row) if c["type"] == "cartesian" else polar_from_px(c, col, row)
