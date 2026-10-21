# SPEOS addin (OSD) — ParabolicSurface

SPEOS plug-in 모드(모드 2) 만.

| Namespace | 용도 | 파일 |
|---|---|---|
| `SpeosDes.*` (= `App.Automation.OSD.*`) | Optical Shape Designer geometry — ParabolicSurface, FreeformLens, ProjectionLens | 이 파일 |
| `App.Automation.SIM.*` | material·source·sensor·simulation·LocalMeshing | `speos_sim_*.md` |

## 기본 패턴

```python
ps = SpeosDes.ParabolicSurface.Create()
ps.Name = "Paraboloid"
ps.Focal = 10.0          # mm
ps.Size = 80.0           # mm, 직경 (R_top × 2)
ps.Axis.Set(Selection.Create(GetRootPart().CoordinateSystems[0].Axes[2]).Items)   # Z (X=0, Y=1, Z=2). default X
ps.Compute()             # property 변경 후 매번. 없으면 surface 미생성
DocumentSave.Execute(OUT_PATH)
```

## Property

| Property | 타입 | Default | 의미 |
|---|---|---|---|
| `Focal` / `FocalText` | Double / String | 20 mm | 초점 거리 |
| `Size` / `SizeText` | Double / String | 100 mm | 직경 |
| `BuildType` / `BuildTypeIndex` | EnumBuildType / Int32 | `WithFocalnSize` / 0 | `With Focal Length and Size` / `With Passing Point` |
| `FocalOut` / `FocalOutText` | Double / String | - | Build Type 의존 |
| `PassingPoint` | nested | - | 통과 강제 점 |
| `OriginPoint` | nested ParabolicSurfaceOriginPoint | world origin | `Set(IDocObject)` — DatumPoint IDocObject 경로 미확인 → 사용 불가 |
| `Axis` | nested ParabolicSurfaceAxis | X | 광축. `.Set(Selection.Items)` |
| `OrientationAxis` | nested | Y | axis 수직 (Set 패턴 미검증) |
| `ReverseOpticalAxis` | Boolean | False | |
| `Name`, `Visible` | | | |

Read-only: `Subject`, `Occurrence`, `StatusInfo`(에러 메시지), `IsUpToDate`.

Method: `Create()`, `Create(Object parent)`, `Find(String)`, `Clone()`, `CopyTo(IApiSpeosDocObject)`, `Delete()`, `Compute()`, `ApplyPreset(String)`, `ExportToPreset(String)`, `PublishParameter(String, Boolean)`.

## 기존 surface 잡기

```python
ps = SpeosDes.ParabolicSurface.Find("Parabolic Surface.1")
ps = SpeosDes.ParabolicSurface(Selection.Create(GetRootPart().GetChildren[ICustomObject]()[0]).Items[0])
```

## focal = origin 규약

`Create()` 직후 focal = (0,0,0), vertex = (0,0,-Focal) (Axis=Z). 추가 translate 금지 — `translate -Focal` 하면 vertex 가 -2·Focal.
표면: `z = r²/(4·Focal)`, `r² = 4·Focal·(z + Focal)`. Focal=10: z=0 → r=20 (둘레 125.664) / z=30 → r=40 (251.327).

## Cut 후 조각 삭제

- top cut: `max_z > CUT_Z + 0.5`. Size 80 → 5 조각 (corner 4 + frustum), Size 100 → 2 조각
- bottom cut (z=0): z<0 조각 max_z ≈ 0.00 → `max_z < BOT_Z + 0.5`

## 다른 addin button (미검증 추정)

`SpeosDes.PolyEllipsoidalReflector.Create()`, `SpeosDes.ProjectionLens.Create()`, `SpeosDes.FreeformLens.Create()` → record 로 확인 (`speos_record_workflow.md`).
