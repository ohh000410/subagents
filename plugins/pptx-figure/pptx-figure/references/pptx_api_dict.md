# PPT 도형 API 사전 — 조회용

**통째로 읽지 않는다.** 필요한 항목만 찾아 쓴다. 개념·판단은 `pptx_3d_core.md`.

## 1. python-pptx 함정 (전부 실측)

python-pptx 자체의 함정 표(EMU·RGBColor·word_wrap·effectLst 중복·PNG 비율)와 `no_shadow()`/`soft()` 헬퍼는 `pptx_figure.md` 에 있다.

**방향·부호 규약 (실측)** — 머리로 계산하면 틀리는 것들. 도형 3개짜리 테스트 슬라이드를 한 번 렌더해 확인한다.
- 화면 좌표는 y 가 아래로 증가 → **양수 회전각이 시계방향**.
- `python-pptx` 의 `gradient_angle` 과 직접 쓴 `<a:lin ang>` 은 **부호 규약이 반대**.
- `lin_multi` 의 stop0 위치는 도형마다 다르다(§2).
- 곡선 화살표의 진행 방향을 뒤집으면 화살촉뿐 아니라 갈고리가 열린 쪽까지 뒤집힌다.

## 2. python-pptx 에 없는 것 → XML 주입

### 투명도

```python
clr.append(parse_xml('<a:alpha %s val="%d"/>' % (nsdecls("a"), int(pct*1000))))
```

⚠️ **`val`은 투명도가 아니라 불투명도다.** `42000` 을 넣으면 PowerPoint UI 는
"투명도 58%"로 표시한다. `투명도 = 100 - val/1000`.


### 다중 stop 선형 그라디언트

2-stop 으로는 "양 끝만 진하고 가운데는 흰색" 같은 프로파일이 **원리상 안 나온다**.

```python
def lin_multi(s, angle_deg, stops):        # stops = [(pos0~1, hex), ...]
    spPr = s._element.spPr
    for tag in ("a:solidFill", "a:noFill", "a:gradFill"):
        e = spPr.find(qn(tag))
        if e is not None: spPr.remove(e)
    gs = "".join('<a:gs pos="%d"><a:srgbClr val="%s"/></a:gs>'
                 % (int(p*100000), c) for p, c in stops)
    el = parse_xml('<a:gradFill %s rotWithShape="1"><a:gsLst>%s</a:gsLst>'
                   '<a:lin ang="%d" scaled="0"/></a:gradFill>'
                   % (nsdecls("a"), gs, int(angle_deg*60000) % 21600000))
    ln = spPr.find(qn("a:ln"))
    (ln.addprevious(el) if ln is not None else spPr.append(el))
    return s
```

⚠️ **stop0 이 머리 쪽인지 꼬리 쪽인지는 도형 bbox 방향에 따라 뒤집힌다.**
같은 그림 안에서도 붉은 화살표는 stop0=머리, 주황 화살표는 stop0=꼬리였다. 한 번 렌더해서 확인한다.


### 방사형 그라디언트

⚠️ **`path="circle"` 은 비정사각·비직사각 도형에서 등고선이 사각형이 된다.**
반원·타원·자유형이면 **`path="shape"`** 를 쓴다 — 등고선이 도형 외곽선을 따라간다. 실측(중성 화소 110k):

| | 평균 \|Δ\| | t 0.70-0.85 | t 0.85-0.99 |
|---|---|---|---|
| `circle` | R 34.4 / G 32.5 / B 23.8 | 37.1 | 39.3 |
| **`shape`** | **R 15.0 / G 16.8 / B 15.9** | **20.7** | **17.5** |

`shape` 로 바꾸면 stop 매핑도 달라지므로 **K 교정을 다시 해야 한다.**

⚠️⚠️ **stop 위치를 기하로 예측하지 않는다 — 렌더로 교정한다.**
`a:path` 방사형은 **stop 1.0 이 bbox 모서리**에 걸린다. "타원 가장자리 = 1/√2 = 0.7071" 계산은 틀린다.
실측: PowerPoint 가 램프를 요청보다 6~7% 바깥에 놓는다. 교정 렌더 2회로 스케일 **K = 0.664**.

```
요청 stop = 원하는 시각적 t x K        # K 는 요소마다 렌더로 교정. 예측값 아님
검증: 렌더에서 t 별 색을 다시 떠서 원본 프로파일과 대조
```

