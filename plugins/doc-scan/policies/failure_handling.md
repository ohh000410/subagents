# 실행 에이전트 실패 처리 — 공통 골격

산출물을 만드는 모든 실행 에이전트 공통 정책.

## 1. 실패의 정의 — "에러가 안 났으니 성공"을 금지한다

각 에이전트는 무엇이 실패인지 목록으로 명시한다. 최소 다섯 갈래:

1. **예외·에러** — traceback, COM 오류, 로그의 `[FATAL]`
2. **되읽기 대조 불일치** — 넣은 값과 되읽은 값이 다름
3. **결과 품질·타당성 위반** — 도메인 기준 미충족(겹침·NaN·0/음수·전 case 동일값 등)
4. **task 미완료** — 산출물 저장 전 응답, graceful close 누락, 검증 생략
5. **타임아웃 초과**

## 2. 되읽기 대조 — 조용한 실패를 잡는 유일한 장치

설정하거나 만든 것을 다시 읽어 의도와 대조한다.

- Inventor `HoleFeature`는 예외 없이 `Count`까지 올리고 실제로는 안 깎을 수 있다 — 체적 델타로 잡는다.
- Origin `doc.Modified=0;`은 True를 반환하고도 무효. 3D `layer.*`는 없는 속성도 rc=1.
- Lumerical `pml profile` 설정이 `pml layers`를 기본값으로 되돌린다 — `getnamed`로 확인.

**반환값이 성공을 보장하지 않는다.** 판정 채널은 설정한 경로와 다른 경로여야 한다(아래 표).
**검증 장치 자체가 캐시될 수 있다.** Inventor `MassProperties`는 `CacheResultsOnCompute=False`가 없으면 이전 값을 돌려준다 — 검증 도구를 처음 쓸 때 그 도구가 갱신되는지부터 확인한다.
**실행이 비싼 도메인은 작업 전에 확인한다** — SPEOS는 Compute 전에 되읽는다.
되읽을 설정이 없는 계산·추출 에이전트는 **독립 경로로 같은 값을 다시 구해 대조**한다(research-compute의 cross-check).

## 3. 진단 순서 — 재시도 말고 위치부터 특정한다

재시도·워밍업·sleep을 먼저 하지 않는다.

1. 어디서 멈췄는지 특정 — 진행 마커·카운터
2. 알려진 함정 목록과 대조
3. 그 자리에서 `[UNRESOLVED]` 기록
4. 대체 경로를 한 번에 병렬 시험
5. 막히면 외부 정답 소스와 대조(아래 표)
6. 원인 확정 후 같은 패턴을 전수 재점검

## 4. 한도 — 횟수가 아니라 진전 여부로 판단한다

| 층위 | 한도 |
|---|---|
| 호출 하나 실패 | 세지 않는다. 원인이 좁혀지는 중이면 계속 |
| 한 목표가 막힘 | 서로 다른 접근 2~3개 실패 + 새 가설 없음 → 그 목표만 포기, 나머지 계속 |
| 세션 사망(hang·모달) | **2회면 즉시 반환** |
| 전체 진행 불가 | 즉시 반환 |
| **환경·라이선스 문제** | **재시도 0회, 즉시 반환.** 에이전트가 고칠 수 없다 |

"시도"는 서로 다른 접근이다. 같은 코드 반복은 1회로도 치지 않는다.

## 5. 기록 — 실패는 발견 즉시

- 실패를 확인하면 그 자리에서 agent-memory에 `[UNRESOLVED]`로 기록한다. 세션이 hang·모달로 죽으면 그때까지의 발견이 사라진다.
- 실패한 시도도 함께 적는다.
- 해결되면 `[RESOLVED]`로 전환하고, 그 증상으로 과거 적립된 규칙이 있으면 철회한다.
- 기록 후 `MEMORY.md` 인덱스를 반영한다.

## 6. 소요 시간 축적

