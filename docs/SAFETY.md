# Risk & Safety Checklist

- Start with DRY_RUN=true and PAPER_TRADE=true
- Set MIN_PROFIT_USD conservatively (e.g., 0.75–2.00) until you profile fills
- Set MAX_NOTIONAL_USD based on your risk appetite and pool depth
- Use a fast private RPC close to your server region
- Prefer Jito bundle submission in volatile periods
- Monitor logs; backoff kicks in via PAUSE_AFTER_FAILS and DailyLossGuard
