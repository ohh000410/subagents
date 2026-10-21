# BFAST — 상세 근거

요약 `fdtd_principles_source.md`. 설정 코드 `fdtd_lumapi_patterns_advanced.md` "BFAST 광원".

## 언제
broadband 고정 입사각. 단일 파장 → Bloch (KB: "single wavelength → Bloch boundary conditions"). 고각 정규화 오류·late-time 발산 → 편광별 air-only sanity check.

## 고각 T>1 = sourcepower 정규화 오류 (gain 아님)
air-only 에서 한쪽 편광만 T_builtin>1. raw Poynting 은 두 편광 동일 → `transmission()` 분모 sourcepower 가 그 편광에서 과소.
- 오류 편광 = p-pol(TM). 크기 mesh 의존(거칠수록 큼). injection 방향 무관
- fix: raw Poynting 재정규화, 분모 = 같은 mesh·같은 셋업 air baseline. 슬랩 vs TMM R·T ≤1% 검증

## late-time 수치 발산
펄스 통과 후 에너지 최저 → late-time 지수 발산. 추정 원인 = 좌표변환 update 의 kx 항(E=E'·exp(i·kx·x) → 허수 i·kx 항 → Yee CFL 실수계수 가정 초과). 각도↑(kx↑) 심화 추정. Bloch 는 실수 update, 발산 없음.
- numerical permittivity gain 아님(상수 (n,k) 재료 Im(eps_num)=0). KB "무손실 유전체 gain 발산" 경고는 분산 fitting 재료 한정
- `bfast dt multiplier`(기본 0.5, `dt=CFL×dt_stability_factor×bfast_dt_multiplier`) 낮추면 지연만. 무손실 floor 잔존. 높이Δ floor 가 Bloch 보다 높음 → 펄스 직후 짧은 window 에서 값 추출

## 정확도 천장
좌표변환 오차 timestep 누적(추정) → fine mesh(dt↓, timestep↑) 에서 악화·느려짐(주로 TM, 실측). 고정밀 → Bloch + 접선축 refine. TE 는 거친 격자로도 정확.

## 제약
각도↑ → dt 축소, 느려짐(KB). 비선형 비호환. TIR critical angle 초과 주입 불가. PML 장시간 불안정(layers↑·sigma↓).
