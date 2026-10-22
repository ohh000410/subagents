# Inventor 2027 도면 COM API

실측 검증된 일반 패턴. 미검증·새 관찰 → agent-memory. references 읽기 전용.

## 환경

| 항목 | 값 |
|---|---|
| Inventor | 2027 (v31.0) |
| Python | CPython 3.12 |

## Launch & 연결

```python
import win32com.client
from win32com.client import CastTo
import time

app = win32com.client.Dispatch("Inventor.Application")
app.Visible = True   # False → Profiles.AddForSolid 실패
time.sleep(3)
tg = app.TransientGeometry
# app.SoftwareVersion.Major == 31
```

- gencache: `win32com.client.gencache.EnsureDispatch("Inventor.Application")` — DrawingDocument 등 CastTo 필요 시. 캐시 `~\AppData\Local\Temp\gen_py\3.12\`
- 실행 전 Inventor 가 이미 떠 있으면 붙지도 죽이지도 않고 거부·보고(Dispatch 는 실행 중 인스턴스에 붙음). 종료는 자기가 띄운 PID 만: `tools/inventor_session.py` `launch()`/`kill_own(pid)`
- 기동(`Dispatch` → `SoftwareVersion`) 5.8~10.3 s, `launch()` + 첫 `Documents.Add(part)` ≈ 11.5~12.5 s (연속 실행). 부팅 직후 첫 기동은 미측정
- 소요 시간(작성자 PC 실측): 기동 + 첫 `Documents.Add` 가 고정비이고(2026-10-22 약 12 s, 2026-08 21 s) 작업 자체는 짧다. 아래는 2026-08 값
  - IPT(revolve + 구멍 2개 + MassProperties + 저장) 20 s, 피처 21개(+ MassProperties 21회) 23 s — 피처 수는 병목이 아니다(피처 하나 ≈ 0.26 s)
  - A3 도면(3뷰 + 치수 8개 + 노트 15줄 + IDW·PDF·PNG) 34~36 s. 뷰 렌더 대기는 `sleep(8)` 한 번이면 된다(뷰마다 아님)
  - 한 스크립트에서 모델링부터 도면까지 이으면 기동 고정비가 한 번만 든다(26.7 s). timeout 은 몇 번 띄우는지부터 세고, 이 규모면 모델 60 s / 도면 120 s

## 상수 (실측)

```python
kPartDocumentObject                = 12290
kDrawingDocumentObject             = 12292
kAssemblyDocumentObject            = 12291
kJoinOperation                     = 20481  # PartFeatureOperationEnum (형식 라이브러리 확인)
kCutOperation                      = 20482
kNewBodyOperation                  = 20485
kPlaneSurface                      = 5890   # face.SurfaceType (constants 에 kPlanarSurface 는 없다)
kCylinderSurface                   = 5891
kPositiveExtentDirection           = 20993  # HoleFeature 필수 (1/2/3 금지)
kNegativeExtentDirection           = 20994
kSymmetricExtentDirection          = 20995
kDistanceExtent                    = 20737
kThroughAllExtent                  = 20743  # 20739 = kFullSweepExtent
kFrontViewOrientation              = 10764
kRightViewOrientation              = 10755
kTopViewOrientation                = 10754
kLeftViewOrientation               = 10758
kBottomViewOrientation             = 10757  # IPT. 10767 은 E_INVALIDARG
kIsoTopRightViewOrientation        = 10759
kHiddenLineDrawingViewStyle        = 32257  # 숨은선 점선
kHiddenLineRemovedDrawingViewStyle = 32258
kShadedDrawingViewStyle            = 32259
kHorizontalDimensionType           = 60162
kVerticalDimensionType             = 60163
kMillimeterLengthUnits             = 11269
kA3DrawingSheetSize                = 9996   # 42×29.7cm
```

상수는 위 「상수 (실측)」 블록을 스크립트 맨 위에 그대로 붙여 이름으로 쓴다. `win32.constants.k*` 는 쓰지 않는다 — gen_py 캐시가 있어야 존재해서, 캐시 없는 새 PC 에서는 첫 `CastTo` 전에 쓰면 `AttributeError` 다(`launch()` 의 `Dispatch` 는 캐시를 만들지 않는다). 블록에 없는 값은 추측한 정수로 쓰지 말고 CHM 열거형 페이지에서 읽는다. `kRearViewOrientation` 이라는 상수는 없다.

## Drawing 시작 패턴

```python
draw_doc = app.Documents.Add(kDrawingDocumentObject, TEMPLATE_IDW)
dd = CastTo(draw_doc, "DrawingDocument")
draw_doc.UnitsOfMeasure.LengthUnits = kMillimeterLengthUnits   # 실패 시 dd 로 재시도. try 로 감싸지 않는다
sheet = dd.ActiveSheet
sheet.Size = kA3DrawingSheetSize
time.sleep(1)
W, H = sheet.Width, sheet.Height  # 42.0, 29.7
dvs = sheet.DrawingViews
gd  = sheet.DrawingDimensions.GeneralDimensions
gn  = sheet.DrawingNotes.GeneralNotes
```

iProperty:
```python
ps = draw_doc.PropertySets
ps.Item("Summary Information").Item("Title").Value  = "My Part"
ps.Item("Summary Information").Item("Author").Value = "<작성자 이름>"
ps.Item("Inventor Summary Information").Item("Revision Number").Value = "A"   # "Design Tracking Properties" 에는 없음
```

## A3 좌표계 & 안전 영역

```
A3: W=42, H=29.7 cm. Y-up (y=0 하단)
Title block top ≈ y=7. 충돌 검사용 bbox = (0.0, 42.0, 0.0, 4.5)
Safe zone: X=[2, 40], Y=[9, 28.5]
Dim line: 뷰 바깥 1.2cm 이상
스펙 노트 앵커 y1 ≤ 14 (텍스트 y=9.5 까지 흐름)
ISO VIEW scale=1.2 → W≈10, H≈8. scale=1.5 → W=12.4, 우측 이탈 위험
```

## 뷰 생성

```python
vf = dvs.AddBaseView(model_doc, tg.CreatePoint2d(cx, cy), scale,
                     kRightViewOrientation, kHiddenLineDrawingViewStyle, "")
