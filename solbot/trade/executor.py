from __future__ import annotations
import os
from typing import TYPE_CHECKING
from solbot.core.logger import logger
from solbot.execution.jupiter_swap import JupiterSwap

if TYPE_CHECKING:
    from solbot.core.rpc import RpcPool
    from solbot.strategy.models import Plan

class Executor:
    def __init__(self, settings, rpc_pool: RpcPool) -> None:
        self.settings = settings
        self.rpc_pool = rpc_pool
        self.jupiter_swap = JupiterSwap()  # Instantiate for new API

    async def try_execute(self, plan: Plan) -> bool:
        if self.settings.DRY_RUN or self.settings.PAPER_TRADE:
            logger.info("paper/dry mode — not sending")
            return False
        
        try:
            for leg in plan.legs:
                swap = await self.jupiter_swap.build_swap(
                    input_mint=leg.input_mint,
                    output_mint=leg.output_mint,
                    amount=leg.input_amount,
                    slippage_bps=plan.max_slippage_bps,
                    user_pubkey=self.settings.USER_PUBKEY,
                    prioritization_micro_lamports=self.settings.PRIORITY_FEE_MICRO_LAMPORTS,
                )
                # TODO: Submit transaction via RPC or Jito
                logger.info("swap built", extra={"swap_instructions": len(swap.get("swapTransaction", ""))})
            return True
        except Exception as e:
            logger.error("execution failed", extra={"err": str(e)})
            return False
