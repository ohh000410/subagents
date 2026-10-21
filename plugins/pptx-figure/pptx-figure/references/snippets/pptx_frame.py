# [reference snippet — 2026-08-23] PPT figure 재현용 공유 프레임 + 3D 투영 역산기.
# 원본: 메인 세션이 직접 실행해 만든 것 (교정 216점, 학습 3.14 / 검증 3.50 px).
#
# ★ 이 파일을 **프로젝트에서 직접 import 하지 마라.** 작업 폴더로 복사한 뒤 import 한다
#   (에이전트는 자기가 소유한 파일만 import 한다 — 다른 에이전트들과 같은 규약).
# ★ 복사한 직후 **반드시 `python pptx_frame.py` 로 self-test 를 한 번 돌려라.**
#   렌더 1회(1~2초)로 오타·구버전 복사를 잡는다. 실패하면 그 상태로 작업하지 않는다.
"""공유 좌표계 + PPT 네이티브 3D 투영 모델.

왜 이게 필요한가
    여러 에이전트가 같은 그림의 요소를 나눠 그린다. 좌표계와 카메라 규약이 다르면
    합칠 때 층끼리 시점이 어긋나고, 합치기 전에는 발견되지 않는다.

진짜 상수는 넷뿐이다 (PowerPoint 3D 엔진의 성질. 도형·슬라이드·프로젝트 무관)
    회전 순서 ZXY · 부호 (RotX +, RotY -, RotZ +) · p0 1.1337 · p1 2.8498 · kr 0.99166
나머지(배율·중심)는 상수가 아니라 렌더 크기에서 계산한다.
"""
import copy
import os

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn, nsdecls
from pptx.oxml import parse_xml

# ── 그림별 좌표계 (호출자가 준 값으로 set_frame 호출) ──────────────────────
FX0, FY0, FX1, FY1 = 0.0, 0.0, 1000.0, 800.0     # 원본 figure 프레임 (원본 px)
WSL = 7.6                                         # 슬라이드 폭 (인치)
S = WSL / (FX1 - FX0)
HSL = (FY1 - FY0) * S
RENDER_W = round(FX1 - FX0)                       # 이 폭으로 export 하면 원본과 1:1


def set_frame(fx0, fy0, fx1, fy1, slide_w_in=7.6):
    """원본 figure 프레임(px)과 슬라이드 폭을 정한다. 다른 것보다 먼저 호출."""
    global FX0, FY0, FX1, FY1, WSL, S, HSL, RENDER_W
    FX0, FY0, FX1, FY1, WSL = fx0, fy0, fx1, fy1, slide_w_in
    S = WSL / (FX1 - FX0)
    HSL = (FY1 - FY0) * S
    RENDER_W = round(FX1 - FX0)


def emu(v):
    return int(Inches(v))


def X(p):
    return (p - FX0) * S


def Y(p):
    return (p - FY0) * S


def PT(px):
    """폰트·선굵기도 원본 px 에서 역산한다. 리터럴로 쓰지 말 것."""
    return px * S * 72.0


def rgb(s):
    return RGBColor.from_string(s)


# ── 슬라이드 / 도형 ────────────────────────────────────────────────────────
def new_slide(bg=None):
    prs = Presentation()
    prs.slide_width, prs.slide_height = emu(WSL), emu(HSL)
    return prs, add_page(prs, bg)


def add_page(prs, bg=None, title=None):
    """★ 배경은 기본 없음. 배경은 배경 요소의 몫이지 각 요소가 깔 것이 아니다.
    구멍이 진짜로 뚫렸는지도 배경이 없어야 눈으로 보인다."""
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    if title:
        tb = sl.shapes.add_textbox(emu(0.12), emu(0.06), emu(WSL - 0.24), emu(0.3))
        tb.text_frame.word_wrap = False
        tb.text_frame.text = title
        tb.text_frame.paragraphs[0].runs[0].font.size = Pt(13)
        tb.name = "page_title"
    if bg:
        r = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, emu(WSL), emu(HSL))
        r.fill.solid()
        r.fill.fore_color.rgb = rgb(bg)
        r.line.fill.background()
        r.shadow.inherit = False
        r.name = "background"
        sl.shapes._spTree.insert(2, r._element)
    return sl.shapes


