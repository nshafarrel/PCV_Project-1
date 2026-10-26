import numpy as np
import config as C

# Bitmap font – 5×7 pixel characters (A-Z, 0-9, common symbols)
_FONT_RAW = {
    'A': ["01110","10001","10001","11111","10001","10001","10001"],
    'B': ["11110","10001","10001","11110","10001","10001","11110"],
    'C': ["01110","10001","10000","10000","10000","10001","01110"],
    'D': ["11100","10010","10001","10001","10001","10010","11100"],
    'E': ["11111","10000","10000","11110","10000","10000","11111"],
    'F': ["11111","10000","10000","11110","10000","10000","10000"],
    'G': ["01110","10001","10000","10111","10001","10001","01110"],
    'H': ["10001","10001","10001","11111","10001","10001","10001"],
    'I': ["11111","00100","00100","00100","00100","00100","11111"],
    'J': ["00111","00010","00010","00010","00010","10010","01100"],
    'K': ["10001","10010","10100","11000","10100","10010","10001"],
    'L': ["10000","10000","10000","10000","10000","10000","11111"],
    'M': ["10001","11011","10101","10101","10001","10001","10001"],
    'N': ["10001","11001","10101","10011","10001","10001","10001"],
    'O': ["01110","10001","10001","10001","10001","10001","01110"],
    'P': ["11110","10001","10001","11110","10000","10000","10000"],
    'Q': ["01110","10001","10001","10001","10101","10010","01101"],
    'R': ["11110","10001","10001","11110","10100","10010","10001"],
    'S': ["01111","10000","10000","01110","00001","00001","11110"],
    'T': ["11111","00100","00100","00100","00100","00100","00100"],
    'U': ["10001","10001","10001","10001","10001","10001","01110"],
    'V': ["10001","10001","10001","10001","01010","01010","00100"],
    'W': ["10001","10001","10001","10101","10101","10101","01010"],
    'X': ["10001","10001","01010","00100","01010","10001","10001"],
    'Y': ["10001","10001","01010","00100","00100","00100","00100"],
    'Z': ["11111","00001","00010","00100","01000","10000","11111"],
    '0': ["01110","10001","10011","10101","11001","10001","01110"],
    '1': ["00100","01100","00100","00100","00100","00100","11111"],
    '2': ["01110","10001","00001","00110","01000","10000","11111"],
    '3': ["01110","10001","00001","00110","00001","10001","01110"],
    '4': ["00010","00110","01010","10010","11111","00010","00010"],
    '5': ["11111","10000","11110","00001","00001","10001","01110"],
    '6': ["01110","10000","10000","11110","10001","10001","01110"],
    '7': ["11111","00001","00010","00100","01000","01000","01000"],
    '8': ["01110","10001","10001","01110","10001","10001","01110"],
    '9': ["01110","10001","10001","01111","00001","00001","01110"],
    ' ': ["00000","00000","00000","00000","00000","00000","00000"],
    ':': ["00000","00100","00100","00000","00100","00100","00000"],
    '.': ["00000","00000","00000","00000","00000","00000","00100"],
    '-': ["00000","00000","00000","11111","00000","00000","00000"],
    '!': ["00100","00100","00100","00100","00100","00000","00100"],
    ',': ["00000","00000","00000","00000","00000","00100","01000"],
    '(': ["00010","00100","01000","01000","01000","00100","00010"],
    ')': ["01000","00100","00010","00010","00010","00100","01000"],
    '+': ["00000","00100","00100","11111","00100","00100","00000"],
    '/': ["00001","00010","00010","00100","01000","01000","10000"],
}

# Pre-build numpy arrays for each glyph once.
FONT_GLYPHS = {}
for _ch, _rows in _FONT_RAW.items():
    _arr = np.zeros((C.FONT_CHAR_H, C.FONT_CHAR_W), dtype=np.uint8)
    for _r, _row_str in enumerate(_rows):
        for _c_idx, _bit in enumerate(_row_str):
            if _bit == '1':
                _arr[_r, _c_idx] = 1
    FONT_GLYPHS[_ch] = _arr



def nn_scale(img, factor):
    if factor == 1:
        return img.copy()
    # np.repeat along each spatial axis
    out = np.repeat(np.repeat(img, factor, axis=0), factor, axis=1)
    return out


