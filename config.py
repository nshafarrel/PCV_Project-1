import os

# Paths
ASSET_DIR = os.path.join(os.path.dirname(__file__), "asset")

# Window
WIN_W = 1280
WIN_H = 720
WIN_TITLE = "Pong Citra Video"

# Palette
BLACK   = 0
DGRAY   = 153
LGRAY   = 204
VLGRAY  = 230
VLGRAY2 = 247
WHITE   = 255

# Camera
CAM_W = 640
CAM_H = 480
DOWN_W = 128
DOWN_H = 96
CAM_INDEX = 0

# Hand detection zones
LEFT_ZONE_END    = 0.50
RIGHT_ZONE_START = 0.50

# Default skin HSV ranges (OpenCV scale: H 0‑179, S/V 0‑255)
HSV_H_LO1 = 0 
HSV_H_HI1 = 25 
HSV_H_LO2 = 160 
HSV_H_HI2 = 179 
HSV_S_LO  = 30 
HSV_S_HI  = 200 
HSV_V_LO  = 60
HSV_V_HI  = 255 

# Morphology
MORPH_KERNEL = 3
MORPH_OPEN_ITERS  = 1
MORPH_CLOSE_ITERS = 1

# Blob selection
BLOB_BOX = 11
BLOB_GROW_ITERS = 40
MIN_BLOB_AREA = 40

# EMA smoothing
EMA_ALPHA = 0.4

# Paddle mapping (fraction of camera height)
MAP_Y_LO = 0.05   
MAP_Y_HI = 0.95  

# Game play
FPS = 60
FIXED_DT = 1.0 / FPS

BALL_SIZE       = 32
BALL_SCALE      = 2
BALL_DRAW_SIZE  = BALL_SIZE * BALL_SCALE
BALL_START_SPEED = 720.0
BALL_SPEED_GAIN  = 1.1
BALL_MAX_SPEED   = 2000.0

SERVE_ANGLE_MAX  = 35.0
PADDLE_ANGLE_MAX = 55.0

PADDLE_W = 24
PADDLE_H = 140
PADDLE_MARGIN = 40     

SCORE_TO_WIN = 5

# UI
DWELL_TIME = 1.0                    # seconds to hold for button press
CURSOR_SIZE = 20                    # hand cursor radius
PIP_SCALE = 2                       # picture‑in‑picture mask enlargement

# Calibration
CALIB_BOX = 80                      # side length of calibration square (px in cam)
CALIB_H_MARGIN = 12                 # ± margin around median hue
CALIB_S_MARGIN = 50                 # ± margin around median saturation
CALIB_V_MARGIN = 60                 # ± margin around median value

# Font
FONT_CHAR_W = 5 
FONT_CHAR_H = 7 
