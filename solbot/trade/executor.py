from __future__ import annotations
import json
from typing import TYPE_CHECKING
from solbot.core.logger import logger
from solbot.execution.jupiter_swap import JupiterSwap

if TYPE_CHECKING:
    from solbot.core.rpc import RpcPool

# Wide-net aliases to catch most bot schemas
ALIASES_IN = [
    "input_mint", "base", "base_mint", "from_mint", "mint_in", "in_mint",
    "src_mint", "token_in", "in_token", "in_symbol", "base_token_mint", "base_token"
]
ALIASES_OUT = [
    "output_mint", "quote", "quote_mint", "to_mint", "mint_out", "out_mint",
    "dst_mint", "token_out", "out_token", "out_symbol", "quote_token_mint", "quote_token"
]
ALIASES_AMT = [
    "input_amount", "amount", "amount_in", "base_amount", "in_amount",
    "qty_in", "notional_in", "size", "base_size", "amount_base"
]

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

    def _inspect_preview(self, d: dict):
        try:
            keys = list(d.keys())[:15]
            preview = {}
            for k in keys:
                v = d.get(k)
                if isinstance(v, (str, int, float)):
                    preview[k] = (v[:12] + "...") if isinstance(v, str) and len(v) > 15 else v
                else:
                    preview[k] = type(v).__name__
            return json.dumps({"keys": list(d.keys()), "preview": preview})
        except Exception:
            return json.dumps({"repr": repr(d)})

    async def try_execute(self, plan) -> bool:
        # Build a dict representation for inspection
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
            plan_repr = {"repr": repr(plan)}

        logger.info("plan.inspect: " + self._inspect_preview(plan_repr))

        # Discover legs or single-leg candidate
        legs = getattr(plan, "legs", None)
        if legs is None and isinstance(plan_repr, dict):
            candidate = {
                "input_mint": self._get_first(plan_repr, ALIASES_IN),
                "output_mint": self._get_first(plan_repr, ALIASES_OUT),
                "input_amount": self._get_first(plan_repr, ALIASES_AMT),
            }
            logger.info("candidate.inspect: " + json.dumps(candidate))
            if all(candidate.values()):
                legs = [candidate]

        if legs is None:
            logger.error("fail.inspect: " + json.dumps({
                "reason": "No legs and no recognizable single-leg fields",
                "plan_keys": list(plan_repr.keys()) if isinstance(plan_repr, dict) else type(plan_repr).__name__
            }))
            return False

        logger.info("execution.start: " + json.dumps({
            "legs_len": len(legs),
            "max_slippage_bps": getattr(plan, "max_slippage_bps", None),
            "dry_run": self.settings.DRY_RUN,
            "paper_trade": self.settings.PAPER_TRADE
        }))

        if self.settings.DRY_RUN or self.settings.PAPER_TRADE:
            logger.info("execution.skip: " + json.dumps({
                "reason": "paper/dry mode",
                "dry_run": self.settings.DRY_RUN,
                "paper_trade": self.settings.PAPER_TRADE
            }))
            return False

        try:
            for i, leg in enumerate(legs):
                lm_src = leg if isinstance(leg, dict) else (getattr(leg, 'model_dump', lambda: None)() or getattr(leg, '__dict__', {}))
                lm = {
                    "input_mint": self._get_first(lm_src, ALIASES_IN) or getattr(leg, "input_mint", None) or getattr(leg, "base", None),
                    "output_mint": self._get_first(lm_src, ALIASES_OUT) or getattr(leg, "output_mint", None) or getattr(leg, "quote", None),
                    "input_amount": self._get_first(lm_src, ALIASES_AMT) or getattr(leg, "input_amount", None) or getattr(leg, "amount", None),
                }
                logger.info("leg.inspect: " + json.dumps({"idx": i+1, **lm}))

                if not (lm.get("input_mint") and lm.get("output_mint") and lm.get("input_amount")):
                    logger.error("fail.inspect: " + json.dumps({
                        "reason": "Missing required fields on leg",
                        "leg": lm
                    }))
                    continue

                swap_result = await self.jupiter_swap.build_swap(
                    input_mint=lm["input_mint"],
                    output_mint=lm["output_mint"],
                    amount=int(lm["input_amount"]),
                    slippage_bps=int(getattr(plan, "max_slippage_bps", 100)),
                    user_pubkey=self.settings.USER_PUBKEY,
                    prioritization_micro_lamports=getattr(self.settings, "PRIORITY_FEE_MICRO_LAMPORTS", None),
                )

                logger.info("leg.success: " + json.dumps({
                    "idx": i+1,
                    "result_keys": list(swap_result.keys()) if isinstance(swap_result, dict) else type(swap_result).__name__
                }))

            return True
        except Exception as e:
            logger.error("fail.inspect: " + json.dumps({
                "reason": "exception",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }))
            return False
