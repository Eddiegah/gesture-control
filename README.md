<div align="center">

<img src="https://img.shields.io/badge/Python-3.9--3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9-3.12"/>
<img src="https://img.shields.io/badge/MediaPipe-0.10.21-00897B?style=for-the-badge&logo=google&logoColor=white" alt="MediaPipe"/>
<img src="https://img.shields.io/badge/OpenCV-4.10.0-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV"/>
<img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"/>
<img src="https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge" alt="MIT License"/>
<img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge" alt="Active"/>

<br/><br/>

# 🖐️ GestureControl

### Real-time hand gesture control for presentations & media — no mouse, no keyboard.

Point, swipe, pinch. That's it.

<br/>

> **Control PowerPoint · Google Slides · Spotify · YouTube · VLC**  
> via your webcam using 7 hand gestures, entirely rule-based — no ML training required.

<br/>

---

</div>

## ✨ Features

- 🎥 **Real-time webcam detection** at 30 fps using MediaPipe Hands
- 🤌 **7 gestures** — swipe left/right, pinch, open palm hold, fist, thumbs up/down
- ⚡ **Sub-100ms latency** from gesture to keypress
- 🗂️ **Two built-in modes** — Presentation and Media, switchable at runtime
- 🔧 **Fully configurable** — remap any gesture to any key via JSON, no code edits
- 🖼️ **Live overlay HUD** — landmarks, gesture name, and action flash on screen
- 🔒 **pyautogui fail-safe enabled** — move mouse to screen corner to abort instantly
- 💻 **Windows-first**, works via OS-level key simulation with any app

<br/>

---

## 📽️ Demo

> **Coming soon** — record a short screen capture and drop it here.
>
> To add your own:
> 1. Record a screen capture using `Win + G` (Xbox Game Bar) or OBS
> 2. Upload the `.gif` or `.mp4` to this repo (drag into a GitHub Issue or use Releases)
> 3. Replace this block with:
>
> ```md
> ![GestureControl Demo](assets/demo.gif)
> ```
>
> Or for a hosted video:
>
> ```md
> [![Watch the demo](https://img.youtube.com/vi/YOUR_VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)
> ```

<br/>

---

## 🗂️ Project Structure

```
gesture-control/
│
├── src/
│   ├── hand_tracker.py       # MediaPipe wrapper + rolling wrist-position history
│   ├── gesture_detector.py   # Geometric rule-based gesture recognition + debounce
│   ├── action_mapper.py      # Config-driven gesture → keypress dispatcher
│   └── main.py               # Webcam loop, HUD overlay, mode switching
│
├── config/
│   ├── presentation_mode.json   # Slide navigation key mappings
│   └── media_mode.json          # Music / video playback key mappings
│
├── requirements.txt
├── .gitignore
└── README.md
```

<br/>

---

## ⚙️ Setup

### Prerequisites

| Requirement | Detail |
|---|---|
| **Python** | `3.9 – 3.12` only — MediaPipe does **not** support 3.13+ |
| **OS** | Windows 10 / 11 (primary). macOS/Linux mostly works. |
| **Webcam** | Any built-in or USB camera |
| **Git** | To clone the repo |

> ⚠️ **OneDrive warning** — do **not** place this project inside a OneDrive-synced folder.
> OneDrive can lock files mid-write during `pip install` and cause permission errors.
> Use a path like `C:\Projects\gesture-control` instead.

---

### Step 1 — Check your Python version

```cmd
py -0
```

You need a `3.9`, `3.10`, `3.11`, or `3.12` entry in the list.
If only `3.13` or `3.14` appear, install Python 3.11 from:
👉 https://www.python.org/downloads/release/python-3119/
_(Windows installer — check "Add to PATH")_

---

### Step 2 — Clone the repo

```cmd
git clone https://github.com/Eddiegah/gesture-control.git
cd gesture-control
```

---

### Step 3 — Create a virtual environment

```cmd
py -3.11 -m venv venv
```

---

### Step 4 — Activate the virtual environment

```cmd
venv\Scripts\activate
```