def poly(sh, pts, fill, name=None):
    """평면 다각형. ★ 입체를 이걸로 흉내내지 마라 — 3D 서식으로 만든다."""
    q = [(X(x), Y(y)) for x, y in pts]
    b = sh.build_freeform(emu(q[0][0]), emu(q[0][1]), scale=1.0)
    b.add_line_segments([(emu(x), emu(y)) for x, y in q[1:]], close=True)
    s = b.convert_to_shape()
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(fill)
    s.line.fill.background()
    s.shadow.inherit = False
    if name:
        s.name = name
    return s


def _area(pts):
    n = len(pts)
    return sum(pts[i][0] * pts[(i + 1) % n][1]
               - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))


def poly_hole(sh, outer, holes, fill, name=None):
    """구멍이 실제로 뚫린 도형.

    ★ 구멍은 **같은 <a:path> 안의 서브패스**로, 바깥과 **반대 방향(winding)** 으로 넣는다.
      <a:path> 를 하나 더 만들면 구멍이 아니라 덧칠된다(실측).
    ★ 배경색 폴리곤으로 덮지 마라 — 배경을 바꾸면 그 자국만 남는다.
      검증: 배경색을 다른 색으로 바꿔 렌더해 구멍 안이 따라오는지 본다.
    """
    s = poly(sh, outer, fill, name)
    path = s._element.spPr.find(qn('a:custGeom')).find(qn('a:pathLst'))[0]
    ox, oy = int(s.left), int(s.top)
    out_dir = 1.0 if _area([(X(x), Y(y)) for x, y in outer]) > 0 else -1.0
    for hole in holes:
        q = [(emu(X(x)) - ox, emu(Y(y)) - oy) for x, y in hole]
        if (1.0 if _area(q) > 0 else -1.0) == out_dir:
            q = q[::-1]
        frags = ['<a:moveTo %s><a:pt x="%d" y="%d"/></a:moveTo>'
                 % (nsdecls('a'), q[0][0], q[0][1])]
        frags += ['<a:lnTo %s><a:pt x="%d" y="%d"/></a:lnTo>'
                  % (nsdecls('a'), p[0], p[1]) for p in q[1:]]
        frags.append('<a:close %s/>' % nsdecls('a'))
        for f in frags:
            path.append(parse_xml(f))
    return s


# ── PPT 3D 투영 모델 ───────────────────────────────────────────────────────
# 엔진 상수. 216점 교정 + 48가설(회전순서 6 x 축부호 8) 탐색으로 확정.
#   학습 3.14 px · 검증(20% 홀드아웃) 3.50 px · 잔차 중앙값 2.68 · 최대 8.29
# ★ 축이 통상 규약과 반대다: COM RotationX = 화면 세로축(yaw), RotationY = 가로축(pitch).
#   단일축 실측: RotationY -45 -> 세로비 0.710(=cos45) / RotationX 45 -> 가로비 0.709
#   이걸 모르고 순서·부호만 48가지 뒤지면 RMS 38 px 에서 안 내려간다.
M3D = dict(order="ZXY", signs=(1, -1, 1), p0=1.1337, p1=2.8498, kr=0.99166)
_D2R = 3.141592653589793 / 180.0


def _cam():
    """배율·중심은 상수가 아니라 렌더 크기에서 계산한다.
    export 폭만 2배로 바꿔 렌더하면 정규화 좌표가 동일(실측)."""
    k = M3D["kr"] * (RENDER_W / WSL)
    return k, k, RENDER_W / 2.0, RENDER_W * HSL / WSL / 2.0


def _rmat(rx, ry, rz):
    import numpy as np
    sg = M3D["signs"]
    a = {"X": ry * sg[1], "Y": rx * sg[0], "Z": rz * sg[2]}   # ★ X<->Y 뒤바뀜
    def mx(t):
        c, s = np.cos(t), np.sin(t)
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    def my(t):
        c, s = np.cos(t), np.sin(t)
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    def mz(t):
        c, s = np.cos(t), np.sin(t)
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    R = np.eye(3)
    for ax in M3D["order"]:
        R = R @ {"X": mx, "Y": my, "Z": mz}[ax](a[ax] * _D2R)
    return R


def project3d(rx, ry, rz, fov, W, H, depth_pt, cx_px, cy_px):
    """윗면 4점 + 밑면 4점을 화면 px 로. 돌출은 z = -Depth_pt/72 (뒤로)."""
    import numpy as np
    R = _rmat(rx, ry, rz)
    kx, ky, _, _ = _cam()
    D = M3D["p0"] * max(W, H) / np.tan(max(fov, 1e-3) * _D2R / 2) + M3D["p1"]
    out = []
    for z in (0.0, -depth_pt / 72.0):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            q = R @ np.array([sx * W / 2, sy * H / 2, z])
            w = max(1.0 - q[2] / D, 1e-6)
            out.append((cx_px + kx * q[0] / w, cy_px + ky * q[1] / w))
    return np.array(out)


