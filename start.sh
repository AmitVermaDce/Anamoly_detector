#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[INFO] Setting up..."
cd "$SCRIPT_DIR"

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

exec uvicorn anomaly_detection.app:app --host 0.0.0.0 --port 8000
