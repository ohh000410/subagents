# FDTD 수렴 — 핵심 원리

절차·판정 `fdtd_convergence_protocol.md`. 근거 → detail(필요할 때만).

## 순서·지표
필수: 종료노브(높이Δ=모니터 높이별 R 편차) → mesh(|ΔR| self-converge) → PML(air 보존 R→0). 단계마다 지표 다름. 외부 GT(TMM/RCWA) 대조는 선택(신뢰할 GT 있을 때만).

## 종료노브 →[fdtd_detail_termination.md]
- "펄스 에너지가 죽는가"(source type 아님). 무손실 grazing Bloch → 긴 pulse(좁은 대역)로 정상상태화
- 판정 = 높이Δ(여러 높이 모니터 R 편차, 공간)가 노브 sweep 에 단조 감소

## mesh (grazing) →[fdtd_detail_mesh_grazing.md]
- acc 넉넉히 고정(보통 4), 수렴은 구조 local dx. dispersion k·Δx=2π/ppw, 파장·재료 무관(acc4≈1%). acc 줄이기는 사후 선택
- grazing 은 접선축 dx refine(정입사와 반대, (2π·sinθ/ppw)² 지배). dy 단독 악화(예외: 법선 박막 해상 → detail)
- 구조 local dx 가 staircase + 공진 위상오차 동시 수렴. 구조-local box 로 충분. tensor mesh → 축 refine 은 수직 전역
- self-converge 진동 가능 → plateau 3점
- mesh accuracy 최대 8(초과 clamp = 가짜 plateau). conformal·dt 축소는 grazing 안 고침

## PML →[fdtd_detail_pml.md]
- distance(구조↔PML gap): span 키우며 R 무변 확인. 시작 ≥λ, grazing 은 더. self-convergence(KB 1순위, coarse mesh 로)
- kappa = grazing 흡수 주효과(과하면 발산). alpha 는 propagating grazing 역효과. profile 고정 금지 → air-only 공정 비교
- 무손실 슬랩 잔차 지배 요인은 대개 PML 아닌 mesh
