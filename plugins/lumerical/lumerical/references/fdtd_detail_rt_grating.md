# grating projection vs net-flux — 상세 근거

요약 `fdtd_principles_extraction.md`.

## 두 방법
- grating projection: monitor field FFT → 회절 차수 분해 → 전차수 반사 합산(Σ P_ref_m). 입사/반사 modal 분리
- net-flux: 순 Poynting flux. 공식은 monitor·source 배치 의존(`fdtd_detail_rt_signs.md`). 입사·반사 교차항(2AB)은 역방향 진행파라 reactive→0, 이미 제거

## 참값 기준
- non-Rayleigh → grating (modal 분리 정확, 위치무관). net-flux 도 |Δ|<1e-4 일치 → 동등
- 정확 Rayleigh 각도(차수 ky→0) → net-flux (grating 무너짐)

## Rayleigh 에서 grating 이 무너지는 이유
`Z=ωμ0/ky_m`, `E_ref=(E−Z·H)/2`. grazing 차수 `H∝ky→0` 인데 `Z` 로 1/ky 증폭 → 수치오차 폭발. `exp(±iky·y)` 기저 축퇴 → 분해행렬 특이 → R 과소. net-flux 는 나눗셈 없음(grazing 차수 ky 가중으로 기여 0).

## 실무
- net-flux 로 통일 무방(각도 sweep 은 정확 Rayleigh 대개 안 밟음). monitor 는 evanescent 죽을 거리 확보(3높이 spread 로 확인)
