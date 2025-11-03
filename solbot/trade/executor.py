from __future__ import annotations
import base64
from typing import Any
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.hash import Hash
from solbot.core.env import Settings
from solbot.core.logger import logger
from solbot.execution.tx_builder import TxBuilder
from solbot.execution.jupiter_swap import JupiterSwap
from solbot.execution.jito import JitoBundles
from solbot.strategy.models import Plan

class Executor:
    def __init__(self, settings: Settings, rpc_pool):
        self.s = settings
        self.rpc_pool = rpc_pool

    async def try_execute(self, plan: Plan) -> bool:
        if self.s.DRY_RUN or self.s.PAPER_TRADE:
            logger.info("paper/dry mode — not sending", extra=plan.model_dump())
            return False

        if not self.s.user_keypair or not self.s.user_pubkey:
            logger.error("missing USER_KEYPAIR/USER_PUBKEY")
            return False

        # 1) Build Jupiter swap transaction (assumes plan.route encodes input/output mints)
        # NOTE: For MVP we only handle single swap route; multi-leg will chain
        input_mint, output_mint = plan.route[0], plan.route[-1]
        swap = await JupiterSwap.build_swap(
            input_mint=input_mint,
            output_mint=output_mint,
            amount=int(plan.notional_usd * 1_000_000),  # placeholder: treat as USDC 6dp
            slippage_bps=min(plan.max_slippage_bps, self.s.MAX_ROUTE_SLIPPAGE_BPS),
            user_pubkey=self.s.user_pubkey,
            prioritization_micro_lamports=self.s.PRIORITY_FEE_MICRO_LAMPORTS,
        )
        swap_tx_b64 = swap.get("swapTransaction")
        if not swap_tx_b64:
            logger.error("jupiter build returned no swapTransaction")
            return False

        # 2) Decode, insert compute budget, sign
        raw = base64.b64decode(swap_tx_b64)
        tx = VersionedTransaction.from_bytes(raw)
        msg: MessageV0 = tx.message  # type: ignore[assignment]
        msg2 = TxBuilder.with_compute_budget(msg, self.s.TARGET_CU, self.s.PRIORITY_FEE_MICRO_LAMPORTS)
        kp = Keypair.from_base58_string(self.s.user_keypair)
        # Note: recreate a signed tx from updated message
        recent = Hash(msg2.recent_blockhash)
        tx2 = VersionedTransaction.populate(msg2, [kp])

        # 3) Submit via Jito bundle if configured, else standard RPC
        tx_b64 = base64.b64encode(bytes(tx2)).decode()
        if self.s.JITO_BLOCK_ENGINE_URL:
            jito = JitoBundles(self.s.JITO_BLOCK_ENGINE_URL, self.s.JITO_AUTH)
            try:
                res = await jito.send_bundle([tx_b64])
                logger.info("bundle submitted", extra=res)
                return True
            except Exception as e:  # noqa: BLE001
                logger.warning("jito bundle failed, falling back", extra={"err": str(e)})

        rpc = await self.rpc_pool.best()
        async with AsyncClient(rpc) as client:
            r = await client.send_raw_transaction(bytes(tx2))
            logger.info("tx sent", extra={"sig": str(r.value)})
            return True
