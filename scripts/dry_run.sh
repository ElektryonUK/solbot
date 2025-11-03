#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate
python - <<'PY'
import asyncio
from solbot.core.env import Settings
from solbot.core.logger import logger
from solbot.services.supervisor import run_supervisor

s = Settings()
s.DRY_RUN = True
s.PAPER_TRADE = True

asyncio.run(run_supervisor(s))
PY
