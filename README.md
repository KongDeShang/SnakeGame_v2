<div align="center">
  <h1>🐍 Neon Snake — Hand Gesture Control</h1>
  <p>
    <strong>A dazzling snake game powered by <em>hand gesture recognition</em> with neon visuals, particle effects, color themes, and CRT filters.</strong>
  </p>
  <p>
    手势操控的霓虹贪吃蛇 · 无需键盘，伸手即玩
  </p>

  <!-- Badges -->
  <p>
    <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python" alt="Python 3.8+"/>
    <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform"/>
    <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"/>
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs Welcome"/>
    <img src="https://img.shields.io/github/stars/yourname/SnakeGame_v2?style=social" alt="Stars"/>
  </p>

  <br>

  <!-- Screenshot Area - Add your own screenshots here -->
  <p>
    <em>(Screenshots / Demo GIF — add your gameplay recording here!)</em>
  </p>
  <br>
</div>

---

## ✨ Features

<table>
<tr>
<td>

### 🎮 Gameplay
- **Hand gesture control** — index finger tracks like a mouse, no keyboard needed
- **Neon visual style** — glowing gradient snake, particle explosions, pulse rings
- **Color theme system** — 6 themes (NEON, INFERNO, ELECTRIC, SOLAR, AURORA, PRISM) that auto-upgrade every 5 points
- **Bonus food** — golden diamond food worth **3 points** (appears randomly for ~3 seconds)
- **Difficulty scaling** — speed increases every 5 points
- **Collision detection** — wall bounce & self-collision
- **Countdown start** — 3...2...1...GO!
- **CRT scanline filter** — retro aesthetic toggle

</td>
<td>

### ✨ Visual Effects
- Snake body: flowing gradient, pulsing aura, trailing sparkle particles
- Food: pulsing neon glow ring
- Screen flash on eating (theme color)
- Particle burst on food collect
- Floating `+1` / `+3` popup text
- Pulsing border frame
- Game-over stats screen (time / food eaten / max length)

### 🔊 Audio
- Non-blocking sound effects via `pygame.mixer` (sine/square wave synthesis)
- Eat food → high beep | Bonus food → higher beep | Death → low buzz
- Zero external audio file dependency

</td>
</tr>
</table>

---

## 📸 Screenshots

> **Tip:** Add your own gameplay screenshots here! Take a screenshot during play and put it in a `screenshots/` folder.
>
> ```
> screenshots/
> ├── gameplay.png
> ├── bonus_food.png
> ├── game_over.png
> └── theme_inferno.png
> ```

<pre>
┌─────────────────────────────────────────────────────┐
│                                                     │
│   NEON                Score  42          FPS  60    │
│                       Level  8                      │
│                       High   100                    │
│                                                     │
│            🐍  ← snake moves here                   │
│                                                     │
│                ⬟  ← bonus food (+3)                 │
│                                                     │
│              🍩  ← regular food                     │
│                                                     │
│   ──────────────── Neon Border ──────────────────   │
└─────────────────────────────────────────────────────┘
</pre>

---

## 🧰 Prerequisites

Before you begin, ensure you have:

| Requirement | Version | Check Command |
|-------------|---------|--------------|
| **Python** | 3.8 – 3.11 | `python --version` |
| **Webcam** | Any built-in or USB camera | — |
| **OS** | Windows 10/11, macOS, or Linux | — |

> ⚠️ **Python 3.12+** may have compatibility issues with some MediaPipe versions. Python 3.10 is recommended for the smoothest experience.
>
> ⚠️ **Python 3.7 以上**版本均可，推荐 Python 3.10。如果你不确定 Python 是什么，请先安装 Python 3.10：
> 1. 打开 https://www.python.org/downloads/release/python-31011/
> 2. 向下滚动，根据你的系统下载安装包
> 3. 安装时**务必勾选** "Add Python to PATH"

---

## 🚀 Installation

### ⚡ Windows — One-Click Setup

If you're on **Windows**, just double-click:

1. **Clone or download** this repository
2. **Double-click** `setup_and_run.bat` — it will:
   - Create a virtual environment (✅)
   - Install all dependencies (✅)
   - Download the hand tracking model (✅)
   - Launch the game (✅)

### 🐧 macOS / Linux — Manual Setup

Open a terminal and run:

```bash
# 1️⃣ Clone the repository
git clone https://github.com/yourusername/SnakeGame_v2.git
cd SnakeGame_v2

# 2️⃣ Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# 3️⃣ Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4️⃣ Download the hand tracking model (about 8 MB)
curl -L -o hand_landmarker.task \
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"

# 5️⃣ Ready! Run the game
python main_improved.py
```

