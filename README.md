# Logger Deployment

One-command setup for the Logger application on Arch Linux.

## Quick Start

```bash
git clone https://github.com/RohithBalasubramani/LoggerDeploy.git
cd LoggerDeploy
chmod +x install.sh start.sh
./install.sh
./start.sh
```

## What it does

The `install.sh` script will:
1. Install Node.js, Python, PostgreSQL libs via pacman
2. Clone the Neuract_v3 repository
3. Run `npm install` for the frontend
4. Create Python venv and run `pip install -r requirements.txt` for backend

## Starting Servers

```bash
./start.sh
```

This starts:
- **Backend** (Django): http://0.0.0.0:8000
- **Frontend** (Vite): http://0.0.0.0:5173

Press `Ctrl+C` to stop both.

## Manual Commands

```bash
# Update code
cd app && git pull

# Reinstall dependencies
cd app && npm install
cd app && source venv/bin/activate && pip install -r requirements.txt

# Run Django migrations
cd app && source venv/bin/activate && python manage.py migrate
```
