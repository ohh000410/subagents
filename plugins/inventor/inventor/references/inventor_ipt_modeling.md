# IPT 모델링 (Standard (mm).ipt)

## WorkPlanes / WorkAxes

```
WorkPlanes.Item(1) = YZ Plane   ← revolve 프로파일 스케치
WorkPlanes.Item(2) = XZ Plane
WorkPlanes.Item(3) = XY Plane
WorkAxes.Item(1) = X, Item(2) = Y, Item(3) = Z ← revolve 축
```

## Revolve

```python
part_doc = app.Documents.Add(kPartDocumentObject, TEMPLATE_IPT)
part_def = CastTo(part_doc, "PartDocument").ComponentDefinition
sk = part_def.Sketches.Add(part_def.WorkPlanes.Item(1))   # YZ: sketch_X = R, sketch_Y = Z
sl = sk.SketchLines
def cm(mm): return mm / 10.0

sp_list = [tg.CreatePoint2d(cm(r), cm(z)) for r, z in pts_mm]   # 닫힌 프로파일
ln0 = sl.AddByTwoPoints(sp_list[0], sp_list[1])                  # EndSketchPoint 체인 필수 — 없으면 AddForSolid E_INVALIDARG
prev = ln0.EndSketchPoint
for i in range(1, len(sp_list) - 1):
    ln = sl.AddByTwoPoints(prev, sp_list[i + 1]); prev = ln.EndSketchPoint
sl.AddByTwoPoints(prev, ln0.StartSketchPoint)

prof = sk.Profiles.AddForSolid()   # Profiles.Count 1 또는 0 — 둘 다 정상
rev_feat = part_def.Features.RevolveFeatures.AddFull(prof, part_def.WorkAxes.Item(3), kJoinOperation)
```

## HoleFeature (관통)

```python
rev_cast = CastTo(rev_feat, "RevolveFeature")
plane_faces = sorted(
    [(f.Evaluator.RangeBox.MinPoint.Z, f) for i in range(1, rev_cast.Faces.Count + 1)
     for f in [rev_cast.Faces.Item(i)] if f.SurfaceType == kPlaneSurface], key=lambda x: x[0])
base_face = plane_faces[0][1]   # Z 최소 = 바닥면

sk_h = part_def.Sketches.Add(base_face)
sp_h = sk_h.SketchPoints.Add(tg.CreatePoint2d(0.0, 0.0)); sp_h.HoleCenter = True
obj_col = app.TransientObjects.CreateObjectCollection(); obj_col.Add(sp_h)
placement = part_def.Features.HoleFeatures.CreateSketchPlacementDefinition(obj_col)
hole = part_def.Features.HoleFeatures.AddDrilledByThroughAllExtent(placement, cm(diameter_mm), kPositiveExtentDirection)
# kNegativeExtentDirection → 구멍 미생성(예외 없음). 아래 「피처 단계 검증」의 step_check 가 FAIL 로 잡는다
```

## MassProperties

```python
mp = part_def.MassProperties   # CacheResultsOnCompute=False 없으면 이전 값 반환 → read_volume_cm3 가 처리
vol_cm3, area_cm2 = mp.Volume, mp.Area   # IPT native 만 정확. STEP→IAM 경로 = 0 (SurfaceBodies=0)
```

## 피처 단계 검증 (`tools/step_check.py`)

절차·보고 형식 = AGENT.md 2·5번. `read_state(part_doc)` = (Volume cm³, Faces, RangeBox cm). 판정:

| 조건 | 판정 |
|---|---|
| dV≈0 이고 dF==0 | FAIL (무동작: 방향 틀린 Hole 등) |
| 이론 dV 와 `max(1e-4×\|exp\|, 1e-7 cm³)` 초과 어긋남 | FAIL (곡면-곡면 단계 7e-5 mm³ 오차 사례 포함) |
| 이론 dV 없음 | WARN |
| `exp_bbox` 와 after RangeBox 가 0.01 mm 초과 어긋남 | FAIL (체적만으론 못 잡는 base extrude 방향 반전) |

함정: Hole 방향은 normal 로 계산하지 말고 kPositive 로 시도 후 step_check 로 확인(Extrude 와 방향 규약이 다름). 윗면 선택 시 `MaxPoint.Z` 만 보면 옆면과 동률 → `MinPoint.Z` 도 비교.

## Save & Close

```python
part_doc.SaveAs2(IPT_PATH, False)
part_doc.Close(True)   # SkipSave=True
app.Quit()
```
