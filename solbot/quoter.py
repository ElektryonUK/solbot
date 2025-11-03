from __future__ import annotations
import os
import httpx
from solbot.core.logger import logger

TAKER_FEE_BPS = 30

class JupiterQuoter:
    def __init__(self, settings):
        self.settings = settings
        self.base = settings.JUP_QUOTE_BASE

    async def get_quote(self, input_mint: str, output_mint: str, amount: int) -> dict | None:
        """Get full Jupiter quote response with routePlan"""
        if os.getenv("OFFLINE_QUOTES", "false").lower() == "true":
            # Offline mode - return mock quote with routePlan structure
            in_amt = amount / 1_000_000
            out_amt = in_amt * 0.995
            expected_pnl_usd = (out_amt - in_amt) - in_amt * (TAKER_FEE_BPS/10_000)
            return {
                "inputMint": input_mint,
                "inAmount": str(amount),
                "outputMint": output_mint, 
                "outAmount": str(int(out_amt * 1_000_000)),
                "otherAmountThreshold": str(int(out_amt * 1_000_000 * 0.99)),
                "swapMode": "ExactIn",
                "slippageBps": self.settings.MAX_ROUTE_SLIPPAGE_BPS,
                "routePlan": [
                    {
                        "swapInfo": {
                            "ammKey": "mock_amm",
                            "label": "Mock",
                            "inputMint": input_mint,
                            "outputMint": output_mint,
                            "inAmount": str(amount),
                            "outAmount": str(int(out_amt * 1_000_000)),
                            "feeAmount": "0",
                            "feeMint": input_mint
                        },
                        "percent": 100
                    }
                ],
                "contextSlot": 12345,
                "timeTaken": 0.1
            }
        
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": self.settings.MAX_ROUTE_SLIPPAGE_BPS,
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self.base}/quote", params=params)
                r.raise_for_status()
                data = r.json()
                
            logger.info("jup.quote", extra={"pair": f"{input_mint[-4:]}->{output_mint[-4:]}", "amount": amount, "status": "ok"})
            
            # Validate response has routePlan
            if "routePlan" not in data or not data["routePlan"]:
                logger.warning("quote.no_route_plan", extra={"response_keys": list(data.keys())})
                return None
                
            return data
            
        except Exception as e:
            logger.error("quote.failed", extra={"error": str(e)})
            return None

    async def top_routes(self, base_mint: str, quote_mint: str, amount: int, n: int = 3):
        """Legacy method for backward compatibility - now returns single quote"""
        quote = await self.get_quote(base_mint, quote_mint, amount)
        if not quote:
            return []
            
        in_amt = float(quote.get("inAmount", 0)) / 1_000_000
        out_amt = float(quote.get("outAmount", 0)) / 1_000_000
        gross = out_amt - in_amt
        fees = in_amt * (TAKER_FEE_BPS/10_000)
        priority = self.settings.PRIORITY_FEE_MICRO_LAMPORTS / 1_000_000_000 * 25
        expected_pnl_usd = gross - fees - priority
        
        return [{
            "inAmount": quote.get("inAmount"),
            "outAmount": quote.get("outAmount"), 
            "expected_pnl_usd": expected_pnl_usd,
            "quote_response": quote  # Include full response
        }]