### 📦 Dependencies Explained

```
opencv-python  → Camera capture & image processing  (摄像头与图像处理)
mediapipe      → Hand landmark detection             (手势识别)
cvzone         → Hand tracking utility               (手势追踪工具)
numpy          → Numerical computation               (数值计算)
pygame         → Audio playback                      (音效播放)
Pillow         → Image loading                       (图片加载)
```

> 💡 Most of these install automatically via `requirements.txt`. If you encounter a `pygame` error, the game will still work — it'll just run without sound.

---

## 🎮 How to Play

```
┌──────────────────────────────────────┐
│                                      │
│  📷 CAMERA WINDOW                    │
│  ┌──────────────┐                    │
│  │              │                    │
│  │   ✋ ← your  │   🖥️ GAME WINDOW  │
│  │      hand    │   ┌──────────┐     │
│  │              │   │ 🐍       │     │
│  └──────────────┘   │    🍩    │     │
│                     │          │     │
│                     └──────────┘     │
│                                      │
└──────────────────────────────────────┘
```

### Gesture Controls

| Gesture | Action | 操作 |
|---------|--------|------|
| ☝️ **Extend index finger** | Control snake direction (moves toward your fingertip) | 伸出食指控制蛇 |
| ✊ **Make a fist** | The snake stops / pauses | 握拳暂停 |
| ✋ **Open palm** (after death) | Restart the game | 死亡后张开手掌重新开始 |

### Keyboard Controls

| Key | Action | 按键功能 |
|-----|--------|---------|
| `P` | Pause / Resume | 暂停/继续 |
| `R` | Restart game | 重新开始 |
| `Q` or `ESC` | Quit | 退出游戏 |

### 🎯 Game Tips

