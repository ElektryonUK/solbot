from __future__ import annotations
import os
import httpx
from typing import Any

class JupiterSwap:
    def __init__(self):
        # Use same base as quoter for consistency
        self.base = os.getenv("JUP_BASE", "https://lite-api.jup.ag/swap/v1")

    async def build_swap(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int,
        user_pubkey: str,
        wrap_and_unwrap_sol: bool = True,
        dynamic_slippage: bool = False,
        prioritization_micro_lamports: int | None = None,
    ) -> dict[str, Any]:
        # New V1 API payload structure
        payload = {
            "inputMint": input_mint,
            "outputMint": output_mint, 
            "amount": str(amount),
            "slippageBps": slippage_bps,
            "userPublicKey": user_pubkey,
            "wrapAndUnwrapSol": wrap_and_unwrap_sol,
            "dynamicComputeUnitLimit": True,
            "priorityLevelWithMaxLamports": {
                "priorityLevel": "medium",
                "maxLamports": prioritization_micro_lamports or 0,
            }
        }
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{self.base}/swap", json=payload)
            r.raise_for_status()
            return r.json()
