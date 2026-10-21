# SPEOS Sim — SensorIntensity (각도 분포)

```python
SensorIntensity = asm_sim.GetType("App.Automation.SIM.SensorIntensity")
sens_int = SensorIntensity.GetMethod("Create", System.Type.EmptyTypes).Invoke(None, None)
sens_int.Name = "Ref_Intensity_Sensor"
sens_int.XStart = -180.0; sens_int.XEnd = 180.0; sens_int.XNbSamples = 180   # phi (추정)
sens_int.YStart = 0.0;    sens_int.YEnd = 90.0;   sens_int.YNbSamples = 45    # theta (추정)
sens_int.SensorTypeIndex = 1        # Radiometric
sens_int.Compute()
```
설정 됨: XStart/XEnd/XNbSamples/YStart/YEnd/YNbSamples/SensorTypeIndex. 설정 안 됨: PhiStart, PhiEnd, ThetaStart, ThetaEnd, PhiNbSamples, NbThetaSamples.

## Report.html (SensorIrradiance 와 다름)

`<li>Flux: X lm</li>` (photometric) — Radiant W 없음. W 는 전역:
1. `Generated power</th>\s*<td>([\d.]+)\s*Watt</td>`
2. `Power emitted by the sources</th>\s*<td>([\d.]+)\s*Watt</td>`
3. `Flux value.*?>([\d.]+)\s*W;`

`<td>Intensity type</td><td>Lambertian</td>` — IntensityTotalAngle=180 → Lambertian 자동 기록.

## .xmp

`YYZOPTIS - newXMP file v33` + zlib 블록 42개. 블록[0](offset 56) = 메타데이터, 블록[3~](offset 694~) = angular map (파싱 미검증). 이론 계산 또는 GUI 추출.

Lambertian, 총 1.0 W: I0 = 1/π = 0.31831 W/sr, I(θ) = I0·cos θ. 8280행 = theta 0–90 간격 2 (46) × phi 0–358 간격 2 (180). I(80°) = 0.05527.
