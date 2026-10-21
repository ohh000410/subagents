# SPEOS Sim — SensorIrradiance

```python
sens = SensorIrradiance.GetMethod("Create", System.Type.EmptyTypes).Invoke(None, None)
sens.Name = "Focal_Plane_Sensor"
sens.XStart = -25.0; sens.XEnd = 25.0; sens.YStart = -25.0; sens.YEnd = 25.0   # mm
sens.XNbSamples = 50; sens.YNbSamples = 50
sens.SensorTypeIndex = 1            # 0=Photometric(lx), 1=Radiometric(W/m²), 2=Spectral
sens.XMPTemplateFile = r"C:\path\to\template.xml"   # 자동 measure (speos_sim_xmp_template.md)
sens.Compute()
```

## writable 속성 (reflection)

```
XStart, XEnd, XNbSamples, XResolution, StepX, XIsMirrored
YStart, YEnd, YNbSamples, YResolution, StepY, YIsMirrored
OriginX, OriginY (float, mm), OriginXText, OriginYText          ← OriginZ 없음
IntegrationDirectionIsReversed (bool)
IlluminanceType(Index), SensorType(Index), RayFileType(Index), LayerType(Index), SCAFilteringMode(Index)
MaximumNbOfSequence, DefineSequencePer, SortSequencesPer, IncidentAnglesSampling
WavelengthStart, WavelengthEnd, WavelengthNbSamples, WavelengthResolution
XDirectionReverse, YDirectionReverse, ShowGrid, DimensionFromFile, DisplayPropertiesFromFile
XMPTemplateFile, Name, Visible. ApplyPreset(String), ExportToPreset(String)
```

- `OriginZ` 없음. `OriginPoint`(nested, get-only) 의 IDocObject 경로 미발견 → z 는 API 로 이동 불가. 대안: body 를 z 이동해 상대 배치, 또는 GUI record
- `IntegrationDirectionIsReversed=True` → -z 에서 +z 로 오는 ray 통합 (xmp `Integration direction: -0 -0 -1`). False(default) → +z 에서 -z
- emitter face normal 은 생성 방법에 따라 +z/-z → `face.Shape.Geometry.Frame.DirZ` 실측 필수. SketchLine + PlanarBody emitter = +z. normal 이 sensor 를 향해야 flux 발생 (z 평면 분리는 문제 없음. z=-50 emitter → z=0 sensor flux 0.967 W)
- "Body inside Irradiance sensor" warning (sensor 와 body 같은 평면): sensor z 0.5 mm 띄움 / `sens.OutputFaces.Set([target_face])` / headless 자동 dismiss
- 설정 변경 후 `Compute()` 재등록
