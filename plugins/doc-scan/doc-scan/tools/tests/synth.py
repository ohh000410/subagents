"""합성 문서 사진 — 책상 위 종이(정면), 대각 조명 기울기, 손 그림자, 잡음. 쪽 종류: text·blank·stamp.

사진 안 종이 위치를 알므로 결과(펴진 쪽)에서 쪽 비율 좌표로 영역을 잰다. PATCH = (x0, x1, y0, y1) 쪽 비율.
"""
import cv2
import numpy as np

PAGE_W, PAGE_H = 620, 877                     # A4 비율
PAD_X, PAD_Y = 70, 90                         # 사진 안 종이 위치
PAPER = (232, 238, 242)                       # BGR
DESK = (40, 70, 110)
INK = 35
FAINT = 170                                   # 옅은 1 px 선
SHADOW = (0.70, 0.68, 0.22, 0.15, 0.55)       # 중심 x, y, 반지름 x, y (쪽 비율), 밝기 배율
PATCH = {
    "paper_bright": (0.08, 0.40, 0.50, 0.58),  # 글자·그림자 밖
    "paper_shadow": (0.62, 0.78, 0.60, 0.64),  # 그림자 안, 글자 밖
    "text": (0.08, 0.92, 0.08, 0.40),          # 글자 줄 영역
}


def _page(kind):
    p = np.empty((PAGE_H, PAGE_W, 3), np.uint8)
    p[:] = PAPER
    rng = np.random.default_rng(1)
    if kind == "text":
        for y0, y1, x0, x1 in ((0.08, 0.40, 0.08, 0.92), (0.68, 0.78, 0.55, 0.88)):   # 두 번째 = 그림자 속 글자
            for y in np.arange(y0 * PAGE_H, y1 * PAGE_H, 0.03 * PAGE_H).astype(int):
                x = int(x0 * PAGE_W)
                while x < x1 * PAGE_W:
                    w = int(rng.integers(12, 40))
                    p[y:y + 4, x:min(x + w, int(x1 * PAGE_W))] = INK
                    x += w + int(rng.integers(6, 12))
        p[int(0.45 * PAGE_H), int(0.1 * PAGE_W):int(0.9 * PAGE_W)] = FAINT
    elif kind == "stamp":
        cv2.circle(p, (int(0.7 * PAGE_W), int(0.25 * PAGE_H)), 60, (40, 40, 200), 6)
    return p


def photo(kind, noise=2.0):
    """kind = text | blank | stamp. 반환 BGR uint8 사진."""
    h, w = PAGE_H + 2 * PAD_Y, PAGE_W + 2 * PAD_X
    img = np.empty((h, w, 3), np.float32)
    img[:] = DESK
    img[PAD_Y:PAD_Y + PAGE_H, PAD_X:PAD_X + PAGE_W] = _page(kind)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img *= (1.0 - 0.25 * (xx / w + yy / h) / 2)[..., None]                # 대각 조명 기울기 1.0 -> 0.75
    cx, cy, rx, ry, k = SHADOW
    mask = np.zeros((h, w), np.float32)
    cv2.ellipse(mask, (int(PAD_X + cx * PAGE_W), int(PAD_Y + cy * PAGE_H)), (int(rx * PAGE_W), int(ry * PAGE_H)),
                0, 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), 15)
    img *= (1.0 - (1.0 - k) * mask)[..., None]                           # 손 그림자
    img += np.random.default_rng(2).normal(0, noise, img.shape)
    return np.clip(img, 0, 255).astype(np.uint8)


def patch(page_img, name):
    x0, x1, y0, y1 = PATCH[name]
    h, w = page_img.shape[:2]
    return page_img[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
