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

    # ---- 2026-10-22 교차 검토 ----

    def write(self, rel, text):
        p = os.path.join(self.dir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    EARLY_LOG = ("Starting 50000 total iterations\nautoshutoff criteria are satisfied\n"
                 "Completed 1000 iterations, or 1.2e-12 s of Simulation Time\n")   # early shutoff at 1200 fs

    def test_rcwa_with_its_fsp_folder_passes(self):  # agents/lumerical.md 4단계 명령 그대로 = 정상 RCWA 가 FAIL 이었다
        t = self.write("rcwa.csv", "case_id,Rs,Ts,Rp,Tp\nc1,0.3,0.6,0.35,0.55\n")
        fsp = self.write("fsp/c1.fsp", "x")
        for args in ([t, os.path.dirname(fsp)], [t, fsp]):
            res = ar.assess(args)
            self.assertEqual((res["solver"], res["verdict"]), ("rcwa", "PASS"), args)
        self.assertEqual(ar.assess([t, os.path.dirname(fsp)], solver="rcwa")["verdict"], "PASS")

    def test_rcwa_table_with_fdtd_logs_is_still_rcwa(self):  # 섞인 폴더면 에너지 위반 RCWA 가 WARN 이었다
        t = self.write("rcwa.csv", "case_id,Rs,Ts,Rp,Tp\nc1,0.8,0.8,0.8,0.8\n")
        self.write("mixed/x_p0.log", self.EARLY_LOG)
        res = ar.assess([t, os.path.join(self.dir, "mixed")])
        self.assertEqual((res["solver"], res["verdict"]), ("rcwa", "FAIL"))
        self.assertEqual(self.verdicts(res, "rt_sum"), ["FAIL", "FAIL"])
        self.assertEqual(self.verdicts(res, "solver"), ["WARN"])   # logs ignored, said so

    def test_folder_argument_links_rows(self):  # 위치 인자 폴더가 행-로그 연결에 안 쓰였다
        t = self.write("task/t.csv", "case_id,R,T,hit_cap\nc1,0.3,0.6,1\n")
        self.write("task/runs/c1_p0.log", self.EARLY_LOG)
        self.assertEqual(self.verdicts(ar.assess([t]), "log_link"), ["WARN"])
        res = ar.assess([t, os.path.join(self.dir, "task", "runs")])
        self.assertEqual(self.verdicts(res, "shutoff_recorded"), ["FAIL"])
        self.assertEqual(res["verdict"], "FAIL")

    def test_same_log_by_two_spellings_is_one_log(self):
        t = self.write("t.csv", "case_id,R,T\nc1,0.3,0.6\n")
        self.write("fsp/c1_p0.log", self.EARLY_LOG)
        res = ar.assess([t, os.path.join(self.dir, "FSP")])   # default fsp/ and the argument FSP/ are one folder
        self.assertEqual(self.verdicts(res, "run_completed"), ["PASS"])
        self.assertEqual(self.verdicts(res, "log_shared"), [])

    def test_unreadable_recorded_shutoff_fails(self):  # NaN·inf·아무 문자열이 검사 항목 없이 통과했다
        self.write("fsp/c1_p0.log", self.EARLY_LOG)
        for col, v in (("shutoff_time_fs", "nan"), ("shutoff_time_fs", "inf"),
                       ("shutoff_time_fs", "invalid_string"), ("hit_cap", "NaN")):
            res = self.table("case_id,R,T,%s\nc1,0.3,0.6,%s\n" % (col, v))
            self.assertEqual(self.verdicts(res, "shutoff_recorded"), ["FAIL"], (col, v))
        for col, v in (("shutoff_time_fs", "1200.5"), ("hit_cap", "0"), ("hit_cap", "False")):
            res = self.table("case_id,R,T,%s\nc1,0.3,0.6,%s\n" % (col, v))
            self.assertEqual(self.verdicts(res, "shutoff_recorded"), ["PASS"], (col, v))

    def test_header_only_table_fails(self):  # 헤더만 쓰고 멈춘 표가 WARN 이었다
        self.assertEqual(self.verdicts(self.table("case_id,R,T\n"), "rows"), ["FAIL"])
        self.assertEqual(self.verdicts(self.table("case_id,Rs,Ts,Rp,Tp\n"), "rows"), ["FAIL"])
        p = self.write("e.json", "[]")
        self.assertEqual(ar.assess([p])["verdict"], "FAIL")   # no columns, no rows: nothing checked

    def test_table_without_rt_columns_is_not_rows_fail(self):  # xlsx 메타 시트 같은 표는 판정 대상 아님
        res = self.table("case_id,note\nc1,meta\n")
        self.assertEqual(self.verdicts(res, "rows"), [])
        self.assertEqual(self.verdicts(res, "rt_columns"), ["WARN"])


if __name__ == "__main__":
    unittest.main()
