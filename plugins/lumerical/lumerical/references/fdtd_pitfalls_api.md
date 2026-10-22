# API·운영 함정

## Monitor 결과 추출 실패
`Done. Elapsed...` 정상 완료인데 `getresult` 시 `Can not find result 'T'` = monitor 저장량 RAM 초과 → fsp 부분 손실. 회피 순서: frequency points↓(선형) → monitor 영역↓ → mesh_accuracy/dx 완화 → monitor 수↓(6면 박스 → 단일면+대칭).

## 엔진 오류는 run() 이 알리지 않는다
- `fdtd.run()` 은 엔진 수준 오류에서 예외를 던지지 않는다. 단일 프로세스 엔진(`Local Computer`)은 바로 정상 반환하고, 증상은 나중에 `Can not find result '<X>' in the result provider '<monitor>'` 로만 나타난다. MS-MPI 엔진은 같은 오류에서 `run()` 이 55분 넘게 반환하지 않는다(엔진 프로세스 유휴, 모달 없음)
- 진짜 메시지는 `.fsp` 옆 `<fsp 이름>_p0.log` 에만 있다. 예: `The program terminated due to an error:Error CPU simulation cannot run with FDTD property express mode active.`
- `Can not find result` 가 나오면 `_p0.log` 부터 연다 — 엔진이 셋업을 거부했으면 거기 이유가 있다(위 RAM 초과와 구별)
- 시험하지 않은 솔버 속성은 버리는 run 에서 짧은 timeout 으로 먼저 확인한다. 배치는 케이스마다 결과를 디스크에 쓴다 — `| tail` 파이프에 묶으면 멈췄을 때 중간 출력이 다 사라진다
- 알려진 유발 설정: `express mode`=1, `pml termination`=`PEC` — 둘 다 GPU 전용(`fdtd_gpu_support.md`)

## _p0.log 에서 종료 시각 읽기
- 조기 종료는 `_p0.log` 에 `Early termination of simulation, the autoshutoff criteria are satisfied.` 가 있을 때만 확정한다. 종료 시각 = `Completed N iterations, or X s of Simulation Time` 줄의 X(초, fs 는 ×1e15)
- `Auto Shutoff: <값>` 진행 줄의 숫자는 시간이 아니라 감쇠 비율이다. `Auto shutoff ... N fs` 꼴 정규식은 v232·v242 로그 어디에도 맞지 않아 모든 케이스를 "상한 도달"로 잘못 분류한다 — 임계값마다 결과는 다른데 종료 시각이 전부 상한이면 파서부터 의심한다
- `Completed` 줄이 없는 로그 = 중단된 run

## sweep case_id 충돌
`case_id` 는 `<case_id>.fsp`·`<case_id>_p0.log` 의 이름이 되고, 종료 시각·상한 도달 여부는 `_p0.log` 에서만 얻는다. sweep 변수를 자릿수가 모자라게 포맷하면(예: `f"{a:.1f}"` 가 0.15·0.10·0.05 를 한 id 로) 다른 케이스가 한 로그를 공유한다 — 순차 실행에선 우연히 맞아 보여도 `.fsp` 출처가 사라지고, 순서를 바꾸거나 병렬이면 종료 시각이 조용히 뒤바뀐다. 격자를 넓히기 전에 전체 격자에서 id 가 유일한지 확인한다.

## 디스크 가득 → 엔진 정지
로그에 `memory overflow` 다음 `Unable to write project file` 이 나오면 RAM·VRAM 이 아니라 디스크 여유부터 본다. 진행 중이던 `.fsp` 가 1바이트로 잘리고(`.bak` 만 남음) 엔진 프로세스들이 오류 없이 CPU 약 22 % 로 6시간 넘게 멈춘 사례가 있다. 무인·야간 배치 전에 여유 공간이 수십 GB 이상인지 확인한다. 복구 = 자기 엔진 PID 만 종료 → 공간 확보 → 마지막 정상 행부터 재개. 케이스마다 append-only 로 저장하면 손실이 진행 중이던 1케이스로 한정된다.

## 고아 엔진 프로세스
`fdtd.run()` 을 감싼 셸이나 python 이 밖에서 종료돼도 `fdtd-solutions.exe`·`fdtd-engine-msmpi.exe` 는 별도 콘솔 세션이라 살아남아 계속 돈다(로그도 계속 는다). lumapi 에는 재접속 API 가 없어 그 run 의 결과는 회수할 수 없다. `tasklist /FI "IMAGENAME eq fdtd-engine-msmpi.exe"` 로 PID 를 찾아 자기 것만 `taskkill /PID <pid> /F /T` 로 끝내고, 정리를 확인한 뒤 그 케이스를 처음부터 다시 돌린다.

## 기타
- Conformal mesh(CMT) 자동 → 메모리 리포트 약간 부정확
- 두꺼운 도메인(H>100µm) FP 공진 스펙트럼 → 스무딩. 10nm 이하 입자 → override mesh
- TFSF cross-section 정규화 = TFSF 면적(monitor 면적 아님) → `fdtd_cross_section_setup.md`
