# Inventor 도면 API reference 목차

Inventor 2027 Drawing COM API. 작업에 필요한 파일만 읽는다.

- 공통 도면 생성, Inventor 연결, 상수, DrawingDocument, A3 좌표계, PDF/IDW 저장: [inventor_drawing_core.md](inventor_drawing_core.md)
- IPT 직접 생성, revolve/extrude/hole/mass property: [inventor_ipt_modeling.md](inventor_ipt_modeling.md)
- 회전체 도면, SIDE/END VIEW 치수, 중심마크/중심선, 참조치수: [inventor_rotational_drawing.md](inventor_rotational_drawing.md)
- IAM/STEP 비회전체 3-view, IAM orientation, 다중 원/홀, A3 3-view 레이아웃: [inventor_iam_3view_layout.md](inventor_iam_3view_layout.md)
- pink dimension, GeometryIntent, GetDrawingCurves, 도면 규격, 레이블, 충돌 검사, ISO 배치 함정: [inventor_dimension_pitfalls.md](inventor_dimension_pitfalls.md)

일반 실행 = `inventor_drawing_core.md` + 작업 유형별 1개 + 필요 시 `inventor_dimension_pitfalls.md`.
