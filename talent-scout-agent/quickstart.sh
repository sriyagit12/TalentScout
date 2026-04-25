#!/usr/bin/env bash
# One-command local setup. Requires: python3.10+, node18+, npm.
set -e

cd "$(dirname "$0")"

echo "==> Setting up backend..."
cd backend
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "⚠️  Edit backend/.env and add your ANTHROPIC_API_KEY."
  echo "   Get one at: https://console.anthropic.com/"
  echo ""
  exit 1
fi

# Start backend in background
echo "==> Starting backend on :8000..."
uvicorn app.main:app --port 8000 &
BACKEND_PID=$!

cd ../frontend
if [ ! -d node_modules ]; then
  echo "==> Installing frontend deps..."
  npm install --silent
fi

echo "==> Starting frontend on :5173..."
echo ""
echo "🎯 Open http://localhost:5173 in your browser"
echo ""

# Trap to kill backend when frontend exits
trap "kill $BACKEND_PID 2>/dev/null" EXIT

npm run dev
