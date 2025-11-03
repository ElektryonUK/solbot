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
        self.base = settings.JUP_SWAP_BASE
        logger.info("JupiterSwap initialized", extra={"base_url": self.base})

    async def build_swap(
        self,
        quote_response: dict[str, Any],
        user_pubkey: str,
        prioritization_fee_lamports: int | None = None,
        compute_unit_price_micro_lamports: int | None = None,
    ) -> dict[str, Any]:
        logger.info("Starting swap build", extra={
            "input_mint": quote_response.get("inputMint", "unknown")[-8:],
            "output_mint": quote_response.get("outputMint", "unknown")[-8:],
            "amount": quote_response.get("inAmount"),
            "user_pubkey": user_pubkey[:8] + "...",
            "priority_fee": prioritization_fee_lamports,
        })

        try:
            # Build swap request payload
            payload = {
                "quoteResponse": quote_response,
                "userPublicKey": user_pubkey,
                "useSharedAccounts": True,
                "wrapAndUnwrapSol": True,
            }
            
            # Add optional parameters
            if prioritization_fee_lamports:
                payload["prioritizationFeeLamports"] = prioritization_fee_lamports
            if compute_unit_price_micro_lamports:
                payload["computeUnitPriceMicroLamports"] = compute_unit_price_micro_lamports
                payload["dynamicComputeUnitLimit"] = True

            async with httpx.AsyncClient(timeout=20) as client:
                # Get serialized transaction
                r = await client.post(f"{self.base}/swap", json=payload)
                logger.info("swap.response", extra={"status": r.status_code})
                r.raise_for_status()
                swap_data = r.json()
                
                if "swapTransaction" not in swap_data:
                    raise ValueError(f"invalid swap response: {list(swap_data.keys())}")

                tx_b64 = swap_data["swapTransaction"]

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
                signed_tx = tx.sign([kp])  # returns a new signed transaction
                signed_b64 = base64.b64encode(bytes(signed_tx)).decode()
                logger.info("tx.signed", extra={"len": len(signed_b64)})

                return {
                    "signed_transaction": signed_b64,
                    "last_valid_block_height": swap_data.get("lastValidBlockHeight"),
                    "prioritization_fee_lamports": swap_data.get("prioritizationFeeLamports")
                }
                
        except Exception as e:
            logger.error("Swap build failed", extra={"err": str(e)})
            raise
