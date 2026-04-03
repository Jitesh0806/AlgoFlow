#!/usr/bin/env bash
# AlgoFlow — Quick Setup Script
set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   AlgoFlow — Compiler Setup          ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── Backend ──────────────────────────────────────────────────────────────────
echo "▶ Setting up Python backend..."
cd backend

if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "  ✓ Virtual environment created"
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
pip install -r requirements.txt -q
echo "  ✓ Python dependencies installed"

echo ""
echo "▶ Running compiler tests..."
pytest tests/ -v --tb=short
echo "  ✓ All tests passed"

cd ..

# ── Frontend ─────────────────────────────────────────────────────────────────
echo ""
echo "▶ Setting up Node.js frontend..."
cd frontend
npm install --silent
echo "  ✓ Node dependencies installed"
cd ..

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Setup complete!                    ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "  Start backend:   cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo "  Start frontend:  cd frontend && npm run dev"
echo ""
echo "  Or use Docker:   docker-compose up --build"
echo ""
