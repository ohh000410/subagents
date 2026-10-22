"""origin_verify 판정 시험 (Origin 불필요, 가짜 COM 객체). 실행: tools 폴더에서 python -m unittest discover -s tests -p "test_*.py"

가짜 app 은 `_num` 이 보내는 "... __v=<sentinel>; __v=<식>;" 에서 식의 값을 돌려준다. 값표에 없는 식 = 속성 없음(sentinel 유지).
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import origin_verify as ov  # noqa: E402


class _Count:
    def __init__(self, items):
        self.items = items
        self.Count = len(items)

    def __call__(self, i):
        return self.items[i]


class _Page:
    def __init__(self, name, n_layers):
        self.Name = name
        self.Layers = _Count([None] * n_layers)


class _Scope:
    def __init__(self, app, prefix):
        self.app, self.prefix = app, prefix

    def Execute(self, cmd):
        return self.app._run(cmd, self.prefix)


class FakeApp:
    def __init__(self, values=None, graphs=()):
        self.values = values or {}          # "<scope><식>" -> 값
        self.vars = {}
        self.GraphPages = _Count([_Page(n, k) for n, k in graphs])
        self.PageBases = _Count([_Page(n, k) for n, k in graphs])
        self.exited = False
        self.IsModified = True

    def _run(self, cmd, prefix):
        sets = [s.strip()[4:] for s in cmd.split(";") if s.strip().startswith("__v=")]
        self.vars["__v"] = float(sets[0])
        key = prefix + sets[-1]
        if key in self.values:
            self.vars["__v"] = self.values[key]
        return True

    def Execute(self, cmd):
        return self._run(cmd, "")

    def LTVar(self, name):
        return self.vars[name]

    def FindGraphLayer(self, name):
        return _Scope(self, name)

    def Exit(self):
        self.exited = True


def axis_values(lay, **over):
    v = {}
    for a in ("x", "y"):
        v.update({"%slayer.%s.from" % (lay, a): 0.0, "%slayer.%s.to" % (lay, a): 10.0,
                  "%slayer.%s.inc" % (lay, a): 2.0, "%slayer.%s.type" % (lay, a): 1.0})
    v.update({"%slayer.x.ticks" % lay: 1.0, "%slayer.y.ticks" % lay: 1.0,
              "%slayer.x2.ticks" % lay: 0.0, "%slayer.y2.ticks" % lay: 0.0})
    v.update({lay + k: x for k, x in over.items()})
    return v


class Same(unittest.TestCase):
    def test_small_values_are_compared_relatively(self):  # 2026-10-22 교차 검토: 1e-9 미만이 전부 0 과 같았다
        self.assertFalse(ov._same(1e-12, 0.0))
        self.assertFalse(ov._same(1e-10, 5e-10))
        self.assertTrue(ov._same(1e-10, 1e-10 * (1 + 1e-12)))
        self.assertTrue(ov._same(0.0, 0.0))
        self.assertTrue(ov._same(4.02, 4.02))

    def test_missing_never_matches(self):
        self.assertFalse(ov._same(0.0, ov.NANUM))
        self.assertFalse(ov._same(0.0, math.nan))
        self.assertFalse(ov._same(0.0, None))


class Verify(unittest.TestCase):
    def test_nanum_cell_fails(self):  # 빈 셀이 결측값(NANUM)으로 읽혀 want 0 과 같았다
        app = FakeApp({"__c[2]": ov.NANUM})
        with self.assertRaises(ov.VerifyError):
            ov.verify(app, {"books": {"Book1": {"cells": {(2, 1): 0.0}}}, "ticks": False})
        self.assertTrue(app.exited)

    def test_nothing_checked_fails(self):  # 빈 프로젝트 + ticks False 가 PASS 였다
        app = FakeApp()
        with self.assertRaises(ov.VerifyError) as cm:
            ov.verify(app, {"ticks": False})
        self.assertEqual(cm.exception.report["checks"][0]["check"], "intended")

    def test_pass(self):
        lay = "[Graph1]1!"
        app = FakeApp(axis_values(lay), graphs=[("Graph1", 1)])
        rep = ov.verify(app, {"pages": ["Graph1"], "axes": {lay: {"x": (0, 10)}}})
        self.assertEqual(rep["verdict"], "PASS")
        self.assertFalse(app.exited)

    def test_nan_axis_type_fails(self):  # type nan 이 "선형 아님 -> 세지 않음" PASS 였다
        lay = "[Graph1]1!"
        for k in ("layer.x.type", "layer.x.inc"):
            app = FakeApp(axis_values(lay, **{k: math.nan}), graphs=[("Graph1", 1)])
            with self.assertRaises(ov.VerifyError, msg=k):
                ov.verify(app, {"pages": ["Graph1"]})
            self.assertTrue(app.exited, k)

    def test_nan_axis_from_fails_and_exits(self):  # from nan 이 major_ticks 에서 ValueError -> Exit 없이 Origin 잔존
        lay = "[Graph1]1!"
        for bad in (math.nan, ov.NANUM):
            app = FakeApp(axis_values(lay, **{"layer.x.from": bad}), graphs=[("Graph1", 1)])
            with self.assertRaises(ov.VerifyError):
                ov.verify(app, {"pages": ["Graph1"]})
            self.assertTrue(app.exited)


if __name__ == "__main__":
    unittest.main()
