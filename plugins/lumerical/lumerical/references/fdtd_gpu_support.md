# GPU 지원

측정 조건: GPU = RTX 3050 8 GB, CC 8.6, CUDA 12.6 (Driver 560.94). 설치 = v242(2024 R2.3) 와 v232(2023 R2) 를 한 PC 에.

## v242 (2024 R2.3): GPU 불가 (측정한 설치)

- `v242\bin\` 에 GPU/CUDA 바이너리 없음 (같은 PC 의 `v232\bin\fdtd-gpu-engine-app.exe` 는 존재)
- `express mode = 1` → CPU 엔진 거부: `Error CPU simulation cannot run with FDTD property express mode active.`
- MPI 무관 — msmpi 다중·단일 프로세스, 비-MPI `Local Computer` 전부 동일. 다중 프로세스면 오류 미전파 + `run()` 55분+ 무한 블로킹(엔진 유휴, 모달 없음)
- resource configuration 에 GPU 필드 없음. `job launching preset` = `Local Computer` / `Remote: Intel MPI` / `Remote: Microsoft MPI` / `Custom`. GPU 인식은 정상
- `express mode` = FDTD 객체 속성 (`setresource` 불가)
- `pml termination` `PEC` 도 GPU 전용 (`CPU simulation only supports 'pmc'`)
- 미해결: 설치 패키지 누락 / 별도 배포 / 학술 entitlement 제외.

## v232 (2023 R2): GPU 엔진 있음

엔진 = `v232\bin\fdtd-gpu-engine-app.exe`. 이 PC 에서 v232 를 쓸 수 있는지·GPU 모드 설정 = 이 PC 환경 값(메모리).

2023 R2 GPU 미지원: TFSF, BFAST, Advanced permittivity(Index Perturbation·Flexible Material Plugin), 2D, Movie/Time monitor, 2D 광전도성(PEC 외), Legacy Uniaxial PML, Checkpoint. 출처 https://optics.ansys.com/hc/en-us/articles/17518942465811
→ cross-section(TFSF+분산 fit)·dispersive sweep·2D 전부 불가. 현재 노하우는 CPU 전제.

업그레이드 시 "Getting started with running FDTD on GPU" 미지원 표 재확인. 2025 R2 "GPU Simulation and Monitor Data" 문서 존재.
GPU 모드: GUI Resources → Device Type `GPU`, 또는 `~/AppData/Roaming/Lumerical/FDTD Solutions.ini` `FDTD\GPU-mode=true`.
