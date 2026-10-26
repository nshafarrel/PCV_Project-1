import numpy as np
import config as C
import render as R


# Button with dwell activation
class DwellButton:
    def __init__(self, name, assets_entry, cx, cy):
        self.name = name
        self.bgr, self.alpha, self.w, self.h = assets_entry
        self.cx = cx
        self.cy = cy
        self.x = cx - self.w // 2
        self.y = cy - self.h // 2
        self.dwell = 0.0        # accumulated hover time (seconds)

    def contains(self, px, py):
        return (self.x <= px < self.x + self.w and
                self.y <= py < self.y + self.h)

    def update(self, cursor_x, cursor_y=None, dt=None):
        if dt is None:
            cursors = cursor_x
            dt = cursor_y
        else:
            cursors = [(cursor_x, cursor_y)]

        if not isinstance(cursors, (list, tuple)) or (len(cursors) == 2 and isinstance(cursors[0], (int, float))):
            cursors = [cursors]

        any_inside = False
        for c in cursors:
            if c is not None and len(c) >= 2 and c[0] is not None and c[1] is not None:
                if self.contains(c[0], c[1]):
                    any_inside = True
                    break

        if any_inside:
            self.dwell += dt
            if self.dwell >= C.DWELL_TIME:
                self.dwell = 0.0
                return True
        else:
            self.dwell = 0.0
        return False

    def draw(self, canvas):
        R.blit_alpha(canvas, self.bgr, self.alpha, self.x, self.y)
        # Progress bar below the button
        if self.dwell > 0:
            progress = self.dwell / C.DWELL_TIME
            bar_h = 6
            bar_y = self.y + self.h + 2
            R.draw_progress_bar(canvas, self.x, bar_y, self.w, bar_h,
                                progress, (C.BLACK, C.BLACK, C.BLACK))

# Screen builders
def make_menu_buttons(assets):
    mid_x = C.WIN_W // 2
    start_y = 340
    gap = 90
    return [
        DwellButton("start",    assets.buttons["start"],    mid_x, start_y),
        DwellButton("help",     assets.buttons["help"],     mid_x, start_y + gap),
        DwellButton("exit",     assets.buttons["exit"],     mid_x, start_y + 2 * gap),
    ]


