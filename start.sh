#!/bin/bash
# Banking CRM Agent — one-command startup for Mac/Linux

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo ""
echo " Banking CRM Agent"
echo " ================="
echo ""

# ── 1. Check GROQ_API_KEY ──────────────────────────────────────────────────
if [ ! -f "$ROOT/backend/.env" ]; then
  echo " [ERROR] backend/.env not found."
  echo "         Copy .env.example to backend/.env and set GROQ_API_KEY."
  exit 1
fi

if ! grep -qi "GROQ_API_KEY" "$ROOT/backend/.env"; then
  echo " [ERROR] GROQ_API_KEY not set in backend/.env"
  exit 1
fi

# ── 2. Start backend ───────────────────────────────────────────────────────
echo " [1/3] Starting backend  (FastAPI on :8000) ..."
source "$ROOT/backend/venv/bin/activate"
cd "$ROOT"
PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "       PID: $BACKEND_PID"

# ── 3. Start frontend ──────────────────────────────────────────────────────
echo " [2/3] Starting frontend (Vite on :3000) ..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!
echo "       PID: $FRONTEND_PID"

# ── 4. Wait for backend, then open browser ────────────────────────────────
echo " [3/3] Waiting for backend to be ready ..."
tries=0
until curl -sf http://localhost:8000/docs > /dev/null 2>&1; do
  tries=$((tries + 1))
  if [ $tries -gt 30 ]; then
    echo " [WARN] Backend did not respond after 30s — opening browser anyway."
    break
  fi
  sleep 1
done

echo " Opening http://localhost:3000 ..."
if command -v open &>/dev/null; then
  open http://localhost:3000          # macOS
elif command -v xdg-open &>/dev/null; then
  xdg-open http://localhost:3000      # Linux
fi

echo ""
echo " Both servers are running."
echo " Frontend : http://localhost:3000"
echo " Backend  : http://localhost:8000"
echo " API Docs : http://localhost:8000/docs"
echo ""
echo " Press Ctrl+C to stop both servers."
echo ""

trap "echo ''; echo ' Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ' Done.'" EXIT INT TERM
wait
