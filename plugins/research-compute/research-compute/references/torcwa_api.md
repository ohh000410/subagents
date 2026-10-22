# torcwa_api — torcwa 함수 사용법 (research-compute)

torcwa = torch 기반 GPU RCWA + autodiff (SNU **Byoungho Lee** 그룹, Computer Physics Communications 2023, peer-reviewed → 신뢰). 주목적은 **metasurface inverse design(gradient 최적화)**. 수렴 워크플로우는 [[torcwa_convergence]], 공통 결론(GPU/병렬·부호 대조·검증 기준값)은 [[rcwa_reference_index]] — 이 파일은 함수·함정만.

## ★ API 함정 (틀리면 결과 오류)
1. **부호규약 e^{-iwt}**: 흡수 매질 eps 허수부 = **양수** (예: n=1.5, k=0.1 → eps = 2.24 **+** 0.3j). ★ meent(e^{+iwt}, n=n_r−ik → eps 허수부 −0.3)와 **반대**. 부호 틀리면 gain 매질로 해석 → **R 폭발**(R=417 목격 = 즉시 감지). torcwa는 **eps 직접 입력**(n 아님).
2. **편광 매핑**: TE = `amplitude=[0,1]`(Ey, ∥groove) + `polarization='yy'`; TM = `amplitude=[1,0]`(Ex) + `'xx'`.
3. **input/output layer**: 양쪽이 air면 `add_input_layer`/`add_output_layer`를 **호출하지 말 것** — Sin=[]로 두고 solve가 Sin[0] 접근 → IndexError. 미호출 = free-space(air) 기본(meent n_top=n_bot=1과 동일, 우리가 원하는 것).
4. **freq = 1/λ**. `add_layer(thickness, eps=(Nx,Ny) tensor)`. total R/T = 모든 propagating order에 대해 `|S_parameters(orders=[m,0], port='reflection'/'transmission', polarization=, power_norm=True)|²` 합.
5. **complex128 + avoid_Pinv_instability=True** (near-singular 안정). ⚠️ complex64(fp32)는 빠르지만(측정: RTX3050) near-singular(Rayleigh 근처)에서 `linalg.inv` singular crash — 아래 참조.
6. **keyword-only 인자**: `rcwa()`의 dtype 이후, `source_planewave()`·`S_parameters()`의 `*` 뒤 인자는 **이름 지정 필수**(위치 인자로 넘기면 TypeError).

## 검증
- 교차검증 게이트 통과.

## 속도·자원 (실측 2026-07-11~13)
- ★ **torcwa는 층수 제곱 O(N_z²)** — `solve_global_smatrix`가 층 연결마다 전 층의 모드 계수(C)를 갱신(field 재구성용 설계). CPU fp64 1스레드 실측 피팅: **t ≈ 0.36·N_z + 0.0102·N_z²** (nz 20/40/80/320 = 11.3/30.4/94.3/1164.5s, 오차 0.2%). meent는 O(N_z)라 N_z=320에서 **58배 차이**.
  - 함의: **staircase 다층(N_z≥~100)은 torcwa 부적합** — 설계 영역이 few-layer 메타표면. few-layer 구조에선 경쟁력 있음(커널 자체는 numpy 동급~우위, 자체 벤치).
- GPU **fp64(complex128)**: 단일 solve 507s @N_z=320 (RTX3050=Ampere GeForce, fp64 = fp32의 정확히 **1/64**) — 측정 PC 에선 GPU 가 같은 PC 의 CPU(1164s)보다 빠름.
- **fp32(complex64)**: 17s로 빠르나 near-singular(56°)서 singular crash → 정밀 계산 부적합([[torcwa_convergence]]).
- 각도/파장 **batch 미지원** — 공식 예제 전부 for-loop 순차. 환경 전체 GPU/병렬 결론(전 경로 실측)과 CPU 병렬 표준은 [[rcwa_reference_index]] 공통 2.

## 참고
- GitHub: https://github.com/kch3782/torcwa (Examples 0~6: Fresnel·파장sweep·기하sweep·gradient·형상/topology 최적화 — 전부 for-loop). 논문: Computer Physics Communications 282 (2023) 108552.
