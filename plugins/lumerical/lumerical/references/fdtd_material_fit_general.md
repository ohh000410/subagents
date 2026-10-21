# Material Fit (분산 모델)

FDTD 시간 영역 → dispersive material 을 Drude-Lorentz 등으로 fit. fit 정확도 부족 = broadband 오차.

- RMS error 확인: GUI Material Explorer → "Plot fit", 또는 실행 직전 메모리 리포트 "Current materials rms error" (`fdtd_mesh_memory_guide.md`)
- Fit RMS error = 시뮬 정확도 하한. 메쉬·도메인 조정으로 못 내림
- 재질별 fit options(max_coefficients·tolerance·imaginary_weight)·정확도 실측 → agent-memory MEMORY.md 에서 재질명(예 `fit_options_au`) 검색
- fit 회피 = 단일 파장 (n,k) Material → `fdtd_cross_section_setup.md` "단일 파장"
