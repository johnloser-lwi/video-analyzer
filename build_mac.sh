#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  build_mac.sh — Build standalone macOS binaries
#
#  Usage:
#    ./build_mac.sh          Build both CLI and GUI
#    ./build_mac.sh cli      Build CLI only
#    ./build_mac.sh gui      Build GUI only
#
#  Output:
#    dist/video-analyzer         CLI binary
#    dist/video-analyzer-gui     GUI binary
#    dist/Video Analyzer.app     macOS app bundle (GUI)
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

TARGET="${1:-all}"

# Colors for output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${CYAN}▸${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠${NC} $*"; }
fail()  { echo -e "${RED}✗${NC} $*"; exit 1; }

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Video Analyzer — macOS Build"
echo "═══════════════════════════════════════════════════════"
echo ""

# ── Check Python ────────────────────────────────────────────
PYTHON=""
for candidate in python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    fail "Python 3.10+ is required but not found. Install it from python.org or via Homebrew."
fi

PY_VERSION=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Using Python $PY_VERSION ($PYTHON)"

# ── Create / activate virtual environment ───────────────────
VENV_DIR="build_venv"

if [ ! -d "$VENV_DIR" ]; then
    info "Creating build virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
ok "Virtual environment activated"

# ── Install dependencies ────────────────────────────────────
info "Installing dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet
ok "Dependencies installed"

# ── Clean previous builds ──────────────────────────────────
info "Cleaning previous builds..."
rm -rf build/ dist/

# ── Build CLI ───────────────────────────────────────────────
if [ "$TARGET" = "all" ] || [ "$TARGET" = "cli" ]; then
    echo ""
    info "Building CLI binary..."
    pyinstaller video-analyzer-cli.spec --noconfirm --clean
    ok "CLI binary built: dist/video-analyzer"
fi

# ── Build GUI ───────────────────────────────────────────────
if [ "$TARGET" = "all" ] || [ "$TARGET" = "gui" ]; then
    echo ""
    info "Building GUI binary..."
    pyinstaller video-analyzer-gui.spec --noconfirm --clean
    ok "GUI binary built: dist/video-analyzer-gui"
    ok "App bundle built: dist/Video Analyzer.app"
fi

# ── Done ────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Build complete! Binaries are in ./dist/"
echo ""

if [ "$TARGET" = "all" ] || [ "$TARGET" = "cli" ]; then
    echo "  CLI:  ./dist/video-analyzer --help"
fi
if [ "$TARGET" = "all" ] || [ "$TARGET" = "gui" ]; then
    echo "  GUI:  ./dist/video-analyzer-gui"
    echo "  App:  open ./dist/Video\\ Analyzer.app"
fi

echo ""
echo "  Note: FFprobe (ffmpeg) must be installed on the"
echo "  target system for video metadata extraction."
echo "═══════════════════════════════════════════════════════"
echo ""

deactivate
