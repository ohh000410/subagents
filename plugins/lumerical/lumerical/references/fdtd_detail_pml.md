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

## layers 읽기값이 요청과 다른 경우
- `pml profile`=2(stabilized)면 `pml layers` 요청이 조용히 32 이상으로 올라감(24 요청 → 읽기 32, 2/2 재현, v242 2D). profile 1·3 은 24 그대로. profile 을 layers 보다 먼저 써도 같고, 하한이 정확히 32 인지는 미측정
- `pml layers` 를 64 넘게 요청하면 오류 없이 64 로 clamp. profile 을 설정하면 layers 가 기본값(8)으로 돌아감(둘 다 v232 실측, v242 재확인 안 함)
- profile·layers 를 쓴 뒤 둘 다 `getnamed` 로 읽고, profile 비교는 요청값이 아니라 읽은 layers 로 맞춤(안 맞추면 layers 수 교란이 섞임)

## 고각 누설 — layer 만으론 안 줄어듦
grazing 흡수 효율 각도↑ 저하, layer 증가만으로 해소 안 됨(문헌 일반). layer·profile·kappa/sigma/alpha·물리두께·mesh cell 얽힘 → air-only sanity check 로 누설 수준 먼저, profile·물리두께·mesh 분리 비교.

무손실 슬랩 grazing 잔차 지배 요인은 대개 PML 아닌 mesh(접선축, `fdtd_detail_mesh_grazing.md`). PML 은 충분한 kappa 면 작은 floor → air-only R→0 로 배제 먼저.

air-only 누설 실측(2D, 10 µm): PML 16층 standard 의 R 누설은 0° 6e-8, 60° 2e-4~3e-4, 75° 3e-3, 80° 1~2e-2, 85° 5e-2 로 각도와 함께 급증. 24층 profile 1 로 60° 를 돌리면 |T−1| 이 s 7e-3, p 2.5e-3 이고 sim time 상한까지 끝나지 않음 — sim time 3배면 p 는 4e-5 로 수렴하지만, s 는 먼 T 모니터 잔차만 줄고(7e-3 → 2.6e-3) 소스 근처 R 모니터 잔차는 커짐(2.4e-3 → 8.6e-3). 그래서 모니터 위치를 두 곳 이상 확인. 같은 실제 layers 에서 profile 2 는 s 를 3.8배 개선·p 를 2.4배 악화, profile 1 의 layers 24 → 48 은 s 26 % 개선·p 52 % 악화 — 순위가 편광마다 뒤바뀌므로 양 편광을 함께 보고 선택. R 누설은 16층 평판 시험, |T−1| 은 24층 경사면 구조 도메인이라 지표가 달라 섞어 쓰지 않음.
