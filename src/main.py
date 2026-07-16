"""
main.py — Webcam loop, overlay UI, mode switching.

Usage
-----
    # Activate the venv first, then:
    python src/main.py                         # defaults to Presentation mode
    python src/main.py --mode media            # start in Media mode
    python src/main.py --mode presentation     # start in Presentation mode

Runtime keyboard shortcuts (in the OpenCV window)
──────────────────────────────────────────────────
    h          Toggle debug overlay (landmarks + status text) on/off
    m          Switch between Presentation and Media modes
    q  / Esc   Quit

The window title shows the current mode. When an action fires, a brief
on-screen flash ("→ NEXT SLIDE") appears in the top-left corner for
FLASH_DURATION_S seconds.
"""

import argparse
import os
import sys
import time

import cv2
import numpy as np

# Ensure the src/ directory is on the path when run from the project root
sys.path.insert(0, os.path.dirname(__file__))

from hand_tracker import HandTracker
from gesture_detector import GestureDetector
from action_mapper import ActionMapper

# ── Config paths ──────────────────────────────────────────────────────────────
_BASE = os.path.join(os.path.dirname(__file__), "..", "config")
MODE_CONFIGS = {
    "presentation": os.path.normpath(os.path.join(_BASE, "presentation_mode.json")),
    "media":        os.path.normpath(os.path.join(_BASE, "media_mode.json")),
}
MODE_ORDER = ["presentation", "media"]  # cycle order for the 'm' key

# ── Display constants ─────────────────────────────────────────────────────────
FLASH_DURATION_S  = 1.2   # How long the action label flashes on screen
OVERLAY_ALPHA     = 0.55  # Translucency of the text background strip
FONT              = cv2.FONT_HERSHEY_SIMPLEX
COLOR_GREEN       = (0, 255, 120)
COLOR_YELLOW      = (0, 220, 255)
COLOR_WHITE       = (255, 255, 255)
COLOR_DARK        = (20,  20,  20)
COLOR_RED         = (60,  60, 220)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GestureControl — control presentations & media with hand gestures"
    )
    parser.add_argument(
        "--mode",
        choices=["presentation", "media"],
        default="presentation",
        help="Starting gesture-map mode (default: presentation)",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Webcam index (default: 0)",
    )
    return parser.parse_args()


def draw_text_with_bg(
    frame: np.ndarray,
    text: str,
    origin: tuple[int, int],
    font_scale: float,
    color: tuple,
    thickness: int = 2,
    bg_color: tuple = COLOR_DARK,
    padding: int = 8,
) -> None:
    """Draw text with a filled rectangle background for readability."""
    (tw, th), baseline = cv2.getTextSize(text, FONT, font_scale, thickness)
    x, y = origin
    # Background rectangle
    cv2.rectangle(
        frame,
        (x - padding, y - th - padding),
        (x + tw + padding, y + baseline + padding),
        bg_color,
        cv2.FILLED,
    )
    cv2.putText(frame, text, (x, y), FONT, font_scale, color, thickness, cv2.LINE_AA)


