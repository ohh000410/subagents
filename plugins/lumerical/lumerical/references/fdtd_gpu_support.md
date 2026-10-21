# GPU 지원 — 이 워크스테이션 한정

## v242 (2024 R2.3): GPU 불가

- `v242\bin\` 에 GPU/CUDA 바이너리 없음 (`v232\bin\fdtd-gpu-engine-app.exe` 는 존재)
- `express mode = 1` → CPU 엔진 거부: `Error CPU simulation cannot run with FDTD property express mode active.`
- MPI 무관 — msmpi 6/1 프로세스, 비-MPI `Local Computer` 전부 동일. 다중 프로세스면 오류 미전파 + `run()` 55분+ 무한 블로킹(엔진 6개 유휴, 모달 없음)
- resource configuration 에 GPU 필드 없음. `job launching preset` = `Local Computer` / `Remote: Intel MPI` / `Remote: Microsoft MPI` / `Custom`. RTX 3050 인식 정상
- `express mode` = FDTD 객체 속성 (`setresource` 불가)
- `pml termination` `PEC` 도 GPU 전용 (`CPU simulation only supports 'pmc'`)
- 미해결: 설치 패키지 누락 / 별도 배포 / 학술 entitlement 제외.

## v232 (역사 — 실행 불능)

| 항목 | 값 |
|---|---|
| GPU | RTX 3050 8 GB, CC 8.6, CUDA 12.6 (Driver 560.94) |
| 엔진 | `v232\bin\fdtd-gpu-engine-app.exe` |
| 설정 | `FDTD\GPU-mode=false` (CPU MSMPI 6 procs) |

2023 R2 GPU 미지원: TFSF, BFAST, Advanced permittivity(Index Perturbation·Flexible Material Plugin), 2D, Movie/Time monitor, 2D 광전도성(PEC 외), Legacy Uniaxial PML, Checkpoint. 출처 https://optics.ansys.com/hc/en-us/articles/17518942465811
→ cross-section(TFSF+분산 fit)·dispersive sweep·2D 전부 불가. 현재 노하우는 CPU 전제.

업그레이드 시 "Getting started with running FDTD on GPU" 미지원 표 재확인. 2025 R2 "GPU Simulation and Monitor Data" 문서 존재.
GPU 모드: GUI Resources → Device Type `GPU`, 또는 `~/AppData/Roaming/Lumerical/FDTD Solutions.ini` `FDTD\GPU-mode=true`.
