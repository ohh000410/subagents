# SpaceClaim — Geometry API 함정

| 잘못 | 올바름 |
|---|---|
| `RevolveEdges.Execute(sel, Selection.Create(line), ...)` → "expected Line got Selection" | `Line.Create(Point.Origin, Direction.DirZ)` 직접 |
| RevolveEdges 인자 4개 → "ISelection got float" | 인자 6개 (`spaceclaim_sketch_revolve.md`) |
| `SketchSpline`/`SketchParabola`/`SketchConic` | NA → NurbsCurve + DesignCurve (`spaceclaim_nurbs.md`) |
| `SplitBody.Execute(body_sel, plane, None)` AttributeError | `SplitBody.ByCutter(body_sel, plane, None)` → True |
| `body.GetBoundingBox(Matrix.Identity)` AttributeError | `body.GetTessellationBoundingBox(Matrix.Identity, True)`, `.MinCorner.Z * 1000` (m → mm) |
| `Move.Execute(body_sel, xform)` AttributeError | `body.Transform(Matrix.CreateTranslation(Vector.Create(MM(dx), MM(dy), MM(dz))))` 또는 `Move.Translate(ISelection, Vector, MoveOptions, ICommandInfo)` |
| `DatumPoint.Create(point)` / `(root, point)` | `DatumPoint.Create(root, "name", point)` 3 args. `.CreatedPoint` 없음 → IDocObject 추출 불가 |
| `DesignFace.GetTessellationBoundingBox` | 없음. face 의 z 범위 = `face.Edges` 각각의 `edge.Shape.GetBoundingBox(Matrix.Identity, True)` 를 모은다(수평 face 는 폭 ≈ 0, 옆면은 두께만큼 — box body 실측). radius 는 body bbox xy 로 근사 |
| `edge.Length` AttributeError | `edge.Shape.Length * 1000` (Modeler.Edge, m) |
| `face.Shape.Geometry.Normal` AttributeError | `face.Shape.Geometry.Frame.DirZ` — 바탕 평면의 법선이라 바닥 face 도 +z 로 나온다. 바깥 법선 = `DirZ × (−1 if face.Shape.IsReversed else 1)` |
| Python list → `NurbsCurve.CreateThroughPoints` | `from System.Collections.Generic import List; points = List[Point](); points.Add(...)` |
| `PolylineOptions()` NameError / `GetPolyline(None)` / `GetPolyline(0.01)` | GetPolyline 불가 → `Length` + `GetBoundingBox(Matrix.Identity, True)` |
| `Window.ActiveWindow.Export(WindowExportFormat.Png, path)` | Student license "not licensed". `Window.Active` 없음. 대안: `GetTessellation` 으로 면별 삼각형을 덤프해 matplotlib 로 그린다 |
| `PullFaces` NameError | `ExtrudeFaces.Execute` |
| `ExtrudeFaces.Execute(face_sel, MM(50), ExtrudeType.None, None)` → "expected Direction, got float" | `(face_sel, Direction.DirZ, MM(50), ExtrudeFaceOptions(), None)` |
| `Body.CreateBox` → Student v261 에서 AttributeError | 사각형 스케치 + `ExtrudeFaces.Execute`(가운데 맞춘 40×30×10 mm 실측) |
| `DocumentNew` 없음 | headless 는 빈 문서가 이미 열려 있다 → `GetRootPart()` 를 바로 쓴다 |
| `Combine.Execute` 로 빼기 | Combine 은 Merge·Intersect·RemoveRegions 만 — 빼기는 `ExtrudeFaces` + `ExtrudeType.Cut` |
| `DesignBody.IsVoid` 없음 | body 유효성 = `len(body.Faces) > 0` |
| `GetTessellation` 결과의 `kv.Key` 로 면 번호 매핑 | 믿을 수 없다 → 면마다 `List[Modeler.Face]()` 에 `body.Faces[i].Shape` 하나씩 넣어 따로 호출 |

## Sketch 좌표 vs Global

`SketchCircle`/`SketchLine` = sketch plane 2D (`Point2D`). `Point.Create(MM(x), MM(y), MM(z))` = global 3D (DesignCurve 등). XZ plane: sketch X = global X, sketch Y = global Z.

## SPEOS paraboloid 자르기

- top cut (z=30) → Size 80: corner 4 + frustum 1 = 5 조각. 삭제 `max_z > CUT_Z + 0.5`
- bottom cut 후 z<0 조각 max_z ≈ 0.00 (tessellation) → 삭제 조건 `max_z < BOT_Z + 0.5`
- `ParabolicSurface.Create()` 직후 focal = origin. `translate -Focal` 추가 → vertex 가 -2·Focal. translate 금지 (`spaceclaim_speos_addin_parabolic.md`)

## 동일 평면 복수 루프

같은 plane 에 사각형 루프 2개 연속 스케치 → compound face body 1개 → CUT "Extrude produced no result". 루프 1개씩 별도 스케치 → 별도 extrude.

## V홈 CUT (v261 실측)

- 꼭짓점 배치(상면과 같은 평면 피하기): apex = (xc, Z_top − depth), 위 두 점 = (xc ± (depth + over)·tanθ, Z_top + over), over = 0.05 mm
- 같은 평면에 홈 여러 개 = 홈마다 스케치 → `ViewHelper.SetViewMode(Solid)` → `ExtrudeFaces`(Cut) 를 차례로(10/10). 같은 sketch plane 을 다시 써도 된다. CUT 전에 body 가 하나 늘었는지(`len(bodies) == before + 1`), 그 face 가 1개인지(`len(tri.Faces) == 1`, compound 아님) 확인
- 직교 두 방향(20/20): Y홈 = `Frame(Point(0, −0.001 mm, 0), DirX, DirZ)` + extrude DirY, X홈 = `Frame(Point(−0.001 mm, 0, 0), DirY, DirZ)` + extrude DirX. plane 법선이 extrude 와 반대여도 Direction 을 명시하면 된다
- 교차 배열 N×N(개구폭 < 피치): faces = 5 + (N+1)² + 4N(N+1), triangles = 2 + 4(3N+2) + 2(N+1)² + 8N(N+1). N=10 실측 566 면·1252 삼각형
