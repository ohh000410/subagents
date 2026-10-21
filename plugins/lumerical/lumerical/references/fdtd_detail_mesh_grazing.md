# mesh — grazing 상세 근거

요약 `fdtd_principles_convergence.md`. 절차 `fdtd_convergence_protocol.md`.

## 사입사 축 = 접선축 (정입사와 반대)
dispersion 오차 ∝ (k·셀)². kx=k0·sinθ(접선), ky=k0·cosθ(법선). grazing 은 kx 큼 → (kx·dx)² 지배 → dx refine. dy 단독 refine 은 anisotropy 로 악화. BFAST 가 grazing 을 정입사화해 통하는 이유.
- 적용 범위: 균질 슬랩/wedge 실측 기반 dispersion 규칙. 법선에 미세 기하(박막·좁은 gap) 있으면 그 해상용 dy 먼저 확보, dispersion 은 dx

## tensor-product mesh
x-격자선은 전 높이 관통 → dx refine 은 그 x-범위 전 높이 fine. box y-범위로 못 가둠 → grazing fine-x 비쌈.

## 구조-local box
반사 power 는 구조(계면·FP)에서 결정, 무손실 전파 보존 → 구조+마진만 override = 전역 override 와 동등(모니터 coarse 무방). 잔차 대부분 구조-local, 전파경로 dispersion 기여 작음.

## mesh accuracy 상한 8
1~8. API >8 은 에러 없이 8 clamp → 9/10/12 동일값 = 가짜 plateau. 더 세밀화 = `addmesh` dx override(clamp 없음. span 정수약수 아니면 snap 가능 → readback 확인).

## self-converge 진동 — 무손실 슬랩 FP
|ΔR| 진동하며 plateau 접근 가능. 유력 원인 FP 다중반사 위상 + 격자 분해능 오차(큰 점프 위치가 두께/위상에 묶임). 진동 시 mesh 1칸씩 더 높여 plateau 3점 확인.

## 안 먹히는 레버 (grazing TM 한정, wedge 실측)
- conformal mesh 무효: CMT 는 계면 permittivity 평균 → TM E_normal 불연속엔 무효. variant 0/1/2 는 금속/PEC 처리만 다름. staircase 는 반대편 overshoot. 정입사~중간각 dispersive 구조에선 conformal 이 표준 개선 수단
- dt 낮추기 금지: Yee 는 Courant≈1 에서 dispersion 최소 → dt stability factor↓ 는 악화

## PML 물리두께 고정 (조건부)
mesh sweep 시 PML 흡수 빠듯하면 cell→두께 변동으로 R 가짜 진동 → `layers=목표두께/cell` 역산. 흡수 충분(높은 kappa)하면 layers 고정 무방 → air-only 두께 민감도 먼저. 파라미터 `fdtd_detail_pml.md`.