실행마다 조건과 함께 elapsed를 쌓고 `예상치 × 1.5`를 timeout으로 쓴다. 새 유형이면 기록, 예상 대비 ±30% 밖이면 갱신, 범위 안이면 기록하지 않는다. 중단됐어도 마지막 마커까지의 elapsed는 남긴다.

## 7. 반환 — 부분 완성을 버리지 않는다

한도를 넘으면 중단하고 반환한다. 담을 것: 어디까지 됐는지(부분 산출물 경로) / 무엇을 시도해 어떻게 실패했는지(로그·반환값 원문) / 외부 소스 대조 결과 / 다음 후보 / 프로세스 정리 여부.
목표 하나가 막혀도 나머지가 독립이면 거기까지 완성해 저장한다. 하류 에이전트로 넘길 산출물이면 불완전함을 명시한다.

**서브에이전트로 실행 중이면 끝낼 때 `SendMessage`로 호출자에게 보낸다.** 평문으로만 끝내면 전달되지 않는다. 특히 첫 spawn이 아닌 후속 메시지 작업은 자동 반환 경로가 없다.

## 에이전트별 채움 — 같은 골격, 다른 값

| 에이전트 | 되읽기 대상 | 판정 채널 | 외부 정답 소스 |
|---|---|---|---|
| `origin-plot` | 데이터 행/열·축 범위·범례 위치·페이지/레이어/폴더 수 / 스타일·컬러맵 | 생성 스크립트 안 sentinel 되읽기(`tools/origin_verify.py`) / export png 픽셀 비교 | 설치 폴더 `*.ogs` |
| `lumerical` | 시뮬 설정(mesh·PML·source) / 실행 결과(로그·R/T) | `tools/check_setup.py` 되읽기 / `tools/assess_run.py` | Lumerical KB 공식 예제 |
| `speos` | sim 조건 — Compute 전에 | .NET reflection 속성 dump | KB·forum, `.NET` XML 문서 |
| `inventor` | 피처별 체적·면 수·bbox / 뷰·치수 개수, `ModelValue` | `tools/step_check.py` `[STEP]` 줄 / COM 실측(단위는 CHM 확인) | 로컬 CHM |
| `spaceclaim` | 피처별 체적·면·정점·바디 수, bbox | `tools/sc_geomcheck.py` `[STEP]`·`[GEOM VERDICT]` 줄 | introspection → KB |
| `research-compute` | 결과 경계·요청 대 실사용 설정·수렴 / cross-check | `tools/checks.py` 판정 줄 / 해석해 극한, 독립 라이브러리 | 레퍼런스 수렴 절차, 논문 벤치마크 |
| `doc-scan` | 쪽마다 `page_found`·`corner_at_photo_edge`, 결과 이미지 | `tools/scan.py` 마지막 줄 JSON `status` / 결과 이미지 직접 확인 | `references/scan.md` 의 근거 |
| `plot-digitizer` | 캘리브 눈금 재투영·추출 곡선 | `tools/check_calibration.py`·`check_extraction.py` 끝줄 / overlay png | 논문 본문·SI 수치 |
| `pptx-figure` | 도형 개수·이름, 3D 렌더 꼭짓점 | `references/snippets/pptx_frame.py` self-test·`solve_3d` / 렌더(png) 원본 대조 | 원본 그림 |

Ansys KB가 403이면 인증이 아니라 User-Agent 차단이다 — 우회 방법은 각 도메인의 `*_kb_resources.md`.

## 8. 산출물을 만든 코드는 남긴다

판별 기준 하나: **이 산출물을 다시 만들거나 결론을 재검증하려면 필요한가.**

| 보존 (산출물 옆에) | 삭제 |
|---|---|
| 산출물을 만든 스크립트 — 모델·도면·그래프·계산 | 스텝 검증 png, 중간 덤프 |
| 정책·reference·memory를 갱신한 probe | 일회성 로그, 임시 변환 파일 |
