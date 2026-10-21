# NurbsCurve / CurveSegment / DesignCurve

```python
from System.Collections.Generic import List
points = List[Point]()                                       # Python list 불가
for i in range(N): points.Add(Point.Create(MM(x_i), MM(y_i), MM(z_i)))
nurbs = NurbsCurve.CreateThroughPoints(False, points, 1.0e-9)   # (periodic, points, fitTolerance)
seg = CurveSegment.Create(nurbs)                             # ITrimmedCurve
dc = DesignCurve.Create(GetRootPart(), seg)
# → RevolveEdges (spaceclaim_sketch_revolve.md)
```

## NurbsCurve static

```
CreateFromControlPoints(NurbsData data, ControlPoint[] controlPoints)
CreateFromKnotPoints(Boolean periodic, IList<Point> points[, Nullable<Direction> startDerivative, Nullable<Direction> endDerivative])
CreateThroughPoints(Boolean periodic, IList<Point> points, Double fitTolerance[, Nullable<Direction> startDerivative, Nullable<Direction> endDerivative])
```

| 메서드 | 용도 | 정확도 |
|---|---|---|
| `CreateThroughPoints` | 점 통과 spline fit | interpolation. 1e-9 권장. 수학적 곡선 아님 (parabola 81점 → .scdocx 99.7 KB) |
| `CreateFromKnotPoints` | knot 통과 | 유사 |
| `CreateFromControlPoints` | NURBS control point 직접 | 정확 (parabola = 3 CP quadratic). `NurbsData`/`ControlPoint` namespace 미확인 |

## CurveSegment static

```
Create(Curve curve, Interval bounds) / Create(Curve curve) / Create(Point start, Point end)
CreateArc(Point center, Point start, Point end, Direction axis)
CreateHelix(Line axis, Point startPoint, Double height, Double pitch, Double taperAngle, CircularSense sense)
```

## DesignCurve.Create

```
Create(IDesignCurveParentMaster parent, ITrimmedCurve shape[, Nullable<Boolean> defaultVisibility])
```
`GetRootPart()` = `IDesignCurveParentMaster`.
