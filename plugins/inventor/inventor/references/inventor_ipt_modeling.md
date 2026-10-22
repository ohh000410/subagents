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

## Extrude (ExtrudeFeatures)

Inventor 2027(API v31)에서 cut 까지 정상 동작한다(4피처 부품 체적 오차 0.000000 %). `E_INVALIDARG` 는 "기능 없음"이 아니라 **인자 값이 틀렸다**는 뜻이다.

```python
ext = part_def.Features.ExtrudeFeatures
ed = ext.CreateExtrudeDefinition(prof, kJoinOperation)
ed.SetDistanceExtent(cm(20), kPositiveExtentDirection)   # 거리는 cm
feat = ext.Add(ed)                                       # 인자는 정의 하나

ed = ext.CreateExtrudeDefinition(prof, kCutOperation)    # cut
ed.SetDistanceExtent(cm(5), kNegativeExtentDirection)    # 막힌 홈
# ed.SetThroughAllExtent(kNegativeExtentDirection)       # 관통
ext.Add(ed)
```

| 잘못된 호출 | 실제 오류 |
|---|---|
| `Add(prof, dist, dir, op)`·`Add(prof, dist)` | pywin32 `TypeError`(인자 개수) — COM 까지 가지 않는다 |
| `Add(prof)` | `0x80020005 DISP_E_TYPEMISMATCH` |
| `AddByDistanceExtent(prof, dist, op, dir)`(순서 바뀜)·닫히지 않은 profile | `0x80020009 DISP_E_EXCEPTION`, excepinfo scode = E_INVALIDARG |

- E_INVALIDARG 는 `e.args[2][5]`(excepinfo scode)에서 읽는다. `e.args[0]` 은 DISP_E_EXCEPTION 뿐이다.
- `AddByDistanceExtent(prof, dist, 방향, 연산)` 은 v31 CHM 에 없지만 2027 형식 라이브러리에서는 동작한다. 새 코드는 `CreateExtrudeDefinition` 을 쓴다.
- 방향: 윗면 스케치(법선 +Z)에서 `kNegativeExtentDirection` 이 재료 안쪽으로 자른다. 아래 HoleFeature 는 반대다 — 두 API 의 방향 규약이 달라 체적 변화로 확인한다.
- `kPositiveExtentDirection` 은 스케치 평면 법선 방향이다. 하드코딩하지 말고 실행 중에 읽는다:
  ```python
  def extent_dir_towards(wp, material_dir):
      n = wp.Plane.Normal
      dot = n.X * material_dir[0] + n.Y * material_dir[1] + n.Z * material_dir[2]
      return kPositiveExtentDirection if dot > 0 else kNegativeExtentDirection
  ```
  원점 평면 법선: `XY Plane`→+Z, `XZ Plane`→+Y, `YZ Plane`→+X. 평면은 `Item(i)` 순서를 가정하지 말고 `WorkPlane.Name` 으로 찾는다.
- `ExtrudeDefinition.Operation` 은 실제 적용된 연산을 되읽는다 — 첫 solid 를 `kJoinOperation` 으로 만들면 `kNewBodyOperation` 으로 읽힌다.
- 체적만으로는 뒤집힌 base extrude 를 못 잡는다(5×5×1 mm 판은 어느 쪽이든 25 mm³) → `ComponentDefinition.RangeBox` 도 본다(아래 「피처 단계 검증」).
- 평면 다면체는 cut 마다 `MassProperties.Volume` 변화가 해석값과 ~1e-11 % 로 맞는다(판 + 관통 V홈 20개) — 정확한 합격 기준으로 쓴다. 방향이 틀리면 변화 0, profile 이 틀리면 다른 값이 나온다.
- 교차하는 두 V홈 묶음: 두 번째 묶음은 겹친 만큼 홈마다 덜 깎인다. 한 묶음을 다 깎고 다음 묶음을 깎으면 체적 변화의 두 단계가 이중 계산을 드러낸다.

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

절차·보고 형식 = agents/inventor.md 2·5번. `read_state(part_doc)` = (Volume cm³, Faces, RangeBox cm). 판정:

| 조건 | 판정 |
|---|---|
| dV≈0 이고 dF==0 | FAIL (무동작: 방향 틀린 Hole 등) |
| 이론 dV 와 `max(1e-4×\|exp\|, 1e-7 cm³)` 초과 어긋남 | FAIL (곡면-곡면 단계에서 MassProperties 가 해석값보다 약 7e-5 상대 — 2598 mm³ 중 0.18 mm³ — 큰 사례도 통과하는 폭) |
| 이론 dV 없음 | WARN |
| `exp_bbox` 와 after RangeBox 가 0.01 mm 초과 어긋남 | FAIL (체적만으론 못 잡는 base extrude 방향 반전) |

함정: Hole 방향은 normal 로 계산하지 말고 kPositive 로 시도 후 step_check 로 확인(Extrude 와 방향 규약이 다름). 윗면 선택 시 `MaxPoint.Z` 만 보면 옆면과 동률 → `MinPoint.Z` 도 비교.

## Save & Close

```python
part_doc.SaveAs2(IPT_PATH, False)
part_doc.Close(True)   # SkipSave=True
app.Quit()
```
