# 회전체 도면 — SIDE / END VIEW

회전체 = SIDE + END + ISO 3뷰 (Top = Side 중복).

## SIDE VIEW 치수 (kRightViewOrientation)

RIGHT view: shaft Z축 = X 방향, Z=0 이 오른쪽, Z=L 이 왼쪽 (미러). 수직 curve 0개 — 지름은 END view 에서.

```python
curves = list(vSide.GetDrawingCurves(None))
valid  = [(c, get_bounds(c)) for c in curves if get_bounds(c)]
horiz  = [(c,b) for c,b in valid if (b[3]-b[1])<0.01 and (b[2]-b[0])>0.02]
x_vals = sorted(set([round(b[0],2) for c,b in horiz] + [round(b[2],2) for c,b in horiz]))

def find_seg(xl, xr, tol=0.08):
    cands = [(c,b) for c,b in horiz if abs(b[0]-xl)<tol and abs(b[2]-xr)<tol]
    return max(cands, key=lambda x: x[1][3]) if cands else None  # top line

def add_hdim(c1,b1,x1, c2,b2,x2, ty, label):
    gi1 = sheet.CreateGeometryIntent(c1, tg.CreatePoint2d(x1, (b1[1]+b1[3])/2))
    gi2 = sheet.CreateGeometryIntent(c2, tg.CreatePoint2d(x2, (b2[1]+b2[3])/2))
    gd.AddLinear(tg.CreatePoint2d((x1+x2)/2, ty), gi1, gi2, kHorizontalDimensionType)
```

치수선 ty 스태킹 (짧은 구간 안쪽, 전체 span 바깥):
```
ty_base = cy + vH/2 + 1.2
ty2 = ty_base + 0.9;  ty3 = ty2 + 0.9;  ty4 = min(ty3 + 0.9, 27.5)
```

전체 span = 2-curve (왼쪽 끝 curve + 오른쪽 끝 curve 각각 GI). 같은 curve 양 끝점 → driven(핑크). 단차 없는 단일 원통은 실루엣 선이 하나라 축 양 끝단의 edge-on 원(별개 curve) 을 앵커로 쓴다 (memory `drawing_dimensioning_pitfalls.md` — Same-curve driven dimension).

## END VIEW 지름 치수 (kFrontViewOrientation)

동심원. `StartPoint`/`EndPoint`/`MidPoint` = None, `Curve2dEvaluator.StartParam` AttributeError → 인덱스 기반만.

```python
end_curves = list(vEnd.GetDrawingCurves(None))   # 순서 INNERMOST → OUTERMOST
expected_r_cm = [cm(r_inner*scale), cm(r_mid*scale), cm(r_outer*scale)]
r_text = vW_end / 2 + 0.5        # 텍스트 = 중심에서 고정 거리, 모든 원 바깥. leader_ext 방식 금지
angles_deg = [25, 45, 65]        # inner 얕게, outer 가파르게

for i, c in enumerate(end_curves):
    if i >= len(expected_r_cm): break
    r, ang = expected_r_cm[i], math.radians(angles_deg[i])
    px, py = end_cx + r*math.cos(ang), end_cy + r*math.sin(ang)
    tx = min(end_cx + r_text*math.cos(ang), W - 1.5); ty = end_cy + r_text*math.sin(ang)
    gd.AddDiameter(tg.CreatePoint2d(tx, ty), sheet.CreateGeometryIntent(c, tg.CreatePoint2d(px, py)))
```

`GetDrawingCurves` 는 단 수보다 많은 curve 를 반환할 수 있다 → `[:N_STEPS]` 슬라이싱. 초과 curve 에 Ø 를 붙이면 유령 치수.

## 중심마크

```python
gi_center = sheet.CreateGeometryIntent(end_curves[-1], tg.CreatePoint2d(END_CX, END_CY))
sheet.Centermarks.Add(gi_center)   # dd.DrawingAnnotations.CenterMarkSymbols.Add 는 실패
```

## 중심선 — late binding 필수

`sheet.Centerlines.AddBisector()`/`.Add()` 직접 호출 → `DISP_E_MEMBERNOTFOUND` (gen_py DISPID 불일치).

```python
from win32com.client import Dispatch as LateDispatch
top_segs_s = sorted([(c,b) for c,b in valid_side if abs(b[3]-b[1])<0.01 and abs(b[2]-b[0])>1.0], key=lambda x: x[1][1])
top_ln, bot_ln = top_segs_s[-1], top_segs_s[0]
mid_x = (x_vals[0] + x_vals[3]) / 2
gi_top = sheet.CreateGeometryIntent(top_ln[0], tg.CreatePoint2d(mid_x, top_ln[1][1]))
gi_bot = sheet.CreateGeometryIntent(bot_ln[0], tg.CreatePoint2d(mid_x, bot_ln[1][1]))
LateDispatch(sheet.Centerlines._oleobj_).AddBisector(gi_top, gi_bot)
```

실패 경로: `Centerlines.Add(gi1, gi2)` MEMBERNOTFOUND / `_oleobj_.InvokeTypes(117479426, …)` MEMBERNOTFOUND / `ObjectCollection` + `Add(oc)` silent fail / `SetAutomatedCenterlineSettings()` 출력 없음 / `Sketches.Add()` 선분 DISP_E_EXCEPTION.

## 참조치수 괄호 표기

`Driven` 프로퍼티 없음. `DimensionText.Override` 없음. `FormattedText` 는 값 뒤에 append.

```python
total_dim.HideValue = True
total_dim.Text.FormattedText = "(80.00)"   # HideValue 없이 FormattedText 만 → "80.00(80.00)"
```
