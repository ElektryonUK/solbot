from pydantic import BaseModel
from functools import lru_cache
import os

class Settings(BaseModel):
    solana_rpc_url: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    jito_rpc_url: str | None = os.getenv("JITO_RPC_URL")
    user_keypair: str = os.getenv("USER_KEYPAIR", "")
    user_pubkey: str = os.getenv("USER_PUBKEY", "")
    environment: str = os.getenv("ENV", "dev")

@lru_cache(maxsize=1)
def get_settings() -> "Settings":
    return Settings()
