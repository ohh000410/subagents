# FDTD R/T 추출 — 핵심 원리

근거 → detail(필요할 때만).

## 부호·배치 →[fdtd_detail_rt_signs.md]
- transmission() 부호는 배치 의존. `abs()` 를 R 로 쓰면 작은 R 을 큰 R 로 오독
- 흡수 큰 구조(R 작음): baseline 차감(a)이 가장 robust
- grazing 에서 소스 뒤 R_mon 은 되통과 손실(~1%, R+T<1 로 감지) → 소스와 구조 사이(b)

## grating vs net-flux →[fdtd_detail_rt_grating.md]
- non-Rayleigh 동등, 정확 Rayleigh 에서 grating 무너짐(ky→0) → net-flux 참값
- flat slab = specular 0차 하나 → grating ≡ net-flux. grating 은 차수별 분해 필요할 때만
- net-flux 통일 무방. monitor 는 evanescent 죽을 거리 확보
