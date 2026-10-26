import time
import numpy as np
import cv2

import config as C
from assets import Assets
from vision import (process_frame, HandTracker, CursorTracker, calibrate_from_roi)
from game import GameState
import ui

def main():
    #  Camera 
    cap = cv2.VideoCapture(C.CAM_INDEX)
    cap.set(3, C.CAM_W) 
    cap.set(4, C.CAM_H) 
    if not cap.isOpened():
        print("ERROR: Cannot open camera.")
        return

    #  Window 
    cv2.namedWindow(C.WIN_TITLE, cv2.WINDOW_NORMAL)

    #  Assets 
    assets = Assets()
    assets.load()
    print("Assets loaded.")

    #  HSV parameters
    hsv_params = {
        'h_lo1': C.HSV_H_LO1, 'h_hi1': C.HSV_H_HI1,
        'h_lo2': C.HSV_H_LO2, 'h_hi2': C.HSV_H_HI2,
        's_lo':  C.HSV_S_LO,  's_hi':  C.HSV_S_HI,
        'v_lo':  C.HSV_V_LO,  'v_hi':  C.HSV_V_HI,
    }

    #  Trackers 
    left_tracker  = HandTracker()
    right_tracker = HandTracker()
    menu_cursor   = CursorTracker()  # cursor menu
    p1_cursor     = CursorTracker()  # P1 cursor 
    p2_cursor     = CursorTracker()  # P2 cursor 

    #  Game state 
    game_state = GameState()

    #  State machine 
    state = "MENU"
    menu_buttons  = ui.make_menu_buttons(assets)
    help_buttons  = ui.make_help_buttons(assets)
    pause_button  = ui.make_pause_button(assets)
    paused_buttons = ui.make_paused_buttons(assets)
    gameover_buttons = ui.make_gameover_buttons(assets)

    show_pip = False       # picture-in-picture mask toggle (M key)

    # Timing
    prev_time = time.perf_counter()

    # Canvas (reused every frame)
    canvas = np.zeros((C.WIN_H, C.WIN_W, 3), dtype=np.uint8)

    print("Starting Pong Citra Video ...")

    # Main loop
    while state != "EXIT":
        #  Timing 
        now = time.perf_counter()
        dt = now - prev_time
        prev_time = now
        dt = min(dt, 0.05) 

        #  Read camera 
        ret, raw_frame = cap.read()
        if not ret:
            raw_frame = np.zeros((C.CAM_H, C.CAM_W, 3), dtype=np.uint8)

        #  Vision pipeline 
        mirrored, mask_small, left_blob, right_blob, full_blob = process_frame(raw_frame, hsv_params)

        # Cursor for menu
        mnx, mny = menu_cursor.update(full_blob)
        cursor_sx = int(mnx * C.WIN_W)
        cursor_sy = int(mny * C.WIN_H)

        #  Key input 
        key = cv2.waitKey(1) & 0xFF

        # Global toggles
        if key == ord('m') or key == ord('M'):
            show_pip = not show_pip
        if key == ord('p') or key == ord('P') or key == 32:
            if state == "PLAYING":
                state = "PAUSED"
                for pb in paused_buttons:
                    pb.dwell = 0.0
            elif state == "PAUSED":
                state = "PLAYING"
                pause_button.dwell = 0.0

        #  State: CALIBRATE 
        if state == "CALIBRATE":
            canvas[:] = 0
            ui.draw_calibration_screen(canvas, mirrored)
            if key == ord('c') or key == ord('C'):
                hsv_params = calibrate_from_roi(mirrored)
                print(f"Calibrated HSV: {hsv_params}")
                state = "MENU"
            elif key == 27:  # ESC
                state = "MENU"

        #  State: MENU 
        elif state == "MENU":
            # Calibrate shortcut
            if key == ord('c') or key == ord('C'):
                state = "CALIBRATE"
                continue

            for btn in menu_buttons:
                if btn.update(cursor_sx, cursor_sy, dt):
                    if btn.name == "start":
                        game_state.new_match()
                        state = "PLAYING"
                    elif btn.name == "help":
                        state = "HELP"
                        for hb in help_buttons:
                            hb.dwell = 0.0
                    elif btn.name == "exit":
                        state = "EXIT"

            canvas[:] = 0
            ui.draw_menu_screen(canvas, assets, menu_buttons, cursor_sx, cursor_sy)

        #  State: HELP 
        elif state == "HELP":
            for btn in help_buttons:
                if btn.update(cursor_sx, cursor_sy, dt):
                    if btn.name == "close":
                        state = "MENU"
                        for mb in menu_buttons:
                            mb.dwell = 0.0

            canvas[:] = 0
            ui.draw_menu_screen(canvas, assets, menu_buttons, cursor_sx, cursor_sy)
            ui.draw_help_popup(canvas, assets, help_buttons, cursor_sx, cursor_sy)

        #  State: PLAYING 
        elif state == "PLAYING":
            # Update paddle positions from hand trackers
            left_y  = left_tracker.update(left_blob, slice(None))
            right_y = right_tracker.update(right_blob, slice(None))
            game_state.p1_paddle.set_y(left_y)
            game_state.p2_paddle.set_y(right_y)

            # 2 cursors during match
            c1_nx, c1_ny = p1_cursor.update(left_blob)
            c2_nx, c2_ny = p2_cursor.update(right_blob)
            c1_sx = int(c1_nx * C.WIN_W)
            c1_sy = int(c1_ny * C.WIN_H)
            c2_sx = int(c2_nx * C.WIN_W)
            c2_sy = int(c2_ny * C.WIN_H)

            match_cursors = []
            if p1_cursor.active:
                match_cursors.append((c1_sx, c1_sy, "1", True))
            if p2_cursor.active:
                match_cursors.append((c2_sx, c2_sy, "2", True))

            # Pause button check
            pause_coords = [(cx, cy) for cx, cy, _, _ in match_cursors if cy < C.WIN_H * 0.35]
            if pause_coords and pause_button.update(pause_coords, dt):
                state = "PAUSED"
                for pb in paused_buttons:
                    pb.dwell = 0.0

            # Physics
            game_state.update(C.FIXED_DT)

            # Check win
            if game_state.winner is not None:
                state = "GAME_OVER"
                for gb in gameover_buttons:
                    gb.dwell = 0.0

            canvas[:] = 0
            ui.draw_playing_screen(canvas, assets, game_state, pause_button,
                                    left_tracker.lost, right_tracker.lost,
                                    match_cursors)

        #  State: PAUSED 
        elif state == "PAUSED":
            for btn in paused_buttons:
                if btn.update(cursor_sx, cursor_sy, dt):
                    if btn.name == "continue":
                        state = "PLAYING"
                        pause_button.dwell = 0.0
                    elif btn.name == "exit":
                        state = "MENU"
                        for mb in menu_buttons:
                            mb.dwell = 0.0

            canvas[:] = 0
            ui.draw_playing_screen(canvas, assets, game_state, pause_button,
                                    left_tracker.lost, right_tracker.lost,
                                    None)

            canvas[:] = (canvas.astype(np.float32) * 0.4).astype(np.uint8)
            ui.draw_paused_overlay(canvas, assets, paused_buttons, cursor_sx, cursor_sy)

        #  State: GAME_OVER 
        elif state == "GAME_OVER":
            for btn in gameover_buttons:
                if btn.update(cursor_sx, cursor_sy, dt):
                    if btn.name == "continue":
                        game_state.new_match()
                        state = "PLAYING"
                    elif btn.name == "exit":
                        state = "MENU"
                        for mb in menu_buttons:
                            mb.dwell = 0.0

            canvas[:] = 0
            ui.draw_playing_screen(canvas, assets, game_state, pause_button,
                                    left_tracker.lost, right_tracker.lost,
                                    None)
            canvas[:] = (canvas.astype(np.float32) * 0.4).astype(np.uint8)
            ui.draw_gameover_overlay(canvas, assets, game_state.winner,
                                     gameover_buttons, cursor_sx, cursor_sy)

        #  PiP mask preview
        if show_pip and state != "CALIBRATE":
            ui.draw_pip_mask(canvas, mask_small)

        # Display
        cv2.imshow(C.WIN_TITLE, canvas)

        # Quit
        if key == 27 and state == "MENU":
            state = "EXIT"

    # Cleanup 
    cap.release()
    cv2.destroyAllWindows()
    print("Pong Citra Video exited.")


if __name__ == "__main__":
    main()