def nn_resize(img, new_h, new_w):
    h, w = img.shape[:2]
    row_idx = (np.arange(new_h) * h // new_h).astype(int)
    col_idx = (np.arange(new_w) * w // new_w).astype(int)
    return img[np.ix_(row_idx, col_idx)]


# Alpha blitting
def blit_alpha(canvas, sprite, alpha, x, y):
    sh, sw = sprite.shape[:2]
    ch, cw = canvas.shape[:2]

    # source region clipping
    sx0 = max(0, -x)
    sy0 = max(0, -y)
    sx1 = min(sw, cw - x)
    sy1 = min(sh, ch - y)
    if sx0 >= sx1 or sy0 >= sy1:
        return  # entirely off-screen

    # destination region
    dx0 = x + sx0
    dy0 = y + sy0
    dx1 = x + sx1
    dy1 = y + sy1

    a = alpha[sy0:sy1, sx0:sx1].astype(np.float32) / 255.0
    a3 = a[:, :, np.newaxis]  # broadcast over BGR channels

    dst = canvas[dy0:dy1, dx0:dx1].astype(np.float32)
    src = sprite[sy0:sy1, sx0:sx1].astype(np.float32)

    canvas[dy0:dy1, dx0:dx1] = (src * a3 + dst * (1.0 - a3)).astype(np.uint8)


def blit_opaque(canvas, sprite, x, y):
    sh, sw = sprite.shape[:2]
    ch, cw = canvas.shape[:2]
    sx0 = max(0, -x); sy0 = max(0, -y)
    sx1 = min(sw, cw - x); sy1 = min(sh, ch - y)
    if sx0 >= sx1 or sy0 >= sy1:
        return
    canvas[y+sy0:y+sy1, x+sx0:x+sx1] = sprite[sy0:sy1, sx0:sx1]

# Draw filled rectangle
def draw_rect(canvas, x, y, w, h, color_bgr):
    ch_h, ch_w = canvas.shape[:2]
    x0 = max(0, x); y0 = max(0, y)
    x1 = min(ch_w, x + w); y1 = min(ch_h, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    canvas[y0:y1, x0:x1] = color_bgr


def draw_rect_border(canvas, x, y, w, h, color_bgr, thickness=4):
    draw_rect(canvas, x, y, w, thickness, color_bgr)             # top
    draw_rect(canvas, x, y + h - thickness, w, thickness, color_bgr)  # bottom
    draw_rect(canvas, x, y, thickness, h, color_bgr)              # left
    draw_rect(canvas, x + w - thickness, y, thickness, h, color_bgr)  # right

# Bitmap text rendering
def draw_text(canvas, text, x, y, scale=2, color_bgr=(0, 0, 0)):
    cx = x
    for ch in text.upper():
        glyph = FONT_GLYPHS.get(ch)
        if glyph is None:
            cx += (C.FONT_CHAR_W + 1) * scale   
            continue
        # Scale glyph
        big = nn_scale(glyph, scale)
        gh, gw = big.shape
        # Clip to canvas
        ch_h, ch_w = canvas.shape[:2]
        gx0 = max(0, -cx);   gy0 = max(0, -y)
        gx1 = min(gw, ch_w - cx); gy1 = min(gh, ch_h - y)
        if gx0 < gx1 and gy0 < gy1:
            mask = big[gy0:gy1, gx0:gx1] > 0
            region = canvas[y+gy0:y+gy1, cx+gx0:cx+gx1]
            region[mask] = color_bgr
        cx += (C.FONT_CHAR_W + 1) * scale


def text_width(text, scale=2):
    return len(text) * (C.FONT_CHAR_W + 1) * scale - scale


def text_height(scale=2):
    return C.FONT_CHAR_H * scale


# Panel
def draw_panel(canvas, x, y, w, h, border=4, lip=16):
    draw_rect(canvas, x, y, w, h, (C.BLACK, C.BLACK, C.BLACK))     # Outer black border
    draw_rect(canvas, x + border, y + border, w - 2 * border, h - 2 * border, (C.WHITE, C.WHITE, C.WHITE))    # Inner white fill
    draw_rect(canvas, x + border, y + h - border - lip, w - 2 * border, lip, (C.LGRAY, C.LGRAY, C.LGRAY))    # Gray lower lip


# Hand cursor (generated, matches pixel style) (P2)
def make_cursor(size=20):
    s = size
    sprite = np.full((s, s, 3), C.WHITE, dtype=np.uint8)
    alpha  = np.zeros((s, s), dtype=np.uint8)
    cx, cy = s // 2, s // 2
    t = 2  # thickness

    # Horizontal bar
    sprite[cy - t//2 : cy + t//2 + t%2, :, :] = 0
    alpha [cy - t//2 : cy + t//2 + t%2, :] = 255

    # Vertical bar
    sprite[:, cx - t//2 : cx + t//2 + t%2, :] = 0
    alpha [:, cx - t//2 : cx + t//2 + t%2] = 255

    return sprite, alpha


# Progress bar under a button (P2)
def draw_progress_bar(canvas, x, y, w, h, progress, color_bgr=(C.BLACK,)*3):
    progress = max(0.0, min(1.0, progress))
    fill_w = int(w * progress)
    if fill_w > 0:
        draw_rect(canvas, x, y, fill_w, h, color_bgr)
