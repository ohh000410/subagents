# FDTD 수렴 절차 (종료노브 → mesh → PML)

sweep·물리값 신뢰 전 자가진단. 원리 → [fdtd_principles_convergence.md](fdtd_principles_convergence.md). 케이스(각도·파장·매질·구조)마다 진단.
수행 주체 = 호출자 또는 lumerical 상담 모드. 실행 모드 = 받은 셋업 실행만.

| 순 | 단계 | 노브 | 판정 지표 |
|---|---|---|---|
| 1 | 종료노브 | autoshutoff (Bloch 는 좁은 대역) | 여러 높이 모니터 간 R 편차 → 0 (높이Δ) |
| 2 | mesh | 구조 local dx (acc4 고정) | \|ΔR\| plateau (진동 감쇠 포함) |
| 3 | PML | distance·profile·layers | air 보존(T→1, R→0) + span 키워 R 무변 |

필수 = 1~3 (FDTD 자체 판정). 외부 GT 대조 = 선택. R+T=1 은 knob 판별 지표 아님 (에너지수지 sanity 만).

## 1. 종료노브 — 높이Δ

R 모니터를 여러 y 높이에 두고 R 편차(공간)를 autoshutoff sweep 에 대해 본다. 부족 → 정재파로 높이별 R 출렁. 충분 → 높이 무관.

| source | 노브 | 값 |
|---|---|---|
| BFAST | autoshutoff | ~1e-7·1e-8. 1e-3~1e-6 은 같은 종료(급락 위). ≤1e-10 → 최저점 아래, late-time 발산으로 cap 오염(높이Δ 폭증). 발산 → `fdtd_detail_bfast.md` |
| Bloch (흡수·무손실) | autoshutoff + 좁은 대역 | `set time domain` + pulselength ~3000fs. broadband 면 grazing evanescent 잔류로 autoshutoff 무력·느림 → `fdtd_detail_termination.md` |

- 판정 = 높이Δ 가 sweep 에 단조 감소 (한 점 = 진동 우연 주의)
- BFAST 높이Δ floor ~e-5 (본질적). `bfast dt multiplier`↓ 는 발산 지연만

## 2. mesh — acc 고정 + 구조 local dx

- acc = 4 고정 (18 ppw). dispersion 오차 = k·Δx = 2π/ppw, 파장·재료 무관. acc 최대 8 (>8 clamp = 가짜 plateau)
- 구조 local dx sweep: 계면·FP 근처 dx↓ → |ΔR| plateau. staircase + 공진 위상오차 동시 수렴
  - grazing = 접선축(dx) 지배 ((k_x·Δx)² = (2π·sinθ/ppw)²), 정입사 = 법선 dy. tensor mesh 라 dx 는 수직 전역. 박막 dy 별도 → `fdtd_detail_mesh_grazing.md`
  - |ΔR| 진동 수렴 가능 (무손실 슬랩 grazing) → 1칸씩 + plateau 3점. conformal·dt 축소는 grazing 안 고침
- dx sweep 시 PML 물리두께 변동 → R 가짜 진동. air-only 두께 민감도 먼저 or `layers = 두께/cell` 고정
- cell 측정: probe run + `Linear Y` monitor y 격자 diff
- (선택, 끝난 뒤) acc 4→3→2 로 비용 절감. acc 는 공진 민감도(dR/dφ) 의존 → 사후 최적화

## 3. PML (mesh 확정 후)

- distance: air-only 에서 span 키우며 R 무변 확인. 시작 gap ≥ λ. 상수 금지 — grazing 은 소멸파 δ > λ
- 진단 = air-only (R=0, T=1) + 위치무관
- profile = (kappa·sigma·alpha) 묶음. 같은 layers 로 3개 비교 → 선택 → 두께 sweep. profile 고정 금지
- API: `set("pml profile", N)` (1 std · 2 stab · 3 steep · 4 custom). profile 후 layers/kappa/sigma/alpha override — profile 설정이 layers 를 기본값으로 되돌림, `getnamed` 확인
- kappa 과도 → late-time 발산 (높이Δ 오염). 절충 ~5 → `fdtd_detail_pml.md`

## (선택) 외부 GT 대조

1~3 수렴 후. 신뢰할 GT 있을 때만. 단순 슬랩·층상 = TMM 정답, FDTD = 복잡 구조용. BFAST 절대 R/T 는 같은 mesh air-only 재정규화 필수 (sourcepower 오류로 T>1 가능) → `fdtd_detail_bfast.md`.
