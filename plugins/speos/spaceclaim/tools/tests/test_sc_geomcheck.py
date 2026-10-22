"""CPython unit tests for sc_geomcheck judging logic (no SpaceClaim needed).

py -V:Astral/CPython3.12.13 -m unittest discover -s <tools>/tests -v
"""
import os
import sys
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS)
import sc_geomcheck as gc  # noqa: E402
import sc_orchestrate as so  # noqa: E402

BLOCK = (12000.0, 6, 8, 1)          # 40x30x10 block
HOLE_DV = -502.6548245743669        # pi*4^2*10
HOLED = (12000.0 + HOLE_DV, 7, 10, 1)


class Judge(unittest.TestCase):
    def test_pass(self):
        s, d = gc.judge(BLOCK, HOLED, exp_dV=HOLE_DV, exp_dF=1, exp_bodies=1)
        self.assertEqual(s, "PASS", d)

    def test_fail_wrong_dV(self):
        s, d = gc.judge(BLOCK, HOLED, exp_dV=HOLE_DV * 1.01, exp_dF=1, exp_bodies=1)
        self.assertEqual(s, "FAIL")
        self.assertIn("dV err", d)

    def test_tol_boundary(self):
        after = (HOLED[0] + 5e-8,) + HOLED[1:]
        self.assertEqual(gc.judge(BLOCK, after, exp_dV=HOLE_DV)[0], "PASS")
        after = (HOLED[0] + 5e-7,) + HOLED[1:]
        self.assertEqual(gc.judge(BLOCK, after, exp_dV=HOLE_DV)[0], "FAIL")

    def test_nan_volume_fails(self):  # NaN compares False either way (review 2026-10-22)
        after = (float("nan"),) + HOLED[1:]
        self.assertEqual(gc.judge(BLOCK, after, exp_dV=HOLE_DV)[0], "FAIL")

    def test_fail_faces_and_bodies(self):
        s, d = gc.judge(BLOCK, HOLED, exp_dV=HOLE_DV, exp_dF=2, exp_bodies=2)
        self.assertEqual(s, "FAIL")
        self.assertIn("dF", d)
        self.assertIn("bodies", d)

    def test_merge_detected_by_body_count(self):
        # touching solid merged: volume is the exact sum, only body count reveals it
        before = (100.0, 6, 8, 1)
        after = (150.0, 10, 16, 1)
        s, _ = gc.judge(before, after, exp_dV=50.0, exp_bodies=2)
        self.assertEqual(s, "FAIL")

    def test_warn_no_expectation(self):
        s, d = gc.judge(BLOCK, HOLED)
        self.assertEqual(s, "WARN")
        self.assertIn("no expectation", d)

    def test_warn_noop_without_exp_dV(self):
        s, d = gc.judge(BLOCK, BLOCK, exp_dF=0)
        self.assertEqual(s, "WARN")
        self.assertIn("no-op", d)

    def test_explicit_zero_dV_is_pass(self):
        self.assertEqual(gc.judge(BLOCK, BLOCK, exp_dV=0.0, exp_dF=0)[0], "PASS")

    def test_warn_imprint_vertices_only(self):
        after = (BLOCK[0], BLOCK[1], BLOCK[2] + 20, 1)
        s, d = gc.judge(BLOCK, after, exp_dV=0.0, exp_dF=0, exp_bodies=1)
        self.assertEqual(s, "WARN")
        self.assertIn("imprint", d)

    def test_fail_beats_warn(self):
        after = (BLOCK[0], BLOCK[1], BLOCK[2] + 20, 1)
        self.assertEqual(gc.judge(BLOCK, after, exp_dV=1.0)[0], "FAIL")

    def test_first_body_from_empty(self):
        self.assertEqual(gc.judge(gc.EMPTY, BLOCK, exp_dV=12000.0, exp_dF=6, exp_bodies=1)[0], "PASS")


class Session(unittest.TestCase):
    def setUp(self):
        self.lines = []
        gc.init(self.lines.append)

    def test_verdict_pass_and_save_target(self):
        gc.step_check("block", gc.EMPTY, BLOCK, exp_dV=12000.0, exp_dF=6, exp_bodies=1)
        gc.step_check("hole", BLOCK, HOLED, exp_dV=HOLE_DV, exp_dF=1, exp_bodies=1)
        saved = []
        v, target = gc.finish("C:/x/model.scdocx", saved.append)
        self.assertEqual((v, target, saved), ("PASS", "C:/x/model.scdocx", ["C:/x/model.scdocx"]))
        self.assertTrue(self.lines[-1].startswith("[GEOM VERDICT] PASS steps=2 warn=0 fail=0"))
        self.assertTrue(self.lines[0].startswith("[STEP PASS] block:"))

    def test_verdict_fail_saves_fail_name(self):
        gc.step_check("hole", BLOCK, HOLED, exp_dV=-1.0)
        gc.step_check("note", BLOCK, HOLED)
        v, target = gc.finish("C:/x/model.scdocx", lambda p: None)
        self.assertEqual((v, target), ("FAIL", "C:/x/model_FAIL.scdocx"))
        self.assertEqual(self.lines[-1], "[GEOM VERDICT] FAIL steps=2 warn=1 fail=1")
        self.assertEqual(self.lines[-2], "[SAVED] C:/x/model_FAIL.scdocx")

    def test_warn_only_is_pass(self):
        gc.step_check("note", BLOCK, HOLED)
        self.assertEqual(gc.verdict(), "PASS")

    def test_zero_steps_is_fail(self):
        self.assertEqual(gc.verdict_line(), "[GEOM VERDICT] FAIL steps=0 warn=0 fail=0")

    def test_logger_utf8_timestamp(self):
        fd, p = tempfile.mkstemp(suffix=".log")
        os.close(fd)
        try:
            log = gc.make_logger(p)
            log(u"[STEP PASS] \uad6c\uba4d: ok")
            with open(p, encoding="utf-8") as f:
                line = f.read()
            self.assertRegex(line, r"^\d\d:\d\d:\d\d \[STEP PASS\] \uad6c\uba4d: ok\n$")
        finally:
            os.remove(p)

    def test_fail_path_rules_match(self):
        from pathlib import Path
        self.assertEqual(gc.fail_path("C:/a.b/model.scdocx"), "C:/a.b/model_FAIL.scdocx")
        self.assertEqual(gc.fail_path("C:\\x\\m.v2.scdocx"), "C:\\x\\m.v2_FAIL.scdocx")
        self.assertEqual(so.fail_path(Path("C:/a.b/model.scdocx")).name, "model_FAIL.scdocx")


class IronPythonCompat(unittest.TestCase):
    def test_source_ascii(self):
        with open(os.path.join(TOOLS, "sc_geomcheck.py"), "rb") as f:
            f.read().decode("ascii")

    def test_ironpython_compiles(self):
        self.assertEqual(so.compile_check(os.path.join(TOOLS, "sc_geomcheck.py")), "COMPILE OK")


if __name__ == "__main__":
    unittest.main()
