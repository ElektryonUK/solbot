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
            "user_pubkey": getattr(settings, 'user_pubkey', 'NOT_SET')[:8] + "..." if hasattr(settings, 'user_pubkey') else "NOT_SET",
            "api_key_set": bool(getattr(settings, 'JUP_API_KEY', ''))
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

        # Validate Ultra order response has required fields
        if "transaction" not in plan.quote_response or "requestId" not in plan.quote_response:
            logger.error("fail.inspect: " + json.dumps({
                "reason": "Missing transaction or requestId in Ultra order response",
                "response_keys": list(plan.quote_response.keys())
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
            # Ultra API: quote_response contains pre-built transaction
            execute_result = await self.jupiter_swap.build_swap(
                quote_response=plan.quote_response,
                user_pubkey=self.settings.user_pubkey,
                prioritization_fee_lamports=self.settings.PRIORITY_FEE_MICRO_LAMPORTS * 1000,
                compute_unit_price_micro_lamports=self.settings.PRIORITY_FEE_MICRO_LAMPORTS,
            )

            logger.info("execution.success: " + json.dumps({
                "status": execute_result.get("status"),
                "signature": execute_result.get("signature", "")[:16] + "..." if execute_result.get("signature") else "none",
                "request_id": plan.quote_response.get("requestId")
            }))

            return True
            
        except Exception as e:
            logger.error("fail.inspect: " + json.dumps({
                "reason": "exception during Ultra execution",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }))
            return False
