# Logger

Full-stack Logger application with React frontend and Django backend.

## Quick Start (Arch Linux)

```bash
git clone https://github.com/RohithBalasubramani/LoggerDeploy.git
cd LoggerDeploy
chmod +x install.sh start.sh
./install.sh
./start.sh
```

## What install.sh does

1. Installs Node.js, Python, PostgreSQL libs via pacman
2. Runs `npm install` in frontend/
3. Creates Python venv and installs requirements in backend/

## Servers

```bash
./start.sh
```

- **Backend** (Django): http://0.0.0.0:8000
- **Frontend** (Vite): http://0.0.0.0:5173

Press `Ctrl+C` to stop.

## Structure

```
LoggerDeploy/
├── frontend/     # React + Vite + MUI
├── backend/      # Django REST API
├── install.sh    # Setup script
└── start.sh      # Start servers
```
