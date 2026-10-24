# Body Operations + Edge + Measurements (모든 모드)

## SplitBody.ByCutter

```python
body_sel = Selection.Create(list(GetRootPart().GetBodies()))
split_plane = Plane.Create(Frame.Create(Point.Origin, Direction.DirX, Direction.DirY))   # z=0
result = SplitBody.ByCutter(body_sel, split_plane, None)   # True
```
`SplitBody.Execute` 없음. overload:
```
ByCutter(ISelection bodySelection, Plane plane, ICommandInfo info)
ByCutter(ISelection bodySelection, ISelection toolFaces, Boolean extendSurfaces, ICommandInfo info)
ByCutter(ISelection bodySelection, ISelection slicer, ICommandInfo info)
```

## bbox / Delete

```python
bb = body.GetTessellationBoundingBox(Matrix.Identity, True)   # GetBoundingBox 없음
min_z, max_z = bb.MinCorner.Z * 1000, bb.MaxCorner.Z * 1000   # m → mm
Delete.Execute(Selection.Create(bodies_to_delete))             # Void
```

## DocumentSave / DocumentOpen

```python
DocumentSave.Execute(r"C:\...\<name>.scdocx")   # SPEOS feature 포함. 일반 모드에서 열면 보이지만 편집 불가
DocumentOpen.Execute(r"C:\...\<name>.scdocx")   # 헤드리스 OK. load 후 SketchLine + SetViewMode 체인 가능
root = GetRootPart(); bodies = list(root.GetBodies())
```

확장자를 `.step` 으로 주면 `DocumentSave.Execute` 가 STEP AP214(HOOPS Exchange)로 내보냄 — 별도 export API 필요 없음(scdocx 238 KB → step 234 KB).

## DesignEdge / Modeler.Edge

`DesignEdge.Shape` → `Modeler.Edge`. `.Parent` → DesignBody. `.Faces` → ICollection.

```python
edge_shape = design_edge.Shape
edge_shape.Length        # m. DesignEdge.Length 없음
edge_shape.Geometry      # Curve
edge_shape.StartPoint, edge_shape.EndPoint, edge_shape.Bounds, edge_shape.IsSmooth, edge_shape.IsConcave
edge_shape.GetBoundingBox(Matrix.Identity, True)   # Box
edge_shape.GetPolyline(PolylineOptions)            # IronPython 불가
```

```python
for edge in list(body.Edges): length_mm = edge.Shape.Length * 1000
bb = edge.Shape.GetBoundingBox(Matrix.Identity, True)
r_bbox = max(abs(bb.MinCorner.X), abs(bb.MaxCorner.X), abs(bb.MinCorner.Y), abs(bb.MaxCorner.Y)) * 1000   # 원형 edge ≈ r. z=0 edge 에서 28.28 오측 사례 (tessellation)
z_level = bb.MinCorner.Z * 1000
```

## Window.Export PNG

`Window.ActiveWindow.Export(WindowExportFormat.Png, path)` → Student license "not licensed". `Window.Active` 없음. WindowExportFormat: AutoCadDwg=0, Dxf=1, Bmp=2, Jpeg=3, Png=4, Tiff=5, Gif=6. 대안 = 수동 스크린샷.
