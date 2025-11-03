from __future__ import annotations
from typing import List
from solbot.core.env import Settings
from solbot.discovery import DiscoveryService
from solbot.quoter import JupiterQuoter
from solbot.strategy.models import Plan

class StableDelta:
    def __init__(self, settings: Settings, discovery: DiscoveryService, quoter: JupiterQuoter):
        self.s = settings
        self.d = discovery
        self.q = quoter

    async def propose_plans(self) -> List[Plan]:
        # placeholder: no stable pool modeling yet
        return []
