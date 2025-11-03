from __future__ annotations
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
        plans: List[Plan] = []
        # Simple seed: no-op for now. Next push will use quote API to compute spreads.
        return plans