Your terminal prompt will show `(venv)` when active.

---

### Step 5 — Install dependencies

```cmd
pip install -r requirements.txt
```

Pinned versions:

```
mediapipe==0.10.21
opencv-python==4.10.0.84
numpy==1.26.4
pyautogui==0.9.54
pynput==1.7.7
```

---

### Step 6 — Verify the installation

```cmd
python -c "import mediapipe; import cv2; import pyautogui; import numpy; print('All imports OK')"
```

**Expected output:** `All imports OK`

If you see a DLL error instead, jump to [Troubleshooting](#-troubleshooting).

<br/>

---

## 🚀 Running the App

```cmd
# Activate venv first (if not already active):
venv\Scripts\activate

# Start in Presentation mode (default):
python src/main.py

# Start in Media mode:
python src/main.py --mode media

# Use a different webcam (e.g. if index 0 is an IR camera):
python src/main.py --camera 1
```

A window will open showing your webcam feed with the hand skeleton overlaid.

<br/>

---

## 🤌 Gesture Reference

### 🎞️ Presentation Mode

| Gesture | How to perform it | Action | Key sent |
|---|---|---|---|
| **Swipe Right** | Move hand left → right briskly | Next slide | `→` Right arrow |
| **Swipe Left** | Move hand right → left briskly | Previous slide | `←` Left arrow |
| **Pinch** | Bring thumb tip + index tip together | Start slideshow | `F5` |
| **Open Palm** | Spread all fingers, hold still ~0.5s | End slideshow | `Esc` |
| **Thumbs Up** | Thumb up, other fingers curled | Volume up | `VolumeUp` |
| **Thumbs Down** | Thumb down, other fingers curled | Volume down | `VolumeDown` |
| **Fist** | Curl all fingers closed | Screenshot | `Win + Shift + S` |

---

### 🎵 Media Mode

| Gesture | How to perform it | Action | Key sent |
|---|---|---|---|
| **Swipe Right** | Move hand left → right briskly | Next track | `NextTrack` |
| **Swipe Left** | Move hand right → left briskly | Previous track | `PrevTrack` |
| **Pinch** | Bring thumb tip + index tip together | Play / Pause | `PlayPause` |
| **Open Palm** | Spread all fingers, hold still ~0.5s | Mute | `M` |
| **Thumbs Up** | Thumb up, other fingers curled | Volume up | `VolumeUp` |
| **Thumbs Down** | Thumb down, other fingers curled | Volume down | `VolumeDown` |
| **Fist** | Curl all fingers closed | Screenshot | `Win + Shift + S` |

<br/>

---

## ⌨️ Runtime Controls

These keys work while the GestureControl window is in focus:

| Key | Action |
|---|---|
| `H` | Toggle landmark + status overlay on / off |
| `M` | Cycle between Presentation and Media modes |
| `Q` or `Esc` | Quit |

<br/>

---

## 🔧 Customising Key Bindings

Edit the JSON files in `config/` — **no code changes needed**.

```json
{
  "gesture_map": {
    "swipe_right": { "type": "key",    "value": "right"              },
    "fist":        { "type": "hotkey", "value": ["win", "shift", "s"] }
  },
  "display_labels": {
    "swipe_right": "→ NEXT SLIDE",
    "fist":        "📸 SCREENSHOT"
  }
}
```

**Action types:**

| Type | Value format | Example |
|---|---|---|
| `"key"` | Single key name string | `"f5"`, `"space"`, `"volumeup"` |
| `"hotkey"` | Array of key names | `["ctrl", "shift", "p"]` |

Full list of valid key names: [pyautogui keyboard keys](https://pyautogui.readthedocs.io/en/latest/keyboard.html#keyboard-keys)

<br/>

---

## 🎛️ Tuning Gesture Sensitivity

All thresholds are at the top of `src/gesture_detector.py` and are commented:

| Constant | Default | What it controls |
|---|---|---|
| `COOLDOWN_S` | `0.8` | Minimum seconds between any two gesture triggers |
| `SWIPE_MIN_DELTA_X` | `0.15` | Swipe travel required (15% of frame width) |
| `SWIPE_WINDOW_S` | `0.6` | Time window in which a swipe must complete |
| `PINCH_THRESHOLD` | `0.08` | Thumb–index closeness (relative to palm size) |
| `PALM_HOLD_S` | `0.5` | Seconds you must hold an open palm before it fires |
| `STATIC_THRESHOLD` | `0.03` | Max wrist drift to count as "stationary" |

**Too sensitive?** Raise `SWIPE_MIN_DELTA_X` or lower `PINCH_THRESHOLD`.  
**Not sensitive enough?** Lower `SWIPE_MIN_DELTA_X` or raise `PINCH_THRESHOLD`.

<br/>

---

## 🛠️ Troubleshooting

<details>
<summary><strong>❌ DLL load failed — mediapipe or opencv won't import</strong></summary>

Install the Microsoft Visual C++ Redistributable (both architectures):

- **x64:** https://aka.ms/vs/17/release/vc_redist.x64.exe
- **x86:** https://aka.ms/vs/17/release/vc_redist.x86.exe

Restart your PC, re-activate the venv, then retry:
```cmd
python -c "import mediapipe; import cv2; print('OK')"
```
</details>

<details>
<summary><strong>❌ ModuleNotFoundError: No module named 'mediapipe'</strong></summary>

You're not inside the virtual environment. Run:
```cmd
venv\Scripts\activate
```
Your prompt should show `(venv)` before the path.
</details>

<details>
<summary><strong>❌ Camera not opening / black screen</strong></summary>

Try a different camera index:
```cmd
python src/main.py --camera 1
```
Some laptops list the IR camera as index 0 and the RGB camera as index 1.
</details>

<details>
<summary><strong>❌ pyautogui FailSafeException — script aborted</strong></summary>

You moved the mouse to a screen corner. This is intentional — pyautogui's
built-in fail-safe is kept enabled as a safety net. Just re-run the script.
</details>

<details>
<summary><strong>❌ Gestures fire too often or not at all</strong></summary>

Adjust the threshold constants at the top of `src/gesture_detector.py`.
See the [Tuning Gesture Sensitivity](#-tuning-gesture-sensitivity) table above.
</details>

<details>
<summary><strong>❌ pip install errors / permission denied</strong></summary>

Make sure the project is **not** inside a OneDrive folder.
Move it to `C:\Projects\gesture-control` and redo the setup steps.
</details>

<br/>

---

## 🏗️ How It Works

```
Webcam frame
     │
     ▼
┌─────────────────┐
│  hand_tracker   │  MediaPipe Hands → 21 landmarks + rolling wrist history
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  gesture_detector   │  Geometric rules (distances / angles) → gesture name
│                     │  + debounce / cooldown (0.8 s gap between triggers)
└────────┬────────────┘
         │
         ▼
┌─────────────────┐
│  action_mapper  │  JSON config → pyautogui.press() / pyautogui.hotkey()
└────────┬────────┘
         │
         ▼
   OS keypress event
   (works with any app)
```

**Detection is purely geometric** — no ML classifier, no training data.
Distances and angles between the 21 MediaPipe landmarks are compared against
tunable thresholds. This makes the logic transparent and easy to tune.

A learned classifier (e.g. a small MLP on flattened landmark coordinates) is
a natural future upgrade if rule-based detection proves unreliable for a
specific gesture in your environment.

<br/>

---

## 🗺️ Roadmap

- [ ] Demo GIF / video in README
- [ ] Two-hand gesture support (v2)
- [ ] GUI settings panel for threshold tuning
- [ ] Gesture recorder to capture custom key combos
- [ ] macOS / Linux key simulation parity
- [ ] Learned gesture classifier (optional upgrade path)

<br/>

---

## 📄 License

MIT © [Eddiegah](https://github.com/Eddiegah)

<br/>

---

<div align="center">

Built with 🖐️ using [MediaPipe](https://mediapipe.dev) · [OpenCV](https://opencv.org) · [pyautogui](https://pyautogui.readthedocs.io)

</div>