def unproject3d(px, py, rx, ry, rz, fov, W, H, cx_px, cy_px):
    """화면 px -> 원본 사각형 평면(z=0) 좌표(인치). 구멍·홈 위치 역산용.
    검산: 바깥 사각형 네 점이 정확히 (±W/2, ±H/2) 로 떨어져야 한다."""
    import numpy as np
    R = _rmat(rx, ry, rz)
    kx, ky, _, _ = _cam()
    D = M3D["p0"] * max(W, H) / np.tan(max(fov, 1e-3) * _D2R / 2) + M3D["p1"]
    u, v = R[:, 0], R[:, 1]
    a, b = (px - cx_px) / kx, (py - cy_px) / ky
    A = np.array([[u[0] + a * u[2] / D, v[0] + a * v[2] / D],
                  [u[1] + b * u[2] / D, v[1] + b * v[2] / D]])
    return tuple(np.linalg.solve(A, np.array([a, b])))


# 실제 렌더 코너 오차 대 fov (요소 5개 실측):
#   fov  1.0 -> 2.1 px | 48.1 -> 4.0 | 54.0 -> 3.0 | 64.9 -> 5.0
#   fov 80.0 -> 14.2   | 83.5 -> 18.1 | 100.8 -> 55.3
# 65 와 80 사이에서 끊긴다. 캘리브 케이스에 80 이 있었지만 **80 은 이미 못 쓴다** —
# 교정 잔차가 낮은 것과 그 각도에서 정확한 것은 다른 얘기다. 검증된 쪽에 붙여 자른다.
FOV_MAX = 70.0
PLAN_MAX_RATIO = 4.0        # plan(W,H) 이 렌더 span 의 몇 배까지 정상인가 — solve_3d 참고


