"""
hand_tracker.py — MediaPipe wrapper + landmark history tracking.

Wraps MediaPipe Hands to:
  - Detect a single hand per frame from a webcam feed.
  - Return the 21 normalized landmarks for the detected hand.
  - Maintain a rolling history of wrist positions so gesture_detector.py
    can compute motion-based gestures (swipes) in addition to static
    pose-based ones (pinch, fist, etc.).
"""

import time
from collections import deque
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np

# ── MediaPipe hand-landmark indices (for readable reference elsewhere) ────────
WRIST        = 0
THUMB_CMC    = 1;  THUMB_MCP   = 2;  THUMB_IP    = 3;  THUMB_TIP   = 4
INDEX_MCP    = 5;  INDEX_PIP   = 6;  INDEX_DIP   = 7;  INDEX_TIP   = 8
MIDDLE_MCP   = 9;  MIDDLE_PIP  = 10; MIDDLE_DIP  = 11; MIDDLE_TIP  = 12
RING_MCP     = 13; RING_PIP    = 14; RING_DIP    = 15; RING_TIP    = 16
PINKY_MCP    = 17; PINKY_PIP   = 18; PINKY_DIP   = 19; PINKY_TIP   = 20


class HandTracker:
    """
    Wraps MediaPipe Hands for single-hand tracking with landmark history.

    Parameters
    ----------
    history_seconds : float
        How many seconds of wrist-position history to retain for motion
        gesture detection (default 1.0 s is enough to catch a swipe).
    min_detection_confidence : float
        MediaPipe detection confidence threshold (0–1).
    min_tracking_confidence : float
        MediaPipe tracking confidence threshold (0–1).
    """

    def __init__(
        self,
        history_seconds: float = 1.0,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        self._mp_hands = mp.solutions.hands
        self._mp_draw  = mp.solutions.drawing_utils
        self._mp_styles = mp.solutions.drawing_styles

        # Single-hand mode for lower latency
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        # Rolling history: deque of (timestamp, wrist_x_norm, wrist_y_norm)
        # Normalised coords are in [0, 1] (MediaPipe convention).
        self._history_seconds = history_seconds
        self._position_history: deque = deque()

    # ── Public API ──────────────────────────────────────────────────────────

    def process_frame(
        self, frame: np.ndarray
    ) -> tuple[Optional[list], Optional[object]]:
        """
        Run MediaPipe on one BGR frame.

        Returns
        -------
        landmarks : list of mp.framework.formats.landmark_pb2.NormalizedLandmark
            21 landmarks for the detected hand, or None if no hand found.
        hand_landmarks_proto : MediaPipe result object (for drawing), or None.
        """
        # MediaPipe expects RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self._hands.process(rgb)
        rgb.flags.writeable = True

        if not results.multi_hand_landmarks:
            return None, None

        # Take the first (and only, since max_num_hands=1) detected hand
        hand_lm = results.multi_hand_landmarks[0]
        landmarks = hand_lm.landmark  # list of NormalizedLandmark objects

        # Record wrist position in history
        now = time.monotonic()
        wrist = landmarks[WRIST]
        self._position_history.append((now, wrist.x, wrist.y))
        self._prune_history(now)

        return landmarks, hand_lm

    def draw_landmarks(self, frame: np.ndarray, hand_landmarks_proto) -> None:
        """Draw the hand skeleton overlay on `frame` in-place."""
        self._mp_draw.draw_landmarks(
            frame,
            hand_landmarks_proto,
            self._mp_hands.HAND_CONNECTIONS,
            self._mp_styles.get_default_hand_landmarks_style(),
            self._mp_styles.get_default_hand_connections_style(),
        )

    def get_position_history(self) -> list[tuple[float, float, float]]:
        """
        Return the recent wrist-position history as a list of
        (timestamp, norm_x, norm_y) tuples, oldest first.
        """
        return list(self._position_history)

    def clear_history(self) -> None:
        """Wipe the position history (e.g. between mode switches)."""
        self._position_history.clear()

    def release(self) -> None:
        """Clean up MediaPipe resources."""
        self._hands.close()

    # ── Internal helpers ────────────────────────────────────────────────────

    def _prune_history(self, now: float) -> None:
        """Remove entries older than history_seconds from the left of the deque."""
        cutoff = now - self._history_seconds
        while self._position_history and self._position_history[0][0] < cutoff:
            self._position_history.popleft()
