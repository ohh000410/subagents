"""scan.py 시험 (합성 사진, 앱·실사진 불필요). 실행: tools 폴더에서 .venv/Scripts/python.exe -m unittest discover -s tests

기준값은 2026-10-22 normalize 제거 전후 비교에서 정했다(references/scan.md 「조명 보정 시험」).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

import cv2
import numpy as np

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(TOOLS, "tests"))
import scan  # noqa: E402
import synth  # noqa: E402


def scanned(kind, mode):
    img = synth.photo(kind)
    pts = scan.find_page(img)
    return scan.render(scan.warp(img, pts) if pts is not None else img, mode), pts is not None


class Flatten(unittest.TestCase):
    """최솟값~최댓값 늘리기가 빈 쪽을 검게 만들던 결함(2026-10-22 외부 검토)."""

    def test_uniform_white_stays_white(self):
        white = np.full((300, 200, 3), 255, np.uint8)
        for mode in ("color", "gray"):
            self.assertEqual(int(scan.render(white, mode).min()), 255, mode)

    def test_one_dark_pixel_not_stretched(self):
        g = np.full((300, 200), 255, np.uint8)
        g[0, 0] = 250
        self.assertEqual(int(scan.flatten(g).min()), 250)


class SyntheticPages(unittest.TestCase):
    def test_text_page_shadow_removed(self):
        g, found = scanned("text", "gray")
        self.assertTrue(found)
        bright, shadow = (float(np.median(synth.patch(g, n))) for n in ("paper_bright", "paper_shadow"))
        self.assertGreaterEqual(min(bright, shadow), 240)
        self.assertLessEqual(abs(bright - shadow), 8)
        self.assertLessEqual(float(np.percentile(synth.patch(g, "text"), 5)), 60)   # 글자는 진하게 남는다

    def test_blank_page_paper_stays_clean(self):
        for kind in ("blank", "stamp"):
            bw, found = scanned(kind, "bw")
            self.assertTrue(found)
            black = np.mean([(synth.patch(bw, n) == 0).mean() for n in ("paper_bright", "paper_shadow")])
            self.assertLess(black, 0.0005, kind)

    def test_color_paper_stays_neutral(self):
        c, _ = scanned("blank", "color")
        med = [float(np.median(synth.patch(c, "paper_bright")[..., i])) for i in range(3)]
        self.assertLessEqual(max(med) - min(med), 2)


class Outputs(unittest.TestCase):
    def test_name_collision_is_error(self):  # 2026-10-22 외부 검토: a/page.jpg·b/page.jpg → 결과 1개, status ok
        with tempfile.TemporaryDirectory() as td:
            paths = []
            for sub in ("a", "b"):
                os.mkdir(os.path.join(td, sub))
                paths.append(os.path.join(td, sub, "page.jpg"))
                cv2.imwrite(paths[-1], synth.photo("blank"))
            out = os.path.join(td, "out")
            r = subprocess.run([sys.executable, os.path.join(TOOLS, "scan.py"), *paths, "--out", out],
                               capture_output=True, encoding="utf-8")
            res = json.loads(r.stdout.strip().splitlines()[-1])
            self.assertEqual((res["status"], len(res["collisions"])), ("error", 1))
            self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
