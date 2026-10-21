# grcwa_api — grcwa 사용법 (research-compute)

grcwa: 순수 python RCWA + autograd(CPU). 수렴 방법론은 [[grcwa_convergence]] 공유, 공통 결론(부호 대조·GPU/병렬·검증 기준값)은 [[rcwa_reference_index]] — 이 파일은 grcwa 고유 API·함정만.

## 환경·BLAS
- import 순서: `OMP_NUM_THREADS`·`OPENBLAS_NUM_THREADS`·`MKL_NUM_THREADS`="1"를 **numpy/grcwa import 前** os.environ으로. (BLAS=1 재현성 근거·near-singular spread gate는 [[grcwa_convergence]] §0·§2.)

## ★ fallback OFF (재현성 필수)
- **dng-shift wrapper 쓰지 말고** 코어 함수 직접 호출. fallback은 near-singular를 자동 회피(dng를 몰래 shift)하지만 **어느 nG가 실제 쓰였는지 은닉 → 재현성 파괴**. 발산은 [[grcwa_convergence]] §3처럼 명시 처리.

## 함수 흐름
```
obj = grcwa.obj(nG, L1=[L,0], L2=[0,1], freq, theta(rad), phi=0, verbose=0)
obj.Add_LayerUniform(thick, eps)      # 균일 층 (air/substrate)
obj.Add_LayerGrid(dz, Nx, Ny)         # 패턴 층 (z-slice)
obj.Init_Setup()
obj.GridLayer_geteps(eps_flat)        # 패턴 층 eps grid (flatten)
obj.MakeExcitationPlanewave(...)      # TE: (0,0,1,0) / TM: (1,0,0,0)
R_ord, T_ord = obj.RT_Solve(normalize=1, byorder=1)
eps = 1 - sum(R_ord) - sum(T_ord)
```
- **nG** = Fourier order 절단 파라미터 (README: "actual number might be smaller" — 실제 유지 개수는 격자에 맞게 잘림; `Init_Setup` 후 `obj.nG` 가 실사용값으로 덮어써짐 → 기록·캐시 키는 이 값, `checks.read_grcwa`·`requested_vs_used`). 실제 Nx,Ny는 `Init_Setup()` 후 `obj.G`에서 2·max|G|+1로 계산. ⚠️ `get_grid_size`는 **grcwa 공식 API가 아니라 우리 자작 헬퍼** — 공식 함수로 오인 금지.
- **eps 직접 입력**(meent와 반대 — [[meent_api]]는 n(굴절률) 입력).

## 발산·수렴
- 하드 발산 R>1.5. 수렴 방법론(near-singular·능선·N_z·세트·필터) = [[grcwa_convergence]].

## 속도
- tilted/sheared는 N_z 커서 무거움 — **O(N_z·nG³)** (실측: nG320·N_z640 ≈ 858s). 역할 분담(meent 주력·grcwa 교차검증)은 [[rcwa_reference_index]] 라우팅 표.
