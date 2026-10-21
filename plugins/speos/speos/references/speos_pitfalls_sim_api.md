# SPEOS SIM — 객체 API 함정

| 시도 | 결과 | 대안 |
|---|---|---|
| `mat.OrientedFaces.Set(...)` (Volumic default) | `Property 'OrientedFaces' is not defined in current state`. read `<read fail>` | Volumic + VOPType=None + `mat.VolumeGeometries.Set([body])` (= GUI "Volume and Surface"). `OpticalPropertiesTypeIndex = 1`(Surfacic) 은 inconsistent |
| `src.ExitanceReverse = True` | `not defined in current state` (`ExitanceVariable=True` 모드 한정) | `for child in src.EmissiveFaces: child.ReverseDirection = True` |
| sensor 평면 = body face 평면 | "Body inside Irradiance sensor" warning, inconsistent 가능 | sensor z 0.5 mm 띄움 / `sensor.OutputFaces` / headless 자동 dismiss |
| `SimulationSettings.Create()` 후 `MeshingStepValue` 변경 | sim 에 미적용 (임시 인스턴스) | `LocalMeshing` (body 별, 자동 적용) |
| `SensorIrradiance.OriginZ` | 없음. `OriginPoint` nested get-only, IDocObject 경로 미발견 | OriginX/Y 만 + Z=0 설계, body 이동, 또는 GUI record |
| `DesignFace.GetNormal()` | AttributeError | `face.Shape.Geometry.Frame.DirZ` (유일) |
| `face.Shape.NormalAt(Point)` | "Cannot import name Point" | 〃 |

emitter face normal 실측 (SketchLine + PlanarBody, z=-50, 100×100): +z. ReverseDirection=False → +z emit → sensor(z=0) flux 0.967 W / True → 0.000 W. normal 이 sensor 를 향해야 flux. 생성 방법에 따라 ±z → `Frame.DirZ` 실측 필수.
