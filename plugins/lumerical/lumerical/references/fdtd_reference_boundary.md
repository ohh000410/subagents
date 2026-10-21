# FDTD reference 경계

reference = 원리, 공식 문서 근거, 안정적 API 패턴, 검증 절차.

포함: 수렴성 원리·절차 / mesh·PML·source·monitor·BC 설정 근거 / lumapi 안정 패턴 / 공식 문서·KB·논문·검토된 근거 / 재사용 체크리스트·실패 방지 규칙.
제외: 특정 geometry·material·wavelength·angle 실측값 / elapsed·mesh sweep 결과·recipe 통과 조건 / 최근 API 오류·임시 workaround·unresolved / 프로젝트별 결과표·검증 좌표·raw output.

경계:
- reference 는 agent-memory 내용에 의존하지 않는다. "agent-memory MEMORY.md 에서 검색" 류 라우팅 포인터만 허용. 특정 memory 파일의 수치·결론 인용 금지
- agent-memory 는 reference 를 근거로 삼을 수 있다
- 실측값·환경 의존 관찰은 reference 밖
- reference 는 에이전트가 생성·수정·삭제하지 않는다
