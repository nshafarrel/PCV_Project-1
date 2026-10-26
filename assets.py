import os
import numpy as np
import cv2
import config as C
from render import nn_scale, nn_resize

# helpers
def _load(name, unchanged=True):
    flag = cv2.IMREAD_UNCHANGED if unchanged else cv2.IMREAD_COLOR
    path = os.path.join(C.ASSET_DIR, name)
    img = cv2.imread(path, flag)
    if img is None:
        raise FileNotFoundError(f"Asset not found: {path}")
    return img


def _flood_fill_alpha(img, threshold=230):
    h, w = img.shape[:2]
    bgr = img[:, :, :3] if img.ndim == 3 else np.stack([img]*3, axis=-1)

    near_white = np.all(bgr >= threshold, axis=2)

    seed = np.zeros((h, w), dtype=bool)
    for cy, cx in [(0, 0), (0, w-1), (h-1, 0), (h-1, w-1)]:
        if near_white[cy, cx]:
            seed[cy, cx] = True

    max_iters = h + w
    for _ in range(max_iters):
        grown = seed.copy()
        grown[1:, :]  |= seed[:-1, :]
        grown[:-1, :] |= seed[1:, :]
        grown[:, 1:]  |= seed[:, :-1]
        grown[:, :-1] |= seed[:, 1:]
        grown &= near_white
        if np.array_equal(grown, seed):
            break       
        seed = grown

    alpha = np.where(seed, np.uint8(0), np.uint8(255))
    return alpha


def _extract_alpha(img, threshold=230):
    if img.ndim == 3 and img.shape[2] == 4:
        bgr   = img[:, :, :3].copy()
        alpha = img[:, :, 3].copy()
    else:
        bgr   = img[:, :, :3].copy() if img.ndim == 3 else np.stack([img]*3, axis=-1)
        alpha = _flood_fill_alpha(img, threshold)
    return bgr, alpha


def _detect_block_size(img):
    row = img[0, :, :3] if img.ndim == 3 else img[0, :]
    runs = []
    i = 0
    w = row.shape[0]
    while i < w:
        j = i + 1
        while j < w and np.array_equal(row[j], row[i]):
            j += 1
        runs.append(j - i)
        i = j
    # GCD of all run lengths
    from math import gcd
    block = runs[0]
    for r in runs[1:]:
        block = gcd(block, r)
    return max(1, block)



# Public: load all assets
class Assets:
    def __init__(self):
        self.bg = None  
        self.ball_bgr = None
        self.ball_alpha = None
        self.paddle_bgr = None
        self.paddle_alpha = None
        self.buttons = {}
        self.cursor_bgr = None
        self.cursor_alpha = None

    def load(self):
        # Background
        bg_raw = _load("background_menu.png", unchanged=False)
        self.bg = nn_resize(bg_raw, C.WIN_H, C.WIN_W)

        # Ball
        ball_raw = _load("asset_ball2.png")
        ball_scaled = nn_resize(ball_raw, C.BALL_DRAW_SIZE, C.BALL_DRAW_SIZE)
        bgr, alpha = _extract_alpha(ball_scaled)
        self.ball_bgr = bgr
        self.ball_alpha = alpha

        # Paddle
        paddle_raw = _load("asset_pong.png")
        paddle_resized = nn_resize(paddle_raw, C.PADDLE_H, C.PADDLE_W)
        bgr_p, alpha_p = _extract_alpha(paddle_resized)
        self.paddle_bgr = bgr_p
        self.paddle_alpha = alpha_p

        # Buttons
        btn_files = {
            "start":    "button_start.png",
            "help":     "button_help.png",
            "exit":     "button_exit.png",
            "close":    "button_close.png",
            "continue": "button_continue.png",
            "pause":    "icon_pause.png",
        }
        for name, fname in btn_files.items():
            raw = _load(fname)
            rh, rw = raw.shape[:2]
            if name == "pause":
                target_h = 48
            else:
                target_h = 60
            ratio = target_h / rh
            new_w = int(rw * ratio)
            new_h = target_h
            resized = nn_resize(raw, new_h, new_w)
            bgr_b, alpha_b = _extract_alpha(resized)
            self.buttons[name] = (bgr_b, alpha_b, new_w, new_h)

        # Cursor
        from render import make_cursor
        self.cursor_bgr, self.cursor_alpha = make_cursor(C.CURSOR_SIZE)
