# FDTD Resource / 병렬 구성

에이전트는 리소스 설정을 생성·변경하지 않는다. `fdtd.run()` 은 사용자 계정 구성(`~/AppData/Roaming/Lumerical/FDTD Solutions.ini` `[jobmanager]`) 을 따른다(기존 실행 스크립트에 `setresource` 0건).

## Resources 창 (File → Resources)
이 PC 의 값(preset·processes·threads) = 이 PC 환경 값(메모리). `tools/check_setup.py` 에 `intended["processes"]` 로 넘긴다.
- processes = MPI 도메인 분할 프로세스 수(`fdtd-engine-msmpi` N개)
- threads = 프로세스당 OpenMP 스레드 (총 = processes × threads)
- capacity = job manager 큐(`runjobs`/sweep) 동시 job 수. `fdtd.run()` 순차 실행 무관
- 기본값 = 물리 코어 수 자동감지(기존 행을 다른 수로 바꿔도 새 리소스는 물리 코어 수로 생성, 6코어 PC 실측). FDTD 권장 = 프로세스 = 물리 코어, threads = 1, HT 비사용
- RCWA 리소스 = 1 proc × N thread — MPI 분할 미지원(`multiProcs=false`)
- `job launching preset` 은 사용자 설정 파일에 남아 세션 간에 유지된다. `Local Computer` 로 바꾸면 `processes` 가 1 이 되고, 다시 `Remote: Microsoft MPI` 로 돌려도 `processes` 는 1 로 남는다 — 프리셋은 정상인데 1 프로세스로 돈다. 복구 = 프리셋과 `processes` 를 둘 다 되돌리고 새 세션에서 읽어 확인(`tools/check_setup.py` 는 `processes` 가 이 PC 기대값보다 적으면 FAIL)

## FDTD 객체 Advanced options "Parallel engine options" (Resources 와 별개)
`set process grid`(기본 off) + `nx`·`ny`·`nz`(기본 1·1·1, placeholder, 스레드 아님). 켜면 nx×ny×nz = processes. 기본 off 유지.

## 스크립트 API
`getresource("FDTD")`(개수) / `getresource("FDTD", i)`(속성 20개) / `getresource·setresource("FDTD", i, "processes")` / `addresource`·`deleteresource`. 속성: active, name, hostname, processes, threads, capacity, job launching preset, mpi executable, mpi extra command line options, mpi no default options, mpi use processor binding when available, mpi bypass on localhost, solver executable, solver extra command line options, solver checkpoint directory, solver no default options, solver create log for all, scheduler command, submission script, GPU Device. design environment 리소스는 script 접근 불가(`Invalid solver`). `solver create log for all`=0 → `*_p0.log` 만 생성.

## GPU
GPU 불가(v242). 상세 → [fdtd_gpu_support.md](fdtd_gpu_support.md)
