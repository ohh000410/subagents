# grcwa_convergence — grcwa 수렴 프로토콜 (research-compute)

grcwa(순수 python RCWA + autograd, CPU) 수렴·재현성 방법론. **grcwa 수렴/calibration = 이 파일 + [[grcwa_api]](함수).** 단순 스윕만이면 [[grcwa_api]]만 읽으면 됨. meent는 [[meent_convergence]]. 공통 결론은 [[rcwa_reference_index]].
검증: wedge s1. 일반 원칙과 "이 구조 관측값" 구분 — 다른 형상/각도는 관측값(발산 nG·노이즈바닥) 재측정.

## 0. 측정 전제 (안 하면 나머지 무의미)
- **BLAS=1**: `OMP/OPENBLAS/MKL_NUM_THREADS="1"`를 numpy/grcwa import 前 os.environ. (스레드만 1↔4↔8 바꿔도 15% 흔들림; thread=1만 bit-identical.)
- **fallback OFF** — wrapper 금지·이유는 [[grcwa_api]] ★ 소유. 발산은 §3 명시 처리.
- ★ **재현 ≠ 정확 (near-singular)**: BLAS=1은 재현이나 near-singular 점에선 값이 눌려 틀릴 수 있다 → spread(1/4/8)로 감지(§2), 배제하고 참값은 안정 능선(spread≈0). (실측 예: memory `project_blas_gate_nearsingular_plus60.md`.)
- **병렬·캐싱**:
  - 캐싱: `{(nG,N_z,pol):eps}` dict, solve 前 조회. ★ `get_grid_size`만 캐시하고 무거운 solve 결과 안 하는 실수 흔함.
  - 병렬: 독립 점(sweep·median 3점·전각도) 전부 Pool — 표준(워커 수·BLAS=1·메모리 가드)은 [[rcwa_reference_index]] 공통 2. 순차는 path iteration 間뿐(path는 iteration 내부만 병렬).

## 1. 두 수렴축
- **nG (Fourier order)**: monotone 아님. 물리 floor 위 plateau, 특정 nG 발산. floor ≈ 2~3×propagating (격자식 `sinθ_m=sinθ_inc+mλ/L`, |sinθ_m|≤1인 m 개수 ~2L/λ; sheared는 evanescent 多 ~150). ★ floor 미만=저샘플링(BLAS spread=0이나 눌림) ≠ near-singular(spread 큼).
- **N_z (z-staircase)**: 형상 이산화 정밀도. monotone·발산상한. sheared는 N_z가 곧 형상 정밀도라 ≫50.

## 2. 수렴 판정
- **신뢰값 = plateau 통계**: 스윕 → 발산점 제거 → 안정구간 mean±std. std=노이즈바닥(사후).
- **stopping = 포화**: tol 사전에 못 박지 않음. |s| 감소 멈추는 지점. 단조감소 가정 금지 — "최근 몇 스텝 |s| 최소 갱신"으로.
- **near-singular 판별 = BLAS spread**: 수렴 후보 시 1/4/8, <0.01 진짜/>0.01 near-singular→nG 소폭(±20%, 등비×2 아님) 이동해 능선으로. ★ 반드시 **별도 subprocess로 thread env 변경**(같은 프로세스 os.environ은 numpy에 안 먹어 spread=0 오판).
- 신뢰 조건 = BLAS 불변 ∧ plateau 내부 ∧ 발산 아님. ★ BLAS spread 일치(=0)만으로는 수렴 증거가 아니다(눌린 저샘플링도 spread=0) — `checks.convergence_line` 은 spread 로 PASS 를 만들지 않는다.
- **path 이동 (다축·비용가중)**: 시작 경량 (40,20). 매 iter 두 축 |s|. 축 선택 = |s_i|÷cost_i (nG O(nG³) 무거움→같은 |s|면 싼 N_z 먼저), 둘 다 유의미면 동시. |s_i|<노이즈바닥 고정. 보폭 2정수승·축별 독립. ⚠️ greedy(한 축 ×2)는 iteration 늘고 coupled(N_z↑ 시 nG 되살아남) 왕복 비효율.

## 3. 발산 처리
- 하드발산(R>1.5·nan): 폐기 후 인접 평가 — 옆 정상=isolated(offset shift + "shifted N→M" 로그), 옆도 발산=축 상한(refine 중단).
- 소프트 이탈(R<1이나 plateau 큰 낙하): 실질 상한, 마지막 안정점.

## 4. 편광별 calibration 필수 (TE≠TM)
near-singular 위치·수렴 N_z가 편광 의존(Fourier factorization 다름) — 편광마다 따로 calibration. 비대칭 형상은 ±θ도 다름(물리적 필연). **구체 N_z 값은 형상 관측치**(s1 각도·편광별 → memory `reference_rcwa_wedge_s1_values.md`).

## 5. 전각도: calibration → production
- ★ **새 형상 첫 calibration은 형상 확인부터** (geometry 함수 도입 시 한 번): **유효 유전율(truncation된 eps) 플롯으로 호출자 확인** — 방법·이유·참조 구현은 [[meent_convergence]] ★첫 calibration(라이브러리 무관 동일 개념). 여의치 않으면 최소한 eps grid(staircase)라도. **파라미터 스윕은 같은 함수라 재확인 불필요.**
- **calibration**: worst-case(가장 grazing)서 수렴점·민감축·노이즈바닥. 세트 = near-singular 벗어난 최소 안정 nG(floor 위)부터 등차 3점(간격 ~20)×안정축.
- **production**: 전각도 동일 세트, eps(θ)=median{3점}, σ(θ)=std(불확실 각도 선별 지표 — 필요 시 독립 솔버 스팟체크 대상 고르는 용도). 형상 바뀌면 calibration만 재실행.

## 5.5 production 자동 판정 필수 필터 (순서 준수)
1. **발산 제거**: |eps|>1·<0·nan 폐기 (`checks.result_bounds` 가 판정 줄 출력). 세트에 발산/미검증 절대 불포함.
2. **near-singular gate**: 눌린 점마다 BLAS spread(1/4/8), >0.01 배제. 초반 1회 "없음" 단정 금지 — 전 구간 확인.
3. **물리 floor**: nG < 2~3×propagating 저샘플링 제외.
4. **plateau/median**: 위 다 제거한 안정 능선(연속 |Δ|<노이즈바닥)에서만.
5. **N_z도 능선에서 재판정**: nG를 능선으로 옮겼으면 N_z도 그 능선 nG서 재확인(near-singular nG는 N_z 과요구, 능선에선 줄어듦). 편광별 다름. (s1 실측 수치 → memory `reference_rcwa_wedge_s1_values.md`.)

## 6. Rayleigh 각도 → meent 격리 (또는 FDTD)
Rayleigh 각도(격자식 → [[rcwa_reference_index]] 공통 3)서 grcwa nan. offset(±0.05°) 회피는 비대칭 구조서 +≠− 편향→폐기. 그 각도만 **meent 격리 실행으로 대체**(검증·규칙 → 공통 3) 또는 FDTD(그 각은 grating projection 부정확 → net-flux R 권장).
