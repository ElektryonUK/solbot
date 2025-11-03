from __future__ import annotations
import base64
import httpx
from typing import Any

class JitoBundles:
    def __init__(self, block_engine_url: str, auth: str | None = None):
        self.url = block_engine_url.rstrip("/")
        self.auth = auth

    async def send_bundle(self, transactions: list[str]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.auth:
            headers["Authorization"] = f"Bearer {self.auth}"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendBundle",
            "params": [transactions],
        }
        async with httpx.AsyncClient(timeout=10, headers=headers) as client:
            r = await client.post(self.url, json=payload)
            r.raise_for_status()
            return r.json()
