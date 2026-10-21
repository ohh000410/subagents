# meent_api — meent 함수 사용법 (research-compute)

meent 0.12.0: GPU 지원 RCWA(numpy/torch/jax backend) + autodiff(gradient 최적화). 수렴 워크플로우는 [[meent_convergence]], 공통 결론(부호 대조·GPU/병렬·검증 기준값)은 [[rcwa_reference_index]] — 이 파일은 함수·함정만.

## 설치·환경
- `pip install meent` (python 3.14 OK, 검증됨). 의존: numpy, scipy (torch backend는 `tqdm` 별도 — 아래 GPU 섹션). backend: numpy(CPU) / torch(CPU·GPU) / jax(CPU — **Windows는 JAX GPU 불가**, Linux/WSL2만).
- **GPU 실익은 autodiff(gradient 최적화)뿐** — 근거·함정·설치는 아래 GPU 섹션과 [[rcwa_reference_index]] 공통 2.

## ★ API 함정 (틀리면 결과 오류)
1. **부호규약 e^{+iwt}**: ucell에 **n = n_r − i·k** (PDMS = 1.8 **−** 0.154j). ★ eps 아니라 **n(굴절률)** 입력, 내부에서 n²=eps(소스 `eps_matrix = ucell**2` 확인). eps 직접 넣으면 완전 다른 값. **부호 틀리면 R>1로 즉시 감지**. (e^{+iwt} 라벨은 코드 동작 기반 추론 — README 미명시. 확실한 것: n=n_r−ik 입력이며 grcwa/torcwa의 e^{-iwt}·eps 직접과 반대.)
2. **n_bot = 1.0**(air), 기판(PDMS)은 ucell **마지막 층**으로 명시.
3. **phi=None** = 1D TE/TM. phi=0 넣으면 conical formulation으로 전환(느리고 결과 다름).
4. **ucell 층 순서**: z-slice 쌓는 방향 주의 — 뒤집으면 eps가 **균질 슬랩값**으로 나와 즉시 감지. 위(tip, 좁은 쪽)→아래(base, 넓은 쪽) 순서 확인.
5. **fto (Fourier order)**: **fto_half** = 0차 중심으로 한쪽 최대 차수, 총 유지 orders = **2·fto_half + 1**. 경사 입사면 propagating 차수가 비대칭((1+|sinθ_inc|)·L/λ 쪽이 큼)이지만 fto_half는 ±대칭이라 큰 쪽을 커버하면 된다. ★ 수렴점은 [[meent_convergence]] 2D path가 s로 찾으니 하한을 미리 계산할 필요 없음(시작 경량, path가 올림).

## 검증
- 교차검증 게이트 통과 — 수치·조건은 memory `reference_rcwa_wedge_s1_values.md`.

## 속도
- **fto_half=67·N_z=320 solve ~19–21s** (2026-07-10~13 반복 실측 일치; 초기 기록 38s는 재현 안 됨 — 환경 차 추정, 폐기). 전각도(22각도) ~13분(numpy CPU, 6워커 병렬, 2026-07-08 기록). 대량 계산·형상 최적화(gradient/autodiff)에 적합.

## field 시각화 API (calculate_field)
- `field_cell = mee.calculate_field(res_x, res_y=1, res_z)` — conv_solve **후** 호출. 반환 shape `(N_layers·res_z, res_y, res_x, 3)`.
- **1D 성분 순서**: TE(pol=0) `[Ey, Hx, Hz]` → |E|²=|Ey|². TM(pol=1) `[Hy, Ex, Ez]` → |E|²=|Ex|²+|Ez|².
- **z 순서**: `field_cell[0]`=top(입사면=ucell 층0), `field_cell[-1]`=bottom(마지막 층). res_z=층당 z픽셀(층 두께 다르면 층별 dz/res_z로 실좌표 계산 — 균일 가정 금지).
- meent 제공 `mee.field_plot(field_cell)`은 |성분|² imshow만(픽셀축·형상 overlay 없음) — 실사용엔 부족.
- **air buffer**: field/정재파를 구조 밖(위/아래 air)까지 보려면 ucell 앞/뒤에 air 유한 층 추가. ★ 흡수율(1−R−T)엔 무관(반무한 n_top/n_bot이 처리) — air 넣어도 R·T 불변. FDTD의 PML spacer 직관과 다름.

## GPU (torch backend) — 검증 2026-07-09
meent 0.12.0 torch GPU는 함정 3개 우회하면 작동(RTX 3050·CUDA 12.6 검증: eps=CPU와 |Δ|=0.000000). ★ **속도: 2026-07-10 재측정 production fto67/N_z320에서 GPU/CPU=1.01x = 이득 없음**(초기 "18%"는 소형 케이스 한정). eigendecomp가 CPU라 단일 1D solve는 GPU 무의미 — **각도/파장 batch도 미지원**(공통 2)이라 GPU 진가는 autodiff뿐. **전용 venv 권장(전역 설치 금지).**
1. **의존성**: CUDA torch(`cu126` wheel은 **py3.14도 존재**: torch 2.13.0+cu126) + **`tqdm`**(torch backend가 import하는데 meent 의존성에 누락 → 미설치 시 ModuleNotFoundError).
2. **device는 정수 1**: `call_mee(backend=2, device=1, ...)`. ★ 문자열 `'cuda'`는 **setter 버그로 ValueError**(`__init__`은 'cuda' 받지만 `self.device=` setter가 0/1/torch.device만 허용).
3. **패치 필수**: `on_torch/emsolver/_base.py`의 `get_kx_ky_vector` `np.sin(self.theta)` → `torch.sin(self.theta)`. (일반 입사각(θ<π/2) 경로가 `np.sin(cuda tensor)`를 호출해 "can't convert cuda tensor to numpy"로 실패. **GitHub main도 동일 미수정** = meent가 torch GPU 미검증.) venv 설치본 직접 수정 또는 스크립트 런타임 monkeypatch — 재설치 시 사라지니 주의.
- eigendecomp는 torch도 GPU 미구현(CPU 계산 후 전송). 참조 구현 `snippets/gpu_test.py`.

## GPU 자원 한계 (RTX 3050 8GB, 2026-07-10)
- **VRAM 8GB 한계**: fto150/N_z600은 VRAM 초과 → CUDA OOM. VRAM ∝ (2·fto+1)²·N_z (실측 fto110=3.9GB, fto130=6.5GB, fto150>8GB). production fto67=~1.5GB 안전. 큰 케이스는 CPU(64GB RAM).
- **연속 GPU worker는 VRAM 즉시 반환 안 함**: 앞 worker가 죽거나 OOM나면 VRAM 안 비워져 다음 worker OOM. 여러 solve 격리 실행(특히 near-singular 채우기)은 **CPU 격리 권장** — 값은 GPU와 |Δ|~1e-15 동일.
- **단일 GPU(i5-12400F=iGPU 없음) → 큰 VRAM 작업 시 화면 먹통**: VRAM 8GB 초과 시 시스템 RAM 스필 → 데스크톱 프리즈. fto67 정도는 안전. near-singular 폭주·격리 실행 안전은 [[meent_convergence]] 참고.

## 참고 (공식 자료)
- GitHub: https://github.com/kc-ml2/meent — README·예제·API (부호규약·ucell·geometry 함수·backend). 함수 상세·버전 업데이트는 여기서 확인.
- 논문: https://arxiv.org/abs/2406.12904 (Meent: Differentiable Electromagnetic Simulator for ML).
