# 치수·레이블·충돌 검사 함정

## ISO 129 치수 기입

- 과잉 치수 금지: 다른 치수에서 계산 가능한 값은 기입하지 않음. 필요하면 참고치수 `(값)`. 예: 8 + 15 = 23 → 8, 15 기입, 23 은 `(23)` 또는 생략
- 단차: 각 단 높이를 직전 면 기준 개별 기입. 누적 합산 금지
- 지름: Ø 접두어 필수. 원이 완전히 보이는 뷰(plan/end) 에서 기입
- 판단: "이 치수 없이 가공 가능한가?" No → 필수, Yes → 생략 또는 참고치수

## 뷰 명칭·스케일

| 뷰 | 이름 |
|---|---|
| kRightViewOrientation (profile) | `SIDE VIEW` |
| kFrontViewOrientation (원형) | `END VIEW` |
| kIsoTopRightViewOrientation | `ISOMETRIC VIEW` |

```
최대 치수 ≤ 40mm → scale 2 / ≤ 80mm → 2 (또는 1) / ≤ 200mm → 1 / > 200mm → 0.5
ISO scale ≈ SIDE/END × 0.65. 1 미만 스케일(1:0.9 등) 금지
표기: "SCALE 2 : 1" (콜론 양쪽 공백)
```

참조치수(전체 스팬) = `(80.00)` 괄호 — `HideValue=True` + `FormattedText` (`inventor_rotational_drawing.md`).

## 뷰 레이블 & 투상법 기호

```python
def add_view_label(gn, tg, cx, bottom_y, label, scale_str, size=0.28):
    note = gn.AddByRectangle(tg.CreatePoint2d(cx - 3.5, bottom_y - 0.3),   # 사각형 폭은 안 쓰인다 — 상자 폭 = 글자 길이
                             tg.CreatePoint2d(cx + 3.5, bottom_y - 1.0),
                             "<StyleOverride FontSize='%s'>%s  %s</StyleOverride>" % (size, label, scale_str))   # 한 줄
    note.HorizontalJustification = 19969                    # 가운데, 이 노트만 (19970 왼쪽 / 19971 오른쪽)
    note.Position = tg.CreatePoint2d(cx, bottom_y - 0.3)    # 기준점 = 글자 중심. 정렬만 바꾸면 상자는 그대로

add_view_label(gn, tg, SIDE_CX, SIDE_CY - vH_side/2, "SIDE VIEW",      "SCALE 2 : 1")
add_view_label(gn, tg, END_CX,  END_CY  - vH_end/2,  "END VIEW",       "SCALE 2 : 1")
add_view_label(gn, tg, ISO_CX,  ISO_CY  - vH_iso/2,  "ISOMETRIC VIEW", "SCALE 1.3 : 1")

# THIRD ANGLE PROJECTION — 독립 노트, 표제란 근처. 스펙 노트 안에 섞지 않는다
note = gn.AddByRectangle(tg.CreatePoint2d(19.0, 9.5), tg.CreatePoint2d(26.0, 7.5),
                         "<StyleOverride FontSize='0.22'>THIRD ANGLE PROJECTION</StyleOverride>")
```

- 이 노트만 정렬하려면 `note.HorizontalJustification` = `HorizontalTextAlignmentEnum`(19969 가운데 · 19970 왼쪽 · 19971 오른쪽). 정렬을 바꿔도 상자는 움직이지 않고 `note.Position.X` 가 기준점(가운데 = 글자 중심, 오른쪽 = 오른쪽 끝)이 된다 — 정렬 뒤 `Position` 을 준다. 8963 은 `kEnglishSystemOfMeasure` 값이라 노트·스타일 어디에 써도 E_INVALIDARG.
- `note.TextStyle.*`(FontSize·HorizontalJustification) 는 도면 공용 스타일('Note Text (ANSI)')이다 — 값은 받지만 한 노트에 쓰면 모든 노트가 바뀌고 마지막 값이 이긴다. 노트마다 다른 크기는 텍스트의 `<StyleOverride FontSize=..>`(한 도면에 0.28·0.20 공존 확인).

## 치수 배치 — 뷰별 역할, 중복 금지

| 치수 | 뷰 |
|---|---|
| 길이(단 구간·전체 스팬) | SIDE VIEW |
| 지름 Ø | END VIEW |
| 참조치수(전체 스팬) | SIDE VIEW |

END VIEW `GetDrawingCurves` 는 단 수 초과 curve 반환 가능 → `[:N_STEPS]` 슬라이싱.

## 분홍 치수 — GI 힌트 점이 곡선 밖

`CreateGeometryIntent(curve, hint)` 의 hint 가 curve extent 밖 → Driven(핑크).

```python
# v-line: x = 자기 x, y = 실제 endpoint
b = get_bounds(v_line_curve); x = (b[0]+b[2])/2; y = b[1]   # 또는 b[3]
gi = sheet.CreateGeometryIntent(v_line_curve, tg.CreatePoint2d(x, y))
# h-line: y = 자기 y, x = clamp
b = get_bounds(h_line_curve); y = (b[1]+b[3])/2; x = max(b[0], min(b[2], x_from_other_curve))
```
2-curve 수직 dim: 각 anchor 는 자기 curve 위 (h-line: mid_x·mid_y / v-line: mid_x·endpoint_y). 두 anchor 가 같은 curve → driven, skip.

## GetDrawingCurves 좌표계 = 시트 좌표 cm, SCALE 반영

curve 좌표는 뷰 위치와 SCALE 이 들어간 시트 좌표다(`inventor_drawing_core.md` 「뷰 생성」). 모델 mm 로 바꿀 때는 SCALE 로 나눈다.

