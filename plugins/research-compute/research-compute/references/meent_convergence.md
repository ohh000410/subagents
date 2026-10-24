# meent_convergence — meent 수렴 프로토콜 (research-compute)

meent(1D linear truncation)는 **값 튐/발산형 near-singular가 거의 없어** 곡선이 단조·완만 → **2D path 한 번에 포화 시작점 집으면 끝**. (단 정확 Rayleigh 각도의 **메모리 폭주형** 실패는 별개로 존재 — 아래 ★ near-singular 격리.) **meent 수렴/calibration = 이 파일 + [[meent_api]](함수·부호규약).** 단순 스윕만이면 [[meent_api]]만. 공통 결론은 [[rcwa_reference_index]].

## TL;DR
```
0. (새 형상만) 유효 유전율(truncated eps) 플롯으로 형상 확인 — solve 없이 첫 단계 [아래 ★]
0.5 (경사 금속 박막만) staircase 연속성 선체크: dz < t/sinα (= N_z ≥ SHEAR/(t/cosα)) — 미달이면 계산 무효 → [[rcwa_metal]]
1. API 설정 ([[meent_api]]: n=n_r−ik · phi=None · ucell=n)
2. worst-case 각도서 2D path → 포화 시작점 (fto*, N_z*)
3. 편광별 따로
4. 전각도에 그 세팅 그대로 + Rayleigh는 격리 실행(아래 ★ near-singular 격리)
★ 새 형상 첫 calibration만 fto sweep 훑어 near-singular/발산 확인
```
grcwa식 BLAS gate · 능선 찾기 · 세트 median은 불필요.

## 2D path 수렴성 테스트
**경량 시작점**(작은 fto, N_z=20)에서 **P + 각 축 ×1.5 한 2점 = 3점**을 평가. 각 축의 변화 s가 target tol보다 크면 그 축 이동 — **두 축 독립 판정**(둘 다·하나만·없음 모두 가능). 곡선이 단조라 s가 방향을 정확히 지시 → **path가 fto·N_z 수렴점을 알아서 찾음**(하한 계산·능선 찾기 불필요).

## 이동 규칙 (각 축 독립, s 비례)
```
probe(민감도) :  s_fto = eps(fto×1.5, N_z) − eps(P)      # ×1.5로 기울기 측정 (×2는 과함)
                 s_Nz  = eps(fto, N_z×1.5) − eps(P)
이동(s 비례)  :  |s_i| > tol → 축_i × 1.5^n,  n = round(log_1.5(|s_i| / tol))
                 (s 크면 여러 배, 수렴 근처 n→0 자동 정지)
                 |s_i| ≤ tol → 그 축 고정
```
- **target tol = 0.001** (사전 지정 = "eps 이 정밀도면 충분"). ★ 노이즈바닥(구조 실제 한계, 사후 측정)과 **다름** — tol은 목표치.

## 종료·최종값
```
종료(각 축):  |s_i| ≤ tol (연속 2회 유지 — 진동 중 일시 dip로 조기 고정 방지)
              OR  포화: |s_i| 최소값이 최근 3스텝 갱신 없음
              OR  발산 상한
종료 = 두 축 다 고정된 시점
```
- ★ **s는 단조 감소 아님**(진동 가능). 노이즈바닥>tol이면 tol에 영영 안 닿으므로 **tol만으로 종료를 설계하지 말 것 — 포화(최소 갱신 멈춤)가 무한 반복 방지 백스톱.** target tol을 노이즈바닥보다 작게 잡아도 포화에서 멈춤. 포화 시 진동폭이 곧 사후 노이즈바닥.
- ★ **최종값 = 포화 시작점의 eps.** 진동폭(~0.0003) < tol(0.001)이라 시작점이 진동 어느 위상이든 오차가 tol 이내 → **path에서 이미 계산된 그 점 그대로**(세트 평균 불필요, 추가 sim 0 = 비용 최소). 단 **세트 생략 = per-angle σ(θ) 지표 포기** — 불확실 각도 선별(스팟체크 대상 고르기)이 필요한 production은 3점 세트+σ 유지를 선택.

- 위 종료 규칙은 `../tools/checks.py` `convergence_line` 이 판정 줄로 출력 (tol→PASS, saturated→WARN, cap→FAIL).

