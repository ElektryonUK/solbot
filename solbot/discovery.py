from __future__ import annotations
import asyncio
import httpx
from solbot.core.env import Settings
from solbot.core.logger import logger

class DiscoveryService:
    def __init__(self, settings: Settings, rpc_pool):
        self.settings = settings
        self.rpc_pool = rpc_pool
        self.watchlist: list[dict] = []

    @property
    def watch_count(self) -> int:
        return len(self.watchlist)

    async def refresh(self) -> None:
        # Minimal viable discovery: pull Jupiter tokens to prime universe
        url = "https://tokens.jup.ag/tokens?filter=verified"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
            r.raise_for_status()
            tokens = r.json()
        # Keep a small subset (stable + SOL and majors) to start
        majors = {"USDC", "USDT", "SOL", "mSOL", "JITOSOL", "wBTC", "ETH"}
        by_symbol = [t for t in tokens if t.get("symbol") in majors]
        # Build simple pairs among majors
        mints = [t["address"] for t in by_symbol]
        self.watchlist = [
            {"base": b, "quote": q} for i, b in enumerate(mints) for q in mints[i+1:]
        ][:120]
        logger.info("discovery.refresh", extra={"pairs": len(self.watchlist)})