```python
dx_mm = (xs[i+1] - xs[i]) / SCALE * 10     # SCALE 2 에서 35 mm 구간 = 7.0 cm
```

## GI hint point — 보조선 겹침 방지

hint 를 뷰 중심으로 두면 보조선이 뷰를 가로질러 치수선까지 내려온다. hint = 치수가 나가는 방향의 뷰 가장자리.

```python
DH("F_W", 80, cl['obj'], x0, y0, cr['obj'], x_end, y0, xm, y0-D1)      # 아래 치수 → hint Y = y0
DH("R_vz", 15, cv0['obj'], x0r, y_endr, cv1['obj'], sx1r, y_endr, tx, y_endr+D1)  # 위 → y_end
DV("F_D", 60, cb['obj'], x0, y0, ct['obj'], x0, y_end, x0-D1, ym)      # 왼쪽 → hint X = x0
DV("R_vy", 15, b0['obj'], x_endr, y0r, bv['obj'], x_endr, sy1, x_endr+D1, ym_r)  # 오른쪽 → x_end
```

## ISO VIEW 위치 — 우측 수직 치수 확보

```python
iso_avail_l = rR + D2 + 1.0          # Right view 최우측 수직 치수 + margin
iso_avail_r = SAFE_R - 1.0
iso_cx = max(iso_avail_l + iW/2 + 0.2, (iso_avail_l + iso_avail_r) / 2.0)
```

## 좌표 기반 충돌 검사 (A3 + `ANSI (mm).idw` 한정)

```python
def _ov(x1a,x2a,y1a,y2a, x1b,x2b,y1b,y2b, m=0.0):
    '''m=0: 겹침 / m>0: gap < m. 시그니처 변형 금지 (면적 계산으로 바꾸면 gap 검사 소실)'''
    return x1a-m < x2b and x2a+m > x1b and y1a-m < y2b and y2a+m > y1b

VIEWS = []   # 존재하는 뷰만 (회전체 = Top 없음)
if vf: VIEWS.append(("Front", vf.Center.X-vf.Width/2, vf.Center.X+vf.Width/2, vf.Center.Y-vf.Height/2, vf.Center.Y+vf.Height/2))
# vr, vt, vi 동일

T = 0.3   # 치수 텍스트 여유
bbs = list(VIEWS) + [
    # ("F-left",  fL-D2-T, fL, fB, fT),  ("R-right", rR, rR+D2+T, rB, rT), ... 뷰별 치수 bbox
    ("Notes", note_x1, note_x2, note_y1, note_y2),
    ("TitleBlock", 0.0, 42.0, 0.0, 4.5),   # 항상 포함. 실측값, 템플릿 바뀌면 재측정
]

for i, (na,ax1,ax2,ay1,ay2) in enumerate(VIEWS):                  # 1단계 뷰-뷰 gap 1cm (A4 0.5, A2 1.5)
    for nb,bx1,bx2,by1,by2 in VIEWS[i+1:]:
        if _ov(ax1,ax2,ay1,ay2, bx1,bx2,by1,by2, m=1.0): log("[GAP<1cm] %s vs %s" % (na, nb))
total_ov = 0
for i, (na,ax1,ax2,ay1,ay2) in enumerate(bbs):                    # 2단계 전체 겹침
    for nb,bx1,bx2,by1,by2 in bbs[i+1:]:
        if _ov(ax1,ax2,ay1,ay2, bx1,bx2,by1,by2, m=0.0): log("[OVERLAP] %s vs %s" % (na, nb)); total_ov += 1
```

### 윤곽선 경계 검사 (겹침 검사와 별도, 필수)

```python
BORDER_L, BORDER_R, BORDER_B, BORDER_T = 1.0, 41.0, 1.0, 28.7   # ANSI A3 추정. IDW 열어 실측 권장
SAFE_GAP = 0.5
def check_border(bbs, bl=BORDER_L, br=BORDER_R, bb=BORDER_B, bt=BORDER_T, m=SAFE_GAP):
    issues = []
    for name, x1, x2, y1, y2 in bbs:
        if x1 < bl + m: issues.append("[BORDER-LEFT]  %s: x1=%.2f < %.2f" % (name, x1, bl+m))
        if x2 > br - m: issues.append("[BORDER-RIGHT] %s: x2=%.2f > %.2f" % (name, x2, br-m))
        if y1 < bb + m: issues.append("[BORDER-BOT]   %s: y1=%.2f < %.2f" % (name, y1, bb+m))
        if y2 > bt - m: issues.append("[BORDER-TOP]   %s: y2=%.2f > %.2f" % (name, y2, bt-m))
    for msg in issues: log(msg)
    return issues
```

레이아웃 공식 (치수가 왼쪽·아래로 나가는 뷰):
```
cx_min = BORDER_L + SAFE_GAP + DIM_OFF + hw     # 1.0 + 0.5 + 1.2 + hw
cy_min = max(BORDER_B, TitleBlock_top) + SAFE_GAP + DIM_OFF + hh
```
scale 20 에서 hw=4.98 → cx_min 8.0, NOTE 공간 부족 → scale 15 (hw 3.735, cx_min 6.43).

FRONT 아래 BOTTOM(projected) 배치: `plan_cy = groove_cy - groove_hh - 4.0 - plan_hh` (GAP 4.0 = label 1.0 + spare 0.5 + gap 2.5). BOTTOM dim 하단 > TitleBlock top 4.5 + 0.5.

한계: ISO bbox 는 AABB 과대추정(false positive) / TitleBlock·윤곽선 좌표는 A3 ANSI(mm).idw 실측·추정값 / 치수 bbox 는 `DIM_OFF` 근사 — verify.png 병행.
