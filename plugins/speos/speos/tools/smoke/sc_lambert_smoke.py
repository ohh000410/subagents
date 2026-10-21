# IronPython 2.7 -- SPEOS smoke: 10x10 mm Lambertian 1 W source at z=50 -> 200x200 mm irradiance sensor at z=0.
# Paths from env: SPEOS_LOG (utf-8 log), SPEOS_OUT (.scdocx), SPEOS_NBRAYS (default 200000), SC_TOOLS (set by sc_orchestrate.run).
# Last line = "[GEOM VERDICT] ..." (the line sc_orchestrate polls for); [FATAL] on exception.
import codecs, os, sys
import System

sys.path.insert(0, os.environ["SC_TOOLS"])
import sc_geomcheck as gc

LOG = os.environ["SPEOS_LOG"]
OUT = os.environ["SPEOS_OUT"]
NB = int(os.environ.get("SPEOS_NBRAYS", "200000"))
log = gc.make_logger(LOG)
N = [0, 0]   # steps, fail


def step(label, got, want, tol):
    ok = abs(float(got) - float(want)) <= tol
    N[0] += 1
    if not ok:
        N[1] += 1
    log(u"[STEP %s] %s: got=%s want=%s" % ("PASS" if ok else "FAIL", label, got, want))


def step_true(label, cond, detail):
    N[0] += 1
    if not cond:
        N[1] += 1
    log(u"[STEP %s] %s: %s" % ("PASS" if cond else "FAIL", label, detail))


def verdict():
    log(u"[GEOM VERDICT] %s steps=%d warn=0 fail=%d" % ("PASS" if N[0] > 0 and N[1] == 0 else "FAIL", N[0], N[1]))


def main():
    asm = None
    for a in System.AppDomain.CurrentDomain.GetAssemblies():
        if a.GetName().Name == "App.Automation.SIM":
            asm = a
            break
    if asm is None:
        raise RuntimeError("App.Automation.SIM not loaded")

    def T(n):
        return asm.GetType("App.Automation.SIM." + n)

    def create(t):
        return t.GetMethod("Create", System.Type.EmptyTypes).Invoke(None, None)

    # source plane 10x10 at z=50
    pl = Plane.Create(Frame.Create(Point.Create(MM(0), MM(0), MM(50.0)), Direction.DirX, Direction.DirY))
    ViewHelper.SetSketchPlane(pl, None)
    pts = [(-5, -5), (5, -5), (5, 5), (-5, 5)]
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        SketchLine.Create(Point2D.Create(MM(a[0]), MM(a[1])), Point2D.Create(MM(b[0]), MM(b[1])))
    ViewHelper.SetViewMode(InteractionMode.Solid, None)
    body = list(GetRootPart().GetBodies())[-1]
    bb = body.GetTessellationBoundingBox(Matrix.Identity, True)
    step("source_x_mm", (bb.MaxCorner.X - bb.MinCorner.X) * 1000, 10.0, 1e-3)
    step("source_y_mm", (bb.MaxCorner.Y - bb.MinCorner.Y) * 1000, 10.0, 1e-3)
    step("source_z_mm", bb.MinCorner.Z * 1000, 50.0, 1e-3)
    face = list(body.Faces)[0]
    step("source_normal_z", face.Shape.Geometry.Frame.DirZ.Z, 1.0, 1e-6)

    mat = create(T("Material"))
    mat.Name = "Source_Plane_Polished"
    mat.SOPTypeIndex = 1   # OpticalPolished: rays pass
    mat.VolumeGeometries.Set(Selection.Create([body]).Items)
    mat.Compute()

    src = create(T("SourceSurface"))
    src.Name = "Lambert_Source"
    src.EmissiveFaces.Set(Selection.Create([face]).Items)
    for c in src.EmissiveFaces:
        c.ReverseDirection = True   # normal +z -> emit -z toward the sensor
    src.FluxTypeIndex = 1
    src.FluxValueRadiant = 1.0
    src.IntensityTotalAngle = 180.0   # Lambertian
    src.Compute()
    step("flux_W", src.FluxValueRadiant, 1.0, 1e-9)
    step("intensity_total_angle", src.IntensityTotalAngle, 180.0, 1e-9)

    sens = create(T("SensorIrradiance"))
    sens.Name = "Plane_Sensor"
    sens.SensorTypeIndex = 1   # Radiometric
    sens.XStart = -100.0
    sens.XEnd = 100.0
    sens.YStart = -100.0
    sens.YEnd = 100.0
    sens.XNbSamples = 100
    sens.YNbSamples = 100
    sens.Compute()
    step("sensor_x_span", sens.XEnd - sens.XStart, 200.0, 1e-9)
    step("sensor_y_span", sens.YEnd - sens.YStart, 200.0, 1e-9)

    sim = create(T("SimulationDirect"))
    sim.Name = "Lambert_Direct"
    sim.NbRays = System.Int64(NB)
    sim.Geometries.Set(Selection.Create([body]).Items)
    sim.Sources.Set(Selection.Create([src.Subject]).Items)
    sim.Sensors.Set(Selection.Create([sens.Subject]).Items)
    step("sim.NbRays", int(sim.NbRays), NB, 0)
    step("sim.Sources.Count", sim.Sources.Count, 1, 0)
    step("sim.Sensors.Count", sim.Sensors.Count, 1, 0)
    if N[1] > 0:
        raise RuntimeError("readback mismatch, not computing")

    d = os.path.dirname(OUT)
    if not os.path.isdir(d):
        os.makedirs(d)
    DocumentSave.Execute(OUT)
    sim.Compute()
    step_true("sim.StatusInfo empty", str(sim.StatusInfo) == "", repr(str(sim.StatusInfo)))
    step_true("sim.IsUpToDate", bool(sim.IsUpToDate), str(sim.IsUpToDate))
    DocumentSave.Execute(OUT)
    verdict()


try:
    main()
except:
    import traceback
    for l in traceback.format_exception(*sys.exc_info()):
        log(u"%s" % l)
    log(u"[FATAL] unhandled exception")
