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
| `asm.GetType("App.Automation.SIM.EnumSOPType")` | None — enum 은 소유 클래스 안에 있음(`App.Automation.SIM.Material+EnumSOPType`) | `ownerType.GetProperty("SOPType").PropertyType` |
| `EnumFluxType` 의 "Radiant" | 없음. 이름은 LuminousFlux·RadiantFlux·LuminousIntensity. `EnumSOPType` = Mirror·OpticalPolished·Library·Plugin·Appearance, `EnumSensorType` = Photometric·Radiometric·Colorimetric·Spectral | index 관례(SOP 0 = Mirror, Flux 1 = Radiant, Sensor 1 = Radiometric)는 v252·v261 같음 |
| `len(list(sim.Geometries))` | 끝나지 않음(코어 하나 100 %, 메모리 2 GB 넘게 증가). collection 이 Python iterator 를 내놓지 않아 정수 인덱스로 끝없이 돎. `SimulationDirectSources` 는 `GetEnumerator` 도 없음 | SPEOS child collection 은 모두 `.Count`·`Item` 으로 읽음. `list()` 금지 |

emitter face normal 실측 (SketchLine + PlanarBody, z=-50, 100×100): +z. ReverseDirection=False → +z emit → sensor(z=0) flux 0.967 W / True → 0.000 W. normal 이 sensor 를 향해야 flux. 생성 방법에 따라 ±z → `Frame.DirZ` 실측 필수.

`Frame.DirZ` 는 face 의 바깥 법선이 아니라 바탕 평면의 법선 — 아래쪽(−z) 바닥 face 도 +z 로 나옴. 바깥 법선 = `DirZ × (−1 if face.Shape.IsReversed else 1)`. 위·아래 face 는 법선 대신 z 로 가름: `face.Edges` 각각의 `edge.Shape.GetBoundingBox(Matrix.Identity, True)` 를 모아 z 범위를 보면 수평 face 는 폭 ≈ 0, 옆면은 body 두께만큼. 수평 face 중 z 가 큰 쪽이 top(box body 실측).
