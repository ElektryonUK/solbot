from __future__ import annotations
from pydantic import BaseModel

class Plan(BaseModel):
    route: list[str]
    notional_usd: float
    expected_pnl_usd: float
    max_slippage_bps: int
    notes: str | None = None
