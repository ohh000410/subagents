# PML — 상세 근거

요약 `fdtd_principles_convergence.md`. 절차 `fdtd_convergence_protocol.md`.

## profile = (kappa·sigma·alpha) 프리셋
- layers = 흡수 두께 (주효과, sweep 대상)
- sigma = 흡수 강도 (steep 1.5)
- alpha = CFS. propagating grazing 흡수엔 역효과(alpha↑ → |T-1|↑, 극단 발산). evanescent 엔 도움
- kappa = 좌표 stretching. grazing 흡수 주효과(kappa↑ → |T-1| 개선). 과하면 ① Wood anomaly overdamping ② late-time 발산(에너지 증가 → autoshutoff 안 걸림·높이Δ 오염). normal 입사엔 영향 작음
- polynomial·alpha-poly 는 프리셋 동일

## profile 고정 금지
두께·각도·발산·매질에 따라 유리한 profile 다름. Ansys 권장 profile = 출발점. 케이스별 air-only 공정 비교.

## 두께 ↔ 종료시간
두꺼운 PML = 안정, 종료 늦음. 수렴되는 최소 두께.

## 고각 누설 — layer 만으론 안 준다
grazing 흡수 효율 각도↑ 저하, layer 증가만으로 해소 안 됨(문헌 일반). layer·profile·kappa/sigma/alpha·물리두께·mesh cell 얽힘 → air-only sanity check 로 누설 수준 먼저, profile·물리두께·mesh 분리 비교.

무손실 슬랩 grazing 잔차 지배 요인은 대개 PML 아닌 mesh(접선축, `fdtd_detail_mesh_grazing.md`). PML 은 충분한 kappa 면 작은 floor → air-only R→0 로 배제 먼저.
