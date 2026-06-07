# Contributing to SnakeGame_v2 🐍✨

Thank you for your interest in contributing! We love contributions from everyone — whether it's fixing bugs, improving documentation, adding features, or just sharing ideas.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Guidelines](#coding-guidelines)
- [Pull Request Process](#pull-request-process)
- [Feature Ideas](#feature-ideas)

---

## Code of Conduct

By participating in this project, you agree to:
- Be **respectful** and **inclusive** — everyone is welcome
- Provide **constructive** feedback
- Focus on what is **best for the community**
- Show **empathy** towards other community members

## Getting Started

1. 🍴 **Fork** the repository
2. 🌿 Create a feature branch: `git checkout -b feature/amazing-idea`
3. 💻 Make your changes
4. ✅ Test your changes
5. 📤 Push: `git push origin feature/amazing-idea`
6. 🔁 Open a **Pull Request**

## How to Contribute

### 🐛 Report Bugs

Found a bug? [Open an issue](../../issues/new) with:

- **A clear title** and description
- **Steps to reproduce** (what you did, what happened, what you expected)
- **Environment info** (OS, Python version, camera model if relevant)
- **Screenshots** or error messages (if possible)

### 💡 Suggest Features

Have an idea? [Open a feature request](../../issues/new) with:

- What you'd like to see added
- Why it would be useful (use cases)
- Any implementation ideas you have

### ✨ Submit Code

1. Follow the [Development Setup](#development-setup) below
2. Follow the [Coding Guidelines](#coding-guidelines)
3. Make sure the game still runs (`python main_improved.py`)
4. Submit a Pull Request!

## Development Setup

```bash
# 1. Fork and clone your fork
git clone https://github.com/YOUR_USERNAME/SnakeGame_v2.git
cd SnakeGame_v2

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 3. Install dev dependencies
pip install -r requirements.txt
pip install pylint              # Optional, for linting

# 4. Download hand tracking model
curl -L -o hand_landmarker.task \
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"

# 5. Verify the game runs
python main_improved.py
```

## Coding Guidelines

### General

| Rule | Description |
|------|-------------|
| **Language** | Python 3.8+ |
| **Style** | Follow [PEP 8](https://peps.python.org/pep-0008/) |
| **Comments** | We use **Chinese** for code comments (the original author's language) |
| **Docstrings** | Use **English** for function/class docstrings (for global contributors) |
| **Types** | Add type annotations to all function signatures |
| **Naming** | `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants |

### Code Style

```python
# ✅ Good: clear naming, type hints, docstring
def calculate_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


# ❌ Avoid: no types, unclear naming, no docstring
def calc(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)
```

### What to Keep in Mind

- **Config over hard-code** — add new parameters to `GameConfig` rather than hard-coding values
- **Performance matters** — the game runs at 30-60 FPS; avoid expensive operations in the main loop
- **Backward compatibility** — don't break existing features without a good reason
- **Camera required** — always handle the case where no camera is available gracefully

## Pull Request Process

1. **One PR = one feature/bugfix** — keep changes focused
2. **Update the README** if your change affects usage
3. **Test the game** — run `python main_improved.py` and verify:
   - Game starts correctly
   - Hand gesture control works
   - No new console errors
4. **Add a descriptive title** — e.g., "Add rainbow color theme" not "Update code"
5. **In the description**, explain:
   - What you changed and why
   - How to test it
   - Any known limitations

### PR Checklist

```markdown
- [ ] Code compiles / runs without errors
- [ ] Tested with actual webcam
- [ ] README updated (if applicable)
- [ ] No hard-coded secrets or personal paths
- [ ] Type annotations added
```

## Feature Ideas

Here are some features we'd love to see implemented:

| Difficulty | Feature | Description |
|-----------|---------|-------------|
| ⭐ Easy | **New color themes** | Add more entries to the `THEMES` list |
| ⭐ Easy | **Sound assets** | Replace synthesized beeps with `.wav` files |
| ⭐⭐ Medium | **Online leaderboard** | Submit high scores to a cloud database |
| ⭐⭐ Medium | **Pause icon** | Visual indicator when game is paused |
| ⭐⭐⭐ Hard | **Two-player mode** | Split screen, each hand controls a snake |
| ⭐⭐⭐ Hard | **Obstacles** | Walls or barriers that appear as score increases |
| ⭐⭐⭐ Hard | **Mobile support** | Guide for using phone as webcam (Iriun, DroidCam) |

---

## Questions?

If you have any questions, feel free to [open a discussion](../../issues/new) or reach out to the maintainers.

**Happy coding!** 🎮🐍✨
