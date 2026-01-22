#!/bin/bash
# Start Logger servers
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Logger..."
echo "Press Ctrl+C to stop"
echo ""

# Start backend
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!
echo "Backend: http://0.0.0.0:8000 (PID: $BACKEND_PID)"

# Start frontend
cd "$SCRIPT_DIR/frontend"
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!
echo "Frontend: http://0.0.0.0:5173 (PID: $FRONTEND_PID)"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
