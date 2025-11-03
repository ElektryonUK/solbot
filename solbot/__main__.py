#!/usr/bin/env python3
import asyncio
from solbot.core.env import Settings
from solbot.core.logger import logger
from solbot.services.supervisor import run_supervisor


def main() -> None:
    settings = Settings()
    logger.info("Starting Solbot", extra={"network": settings.solana_rpc_url})
    asyncio.run(run_supervisor(settings))
