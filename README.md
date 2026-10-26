# Pong Citra Video – README

## Overview
Game Pong untuk 2-Player menggunakan deteksi warna telapak tangan menggunakan **OpenCV** melalui kamera web sebagai input penggerak paddle.
Dibuat dengan menggunakan **NumPy** untuk operasi piksel manual dan **OpenCV** hanya untuk imread, imshow, VideoCapture.

![Menu](./guide/00_menu.png)

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
| `asset/` | Image assets (ball, paddle, buttons, background) |

## Requirements
- Python 3.8+
- numpy
- opencv-python

```
pip install numpy opencv-python
```

## Running
```
python main.py
```

## Controls

| Key | Action | Examples |
|-----|--------|---------|
| **C** | Kalibrasi warna kulit untuk tracking | ![Kalibrasi](./guide/01_kalibrasi.png) |
| **M** | Toggle picture-in-picture untuk preview masking | ![Mask](./guide/02_mask.png) |
| **ESC** | Exit dari menu | ![Paused](./guide/05_pause.png) |


### Gameplay
- Kedua pemain mengendalikan paddles dengan menggerakan tangan, tidak menggunakan mouse atau keyboard untuk gameplay.
![Game](./guide/04_game.png)
- Pemain di sebelah kiri mengendalikan paddle kiri, pemain di sebelah kanan mengendalikan paddle kanan.
- Gerakkan telapak tangan ke atas dan ke bawah untuk mengendalikan paddle.
- Posisikan tangan di atas tombol selama 1 detik untuk menekannya.
- Pemain pertama yang mencetak 5 poin menang

![Help](./guide/03_help.png)

## Calibration (untuk tracking yang lebih mulus)
1. Dari menu, tekan **C** untuk masuk mode kalibrasi.
2. Letakkan telapak tangan di kotak tengah pada layar.
![Kalibrasi](./guide/01_kalibrasi.png)
3. Pastikan telapak tangan memenuhi sebagian besar kotak.
4. Tekan **C** lagi untuk menyimpan warna.
5. Gunakan pencahayaan yang konsisten dan ideal.
6. Jika hasil deteksi buruk, ulangi kalibrasi atau sesuaikan pencahayaan.
7. Jauhkan wajah dari area deteksi.

## Constraints
- Only `cv2.imread`, `cv2.imshow`, `cv2.VideoCapture`, `cv2.waitKey`, `cv2.namedWindow`, `cv2.destroyAllWindows` are used from OpenCV.
- All pixel operations are manual NumPy: colour conversion, thresholding, morphology, blob detection, sprite blitting, text rendering.
