#!/bin/bash
# Logger Installation Script for Arch Linux
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  Logger Installation - Arch Linux"
echo "=========================================="

# Install system dependencies
echo -e "\n[1/3] Installing system dependencies..."
sudo pacman -S --noconfirm --needed nodejs npm python python-pip postgresql-libs python-virtualenv

# Setup frontend
echo -e "\n[2/3] Installing frontend dependencies..."
cd "$SCRIPT_DIR/frontend"
npm install

# Setup backend
echo -e "\n[3/3] Setting up backend..."
cd "$SCRIPT_DIR/backend"

if [ ! -d "venv" ]; then
    python -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "\n=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "Run: ./start.sh"