def main() -> None:
    args = parse_args()

    current_mode_key = args.mode
    tracker  = HandTracker()
    detector = GestureDetector()
    mapper   = ActionMapper(MODE_CONFIGS[current_mode_key])

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera index {args.camera}.")
        print("  Try a different --camera index (e.g. --camera 1).")
        sys.exit(1)

    # Request a reasonable capture resolution for low latency
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    show_overlay    = True    # toggled by 'h'
    flash_text      = ""      # current action label to flash
    flash_until     = 0.0     # monotonic time until flash expires
    current_gesture = ""      # gesture label shown in the HUD

    print(f"\n[GestureControl] Starting in {mapper.mode_name} mode.")
    print("  Press 'h' to toggle overlay, 'm' to switch mode, 'q'/Esc to quit.\n")
    _print_mappings(mapper)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Frame grab failed — retrying.")
            time.sleep(0.05)
            continue

        # Mirror the frame so the user sees their hand naturally
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        now  = time.monotonic()

        # ── Hand tracking ──────────────────────────────────────────────────
        landmarks, hand_proto = tracker.process_frame(frame)

        if landmarks is None:
            detector.reset_palm_state()
            current_gesture = ""
        else:
            # ── Gesture detection ──────────────────────────────────────────
            gesture = detector.detect(landmarks, tracker.get_position_history())

            if gesture:
                current_gesture = mapper.get_label(gesture)
                action_taken = mapper.trigger(gesture)
                if action_taken:
                    flash_text  = current_gesture
                    flash_until = now + FLASH_DURATION_S

            # ── Draw landmarks overlay ─────────────────────────────────────
            if show_overlay and hand_proto is not None:
                tracker.draw_landmarks(frame, hand_proto)

        # ── HUD overlay ────────────────────────────────────────────────────
        if show_overlay:
            # Mode badge — top-right corner
            mode_label = f"Mode: {mapper.mode_name}"
            draw_text_with_bg(
                frame, mode_label,
                (w - _text_width(mode_label, 0.55) - 12, 28),
                font_scale=0.55, color=COLOR_YELLOW, thickness=1,
            )

            # Current gesture — bottom-left
            if current_gesture:
                draw_text_with_bg(
                    frame, f"Gesture: {current_gesture}",
                    (10, h - 14),
                    font_scale=0.55, color=COLOR_GREEN, thickness=1,
                )

        # ── Action flash ───────────────────────────────────────────────────
        if now < flash_until:
            # Pulsing effect: brighter when fresh, fading as it expires
            alpha   = min(1.0, (flash_until - now) / FLASH_DURATION_S)
            overlay = frame.copy()
            draw_text_with_bg(
                overlay, flash_text,
                (10, 50),
                font_scale=1.1, color=COLOR_WHITE, thickness=2,
                bg_color=(0, int(160 * alpha), 0),
                padding=12,
            )
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha * 0.4, 0, frame)

        # ── No-hand indicator ──────────────────────────────────────────────
        if show_overlay and landmarks is None:
            draw_text_with_bg(
                frame, "No hand detected",
                (10, 28),
                font_scale=0.55, color=COLOR_RED, thickness=1,
            )

        # ── Show frame ────────────────────────────────────────────────────
        win_title = f"GestureControl — {mapper.mode_name} Mode"
        cv2.imshow(win_title, frame)

        # ── Key handling ──────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        if key in (ord('q'), 27):          # q or Esc → quit
            break

        elif key == ord('h'):              # h → toggle overlay
            show_overlay = not show_overlay
            print(f"[INFO] Overlay {'ON' if show_overlay else 'OFF'}")

        elif key == ord('m'):              # m → cycle mode
            idx = MODE_ORDER.index(current_mode_key)
            current_mode_key = MODE_ORDER[(idx + 1) % len(MODE_ORDER)]
            mapper.load_config(MODE_CONFIGS[current_mode_key])
            tracker.clear_history()
            detector.reset_palm_state()
            current_gesture = ""
            flash_text  = f"Mode: {mapper.mode_name}"
            flash_until = now + FLASH_DURATION_S
            print(f"\n[INFO] Switched to {mapper.mode_name} mode.")
            _print_mappings(mapper)

    # ── Cleanup ────────────────────────────────────────────────────────────
    cap.release()
    tracker.release()
    cv2.destroyAllWindows()
    print("\n[GestureControl] Exited cleanly.")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _text_width(text: str, scale: float) -> int:
    (tw, _), _ = cv2.getTextSize(text, FONT, scale, 1)
    return tw


def _print_mappings(mapper: ActionMapper) -> None:
    print(f"  {'Gesture':<16} {'Action':<24} {'Key'}")
    print(f"  {'-'*16} {'-'*24} {'-'*20}")
    for gesture, label, key in mapper.list_mappings():
        print(f"  {gesture:<16} {label:<24} {key}")
    print()


if __name__ == "__main__":
    main()
