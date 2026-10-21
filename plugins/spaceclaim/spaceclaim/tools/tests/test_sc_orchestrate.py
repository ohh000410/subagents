"""CPython unit tests for sc_orchestrate log parsing (no SpaceClaim needed)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sc_orchestrate as so  # noqa: E402

PASS_LOG = (
    "21:30:01 start\n"
    "21:30:05 [STEP PASS] block: dV=+12000 mm3 (exp +12000) dF=+6 (exp 6) bodies=1 (exp 1) dVerts=+8 V=12000\n"
    "21:30:06 [STEP WARN] note: dV=+0 mm3 (exp -) dF=+0 (exp -) bodies=1 (exp -) dVerts=+0 V=12000 | no expectation\n"
    "21:30:07 [SAVED] C:/x/model.scdocx\n"
    "21:30:07 [GEOM VERDICT] PASS steps=2 warn=1 fail=0\n"
)


class ParseLog(unittest.TestCase):
    def test_pass(self):
        r = so.parse_log(PASS_LOG)
        self.assertEqual((r["verdict"], r["kind"], r["steps"], r["warn"], r["fail"]),
                         ("PASS", "verdict", 2, 1, 0))
        self.assertEqual(len(r["step_lines"]), 2)
        self.assertTrue(r["step_lines"][1].startswith("[STEP WARN] note"))

    def test_fail_verdict(self):
        r = so.parse_log("x [STEP FAIL] hole: ...\nx [GEOM VERDICT] FAIL steps=1 warn=0 fail=1\n")
        self.assertEqual((r["verdict"], r["kind"], r["fail"]), ("FAIL", "verdict", 1))

    def test_no_verdict_line_is_fail(self):
        r = so.parse_log("21:30:01 start\n21:30:05 [STEP PASS] block: ...\n")
        self.assertEqual((r["verdict"], r["kind"]), ("FAIL", "no_verdict"))

    def test_fatal(self):
        r = so.parse_log("21:30:01 start\nTraceback ...\n21:30:02 [FATAL] unhandled exception\n")
        self.assertEqual((r["verdict"], r["kind"]), ("FAIL", "fatal"))

    def test_fatal_after_verdict_wins(self):
        r = so.parse_log(PASS_LOG + "21:30:08 [FATAL] unhandled exception\n")
        self.assertEqual((r["verdict"], r["kind"]), ("FAIL", "fatal"))

    def test_empty_log(self):
        r = so.parse_log("")
        self.assertEqual((r["verdict"], r["kind"]), ("FAIL", "empty_log"))

    def test_marker(self):
        self.assertTrue(so.log_has_marker(PASS_LOG))
        self.assertTrue(so.log_has_marker("x [FATAL] y"))
        self.assertFalse(so.log_has_marker("21:30:05 [STEP PASS] block\n21:30:07 [SAVED] x\n"))

    def test_ascii_safe(self):
        self.assertEqual(so.ascii_safe(u"\uad6c\uba4d ok"), "\\uad6c\\uba4d ok")


class SeatBusy(unittest.TestCase):
    """Seat still taken after the wait -> FAIL seat_busy, SpaceClaim is never launched."""

    def setUp(self):
        self.saved = (so.compile_check, so.sc_count, so.subprocess.Popen)

    def tearDown(self):
        so.compile_check, so.sc_count, so.subprocess.Popen = self.saved

    def test_not_launched(self):
        so.compile_check = lambda script: "COMPILE OK"
        so.sc_count = lambda: 1

        def no_launch(*a, **k):
            raise AssertionError("SpaceClaim must not be launched while the seat is taken")
        so.subprocess.Popen = no_launch
        res = so.run("x.py", "x.log", "x.scdocx", seat_wait_s=0)
        self.assertEqual((res["verdict"], res["kind"]), ("FAIL", "seat_busy"))
        self.assertIn("kind=seat_busy", res["summary"])


if __name__ == "__main__":
    unittest.main()
