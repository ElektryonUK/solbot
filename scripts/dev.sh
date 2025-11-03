#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate
uvicorn solbot.api:app --host 0.0.0.0 --port 8080 --reload
