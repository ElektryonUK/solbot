from __future__ import annotations
import time

class DailyLossGuard:
    def __init__(self, limit_usd: float):
        self.limit = limit_usd
        self.reset_ts = time.time()
        self.accum = 0.0

    def add_pnl(self, pnl_usd: float) -> None:
        now = time.time()
        if now - self.reset_ts > 24*3600:
            self.reset_ts = now
            self.accum = 0.0
        self.accum += pnl_usd

    def exceeded(self) -> bool:
        return self.accum < -abs(self.limit)
