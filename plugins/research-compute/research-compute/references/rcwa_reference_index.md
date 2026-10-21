# rcwa_reference_index — **순수 python RCWA** reference 라우팅 인덱스 (research-compute 소유)

> ⚠️ **범위**: 이 인덱스는 **python 라이브러리 RCWA(meent · grcwa · torcwa)** 전용이다. 호출자가 "python RCWA"를 지정했을 때만 이 경로로 돈다.
>
> **Lumerical RCWA는 여기 없다** — `lumerical` 에이전트 관할이다. 라이선스로 도는 solver 전부(FDTD·RCWA·STACK)가 그쪽이다.
>
> 두 계열은 **다른 구현**이다. 아래의 수렴 예산(fto/nG)·부호규약·GPU 결론·near-singular 격리 절차를 **Lumerical RCWA에 그대로 옮기지 마라.** 실측 대비: 같은 wedge s1 +60° 지점에서 grcwa는 BLAS 스레드 의존 near-singular로 spread 0.013~0.017인데 Lumerical RCWA는 bit-identical(spread 0.0)이다. 교차검증 수치 대조 목적으로만 서로 참조한다.

RCWA 작업의 최상위 라우팅. 라이브러리별 **자체완결**: 수렴/calibration = `<lib>_convergence`(+`<lib>_api`), **단순 스윕만이면 `<lib>_api`만**. 항상 필요한 공통(부호·격리)은 이 파일, 상황별 상세는 아래 전용 파일로 분리(안 열면 로드 안 됨).

## 라우팅

| 라이브러리 | 역할 | api | convergence |
|---|---|---|---|
| **meent** | **주력** (grcwa 대비 7~8배, near-singular robust, Rayleigh 격리 시 valid) | [meent_api.md](meent_api.md) | [meent_convergence.md](meent_convergence.md) |
| **grcwa** | 교차검증 보조 (CPU, near-singular 취약: BLAS gate·Rayleigh nan) | [grcwa_api.md](grcwa_api.md) | [grcwa_convergence.md](grcwa_convergence.md) |
| **torcwa** | 교차검증·gradient 최적화. ⚠️ **O(N_z²)** — staircase 다층(N_z≥~100)은 부적합, few-layer 메타표면엔 경쟁력 | [torcwa_api.md](torcwa_api.md) | [torcwa_convergence.md](torcwa_convergence.md) |

**상황별 전용 파일 (해당될 때만 열어라 — 평시 로드 불필요):**
- **경사 금속 박막** 작업 → [rcwa_metal.md](rcwa_metal.md) (staircase 연속성 선체크·반사측 TM 한계)
- **wedge s1 재현/게이트** (검증 수치 대조) → memory `reference_rcwa_wedge_s1_values.md` (형상 관측값 — 새 형상엔 무의미)
- **GPU batch/최적화 재시도** 고민 시 → [rcwa_gpu_investigation.md](rcwa_gpu_investigation.md) (전수조사 상세)

## 판정 줄 — `../tools/checks.py` (계산 뒤 필수, 소유: AGENT.md 작업 3·5)

| 함수 | 시점 | 내용 |
|---|---|---|
| A `result_bounds(R,T,eps,tol=0)` | 매 계산 | 유한값·R,T≥0·0≤eps≤1 (R+T+A=1은 정의라 제외) |
| B `requested_vs_used(req, read_meent/read_grcwa/read_torcwa(obj))` | 매 계산 | 요청 대 solver 가 실제 쓴 값 (grcwa nG 는 항상 요청보다 작게 잘림 → `obj.nG` 로 기록) |
| C `convergence_line(path,tol)` | 수렴·calibration | `converge: s_fto, s_Nz, tol, stop=tol\|saturated\|cap` — 규칙 원문은 [[meent_convergence]]·[[grcwa_convergence]] |
| D `mirror_fixture(eps+,eps-,tol)` | **새 형상 도입 시 필수** (대칭 구조 한정) | bare 구조 ±θ 비교 |

## 공통 1 — 부호규약·입력 대조 (교차검증 시 최다 실수)

| | 입력 | 시간규약 | 흡수 매질 예 (PDMS n=1.8, k=0.154) |
|---|---|---|---|
| grcwa | **eps 직접** | e^{-iωt} | eps = (1.8+0.154j)² = 3.216**+**0.554j |
| meent | **n(굴절률)** | e^{+iωt} (코드 추론, README 미명시) | n = 1.8**−**0.154j |
| torcwa | **eps 직접** | e^{-iωt} | eps = 3.216**+**0.554j |

부호 틀리면 gain 매질 → **R>1 폭발로 즉시 감지**(torcwa R=417 실측).
FDTD(Lumerical 2D) 교차검증 시 **편광 라벨 스왑** 주의: Lumerical `pol_angle=0`=p-pol/TM, `90`=s-pol/TE — GUI 표기와 반대다.

## 공통 2 — GPU/병렬 (결론)

**RCWA GPU batch는 이 환경(Windows+RTX3050) 전 경로 불가 → CPU 병렬이 표준.**
- **CPU 표준**: `Pool(물리코어, maxtasksperchild=1)` — 워커=물리코어(`psutil.cpu_count(logical=False)`; `os.cpu_count()`는 논리라 과다), 워커별 **BLAS=1**, `maxtasksperchild=1`(프로세스 누적 차단 = near-singular 폭주 방지, 공통 3). 큰 fto/nG·N_z 배치는 워커 축소(메모리 가드). 실측 speedup **~4배**(07-08 production 132 task, 재spawn 오버헤드 포함 — "6배" 아님).
- 경로별 왜 불가한지·WSL2/클라우드 대안은 **[rcwa_gpu_investigation.md](rcwa_gpu_investigation.md)** (재시도 고민 시만).

## 공통 3 — near-singular(Rayleigh) 실행 안전 (거의 항상 적용)

- 폭주 = **solve 누적(leak) ∧ near-singular 대형 할당의 합작**(실측·메커니즘 → [[meent_convergence]] ★격리). **각 solve = 독립 프로세스 + Job Object RAM 상한**(win32job; 규모별 — 유전체 fto67급 ~15GB, 대형 금속 N_z≥640급 45~60GB 실측. 총 RAM−타 프로그램 몫−시스템 여유 이내로) — 참조 구현 `snippets/iso_worker.py`.
- **Rayleigh 각도** = 회절차수 grazing, `sinθ_R = 1 − m·λ/L`. 정밀값 필요 시 = **meent 격리 실행**(검증: GPU=CPU 1e-15). grcwa는 그 각도 nan.
- 타 무거운 프로그램(FDTD·SPEOS 등)과 동시 실행 시 공유 자원은 **시스템 RAM뿐** → worker RAM 상한으로 칸막이.

---
*wedge s1 검증 수치(교차검증 기준값·수렴 N_z·nG↔fto 환산) → memory `reference_rcwa_wedge_s1_values.md` / 경사 금속 → [rcwa_metal.md](rcwa_metal.md)*
