from __future__ import annotations
import httpx
from typing import Sequence
from solbot.core.env import Settings

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
        return (data or {}).get("data", [])[:n]
