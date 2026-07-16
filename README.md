# GestureControl — Hand Gesture Presentation & Media Controller

Control PowerPoint, Google Slides, Spotify, YouTube, VLC — and anything else
with keyboard shortcuts — using only your hand in front of a webcam.  No mouse,
no keyboard needed.

---

## Table of Contents

1. [Requirements](#requirements)
2. [Setup](#setup)
3. [Running the App](#running-the-app)
4. [Gesture Mappings](#gesture-mappings)
5. [Runtime Controls](#runtime-controls)
6. [Customising Key Bindings](#customising-key-bindings)
7. [Troubleshooting](#troubleshooting)
8. [Architecture Notes](#architecture-notes)

---

## Requirements

| Item | Version |
|---|---|
| Python | **3.9 – 3.12** (3.13+ is **not** supported — MediaPipe incompatible) |
| OS | Windows 10/11 (primary), macOS/Linux (mostly works, not tested) |
| Webcam | Any USB or built-in camera |

---

## Setup

### 1. Check your Python installation

```cmd
py -0
```

You need a `3.9`, `3.10`, `3.11`, or `3.12` entry.  
If only `3.13` or `3.14` are shown, install Python 3.11 from
<https://www.python.org/downloads/release/python-3119/> (Windows installer,
"Add to PATH" checked).

### 2. Clone / open the project

Make sure the project is **not** inside a OneDrive-synced folder.  
Recommended path: `C:\Projects\gesture-control`

OneDrive can lock files mid-write and cause permission errors during `pip install`.

### 3. Create a virtual environment

```cmd
py -3.11 -m venv venv
```

### 4. Activate the virtual environment

```cmd
venv\Scripts\activate
```

Your prompt will show `(venv)` when active.

### 5. Install dependencies

```cmd
pip install -r requirements.txt
```

Pinned versions used:

```
mediapipe==0.10.21
opencv-python==4.10.0.84
numpy==1.26.4
pyautogui==0.9.54
pynput==1.7.7
```

If any of these are unavailable at your install time, substitute the closest
available patch version (e.g. `mediapipe==0.10.22`).

### 6. Verify the installation

```cmd
python -c "import mediapipe; import cv2; import pyautogui; import numpy; print('All imports OK')"
```

Expected output: `All imports OK`

---

## Running the App

```cmd
# From the project root, with venv activated:

python src/main.py                    # Presentation mode (default)
python src/main.py --mode media       # Media mode
python src/main.py --mode presentation --camera 1   # second webcam
```

A window will open showing your webcam feed with the hand skeleton drawn over it.

---

## Gesture Mappings

### Presentation Mode (default)

| Gesture | Action | Key sent |
|---|---|---|
| Swipe right | Next slide | `→` Right arrow |
| Swipe left | Previous slide | `←` Left arrow |
| Pinch | Start slideshow | `F5` |
| Open palm (held) | End slideshow | `Esc` |
| Thumbs up | Volume up | `VolumeUp` |
| Thumbs down | Volume down | `VolumeDown` |
| Fist | Screenshot | `Win+Shift+S` |

### Media Mode

| Gesture | Action | Key sent |
|---|---|---|
| Swipe right | Next track / seek forward | `NextTrack` |
| Swipe left | Previous track / seek back | `PrevTrack` |
| Pinch | Play / Pause | `PlayPause` |
| Open palm (held) | Mute | `M` |
| Thumbs up | Volume up | `VolumeUp` |
| Thumbs down | Volume down | `VolumeDown` |
| Fist | Screenshot | `Win+Shift+S` |

---

## Runtime Controls

| Key | Action |
|---|---|
| `h` | Toggle debug overlay (landmarks + status text) |
| `m` | Cycle between Presentation and Media modes |
| `q` or `Esc` | Quit |

---

## Customising Key Bindings

Edit the JSON files in `config/` — no code changes needed.

Each gesture entry has:

```json
"swipe_right": { "type": "key",    "value": "right" }
"fist":        { "type": "hotkey", "value": ["win", "shift", "s"] }
```

- `"type": "key"` — a single key name from [pyautogui's key list](https://pyautogui.readthedocs.io/en/latest/keyboard.html#keyboard-keys)
- `"type": "hotkey"` — list of key names pressed simultaneously

You can also add a `display_labels` entry to change the on-screen flash text
for any gesture.

---

## Troubleshooting

### `DLL load failed` on Windows when importing mediapipe or opencv

Install the Microsoft Visual C++ Redistributable (both x64 and x86):

- x64: <https://aka.ms/vs/17/release/vc_redist.x64.exe>
- x86: <https://aka.ms/vs/17/release/vc_redist.x86.exe>

Restart your PC, re-activate the venv, and retry the import verification.

### `ModuleNotFoundError: No module named 'mediapipe'`

You're not in the virtual environment. Run:

```cmd
venv\Scripts\activate
```

### Camera not opening / black screen

Try a different camera index:

```cmd
python src/main.py --camera 1
```

Some laptops enumerate the IR camera as index 0 and the visible-light camera as 1.

### Gestures fire too easily / too late

Tune the thresholds at the top of `src/gesture_detector.py`:

| Constant | Default | Effect |
|---|---|---|
| `COOLDOWN_S` | `0.8` | Minimum gap between any two gestures |
| `SWIPE_MIN_DELTA_X` | `0.15` | How far you must swipe (15 % of frame width) |
| `SWIPE_WINDOW_S` | `0.6` | Time window in which a swipe must complete |
| `PINCH_THRESHOLD` | `0.08` | How close thumb+index must be (relative to palm size) |
| `PALM_HOLD_S` | `0.5` | How long to hold open palm before it fires |

### pyautogui FailSafeException — script aborted

You moved the mouse to a screen corner.  This is the `pyautogui` built-in
fail-safe and is intentionally **kept enabled** as a safety net during testing.
Just re-run the script.

### OneDrive sync conflicts during install

Move the project to a non-OneDrive path such as `C:\Projects\gesture-control`
and re-run the setup steps.

---

## Architecture Notes

```
gesture-control/
├── src/
│   ├── hand_tracker.py     # MediaPipe wrapper + rolling wrist-position history
│   ├── gesture_detector.py # Rule-based geometric gesture recognition + debounce
│   ├── action_mapper.py    # Config-driven gesture → keypress dispatcher
│   └── main.py             # Webcam loop, overlay UI, mode switching
├── config/
│   ├── presentation_mode.json
│   └── media_mode.json
├── requirements.txt
├── .gitignore
└── README.md
```

**Gesture detection approach:** purely geometric — distances and angles between
the 21 MediaPipe hand landmarks are compared against tunable thresholds.
No ML classifier is required, which keeps the code transparent and easy to tune.
A learned classifier (e.g. a small MLP on landmark coordinates) is a natural
future upgrade if rule-based detection proves unreliable for a particular gesture.

**Latency:** MediaPipe runs on CPU in real time at 30 fps on a modern laptop.
The gesture-to-keypress path is entirely in-process (no network calls), so
end-to-end latency is well under 100 ms under normal conditions.

**Key simulation:** `pyautogui` simulates OS-level keyboard events, so it works
with any application that accepts keyboard shortcuts — no app-specific API
integration needed.
