from __future__ import annotations
import os
import httpx
from solbot.core.logger import logger

TAKER_FEE_BPS = 30

class JupiterQuoter:
    def __init__(self, settings):
        self.settings = settings
        self.base = os.getenv("JUP_BASE", "https://lite-api.jup.ag/swap/v1")

    async def top_routes(self, base_mint: str, quote_mint: str, amount: int, n: int = 3):
        if os.getenv("OFFLINE_QUOTES", "false").lower() == "true":
            in_amt = amount / 1_000_000
            out_amt = in_amt * 0.995
            expected_pnl_usd = (out_amt - in_amt) - in_amt * (TAKER_FEE_BPS/10_000)
            return [{
                "inAmount": str(amount),
                "outAmount": str(int(out_amt * 1_000_000)),
                "expected_pnl_usd": expected_pnl_usd,
            }]
        params = {
            "inputMint": base_mint,
            "outputMint": quote_mint,
            "amount": str(amount),
            "slippageBps": self.settings.MAX_ROUTE_SLIPPAGE_BPS,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{self.base}/quote", params=params)
            r.raise_for_status()
            data = r.json()
        # Do not log the URL (avoid huge links); summarize only
        logger.info("jup.quote", extra={"pair": f"{base_mint[-4:]}->{quote_mint[-4:]}", "amount": amount, "status": "ok"})
        route = (data or {}).get("data") or data
        if isinstance(route, dict):
            route = [route]
        routes = route[:n] if isinstance(route, list) else []
        for r in routes:
            in_amt = float(r.get("inAmount", 0)) / 1_000_000
            out_amt = float(r.get("outAmount", 0)) / 1_000_000
            gross = out_amt - in_amt
            fees = in_amt * (TAKER_FEE_BPS/10_000)
            priority = self.settings.PRIORITY_FEE_MICRO_LAMPORTS / 1_000_000_000 * 25
            r["expected_pnl_usd"] = gross - fees - priority
        return routes
