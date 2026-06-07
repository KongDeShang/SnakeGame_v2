@echo off
chcp 65001 >nul
title 🐍 Neon Snake by KongDeShang — Setup & Run

echo ================================================
echo   🐍 Neon Snake — Hand Gesture Control Game
echo   One-Click Setup ^& Launch
echo ================================================
echo.

:: ── Step 1: Check Python ──
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please download Python 3.10 from:
    echo https://www.python.org/downloads/release/python-31011/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
python --version
echo.

:: ── Step 2: Create virtual environment ──
echo [2/5] Setting up virtual environment...
if not exist venv\ (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo   ✓ Virtual environment created
) else (
    echo   ✓ Virtual environment already exists
)
echo.

:: ── Step 3: Install dependencies ──
echo [3/5] Installing dependencies (this may take a few minutes)...
call venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Some packages failed to install.
    echo The game may still work with reduced features.
)
echo   ✓ Dependencies installed
echo.

:: ── Step 4: Download hand tracking model ──
echo [4/5] Checking hand tracking model...
if not exist hand_landmarker.task (
    echo   Downloading hand_landmarker.task (~8 MB)...
    curl -L -o hand_landmarker.task ^
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
    if errorlevel 1 (
        echo.
        echo [WARNING] Download failed. You can download manually:
        echo   https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
    ) else (
        echo   ✓ Model downloaded
    )
) else (
    echo   ✓ Model file exists
)
echo.

:: ── Step 5: Launch game ──
echo [5/5] Launching game...
echo.
echo ================================================
echo   🎮 Game Controls
echo   ☝️  Index finger  → Move snake
echo   ✊  Fist           → Pause
echo   ✋  Open palm      → Restart (after death)
echo   P                 → Pause/Resume
echo   R                 → Restart
echo   Q / ESC           → Quit
echo ================================================
echo.
timeout /t 3 /nobreak >nul

python main_improved.py

if errorlevel 1 (
    echo.
    echo [ERROR] Game exited with an error.
    echo Try running this script again, or check TROUBLESHOOTING.md
    pause
)
