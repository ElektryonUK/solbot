from pydantic import BaseModel
from functools import lru_cache
import os
from typing import List

class Settings(BaseModel):
    # Core
    solana_rpc_url: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    jito_rpc_url: str | None = os.getenv("JITO_RPC_URL")
    user_keypair: str = os.getenv("USER_KEYPAIR", "")
    user_pubkey: str = os.getenv("USER_PUBKEY", "")
    environment: str = os.getenv("ENV", "dev")

    # Jupiter Ultra API (authenticated)
    JUP_API_KEY: str = os.getenv("JUP_API_KEY", "")
    JUP_ORDER_BASE: str = os.getenv("JUP_ORDER_BASE", "https://api.jup.ag/ultra/v1")
    JUP_EXECUTE_BASE: str = os.getenv("JUP_EXECUTE_BASE", "https://api.jup.ag/ultra/v1")

    # Pools & scanning
    RPC_HTTPS: List[str] = os.getenv("RPC_HTTPS", "").split(",") if os.getenv("RPC_HTTPS") else ["https://api.mainnet-beta.solana.com"]
    SCAN_INTERVAL_MS: int = int(os.getenv("SCAN_INTERVAL_MS", "200"))
    PAUSE_AFTER_FAILS: int = int(os.getenv("PAUSE_AFTER_FAILS", "5"))

    # Risk & profit
    MIN_PROFIT_USD: float = float(os.getenv("MIN_PROFIT_USD", "0.50"))
    MAX_NOTIONAL_USD: float = float(os.getenv("MAX_NOTIONAL_USD", "50"))
    MAX_DAILY_LOSS_USD: float = float(os.getenv("MAX_DAILY_LOSS_USD", "25"))

    # Slippage
    SLIPPAGE_BPS_PER_LEG: int = int(os.getenv("SLIPPAGE_BPS_PER_LEG", "25"))
    MAX_ROUTE_SLIPPAGE_BPS: int = int(os.getenv("MAX_ROUTE_SLIPPAGE_BPS", "60"))

    # Compute budget / Priority fees
    TARGET_CU: int = int(os.getenv("TARGET_CU", "1200000"))
    PRIORITY_FEE_MICRO_LAMPORTS: int = int(os.getenv("PRIORITY_FEE_MICRO_LAMPORTS", "1500"))

    # Modes
    DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    PAPER_TRADE: bool = os.getenv("PAPER_TRADE", "true").lower() == "true"

    # Jito
    JITO_BLOCK_ENGINE_URL: str | None = os.getenv("JITO_BLOCK_ENGINE_URL")
    JITO_AUTH: str | None = os.getenv("JITO_AUTH")

@lru_cache(maxsize=1)
def get_settings() -> "Settings":
    return Settings()
