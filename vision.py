import numpy as np
import config as C


# BGR → HSV 
def bgr_to_hsv(frame):
    img = frame.astype(np.float32) / 255.0   # normalise to [0, 1]
    b = img[:, :, 0]
    g = img[:, :, 1]
    r = img[:, :, 2]

    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin

    v = cmax     # Value

    s = np.zeros_like(v)     # Saturation
    nz = cmax > 0
    s[nz] = delta[nz] / cmax[nz]

    h = np.zeros_like(v)     # Hue
    mask = delta > 0

    # Red is max
    m = mask & (cmax == r)
    h[m] = 60.0 * (((g[m] - b[m]) / delta[m]) % 6.0)

    # Green is max
    m = mask & (cmax == g)
    h[m] = 60.0 * ((b[m] - r[m]) / delta[m] + 2.0)

    # Blue is max
    m = mask & (cmax == b)
    h[m] = 60.0 * ((r[m] - g[m]) / delta[m] + 4.0)

    # Convert to OpenCV scale
    h_out = (h / 2.0).astype(np.uint8)
    s_out = (s * 255.0).astype(np.uint8)
    v_out = (v * 255.0).astype(np.uint8)           

    return np.stack([h_out, s_out, v_out], axis=-1)

# Skin-color mask
def skin_mask(hsv, h_lo1, h_hi1, h_lo2, h_hi2, s_lo, s_hi, v_lo, v_hi):
    h = hsv[:, :, 0]
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]

    # Hue range 1
    hue_ok = (h >= h_lo1) & (h <= h_hi1)
    # Hue range 2
    hue_ok |= (h >= h_lo2) & (h <= h_hi2)

    # Saturation + value
    sv_ok = (s >= s_lo) & (s <= s_hi) & (v >= v_lo) & (v <= v_hi)

    return hue_ok & sv_ok

# Morphological operations
def _pad(mask, p=1):
    h, w = mask.shape
    out = np.zeros((h + 2*p, w + 2*p), dtype=bool)
    out[p:p+h, p:p+w] = mask
    return out

def erode_3x3(mask):
    padded = _pad(mask, 1)
    h, w = mask.shape
    result = np.ones((h, w), dtype=bool)
    for dy in range(3):
        for dx in range(3):
            result &= padded[dy:dy+h, dx:dx+w]
    return result

def dilate_3x3(mask):
    padded = _pad(mask, 1)
    h, w = mask.shape
    result = np.zeros((h, w), dtype=bool)
    for dy in range(3):
        for dx in range(3):
            result |= padded[dy:dy+h, dx:dx+w]
    return result

def morph_open(mask, iters=1):
    m = mask
    for _ in range(iters):
        m = erode_3x3(m)
    for _ in range(iters):
        m = dilate_3x3(m)
    return m

def morph_close(mask, iters=1):
    m = mask
    for _ in range(iters):
        m = dilate_3x3(m)
    for _ in range(iters):
        m = erode_3x3(m)
    return m

# Largest blob selection
def _integral_image(mask):
    return np.cumsum(np.cumsum(mask.astype(np.int32), axis=0), axis=1)

def _box_sum(integral, cy, cx, r):
    h, w = integral.shape
    y0 = max(0, cy - r) - 1
    y1 = min(h - 1, cy + r)
    x0 = max(0, cx - r) - 1
    x1 = min(w - 1, cx + r)

    s = integral[y1, x1]
    if y0 >= 0:
        s -= integral[y0, x1]
    if x0 >= 0:
        s -= integral[y1, x0]
    if y0 >= 0 and x0 >= 0:
        s += integral[y0, x0]
    return s


