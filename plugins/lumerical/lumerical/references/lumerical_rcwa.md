# Lumerical RCWA / STACK — `lumerical` 에이전트

Lumerical 라이선스 RCWA·STACK. 순수 python RCWA(meent/grcwa/torcwa) = `research-compute` (`rcwa_reference_index.md`) — 수렴 예산·부호규약·GPU 결론 상호 이식 금지. 실측 2026-08-10~13, v242.

## 0. 버전 — v242 만

v232 RCWA 는 `Im(eps)` 를 버린다 (`n = sqrt(Re(eps))`) → 모든 구조 `R+T = 1.000000`, 금속 S-행렬 비유니터리(`R_TM = 3.724`). v242 에서 해소 — 손실 유전체 TMM 8자리, 금속 Fresnel 3.6e-15 일치.

## 1. 라이선스

RCWA = `lum_stack_solve` 소비. `lum_fdtd_solve` 와 경쟁 없음 → FDTD 4 + RCWA 4 동시 가능. `lum_fdtd_gui` 1석 → 세션 중복 금지. `lum_rcwa` feature 는 존재하지 않음.

## 2. 최소 셋업

```python
fdtd.eval('addrcwa; set("name","RCWA");')
fdtd.eval('setnamed("RCWA","interface absolute positions", <N x 1 array>);')
fdtd.eval('setnamed("RCWA","report grating characterization",1);')   # run 전. 없으면 R/T 미출력 (x y z num_k total_energy substrate 만)
fdtd.eval('run;')
te = fdtd.getresult("RCWA","total_energy")   # keys: lambda f theta phi Rs Ts Rp Tp
```
- `incident angle` = `'single'` 만. `'sweep'`·`'theta and phi sweep'` throw → python 루프 `switchtolayout; setnamed("RCWA","angle theta",t); run;`
- `interface actual positions` 되읽기 (실측 일치 1.4e-14 µm)
- 주기 초과 형상(apex overhang) = x 방향 수동 타일링. RCWA 는 wrap 하지 않음

## 3. 종단층 손실 무시

흡수 측정 재질을 반무한 종단층으로 두면 `R = 1.000000` (또는 `R+T = 1.000000`) 정확히. 유한 두께 + 진공 종단.

| Al @ 10 µm, n = 25+85.96i, θ 0~75° | 결과 |
|---|---|
| Al = 반무한 기판 | `R = 1.000000` 전 각도 |
| Al = 1 µm 중간층 + 진공 종단 | Fresnel 3.6e-15 일치 |

## 4. 수렴 knob

| knob | 역할 |
|---|---|
| `max number ku` | Fourier 예산. 분해능 = L/(2·ku+1) |
| interface 개수 (staircase 층수) | z 분해능 |

- `mesh cells z` 는 `interface position = absolute` 에서 무시 (43층→64, 163층→163, 483층→483). z knob = interface 개수
- `mesh type` 기본 `auto` → `mesh cells x` 무시. `custom` 필요. `actual mesh cells x/y/z` 되읽어 기록

병목 (경사 격자 한 형상, θ=+60° 실측):

| 케이스 | 병목 | 거동 |
|---|---|---|
| 무금속 유전체 | n_z | 단조, 차수 p≈2. ku 수렴 (spread 3e-6/1.2e-4) |
| 얇은 금속 코팅 | ku | n_z 비단조·plateau 없음. ku 67→200 에서 eps 0.58 이동, 268 에서도 상승 |

임계 ku ≈ L/(2·w) (w = 가장 좁은 수평 폭, 경사 코팅이면 두께/cos(경사)). 분해능 L/(2·ku+1) 이 w 보다 커지면 수렴하지 않는다 — 위 금속 코팅은 ku 67 이 임계의 약 1/3 이었다. feature/주기 비로 ku 예산 선계산.
가짜 plateau: Al s/TE li-off 0.03 평탄 vs 같은 구조 TM 0.84 → 모순 (평면 Al 60° R_s 0.9938 / R_p 0.9754). 편광 간·해석해 정합성 같이 판정.

## 5. `use li factorization`

2024 R1.1 신규. 릴리즈 노트: 1D grating 고대비(금속) 수렴 개선. 실측(10 설정, ku 67~200, n_z 160~720, nx 600~4800, conformal·staircase): s/TE 만 변화(금속 최대 +0.87), p/TM bit-identical. s/p 라벨 스왑 아님(유전체 Rs↔TE, Rp↔TM 앵커 4e-4/6.9e-4, 스왑 시 1.6e-2). li-on / li-off 계열은 같은 극한으로 수렴하지 않음 — 혼합 금지. 비용 <1.5%. 원인 미해결. 미시험: `use tangent vector field`.

## 6. 검증 채널 — `_p0.log` 없음

RCWA = in-process. 결과 자체 검사만:
1. R, T finite — 주기의 15% 폭 금속(Al) ku=67 에서 Rs/Ts/Rp/Tp 전부 NaN, 예외·로그 없음
2. `R+T == 1.000000` 정확 → 3절 위반
3. `eps = 1−R−T` ∈ [0,1] — `R+T−1 > 1e-6` 이면 비물리(v242 손실 유전체 TMM 8자리 일치 기준)
4. 편광 간 정합성

## 7. 재현성

동일 설정 bit-identical. 동일 세션 ×3 spread 0.0 / 별도 프로세스 OMP·MKL 1/8/12 스레드 spread 0.0 (속도만 115 s ↔ 44 s). grcwa 는 스레드 수에 따라 eps 0.890↔0.905 (spread 0.013~0.017). 재현성 시험 = 스레드 수 바꿔 별도 프로세스.

## 8. 비용 (양 편광 동시)

스케일링 n_z^1.3~1.5, ku^1.5~2. setup 0.2 s. 형상마다 절대 시간은 다르니 첫 calibration 의 실측으로 timeout 을 정한다.

## 9. API 함정

- `getresult("RCWA","index")` dataset 불가 — z 길이 선언 = 실제+1 (44 vs 43) → `ValueError: cannot reshape`. `eval` + `getv` 멤버 행렬 → `order="F"` reshape
- script 변수명 `__` 시작 금지 (`Failed to evaluate code`)
- `addmaterial(...)` 은 이름 반환. `setmaterial(fdtd.getmaterial(), ...)` throw (인자 없는 `getmaterial()` = 전체 목록)
- 재질은 `deleteall()` 에 살아남고 analysis 모드에서 추가 불가 (`switchtolayout` 먼저)

## 10. 부호 규약

Lumerical e^{−iωt}. meent(e^{+iωt}) 값 이식 시 허수부 부호 반전.
- 흡수 매질 예 n = 1.5, k = 0.1: meent `1.5 − 0.1i` → Lumerical `1.5 + 0.1i`
- Al @ 10 µm: meent `25 − 85.96i` → Lumerical `25 + 85.96i`
부호 오류 → gain 매질 → R>1.
