# API·운영 함정

## Monitor 결과 추출 실패
`Done. Elapsed...` 정상 완료인데 `getresult` 시 `Can not find result 'T'` = monitor 저장량 RAM 초과 → fsp 부분 손실. 회피 순서: frequency points↓(선형) → monitor 영역↓ → mesh_accuracy/dx 완화 → monitor 수↓(6면 박스 → 단일면+대칭).

## 기타
- Conformal mesh(CMT) 자동 → 메모리 리포트 약간 부정확
- 두꺼운 도메인(H>100µm) FP 공진 스펙트럼 → 스무딩. 10nm 이하 입자 → override mesh
- TFSF cross-section 정규화 = TFSF 면적(monitor 면적 아님) → `fdtd_cross_section_setup.md`
