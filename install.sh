#!/bin/bash
# Logger Installation Script for Arch Linux
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

REPO_URL="https://github.com/RohithBalasubramani/Neuract_v3.git"
APP_DIR="$SCRIPT_DIR/app"

echo "=========================================="
echo "  Logger Installation - Arch Linux"
echo "=========================================="

# Install system dependencies
echo -e "\n[1/4] Installing system dependencies..."
sudo pacman -S --noconfirm --needed nodejs npm python python-pip postgresql-libs python-virtualenv git

# Clone repo
echo -e "\n[2/4] Cloning repository..."
if [ -d "$APP_DIR" ]; then
    echo "Repo exists, pulling latest..."
    cd "$APP_DIR" && git pull && cd ..
else
    git clone "$REPO_URL" app
fi

# Setup frontend (package.json at root)
echo -e "\n[3/4] Installing frontend dependencies..."
cd "$APP_DIR"
if [ -f "package.json" ]; then
    npm install
    echo "Frontend dependencies installed"
else
    echo "No package.json found at root, skipping frontend npm install"
fi

# Setup backend (Django with requirements.txt)
echo -e "\n[4/4] Setting up backend..."
cd "$APP_DIR"

# Create venv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "Backend dependencies installed"
else
    echo "No requirements.txt found, skipping pip install"
fi

# Make scripts executable
chmod +x "$SCRIPT_DIR/start.sh" 2>/dev/null || true

echo -e "\n=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "To start the servers, run:"
echo "  ./start.sh"
echo ""
