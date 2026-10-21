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
| `DesignFace.GetTessellationBoundingBox` | 없음. face bbox 는 reflection 필요(미검증). radius 는 body bbox xy 로 근사 |
| `edge.Length` AttributeError | `edge.Shape.Length * 1000` (Modeler.Edge, m) |
| `face.Shape.Geometry.Normal` AttributeError | `face.Shape.Geometry.Frame.DirZ` |
| Python list → `NurbsCurve.CreateThroughPoints` | `from System.Collections.Generic import List; points = List[Point](); points.Add(...)` |
| `PolylineOptions()` NameError / `GetPolyline(None)` / `GetPolyline(0.01)` | GetPolyline 불가 → `Length` + `GetBoundingBox(Matrix.Identity, True)` |
| `Window.ActiveWindow.Export(WindowExportFormat.Png, path)` | Student license "not licensed". `Window.Active` 없음. 수동 스크린샷 |
| `PullFaces` NameError | `ExtrudeFaces.Execute` |
| `ExtrudeFaces.Execute(face_sel, MM(50), ExtrudeType.None, None)` → "expected Direction, got float" | `(face_sel, Direction.DirZ, MM(50), ExtrudeFaceOptions(), None)` |

## Sketch 좌표 vs Global

`SketchCircle`/`SketchLine` = sketch plane 2D (`Point2D`). `Point.Create(MM(x), MM(y), MM(z))` = global 3D (DesignCurve 등). XZ plane: sketch X = global X, sketch Y = global Z.

## SPEOS paraboloid 자르기

- top cut (z=30) → Size 80: corner 4 + frustum 1 = 5 조각. 삭제 `max_z > CUT_Z + 0.5`
- bottom cut 후 z<0 조각 max_z ≈ 0.00 (tessellation) → 삭제 조건 `max_z < BOT_Z + 0.5`
- `ParabolicSurface.Create()` 직후 focal = origin. `translate -Focal` 추가 → vertex 가 -2·Focal. translate 금지 (`spaceclaim_speos_addin_parabolic.md`)

## 동일 평면 복수 루프

같은 plane 에 사각형 루프 2개 연속 스케치 → compound face body 1개 → CUT "Extrude produced no result". 루프 1개씩 별도 스케치 → 별도 extrude.
