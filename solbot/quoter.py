from __future__ import annotations
import httpx
from typing import Sequence
from solbot.core.env import Settings

TAKER_FEE_BPS = 30  # 0.30% placeholder until per-venue fees are modeled

class JupiterQuoter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base = "https://quote-api.jup.ag/v6"

    async def top_routes(self, base_mint: str, quote_mint: str, amount: int, n: int = 3):
        params = {
            "inputMint": base_mint,
            "outputMint": quote_mint,
            "amount": str(amount),
            "slippageBps": self.settings.MAX_ROUTE_SLIPPAGE_BPS,
            "onlyDirectRoutes": False,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{self.base}/quote", params=params)
            r.raise_for_status()
            data = r.json()
        routes = (data or {}).get("data", [])[:n]
        # annotate with a simple expected pnl model for dry-run decisions
        for r in routes:
            in_amt = float(r.get("inAmount", 0)) / 1_000_000
            out_amt = float(r.get("outAmount", 0)) / 1_000_000
            gross = out_amt - in_amt
            fees = in_amt * (TAKER_FEE_BPS / 10_000)
            priority = self.settings.PRIORITY_FEE_MICRO_LAMPORTS / 1_000_000_000 * 25  # est SOL/USD 25
            r["expected_pnl_usd"] = gross - fees - priority
        return routes
