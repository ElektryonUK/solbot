from __future__ import annotations
from typing import TYPE_CHECKING
from solbot.core.logger import logger
from solbot.execution.jupiter_swap import JupiterSwap

if TYPE_CHECKING:
    from solbot.core.rpc import RpcPool

class Executor:
    def __init__(self, settings, rpc_pool: RpcPool) -> None:
        self.settings = settings
        self.rpc_pool = rpc_pool
        self.jupiter_swap = JupiterSwap()
        logger.info("Executor initialized", extra={
            "dry_run": settings.DRY_RUN,
            "paper_trade": settings.PAPER_TRADE,
            "user_pubkey": getattr(settings, 'USER_PUBKEY', 'NOT_SET')[:8] + "..." if hasattr(settings, 'USER_PUBKEY') else "NOT_SET"
        })

    async def try_execute(self, plan) -> bool:
        # Defensive structure discovery
        legs = getattr(plan, "legs", None)
        if legs is None:
            # Try common single-plan fields
            candidate = {
                "input_mint": getattr(plan, "input_mint", None) or getattr(plan, "base", None),
                "output_mint": getattr(plan, "output_mint", None) or getattr(plan, "quote", None),
                "input_amount": getattr(plan, "amount", None) or getattr(plan, "input_amount", None),
            }
            if all(candidate.values()):
                legs = [candidate]
            else:
                # Last resort: log structure and skip
                logger.error("execution failed", extra={
                    "error_type": "StructureError",
                    "error_message": "Plan has no legs and no recognizable single-leg fields",
                    "plan_repr": repr(plan)
                })
                return False

        logger.info("Execution attempt started", extra={
            "plan_legs": len(legs),
            "max_slippage_bps": getattr(plan, "max_slippage_bps", None),
            "dry_run": self.settings.DRY_RUN,
            "paper_trade": self.settings.PAPER_TRADE
        })

        if self.settings.DRY_RUN or self.settings.PAPER_TRADE:
            logger.info("paper/dry mode — not sending")
            return False

        try:
            for i, leg in enumerate(legs):
                # Support both dict-like and object-like legs
                lm = leg if isinstance(leg, dict) else {
                    "input_mint": getattr(leg, "input_mint", None) or getattr(leg, "base", None),
                    "output_mint": getattr(leg, "output_mint", None) or getattr(leg, "quote", None),
                    "input_amount": getattr(leg, "input_amount", None) or getattr(leg, "amount", None),
                }
                logger.info(f"Executing leg {i+1}/{len(legs)}", extra=lm)

                if not (lm.get("input_mint") and lm.get("output_mint") and lm.get("input_amount")):
                    logger.error("execution failed", extra={
                        "error_type": "LegMappingError",
                        "error_message": "Missing required fields on leg",
                        "leg": lm
                    })
                    continue

                swap_result = await self.jupiter_swap.build_swap(
                    input_mint=lm["input_mint"],
                    output_mint=lm["output_mint"],
                    amount=int(lm["input_amount"]),
                    slippage_bps=int(getattr(plan, "max_slippage_bps", 100)),
                    user_pubkey=self.settings.USER_PUBKEY,
                    prioritization_micro_lamports=getattr(self.settings, "PRIORITY_FEE_MICRO_LAMPORTS", None),
                )

                logger.info(f"Leg {i+1} executed successfully", extra={
                    "swap_result_keys": list(swap_result.keys()) if isinstance(swap_result, dict) else type(swap_result).__name__
                })

            return True
        except Exception as e:
            logger.error("execution failed", extra={
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            return False