def solve_3d(top4, thickness_px, x0=None, square=False):
    """★ 각도를 렌더로 더듬지 마라. 목표를 넣으면 계산으로 나온다.

    top4          윗면 꼭짓점 4개 (원본 px = 렌더 px)
    thickness_px  옆면 세로 두께 (px)
    square        True 면 H=W 로 묶는다. ★ 실물이 정사각이면 반드시 켜라 —
                  자유 피팅은 측정 노이즈를 **형상 왜곡으로 흡수**한다(RMS 0.00 이 나와도
                  W:H 가 0.68 로 찌그러진다). 제약을 걸면 RMS 는 올라가지만 형상이 맞다.
                  검증: 바깥만 정사각으로 묶었더니 **구멍이 저절로 정사각이 됐다**
                  (변 0.331/0.499 -> 0.382/0.403).
    반환          RotationX/Y/Z, FieldOfView, W, H(인치), Depth(pt), cx, cy(인치), rms

    ★★ rms 를 믿기 전에 FieldOfView 가 캘리브 유효 범위(<= 70도) 안인지 봐라.
       모델은 fov 30/55/80 에서만 교정됐다. fov 가 70 위로 나가면 원근 나눗셈
       1/(1-z'/D) 가 폭주해서 **rms 와 실제 렌더 오차의 상관이 뒤집힌다.**
       실측: 같은 요소의 세 해 — fov 64.9 는 rms 0.00 / 렌더 3.7 px,
       fov 83.5 는 rms 3.56 / 렌더 10.8 px, fov 100.8 은 **rms 0.00 / 렌더 32 px**.
       모델이 완벽하다고 한 해가 실제로는 가장 나빴다.
       ★ 그래서 fov > 70 이면 이 함수는 **예외를 던진다**. 잔차를 낮추는 게 아니라
         조건을 하나 더 넣어라 (예: 이웃 요소와 카메라를 맞춘다).

    ★★★ fov 가 **낮은** 쪽에도 함정이 있다 (2026-08-28, Nighttime 소자에서 실측).
       "정사영 극한이라 안전하다"고 여기 적혀 있었는데 **틀렸다.**
       윗면 앞/뒤 모서리 중심의 shear 를 0.8 -> 1.6 px 로 1 px 도 안 움직였더니:
           shear  0.8   ratio  1.00   fov 8.05   rms 0.0004   H  1.35 in
           shear  1.6   ratio 17.08   fov 7.16   rms 0.0000   H 23.11 in   <- 절벽
           shear  6.35  ratio 33.93   fov 7.14   rms 0.0000   H 45.89 in
       옵티마이저가 **RotY -87 도의 스치는 시선 + 거대한 plan** 이라는 축퇴 가지로 넘어간다.
       판별이 안 되는 이유가 셋이다:
         · rms 는 양쪽 다 0 이다 (윗면 4점을 똑같이 재현한다)
         · fov 는 오히려 **내려가서** FOV_MAX 가드에 안 걸린다
         · project3d 로 8점 bbox 를 찍어도 **양쪽 다 558.5 px** 로 같다
       그런데 실제 PowerPoint 렌더는 27% 크다 — 이 영역에서는 투영 모델 자체가 안 맞는다.
       유일한 신호는 **plan 크기가 렌더 크기에 비해 터무니없이 크다**는 것이라서,
       아래 PLAN_MAX_RATIO 가드가 그걸 잡는다. 걸리면 shear 를 재측정하거나
       square=True 로 묶어라.

       ★ **허용 shear 구간은 quad 마다 다르다. 남의 구간을 옮겨 쓰지 마라.**
       같은 그림의 두 패널, 같은 물체인데:
           Nighttime (뒤 528.7 / 앞 558.6 / 깊이 27.3)   0.4~1.6 통과, 1.0 만 폭주
           Daytime   (뒤 529.0 / 앞 555.1 / 깊이 27.4)   0.4~0.8 통과, 1.0 부터 차단
       앞면 폭 3.5 px 차이로 갈린다. **요소마다 훑어서 통과 구간을 직접 찾아라.**
       (이 가드는 실제로 값을 했다 — Daytime 소자의 앞모서리를 3.4 px 고치자
        rms 0.0000 · fov 정상인 채로 ratio 13 짜리 해가 나왔고, 가드가 없었으면
        그대로 저장돼 27% 큰 렌더가 됐을 것이다.)
    """
    import numpy as np
    from scipy.optimize import least_squares
    T = np.array(top4, float)
    ctr, span = T.mean(0), float(np.hypot(*(T.max(0) - T.min(0))))
    ppi = RENDER_W / WSL
    if x0 is None:
        x0 = [60.0, -35.0, -55.0, 45.0, span / ppi, span / ppi * 0.6,
              max(thickness_px, 1.0) / 2.3, ctr[0], ctr[1]]
        if square:
            x0 = x0[:5] + x0[6:]

    def unpack(v):
        if square:
            rx, ry, rz, fov, W, dep, cx, cy = v
            return rx, ry, rz, fov, W, W, dep, cx, cy
        return v

    def res(v):
        rx, ry, rz, fov, W, H, dep, cx, cy = unpack(v)
        q = project3d(rx, ry, rz, fov, abs(W), abs(H), abs(dep), cx, cy)
        top, bot = q[:4], q[4:]
        best = None
        for m in (T, T[::-1]):                 # 꼭짓점 대응은 시작점·방향을 모른다
            for k in range(4):
                e = np.roll(m, k, axis=0) - top
                s = float((e ** 2).sum())
                if best is None or s < best[0]:
                    best = (s, e.ravel())
        th = float(np.abs(bot[:, 1] - top[:, 1]).mean())
        return np.concatenate([best[1], [(th - thickness_px) * 3.0]])

    s = least_squares(res, x0, method="lm", max_nfev=20000)
    rx, ry, rz, fov, W, H, dep, cx, cy = unpack(s.x)
    wrap = lambda a: float(a % 360 - 360 if a % 360 > 180 else a % 360)
    if abs(unpack(s.x)[3]) > FOV_MAX:
        raise ValueError(
            "solve_3d: fov %.1f 도가 캘리브 범위(<= %.0f)를 벗어났다. rms %.2f 는 "
            "믿을 수 없다 — 이 영역에서는 잔차가 낮을수록 렌더가 더 틀린다. "
            "꼭짓점 하나가 추정값이면 그게 원인이다. 조건을 하나 더 넣어라: "
            "이웃 요소의 RotX/Y/Z 에 맞추거나, 추정 꼭짓점을 자유변수로 두고 "
            "실측 꼭짓점만 맞춰라." % (abs(unpack(s.x)[3]), FOV_MAX,
                float(np.sqrt((s.fun[:8] ** 2).mean()))))
    if max(abs(W), abs(H)) > PLAN_MAX_RATIO * span / ppi:
        raise ValueError(
            "solve_3d: plan 이 %.2f x %.2f in 인데 렌더 span 은 %.2f in 뿐이다 (%.0f 배). "
            "스치는 시선 축퇴 가지에 빠졌다 — **rms %.4f 는 판별력이 없다**(양쪽 가지 다 0), "
            "fov 는 오히려 내려가서 FOV_MAX 도 안 걸리고, project3d 의 8점 bbox 도 정상으로 "
            "나온다. 실제 렌더만 20~30%% 크게 나온다. 원인은 대개 윗면 앞/뒤 모서리 중심의 "
            "shear 이고, 1 px 차이로 넘어간다. shear 를 다시 재거나 square=True 로 묶어라."
            % (abs(W), abs(H), span / ppi, max(abs(W), abs(H)) / (span / ppi),
               float(np.sqrt((s.fun[:8] ** 2).mean()))))
    return dict(RotationX=wrap(rx), RotationY=wrap(ry), RotationZ=wrap(rz),
                FieldOfView=float(min(max(fov, 1.0), 120.0)),
                W=float(abs(W)), H=float(abs(H)), Depth=float(abs(dep)),
                cx=float(cx / ppi), cy=float(cy / ppi),
                rms=float(np.sqrt((s.fun[:8] ** 2).mean())))


