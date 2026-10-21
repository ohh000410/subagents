# rcwa_metal — 경사 금속 박막 RCWA 한계 (research-compute)

경사 금속면 형상 작업 시 읽어라. 프로토콜은 `<lib>_convergence`, 공통 규칙은 [[rcwa_reference_index]], s1 유전체 수치는 memory `reference_rcwa_wedge_s1_values.md`.

## ★ staircase 필름 연속성 선체크 (계산 전 필수 — 자체완결)
경사 금속 박막을 z-slice **중점 점샘플**로 썰면 `N_z < SHEAR/(t_film/cosα)` (동치: `dz > t_film/sinα`)에서 **필름이 z방향으로 끊김** → 분리된 금속 조각 배열 = **가짜 흡수**(와이어그리드 거동: TE는 y-연속이라 정상, TM은 끊긴 방향 가로질러 누설).
- **미달이면 그 위의 수렴 스윕은 전부 무효**

## 유효 기하에서의 수렴
- **외삽으로 수렴 판정 금지**.

## 실무 규칙
- **금속 raster엔 CFS**(`fourier_type=1`): DFS와 값 동일(Δ≤5e-5), 속도 ~5.7배 빠름.
- meent **Li(1996) factorization은 정식 구현·활성**(소스 감사) — "Li rule 불충분" 서술 폐기.
- 상세: memory `reference_al_coated_rcwa_staircase_step6.md`
