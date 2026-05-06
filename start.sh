#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "[INFO] Building frontend..."
cd "$FRONTEND_DIR"
npm install
npm run build

echo "[INFO] Setting up backend..."
cd "$BACKEND_DIR"

if command -v conda &>/dev/null; then
    ENV_NAME="anomaly-detection"
    if ! conda env list | grep -q "^${ENV_NAME} "; then
        echo "[INFO] Creating conda environment..."
        conda create -n "$ENV_NAME" python=3.12 -y
    fi
    eval "$(conda shell.bash hook)"
    conda activate "$ENV_NAME"
else
    if [ ! -d ".venv" ]; then
        echo "[INFO] Creating virtual environment..."
        python3 -m venv .venv
    fi
    source .venv/bin/activate
fi

pip install --upgrade pip setuptools wheel
pip install -e "."

echo ""
echo "======================================"
echo "  Dashboard : http://localhost:8000"
echo "  API Docs  : http://localhost:8000/docs"
echo "======================================"
echo ""
echo "Press Ctrl+C to stop"
echo ""

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
