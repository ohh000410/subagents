# SpaceClaim Sketch + Revolve + Extrude

## Sketch plane

```python
ViewHelper.SetSketchPlane(Plane.PlaneXY, None)   # PlaneYZ, PlaneZX
plane = Plane.Create(Frame.Create(Point.Origin, Direction.DirX, Direction.DirZ))   # sketch X = global X, sketch Y = global Z
ViewHelper.SetSketchPlane(plane, None)
```
YZ(normal X): sketch_X = global_Y, sketch_Y = global_Z. XZ(normal Y): sketch_X = global_X, sketch_Y = global_Z.

## Sketch primitive

```python
SketchCircle.Create(Point2D.Create(MM(0), MM(0)), MM(10))
SketchLine.Create(Point2D.Create(MM(0), MM(0)), Point2D.Create(MM(10), MM(0)))
```
`SketchSpline`, `SketchPolyline`, `SketchParabola`, `SketchConic` NA (Scripting wrapper 없음) → NurbsCurve (`spaceclaim_nurbs.md`). `SketchRectangle` 미검증 → SketchLine ×4.

## Sketch 종료 → body

```python
ViewHelper.SetViewMode(InteractionMode.Solid, None)
```
닫힌 loop → planar surface body. 열린 polyline → DesignCurve (revolve 용).

## 닫힌 루프 사각형 (offset 평면)

```python
origin_z50 = Point.Create(MM(0), MM(0), MM(50))
plane_z50 = Plane.Create(Frame.Create(origin_z50, Direction.DirX, Direction.DirY))
ViewHelper.SetSketchPlane(plane_z50, None)
p_bl, p_br, p_tr, p_tl = Point2D.Create(MM(-40), MM(-100)), Point2D.Create(MM(40), MM(-100)), Point2D.Create(MM(40), MM(100)), Point2D.Create(MM(-40), MM(100))
SketchLine.Create(p_bl, p_br); SketchLine.Create(p_br, p_tr); SketchLine.Create(p_tr, p_tl); SketchLine.Create(p_tl, p_bl)
ViewHelper.SetViewMode(InteractionMode.Solid, None)
# 결과: face_count=1, bbox z=[50,50], x=[-40,40], y=[-100,100]
```
같은 plane 에 루프 2개 연속 스케치 → 1개 compound face body 로 병합 → CUT extrude "Extrude produced no result". 루프 1개씩 별도 스케치·extrude.

## RevolveEdges.Execute

```
RevolveEdgesResult Execute(ISelection selectObject, Line revolveAxis, Double angle, Boolean symmetric, ExtrudeType extrudeType, ICommandInfo info)   # 6 args
RevolveEdgesResult Execute(ISelection selectObject, Line revolveAxis, ISelection upToEntity, ExtrudeType extrudeType, ICommandInfo info)         # 5 args, to-entity
```

```python
sel_edges = Selection.Create(GetRootPart().Curves)
axis_line = Line.Create(Point.Origin, Direction.DirZ)   # Line 직접. Selection wrap → "expected Line got Selection". DatumLine 불필요
result = RevolveEdges.Execute(sel_edges, axis_line, DEG(360), False, getattr(ExtrudeType, "None"), None)
# ExtrudeType.None = 새 body / Add = 기존에 추가 / Cut = 빼기. 4 args → "ISelection got float"
```

## RevolveFaces.Execute (인자 5개)

```
RevolveCommandResult Execute(ISelection selectObject, Line axis, Double angle, RevolveFaceOptions options, ICommandInfo info)
```
```python
options = RevolveFaceOptions(); options.ExtrudeType = getattr(ExtrudeType, "None")
result = RevolveFaces.Execute(face_sel, axis_line, DEG(360), options, None)
```

## ExtrudeFaces.Execute

```python
ViewHelper.SetSketchPlane(plane, None)
SketchLine.Create(p00, p10); ...                              # 닫힌 루프
ViewHelper.SetViewMode(InteractionMode.Solid, None)
body = GetRootPart().Bodies[len(GetRootPart().Bodies) - 1]   # 최신 body
face_sel = Selection.Create(body.Faces[0])
opt = ExtrudeFaceOptions(); opt.ExtrudeType = getattr(ExtrudeType, "Cut")   # 또는 "None" = JOIN
result = ExtrudeFaces.Execute(face_sel, Direction.DirZ, MM(50), opt, None)   # (selection, direction, distance, options, info). direction 누락 → "expected Direction, got float"
ExtrudeFaces.Execute(face_sel, Direction.Create(-1.0, 0.0, 0.0), MM(4), opt, None)   # 음수 방향
```
`PullFaces` 없음. 스케치 평면이 box face 와 동일하면 흡수 → `MM(-0.001)` offset. through-hole CUT 은 진입·이탈 overshoot ≥ 0.05 mm.

## Matrix.CreateRotation — body 회전

```python
import math
rotation_matrix = Matrix.CreateRotation(Line.Create(Point.Origin, Direction.DirX), 30.0 * math.pi / 180.0)   # radians
body.Transform(rotation_matrix)   # Void
```
검증: plane z=60, 80×200 → X축 30° → y=[-116.603, 56.603], z=[1.962, 101.962] (이론 오차 <0.003 mm). 오른손 법칙.
Matrix static: `CreateRotation(Line, Double)`, `CreateMapping(Frame)`, `get_HasRotation()`, `get_Rotation()`, `TryGetRotation(Line&, Double&)`.

## Face mesh 직접 push (PySpeos)

```python
face = body.create_face(name="top")
face.vertices = [x1,y1,z1, ...]; face.facets = [i1,j1,k1, ...]; face.normals = [nx1,ny1,nz1, ...]
root.commit()   # face.commit() 호출 금지
```
mesh body (CAD geometry 아님). .scdocx 저장 가능.
