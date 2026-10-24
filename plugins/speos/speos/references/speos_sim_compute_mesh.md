# SPEOS Sim — Compute · Meshing · Triangle 수

## SimulationDirect

```python
sim = SimulationDirect.GetMethod("Create", System.Type.EmptyTypes).Invoke(None, None)
sim.Name = "Direct_Sim"
sim.NbRays = 10000                                          # default 200000
sim.Geometries.Set(Selection.Create(bodies).Items)
sim.Sources.Set(Selection.Create([src.Subject]).Items)      # .Subject
sim.Sensors.Set(Selection.Create([sens.Subject]).Items)
sim.Compute()
print(sim.StatusInfo)     # 정상 = "". 거부(Student 한도 등)는 예외 없이 여기만
print(sim.IsUpToDate)     # True = 완료
```

writable: `Geometries, RayFileType(Index), Sources, Sensors, UsesLXP, LXPMaxPath(Text), HasRayNbLimit, NbRays(Text), HasDurationLimit, DurationLimit(Text), AmbientMaterial, Name, Visible`. seed 속성 없음 — SC 프로세스를 새로 띄울 때마다 내부 seed 변경 → 독립 MC 샘플.

결과 위치 = **DocumentSave 한 .scdocx 폴더** 기준: `SPEOS output files/<base>/<sim>.<sensor>.xmp`, `.xml`(template 시), `<sim>.Report.html`. 새 위치 → DocumentSave 먼저 → Compute.
`sim.Export(out_dir)` = scene 만 (`.speos`), 결과 아님.

## LocalMeshing — Student triangle 한도 32k

```
StatusInfo: "Simulation not supported with student license  The simulation includes 54,615 triangles..."
```
face 한도(300) 는 LocalMeshing 으로 못 풂 → `speos_pitfalls_sim_workflow.md`.

```python
lm = LocalMeshing.GetMethod("Create", System.Type.EmptyTypes).Invoke(None, None)
lm.Name = "Paraboloid_Fine_Mesh"
lm.MeshingSagLengthValue = 0.1                 # default 0.005 mm
lm.MeshingStepValueProportionalToBody = 50.0   # default 10
lm.MeshingAngle = 15.0                         # default 15°. angle=1 은 sag 무관 32k 초과. ≥5 정상
lm.Geometries.Set(Selection.Create([curve_body]).Items)
lm.Compute()
```
곡면 body 에만 적용. 평면 source = default. `EnumMeshingSagMode/StepMode`: ProportionalFace=0, Fixed=1, ProportionalBody=2.
`SimulationSettings.Create()` 변경은 sim 에 적용되지 않음 → LocalMeshing.

## Triangle 수 = NbRays=1 Compute → Report.html

객체에 count 속성 없음.
```python
import re, codecs
html = codecs.open(report_path, "r", "utf-8", "replace").read()
m = re.search(r'Number of triangles[^<]*</th>\s*<td[^>]*>([\d,]+)</td>', html)
triangle_count = int(m.group(1).replace(",", ""))
```
첫 기동 30 s + NbRays=1 ~15 s ≈ 45 s/case.

## Report.html Flux 파싱 (template 없을 때)

```python
m = re.search(r'<li>Flux:\s*([\d.]+)\s*W</li>', html)                                    # 1. sensor section
m = re.search(r'Radiated power[^<]*</th>\s*<td[^>]*>([\d.]+)\s*Watt</td>', html)         # 2. Power Report (단위 Watt)
m = re.search(r'Generated power[^<]*</th>\s*<td[^>]*>([\d.]+)\s*Watt</td>', html)        # 3
all_vals = re.findall(r'<td[^>]*>([\d.]+)\s*W(?:att)?</td>', html)                       # fallback
```
`<td class="value">` 없음 — plain `<td>`.

## 이름 충돌

기존 sim 저장 .scdocx 를 DocumentOpen → 같은 이름 `Create()` → `The name 'Paraboloid_Mesh' is already in use`. 새 이름(`_TC` 등) 으로 Create → Compute.
