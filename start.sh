#!/usr/bin/env bash
export PYTHONPATH="$(cd "$(dirname "$0")" && pwd)/src:${PYTHONPATH:-}"
exec uvicorn anomaly_detection.app:app --host 0.0.0.0 --port 8000
