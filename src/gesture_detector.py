"""
gesture_detector.py — Geometric gesture recognition with debounce.

All detection is purely rule-based: distances and angles between MediaPipe
hand landmarks are compared against thresholds — no trained ML model required.

Gestures detected
─────────────────
  swipe_right   hand wrist moves left→right across ≥15 % of frame width
                in under SWIPE_WINDOW_S seconds
  swipe_left    hand wrist moves right→left (mirror of above)
  pinch         Euclidean distance between THUMB_TIP and INDEX_TIP < threshold
                (threshold is normalised relative to palm size)
  open_palm     all 4 finger tips above their respective MCP knuckles AND
                wrist position stable for PALM_HOLD_S seconds
  fist          all 4 finger tips below their respective PIP joints
  thumbs_up     thumb tip above thumb MCP, all other finger tips below
                their respective PIP joints, and thumb is pointing up
  thumbs_down   mirror of thumbs_up but thumb tip is below wrist

Debounce / cooldown
───────────────────
  A gesture is only fired if ≥ COOLDOWN_S seconds have elapsed since the
  last time *any* gesture was fired (global cooldown).  This prevents a
  single held gesture from firing repeatedly across consecutive frames.
"""

import time
import math
from typing import Optional

# ── Landmark index constants (mirrors hand_tracker.py for readability) ────────
WRIST        = 0
THUMB_CMC    = 1;  THUMB_MCP   = 2;  THUMB_IP    = 3;  THUMB_TIP   = 4
INDEX_MCP    = 5;  INDEX_PIP   = 6;  INDEX_DIP   = 7;  INDEX_TIP   = 8
MIDDLE_MCP   = 9;  MIDDLE_PIP  = 10; MIDDLE_DIP  = 11; MIDDLE_TIP  = 12
RING_MCP     = 13; RING_PIP    = 14; RING_DIP    = 15; RING_TIP    = 16
PINKY_MCP    = 17; PINKY_PIP   = 18; PINKY_DIP   = 19; PINKY_TIP   = 20

# ── Tunable thresholds ────────────────────────────────────────────────────────
COOLDOWN_S         = 0.8   # Minimum seconds between any two gesture triggers
SWIPE_WINDOW_S     = 0.6   # Time window in which a swipe must complete
SWIPE_MIN_DELTA_X  = 0.15  # Min horizontal travel (fraction of frame width)
PINCH_THRESHOLD    = 0.08  # Pinch distance as fraction of palm diagonal
PALM_HOLD_S        = 0.5   # How long open palm must be held before firing
STATIC_THRESHOLD   = 0.03  # Max wrist movement (norm coords) to be "still"


