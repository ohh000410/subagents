"""check_setup 의 launch preset 판정 시험 (Lumerical 불필요, 가짜 세션). 실행: tools 폴더에서 python -m unittest discover -s tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import check_setup as cs  # noqa: E402


class FakeFDTD:
    def __init__(self, preset, processes):
        self.res = {"job launching preset": preset, "processes": float(processes)}

    def getresource(self, solver, i, key):
        return self.res[key]


def preset_items(preset, processes, expected):
    rep = cs._Rep()
    cs._check_preset(FakeFDTD(preset, processes), rep, expected)
    return [(it["verdict"], it["detail"]) for it in rep.items]


class Preset(unittest.TestCase):
    def test_local_computer_fails_against_expected(self):  # 조용한 1 프로세스 실행(fdtd_resource_config.md)
        (v, _), = preset_items("Local Computer", 1, 6)
        self.assertEqual(v, "FAIL")

    def test_mpi_preset_with_one_process_fails(self):  # 프리셋은 되돌렸는데 processes 가 1 로 남은 경우 — 예전에는 WARN
        (v, _), = preset_items("Remote: Microsoft MPI", 1, 6)
        self.assertEqual(v, "FAIL")

    def test_expected_met_passes(self):
        (v, _), = preset_items("Remote: Microsoft MPI", 6, 6)
        self.assertEqual(v, "PASS")
        (v, _), = preset_items("Local Computer", 1, 1)   # 다른 PC: MPI 가 없고 1 프로세스가 기대값
        self.assertEqual(v, "PASS")

    def test_no_expected_value_warns(self):  # 이 PC 값을 받지 못하면 읽은 값만 알린다(작성자 PC 값을 기본값으로 쓰지 않음)
        (v, d), = preset_items("Local Computer", 1, None)
        self.assertEqual(v, "WARN")
        self.assertIn("processes=1", d)


if __name__ == "__main__":
    unittest.main()
