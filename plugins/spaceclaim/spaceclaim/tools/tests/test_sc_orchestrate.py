"""CPython unit tests for sc_orchestrate log parsing (no SpaceClaim needed)."""
import importlib
import os
import shutil
import sys
import tempfile
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

    def test_pass_word_alone_is_not_pass(self):  # cross review 2026-10-22
        for text in ("x [GEOM VERDICT] PASS steps=0 warn=0 fail=0\n",
                     "x [STEP PASS] a: ...\nx [GEOM VERDICT] PASS steps=1 warn=0 fail=1\n",
                     "x [STEP FAIL] hole: ...\nx [GEOM VERDICT] PASS steps=1 warn=0 fail=0\n"):
            r = so.parse_log(text)
            self.assertEqual((r["verdict"], r["kind"]), ("FAIL", "verdict"), text)

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


class InstallRoot(unittest.TestCase):
    """Paths come from AWP_ROOT261 (set by the Ansys installer), not a fixed Student path."""

    def test_paths_follow_awp_root(self):
        old = os.environ.get("AWP_ROOT261")
        try:
            os.environ["AWP_ROOT261"] = r"D:\Ansys\v261"
            m = importlib.reload(so)
            self.assertEqual(m.SC_EXE, r"D:\Ansys\v261\scdm\SpaceClaim.exe")
            self.assertIn(r"/AddInManifestFile=D:\Ansys\v261\Optical Products\Speos\bin\SpeosSC.Manifest.xml", m.SPEOS_ARGS)
        finally:
            if old is None:
                os.environ.pop("AWP_ROOT261", None)
            else:
                os.environ["AWP_ROOT261"] = old
            importlib.reload(so)


class RunVerdict(unittest.TestCase):
    """A PASS log alone is not a PASS run: the output file must exist and no own process may be left
    (review 2026-10-22: '[ORCH] PASS ... residual=1 out=no')."""

    def setUp(self):
        self.saved = (so.compile_check, so.sc_count, so.launcher_count, so.close_pid, so.subprocess.Popen)
        self.dir = tempfile.mkdtemp()
        self.log, self.out = os.path.join(self.dir, "run.log"), os.path.join(self.dir, "model.scdocx")
        so.compile_check = lambda script: "COMPILE OK"
        so.sc_count = so.launcher_count = lambda: 0

    def tearDown(self):
        so.compile_check, so.sc_count, so.launcher_count, so.close_pid, so.subprocess.Popen = self.saved
        shutil.rmtree(self.dir)

    def run_with(self, write_out, residual, out_bytes=2048):
        log, out = self.log, self.out

        class Proc:
            pid = 99999

            def __init__(self, *a, **k):
                with open(log, "a", encoding="utf-8") as f:
                    f.write("21:30:07 [GEOM VERDICT] PASS steps=1 warn=0 fail=0\n")
                if write_out:
                    with open(out, "wb") as f:
                        f.write(b"n" * out_bytes)

            def poll(self):
                return 0
        so.subprocess.Popen = Proc
        so.close_pid = lambda pid, wait_s=30: residual
        return so.run(os.path.join(self.dir, "s.py"), log, out, timeout_s=5, poll_s=0.01)

    def write(self, path, data):
        with open(path, "wb") as f:
            f.write(data)

    def test_pass(self):
        res = self.run_with(write_out=True, residual=0)
        self.assertEqual((res["verdict"], res["problems"]), ("PASS", []))
        self.assertIn("out=new", res["summary"])

    def test_no_output_fails(self):
        res = self.run_with(write_out=False, residual=0)
        self.assertEqual((res["verdict"], res["problems"]), ("FAIL", ["no_output"]))
        self.assertIn("problems=no_output", res["summary"])

    def test_tiny_output_fails(self):  # a 10-byte out passed (cross review 2026-10-22)
        res = self.run_with(write_out=True, residual=0, out_bytes=10)
        self.assertEqual((res["verdict"], res["problems"]), ("FAIL", ["no_output"]))

    def test_residual_fails(self):
        res = self.run_with(write_out=True, residual=1)
        self.assertEqual((res["verdict"], res["problems"]), ("FAIL", ["residual"]))

    def test_previous_output_is_kept_and_not_counted(self):  # it was deleted before launch (cross review 2026-10-22)
        self.write(self.out, b"o" * 4096)
        self.write(so.fail_path(so.Path(self.out)), b"f" * 4096)
        self.write(self.log, b"21:00:00 [GEOM VERDICT] PASS steps=3 warn=0 fail=0\n")
        res = self.run_with(write_out=False, residual=0)
        self.assertEqual((res["verdict"], res["problems"]), ("FAIL", ["no_output"]))
        self.assertIn("out=old fail_out=old", res["summary"])
        with open(self.out, "rb") as f:
            self.assertEqual(f.read(), b"o" * 4096)
        with open(self.log, encoding="utf-8") as f:   # the log is this run's only
            self.assertEqual(f.read().count("[GEOM VERDICT]"), 1)

    def test_previous_output_survives_failed_launch(self):
        self.write(self.out, b"o" * 4096)

        def no_exe(*a, **k):
            raise FileNotFoundError("SpaceClaim.exe")
        so.subprocess.Popen = no_exe
        with self.assertRaises(FileNotFoundError):
            so.run(os.path.join(self.dir, "s.py"), self.log, self.out, timeout_s=5, poll_s=0.01)
        self.assertEqual(os.path.getsize(self.out), 4096)

    def test_overwritten_output_counts(self):
        self.write(self.out, b"o" * 4096)
        res = self.run_with(write_out=True, residual=0)
        self.assertEqual((res["verdict"], res["out_new"]), ("PASS", True))


class PowerShell(unittest.TestCase):
    def test_nonzero_exit_raises(self):  # a failed count read as 0 = "no SpaceClaim" (cross review 2026-10-22)
        with self.assertRaises(RuntimeError):
            so._ps("Write-Error 'boom' -ErrorAction Stop")

    def test_compile_check_reports_missing_install(self):
        old = so.SC_DIR
        so.SC_DIR = tempfile.mkdtemp()
        try:
            msg = so.compile_check(os.path.abspath(__file__))
        finally:
            os.rmdir(so.SC_DIR)
            so.SC_DIR = old
        self.assertNotEqual(msg, "COMPILE OK")
        self.assertIn("Microsoft.Scripting.dll", msg)


if __name__ == "__main__":
    unittest.main()