def largest_blob(mask, box_r=None, grow_iters=None):
    if box_r is None:
        box_r = C.BLOB_BOX
    if grow_iters is None:
        grow_iters = C.BLOB_GROW_ITERS

    h, w = mask.shape
    if mask.sum() == 0:
        return mask.copy()

    integral = _integral_image(mask)

    # Coarse grid search for densest point (step = box_r)
    best_val = -1
    best_y, best_x = 0, 0
    step = max(1, box_r // 2)
    for cy in range(0, h, step):
        for cx in range(0, w, step):
            val = _box_sum(integral, cy, cx, box_r)
            if val > best_val:
                best_val = val
                best_y, best_x = cy, cx

    # Seed: small box around best point, restricted to mask
    seed = np.zeros((h, w), dtype=bool)
    r = box_r
    sy0 = max(0, best_y - r); sy1 = min(h, best_y + r + 1)
    sx0 = max(0, best_x - r); sx1 = min(w, best_x + r + 1)
    seed[sy0:sy1, sx0:sx1] = mask[sy0:sy1, sx0:sx1]

    # Grow by dilation restricted to mask (bounded loop, capped)
    for _ in range(grow_iters):
        grown = dilate_3x3(seed) & mask
        if np.array_equal(grown, seed):
            break
        seed = grown

    return seed



# Hand tracker state (per player)
class HandTracker:
    def __init__(self):
        self.smooth_y = 0.5         # normalised y, starts at centre
        self.last_valid = False     # was the hand seen last frame?
        self.lost = True            # currently lost

    def update(self, blob_mask, zone_slice_x):
        zone = blob_mask[:, zone_slice_x]
        area = int(zone.sum())

        if area < C.MIN_BLOB_AREA:
            # Hand lost – hold last position
            self.lost = True
            return self.smooth_y

        # Centroid y
        ys = np.where(zone)[0]
        cy = float(ys.mean())
        h = blob_mask.shape[0]

        # Map from middle 80 % → [0, 1]
        lo = h * C.MAP_Y_LO
        hi = h * C.MAP_Y_HI
        normed = (cy - lo) / (hi - lo)
        normed = max(0.0, min(1.0, normed))

        # EMA smoothing
        self.smooth_y = C.EMA_ALPHA * normed + (1 - C.EMA_ALPHA) * self.smooth_y
        self.lost = False
        return self.smooth_y

# Neutral-zone tracker (for menu cursor)
class CursorTracker:
    def __init__(self):
        self.smooth_x = 0.5
        self.smooth_y = 0.5
        self.active = False

    def update(self, blob_mask):
        area = int(blob_mask.sum())
        if area < C.MIN_BLOB_AREA:
            self.active = False
            return self.smooth_x, self.smooth_y

        ys, xs = np.where(blob_mask)
        cy = float(ys.mean())
        cx = float(xs.mean())
        h, w = blob_mask.shape

        nx = cx / w
        ny = cy / h

        self.smooth_x = C.EMA_ALPHA * nx + (1 - C.EMA_ALPHA) * self.smooth_x
        self.smooth_y = C.EMA_ALPHA * ny + (1 - C.EMA_ALPHA) * self.smooth_y
        self.active = True
        return self.smooth_x, self.smooth_y



# Function
def process_frame(frame, hsv_params):
    # Mirror horizontally using slicing
    mirrored = frame[:, ::-1, :].copy()

    # Downsample to 160×120 with slicing
    small = mirrored[::4, ::4, :]

    # BGR → HSV
    hsv = bgr_to_hsv(small)

    # Skin-color thresholding
    raw_mask = skin_mask(
        hsv,
        hsv_params['h_lo1'], hsv_params['h_hi1'],
        hsv_params['h_lo2'], hsv_params['h_hi2'],
        hsv_params['s_lo'],  hsv_params['s_hi'],
        hsv_params['v_lo'],  hsv_params['v_hi'],
    )

    # Morphological opening then closing
    cleaned = morph_open(raw_mask, C.MORPH_OPEN_ITERS)
    cleaned = morph_close(cleaned, C.MORPH_CLOSE_ITERS)

    # Split into left and right zones (no exclusion area)
    h, w = cleaned.shape
    mid_x = w // 2

    # Left zone blob (left half)
    left_zone_mask = np.zeros_like(cleaned)
    left_zone_mask[:, :mid_x] = cleaned[:, :mid_x]
    left_blob = largest_blob(left_zone_mask)

    # Right zone blob (right half)
    right_zone_mask = np.zeros_like(cleaned)
    right_zone_mask[:, mid_x:] = cleaned[:, mid_x:]
    right_blob = largest_blob(right_zone_mask)

    # Full-frame blob (for menu cursor)
    full_blob = largest_blob(cleaned)

    return mirrored, cleaned, left_blob, right_blob, full_blob

# Calibration helper
def calibrate_from_roi(frame, box_size=None):
    if box_size is None:
        box_size = C.CALIB_BOX

    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    half = box_size // 2
    roi = frame[cy-half:cy+half, cx-half:cx+half]

    hsv = bgr_to_hsv(roi)
    med_h = int(np.median(hsv[:, :, 0]))
    med_s = int(np.median(hsv[:, :, 1]))
    med_v = int(np.median(hsv[:, :, 2]))

    # Build ranges
    s_lo = max(0, med_s - C.CALIB_S_MARGIN)
    s_hi = min(255, med_s + C.CALIB_S_MARGIN)
    v_lo = max(0, med_v - C.CALIB_V_MARGIN)
    v_hi = min(255, med_v + C.CALIB_V_MARGIN)

    h_margin = C.CALIB_H_MARGIN
    h_lo = med_h - h_margin
    h_hi = med_h + h_margin

    if h_lo < 0:
        # Red wrap: hue wraps around 0/179
        return {
            'h_lo1': 0,        'h_hi1': h_hi,
            'h_lo2': 180 + h_lo, 'h_hi2': 179,
            's_lo': s_lo, 's_hi': s_hi,
            'v_lo': v_lo, 'v_hi': v_hi,
        }
    elif h_hi > 179:
        return {
            'h_lo1': h_lo,     'h_hi1': 179,
            'h_lo2': 0,        'h_hi2': h_hi - 180,
            's_lo': s_lo, 's_hi': s_hi,
            'v_lo': v_lo, 'v_hi': v_hi,
        }
    else:
        return {
            'h_lo1': h_lo,     'h_hi1': h_hi,
            'h_lo2': 200,      'h_hi2': 200,   # effectively disabled
            's_lo': s_lo, 's_hi': s_hi,
            'v_lo': v_lo, 'v_hi': v_hi,
        }
