#!/usr/bin/env bash
set -e

# ================================================
#   🐍 Neon Snake — Hand Gesture Control Game
#   One-Click Setup & Launch (macOS / Linux)
# ================================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}  🐍  Neon Snake — Setup & Launch${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""

# ── Step 1: Check Python ──
echo -e "[1/5] ${BOLD}Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PY=python3
elif command -v python &> /dev/null; then
    PY=python
else
    echo -e "${RED}[ERROR] Python is not installed!${NC}"
    echo "Install Python 3.8+ from https://www.python.org/downloads/"
    exit 1
fi
$PY --version
echo ""

# ── Step 2: Create virtual environment ──
echo -e "[2/5] ${BOLD}Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    $PY -m venv venv
    echo -e "  ${GREEN}✓${NC} Virtual environment created"
else
    echo -e "  ${GREEN}✓${NC} Virtual environment already exists"
fi
echo ""

# ── Step 3: Install dependencies ──
echo -e "[3/5] ${BOLD}Installing dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt
echo -e "  ${GREEN}✓${NC} Dependencies installed"
echo ""

# ── Step 4: Download hand tracking model ──
echo -e "[4/5] ${BOLD}Checking hand tracking model...${NC}"
if [ ! -f "hand_landmarker.task" ]; then
    echo "  Downloading hand_landmarker.task (~8 MB)..."
    curl -L -o hand_landmarker.task \
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
    if [ $? -ne 0 ]; then
        echo -e "  ${YELLOW}[WARNING] Download failed.${NC}"
        echo "  Manual download: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
    else
        echo -e "  ${GREEN}✓${NC} Model downloaded"
    fi
else
    echo -e "  ${GREEN}✓${NC} Model file exists"
fi
echo ""

# ── Step 5: Launch game ──
echo -e "[5/5] ${BOLD}Launching game...${NC}"
echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}  🎮 Game Controls${NC}"
echo -e "  ☝️  Index finger  → Move snake"
echo -e "  ✊  Fist           → Pause"
echo -e "  ✋  Open palm      → Restart (after death)"
echo -e "  P                 → Pause/Resume"
echo -e "  R                 → Restart"
echo -e "  Q / ESC           → Quit"
echo -e "${BOLD}============================================${NC}"
echo ""
sleep 2

$PY main_improved.py

echo ""
echo -e "${YELLOW}Game exited. Thanks for playing!${NC}"
