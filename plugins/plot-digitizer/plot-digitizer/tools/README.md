# plot-digitizer/tools

plot-digitizer 에이전트 도구. 검증 도구 범위 = 실제로 일어났던 사고 유형만. **경고·보고만** 한다 — 점·눈금을 자동 삭제·제외·보정하지 않는다.

| 파일 | 시점 | 입력 | 출력 |
|---|---|---|---|
| `picker_server.py` | 캘리브 (클릭) | 이미지, 포트 | `_clicks.json` (사용법 = agents/plot-digitizer.md 클릭 picker) |
| `check_calibration.py` | 캘리브 직후, 추출 전 (절차 3) | calib.json (+ `--overlay <원본> <png>`) | 눈금별 재투영 오차(px)·RMS, dropped 후보 순위, 테두리에 가린 끝 눈금 후보, polar R 사용값 vs 격자 원 LSQ. `--overlay` = 눈금별 재투영 위치를 원본 위에 그린 캘리브 체크 overlay png (flag 눈금 빨강). 끝줄 `check_calibration: PASS|WARN|FAIL N tick, RMS x px`. 종료코드 0 = flag 없음 / 1 = WARN / 2 = 눈금 0개(FAIL) |
| `check_extraction.py` | 추출 CSV 저장 뒤 (절차 6) | wide 또는 long(`series,x,y`) CSV, 헤더 자동 감지 (+calib.json) | flag: `empty` `gap` `nan_run` `interp_run` `out_of_range` `near_tick`. 끝줄 `check_extraction: PASS|WARN|FAIL flag N건`. 종료코드 0 / 1 / 2 = 곡선 0개(FAIL) |
| `calib_model.py` | (공용 모듈) | — | calib.json 스키마·`save`/`load`·값↔픽셀 변환 `to_px`/`from_px` (추출 스크립트와 검사 도구가 같은 변환 사용) |
| `tests/run_synthetic.py` | 도구 수정 뒤 | 없음 (메모리 렌더) | 합성 정답 7유형 결함/정상 표 (유형 6 long CSV, 7 calib.json·overlay 는 임시 폴더에 파일을 써 CLI 까지 검사), 어긋나면 종료코드 1 |

- calib.json = 캘리브 산출물: 눈금 측정·변환식 확정 시점에 `calib_model.save`, 추출 스크립트는 `load` + `from_px` 로 변환. 스키마 = `calib_model.py` docstring. 픽셀 = 원본 전체 이미지 좌표. cartesian 선형 축 / polar(반원·전원) radial 선형만.
- 기준: 눈금 재투영 1 px (`--tol-px`), 빈 구간 = x 간격 > 중앙값 × 3 (`--gap-factor`), 눈금 발자국 = 테두리에서 `tick_len_px`(실측값) + 눈금선 ±2 px (`--near-px`).
- `near_tick` 은 calib 에 `tick_len_px`·`tick_sides` 가 있을 때만. 이웃과 튀는 고립점은 flag 하지 않는다(실제 데이터일 수 있음).
- 행 자체가 CSV 시작·끝에서 빠진 경우(곡선 앞부분 통째 누락)는 잡지 못한다 — overlay 로 확인.
- 하지 않는 것: 로그·범주형 축, 패널 자동 분할, 점별 불확도 전파.
- 검사별 근거 = `../references/calibration_extraction.md` 의 절(각 파일 docstring 에 표시).

```
C:/Python314/python.exe tools/check_calibration.py calib.json --overlay 원본.png calib_overlay.png
C:/Python314/python.exe tools/check_extraction.py out.csv --calib calib.json
C:/Python314/python.exe tools/tests/run_synthetic.py -v
```
