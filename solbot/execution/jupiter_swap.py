from __future__ import annotations
import httpx
from typing import Any

class JupiterSwap:
    base = "https://quote-api.jup.ag/v6"

    @staticmethod
    async def build_swap(
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int,
        user_pubkey: str,
        wrap_and_unwrap_sol: bool = True,
        dynamic_slippage: bool = False,
        prioritization_micro_lamports: int | None = None,
    ) -> dict[str, Any]:
        payload = {
            "quoteResponse": None,  # can be set when we pass pre-fetched quote
            "userPublicKey": user_pubkey,
            "wrapAndUnwrapSol": wrap_and_unwrap_sol,
            "slippageBps": slippage_bps,
            "dynamicSlippage": dynamic_slippage,
        }
        if prioritization_micro_lamports is not None:
            payload["prioritizationFeeLamports"] = prioritization_micro_lamports
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{JupiterSwap.base}/swap", json=payload)
            r.raise_for_status()
            return r.json()
