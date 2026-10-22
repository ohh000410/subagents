# origin-plot/tools

origin-plot 에이전트 실행 모드 검증 도구. 범위 = 실제로 실패했던 함정 중 **값으로 되읽히는 것**만. 판정 PASS / FAIL.

| 함수 | 시점 | 실패 시 |
|---|---|---|
| `open_session()` | 생성 스크립트 시작 | Origin 이 이미 떠 있음 · `__ready` 왕복 실패 · `PageBases.Count != 0` → `VerifyError` |
| `ex(app, stmts, tag, scope=None)` | LabTalk 를 보낼 때마다 | 진행 카운터로 멈춘 문장 · numpy repr(`np.float64(...)`) → `VerifyError` + 저장 없이 종료 |
| `verify(app, intended)` | 그리기 끝, png export · Save 전 | 페이지 집합 · 레이어 수 · 축 범위 · 범례 위치/부재 · 워크시트 모양/셀 · PE 폴더 · **눈금(기본 켜짐, 모든 그래프 레이어)** → `VerifyError` + 저장 없이 종료 |
| `close(app, saved=None)` | Save 뒤 | 저장 파일 없음/0 byte → `VerifyError` (종료는 함) |
| `origin_verify.py --after [--wait 30]` | 스크립트 종료 뒤 (별도 명령) | Origin 프로세스 잔존 → 종료코드 2, PID 별 보이는 창(모달 후보) 출력 |

별도 프로세스 검증·`.opju` 재로드는 쓰지 않는다 (Origin 은 COM 참조를 놓으면 종료, 재로드는 모달 위험). 스타일·색·선·심볼·`page.width`·3D 시점·렌더 글자 크기는 검사하지 않는다 → png 확인.
사용법·`intended` 스키마 = `origin_verify.py` docstring. 검사별 근거 = 각 검사 주석과 보고의 `ref` 필드(`../references/` 아래 파일).

## 눈금 검사 (2026-10-18)

`intended` 에 키가 없어도 프로젝트의 모든 그래프 레이어에 적용된다 (스타일 기본값 5 가 모든 그래프의 규칙이므로). 값 되읽기만 쓴다.

- major 눈금 수 = `layer.x/y.inc` 의 배수(0 기준)가 `[from, to]` 안에 드는 개수, 양 끝 포함. png 픽셀과 29/29 범위 일치. 최소 기본 3 (Origin 자동 축척이 22개 범위에서 낸 최소값; 4 로 잡으면 Origin 자체 출력이 FAIL). 더 엄격히 = `intended["ticks"] = {"[Graph1]1!": {"min": (4, 4)}}`. 선형 축(`type==1`)만 센다 — 로그 등은 "not counted" 로 보고.
- 방향 = `layer.x/y.ticks & 3 == 1` (안쪽), `layer.x2/y2.ticks & 3 == 0` (없음). 실측: 0 없음, 1 안, 2 바깥, 3 양쪽, 상위 비트는 방향에 무관(4 없음, 5 안, 8 없음, 9 안, 10 바깥, 12 없음). **Origin 기본값은 x/y = 10(바깥), x2/y2 = 5(안)** → 스타일 줄을 안 보내면 FAIL.
- 끄기: 레이어별 `{"style": False}`(방향만), 전체 `"ticks": False`(크롬 없는 선화·3D·행렬).
- 시험: `tests/ticks_defect_injection.py <case>` (good, good_min4, min5, two_ticks, outward, top_tick, right_tick, untouched, off). 케이스마다 Origin 세션 하나, 사이에 `--after`. 근거 = `../references/origin/page_and_axes.md` 「눈금 방향과 개수」.