# ── COM 후처리 (python-pptx 로는 못 하는 부분) ─────────────────────────────
def com_post(path, ops):
    """ops = [{"slide":1, "merge":(names, cmd, primary, new_name)},
              {"slide":1, "three_d":(name, {...})}]

    ★ PowerPoint 를 한 번만 연다. 연산마다 열고 닫으면 건당 10초가 든다.
    ★ 병합 -> 3D 순서. 반대로 하면 primary 쪽 3D 만 남는다.
    ★ MsoMergeCmd: 1 Union · 2 Combine · 3 Intersect · 4 Subtract · 5 Fragment
    """
    import win32com.client
    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = app.Presentations.Open(os.path.abspath(path), WithWindow=False)
    try:
        for op in ops:
            sl = pres.Slides(op["slide"])
            if "merge" in op:
                names, cmd, primary, newname = op["merge"]
                before = {sl.Shapes(i + 1).Name for i in range(sl.Shapes.Count)}
                sl.Shapes.Range(list(names)).MergeShapes(cmd, sl.Shapes(primary))
                after = {sl.Shapes(i + 1).Name for i in range(sl.Shapes.Count)}
                new = sorted(after - before)
                if not new:      # ★ Subtract 에서 primary 를 거꾸로 주면 둘 다 사라진다
                    raise RuntimeError("병합 결과 없음: %s cmd=%s primary=%s"
                                       % (names, cmd, primary))
                sl.Shapes(new[0]).Name = newname   # ★ 병합하면 이름이 날아간다
            if "group" in op:
                # 그룹은 3D 를 **덮어쓰지 않는다** — 각 도형이 자기 3D 를 유지한 채
                # 한 단위로 움직인다. 단차처럼 두께가 다른 슬래브를 겹칠 때 쓴다.
                # ★ 반드시 각 도형의 3D 를 먼저 걸고 마지막에 그룹한다.
                names, newname = op["group"]
                g = sl.Shapes.Range(list(names)).Group()
                g.Name = newname
            if "three_d" in op:
                name, cfg = op["three_d"]
                t = sl.Shapes(name).ThreeD
                t.Visible = True                   # ★ 먼저 켜야 나머지가 먹는다
                # ★ PresetCamera 는 **항상 먼저**. cfg 를 순서대로 돌리면
                #   RotationX/Y/Z 뒤에 온 SetPresetCamera 가 그 회전을 프리셋 값으로
                #   **조용히 되돌린다** — 예외도 경고도 없고 육안으로만 잡힌다.
                #   호출자가 dict 순서를 기억하게 두지 않고 여기서 강제한다.
                #   ★★ 회전은 **맨 마지막**이다. PresetCamera 뿐 아니라
                #   PresetMaterial / PresetLighting / Depth 를 회전 뒤에 설정해도
                #   RotationX/Y/Z 가 조용히 0 으로 날아간다. 그때 PowerPoint 기본
                #   oblique 로 렌더돼 «상자처럼» 보이므로 육안으로도 안 잡힌다.
                #   (2026-09-05 발견: 카메라 프리셋 10종을 넣었는데 6칸이 동일하게
                #    렌더돼서 드러났다.)
                if "PresetCamera" in cfg:
                    t.SetPresetCamera(cfg["PresetCamera"])      # 48 = perspectiveFront
                ROT = ("RotationX", "RotationY", "RotationZ")
                # ★★★ 중간 키도 순서가 있다. Depth / ExtrusionColor 를
                #   PresetMaterial / PresetLighting «뒤» 에 두면 **카메라가 정사영으로
                #   되돌아간다** (fov 105->45, Perspective -1->0, PresetCamera 50->3).
                #   회전은 살아남아 아래 회전 되읽기를 **통과하므로 조용히 깨진다.**
                #   호출자 dict 순서에 맡기지 말고 여기서 강제한다.
                #   (2026-09-06 발견: 원근 전환에서 옆면 기울기가 상자 크기와 무관하게
                #    -0.278 로 고정돼 드러났다. A/B 이분법으로 확정.)
                ORDER = ("Depth", "ExtrusionColor", "FieldOfView",
                         "PresetMaterial", "PresetLighting",
                         "PresetLightingDirection", "ContourWidth", "ContourColor")
                keys = ([k for k in ORDER if k in cfg]
                        + [k for k in cfg if k not in ORDER
                           and k != "PresetCamera" and k not in ROT])
                for k in keys:
                    if k == "ExtrusionColor":
                        t.ExtrusionColor.RGB = cfg[k]   # ★ COM RGB 는 BGR 순
                    elif k == "ContourColor":
                        t.ContourColor.RGB = cfg[k]
                    else:
                        setattr(t, k, cfg[k])
                for k in ROT:                      # ★ 회전은 반드시 맨 마지막
                    if k in cfg:
                        setattr(t, k, cfg[k])      # RotationX/Y 는 -90~90
                # 되읽기로 검증 — 날아갔으면 조용히 넘어가지 말고 터뜨린다
                for k in ROT:
                    if k in cfg and abs(getattr(t, k) - cfg[k]) > 0.5:
                        raise RuntimeError(
                            "3D 회전이 적용되지 않았다: %s %s=%s (실제 %s)"
                            % (name, k, cfg[k], getattr(t, k)))
                # ★ 회전만 보면 위 순서 사고를 못 잡는다. 원근을 따로 되읽는다.
                #   (Group() 뒤에는 prst 가 재작성되므로 반드시 그룹 «전» 에 잰다.)
                if "FieldOfView" in cfg and abs(t.FieldOfView - cfg["FieldOfView"]) > 0.5:
                    raise RuntimeError(
                        "원근이 정사영으로 되돌아갔다 (cfg 키 순서 의심): "
                        "%s FieldOfView=%s (실제 %s, Perspective=%s)"
                        % (name, cfg["FieldOfView"], t.FieldOfView, t.Perspective))
        # ★ 같은 경로로 SaveAs 하면 PowerPoint 가 예외 없이 «아무것도 쓰지 않는다».
        #   COM 되읽기는 메모리 상태를 보므로 통과해 버려서 사고를 못 잡는다.
        #   반드시 Save() 를 쓰고 Saved 플래그로 확인한다.
        #   (2026-09-05 발견: 이 줄 때문에 3D·병합·그룹이 디스크에 안 남고,
        #    self-test 가 «꼭짓점 RMS 282 px» 로 실패했다. 고친 뒤 RMS 2.87 px.)
        pres.Save()
        if not pres.Saved:
            raise RuntimeError(f"PowerPoint did not save: {path} (Saved=0)")
    finally:
        pres.Close()
        app.Quit()
    return path


