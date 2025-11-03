# Extended Operations Runbook

This document augments SETUP.md with ops notes and tuning for arbitrage.

- Benchmark your RPCs: `python scripts/bench_rpcs.py`
- Keep DRY_RUN and PAPER_TRADE enabled until you validate quotes and routes
- Set PRIORITY_FEE_MICRO_LAMPORTS based on congestion to land within 1–2 slots
- Rotate RPC if median latency > 250 ms
- Prefer Jito bundle submission for protection in live mode
