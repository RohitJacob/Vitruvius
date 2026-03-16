#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Backend setup ──
echo "==> Setting up backend..."
cd "$ROOT/backend"

if [ ! -d ".venv" ]; then
    echo "    Creating virtual environment with uv..."
    uv venv .venv
fi

echo "    Installing Python dependencies..."
uv pip install -r requirements.txt

# ── Frontend setup ──
echo "==> Setting up frontend..."
cd "$ROOT/frontend"

if [ ! -d "node_modules" ]; then
    echo "    Installing npm dependencies..."
    npm install
fi

# ── Start both servers ──
echo "==> Starting backend (port 8111) and frontend (port 5111)..."

cd "$ROOT/backend"
uv run uvicorn main:app --reload --port 8111 &
BACKEND_PID=$!

cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

cleanup() {
    echo ""
    echo "==> Shutting down..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
    echo "    Done."
}
trap cleanup INT TERM

echo ""
echo "  Backend:  http://localhost:8111"
echo "  Frontend: http://localhost:5111"
echo "  API docs: http://localhost:8111/docs"
echo ""
echo "  Press Ctrl+C to stop both servers."
echo ""

wait
