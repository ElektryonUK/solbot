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

            plans.sort(key=lambda p: p.expected_pnl_usd, reverse=True)

            for plan in plans:
                if plan.expected_pnl_usd < settings.MIN_PROFIT_USD:
                    continue
                ok = await executor.try_execute(plan)
                if ok:
                    guard.add_pnl(plan.expected_pnl_usd)
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
