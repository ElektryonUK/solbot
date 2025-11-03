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
        self.base = os.getenv("JUP_BASE", "https://lite-api.jup.ag/ultra/v1")
        logger.info("JupiterSwap initialized", extra={"base_url": self.base})

    async def build_swap(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int,
        user_pubkey: str,
        prioritization_micro_lamports: int | None = None,
    ) -> dict[str, Any]:
        logger.info("Starting swap build", extra={
            "input_mint": input_mint,
            "output_mint": output_mint,
            "amount": amount,
            "slippage_bps": slippage_bps,
            "user_pubkey": user_pubkey[:8] + "...",
            "priority_fee": prioritization_micro_lamports,
        })

        try:
            # 1) Get order
            order_url = f"{self.base}/order"
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount),
                "slippageBps": slippage_bps,
                "taker": user_pubkey,
            }
            if prioritization_micro_lamports:
                params["priorityFee"] = prioritization_micro_lamports

            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(order_url, params=params)
                logger.info("order.response", extra={"status": r.status_code})
                r.raise_for_status()
                order = r.json()
                if "transaction" not in order or "requestId" not in order:
                    raise ValueError(f"invalid order: {order}")

                tx_b64 = order["transaction"]
                request_id = order["requestId"]

                # 2) Sign locally with solders
                kp_env = os.getenv("USER_KEYPAIR")
                if not kp_env:
                    raise ValueError("USER_KEYPAIR missing in env")
                if kp_env.startswith("["):
                    key_bytes = bytes(json.loads(kp_env))
                    kp = Keypair.from_bytes(key_bytes)
                else:
                    kp = Keypair.from_base58_string(kp_env)

                tx = Transaction.from_bytes(base64.b64decode(tx_b64))
                tx = tx.sign([kp])  # returns a new signed transaction
                signed_b64 = base64.b64encode(bytes(tx)).decode()
                logger.info("tx.signed", extra={"len": len(signed_b64)})

                # 3) Execute
                exec_url = f"{self.base}/execute"
                payload = {"signedTransaction": signed_b64, "requestId": request_id}
                exec_resp = await client.post(exec_url, json=payload)
                logger.info("execute.response", extra={"status": exec_resp.status_code})
                exec_resp.raise_for_status()
                return exec_resp.json()
        except Exception as e:
            logger.error("Swap build failed", extra={"err": str(e)})
            raise
