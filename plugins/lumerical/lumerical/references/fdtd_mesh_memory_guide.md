# FDTD 메모리 리포트 읽기

리포트 항목: Approximate total memory (Initialization and mesh / Running simulation / Data collection / Monitor data saved to fsp file), Total FDTD Yee nodes, Simulation bandwidth, Current materials RMS error, Memory details(fields·index, monitor 별).

증가 원인: mesh cell 수, monitor 면적·수, frequency points, field component 저장량, mesh override 범위, material fit·index storage.

줄이기: frequency points↓, monitor 영역·수↓, override 범위↓, symmetry·2D·periodic/Bloch, 불필요 field profile monitor 제거. run 전 리포트로 병목 구분:
- `Running simulation` 큼 → mesh cell 수·domain size·material storage
- `Data collection` 큼 → monitor 면적·수·frequency points
- `Monitor data saved to fsp file` 큼 → 저장 monitor·field component
- `Current materials RMS error` = fit 정확도 하한, 결과 오차 해석 시 별도 확인
