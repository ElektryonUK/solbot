from __future__ import annotations
from typing import Optional
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair
from solders.signature import Signature
from solders.hash import Hash
from solders.instruction import Instruction
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price

class TxBuilder:
    @staticmethod
    def with_compute_budget(msg: MessageV0, cu: int, micro_lamports: int) -> MessageV0:
        i1 = set_compute_unit_limit(cu)
        i2 = set_compute_unit_price(micro_lamports)
        # Prepend compute budget instructions
        new_ix = [i1, i2] + list(msg.instructions)
        return MessageV0(
            msg.header,
            msg.account_keys,
            msg.recent_blockhash,
            tuple(new_ix),
            msg.address_table_lookups,
        )
