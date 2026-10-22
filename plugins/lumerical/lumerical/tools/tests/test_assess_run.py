"""assess_run 판정 시험 (Lumerical 불필요). 실행: tools 폴더에서 python -m unittest discover -s tests"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import assess_run as ar  # noqa: E402


class Assess(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def table(self, text):
        p = os.path.join(self.dir, "t.csv")
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return ar.assess([p])

    def verdicts(self, res, check):
        return [c["verdict"] for c in res["checks"] if c["check"] == check]

    def test_rcwa_energy_violation_fails(self):  # 2026-10-22 외부 검토: 각각 [0,1] 이라 PASS 였다
        res = self.table("case_id,Rs,Ts,Rp,Tp\nc1,0.8,0.8,0.8,0.8\n")
        self.assertEqual((res["solver"], res["verdict"]), ("rcwa", "FAIL"))
        self.assertEqual(self.verdicts(res, "rt_sum"), ["FAIL", "FAIL"])

    def test_rcwa_lossy_passes(self):
        res = self.table("case_id,Rs,Ts,Rp,Tp\nc1,0.3,0.6,0.35,0.55\n")
        self.assertEqual(res["verdict"], "PASS")

    def test_fdtd_sum_bands(self):  # <= 1e-3 PASS, 1e-3~1e-2 WARN, > 1e-2 FAIL
        res = self.table("case_id,R,T\nc1,0.3,0.7005\nc2,0.3,0.705\nc3,0.3,0.75\n")
        self.assertEqual(self.verdicts(res, "rt_sum"), ["PASS", "WARN", "FAIL"])

    def test_empty_folder_fails(self):  # 2026-10-22 외부 검토: 검사 0개인데 PASS 였다
        empty = os.path.join(self.dir, "empty")
        os.mkdir(empty)
        res = ar.assess([empty])
        self.assertEqual(res["verdict"], "FAIL")
        self.assertEqual(self.verdicts(res, "inputs"), ["FAIL"])


if __name__ == "__main__":
    unittest.main()
