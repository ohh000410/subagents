# FDTD source — 핵심 원리

설정 코드 `fdtd_lumapi_patterns_advanced.md`. 근거 → detail(필요할 때만).

## 2D 편광 라벨
Lumerical 2D `polarization angle = 0` = p-pol/TM(in-plane E), `90` = s-pol/TE — 직관·GUI 표기와 반대. RCWA/TMM 비교·보고 라벨 스왑 (flat 슬랩 Brewster vs TMM 검증).

## 3D conical 소스 각도 매핑 (injection y-axis, Backward) — GUI 화살표+편광 실측
1D 격자(홈 방향 z 불변)를 3D 얇은 z-슬라이스 + Bloch 로 conical 입사.
- 좌표: x=주기(홈 수직, 면내), y=법선(injection axis), z=홈축
- y-inject Backward 실측: `k = (sinθ_L·sinφ_L, -cosθ_L, sinθ_L·cosφ_L)`
  - `kx=sinθcosφ, kz=sinθsinφ`(문서 스니펫류) 는 틀림. in-plane(kz=0) 은 phi=±90
- 원하는 하늘방향 d → 입력 (입사 = −d):
  ```
  d = (sinφ'·sinθ', sinφ'·cosθ', cosφ')     # φ'=홈축과의 각, θ'=단면 정사영각(법선 기준)
  θ_L = sign(θ') · arccos(sinφ'·cosθ')       # θ' 부호 유지 (양수화하면 편광 반대)
  φ_L = atan2(-d_x / sinθ_L, -d_z / sinθ_L)  # sinθ_L 로 나눔(부호 유지) = 편광까지 맞춤
  pol = 90(TE) / 0(TM)
  ```
- 함정 2개:
  1. `atan2(d_x, d_z)` + θ_L 양수화 → k 맞아도 편광 반대
  2. phi 0/180 → kx=0 + kz≠0 → TE 만 2D θ=0 유사, TM 은 편광 오염
- 검증: in-plane 극한(φ'=90 → θ_L=θ', φ_L=−90)이 2D 같은 각 ε 을 편광별 0.01 이내 재현. 소스 실제 k 는 API 로 못 읽음(`getnamed(FDTD,kx)`=0) → GUI 화살표 + 앵커 실런이 유일 검증

## BFAST →[fdtd_detail_bfast.md]
- 단일 파장 → Bloch. broadband + 고정각에만 BFAST
- 고각 T>1 = sourcepower 정규화 오류(gain 아님, p-pol) → raw Poynting 재정규화(같은 mesh air baseline 분모)
- 정확도 천장: mesh 조여도 악화(timestep 누적). 고정밀 = Bloch + 접선축 refine
- late-time 발산(좌표변환 kx 항). 편광별 air-only sanity check
