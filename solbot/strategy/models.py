from __future__ import annotations
from pydantic import BaseModel
from typing import Any

class Plan(BaseModel):
    input_mint: str
    output_mint: str
    input_amount: int
    quote_response: dict[str, Any]  # Full Jupiter quote response with routePlan
    notional_usd: float
    expected_pnl_usd: float
    max_slippage_bps: int
    notes: str | None = None