★ 증상이 "그라디언트가 안 먹은 것처럼 평평하다" 로 나타난다 — 램프가 도형 밖으로 나간 것이다.

반투명 원을 여러 겹 쌓으면 경계에 **동심원 링**이 생긴다. 도형 1개 + 방사 그라디언트로 대체한다.

```python
'<a:gradFill %s rotWithShape="1"><a:gsLst>%s</a:gsLst>'
'<a:path path="circle"><a:fillToRect l="50000" t="50000" r="50000" b="50000"/></a:path>'
'</a:gradFill>'
```

앵커링 함정:
1. 마지막 stop 은 **bbox 모서리** 기준이라, 타원 가장자리에서 alpha 가 아직 0 이 아니면
   테두리에 링이 남는다 → alpha 0 을 pos 0.75 쯤에서 미리 만들고 뒤를 평탄하게.
2. 중심을 프레임 밖에 두면(코너 글로우) 화면 안이 전부 저-alpha 구간이라 효과가 통째로 사라진다.


### ★ 스키마 순서 — "태그가 있는데 안 먹는다"의 정체

OOXML 의 컨테이너는 **자식 순서가 강제**다. 순서를 어기면 PowerPoint 가 **예외 없이, 경고 없이
그 자식을 버린다.** 태그 존재 검사로는 절대 안 잡힌다. **렌더로만 잡힌다.**

| 컨테이너 | 자식 순서 |
|---|---|
| `p:spPr` | `a:xfrm` → **geometry**(`a:prstGeom`/`a:custGeom`) → **fill** → `a:ln` → `a:effectLst` → `a:scene3d` → `a:sp3d` |
| `a:ln` | fill → `a:prstDash`/`a:custDash` → `a:round`/`a:bevel`/`a:miter` → `a:headEnd` → `a:tailEnd` |
| `a:rPr` | `a:ln` → fill → **`a:effectLst`** → `a:highlight` → `a:uLnTx/uLn` → `a:uFillTx/uFill` → `a:latin` → `a:ea` → `a:cs` |

```python
geom = spPr.find(qn('a:prstGeom')) or spPr.find(qn('a:custGeom'))
geom.addnext(grad)          # ★ append/insert(1) 이 아니라 기준 노드 뒤에 붙인다
```

실측 세 건 (전부 XML 검사는 통과했다):
- `a:gradFill` 을 `spPr` index 1(geometry 앞)에 → 그라디언트가 통째로 무시, 노출 배경 |d| 119
- `a:effectLst` 를 `rPr` 에 append(`a:latin` 뒤) → glow 가 안 그려짐
- `shadow.inherit = False` 를 쓴 뒤 `SubElement(spPr, "ln")` → `inherit=False` 가 빈 `<a:effectLst/>` 를
  심어놓기 때문에 뒤이은 `ln` 이 effectLst 뒤로 가서 버려진다. 3.06 pt 네이비 점선이 1 pt 파란 실선으로 렌더.

★ **자식마다 앵커를 따로 잡는다.** 한 자식이 통과했다고 다른 자식도 통과하지 않는다.
검사 코드는 "태그가 있나"가 아니라 "순서가 맞나"를 물어야 한다.


### 텍스트에 효과 걸기 — 조용히 버려지는 두 자리

글자에 `a:glow`/`a:outerShdw` 를 걸 때, 틀린 두 방법이 렌더에서 "효과 없음"과 픽셀 단위로 같다.

| 시도 | 결과 |
|---|---|
| `a:effectLst` 를 도형 `spPr` 에 | 글자가 아니라 **상자**에 걸린다. 상자가 `noFill` 이면 아무것도 안 그려진다 |
| run 의 `a:rPr` 에 `append` | `rPr` 도 **스키마 순서**다. `a:latin` 뒤에 놓이면 조용히 버린다 |

```python
rPr = run._r.get_or_add_rPr()
latin = rPr.find(qn('a:latin'))
el = parse_xml('<a:effectLst %s><a:glow rad="47413">...</a:glow></a:effectLst>' % nsdecls('a'))
latin.addprevious(el) if latin is not None else rPr.append(el)   # ★ latin 앞
```

