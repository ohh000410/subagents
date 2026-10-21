# 종료노브 — 상세 근거

요약 `fdtd_principles_convergence.md`. 절차 `fdtd_convergence_protocol.md`.

## 모든 source 는 유한 펄스
단일파장(start=stop)도 유한 bandwidth 펄스 + DFT 추출. 종료노브는 "펄스 에너지가 죽는가"로 갈림(source type 아님):
- BFAST: 좌표변환으로 정입사화 → 펄스 한 번에 통과
- 흡수체 Bloch: 흡수로 죽음
- 무손실 Bloch(air·고반사): 짧은 pulse 는 broadband, Bloch 가 kx 를 ω₀ 고정 → 저주파 성분 evanescent(허수 ky) → near-field 잔류 → 에너지 floor·정재파 → autoshutoff 무력 + 높이Δ 진동. 긴 pulse(좁은 대역, `set time domain`+pulselength↑) → evanescent 제거 → 에너지 0 → autoshutoff 작동 + 높이Δ=0. 대역(pulse 길이) 문제

wrap: Bloch 주기경계 한쪽 나간 파가 반대쪽 재진입. grazing 은 횡방향 진행 커 wrap 반복하며 PML 로 천천히 빠짐. 무손실이면 CW 처럼 보일 수 있음.

## 판정 = 높이Δ = 모니터 높이별 R 편차 (공간, 시간 아님)
R 모니터 여러 y-높이 → R 편차. 노브 부족 = transient 미완 = 정재파 = 높이마다 R 출렁. 단일 지점은 우연 진동에 속음 → 노브 sweep 해 Δ 단조 감소 확인.

## 무손실 정재파 — 측정 함정 2개
입사파 + PML 불완전 흡수 반사파 → 정재파:
- 점 모니터 에너지 판단 금지: time monitor 몇 점 `|E|²` 합은 마디/배가 측정점 스쳐 출렁 → 가짜 반등·floor. 총 에너지는 area monitor 공간적분(단조 감소)
- transmission() DFT 오염: 짧은 pulse ring-down 정재파 위상이 DFT 에 포함 → sim time·shutoff·PML sweep 해도 R 진동. 긴 pulse 로 정상상태화

BFAST late-time 발산 → `fdtd_detail_bfast.md`.
