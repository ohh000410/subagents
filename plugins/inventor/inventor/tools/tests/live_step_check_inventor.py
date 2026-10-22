"""step_check 실측 (Inventor 필요, 수동 실행): 20x20x5 mm 블록 + phi4 관통 구멍.
기대: 블록 PASS / kPositive 구멍 PASS / kNegative 구멍 FAIL(무동작) / 반전 extrude FAIL(bbox)."""
import math, os, sys, time
import win32com.client as win32
class K:  # 상수 = references/inventor_drawing_core.md 「상수 (실측)」 (gen_py 없이 Dispatch 하면 constants 없음)
    kJoinOperation, kPositiveExtentDirection, kNegativeExtentDirection = 20481, 20993, 20994

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from step_check import step_check, step_summary, read_state  # noqa: E402
from inventor_session import launch, kill_own  # noqa: E402

TPL = r"C:\Users\Public\Documents\Autodesk\Inventor 2027\Templates\en-US\Metric\Standard (mm).ipt"
BOX = (0, 0, 0, 2, 2, 0.5)
HOLE = -math.pi * 0.2 ** 2 * 0.5
t0 = time.time()
results = []


def mark(s):
    print("[t=%.1fs] %s" % (time.time() - t0, s), flush=True)


def new_block(app, ext_dir):
    doc = win32.CastTo(app.Documents.Add(12290, TPL), "PartDocument")  # gen_py 캐시 있으면 Document 로 반환 -> 캐스트 필요
    comp = doc.ComponentDefinition
    tg = app.TransientGeometry
    xy = [comp.WorkPlanes.Item(i) for i in range(1, comp.WorkPlanes.Count + 1)]
    xy = next(w for w in xy if w.Name == "XY Plane")
    sk = comp.Sketches.Add(xy)
    sk.SketchLines.AddAsTwoPointRectangle(tg.CreatePoint2d(0, 0), tg.CreatePoint2d(2, 2))
    ed = comp.Features.ExtrudeFeatures.CreateExtrudeDefinition(sk.Profiles.AddForSolid(), K.kJoinOperation)
    ed.SetDistanceExtent(0.5, ext_dir)
    comp.Features.ExtrudeFeatures.Add(ed)
    return doc, comp


def hole(app, doc, comp, direction):
    top = max((f for i in range(1, comp.SurfaceBodies.Item(1).Faces.Count + 1)
               for f in [comp.SurfaceBodies.Item(1).Faces.Item(i)] if f.SurfaceType == 5890),
              key=lambda f: (f.Evaluator.RangeBox.MinPoint.Z, f.Evaluator.RangeBox.MaxPoint.Z))  # 윗면 = MinZ 도 최대(옆면 제외)
    sk = comp.Sketches.Add(top)
    sp = sk.SketchPoints.Add(app.TransientGeometry.CreatePoint2d(0, 0))
    # 스케치 좌표 -> 모델 좌표가 면 방향에 따라 달라지므로 면 중심 근처 점으로 이동
    c = top.PointOnFace
    sp.MoveTo(sk.ModelToSketchSpace(c))
    sp.HoleCenter = True
    col = app.TransientObjects.CreateObjectCollection(); col.Add(sp)
    pl = comp.Features.HoleFeatures.CreateSketchPlacementDefinition(col)
    comp.Features.HoleFeatures.AddDrilledByThroughAllExtent(pl, 0.4, direction)


app, pid = launch()  # 이미 떠 있으면 거부
docs = []
try:
    mark("block + hole")
    for label, hdir in (("hole kPositive", K.kPositiveExtentDirection), ("hole kNegative", K.kNegativeExtentDirection)):
        doc, comp = new_block(app, K.kPositiveExtentDirection); docs.append(doc)
        s_base = read_state(doc)
        if label.endswith("Positive"):
            results.append(step_check("base extrude (+Z)", (0.0, 0), s_base, exp_dV_cm3=2.0, exp_bbox=BOX))
        hole(app, doc, comp, hdir)
        s_hole = read_state(doc)
        results.append(step_check(label, s_base, s_hole, exp_dV_cm3=HOLE))
    mark("flipped base extrude")
    doc, comp = new_block(app, K.kNegativeExtentDirection); docs.append(doc)
    results.append(step_check("base extrude (-Z flipped)", (0.0, 0), read_state(doc), exp_dV_cm3=2.0, exp_bbox=BOX))
    print(step_summary(results))
finally:
    for d in docs:
        d.Close(True)
    app.Quit()
    kill_own(pid)
    mark("quit")
