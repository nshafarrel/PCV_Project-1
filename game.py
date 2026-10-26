import math
import random
import numpy as np
import config as C



# Ball
class Ball:
    def __init__(self):
        self.x = 0.0          # centre x
        self.y = 0.0          # centre y
        self.vx = 0.0         # speed x
        self.vy = 0.0         # speed y
        self.speed = C.BALL_START_SPEED
        self.size = C.BALL_DRAW_SIZE 
        self.half = self.size / 2.0

    def reset(self):
        self.x = C.WIN_W / 2.0
        self.y = C.WIN_H / 2.0
        self.speed = C.BALL_START_SPEED

        angle_deg = random.uniform(-C.SERVE_ANGLE_MAX, C.SERVE_ANGLE_MAX)
        angle_rad = math.radians(angle_deg)
        direction = random.choice([-1, 1])

        self.vx = direction * self.speed * math.cos(angle_rad)
        self.vy = self.speed * math.sin(angle_rad)

    @property
    def left(self):   return self.x - self.half
    @property
    def right(self):  return self.x + self.half
    @property
    def top(self):    return self.y - self.half
    @property
    def bottom(self): return self.y + self.half


# Paddle
class Paddle:
    def __init__(self, side):
        """*side*: 'left' or 'right'."""
        self.w = C.PADDLE_W
        self.h = C.PADDLE_H
        self.half_h = self.h / 2.0
        self.half_w = self.w / 2.0

        if side == 'left':
            self.x = C.PADDLE_MARGIN                   # centre x
        else:
            self.x = C.WIN_W - C.PADDLE_MARGIN          # centre x
        self.y = C.WIN_H / 2.0                          # centre y

    def set_y(self, norm_y):
        self.y = norm_y * C.WIN_H
        # Clamp so paddle stays on screen
        self.y = max(self.half_h, min(C.WIN_H - self.half_h, self.y))

    @property
    def left(self):   return self.x - self.half_w
    @property
    def right(self):  return self.x + self.half_w
    @property
    def top(self):    return self.y - self.half_h
    @property
    def bottom(self): return self.y + self.half_h


# Swept collision  
def _swept_paddle_hit(ball, paddle, dt):
    # Future position
    nx = ball.x + ball.vx * dt
    ny = ball.y + ball.vy * dt

    # Check side of the paddle for ball
    if ball.vx > 0:
        face_x = paddle.left
        if ball.right <= face_x and nx + ball.half >= face_x:
            t = (face_x - ball.right) / (ball.vx * dt)
            if 0 <= t <= 1:
                hit_y = ball.y + ball.vy * dt * t
                if paddle.top - ball.half <= hit_y <= paddle.bottom + ball.half:
                    _reflect(ball, paddle, hit_y, face_x, dt, t)
                    return True
    elif ball.vx < 0:
        face_x = paddle.right
        if ball.left >= face_x and nx - ball.half <= face_x:
            t = (face_x - ball.left) / (ball.vx * dt)
            if 0 <= t <= 1:
                hit_y = ball.y + ball.vy * dt * t
                if paddle.top - ball.half <= hit_y <= paddle.bottom + ball.half:
                    _reflect(ball, paddle, hit_y, face_x, dt, t)
                    return True
    return False


def _reflect(ball, paddle, hit_y, face_x, dt, t):
    rel = (hit_y - paddle.y) / paddle.half_h
    rel = max(-1.0, min(1.0, rel))

    # Reflection angle
    angle_deg = rel * C.PADDLE_ANGLE_MAX
    angle_rad = math.radians(angle_deg)
    ball.speed = min(ball.speed * C.BALL_SPEED_GAIN, C.BALL_MAX_SPEED)     # Increase speed

    direction = 1.0 if ball.vx < 0 else -1.0
    ball.vx = direction * ball.speed * math.cos(angle_rad)
    ball.vy = ball.speed * math.sin(angle_rad)

    if direction > 0:
        ball.x = face_x + ball.half + 1
    else:
        ball.x = face_x - ball.half - 1
    ball.y = hit_y


class GameState:
    def __init__(self):
        self.ball = Ball()
        self.p1_paddle = Paddle('left')
        self.p2_paddle = Paddle('right')
        self.score1 = 0
        self.score2 = 0
        self.winner = None      # None, 1, or 2

    def new_match(self):
        self.score1 = 0
        self.score2 = 0
        self.winner = None
        self.ball.reset()

    def update(self, dt):
        ball = self.ball

        # Wall bounces (top / bottom)
        ny = ball.y + ball.vy * dt
        if ny - ball.half < 0:
            ball.vy = abs(ball.vy)
            ball.y = ball.half
        elif ny + ball.half > C.WIN_H:
            ball.vy = -abs(ball.vy)
            ball.y = C.WIN_H - ball.half

        # Paddle collisions (swept)
        hit1 = _swept_paddle_hit(ball, self.p1_paddle, dt)
        hit2 = _swept_paddle_hit(ball, self.p2_paddle, dt)

        # Move ball
        ball.x += ball.vx * dt
        ball.y += ball.vy * dt

        # Scoring
        if ball.right < 0:                  # Ball left the left edge, P2 scores
            self.score2 += 1
            if self.score2 >= C.SCORE_TO_WIN:
                self.winner = 2
            else:
                ball.reset()
            return 'scored_right'

        if ball.left > C.WIN_W:             # Ball left the right edge, P1 scores
            self.score1 += 1
            if self.score1 >= C.SCORE_TO_WIN:
                self.winner = 1
            else:
                ball.reset()
            return 'scored_left'

        return None
