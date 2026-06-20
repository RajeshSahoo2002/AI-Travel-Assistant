# backend/a2a/registry.py
from typing import Dict, List, Optional
from .protocol import AgentCard, AgentCapability


class AgentRegistry:
    """Central registry — agents self-register; orchestrator discovers them."""

    def __init__(self):
        self._agents: Dict[str, AgentCard] = {}

    def register(self, card: AgentCard):
        self._agents[card.agent_id] = card

    def get(self, agent_id: str) -> Optional[AgentCard]:
        return self._agents.get(agent_id)

    def find_by_capability(self, cap: AgentCapability) -> List[AgentCard]:
        return [c for c in self._agents.values() if cap in c.capabilities]

    def all(self) -> List[Dict]:
        return [c.to_dict() for c in self._agents.values()]


agent_registry = AgentRegistry()