class GestureDetector:
    """
    Stateful gesture detector that wraps a HandTracker's per-frame output.

    Usage
    -----
        detector = GestureDetector()
        gesture = detector.detect(landmarks, position_history)
        if gesture:
            action_mapper.trigger(gesture)
    """

    def __init__(self) -> None:
        self._last_gesture_time: float = 0.0

        # State for open_palm hold detection
        self._palm_hold_start: Optional[float] = None
        self._palm_fired_this_hold: bool = False

    # ── Public API ────────────────────────────────────────────────────────────

    def detect(
        self,
        landmarks,                        # list of NormalizedLandmark (21 items)
        position_history: list,           # list of (ts, norm_x, norm_y)
    ) -> Optional[str]:
        """
        Analyse landmarks + position history and return a gesture name string,
        or None if no gesture has been confirmed this frame.

        Gesture names (strings returned):
            'swipe_right', 'swipe_left', 'pinch',
            'open_palm', 'fist', 'thumbs_up', 'thumbs_down'
        """
        now = time.monotonic()
        cooldown_ok = (now - self._last_gesture_time) >= COOLDOWN_S

        # ── Static (single-frame) gestures ───────────────────────────────────
        # These are checked in priority order; first match wins.

        if cooldown_ok:
            # 1. Pinch — thumb tip close to index tip
            if self._is_pinch(landmarks):
                return self._fire("pinch", now)

            # 2. Thumbs up / down (checked before fist because thumb is extended)
            if self._is_thumbs_up(landmarks):
                return self._fire("thumbs_up", now)

            if self._is_thumbs_down(landmarks):
                return self._fire("thumbs_down", now)

            # 3. Fist — all fingers curled
            if self._is_fist(landmarks):
                return self._fire("fist", now)

        # ── Open palm hold (stateful, not affected by global cooldown after
        #    hold begins, but respects it for the fire event itself) ──────────
        gesture = self._check_open_palm(landmarks, position_history, now, cooldown_ok)
        if gesture:
            return gesture

        # ── Motion-based gestures (use position history) ─────────────────────
        if cooldown_ok:
            gesture = self._check_swipe(position_history, now)
            if gesture:
                return self._fire(gesture, now)

        return None

    def reset_palm_state(self) -> None:
        """Call this when the hand leaves the frame to reset hold state."""
        self._palm_hold_start = None
        self._palm_fired_this_hold = False

    # ── Static gesture helpers ────────────────────────────────────────────────

    def _is_pinch(self, lm) -> bool:
        """
        Thumb tip (4) to index tip (8) distance < PINCH_THRESHOLD * palm_size.
        Palm size is approximated as the distance from wrist (0) to middle MCP (9),
        giving a scale-invariant threshold that works at any hand distance.
        """
        palm_size = _dist(lm[WRIST], lm[MIDDLE_MCP])
        if palm_size < 1e-6:
            return False
        pinch_dist = _dist(lm[THUMB_TIP], lm[INDEX_TIP])
        # Normalise by palm size to be distance-invariant
        return (pinch_dist / palm_size) < PINCH_THRESHOLD

    def _is_fist(self, lm) -> bool:
        """
        All four finger tips (index, middle, ring, pinky) must be BELOW
        (higher y value in image coords) their respective PIP joints.
        Y increases downward in MediaPipe normalised coords.
        """
        return (
            lm[INDEX_TIP].y  > lm[INDEX_PIP].y  and
            lm[MIDDLE_TIP].y > lm[MIDDLE_PIP].y and
            lm[RING_TIP].y   > lm[RING_PIP].y   and
            lm[PINKY_TIP].y  > lm[PINKY_PIP].y
        )

    def _is_thumbs_up(self, lm) -> bool:
        """
        Thumbs-up: thumb tip is significantly ABOVE (lower y) the thumb MCP,
        AND all four fingers are curled (tips below their PIP joints).
        We also require the thumb tip to be above the wrist to disambiguate
        from a sideways hand.
        """
        thumb_extended_up = (
            lm[THUMB_TIP].y < lm[THUMB_MCP].y - 0.04 and   # tip above MCP
            lm[THUMB_TIP].y < lm[WRIST].y                    # tip above wrist
        )
        fingers_curled = (
            lm[INDEX_TIP].y  > lm[INDEX_PIP].y  and
            lm[MIDDLE_TIP].y > lm[MIDDLE_PIP].y and
            lm[RING_TIP].y   > lm[RING_PIP].y   and
            lm[PINKY_TIP].y  > lm[PINKY_PIP].y
        )
        return thumb_extended_up and fingers_curled

    def _is_thumbs_down(self, lm) -> bool:
        """
        Thumbs-down: thumb tip is significantly BELOW (higher y) the thumb MCP,
        AND all four fingers are curled.
        Thumb tip must also be below the wrist.
        """
        thumb_extended_down = (
            lm[THUMB_TIP].y > lm[THUMB_MCP].y + 0.04 and   # tip below MCP
            lm[THUMB_TIP].y > lm[WRIST].y                    # tip below wrist
        )
        fingers_curled = (
            lm[INDEX_TIP].y  > lm[INDEX_PIP].y  and
            lm[MIDDLE_TIP].y > lm[MIDDLE_PIP].y and
            lm[RING_TIP].y   > lm[RING_PIP].y   and
            lm[PINKY_TIP].y  > lm[PINKY_PIP].y
        )
        return thumb_extended_down and fingers_curled

    def _is_open_palm(self, lm) -> bool:
        """
        Open palm: all four finger tips are ABOVE (lower y) their MCP knuckles.
        We check tips vs MCPs (not PIPs) so the fingers need to be fully extended.
        """
        return (
            lm[INDEX_TIP].y  < lm[INDEX_MCP].y  and
            lm[MIDDLE_TIP].y < lm[MIDDLE_MCP].y and
            lm[RING_TIP].y   < lm[RING_MCP].y   and
            lm[PINKY_TIP].y  < lm[PINKY_MCP].y
        )

    # ── Open-palm hold (stateful) ─────────────────────────────────────────────

    def _check_open_palm(self, lm, history, now: float, cooldown_ok: bool) -> Optional[str]:
        """
        The open-palm gesture requires the hand to be:
          1. In the open-palm shape.
          2. Stationary (wrist hasn't moved more than STATIC_THRESHOLD in the
             last PALM_HOLD_S seconds).
          3. Held for at least PALM_HOLD_S continuous seconds.
        """
        shape_ok = self._is_open_palm(lm)

        if not shape_ok:
            # Reset hold timer if shape breaks
            self._palm_hold_start = None
            self._palm_fired_this_hold = False
            return None

        # Shape is OK — check if hand is stationary using position history
        if not self._is_hand_still(history, now):
            self._palm_hold_start = None
            self._palm_fired_this_hold = False
            return None

        # Hand is open and still — start or continue hold timer
        if self._palm_hold_start is None:
            self._palm_hold_start = now
            return None

        hold_duration = now - self._palm_hold_start

        if hold_duration >= PALM_HOLD_S and not self._palm_fired_this_hold and cooldown_ok:
            self._palm_fired_this_hold = True
            return self._fire("open_palm", now)

        return None

    def _is_hand_still(self, history: list, now: float) -> bool:
        """
        Returns True if the wrist hasn't moved more than STATIC_THRESHOLD
        (in normalised coords) within the last PALM_HOLD_S seconds.
        """
        window = [entry for entry in history if now - entry[0] <= PALM_HOLD_S]
        if len(window) < 2:
            return True  # Not enough history — treat as still

        xs = [e[1] for e in window]
        ys = [e[2] for e in window]
        travel = math.sqrt((max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2)
        return travel < STATIC_THRESHOLD

    # ── Swipe detection (motion-based) ────────────────────────────────────────

    def _check_swipe(self, history: list, now: float) -> Optional[str]:
        """
        A swipe is detected when the wrist travels > SWIPE_MIN_DELTA_X in
        normalised x-coords within the last SWIPE_WINDOW_S seconds.

        MediaPipe's x is mirrored by default (x=0 is right side of image),
        so we un-mirror: real_x = 1 - mp_x. A right-swipe in the real world
        means x increases in image coords (real_x decreases).

        We flip here: a natural right-swipe moves the wrist from left to right
        in front of the camera, which maps to x DECREASING in MediaPipe coords.
        """
        window = [e for e in history if now - e[0] <= SWIPE_WINDOW_S]
        if len(window) < 2:
            return None

        # Use the first and last point in the window for net displacement
        x_start = window[0][1]
        x_end   = window[-1][1]
        delta_x = x_end - x_start  # positive = moved toward larger x

        # In MediaPipe coords (mirrored), moving right → x decreases
        # → we treat a sufficiently negative delta as "swipe right"
        if delta_x < -SWIPE_MIN_DELTA_X:
            return "swipe_right"
        if delta_x > SWIPE_MIN_DELTA_X:
            return "swipe_left"

        return None

    # ── Internal helper ───────────────────────────────────────────────────────

    def _fire(self, gesture: str, now: float) -> str:
        """Record the trigger time and return the gesture name."""
        self._last_gesture_time = now
        return gesture


# ── Utility ───────────────────────────────────────────────────────────────────

def _dist(a, b) -> float:
    """Euclidean distance between two NormalizedLandmark points (x, y only)."""
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
