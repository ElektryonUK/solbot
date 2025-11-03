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
        """Get Jupiter Ultra order response with pre-built transaction (POST /order)"""
        if os.getenv("OFFLINE_QUOTES", "false").lower() == "true":
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

        body = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "taker": self.settings.user_pubkey,
            "slippageBps": self.settings.MAX_ROUTE_SLIPPAGE_BPS,
            # Explicit build-mode request for executable transaction
            "mode": "build",
            "swapMode": "ExactIn",
            "useSharedAccounts": True,
            "wrapAndUnwrapSol": True,
        }
        if self.settings.PRIORITY_FEE_MICRO_LAMPORTS:
            body["computeUnitPriceMicroLamports"] = self.settings.PRIORITY_FEE_MICRO_LAMPORTS

        headers = {"Content-Type": "application/json"}
        if self.settings.JUP_API_KEY:
            headers["X-API-Key"] = self.settings.JUP_API_KEY

        try:
            async with httpx.AsyncClient(timeout=12) as client:
                r = await client.post(f"{self.base}/order", json=body, headers=headers)
                body_txt = None
                try:
                    body_txt = r.text[:800]
                except Exception:
                    pass
                logger.info("ultra.order", extra={"status": r.status_code, "body": body_txt})
                r.raise_for_status()
                data = r.json()

            if not (isinstance(data, dict) and data.get("transaction") and data.get("requestId")):
                logger.warning("order.invalid_or_quote_only", extra={"keys": list(data.keys()) if isinstance(data, dict) else type(data).__name__})
                return None

            return data

        except Exception as e:
            logger.error("order.failed", extra={"error": str(e)})
            return None
