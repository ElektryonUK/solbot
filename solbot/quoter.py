from __future__ import annotations
import os
import httpx
from solbot.core.logger import logger

TAKER_FEE_BPS = 30

class JupiterQuoter:
    def __init__(self, settings):
        self.settings = settings
        self.base = settings.JUP_ORDER_BASE

    async def get_quote(self, input_mint: str, output_mint: str, amount: int) -> dict | None:
        """Get Jupiter Ultra order response with pre-built transaction"""
        if os.getenv("OFFLINE_QUOTES", "false").lower() == "true":
            # Offline mode - return mock Ultra-style response
            in_amt = amount / 1_000_000
            out_amt = in_amt * 0.995
            return {
                "requestId": "mock-request-id",
                "status": "success",
                "transaction": "mock-transaction-b64",
                "inputMint": input_mint,
                "outputMint": output_mint,
                "inAmount": str(amount),
                "outAmount": str(int(out_amt * 1_000_000)),
                "slippageBps": self.settings.MAX_ROUTE_SLIPPAGE_BPS
            }
        
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "taker": self.settings.user_pubkey,  # Required for Ultra API
            "slippageBps": self.settings.MAX_ROUTE_SLIPPAGE_BPS,
        }
        
        headers = {}
        if self.settings.JUP_API_KEY:
            headers["X-API-Key"] = self.settings.JUP_API_KEY
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self.base}/order", params=params, headers=headers)
                body_txt = None
                try:
                    body_txt = r.text[:400]
                except Exception:
                    pass
                logger.info("ultra.order", extra={"status": r.status_code, "body": body_txt})
                r.raise_for_status()
                data = r.json()
                
            # Validate Ultra response has required fields
            if "transaction" not in data or "requestId" not in data:
                logger.warning("order.invalid_response", extra={"keys": list(data.keys())})
                return None
                
            return data
            
        except Exception as e:
            logger.error("order.failed", extra={"error": str(e)})
            return None

    async def top_routes(self, base_mint: str, quote_mint: str, amount: int, n: int = 3):
        """Legacy method for backward compatibility - now returns single Ultra order"""
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
            "quote_response": quote  # Include full Ultra response
        }]
