from __future__ import annotations
import asyncio
import time
from typing import Sequence
from solbot.core.env import Settings
from solbot.core.logger import logger
from solbot.core.rpc import RpcPool
from solbot.discovery import DiscoveryService
from solbot.quoter import JupiterQuoter
from solbot.strategy.models import Plan
from solbot.strategy.two_leg_spread import TwoLegSpread
from solbot.strategy.stable_delta import StableDelta
from solbot.trade.executor import Executor
from solbot.risk.daily_guard import DailyLossGuard


async def run_supervisor(settings: Settings) -> None:
    rpc_pool = RpcPool(settings)
    discovery = DiscoveryService(settings, rpc_pool)
    quoter = JupiterQuoter(settings)
    executor = Executor(settings, rpc_pool)
    guard = DailyLossGuard(settings.MAX_DAILY_LOSS_USD)

    strategies = [
        TwoLegSpread(settings, discovery, quoter),
        StableDelta(settings, discovery, quoter),
    ]

    await discovery.refresh()
    logger.info("Discovery primed", extra={"pairs": discovery.watch_count})

    failures = 0
    while True:
        try:
            if guard.exceeded():
                logger.error("Daily loss limit exceeded — pausing execution")
                await asyncio.sleep(60)
                continue

            t0 = time.perf_counter()
            plans: list[Plan] = []
            results = await asyncio.gather(
                *[s.propose_plans() for s in strategies], return_exceptions=True
            )
            for res in results:
                if isinstance(res, Exception):
                    logger.warning("strategy error", extra={"err": str(res)})
                    continue
                plans.extend(res)

            # Log plan summaries for visibility
            if plans:
                summary = [
                    {
                        "route": p.route,
                        "notional_usd": round(p.notional_usd, 4),
                        "exp_pnl": round(p.expected_pnl_usd, 6),
                        "slip_bps": p.max_slippage_bps,
                    }
                    for p in plans
                ]
                logger.info("plans", extra={"count": len(plans), "items": summary})

            plans.sort(key=lambda p: p.expected_pnl_usd, reverse=True)

            executed = False
            for plan in plans:
                if plan.expected_pnl_usd < settings.MIN_PROFIT_USD:
                    logger.info(
                        "filtered plan",
                        extra={
                            "reason": "below_min_profit",
                            "min": settings.MIN_PROFIT_USD,
                            "exp_pnl": round(plan.expected_pnl_usd, 6),
                            "route": plan.route,
                        },
                    )
                    continue
                logger.info("attempting plan", extra={"route": plan.route, "exp_pnl": round(plan.expected_pnl_usd, 6)})
                ok = await executor.try_execute(plan)
                logger.info("execution result", extra={"ok": ok})
                if ok:
                    guard.add_pnl(plan.expected_pnl_usd)
                    executed = True
                    break

            dt = (time.perf_counter() - t0) * 1000
            await asyncio.sleep(max(0.05, (settings.SCAN_INTERVAL_MS - dt) / 1000))
            failures = 0
        except Exception as e:  # noqa: BLE001
            failures += 1
            logger.exception("supervisor loop error", extra={"failures": failures, "err": str(e)})
            if failures >= settings.PAUSE_AFTER_FAILS:
                logger.error("pausing after repeated failures")
                await asyncio.sleep(5)
                failures = 0
