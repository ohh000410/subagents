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

    # ---- 2026-10-22 교차 검토 ----

    def run_scan(self, *args):
        r = subprocess.run([sys.executable, "-B", os.path.join(TOOLS, "scan.py"), *args],
                           capture_output=True, encoding="utf-8")
        return json.loads(r.stdout.strip().splitlines()[-1])

    def photo(self, path):
        ok, buf = cv2.imencode(os.path.splitext(path)[1], synth.photo("blank"))
        with open(path, "wb") as f:
            f.write(buf.tobytes())
        with open(path, "rb") as f:
            return f.read()

    def test_output_over_input_is_error(self):  # page.png 의 결과 page_gray.png 가 입력 page_gray.png 를 덮었다
        with tempfile.TemporaryDirectory() as td:
            a, b = os.path.join(td, "page.png"), os.path.join(td, "page_gray.png")
            self.photo(a)
            before = self.photo(b)
            res = self.run_scan(a, b, "--out", td, "--mode", "gray")
            self.assertEqual((res["status"], res["overwrite"]), ("error", [b]))
            with open(b, "rb") as f:
                self.assertEqual(f.read(), before)

    def test_rerun_into_photo_folder_is_error(self):  # 지난 결과가 다음 실행의 입력에 섞였다
        with tempfile.TemporaryDirectory() as td:
            self.photo(os.path.join(td, "receipt.jpg"))
            self.assertEqual(self.run_scan(td, "--out", td)["status"], "ok")
            res = self.run_scan(td, "--out", td)
            self.assertEqual(res["status"], "error")
            self.assertIn(os.path.join(td, "receipt_color.jpg"), res["overwrite"])

    def test_empty_mode_is_error(self):  # 아무것도 안 만들고 ok 였다
        with tempfile.TemporaryDirectory() as td:
            a = os.path.join(td, "a.png")
            self.photo(a)
            for mode in ("", ",", " , "):
                res = self.run_scan(a, "--out", os.path.join(td, "out"), "--mode", mode)
                self.assertEqual((res["status"], res["reason"]), ("error", "mode 이름"), repr(mode))
            self.assertFalse(os.path.exists(os.path.join(td, "out")))

    def test_repeated_mode_runs_once(self):  # color,color 면 PDF 에 같은 쪽이 두 번 들어갔다
        with tempfile.TemporaryDirectory() as td:
            a = os.path.join(td, "a.png")
            self.photo(a)
            res = self.run_scan(a, "--out", os.path.join(td, "out"), "--mode", "color,color")
            self.assertEqual((res["status"], list(res["pages"][0]["outputs"])), ("ok", ["color"]))

    def test_non_photo_file_is_error_before_writing(self):  # a 의 결과를 쓴 뒤 notes.txt 에서 예외로 죽었다
        with tempfile.TemporaryDirectory() as td:
            a, t = os.path.join(td, "a.png"), os.path.join(td, "notes.txt")
            self.photo(a)
            with open(t, "w", encoding="utf-8") as f:
                f.write("not a photo")
            out = os.path.join(td, "out")
            res = self.run_scan(a, t, "--out", out)
            self.assertEqual((res["status"], res["not_photo"]), ("error", [t]))
            self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
