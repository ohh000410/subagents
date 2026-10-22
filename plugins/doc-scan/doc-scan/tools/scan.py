"""문서 사진 → 스캔본. 창을 띄우지 않는다.

  scan.py <사진|폴더> [...] [--out 폴더] [--mode color,bw] [--pdf 이름.pdf] [--no-crop]

  1. 사진을 연다(EXIF 회전 반영, HEIC 포함)
  2. 종이 모서리 4개를 찾아 반듯하게 편다. 못 찾으면 자르지 않고 page_found=false 로 알린다(--no-crop 이면 찾지 않는다)
  3. 그림자·조명 얼룩을 지운다 → mode 별 저장
       color  컬러, 배경을 흰색으로 (JPG)
       gray   회색조 (PNG)
       bw     흑백 스캔 — 글자만 남김 (PNG)
  4. --pdf 면 입력 순서대로 첫 번째 mode 의 결과를 한 PDF 로 묶는다

출력 폴더 기본값: 첫 입력과 같은 폴더의 scanned/. 원본은 건드리지 않는다.
마지막 줄은 JSON: status = ok | error
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()
EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".bmp", ".tif", ".tiff"}
MODES = ("color", "gray", "bw")


def emit(**kw):
    print(json.dumps(kw, ensure_ascii=False), flush=True)


def load(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def angle_range(quad):
    """내각의 최대-최소(도). 종이가 아닌 찌그러진 사각형을 거른다 — andrewdcampbell/OpenCV-Document-Scanner 의 MAX_QUAD_ANGLE_RANGE."""
    q = order(quad)
    angs = []
    for i in range(4):
        a, b, c = q[i - 1], q[i], q[(i + 1) % 4]
        u, v = a - b, c - b
        angs.append(np.degrees(np.arccos(np.clip(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v)), -1, 1))))
    return max(angs) - min(angs)


def find_page(img):
    """가장 큰 볼록 사각형(사진 면적 20% 이상, 내각 차 40° 미만)의 꼭짓점. 글자를 지우려고 먼저 닫힘 연산을 한다.
    후보 두 갈래: ① 경계선(Canny, 문턱은 사진의 중앙 밝기에서 — AVI20953/doc-scan 의 adaptive Canny)
    ② 밝은 덩어리(Otsu) — 그림자 쪽 테두리가 약해 경계선이 끊겨도 종이는 배경보다 밝다(2026-10-08 시험: 기울인 사진에서 ① 실패)."""
    h, w = img.shape[:2]
    s = 1000 / max(h, w)
    small = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)), iterations=3)
    med = float(np.median(gray))
    edges = cv2.dilate(cv2.Canny(gray, int(max(0, 0.67 * med)), int(min(255, 1.33 * med))), np.ones((3, 3), np.uint8))
    _, bright = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bright = cv2.morphologyEx(bright, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
    area = small.shape[0] * small.shape[1]
    best = None
    for mask, mode in ((edges, cv2.RETR_LIST), (bright, cv2.RETR_EXTERNAL)):
        contours, _ = cv2.findContours(mask, mode, cv2.CHAIN_APPROX_SIMPLE)
        for c in sorted(contours, key=cv2.contourArea, reverse=True)[:10]:
            approx = cv2.approxPolyDP(cv2.convexHull(c), 0.02 * cv2.arcLength(c, True), True)
            if len(approx) == 4 and cv2.contourArea(approx) > 0.2 * area \
                    and angle_range(approx.reshape(4, 2).astype("float32")) < 40 \
                    and (best is None or cv2.contourArea(approx) > cv2.contourArea(best)):
                best = approx
    return None if best is None else best.reshape(4, 2).astype("float32") / s


def order(pts):
    """왼위·오위·오아래·왼아래."""
    s, d = pts.sum(1), np.diff(pts, axis=1).ravel()
    return np.array([pts[s.argmin()], pts[d.argmin()], pts[s.argmax()], pts[d.argmax()]], dtype="float32")


def aspect(tl, tr, br, bl, center):
    """종이의 실제 가로/세로 비. 비스듬히 찍으면 먼 변이 짧아 보여 변 길이 비가 틀린다(2026-10-08 시험: A4 0.707 → 0.82)
    → 사각형 꼭짓점으로 초점거리와 비를 함께 구한다(Zhang & He, Whiteboard scanning, 2007). 정면 사진처럼 풀이가
    성립하지 않으면(f² ≤ 0) 원근이 거의 없다는 뜻이라 변 길이 비를 쓴다."""
    m1, m2, m3, m4 = (np.array([p[0] - center[0], p[1] - center[1], 1.0]) for p in (tl, tr, bl, br))
    k2 = np.dot(np.cross(m1, m4), m3) / np.dot(np.cross(m2, m4), m3)
    k3 = np.dot(np.cross(m1, m4), m2) / np.dot(np.cross(m3, m4), m2)
    n2, n3 = k2 * m2 - m1, k3 * m3 - m1
    f2 = -(n2[0] * n3[0] + n2[1] * n3[1]) / (n2[2] * n3[2]) if n2[2] * n3[2] != 0 else -1
    if f2 <= 0:
        return np.hypot(n2[0], n2[1]) / np.hypot(n3[0], n3[1])
    return np.sqrt((n2[0] ** 2 + n2[1] ** 2) / f2 + n2[2] ** 2) / np.sqrt((n3[0] ** 2 + n3[1] ** 2) / f2 + n3[2] ** 2)


def warp(img, pts):
    tl, tr, br, bl = order(pts)
    w = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
    h = int(round(w / aspect(tl, tr, br, bl, (img.shape[1] / 2, img.shape[0] / 2))))
    m = cv2.getPerspectiveTransform(np.array([tl, tr, br, bl]), np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]]))
    return cv2.warpPerspective(img, m, (w, h), flags=cv2.INTER_CUBIC)


def flatten(channel):
    """조명 보정: 글자를 지운 배경(팽창 + 중앙값 흐림)으로 나눠 그림자·얼룩을 없앤다. 나누면 종이가 약 255 가 된다.
    최솟값~최댓값 늘리기는 두지 않는다 — 가장 어두운 한 화소가 배율을 정해 빈 쪽이 검게 되고 잡음이 커졌다
    (2026-10-22 외부 검토 재현, references/scan.md 「조명 보정 시험」)."""
    k = max(15, (min(channel.shape) // 40) | 1)
    bg = cv2.medianBlur(cv2.dilate(channel, np.ones((7, 7), np.uint8)), k)
    return cv2.divide(channel, bg, scale=255)


def render(page, mode):
    if mode == "color":
        return cv2.merge([flatten(c) for c in cv2.split(page)])
    gray = flatten(cv2.cvtColor(page, cv2.COLOR_BGR2GRAY))
    if mode == "gray":
        return gray
    block = max(15, (min(gray.shape) // 30) | 1)
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block, 10)


def save(img, path):
    ok, buf = cv2.imencode(path.suffix, img, [cv2.IMWRITE_JPEG_QUALITY, 92] if path.suffix == ".jpg" else [])
    if not ok:
        raise RuntimeError(f"저장 실패: {path}")
    path.write_bytes(buf.tobytes())        # 한글 경로 — cv2.imwrite 는 Windows 에서 비 ASCII 경로를 못 쓴다


def inputs(args):
    files = []
    for a in args:
        p = Path(a)
        files += sorted(f for f in p.iterdir() if f.suffix.lower() in EXTS) if p.is_dir() else [p]
    return files


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--mode", default="color,bw")
    ap.add_argument("--pdf")
    ap.add_argument("--no-crop", action="store_true")
    a = ap.parse_args()
    modes = [m.strip() for m in a.mode.split(",") if m.strip()]
    bad = [m for m in modes if m not in MODES]
    files = inputs(a.paths)
    missing = [str(f) for f in files if not f.is_file()]
    if bad or not files or missing:
        return emit(status="error", reason="mode 이름" if bad else "입력 없음", bad_modes=bad, missing=missing, allowed=MODES)
    # 출력 이름 = <원본 이름>_<mode> — 이름이 같은 사진(다른 폴더·확장자, 대소문자만 다름)은 앞 결과를 덮어쓴다
    # (2026-10-22 외부 검토: 2장 → 결과 1개, status ok). 아무것도 쓰기 전에 멈춘다
    first, collisions = {}, []
    for f in files:
        k = f.stem.casefold()
        if k in first:
            collisions.append([str(first[k]), str(f)])
        else:
            first[k] = f
    if collisions:
        return emit(status="error", reason="출력 이름 충돌 — 이름이 같은 사진은 --out 을 나눠 따로 실행", collisions=collisions)
    out = Path(a.out) if a.out else files[0].parent / "scanned"
    out.mkdir(parents=True, exist_ok=True)
    results, pdf_pages = [], []
    for f in files:
        img = load(f)
        pts = None if a.no_crop else find_page(img)
        page = warp(img, pts) if pts is not None else img
        saved = {}
        for m in modes:
            r = render(page, m)
            dst = out / f"{f.stem}_{m}{'.jpg' if m == 'color' else '.png'}"
            save(r, dst)
            saved[m] = str(dst)
            if m == modes[0]:
                pdf_pages.append(Image.fromarray(cv2.cvtColor(r, cv2.COLOR_BGR2RGB) if r.ndim == 3 else r))
        # 모서리가 사진 가장자리(1%)에 닿으면 종이 일부가 사진 밖 — 펴진 결과가 잘리거나 비뚤다(2026-10-08 시험)
        edge = pts is not None and bool(((pts < [img.shape[1] * 0.01, img.shape[0] * 0.01]) |
                                         (pts > [img.shape[1] * 0.99, img.shape[0] * 0.99])).any())
        results.append({"input": str(f), "page_found": pts is not None, "corner_at_photo_edge": edge,
                        "corners": None if pts is None else order(pts).round().astype(int).tolist(),
                        "photo_size": [img.shape[1], img.shape[0]], "page_size": [page.shape[1], page.shape[0]],
                        "outputs": saved})
    pdf = None
    if a.pdf:
        pdf = out / a.pdf
        pdf_pages[0].save(pdf, save_all=True, append_images=pdf_pages[1:], resolution=200)
        pdf = str(pdf)
    emit(status="ok", out=str(out), pages=results, pdf=pdf,
         page_not_found=[r["input"] for r in results if not r["page_found"] and not a.no_crop])


if __name__ == "__main__":
    main()