vW, vH = vf.Width, vf.Height   # AddBaseView 직후 읽기 가능
time.sleep(6)                  # 모든 뷰 추가 후 렌더 대기 — 없으면 GetDrawingCurves 1개만 반환
```

뷰 스타일: SIDE(profile) = `kHiddenLineDrawingViewStyle` (bore 점선) / END(circles), ISO = `kHiddenLineRemovedDrawingViewStyle`.

`GetDrawingCurves` 의 좌표(`StartPoint`·`EndPoint`·`CenterPoint`·`Evaluator2D`)는 시트 좌표 cm 다 — 뷰 위치와 SCALE 이 들어 있고 `CreateGeometryIntent` 힌트 점과 같은 공간이다. 전원·edge-on 원은 `StartPoint`/`EndPoint` 가 None 이라 박스는 `RangeBox` 로 읽는다:

```python
def get_bounds(c):   # (x_min, y_min, x_max, y_max), 시트 cm
    rb = c.Evaluator2D.RangeBox
    return (rb.MinPoint.X, rb.MinPoint.Y, rb.MaxPoint.X, rb.MaxPoint.Y)
```

## IAM/STEP 열기

```python
app.SilentOperation = True                 # Open() 전. import dialog 억제
model_doc = app.Documents.Open(IAM_PATH)   # .iam 직접. .step Open → "Save As IAM" 모달로 블로킹
time.sleep(6)
```

## 스펙 노트 & 저장

```python
note = gn.AddByRectangle(tg.CreatePoint2d(2.0, 14.0), tg.CreatePoint2d(12.0, 9.5), "NOTE LINE1\nLINE2")  # Point1 = 노트 좌상단
note.TextStyle.FontSize = 0.25  # cm

draw_doc.SaveAs2(IDW_PATH, False)  # 주 문서. 다시 저장은 draw_doc.Save() — 같은 경로 SaveAs2 두 번째는 E_INVALIDARG
draw_doc.SaveAs2(PDF_PATH, True)   # copy

draw_doc.Close(True)   # SkipSave=True. False → dirty 시 저장 모달
part_doc.Close(True)
app.Quit()
```

- **PDF 로 저장할 도면의 노트는 ASCII 로 쓴다.** 노트에 한글이 있으면 PDF 저장 때 'Published with a warning(s)' 창(Font Tahoma for symbol … was replaced by font 맑은 고딕)이 떠서 `SaveAs2(pdf, True)`·TranslatorAddIn 모두 비대화형 세션이 멈춘다(PDF 파일은 창이 뜨기 전에 써진다). 제목란 iProperty 의 한글은 미확인
- `AddByRectangle` 의 사각형 폭으로는 줄이 바뀌지 않는다 — 줄바꿈은 `\n`. `AddFitted` 도 Point1 이 노트 좌상단
- `SaveAs2(pdf, True)` 와 TranslatorAddIn `SaveCopyAs` 는 같은 PDF 를 만든다(ASCII 노트, 바이트 동일)

PDF 검증:
```python
import fitz
fitz.open(PDF_PATH)[0].get_pixmap(matrix=fitz.Matrix(4,4)).save("verify.png")
```