def make_help_buttons(assets): # CLOSE button for the help popup
    return [
        DwellButton("close", assets.buttons["close"],
                    C.WIN_W // 2, 530),
    ]


def make_pause_button(assets): # in-game pause button at top centre
    return DwellButton("pause", assets.buttons["pause"],
                       C.WIN_W // 2, 30)


def make_paused_buttons(assets): # CONTINUE and EXIT buttons for the pause overlay
    mid_x = C.WIN_W // 2
    return [
        DwellButton("continue", assets.buttons["continue"], mid_x, 380),
        DwellButton("exit",     assets.buttons["exit"],     mid_x, 460),
    ]


def make_gameover_buttons(assets): # CONTINUE (rematch) and EXIT (menu) for game-over overlay
    mid_x = C.WIN_W // 2
    return [
        DwellButton("continue", assets.buttons["continue"], mid_x, 420),
        DwellButton("exit",     assets.buttons["exit"],     mid_x, 500),
    ]



# Drawing helpers for HUD / overlays
def draw_scores(canvas, score1, score2): # P1 and P2 scores at the top of the scree
    # P1 score
    s1_text = f"P1  {score1}"
    R.draw_text(canvas, s1_text, (C.WIN_W // 2 - 180) + 48, 14, scale=3,
                color_bgr=(C.BLACK, C.BLACK, C.BLACK))
    # P2 score
    s2_text = f"{score2}  P2"
    tw = R.text_width(s2_text, 3)
    R.draw_text(canvas, s2_text, (C.WIN_W // 2 + 180 - tw) - 48, 14, scale=3,
                color_bgr=(C.BLACK, C.BLACK, C.BLACK))


def draw_cursors(canvas, assets, cursor_x, cursor_y=None): # Dual hand tracking cursor
    if cursor_y is not None:
        items = [(cursor_x, cursor_y, None, True)]
    elif isinstance(cursor_x, (list, tuple)):
        if len(cursor_x) == 2 and isinstance(cursor_x[0], (int, float)):
            items = [(cursor_x[0], cursor_x[1], None, True)]
        else:
            items = []
            for it in cursor_x:
                if it is None:
                    continue
                if len(it) == 2:
                    items.append((it[0], it[1], None, True))
                elif len(it) == 3:
                    items.append((it[0], it[1], it[2], True))
                elif len(it) >= 4:
                    if it[3]:  # is_active
                        items.append((it[0], it[1], it[2], True))
    else:
        return

    for cx, cy, label, _ in items:
        if cx is None or cy is None:
            continue
        px = int(cx) - C.CURSOR_SIZE // 2
        py = int(cy) - C.CURSOR_SIZE // 2
        R.blit_alpha(canvas, assets.cursor_bgr, assets.cursor_alpha, px, py)
        if label:
            R.draw_text(canvas, str(label), px + C.CURSOR_SIZE + 2, py - 4, scale=1,
                        color_bgr=(C.BLACK, C.BLACK, C.BLACK))


def draw_menu_screen(canvas, assets, buttons, cursor_x, cursor_y=None): # Main menu screen
    # Background
    R.blit_opaque(canvas, assets.bg, 0, 0)

    # Title
    title = "PONG CITRA VIDEO"
    tw = R.text_width(title, scale=5)
    R.draw_text(canvas, title, (C.WIN_W - tw) // 2, 120, scale=5,
                color_bgr=(C.BLACK, C.BLACK, C.BLACK))

    # Subtitle
    sub = "PRESS C TO CALIBRATE"
    sw = R.text_width(sub, scale=2)
    R.draw_text(canvas, sub, (C.WIN_W - sw) // 2, 220, scale=2,
                color_bgr=(C.DGRAY, C.DGRAY, C.DGRAY))

    # Buttons
    for btn in buttons:
        btn.draw(canvas)

    # Cursor(s)
    draw_cursors(canvas, assets, cursor_x, cursor_y)


def draw_help_popup(canvas, assets, buttons, cursor_x, cursor_y=None): # How to play popup
    pw, ph = 700, 360
    px = (C.WIN_W - pw) // 2
    py = (C.WIN_H - ph) // 2

    R.draw_panel(canvas, px, py, pw, ph, border=4, lip=20)

    # Title
    title = "HOW TO PLAY"
    tw = R.text_width(title, 3)
    R.draw_text(canvas, title, (C.WIN_W - tw) // 2, py + 20, scale=3,
                color_bgr=(C.BLACK, C.BLACK, C.BLACK))

    # Instructions
    lines = [
        "STAND FACING THE CAMERA",
        "LEFT PLAYER USES THE LEFT SIDE",
        "RIGHT PLAYER USES THE RIGHT SIDE",
        "MOVE YOUR PALM UP AND DOWN",
        "TO MOVE YOUR PADDLE",
        f"FIRST TO {C.SCORE_TO_WIN} POINTS WINS",
        "PRESS P OR HOLD PAUSE BUTTON TO PAUSE THE GAME",
    ]
    ly = py + 75
    for line in lines:
        lw = R.text_width(line, 2)
        R.draw_text(canvas, line, (C.WIN_W - lw) // 2, ly, scale=2,
                    color_bgr=(C.DGRAY, C.DGRAY, C.DGRAY))
        ly += 28

    # Buttons
    for btn in buttons:
        btn.draw(canvas)

    # Cursor(s)
    draw_cursors(canvas, assets, cursor_x, cursor_y)


def draw_playing_screen(canvas, assets, game_state, pause_btn, p1_lost, p2_lost, cursors=None, cursor_y=None):
    # Background
    R.blit_opaque(canvas, assets.bg, 0, 0)

    # Paddles
    _draw_paddle(canvas, assets, game_state.p1_paddle, p1_lost)
    _draw_paddle(canvas, assets, game_state.p2_paddle, p2_lost)

    # Ball
    bx = int(game_state.ball.x - game_state.ball.half)
    by = int(game_state.ball.y - game_state.ball.half)
    R.blit_alpha(canvas, assets.ball_bgr, assets.ball_alpha, bx, by)

    # HUD: scores + pause button
    draw_scores(canvas, game_state.score1, game_state.score2)
    if pause_btn is not None:
        pause_btn.draw(canvas)

    # During active match, draw both hand cursors
    if cursors is not None:
        draw_cursors(canvas, assets, cursors, cursor_y)


def _draw_paddle(canvas, assets, paddle, lost):
    px = int(paddle.left)
    py = int(paddle.top)
    if not lost:
        R.blit_alpha(canvas, assets.paddle_bgr, assets.paddle_alpha, px, py)
    else:
        R.draw_rect_border(canvas, px, py, paddle.w, paddle.h,
                           (C.DGRAY, C.DGRAY, C.DGRAY), thickness=2)
        mid_y = int(paddle.y)
        R.draw_dashed_hline(canvas, px, px + paddle.w, mid_y,
                            (C.DGRAY, C.DGRAY, C.DGRAY))


def draw_paused_overlay(canvas, assets, buttons, cursor_x, cursor_y=None): # Paused overlay
    pw, ph = 400, 250
    px = (C.WIN_W - pw) // 2
    py = (C.WIN_H - ph) // 2

    R.draw_panel(canvas, px, py, pw, ph, border=4, lip=20)

    title = "PAUSED"
    tw = R.text_width(title, 4)
    R.draw_text(canvas, title, (C.WIN_W - tw) // 2, py + 30, scale=4,
                color_bgr=(C.BLACK, C.BLACK, C.BLACK))

    for btn in buttons:
        btn.draw(canvas)

    draw_cursors(canvas, assets, cursor_x, cursor_y)


def draw_gameover_overlay(canvas, assets, winner, buttons, cursor_x, cursor_y=None): # Game over overlay
    pw, ph = 500, 300
    px = (C.WIN_W - pw) // 2
    py = (C.WIN_H - ph) // 2

    R.draw_panel(canvas, px, py, pw, ph, border=4, lip=20)

    title = "GAME OVER"
    tw = R.text_width(title, 4)
    R.draw_text(canvas, title, (C.WIN_W - tw) // 2, py + 25, scale=4,
                color_bgr=(C.BLACK, C.BLACK, C.BLACK))

    who = f"P{winner} WINS!"
    ww = R.text_width(who, 3)
    R.draw_text(canvas, who, (C.WIN_W - ww) // 2, py + 80, scale=3,
                color_bgr=(C.DGRAY, C.DGRAY, C.DGRAY))

    for btn in buttons:
        btn.draw(canvas)

    draw_cursors(canvas, assets, cursor_x, cursor_y)


def draw_calibration_screen(canvas, frame, box_size=None): # Calibration screen
    if box_size is None:
        box_size = C.CALIB_BOX

    # Resize camera frame to fill the window
    from render import nn_resize
    cam = nn_resize(frame, C.WIN_H, C.WIN_W)
    canvas[:, :, :] = cam

    # Draw guide box at centre
    cx, cy = C.WIN_W // 2, C.WIN_H // 2
    half = box_size
    R.draw_rect_border(canvas, cx - half, cy - half,
                       half * 2, half * 2,
                       (C.BLACK, C.BLACK, C.BLACK), thickness=3)

    # Instructions
    txt = "PLACE PALM IN BOX - PRESS C TO CAPTURE - ESC TO CANCEL"
    tw = R.text_width(txt, 2)
    R.draw_text(canvas, txt, (C.WIN_W - tw) // 2, 30, scale=2,
                color_bgr=(C.BLACK, C.BLACK, C.BLACK))


def draw_pip_mask(canvas, mask, scale=None):
    if scale is None:
        scale = C.PIP_SCALE
    from render import nn_scale
    # Convert bool mask to uint8 grayscale
    vis = (mask.astype(np.uint8) * 255)
    vis_big = nn_scale(vis, scale)  # (H*s, W*s)
    # Make it 3-channel
    vis3 = np.stack([vis_big, vis_big, vis_big], axis=-1)
    ph, pw = vis3.shape[:2]

    # Horizontal center, vertical position
    x = (C.WIN_W - pw) // 2
    y = (C.WIN_H - ph) - 8

    # Draw border with header panel
    R.draw_rect(canvas, x - 4, y - 28, pw + 8, ph + 32, (C.BLACK, C.BLACK, C.BLACK))
    R.draw_rect(canvas, x - 2, y - 26, pw + 4, 24, (C.WHITE, C.WHITE, C.WHITE))
    title = "MASK PREVIEW [M TO CLOSE]"
    tw = R.text_width(title, 2)
    R.draw_text(canvas, title, x + (pw - tw) // 2, y - 22, scale=2,
                color_bgr=(C.BLACK, C.BLACK, C.BLACK))

    R.blit_opaque(canvas, vis3, x, y)
