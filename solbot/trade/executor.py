from __future__ import annotations
from typing import TYPE_CHECKING
from solbot.core.logger import logger
from solbot.execution.jupiter_swap import JupiterSwap

if TYPE_CHECKING:
    from solbot.core.rpc import RpcPool

ALIASES_IN = ["input_mint", "base", "base_mint", "from_mint", "mint_in", "in_mint"]
ALIASES_OUT = ["output_mint", "quote", "quote_mint", "to_mint", "mint_out", "out_mint"]
ALIASES_AMT = ["input_amount", "amount", "amount_in", "base_amount", "in_amount"]

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

    def _get_first(self, obj: dict, keys: list[str]):
        for k in keys:
            v = obj.get(k)
            if v is not None:
                return v
        return None

    async def try_execute(self, plan) -> bool:
        # Log raw plan structure for debugging
        plan_repr = None
        try:
            if hasattr(plan, 'model_dump'):
                plan_repr = plan.model_dump()
            elif hasattr(plan, 'dict'):
                plan_repr = plan.dict()
            elif isinstance(plan, dict):
                plan_repr = plan
            else:
                plan_repr = plan.__dict__
        except Exception:
            plan_repr = repr(plan)
        logger.info("plan.structure", extra={"plan": plan_repr})

        # Defensive structure discovery
        legs = getattr(plan, "legs", None)
        if legs is None and isinstance(plan_repr, dict):
            candidate = {
                "input_mint": self._get_first(plan_repr, ALIASES_IN),
                "output_mint": self._get_first(plan_repr, ALIASES_OUT),
                "input_amount": self._get_first(plan_repr, ALIASES_AMT),
            }
            logger.info("plan.single_candidate", extra=candidate)
            if all(candidate.values()):
                legs = [candidate]

        if legs is None:
            logger.error("execution.failed", extra={
                "reason": "No legs and no recognizable single-leg fields",
                "plan_keys": list(plan_repr.keys()) if isinstance(plan_repr, dict) else type(plan_repr).__name__
            })
            return False

        logger.info("execution.start", extra={
            "legs_len": len(legs),
            "max_slippage_bps": getattr(plan, "max_slippage_bps", None),
            "dry_run": self.settings.DRY_RUN,
            "paper_trade": self.settings.PAPER_TRADE
        })

        if self.settings.DRY_RUN or self.settings.PAPER_TRADE:
            logger.info("execution.skip", extra={
                "reason": "paper/dry mode",
                "dry_run": self.settings.DRY_RUN,
                "paper_trade": self.settings.PAPER_TRADE
            })
            return False

        try:
            for i, leg in enumerate(legs):
                # Support dict or object
                if isinstance(leg, dict):
                    lm_src = leg
                else:
                    # build dict from object
                    lm_src = getattr(leg, 'model_dump', lambda: None)() or getattr(leg, '__dict__', {})

                lm = {
                    "input_mint": self._get_first(lm_src, ALIASES_IN) or getattr(leg, "input_mint", None) or getattr(leg, "base", None),
                    "output_mint": self._get_first(lm_src, ALIASES_OUT) or getattr(leg, "output_mint", None) or getattr(leg, "quote", None),
                    "input_amount": self._get_first(lm_src, ALIASES_AMT) or getattr(leg, "input_amount", None) or getattr(leg, "amount", None),
                }
                logger.info("leg.mapped", extra={"idx": i+1, "len": len(legs), **lm})

                if not (lm.get("input_mint") and lm.get("output_mint") and lm.get("input_amount")):
                    logger.error("execution.failed", extra={
                        "reason": "Missing required fields on leg",
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

                logger.info("leg.success", extra={
                    "idx": i+1,
                    "result_keys": list(swap_result.keys()) if isinstance(swap_result, dict) else type(swap_result).__name__
                })

            return True
        except Exception as e:
            logger.error("execution.failed", extra={
                "reason": "exception",
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            return False
