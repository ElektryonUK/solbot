from __future__ import annotations
import os
import httpx
from solbot.core.logger import logger

OFFLINE_PAIRS = [
    {"base": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "quote": "So11111111111111111111111111111111111111112"}, # USDC/SOL
    {"base": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", "quote": "So11111111111111111111111111111111111111112"}, # USDT/SOL
]

# Modern token list endpoints (Jupiter ecosystem tokens)
TOKEN_SOURCES = [
    "https://cache.jup.ag/tokens",  # Jupiter's token cache (primary)
    "https://token.jup.ag/strict", # Strict list (backup)
]

class DiscoveryService:
    def __init__(self, settings, rpc_pool):
        self.settings = settings
        self.rpc_pool = rpc_pool
        self.watchlist: list[dict] = []

    @property
    def watch_count(self) -> int:
        return len(self.watchlist)

    async def refresh(self) -> None:
        if os.getenv("OFFLINE_DISCOVERY", "false").lower() == "true":
            self.watchlist = OFFLINE_PAIRS
            logger.info("discovery.offline", extra={"pairs": len(self.watchlist)})
            return
        
        tokens = []
        for url in TOKEN_SOURCES:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.get(url)
                    r.raise_for_status()
                    tokens = r.json()
                    logger.info("discovery.online", extra={"source": url, "tokens": len(tokens)})
                    break
            except Exception as e:
                logger.warning("token source failed", extra={"url": url, "err": str(e)})
                continue
        
        if not tokens:
            logger.warning("all token sources failed, using offline pairs")
            self.watchlist = OFFLINE_PAIRS
            return
            
        majors = {"USDC", "USDT", "SOL", "mSOL", "JITOSOL", "wBTC", "ETH"}
        by_symbol = [t for t in tokens if t.get("symbol") in majors]
        mints = [t["address"] for t in by_symbol]
        self.watchlist = [
            {"base": b, "quote": q} for i, b in enumerate(mints) for q in mints[i+1:]
        ][:120]
