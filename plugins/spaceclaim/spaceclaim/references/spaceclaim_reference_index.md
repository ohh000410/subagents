# SpaceClaim reference 목차

작업에 필요한 파일만 읽는다.

- Launch mode, orchestrator polling, headless: [spaceclaim_launch_modes.md](spaceclaim_launch_modes.md) — 공용 함수·피처별 기하 판정은 [../tools/README.md](../tools/README.md)
- IronPython 2.7 문법, encoding, process cleanup: [spaceclaim_pitfalls_ironpython.md](spaceclaim_pitfalls_ironpython.md)
- geometry API 함정, RevolveEdges, SplitBody, Move, bbox, DesignEdge: [spaceclaim_pitfalls_geometry_api.md](spaceclaim_pitfalls_geometry_api.md)
- 스케치 평면·primitive·revolve: [spaceclaim_sketch_revolve.md](spaceclaim_sketch_revolve.md)
- NurbsCurve, CurveSegment, DesignCurve: [spaceclaim_nurbs.md](spaceclaim_nurbs.md)
- SPEOS geometry 버튼·ParabolicSurface: [spaceclaim_speos_addin_parabolic.md](spaceclaim_speos_addin_parabolic.md)
- SPEOS body geometry 도우미, SplitBody/DesignEdge/DocumentSave/Open: [spaceclaim_speos_addin_body_geometry.md](spaceclaim_speos_addin_body_geometry.md)
- .NET reflection·property 덤프: [spaceclaim_introspection.md](spaceclaim_introspection.md)
- KB·포럼, GUI 매크로 녹화: [spaceclaim_kb_resources.md](spaceclaim_kb_resources.md), [spaceclaim_record_workflow.md](spaceclaim_record_workflow.md)

일반 실행 = `spaceclaim_launch_modes.md` + `spaceclaim_pitfalls_ironpython.md` + 작업 유형별 API 파일. 모르는 API → introspection → KB/forum → macro recording. 새 API 함정·검증된 pattern 은 agent-memory. references 읽기 전용.
