from __future__ import annotations
import json
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
        self.jupiter_swap = JupiterSwap()
        self.jupiter_swap.init_with_settings(settings)
        logger.info("Executor initialized", extra={
            "dry_run": settings.DRY_RUN,
            "paper_trade": settings.PAPER_TRADE,
            "user_pubkey": getattr(settings, 'user_pubkey', 'NOT_SET')[:8] + "..." if hasattr(settings, 'user_pubkey') else "NOT_SET"
        })

    async def try_execute(self, plan: Plan) -> bool:
        logger.info("execution.start: " + json.dumps({
            "input_mint": plan.input_mint[-8:],
            "output_mint": plan.output_mint[-8:], 
            "input_amount": plan.input_amount,
            "expected_pnl": plan.expected_pnl_usd,
            "dry_run": self.settings.DRY_RUN,
            "paper_trade": self.settings.PAPER_TRADE
        }))

        # Validate quote_response has routePlan
        if "routePlan" not in plan.quote_response or not plan.quote_response["routePlan"]:
            logger.error("fail.inspect: " + json.dumps({
                "reason": "Missing or empty routePlan in quote response",
                "quote_keys": list(plan.quote_response.keys())
            }))
            return False

        if self.settings.DRY_RUN or self.settings.PAPER_TRADE:
            logger.info("execution.skip: " + json.dumps({
                "reason": "paper/dry mode",
                "dry_run": self.settings.DRY_RUN,
                "paper_trade": self.settings.PAPER_TRADE
            }))
            return False

        try:
            swap_result = await self.jupiter_swap.build_swap(
                quote_response=plan.quote_response,
                user_pubkey=self.settings.user_pubkey,
                prioritization_fee_lamports=self.settings.PRIORITY_FEE_MICRO_LAMPORTS * 1000,  # Convert micro to regular lamports
                compute_unit_price_micro_lamports=self.settings.PRIORITY_FEE_MICRO_LAMPORTS,
            )

            logger.info("execution.success: " + json.dumps({
                "signed_tx_len": len(swap_result.get("signed_transaction", "")),
                "last_valid_block": swap_result.get("last_valid_block_height"),
                "priority_fee": swap_result.get("prioritization_fee_lamports")
            }))

            # TODO: Submit signed transaction to network via RPC
            # For now, just log success
            return True
            
        except Exception as e:
            logger.error("fail.inspect: " + json.dumps({
                "reason": "exception during swap build",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }))
            return False
