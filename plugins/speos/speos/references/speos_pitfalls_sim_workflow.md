# SPEOS SIM — 워크플로·메시·파일 함정

## Student license 한도 — triangle 과 face, 독립

| 한도 | 값 | 거부 메시지 |
|---|---|---|
| mesh triangle | 32,000 미만 | `The simulation includes 54,615 triangles...` |
| face | 300 미만 | `The simulation includes 567 faces. Student license only supports simulations with less than 300 faces` |

triangle = tessellation, face = topology.
- `LocalMeshing` 은 face 한도에 무효 → geometry 변경 (주기 수 축소)
- face 는 scene 전체 합산
- 교차 V-groove face 수: memory `student_license_limits`
- triangle: `MeshingSagLengthValue` 0.005 → 0.1~0.5 (`speos_sim_compute_mesh.md`)

거부 = 예외 없이 `sim.Compute()` 0.8초 정상 리턴 + `sim.StatusInfo` 메시지. 통과 = "". `DoesRulesSucceed()` 는 정상 sim 에서도 False — 게이트 불가.

## MeshingAngle=1

sag 0.01~2.0 전 범위에서 32k 초과. angle ≥ 5 → sag [0.01, 2.0] × step [5, 100] 정상. sweep 은 angle=1 사전 SKIP.

## 결과 위치

`<DocumentSave .scdocx 폴더>/SPEOS output files/<base>/` — `.xmp`, `.xml`, `Report.html`. Compute 는 input 파일 위치 기준 → DocumentSave 먼저.

## XML 템플릿 = ISO-8859-1

`write_text(xml, encoding="iso-8859-1")` 에서 em-dash·한글 → UnicodeEncodeError. Comment·Name 은 ASCII 만.

## DocumentOpen 후 이름 충돌

기존 객체(LocalMeshing, Material, SourceSurface …) 로드됨 → 같은 이름 `Create()` 충돌. 새 이름으로 Create → Compute.

## sc.log 공유 + 빠른 polling → false "ALL OK missing"

case 마다 SC 별도 launch + sc.log w 모드 초기화 시, graceful_close 후 log 읽기가 다음 case 덮어쓰기와 race → flux 정상·FATAL 없음인데 WARN. single sim 에서도 발생. → case·sim 마다 별도 log 경로 (`sims/{run_id}/sc.log`).