def set_lightrig(path, rig="flat", direction="t", pages=None):
    """★ 기본 threePt 는 돌출색을 무시하고 옆면을 검게 태운다.
    ★ **승자는 카메라마다 다르다.** flat 은 edge-on 시점에서 안쪽 벽을 태운다
      (실측 45 dE). 요소마다 rig x dir 를 프로브해 면적가중 dE 로 고른다.
    ★ **그룹 안까지 들어간다** — sl.shapes 는 그룹을 하나로 주므로 XML 을 전수 검색한다.
    ★ pages: 1-based 페이지 집합. 주지 않으면 파일 전체 — 남이 맞춰놓은 조명까지
      덮어쓴다. 여러 요소를 모아 담은 파일에서는 **반드시 자기 페이지만 지정**한다."""
    prs = Presentation(path)
    n = 0
    for i, sl in enumerate(prs.slides, start=1):
        if pages is not None and i not in pages:
            continue

        for lr in sl.shapes._spTree.iter(qn("a:lightRig")):
            lr.set("rig", rig)
            lr.set("dir", direction)
            n += 1
    prs.save(path)
    return n


def export_png(path, dst, slide=1, width=None):
    """★ 육안 확인은 width=1350 으로 뽑아라 — Read 토큰이 1/16 이다.
    측정(코너·색·recall)은 기본(원본 1:1 폭). 두 용도를 한 렌더로 겸하지 마라."""
    import win32com.client
    w = width or RENDER_W
    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = app.Presentations.Open(os.path.abspath(path), WithWindow=False)
    try:
        if os.path.exists(dst):
            os.remove(dst)
        pres.Slides(slide).Export(os.path.abspath(dst), "PNG", w,
                                  int(round(w * HSL / WSL)))
    finally:
        pres.Close()
        app.Quit()
    return dst


