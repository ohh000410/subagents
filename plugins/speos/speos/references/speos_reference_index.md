# SPEOS reference 목차

작업에 필요한 파일만 읽는다.

- 기본 workflow, namespace/import, DocumentOpen, config encoding: [speos_sim_core.md](speos_sim_core.md)
- Material, SourceSurface, OrientedFace: [speos_sim_optics.md](speos_sim_optics.md)
- Irradiance sensor, 적분 방향: [speos_sim_sensor_irradiance.md](speos_sim_sensor_irradiance.md)
- Intensity sensor, report 패턴, Lambertian: [speos_sim_sensor_intensity.md](speos_sim_sensor_intensity.md)
- SimulationDirect, LocalMeshing, Student triangle 한도: [speos_sim_compute_mesh.md](speos_sim_compute_mesh.md)
- XMP 템플릿, 여러 sensor 파싱: [speos_sim_xmp_template.md](speos_sim_xmp_template.md)
- Sweep loop: [speos_sim_sweep.md](speos_sim_sweep.md)
- SPEOS geometry 버튼·ParabolicSurface: [speos_addin_parabolic.md](speos_addin_parabolic.md)
- SplitBody, DesignEdge, body geometry 도우미: [speos_addin_body_geometry.md](speos_addin_body_geometry.md)
- plug-in launch mode, orchestrator(좌석 대기·자기 PID 종료): [speos_launch_modes.md](speos_launch_modes.md), 도구 `../tools/README.md`
- IronPython/process 함정: [speos_pitfalls_ironpython.md](speos_pitfalls_ironpython.md)
- SIM API/workflow 함정: [speos_pitfalls_sim_api.md](speos_pitfalls_sim_api.md), [speos_pitfalls_sim_workflow.md](speos_pitfalls_sim_workflow.md)
- KB·포럼, 매크로 녹화: [speos_kb_resources.md](speos_kb_resources.md), [speos_record_workflow.md](speos_record_workflow.md)

일반 실행 = `speos_sim_core.md` + 객체 파일 + launch/pitfall. Sweep → `speos_sim_sweep.md`, XMP 파싱 → `speos_sim_xmp_template.md`. 새 실측 오류·workaround 는 agent-memory. references 읽기 전용.
