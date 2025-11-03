# Logging
- The supervisor now logs plan summaries each scan with route, notional, expected PnL and slippage.
- It logs when a plan is filtered for being below `MIN_PROFIT_USD` and when an execution attempt is made.
- Executor continues to report `paper/dry mode — not sending` when DRY_RUN/PAPER_TRADE are enabled.