# ── 측정 공통 (요소마다 measure_*.py 에 다시 쓰지 않는다) ──────────────────
def load_rgb(path):
    """PNG -> HxWx3 int 배열."""
    import numpy as np
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    return np.asarray(Image.open(path).convert("RGB")).astype(int)


def blobs(mask, min_px=300):
    """True 마스크의 연결요소를 큰 순으로 [(px, x0, x1, y0, y1)].
    '원본에 있는데 재현에 없는 것' 검사의 기본 도구다."""
    import numpy as np
    from scipy.ndimage import label
    lb, _ = label(mask)
    sz = np.bincount(lb.ravel())
    sz[0] = 0
    out = []
    for i in np.argsort(sz)[::-1]:
        if sz[i] < min_px:
            break
        ys, xs = np.where(lb == i)
        out.append((int(sz[i]), int(xs.min()), int(xs.max()),
                    int(ys.min()), int(ys.max())))
    return out


def mask_compare(mo, mr):
    """원본 마스크 vs 재현 마스크 -> dict(recall, iou, bbox 차, 원본에만 %).
    ★ 비교 조건(가림 합성·창 크기)은 호출자가 마스크로 먼저 맞춘다."""
    import numpy as np
    yo, xo = np.where(mo)
    yr, xr = np.where(mr)
    inter = (mo & mr).sum()
    return dict(recall=float(inter / max(mo.sum(), 1)),
                iou=float(inter / max((mo | mr).sum(), 1)),
                only_orig_pct=float(100.0 * (mo & ~mr).sum() / max(mo.sum(), 1)),
                bbox_d=(int(xr.min() - xo.min()), int(xr.max() - xo.max()),
                        int(yr.min() - yo.min()), int(yr.max() - yo.max()))
                       if len(xr) and len(xo) else None)


def diff_stats(a, b, mask):
    """마스크 안 채널별 평균|Δ| 와 |Δ|max 백분위(50/90/99).
    ★ 방향성 있는 모델(방사형·선형)은 이걸 통째로 쓰지 말고 축별로 나눠 재라."""
    import numpy as np
    d = np.abs(a - b)[mask]
    return (tuple(float(v) for v in d.mean(0)),
            tuple(float(np.percentile(d.max(1), q)) for q in (50, 90, 99)))


def radial_profile(img, cx, cy, rx, ry, az_deg, ts, skip_fn=None):
    """방위각 하나를 따라 t 별 RGB. ★ 방사형 검증은 방위각 3개 이상으로 —
    전 방위 평균은 등고선이 틀려도 안 잡는다. skip_fn(rgb)->True 면 아트워크 건너뜀."""
    import numpy as np
    a = np.deg2rad(az_deg)
    out = []
    for t in ts:
        x, y = int(cx + t * rx * np.cos(a)), int(cy + t * ry * np.sin(a))
        if not (0 <= y < img.shape[0] and 0 <= x < img.shape[1]):
            out.append(None)
            continue
        v = img[y, x]
        out.append(None if (skip_fn and skip_fn(v)) else tuple(int(c) for c in v))
    return out


def guarded_extent(mask, min_run=16):
    """행별 (min_x, max_x). ★ 연속 min_run 미만 조각은 무시한다 — 이웃 요소
    사이의 안티에일리어싱 블렌드가 요소로 잡히는 것을 막는다(실측 -232px 사고)."""
    import numpy as np
    res = {}
    for y in range(mask.shape[0]):
        row = mask[y]
        if not row.any():
            continue
        d = np.diff(np.concatenate(([0], row.astype(int), [0])))
        starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
        runs = [(s, e) for s, e in zip(starts, ends) if e - s >= min_run]
        if runs:
            res[y] = (int(runs[0][0]), int(runs[-1][1] - 1))
    return res


