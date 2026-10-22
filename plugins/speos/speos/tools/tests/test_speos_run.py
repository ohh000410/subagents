"""speos_run 단독 시험 (SpaceClaim·SPEOS 불필요, sc_orchestrate.run 을 가짜로). 실행: tools 폴더에서 python -m unittest discover -s tests"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import speos_run as sr  # noqa: E402


class RunSpeos(unittest.TestCase):
    def setUp(self):
        self.saved = sr.sco.run

    def tearDown(self):
        sr.sco.run = self.saved

    def test_env_reaches_child_and_is_restored(self):
        seen = {}

        def fake_run(script, log, out, **kw):
            seen.update(kw, SPEOS_LOG=os.environ.get("SPEOS_LOG"), SPEOS_NEW=os.environ.get("SPEOS_NEW"))
            return {"verdict": "PASS"}
        sr.sco.run = fake_run
        os.environ["SPEOS_LOG"] = "old"
        os.environ.pop("SPEOS_NEW", None)
        try:
            res = sr.run_speos("s.py", "s.log", "o.scdocx", timeout_s=5, env={"SPEOS_LOG": "new", "SPEOS_NEW": 1}, seat_wait_s=0)
            self.assertEqual(res["verdict"], "PASS")
            self.assertEqual((seen["SPEOS_LOG"], seen["SPEOS_NEW"], seen["speos"]), ("new", "1", True))
            self.assertEqual(os.environ.get("SPEOS_LOG"), "old")      # 돌려놓는다
            self.assertNotIn("SPEOS_NEW", os.environ)                  # 없던 키는 지운다
        finally:
            os.environ.pop("SPEOS_LOG", None)

    def test_env_is_restored_when_run_raises(self):
        def boom(*a, **k):
            raise FileNotFoundError("SpaceClaim.exe")
        sr.sco.run = boom
        os.environ.pop("SPEOS_X", None)
        with self.assertRaises(FileNotFoundError):
            sr.run_speos("s.py", "s.log", "o.scdocx", env={"SPEOS_X": "1"})
        self.assertNotIn("SPEOS_X", os.environ)


class SensorFlux(unittest.TestCase):
    def test_every_sensor_section(self):
        fd, p = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write("<ul><li>Flux: 0.830692 W</li></ul> ... <ul><li>Flux: 1.2e-3 W</li></ul>")
            self.assertEqual(sr.sensor_flux_w(p), [0.830692, 0.0012])
        finally:
            os.remove(p)


if __name__ == "__main__":
    unittest.main()
