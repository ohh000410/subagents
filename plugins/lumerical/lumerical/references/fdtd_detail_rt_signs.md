# R/T 부호·배치 — 상세 근거

요약 `fdtd_principles_extraction.md`.

## transmission() 부호
`fdtd.transmission("mon")` = 모니터 법선(+) 방향 normalized net power. 법선(+)과 진행 방향 반대면 음수.
예 Backward −y injection: R_mon·T_mon 모두 +y normal. 공기만 시뮬 → 음수.
- R 추출(source 아래 R_mon, Backward): `R = 1 + transmission("R_mon")`. `abs(transmission)` 을 R 로 쓰면 작은 반사를 큰 반사로 오독
- 배치가 다르면 부호 공식을 재사용하지 않는다. (±R, ±T) 네 조합 중 에너지 보존 `min|1−R−T|` 이 맞고 값이 [0,1] 안인 조합을 택한다(맞는 조합 5e-4 수준, 나머지는 0.7 이상 어긋남)

## 흡수 큰 구조 (R 작음)
- (a) baseline 차감 — 가장 robust: 공기만 + 구조 2회. `R_corr = trans_struct − trans_air`, `T_corr = |trans_T_struct|/|trans_T_air|`. 누설 동일 → 차감 제거, monitor 위치 무관
- (b) source > R_mon > 구조: `R = 1 − |net|`. 누설 섞이면 오염 → oblique 누설 사전 확인, baseline 병행
- (c) source 위 R_mon 직접: R≫0.1 용. R≪1 흡수체는 oblique 누설 상대오차 큼 → (a)/(b)

## grazing 소스 되통과 손실 (배치 함정)
소스 뒤 R_mon 은 반사파가 소스면 되통과 → 소스 전류 sheet 가 grazing 반사파 불완전 투과 → ~1% 손실(고각 의존, 정입사 ~0), R 계통적으로 낮음. R+T<1 로 감지, air baseline 로 못 고침 → 고각은 (b).
