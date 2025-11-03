# Dry Run Guide

1) Prepare environment
```
cp .env.example .env
# fill SOLANA_RPC_URL and optionally RPC_HTTPS list
# leave DRY_RUN=true and PAPER_TRADE=true
```

2) Create venv and install deps
```
./scripts/bootstrap.sh
```

3) Start dry-run supervisor
```
./scripts/dry_run.sh
```

4) Observe logs
- Strategies propose plans with `expected_pnl_usd`
- Supervisor filters by `MIN_PROFIT_USD`
- Executor logs "paper/dry mode — not sending"

5) Tune parameters
- Adjust MIN_PROFIT_USD, SCAN_INTERVAL_MS, SLIPPAGE_BPS_PER_LEG
- Add more RPCs to RPC_HTTPS for failover

When satisfied, flip DRY_RUN/PAPER_TRADE to false to enable live sends (after keys configured).