# ── 검증 ──────────────────────────────────────────────────────────────────
def corners(png, mask_fn):
    """볼록 사각형의 네 꼭짓점.

    ★ 볼록껍질을 만든 뒤 **면적 손실이 가장 작은 꼭짓점부터 지워** 4개로 줄인다.
      ±x±y 극점이나 꺾임각 상위 4개는 얇은 사각형에서 두 점이 붙어 실패한다(둘 다 실측).
    mask_fn(a) -> bool 배열 (a 는 HxWx3 int 배열)
    """
    import numpy as np
    from PIL import Image
    from scipy.spatial import ConvexHull
    a = np.asarray(Image.open(png).convert("RGB")).astype(int)
    m = mask_fn(a)
    if m.sum() < 200:
        return None
    ys, xs = np.where(m)
    h = [tuple(p) for p in np.stack([xs, ys], 1).astype(float)[
        ConvexHull(np.stack([xs, ys], 1).astype(float)).vertices]]
    while len(h) > 4:
        n = len(h)
        loss = [abs((h[i][0] - h[i - 1][0]) * (h[(i + 1) % n][1] - h[i - 1][1])
                    - (h[(i + 1) % n][0] - h[i - 1][0]) * (h[i][1] - h[i - 1][1]))
                for i in range(n)]
        h.pop(int(np.argmin(loss)))
    return [(float(x), float(y)) for x, y in h]


def corner_rms(got4, target4):
    """대응이 회전·반전 8가지라 전부 맞춰보고 최소를 취한다."""
    import numpy as np
    g, T = np.array(got4, float), np.array(target4, float)
    best = None
    for m in (T, T[::-1]):
        for k in range(4):
            e = np.roll(m, k, axis=0) - g
            v = float(np.sqrt((e ** 2).sum(1).mean()))
            if best is None or v < best:
                best = v
    return best


def selftest(tmp="_pptx_frame_selftest"):
    """★ 복사 직후 반드시 한 번 돌린다. 렌더 1회로 오타·구버전 복사를 잡는다."""
    import numpy as np
    # 측정 헬퍼 무결성 (COM 불필요, ~0초)
    _m = np.zeros((40, 60), bool)
    _m[5:15, 5:30] = True
    _m[30:34, 40:44] = True                      # min_px 미만 -> 무시돼야
    assert blobs(_m, min_px=50) == [(250, 5, 29, 5, 14)], "blobs 손상"
    _r = np.zeros((40, 60), bool)
    _r[5:15, 7:32] = True
    _c = mask_compare(_m, _r)
    assert abs(_c["recall"] - 230.0 / 266.0) < 1e-6, "mask_compare 손상"
    _g = guarded_extent(_m[5:6], min_run=16)
    assert _g == {0: (5, 29)}, "guarded_extent 손상"
    set_frame(194, 60, 194 + 1239, 60 + 1030, 7.6)
    tgt = [(631, 329), (965, 412), (623, 509), (258, 404)]
    r = solve_3d(tgt, 24)
    prs, sh = new_slide(None)
    s = sh.add_shape(MSO_SHAPE.RECTANGLE,
                     emu(r["cx"] - r["W"] / 2), emu(r["cy"] - r["H"] / 2),
                     emu(r["W"]), emu(r["H"]))
    s.fill.solid()
    s.fill.fore_color.rgb = rgb("FF0000")
    s.line.fill.background()
    s.shadow.inherit = False
    s.name = "t"
    prs.save(tmp + ".pptx")
    com_post(tmp + ".pptx", [{"slide": 1, "three_d": ("t", {
        "PresetCamera": 48, "RotationX": r["RotationX"], "RotationY": r["RotationY"],
        "RotationZ": r["RotationZ"], "FieldOfView": r["FieldOfView"], "Depth": 0})}])
    export_png(tmp + ".pptx", tmp + ".png")
    got = corners(tmp + ".png",
                  lambda a: (a[..., 0] > 150) & (a[..., 1] < 110) & (a[..., 2] < 110))
    rms = corner_rms(got, tgt)
    for f in (tmp + ".pptx", tmp + ".png"):
        if os.path.exists(f):
            os.remove(f)
    if got is None or rms > 5.0:
        raise SystemExit("self-test 실패: 꼭짓점 RMS %.2f px (기준 5.0). "
                         "상수를 잘못 베꼈거나 구버전이다." % (rms if got else -1))
    print("self-test OK — 꼭짓점 RMS %.2f px" % rms)
    return rms


if __name__ == "__main__":
    selftest()
