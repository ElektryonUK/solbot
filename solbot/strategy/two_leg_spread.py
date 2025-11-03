from __future__ annotations
from typing import List
from solbot.core.env import Settings
from solbot.discovery import DiscoveryService
from solbot.quoter import JupiterQuoter
from solbot.strategy.models import Plan

USD_MINTS = {"USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"}
SOL_MINT = "So11111111111111111111111111111111111111112"

class TwoLegSpread:
    def __init__(self, settings: Settings, discovery: DiscoveryService, quoter: JupiterQuoter):
        self.s = settings
        self.d = discovery
        self.q = quoter

    async def propose_plans(self) -> List[Plan]:
        plans: List[Plan] = []
        notional_usd = min(self.s.MAX_NOTIONAL_USD, 50)
        amount = int(notional_usd * 1_000_000)
        for usd_mint in USD_MINTS.values():
            routes = await self.q.top_routes(usd_mint, SOL_MINT, amount, n=1)
            if not routes:
                continue
            r = routes[0]
            est = float(r.get("expected_pnl_usd", -1))
            plans.append(Plan(route=[usd_mint, SOL_MINT], notional_usd=notional_usd, expected_pnl_usd=est, max_slippage_bps=self.s.SLIPPAGE_BPS_PER_LEG*2))
        return plans
