"""
action_mapper.py — Config-driven gesture-to-keypress mapping.

Reads a mode JSON file (e.g. config/presentation_mode.json) and translates
gesture names into pyautogui keyboard actions.

Supports two action types in the JSON:
  { "type": "key",    "value": "right"           }  → pyautogui.press('right')
  { "type": "hotkey", "value": ["win","shift","s"] }  → pyautogui.hotkey(...)

pyautogui's fail-safe is left ENABLED (FAILSAFE = True, which is the default).
Moving the mouse to a screen corner will abort the script — keep this as a
safety net while testing gesture-to-keypress mappings.
"""

import json
import os
from typing import Optional

import pyautogui

# pyautogui FAILSAFE is True by default — do NOT set it to False.
# Moving the mouse to a corner will abort the script, which is useful
# safety behaviour when testing in front of an audience.
pyautogui.PAUSE = 0.0   # Remove the built-in inter-call delay for low latency


class ActionMapper:
    """
    Loads a gesture mapping config and executes the mapped keypress(es)
    when trigger() is called.

    Parameters
    ----------
    config_path : str
        Path to a mode JSON file (presentation_mode.json or media_mode.json).
    """

    def __init__(self, config_path: str) -> None:
        self._config_path = config_path
        self._gesture_map: dict = {}
        self._display_labels: dict = {}
        self._mode_name: str = "Unknown"
        self.load_config(config_path)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_config(self, config_path: str) -> None:
        """Load (or reload) a gesture mapping from a JSON config file."""
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        self._config_path   = config_path
        self._gesture_map   = cfg.get("gesture_map", {})
        self._display_labels = cfg.get("display_labels", {})
        self._mode_name     = cfg.get("mode_name", os.path.basename(config_path))

    def trigger(self, gesture: str) -> bool:
        """
        Execute the keypress(es) mapped to `gesture`.

        Returns True if an action was taken, False if the gesture has no mapping.
        """
        mapping = self._gesture_map.get(gesture)
        if mapping is None:
            return False

        action_type = mapping.get("type")
        value       = mapping.get("value")

        if action_type == "key":
            # Single key press — works for both regular keys and media keys
            pyautogui.press(value)

        elif action_type == "hotkey":
            # Multiple keys pressed simultaneously (e.g. Win+Shift+S)
            if isinstance(value, list):
                pyautogui.hotkey(*value)
            else:
                pyautogui.press(value)

        return True

    def get_label(self, gesture: str) -> str:
        """Return the human-readable display label for a gesture."""
        return self._display_labels.get(gesture, gesture.upper().replace("_", " "))

    @property
    def mode_name(self) -> str:
        return self._mode_name

    @property
    def config_path(self) -> str:
        return self._config_path

    def list_mappings(self) -> list[tuple[str, str, str]]:
        """
        Return all current mappings as a list of
        (gesture_name, display_label, key_value) tuples — useful for the README
        and for printing a summary at startup.
        """
        result = []
        for gesture, mapping in self._gesture_map.items():
            label = self._display_labels.get(gesture, gesture)
            key   = mapping.get("value", "?")
            if isinstance(key, list):
                key = "+".join(key)
            result.append((gesture, label, key))
        return result
