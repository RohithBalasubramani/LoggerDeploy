#!/bin/bash
# Start Logger servers
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/app"

echo "Starting Logger..."
echo "Press Ctrl+C to stop"
echo ""

# Start backend (Django)
cd "$APP_DIR"
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!
echo "Backend started on http://0.0.0.0:8000 (PID: $BACKEND_PID)"

# Start frontend (Vite)
cd "$APP_DIR"
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!
echo "Frontend starting on http://0.0.0.0:5173 (PID: $FRONTEND_PID)"

# Cleanup on exit
trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait
