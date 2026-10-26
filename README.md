# Pong Citra Video – README

## Overview
A two-player Pong game controlled by palm detection via webcam.
Built entirely with **NumPy** for pixel operations and minimal **OpenCV** for camera I/O and window display.

## Requirements
- Python 3.8+
- numpy
- opencv-python

```
pip install -r requirements.txt
```

## Running
```
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| **C** | Calibrate skin colour (menu only) |
| **M** | Toggle picture-in-picture mask preview |
| **ESC** | Exit from menu |

### Gameplay
- **No keyboard or mouse gameplay.** Both players control paddles with their palms.
- Stand facing the camera. Left player uses the left side of the frame, right player uses the right side.
- Move your palm up and down to control your paddle.
- Hold your palm over a button for 1 second to press it.
- First player to 7 points wins.

## Calibration Tips
1. From the menu, press **C** to enter calibration mode.
2. Place your open palm in the centre box on screen.
3. Make sure your palm fills most of the box.
4. Press **C** again to capture the colour.
5. Use consistent, even lighting. Avoid backlighting.
6. If detection is poor, recalibrate or adjust lighting.
7. Keep your face outside the active detection zones (far left and far right of the camera view).
8. A plain background behind your hands works best.

## Project Structure

| File | Purpose |
|------|---------|
| `main.py` | Entry point, state machine, game loop |
| `config.py` | All tunable constants |
| `assets.py` | Asset loading, alpha extraction, sprite scaling |
| `render.py` | Drawing primitives: font, blitting, rectangles |
| `vision.py` | BGR→HSV, skin mask, morphology, blob detection |
| `game.py` | Ball physics, paddle state, swept collision |
| `ui.py` | Button dwell logic, screen layouts |
| `check_rules.py` | Source scanner for forbidden cv2 usage |
| `asset/` | Image assets (ball, paddle, buttons, background) |

## Course Constraints
- Only `cv2.imread`, `cv2.imshow`, `cv2.VideoCapture`, `cv2.waitKey`, `cv2.namedWindow`, `cv2.destroyAllWindows` are used from OpenCV.
- All pixel operations are manual NumPy: colour conversion, thresholding, morphology, blob detection, sprite blitting, text rendering.
- No per-pixel Python loops. All operations use vectorized slicing and boolean masks.
- Run `python check_rules.py` to verify compliance.
