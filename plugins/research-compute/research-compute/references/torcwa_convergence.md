# torcwa_convergence — torcwa 수렴 프로토콜 (research-compute)

**torcwa 수렴/calibration = 이 파일 + [[torcwa_api]](함수·부호규약).** 단순 스윕만이면 [[torcwa_api]]만. 공통 결론(GPU/병렬·near-singular 격리·부호 대조)은 [[rcwa_reference_index]].

## ★ 현재 상태 (2026-07-11): 자체 수렴 프로토콜 미수립 — meent 수렴점 차용

torcwa로 **독자적인 2D path 수렴을 아직 돌린 적 없음.** 지금까지의 사용 = meent가 찾은 수렴점을 그대로 차용해 값 검증만 수행. 교차검증 용도(같은 수렴점에서 값 대조)로는 이걸로 충분함.

- torcwa를 **단독 신뢰 소스**로 신규 형상에 쓰려면: [[meent_convergence]]의 2D path 절차(경량 시작 → 축별 probe ×1.5 → s 비례 이동 → 포화 종료)를 그대로 적용. torcwa order=[fto_half, 0]가 meent fto=(fto_half,0)와 같은 의미라 축 정의 동일. 형상 확인(유효 유전율 플롯) 개념도 동일([[meent_convergence]] ★ 새 형상 첫 calibration).
- near-singular 거동이 meent와 같다고 **단정 금지** — Fourier factorization 구현이 다름. 첫 calibration 시 fto sweep으로 발산/near-singular 존재 확인.

## 수치 안정성 (실측)

- **dtype = complex128 + `avoid_Pinv_instability=True` 필수.** complex64(fp32)는 빠르지만(17s vs fp64 507s) **near-singular(Rayleigh 근처 56°)에서 `linalg.inv` singular crash 실측** → 정밀 계산·수렴 테스트에 fp32 금지.
- fp64는 RTX 3050에서 507s/solve로 실용 불가 → **torcwa 수렴·대량 계산은 사실상 CPU 또는 다른 라이브러리**(meent) 영역. torcwa의 실용 가치는 교차검증(단발)·향후 GPU 환경(WSL2/클라우드)에서의 gradient 최적화.

## 편광·Rayleigh

- 편광별 수렴점 분리 원칙은 grcwa/meent와 동일([[meent_convergence]]) — TE/TM 각각 calibration.
- Rayleigh 각도 정밀값은 **meent 격리 실행이 검증된 경로**([[rcwa_reference_index]] 공통 3). torcwa의 Rayleigh 격리 안정성은 미검증.
