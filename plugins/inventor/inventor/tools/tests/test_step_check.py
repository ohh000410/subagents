"""step_check 단독 시험 (Inventor 불필요). 실행: tools 폴더에서 python -m unittest discover -s tests"""
import math, os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from step_check import step_check, step_summary  # noqa: E402

BOX = (0, 0, 0, 2, 2, 0.5)           # 20x20x5 mm 블록 (cm)
BOX_FLIPPED = (0, 0, -0.5, 2, 2, 0)  # base extrude 방향 반전
HOLE = -math.pi * 0.2 ** 2 * 0.5     # phi4 관통, 두께 5 mm (cm3)


def chk(*a, **k):
    return step_check(*a, echo=False, **k)


class StepCheck(unittest.TestCase):
    def test_noop_fails(self):  # kNegative 무동작 (references/inventor_ipt_modeling.md 「HoleFeature」)
        r = chk("hole", (1.9, 14), (1.9, 14), exp_dV_cm3=HOLE)
        self.assertEqual(r.status, "FAIL"); self.assertIn("no-op", r.line)

    def test_noop_fails_without_theory(self):
        self.assertEqual(chk("hole", (1.9, 14), (1.9, 14)).status, "FAIL")

    def test_theory_mismatch_fails(self):
        r = chk("hole", (2.0, 6), (2.0 + HOLE * 0.5, 7), exp_dV_cm3=HOLE)
        self.assertEqual(r.status, "FAIL"); self.assertIn("dV mismatch", r.line)

    def test_no_theory_warns(self):
        self.assertEqual(chk("fillet", (2.0, 6), (1.99, 12)).status, "WARN")

    def test_pass(self):
        r = chk("hole", (2.0, 6), (2.0 + HOLE, 7), exp_dV_cm3=HOLE)
        self.assertEqual(r.status, "PASS")
        self.assertTrue(r.line.startswith("[STEP PASS] hole dV=-0.062832 dF=+1 exp=-0.062832"))

    def test_curved_tolerance(self):  # 곡면 단계 7e-5 mm3 (=7e-8 cm3) 오차는 통과
        self.assertEqual(chk("arch", (2.0, 6), (2.0 - 2.598 + 7e-5 / 1000, 9), exp_dV_cm3=-2.598).status, "PASS")

    def test_bbox_ok(self):
        self.assertEqual(chk("base", (0, 0), (2.0, 6, BOX), exp_dV_cm3=2.0, exp_bbox=BOX).status, "PASS")

    def test_bbox_flipped_fails(self):  # 체적은 같아서 체적만으론 못 잡는 경우
        r = chk("base", (0, 0), (2.0, 6, BOX_FLIPPED), exp_dV_cm3=2.0, exp_bbox=BOX)
        self.assertEqual(r.status, "FAIL"); self.assertIn("bbox mismatch", r.line)

    def test_nan_volume_fails(self):  # NaN 은 비교가 모두 거짓 — 통과로 새면 안 된다(2026-10-22 외부 검토)
        self.assertEqual(chk("hole", (2.0, 6), (math.nan, 7), exp_dV_cm3=HOLE).status, "FAIL")

    def test_nan_bbox_fails(self):
        self.assertEqual(chk("base", (0, 0), (2.0, 6, (math.nan,) * 6), exp_dV_cm3=2.0, exp_bbox=BOX).status, "FAIL")

    def test_partial_nan_bbox_fails(self):  # 좌표 하나만 NaN 이어도 — 첫 좌표가 아니면 max() 가 건너뛰었다(2026-10-22 교차 검토)
        for i in range(6):
            bb = list(BOX); bb[i] = math.nan
            self.assertEqual(chk("base", (0, 0), (2.0, 6, tuple(bb)), exp_dV_cm3=2.0, exp_bbox=BOX).status, "FAIL", i)
            self.assertEqual(chk("base", (0, 0), (2.0, 6, BOX), exp_dV_cm3=2.0, exp_bbox=tuple(bb)).status, "FAIL", i)

    def test_short_bbox_raises(self):  # zip() 이 앞 3개만 비교해 통과했다
        with self.assertRaises(ValueError):
            chk("base", (0, 0), (2.0, 6, BOX[:3]), exp_dV_cm3=2.0, exp_bbox=BOX)

    def test_nan_volume_without_theory_fails(self):  # 기대 dV 가 없으면 WARN 으로 새어 "FAIL 0" 완료 기준을 통과했다
        for bad in (math.nan, math.inf):
            self.assertEqual(chk("fillet", (2.0, 6), (bad, 10)).status, "FAIL")
            self.assertEqual(chk("fillet", (bad, 6), (2.0, 10)).status, "FAIL")

    def test_bbox_without_after_bbox_raises(self):
        with self.assertRaises(ValueError):
            chk("base", (0, 0), (2.0, 6), exp_dV_cm3=2.0, exp_bbox=BOX)

    def test_summary(self):
        rs = [chk("a", (1, 1), (1, 1)), chk("b", (1, 1), (2, 2)), chk("c", (1, 1), (2, 2), exp_dV_cm3=1.0)]
        self.assertEqual(step_summary(rs), "STEP 요약: FAIL 1 / WARN 1 / PASS 1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
