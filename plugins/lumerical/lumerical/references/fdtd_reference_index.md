# Lumerical FDTD reference 목차

작업에 필요한 파일만 읽음.

- RCWA·STACK → [lumerical_rcwa.md](lumerical_rcwa.md) (solver 다름)
- 버전 **v242**(2024 R2.3)

2계층: Tier-1 `fdtd_principles_*`(기본 read) → 필요 시 그 안의 `fdtd_detail_*` 포인터.

## Execution
- [fdtd_lumapi_patterns_basic.md](fdtd_lumapi_patterns_basic.md) — lumapi 실행, 결과 추출, xlsx
- [fdtd_lumapi_patterns_advanced.md](fdtd_lumapi_patterns_advanced.md) — 필요 시

## 수렴·사전 검증
- 원리: [fdtd_principles_convergence.md](fdtd_principles_convergence.md)
- 절차: [fdtd_convergence_protocol.md](fdtd_convergence_protocol.md)

## Source (BFAST / Bloch), 2D 편광 라벨
- [fdtd_principles_source.md](fdtd_principles_source.md)

## R/T 추출 (부호·배치, grating vs net-flux)
- [fdtd_principles_extraction.md](fdtd_principles_extraction.md)

## 형상·source 설정
- structure group 회전: [fdtd_structure_group_rotation.md](fdtd_structure_group_rotation.md)
- TFSF 단일 입자 cross-section: [fdtd_cross_section_setup.md](fdtd_cross_section_setup.md)

## Troubleshooting / External
- API·운영 함정: [fdtd_pitfalls_api.md](fdtd_pitfalls_api.md)
- 실패 대응·fallback·공식 예제: [fdtd_agent_runbook.md](fdtd_agent_runbook.md)
- KB: [fdtd_kb_resources.md](fdtd_kb_resources.md)

## detail (Tier-1 이 포인팅, 직접 라우팅 안 함)
`fdtd_detail_termination` / `fdtd_detail_mesh_grazing` / `fdtd_detail_pml` / `fdtd_detail_bfast` / `fdtd_detail_rt_signs` / `fdtd_detail_rt_grating`

## Explicit Only (주제 명시 시만)
- [fdtd_resource_config.md](fdtd_resource_config.md) — Resources 병렬 구성·process grid
- [fdtd_gpu_support.md](fdtd_gpu_support.md) — GPU/CPU 한계
- [fdtd_material_fit_general.md](fdtd_material_fit_general.md) — 재질 fit·RMS
- [fdtd_mesh_memory_guide.md](fdtd_mesh_memory_guide.md) — memory report
- [fdtd_reference_boundary.md](fdtd_reference_boundary.md) — reference 경계 정책
