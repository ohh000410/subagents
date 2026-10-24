# FDTD reference 경계

reference = 원리, 공식 문서 근거, 안정적 API 패턴, 검증 절차, 다시 확인된 실측 함정.

포함: 수렴성 원리·절차 / mesh·PML·source·monitor·BC 설정 근거 / lumapi 안정 패턴 / 공식 문서·KB·논문·검토된 근거 / 재사용 체크리스트·실패 방지 규칙 / 다른 PC 에서도 맞는 실측 함정과 그 수치(조건·버전을 함께).
제외: 이 PC·프로젝트 고유 값(특정 형상·재질의 결과표, elapsed, 경로, 검증 좌표, raw output) / 미검증·미해결 추론 / 원인이 확정되지 않은 우회책.

경계:
- reference·본문·도구는 메모리 파일을 가리키지 않음. reference 에 있어야 할 내용이면 메모리에서 승격
- 메모리는 reference 를 근거로 삼을 수 있음
- reference 는 에이전트가 생성·수정·삭제하지 않음
