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
        logger.info("Executor initialized", extra={
            "dry_run": settings.DRY_RUN,
            "paper_trade": settings.PAPER_TRADE,
            "user_pubkey": getattr(settings, 'USER_PUBKEY', 'NOT_SET')[:8] + "..." if hasattr(settings, 'USER_PUBKEY') else "NOT_SET"
        })

    async def try_execute(self, plan: Plan) -> bool:
        logger.info("Execution attempt started", extra={
            "plan_legs": len(plan.legs),
            "max_slippage_bps": plan.max_slippage_bps,
            "dry_run": self.settings.DRY_RUN,
            "paper_trade": self.settings.PAPER_TRADE
        })
        
        if self.settings.DRY_RUN or self.settings.PAPER_TRADE:
            logger.info("paper/dry mode — not sending")
            return False
        
        try:
            logger.info("Attempting live execution", extra={"legs_to_execute": len(plan.legs)})
            
            for i, leg in enumerate(plan.legs):
                logger.info(f"Executing leg {i+1}/{len(plan.legs)}", extra={
                    "input_mint": leg.input_mint,
                    "output_mint": leg.output_mint,
                    "input_amount": leg.input_amount
                })
                
                swap_result = await self.jupiter_swap.build_swap(
                    input_mint=leg.input_mint,
                    output_mint=leg.output_mint,
                    amount=leg.input_amount,
                    slippage_bps=plan.max_slippage_bps,
                    user_pubkey=self.settings.USER_PUBKEY,
                    prioritization_micro_lamports=self.settings.PRIORITY_FEE_MICRO_LAMPORTS,
                )
                
                logger.info(f"Leg {i+1} executed successfully", extra={
                    "swap_result_keys": list(swap_result.keys()) if swap_result else []
                })
                
            logger.info("All legs executed successfully")
            return True
            
        except Exception as e:
            logger.error("execution failed", extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "plan_legs": len(plan.legs)
            })
            return False