## 편광·Rayleigh
**편광별 2D path 각각** — 한 path가 fto·N_z 두 축을 함께 수렴시키니, TE/TM 따로 돌리면 각자 `(fto*, N_z*)`가 나옴(편광마다 다를 수 있음). Rayleigh 각도는 아래 '★ near-singular 격리'로. 경사 금속 박막 선체크·반사측 TM 한계는 TL;DR 0.5·[[rcwa_metal]].

## 발산·병렬
- **발산**: 하드발산 R>1.5 또는 nan → 그 점 폐기(발산은 거의 없음). 인접 정상이면 isolated, 옆도 발산이면 축 상한.
- **병렬**: Pool 표준(워커 수·BLAS=1·메모리 가드)은 [[rcwa_reference_index]] 공통 2. meent 고유: **`maxtasksperchild=1` 필수**(leak — ★ 격리 섹션), path만 iteration 내부 병렬, 캐싱 `{(fto,N_z,pol):eps}`.

## ★ 새 형상 첫 calibration (geometry 함수 도입 시 한 번)
1. **형상 확인 = 유효 유전율(Fourier-truncated eps)로 플롯** ★수렴테스트 1단계: geometry 함수의 ucell을 **fto_half 차수로 Fourier truncation한 eps(x,z) 맵**(Re/Im)을 그려 **호출자에게 확인**받음. ★ 입력 ucell staircase가 아니라 **meent가 실제 계산에 쓰는 유효 유전율**을 봐야 함 — 좌표·tip·mirror·overhang·주기 wrap(%L) 버그 + truncation 상태(Gibbs ringing 과다 여부 = fto 적절성 초기 신호)를 계산 전 한 번에 차단. **solve·field 불필요(순수 FFT, 수 초)** 라 첫 단계로 가벼움. 재구성: `eps_row = n_row² → FFT/Nx → 0..fto_x 및 −fto_x..−1 차수만 유지 → IFFT×RES_X` (meent dfs2d 역, fourier_type=0). ★ **ucell에서만** — 별도 기하식 재계산 금지(실제 계산에 들어가는 ucell 배열이 유일 소스). air buffer는 형상 확인엔 불필요(field 정재파 볼 때만). 참조 구현 `snippets/truncated_eps_only.py`. ★ geometry 함수 도입 시 **한 번만** — 파라미터 스윕/최적화 iteration은 같은 함수라 재확인 불필요. **예외: N_z(슬라이스 수) 변경은 유효 기하 자체를 바꿈**(점샘플 staircase — 경사 박막이면 연속성부터 재확인; [[rcwa_metal]]).
2. **fto sweep**: near-singular/발산 없나 훑어 확인(near-singular robust는 형상·각도 의존, 완전 배제 단정 금지). 발산 안전장치는 유지.

## ★ near-singular(Rayleigh) 격리 실행 (2026-07-10)
정확한 Rayleigh 각도(격자식 → [[rcwa_reference_index]] 공통 3)에서 meent는 grcwa처럼 nan을 내지 **않지만** — 메모리 폭주형 실패가 있음:
- **폭주 = solve 누적(leak) ∧ near-singular 대형 할당의 합작**: 한 프로세스 for-loop로 돌리다 near-singular 각도에 닿으면 메모리 폭주 → 시스템 RAM commit-limit(`0xc000012d`) → **전체 시스템 먹통**(VRAM 아님). meent/torch가 solve 간 메모리를 완전히 안 풀어 **누적이 필요조건**(실측: 같은 각도가 in-loop 먹통 vs 격리는 정상 완료). 정상 각도 누적 단독 폭주는 미검증.
- 격리 실행 규칙(독립 프로세스 + Job Object RAM 상한 + RAM 칸막이 + 참조 구현)과 값 신뢰 검증은 **[[rcwa_reference_index]] 공통 3**. meent 고유 근거: offset과 ~0.001 차이, grcwa식 BLAS-spread 없음. 스레드는 메모리 공유라 격리 무효 — 반드시 프로세스.
- 여러 solve 격리 배치는 **CPU 권장**(연속 GPU worker는 VRAM 미반환 → OOM; [[meent_api]]).

## 검증
교차검증 게이트 통과.
