#!/usr/bin/env python3
import asyncio
import statistics
import time
import httpx

ENDPOINTS = [
    "https://api.mainnet-beta.solana.com",
]

async def ping(url: str) -> float:
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            await client.post(url, json={"jsonrpc":"2.0","id":1,"method":"getHealth"})
    except Exception:
        pass
    return (time.perf_counter() - t0) * 1000

async def main():
    samples = {u: [] for u in ENDPOINTS}
    for _ in range(10):
        rs = await asyncio.gather(*[ping(u) for u in ENDPOINTS])
        for u, ms in zip(ENDPOINTS, rs):
            samples[u].append(ms)
    for u, arr in samples.items():
        print(u, "median(ms)=", round(statistics.median(arr),1))

if __name__ == "__main__":
    asyncio.run(main())
