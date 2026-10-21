# SPEOS Sim — 핵심 (namespace · import · 작업 흐름)

`App.Automation.SIM` 자동화 배선. geometry(`SpeosDes.*`) → `speos_addin_parabolic.md`. SPEOS plug-in 모드(`speos_launch_modes.md` 모드 2) 헤드리스.
객체별: `speos_sim_optics.md`(Material/Source) · `speos_sim_sensor_irradiance.md` · `speos_sim_sensor_intensity.md` · `speos_sim_compute_mesh.md` · `speos_sim_xmp_template.md` · `speos_sim_sweep.md`

| Namespace | 용도 | 클래스 |
|---|---|---|
| `SpeosDes.*` | Optical Shape Designer geometry | `ParabolicSurface`, `FreeformLens`, `ProjectionLens`, `CircularLens`, `HoneycombLens` |
| `App.Automation.SIM.*` | 광학·source·sensor·simulation | `Material`, `SourceSurface`, `SensorIrradiance`, `SensorIntensity`, `SimulationDirect`, `LocalMeshing`, `SimulationSettings` |

## import (IronPython)

```python
import System
asm_sim = None
for a in System.AppDomain.CurrentDomain.GetAssemblies():
    if a.GetName().Name == "App.Automation.SIM": asm_sim = a; break
Material         = asm_sim.GetType("App.Automation.SIM.Material")
SourceSurface    = asm_sim.GetType("App.Automation.SIM.SourceSurface")
SensorIrradiance = asm_sim.GetType("App.Automation.SIM.SensorIrradiance")
SimulationDirect = asm_sim.GetType("App.Automation.SIM.SimulationDirect")
LocalMeshing     = asm_sim.GetType("App.Automation.SIM.LocalMeshing")
inst = Material.GetMethod("Create", System.Type.EmptyTypes).Invoke(None, None)   # parameterless Create = reflection invoke
```

## 전체 작업 흐름

```
0. import
1. DocumentOpen.Execute(input_scdocx)
2. body 식별
3. LocalMeshing — 곡면 body
4. Material — 곡면(Mirror, R=95%), source plane(OpticalPolished)
5. SourceSurface — face + ReverseDirection + Radiant + IntensityAngle
6. SensorIrradiance — Radiometric, XMPTemplateFile
7. SimulationDirect — Geometries/Sources/Sensors + NbRays + Compute
8. DocumentSave.Execute(out_scdocx)
→ <out_scdocx 폴더>/SPEOS output files/<base>/ .xmp/.xml/.html
```
cold-to-result ~30~40초 (launch + 10k rays). headless 에서 GUI dialog("Body inside sensor" 등) 자동 dismiss.

## DocumentOpen.Execute — 1-arg 만

```python
DocumentOpen.Execute(path)          # OK
DocumentOpen.Execute(path, None)    # TypeError: Multiple targets could match: Execute(str, ImportOptions) / (str, str) / (str, IScriptObject[IFileSettings])
```

## config.json — utf-8 명시

```python
import codecs
with codecs.open(CONFIG, "r", "utf-8") as f: cfg = json.load(f)   # 기본 open() = cp949
```
