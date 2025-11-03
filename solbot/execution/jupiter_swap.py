from __future__ import annotations
import os
import base64
import json
import httpx
from typing import Any
from solbot.core.logger import logger
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction as Transaction

class JupiterSwap:
    def __init__(self):
        self.settings = None
        
    def init_with_settings(self, settings):
        """Initialize with settings after construction"""
        self.settings = settings
        self.base = settings.JUP_EXECUTE_BASE
        logger.info("JupiterSwap initialized", extra={"base_url": self.base, "api_key_set": bool(settings.JUP_API_KEY)})

    async def build_swap(
        self,
        quote_response: dict[str, Any],
        user_pubkey: str,
        prioritization_fee_lamports: int | None = None,
        compute_unit_price_micro_lamports: int | None = None,
    ) -> dict[str, Any]:
        """Ultra API: Sign the transaction from order response and execute"""
        logger.info("Starting Ultra swap", extra={
            "request_id": quote_response.get("requestId", "unknown"),
            "input_mint": quote_response.get("inputMint", "unknown")[-8:],
            "output_mint": quote_response.get("outputMint", "unknown")[-8:],
            "amount": quote_response.get("inAmount"),
        })

        try:
            # Extract transaction and requestId from Ultra order response
            tx_b64 = quote_response.get("transaction")
            request_id = quote_response.get("requestId")
            
            if not tx_b64 or not request_id:
                raise ValueError(f"Ultra order missing transaction or requestId: {list(quote_response.keys())}")

            # Sign locally with solders
            kp_env = os.getenv("USER_KEYPAIR")
            if not kp_env:
                raise ValueError("USER_KEYPAIR missing in env")
                
            if kp_env.startswith("["):
                key_bytes = bytes(json.loads(kp_env))
                kp = Keypair.from_bytes(key_bytes)
            else:
                kp = Keypair.from_base58_string(kp_env)

            tx = Transaction.from_bytes(base64.b64decode(tx_b64))
            signed_tx = tx.sign([kp])
            signed_b64 = base64.b64encode(bytes(signed_tx)).decode()
            logger.info("tx.signed", extra={"len": len(signed_b64), "request_id": request_id})

            # Execute via Ultra API
            payload = {
                "requestId": request_id,
                "signedTransaction": signed_b64
            }
            
            headers = {}
            if self.settings.JUP_API_KEY:
                headers["X-API-Key"] = self.settings.JUP_API_KEY

            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.post(f"{self.base}/execute", json=payload, headers=headers)
                body_txt = None
                try:
                    body_txt = r.text[:800]
                except Exception:
                    pass
                logger.info("execute.response", extra={"status": r.status_code, "body": body_txt})
                r.raise_for_status()
                result = r.json()
                
                logger.info("execute.success", extra={
                    "status": result.get("status"),
                    "signature": result.get("signature", "")[:16] + "..." if result.get("signature") else "none"
                })
                
                return result
                
        except Exception as e:
            logger.error("Ultra swap failed", extra={"err": str(e)})
            raise
