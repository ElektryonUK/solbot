from __future__ import annotations
from dataclasses import dataclass
import asyncio
import random
import time
from typing import Iterable
import httpx
from solbot.core.logger import logger
from solbot.core.env import Settings

@dataclass
class Endpoint:
    url: str
    latency_ms: float = 9999.0
    healthy: bool = True

class RpcPool:
    def __init__(self, settings: Settings):
        self._eps = [Endpoint(u) for u in settings.RPC_HTTPS]
        self._lock = asyncio.Lock()

    async def probe(self) -> None:
        async with httpx.AsyncClient(timeout=2) as client:
            tasks = []
            for ep in self._eps:
                tasks.append(self._probe_one(client, ep))
            await asyncio.gather(*tasks, return_exceptions=True)
        self._eps.sort(key=lambda e: (not e.healthy, e.latency_ms))
        logger.info("rpc probe", extra={"ordered": [e.url for e in self._eps]})

    async def _probe_one(self, client: httpx.AsyncClient, ep: Endpoint) -> None:
        t0 = time.perf_counter()
        try:
            r = await client.post(ep.url, json={"jsonrpc":"2.0","id":1,"method":"getHealth"})
            ep.healthy = r.status_code == 200 and (r.json().get("result") in ("ok", None))
        except Exception:  # noqa: BLE001
            ep.healthy = False
        ep.latency_ms = (time.perf_counter() - t0) * 1000

    async def best(self) -> str:
        if random.random() < 0.1:
            await self.probe()
        for ep in self._eps:
            if ep.healthy:
                return ep.url
        return self._eps[0].url
