# SPEOS Sim — 광학 (Material · SourceSurface)

## Material

GUI "Volume and Surface" = `OpticalPropertiesType=Volumic` + `VOPType=None` + `SOPType=Mirror` + `VolumeGeometries` 에 body 등록 (별도 enum 아님).

```python
mat = Material.GetMethod("Create", System.Type.EmptyTypes).Invoke(None, None)
mat.Name = "Paraboloid_Mirror"
# OpticalPropertiesType: Volumic(0, default) / Surfacic(1). VOPType default None(Idx 3)
mat.SOPTypeIndex = 0                # 0=Mirror, 1=OpticalPolished(transparent, ray 통과)
mat.SOPReflectance = 95.0           # %
mat.VolumeGeometries.Set(Selection.Create([body]).Items)   # body 단위
mat.Compute()
```
`Surfacic`(Index 1) 로 바꾸면 `OrientedFaces` 활성화되지만 sim 결과 inconsistent (Ansys: surface body 는 Volumic + VOP=None). Volumic 에서 `OrientedFaces` read → `<read fail>`.

## SourceSurface

```python
src = SourceSurface.GetMethod("Create", System.Type.EmptyTypes).Invoke(None, None)
src.Name = "Source_Plane_Surface"
src.EmissiveFaces.Set(Selection.Create(faces).Items)
for child in src.EmissiveFaces: child.ReverseDirection = True   # OrientedFace.ReverseDirection = face normal 뒤집기
src.FluxTypeIndex = 1               # 0=Luminous(lm), 1=Radiant(W), 2=Intensity
src.FluxValueRadiant = 1.0          # W (Luminous: src.FluxValueLuminous = 683.0)
src.IntensityTotalAngle = 0.0       # 0 = collimated. 180 (default) = Lambertian. IntensityType default Lambertian
# SpectrumType default Monochromatic, SpectrumValueWavelength = 555nm
src.Compute()
```
OrientedFace: `Add(OrientedFace)`, R/W `ReverseDirection`, `Face`(nested), static `Create()`.
`src.ExitanceReverse = True` → "in its current state" 에러 (`ExitanceVariable=True` 모드 한정). 방향 뒤집기 = EmissiveFaces child 의 ReverseDirection.
