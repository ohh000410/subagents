# 비회전체 3-view (IAM/STEP, Boss Plate 계열)

## orientation 상수 ≠ 뷰 레이블

XY 평면 스케치 비회전체, IAM·IPT 동일:

| 원하는 뷰 | 상수 | 보이는 면 | 실측 W×H (Boss Plate) |
|---|---|---|---|
| 평면도 (plan, 위) | `kFrontViewOrientation` | XY (홀·보스 원) | 11.5×7.5 |
| 정면도 (elevation, 앞) | `kTopViewOrientation` | XZ (폭×높이) | 11.5×3.0 |
| 측면도 (side, 우측) | `kRightViewOrientation` (`kLeft` 는 반전) | YZ (깊이×높이) | 3.0×7.5 |

IPT revolve 에서는 `kFront` = END VIEW(원형), `kRight` = SIDE VIEW(profile) — 회전체와 반대. 레이블은 `add_view_label()` 로 직접 붙인다.

## 아래 뷰(BOTTOM VIEW) = AddProjectedView

`kBottomViewOrientation=10767` → E_INVALIDARG. 10753~10800 중 10754 만 XZ 크기. `ModelViewName="Bottom"` + 10753 → XY 단면(groove 없음).

```python
vp = dvs.AddProjectedView(vg, tg.CreatePoint2d(plan_cx, plan_cy_below), kHiddenLineRemovedDrawingViewStyle)
# 부모(FRONT) 아래 위치 → 3각법 BOTTOM 자동. scale 상속. groove face ncurves≈250 (smooth face 4)
```

## 3rd-angle 배치

| 부품 | 뷰 |
|---|---|
| 회전체 (shaft, cup, cap) | SIDE + END + ISO |
| 비회전체 (bracket, plate, housing) | TOP + FRONT + SIDE + ISO |

```
TOP (plan):   upper-left,  kFrontViewOrientation
FRONT (elev): lower-left,  kTopViewOrientation, TOP 과 같은 cx
SIDE (right): upper-right, kRightViewOrientation, TOP 과 같은 cy   ← FRONT 옆 아님
```

치수 역할: TOP = 가로×세로 외형 + 홀 Ø / FRONT = 높이·단 구간 + 특징부 Ø / SIDE = 고유 치수 없으면 생략.

## DrawingCurve circle 크기 식별 불가

`c.Geometry.Radius` 0.0 / `c.MidPoint`·`c.Length` AttributeError / `dim.Value` 0.0 / `dim.Text.FormattedText` = `'<DimensionValue/>'`. Python COM 으로 plan view 원 크기 구별 불가.
→ boss Ø 는 circle 로 보이는 다른 view(FRONT) 에서 1회, plan view 에는 hole Ø 만. ci_plan 순회 시 첫 성공 원을 hole 로 처리.

## 중심마크 — 다중 원 (circle object 순회)

```python
N_CIRC = min(len(ci_plan), 7); cm_fail = []
for i, c in enumerate(ci_plan[:N_CIRC]):
    try:
        sheet.Centermarks.Add(sheet.CreateGeometryIntent(c, tg.CreatePoint2d(PLAN_CX, PLAN_CY)))  # hint 임의 — 마크는 circle 중심에
    except Exception as e:
        cm_fail.append((i, str(e)))
if cm_fail:
    raise RuntimeError("centermark %d/%d 실패 -- %s" % (len(cm_fail), N_CIRC, "; ".join("circle[%d]: %s" % (i, e) for i, e in cm_fail)))
```
arc 로 나타나는 원(boss 접선 홀) 은 ci_plan 에 없다 — 별도 처리.

## A3 레이아웃 공식 (비회전체)

```
vW, vH = view.Width, view.Height          # AddBaseView 직후
안전 영역 X[1.5, 40.5], Y[8.5, 28.5], title block top ≈ 7

TOP_CX  = safe_left + vW_top/2 + margin           # 예 1.5 + 7.5 + 2 = 11
TOP_CY  = safe_top - vW_top_vert/2 - dim_space
FRONT_CX = TOP_CX;  FRONT_CY = safe_bottom + vH_front/2 + dim_space
SIDE_CX = TOP_CX + vW_top/2 + center_gap + vW_side/2;  SIDE_CY = TOP_CY
ty_above = TOP_CY + vH_top/2 + 1.2;  tx_left = FRONT_CX - vW_front/2 - 2.0
```

스케일: 최대 치수 100mm → 1.5 (TOP W=15cm). 2.0 → W=20cm, 우측 낭비.
