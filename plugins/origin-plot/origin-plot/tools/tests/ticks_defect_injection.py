"""Defect injection for origin_verify ticks check (needs Origin). usage: ticks_defect_injection.py <case>
Exit 0 when the verdict matches EXPECT[case], else 1 (it only printed the verdict and exited 0 before,
and the pages check compared the project with itself -- cross review 2026-10-22)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from origin_verify import open_session, ex, verify, close, VerifyError
EXPECT = {"good": "PASS", "good_min4": "PASS", "min5": "FAIL", "two_ticks": "FAIL", "outward": "FAIL",
          "top_tick": "FAIL", "right_tick": "FAIL", "untouched": "FAIL", "off": "PASS"}
case = sys.argv[1]
STYLE = ["layer.x.showAxes=3", "layer.y.showAxes=3", "layer.x.thickness=3", "layer.y.thickness=3", "layer.x2.thickness=3", "layer.y2.thickness=3",
         "layer.x.ticks=1", "layer.y.ticks=1", "layer.x2.ticks=0", "layer.y2.ticks=0"]
app = open_session()
ex(app, ["newbook name:=\"B1\"", "col(1)[1]=0.3", "col(1)[2]=2.5", "col(2)[1]=0.1", "col(2)[2]=0.9"], "d")
ex(app, ["plotxy iy:=[B1]1!(1,2) plot:=200 ogl:=[<new>]"], "p")
gl = app.FindGraphLayer("[Graph1]1!")
intended = {"layers": {"Graph1": 1}}   # the new graph page from plotxy ogl:=[<new>]; keeps "off" from checking nothing
if case == "good":              # autoscale 0..3 inc 1 (4 ticks), style 5
    ex(app, STYLE, "style", scope=gl)
elif case == "good_min4":       # same graph, caller asks min 4 -> still 4
    ex(app, STYLE, "style", scope=gl); intended["ticks"] = {"[Graph1]1!": {"min": (4, 4)}}
elif case == "min5":            # caller asks 5, graph has 4 -> FAIL
    ex(app, STYLE, "style", scope=gl); intended["ticks"] = {"[Graph1]1!": {"min": 5}}
elif case == "two_ticks":       # benchmark failure: manual from/to, inc stays at autoscale value
    ex(app, STYLE + ["layer.x.from=0.3", "layer.x.to=2.5"], "style", scope=gl)
elif case == "outward":
    ex(app, STYLE + ["layer.x.ticks=2"], "style", scope=gl)
elif case == "top_tick":
    ex(app, STYLE + ["layer.x2.ticks=1"], "style", scope=gl)
elif case == "right_tick":
    ex(app, STYLE + ["layer.y2.ticks=1"], "style", scope=gl)
elif case == "untouched":       # Origin defaults: x/y out, x2/y2 in
    pass
elif case == "off":             # ticks False -> untouched graph passes
    intended["ticks"] = False
try:
    verify(app, intended)
    got = "PASS"
    print("RESULT %s: PASS" % case)
    close(app)
except VerifyError as e:
    got = "FAIL"
    print("RESULT %s: FAIL (%s)" % (case, str(e)[:300]))
ok = got == EXPECT[case]
print("EXPECT %s: %s -> %s" % (case, EXPECT[case], "OK" if ok else "MISMATCH"))
sys.exit(0 if ok else 1)