- Keep your hand **30–60 cm** from the camera (one arm's length)
- Ensure **good lighting** — backlight confuses the hand detector
- Only **extend your index finger**; curl the others into a fist
- The snake moves toward your fingertip position on screen
- Avoid **complex backgrounds** for best gesture recognition

---

## 🏆 Scoring & Progression

| Score Milestone | Unlock |
|----------------|--------|
| 0 pts | **NEON** theme (default) — purple to cyan |
| 5 pts | **INFERNO** — dark red to orange blaze |
| 10 pts | **ELECTRIC** — deep blue to electric blue |
| 15 pts | **SOLAR** — amber to golden |
| 20 pts | **AURORA** — violet to cyan-green |
| 25 pts | **PRISM** — rainbow shift, most colors |
| Every +5 pts | Speed increases by 10% |
| Bonus food | **+3 points** (golden diamond, 3-second window) |

### Challenge Badges

| Rank | Score Required |
|------|---------------|
| 🥉 Bronze | 10 |
| 🥈 Silver | 20 |
| 🥇 Gold | 30 |
| 💎 Diamond | 50 |
| 👑 King | 100 |

---

## ⚙️ Configuration

All game parameters are centralized in the `GameConfig` class inside `main_improved.py` (~line 66).

```python
class GameConfig:
    # ── Difficulty ──
    SPEED_INCREASE_INTERVAL = 5       # Speed up every N points (higher = easier)
    SPEED_MULTIPLIER_INCREMENT = 0.1  # Speed increase per level (lower = easier)
    INITIAL_LENGTH = 150              # Snake starting length
    
    # ── Bonus Food ──
    BONUS_ENABLED = True              # Enable golden bonus food
    BONUS_COOLDOWN = 600              # Cooldown frames (~10 sec)
    BONUS_DURATION = 180              # Visible duration frames (~3 sec)
    BONUS_SCORE = 3                   # Points for bonus food
    
    # ── Visual ──
    CRT_ENABLED = True               # CRT scanline filter
    BOUNDARY_MARGIN = 40             # Wall collision margin
    
    # ── Performance ──
    HAND_DETECT_INTERVAL = 2         # Hand detection every N frames (2 = ~30fps detection)
    GESTURE_SMOOTH_WINDOW = 12       # Smoothing window (higher = smoother but laggier)
```

> 💡 **Making the game easier:** Increase `SPEED_INCREASE_INTERVAL` (e.g., to 10) and decrease `SPEED_MULTIPLIER_INCREMENT` (e.g., to 0.05).

---

## 📁 Project Structure

```
SnakeGame_v2/
├── main_improved.py          # ⭐ Main game (enhanced v4, recommended)
├── mediapipe_compat.py       # MediaPipe compatibility shim (new→old API)
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── CONTRIBUTING.md           # Contribution guide
├── LICENSE                   # MIT License
│
├── donut.png                 # Food image asset (PNG)
├── hand_landmarker.task      # Hand landmark model (~8 MB)
├── high_score.json           # High score data (auto-generated)
│
├── run_improved.bat          # Windows launcher (improved version)
├── setup_and_run.bat         # Windows auto-setup + launch
│
├── video_editor/             # Bonus: video editing utility
│   ├── auto_edit.py
│   ├── config.json
│   ├── README.md
│   └── requirements.txt
│
└── venv/                     # Virtual environment (auto-created by setup)
```

---

## ❓ Troubleshooting

<details>
<summary><b>📷 "Cannot open camera!" error</b></summary>

```bash
# Check if another app is using the camera (Zoom, WeChat, etc.)
# Try changing camera index in main_improved.py:
# Line ~1390:  cap = cv2.VideoCapture(0)  →  cap = cv2.VideoCapture(1)
```
</details>

<details>
<summary><b>🖐️ Gesture detection is inaccurate</b></summary>

- Ensure **good lighting** (daylight or direct room light)
- Keep hand **30–60 cm** from the camera
- Avoid **backgrounds with skin tones** or complex patterns
- Only **extend your index finger**; keep others curled
</details>

<details>
<summary><b>🐌 Game is laggy / low FPS</b></summary>

- Lower the camera resolution (find `1280, 720` in the code and change to `640, 480`)
- Increase `HAND_DETECT_INTERVAL` to 3 or 4
- Disable CRT filter: set `CRT_ENABLED = False`
</details>

<details>
<summary><b>🔊 No sound</b></summary>

```bash
pip install pygame   # Install audio library
# Or on Windows: sound should work without pygame via winsound
```
</details>

<details>
<summary><b>📦 MediaPipe installation fails</b></summary>

```bash
# Python 3.10 is recommended
pip install mediapipe==0.10.9
# If still failing, try:
pip install mediapipe==0.8.11
```
</details>

<details>
<summary><b>🐍 "hand_landmarker.task not found"</b></summary>

Download it manually:
```bash
curl -L -o hand_landmarker.task \
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
```
</details>

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| [Python](https://www.python.org/) | Core language |
| [OpenCV](https://opencv.org/) | Camera capture, image processing, rendering |
| [MediaPipe](https://mediapipe.io/) | Hand landmark detection (21 keypoints per hand) |
| [cvzone](https://github.com/cvzone/cvzone) | Hand tracking utility wrapper |
| [NumPy](https://numpy.org/) | Numerical computations, array operations |
| [Pygame](https://www.pygame.org/) | Audio playback |
| [Pillow](https://python-pillow.org/) | Image asset loading |

---

## 🤝 Contributing

Contributions are **welcome and appreciated**! Here's how you can help:

1. 🍴 **Fork** the repository
2. 🌿 Create a feature branch: `git checkout -b feature/my-idea`
3. 💻 Commit your changes: `git commit -m 'Add my awesome feature'`
4. 📤 Push: `git push origin feature/my-idea`
5. 🔁 Open a **Pull Request**

Check out [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

### Ideas for Contribution

- ✨ **More color themes** (add to the `THEMES` list in `main_improved.py`)
- 🎮 **Two-player mode** (split screen, each hand controls a snake)
- 📱 **Mobile support** (via smartphone camera as webcam, e.g., Iriun)
- 🏆 **Online leaderboard** (submit high scores)
- 🌍 **Localization** (add more language support)
- 🐛 **Bug fixes and performance improvements**

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- Based on [Bilibili tutorial](https://b23.tv/dBJlEwJ) and [CSDN blog](https://blog.csdn.net/qq_44631615/article/details/123270882)
- Built with [MediaPipe](https://mediapipe.io/) by Google
- Hand tracking wrapper via [cvzone](https://github.com/cvzone/cvzone)

---

<div align="center">
  <h3>⭐ If you like this project, please give it a star! ⭐</h3>
  <p>
    <a href="https://github.com/yourusername/SnakeGame_v2/stargazers">
      <img src="https://img.shields.io/github/stars/yourusername/SnakeGame_v2?style=for-the-badge&logo=github" alt="stars"/>
    </a>
  </p>
  <p>
    <a href="../../issues">Report Bug</a>
    ·
    <a href="../../issues">Request Feature</a>
    ·
    <a href="https://github.com/yourusername">Follow Me</a>
  </p>
  <p>
    Made with ❤️ and 🐍
  </p>
</div>
