#!/usr/bin/env bash
set -euo pipefail

# Load .env into environment (ignore comments/empty lines)
if [ -f .env ]; then
  export $(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' .env | xargs)
fi

# Ensure venv exists
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null

# Honor timeboxing via env, default to unlimited
TIMEBOX_SECONDS=${TIMEBOX_SECONDS:-0}

python3 - <<'PY'
import asyncio, os
from solbot.core.env import Settings
from solbot.services.supervisor import run_supervisor

s = Settings()  # pulls from env (.env loaded by shell)

# Optional overrides: if env provides these, Settings already has them
# We keep this thin to rely on .env values by default.

timebox = int(os.getenv("TIMEBOX_SECONDS", "0"))

async def main():
    task = asyncio.create_task(run_supervisor(s))
    if timebox > 0:
        await asyncio.sleep(timebox)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    else:
        await task

asyncio.run(main())
PY