★ **검출은 링 통계로 한다.** 글자 잉크 마스크를 3/6/10 px 팽창시켜 링별 평균색을 찍는다.
효과가 죽어 있으면 3 px 링이 배경색 그대로다(고장 (34,34,128) / 정상 (140,139,188)).
`a:glow` 는 꼬리가 짧아서 원본이 10~16 px 까지 밝으면 반경을 키워도 못 맞춘다 — `[UNRESOLVED]`.


## 3. 3D 서식 — API 사전

출처: [a:camera](https://www.datypic.com/sc/ooxml/e-a_camera-1.html) ·
[a:sp3d](https://www.datypic.com/sc/ooxml/e-a_sp3d-1.html) ·
[a:scene3d](https://www.datypic.com/sc/ooxml/e-a_scene3d-1.html) ·
[ECMA-376 sp3d](https://c-rex.net/samples/ooxml/e1/part4/OOXML_P4_DOCX_sp3d_topic_ID0ET5DMB.html) ·
[ThreeDFormat](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.threedformat)
+ COM 설정→XML 덤프 왕복 프로브 실측.

```xml
<p:spPr>
  <a:scene3d>
    <a:camera prst="..." fov="..." zoom="..."><a:rot lat lon rev/></a:camera>
    <a:lightRig rig="..." dir="..."><a:rot lat lon rev/></a:lightRig>
    <a:backdrop><a:anchor x y z/><a:norm dx dy dz/><a:up dx dy dz/></a:backdrop>
  </a:scene3d>
  <a:sp3d z="..." extrusionH="..." contourW="..." prstMaterial="...">
    <a:bevelT w h prst/><a:bevelB w h prst/>
    <a:extrusionClr>...</a:extrusionClr><a:contourClr>...</a:contourClr>
  </a:sp3d>
</p:spPr>
<p:txBody><a:bodyPr ...><a:flatTx/></a:bodyPr></p:txBody>   <!-- 텍스트 평면 유지 -->
```

**단위**: 1 pt = **12700** EMU · 1도 = **60000** · 백분율 ×1000

**UI 「3차원 서식」 ↔ COM ↔ XML**

| UI | COM (ThreeDFormat) | XML | 단위 |
|---|---|---|---|
| 위쪽 입체 · 모양 | `BevelTopType` | `a:bevelT@prst` | enum |
| 위쪽 입체 · 너비 | `BevelTopInset` | `a:bevelT@w` | pt→EMU |
| 위쪽 입체 · 높이 | `BevelTopDepth` | `a:bevelT@h` | pt→EMU |
| 아래쪽 입체 | `BevelBottom*` | `a:bevelB@prst/w/h` | 〃 |
| 깊이 · 크기 | `Depth` | `a:sp3d@extrusionH` | pt→EMU |
| 깊이 · 색 | `ExtrusionColor.RGB` | `a:extrusionClr` | |
| 외형선 · 크기 | `ContourWidth` | `a:sp3d@contourW` | pt→EMU |
| 외형선 · 색 | `ContourColor.RGB` | `a:contourClr` | |
| 표면 효과 · 재질 | `PresetMaterial` | `a:sp3d@prstMaterial` | enum |
| 표면 효과 · 조명 | `PresetLighting` | `a:lightRig@rig` | enum |
| 표면 효과 · 조명 방향 | `PresetLightingDirection` | `a:lightRig@dir` | enum |
| 표면 효과 · 각도 | `LightAngle` | `a:lightRig > a:rot@rev` | 도→60000 |
| (부드럽게) | `PresetLightingSoftness` | **XML 에 안 남음** | legacy 전용 |

**UI 「3차원 회전」 ↔ COM ↔ XML**

| UI | COM | XML | 비고 |
|---|---|---|---|
| 미리 설정 | `SetPresetCamera(n)` / `PresetCamera` | `a:camera@prst` | enum 1~62 |
| X 회전 | `RotationX` | `a:camera > a:rot@lon` | **부호 반대**, −90~90 |
| Y 회전 | `RotationY` | 〃 `@lat` | 부호 같음, −90~90 |
| Z 회전 | `RotationZ` | 〃 `@rev` | **부호 반대** |
| 원근감 | `FieldOfView` — 문서 0~180 이나 **COM 은 120 초과 거부**(실측 120 OK / 130 실패) | `a:camera@fov` | **`orthographic`·`isometric`·`oblique` 계열은 무시하고 XML 에 쓰지도 않음** |
| 밑면에서의 거리 | `Z` | `a:sp3d@z` | pt→EMU |
| 텍스트를 평면에 유지 | `ProjectText` | **`a:bodyPr > a:flatTx`** | ★ spPr 이 아니라 txBody 쪽. False 일 때 flatTx 삽입 |
| — (UI 없음) | — | `a:camera@zoom` | 백분율×1000, 기본 100000 |
| — (UI 없음) | — | `a:scene3d > a:backdrop` | `a:anchor(x,y,z)` `a:norm(dx,dy,dz)` `a:up(dx,dy,dz)` |
| 회전 초기화 | `ResetRotation()` | | |
| 증분 회전 | `IncrementRotationX/Y/Z()` | | |

⚠️ `PresetExtrusionDirection` 은 **읽기 전용** — `Property can not be set` 로 실패한다.

**열거형 — COM 정수 = XML 문자열** (전수 실측)

`BevelTopType` / `BevelBottomType`
```
1 없음  2 relaxedInset  3 circle(기본, prst 생략)  4 slope  5 cross  6 angle
7 softRound  8 convex  9 coolSlant  10 divot  11 riblet  12 hardEdge  13 artDeco
```

`PresetMaterial`
```
1 legacyMatte  2 legacyPlastic  3 legacyMetal  4 legacyWireframe  5 matte  6 plastic
7 metal  8 warmMatte(기본, 속성 생략)  9 translucentPowder  10 powder  11 dkEdge
12 softEdge  13 clear  14 flat  15 softmetal
```

`PresetLightingDirection` → `a:lightRig@dir`
```
1 tl  2 t  3 tr  4 l  5 (없음→legacy rig 로 되돌림)  6 r  7 bl  8 b  9 br
```

`PresetLighting` → `a:lightRig@rig` (문자열 전량)
```
threePt  balanced  soft  harsh  flood  contrasting  morning  sunrise  sunset
chilly  freezing  flat  twoPt  glow  brightRoom
+ legacy 12종: legacyFlat1~4  legacyNormal1~4  legacyHarsh1~4
```

`SetPresetCamera` → `a:camera@prst`
```
 1~ 9  legacyOblique     TopLeft Top TopRight Left Front Right BottomLeft Bottom BottomRight
10~18  legacyPerspective 〃 (같은 9방향)
   19  orthographicFront
20~27  isometric         TopUp TopDown BottomUp BottomDown LeftUp LeftDown RightUp RightDown
28~39  isometricOffAxis  1Left 1Right 1Top / 2Left 2Right 2Top / 3Left 3Right 3Bottom / 4Left 4Right 4Bottom
40~47  oblique           TopLeft Top TopRight Left Right BottomLeft Bottom BottomRight
48~52  perspective       Front Left Right Above Below
53~54  perspectiveAbove  LeftFacing RightFacing
55~56  perspectiveContrasting  LeftFacing RightFacing
57~60  perspectiveHeroic       LeftFacing RightFacing ExtremeLeftFacing ExtremeRightFacing
   61  perspectiveRelaxed        62  perspectiveRelaxedModerately
```

**COM 제약**

- 각도·재질을 만지기 전에 **`.ThreeD.Visible = True`** 를 먼저 켠다.
- `RotationX` / `RotationY` 는 **−90~90 만**. 벗어나면 `com_error '지정한 값이 범위를 벗어났습니다'`.
- MS 문서: multiple-disjoint paths(구멍 뚫린 도형)에는 COM 3D 적용 불가. XML 로 직접 넣으면 렌더는 정상(실측).

**프리셋 실측치** — 원본 사각형 1:1, 돌출 0.09in

| prst | RotX | RotY | RotZ | bh/hw | fh/hw |
|---|---|---|---|---|---|
| `isometricTopUp` | 45.3 | −35.4 | −60.2 | 0.607 | 0.515 |
| `isometricTopDown` | −45.3 | −35.4 | 60.2 | 0.597 | 0.569 |
| `isometricOffAxis1Top` | 53.5 | −58.7 | −57.6 | 0.291 | 0.196 |
| `isometricOffAxis2Top` | −53.5 | −58.7 | 57.6 | 0.284 | 0.261 |
| `perspectiveAbove` / `Relaxed` / `orthographicFront` | 0 | −20 / −50.4 / 0 | 0 | 정면 | |

**★ 조명 실측 — 지정한 색이 그대로 안 나온다**

`isometricOffAxis2Top` / `dir="t"` / 윗면 지정 `66B2FE`(102,178,254):

| rig | 윗면 실제 | 옆면 |
|---|---|---|
| **`flat`** | **(102,177,253) = 지정색 그대로** | 은은하게 어두움. 안 탐 |
| `contrasting` | 그대로 | 무난 |
| `brightRoom` `glow` | 그대로 | **시안으로 과하게 밝음** |
| `threePt` | (106,185,255) 밝아짐 | **검게 탄다** |
| `soft` `harsh` `flood` `twoPt` | 어두워짐 | **검게 탄다** |
| `balanced` | (96,169,241) | 무난 |
| `morning` `sunrise` | (88,151,195) / (86,139,169) 색조 변함 | |

→ `threePt` 는 돌출색을 무시하고 옆면을 검게 만든다. 좌우 옆면 색을 다르게 하려면 `dir` 로 방향을 준다.

⚠️ **위 표는 이 카메라 하나에서 잰 값이다. 승자는 카메라마다 다르다.** RotX 81.6° 의 거의 edge-on
트레이에서는 `flat/t` 가 안쪽 벽 두 장을 45 / 40 dE 어둡게 태웠고 **`contrasting/t`** 가 이겼다.
`flat/tr`·`flat/r`·`flat/l` 은 벽 하나가 흰색으로 날아갔다. **요소마다 rig×dir 를 프로브하고 면적가중 dE 로 고른다**(19.1 → 9.1).


## 4. 불리언 병합 (COM 전용) — API 사전

출처: [ShapeRange.MergeShapes](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.shaperange.mergeshapes) ·
[MsoMergeCmd](https://learn.microsoft.com/en-us/office/vba/api/overview/library-reference/msomergecmd-enumeration-office)
+ 실측.

python-pptx 에 없다. `ShapeRange.MergeShapes(MergeCmd, PrimaryShape)`

| MsoMergeCmd | 값 | 동작 |
|---|---|---|
| `msoMergeUnion` | 1 | 합집합 |
| `msoMergeCombine` | 2 | 합치되 **겹친 부분은 도려냄** |
| `msoMergeIntersect` | 3 | 교집합 |
| `msoMergeSubtract` | 4 | **primary − 나머지** |
| `msoMergeFragment` | 5 | 교선 기준으로 조각냄 |

```python
sl.Shapes.Range(["base", "cut"]).MergeShapes(4, sl.Shapes("base"))   # base - cut
```

**★ PrimaryShape — 문서상 optional 이지만 사실상 필수 인자**
- 생략하면 pywin32 에서 `TypeError: The Python instance can not be converted to a COM object`.
- **결과가 이 도형의 서식을 물려받는다** — 채우기·선·3D 전부.
- **Subtract 에서는 이게 피감수다.** 거꾸로 주면 결과가 빈 도형이 되어 **양쪽 다 사라진다**
  (도형 수 7 → 5, 오류 없음). 병합 후 **도형 수를 반드시 확인**한다.

**★ 병합하면 이름이 날아간다.** 두 이름 모두 사라지고 `Freeform N` 이 된다. 병합 직후 새 이름을 다시 붙인다.

```python
before = {sl.Shapes(i+1).Name for i in range(sl.Shapes.Count)}
rng.MergeShapes(4, sl.Shapes("base"))
after  = {sl.Shapes(i+1).Name for i in range(sl.Shapes.Count)}
sl.Shapes(list(after - before)[0]).Name = "base_merged"     # 이름 복구
```

**★ 병합 + 3D 를 같이 쓸 때** (전부 실측)

| 질문 | 답 |
|---|---|
| Subtract 결과(구멍 = disjoint paths)에 COM 3D 를 걸 수 있나? | **된다.** (`Depth=30` 적용 성공, `AutoShapeType=138`, `Nodes.Count=8`) |
| 3D 를 먼저 걸고 병합하면 3D 가 남나? | **primary 쪽 3D 만 남는다.** 다른 쪽에만 있으면 사라진다 |
| 권장 순서 | **병합 → 3D**. 또는 3D 를 primary 에 걸어두고 병합 |

구멍 뚫린 기판·홈 파인 슬래브는 **Subtract 로 윤곽을 만들고 그 결과에 `sp3d` 를 얹으면** 도형 하나로 끝난다.

**검증**
- 결과는 `AutoShapeType == 138`(msoShapeNotPrimitive). `Nodes.Count` 가 형상 검증의 정본이다.
  사각형 − 사각형 = **8** 정점, 사각형 − 삼각형 8개 = 4 + 8×3 = **28** 정점.
- 도형 수 변화로 연산을 판별한다 — 늘어나는 건 Fragment 뿐. 단 한쪽이 다른 쪽에 완전히 포함되면
  Fragment 도 2 → 2 로 안 늘어난다.

---

## 실전 관용구

원작자들이 실제로 쓴 조합. 재현 때 이 패턴을 만나면 같은 방식으로 만들고, 창작 때는 그대로 가져다 쓴다.

- **베벨 렌즈/버튼**: `depth=0 + bevelT 15x15pt + orthographicFront + threePt`.
  돌출 없이 도형 하나로 볼록한 렌즈·패드. 옆면이 없으므로 "threePt 가 옆면을 태운다" 경고가 적용되지 않는다.
- **cube/can/parallelogram 프리셋**: 아이콘 크기의 상자·원통은 네이티브 3D 대신 **프리셋 도형 하나**로.
  단일 도형이라 편집 가능성 규칙에 어긋나지 않는다.
- **잘라낸 구(cut-away)**: 방사형 타원(몸체) + pie 3장(껍질 절개면) + pie 3장(코어). **총 7장**.
  ```
  정면   rot 180  · adj 89.88..180.00  · ext 정사각
  눌린A  rot 270  · adj 89.88..225.16  · ext 폭 0.298
  눌린B  flipV=1  · adj 89.88..224.97  · ext 폭 0.300     <- rot 0 이 아니다
  ```
  ★ 눌린 두 장은 "같은 도형을 90도 돌린 것"이 아니다 — 스윕각 90° vs 135°, 셋째는 회전이 아니라 **`flipV`** 다.
  ★ 3면 명암은 두 해법을 한 그림에서 섞어 쓴다: 껍질은 같은 회색에 **알파 60/70/90**, 코어는 같은 색에 **`lumMod` 90/80/65**.
- **`flipV="1"` 은 `rot 180` 과 다르다.** 부채꼴·화살표에서 갈린다. python-pptx API 가 없어 `<a:xfrm flipV="1">` 로 직접 넣는다.
- ★ **`shape.rotation` 은 flip 을 반영하지 않는다.** `rot 135.88 + flipH + flipV` 는 실제로 **315.88°** 다.
  **`rot` 은 항상 `flipH`/`flipV` 와 같이 읽는다.** 화살표가 가리키는 방향으로 검산하면 바로 걸린다.
- **`pie` 의 `adj` = 시작각·끝각** (0°=3시, 시계방향): `0..90 -> 우하 · 90..180 -> 좌하 · 180..270 -> 좌상 · 270..360 -> 우상`.
  python-pptx 로 만든 PIE 에는 기본 `gd` 가 이미 있다 — `for g in list(avLst): avLst.remove(g)` 먼저.
- ★ **화소에서 읽은 색은 결과지 입력이 아니다.** `scene3d` 나 효과가 걸린 도형에 렌더값을 원색으로 넣으면
  조명이 두 번 먹는다(`#DE7C7C` + scene3d -> `#EC8989`). 원색을 넣고 렌더로 확인한다.
- **`sp3d` 없이 `scene3d` 만** 있는 도형이 있다 — 돌출·베벨 없이 **조명만** 얹는 용법. 채움이 정답과
  글자 그대로 같은데 렌더가 균일하게 어긋나면 `scene3d` 를 의심한다(|d| 7.64 -> 0.16).
- **화살표 꼬리 페이드**: 같은 색 2-stop 선형 그라디언트에 **알파만 100→0**. 방사 배치는 rot 로.
- **레이저/빛 번짐**: `softEdge` + 방사형 그라디언트+알파. 글로우는 `a:glow`.
- **속도 프로파일**: arc 1개 + 길이가 포물선인 rightArrow 9개.
- **NN 다이어그램**: ellipse N개 + line N² — 반드시 루프로 생성한다.
