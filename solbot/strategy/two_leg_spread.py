from __future__ import annotations
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
        amount = int(notional_usd * 1_000_000)  # assume USDC 6dp
        
        # scan SOL<>USD pairs as a simple baseline
        for usd_mint in USD_MINTS.values():
            quote = await self.q.get_quote(usd_mint, SOL_MINT, amount)
            if not quote:
                continue
                
            # Extract data from quote response
            in_amt = float(quote.get("inAmount", 0)) / 1_000_000
            out_amt = float(quote.get("outAmount", 0)) / 1_000_000
            gross = out_amt - in_amt
            fees = in_amt * (30/10_000)  # Taker fee
            priority = self.s.PRIORITY_FEE_MICRO_LAMPORTS / 1_000_000_000 * 25
            est_pnl = gross - fees - priority
            
            plans.append(Plan(
                input_mint=usd_mint,
                output_mint=SOL_MINT,
                input_amount=amount,
                quote_response=quote,
                notional_usd=notional_usd,
                expected_pnl_usd=est_pnl,
                max_slippage_bps=self.s.SLIPPAGE_BPS_PER_LEG*2
            ))
        return plans
