# backend/a2a/protocol.py
"""
A2A (Agent-to-Agent) Protocol Implementation.

Agents communicate via typed A2AMessage envelopes over an async in-process
message bus. In production this bus would be Redis pub/sub or NATS.

Key concepts:
  AgentCard   — describes an agent's identity and capabilities (like a business card)
  A2AMessage  — typed envelope: from/to/capability/payload
  A2AMessageBus — async queue-per-agent; routes direct & broadcast messages
"""
import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


# ── Enums ────────────────────────────────────────────────────────────────────

class MessageType(str, Enum):
    REQUEST      = "request"
    RESPONSE     = "response"
    NOTIFICATION = "notification"
    BROADCAST    = "broadcast"
    ERROR        = "error"


class AgentCapability(str, Enum):
    FLIGHT_SEARCH    = "flight_search"
    HOTEL_SEARCH     = "hotel_search"
    ACTIVITY_SEARCH  = "activity_search"
    WEATHER_FORECAST = "weather_forecast"
    BUDGET_ANALYSIS  = "budget_analysis"
    ITINERARY_COMPOSE = "itinerary_compose"
    CONTEXT_SHARE    = "context_share"


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class A2AMessage:
    """Standard A2A protocol message envelope."""
    id:            str            = field(default_factory=lambda: str(uuid.uuid4()))
    from_agent:    str            = ""
    to_agent:      str            = ""       # empty string = broadcast
    message_type:  MessageType    = MessageType.NOTIFICATION
    capability:    str            = ""
    payload:       Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    timestamp:     str            = field(default_factory=lambda: datetime.utcnow().isoformat())
    priority:      int            = 5        # 1 (high) – 10 (low)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id":             self.id,
            "from_agent":     self.from_agent,
            "to_agent":       self.to_agent,
            "message_type":   self.message_type.value,
            "capability":     self.capability,
            "payload":        self.payload,
            "correlation_id": self.correlation_id,
            "timestamp":      self.timestamp,
        }


@dataclass
class AgentCard:
    """A2A Agent Card — agent identity + capabilities."""
    agent_id:     str
    name:         str
    description:  str
    version:      str                    = "1.0.0"
    capabilities: List[AgentCapability]  = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id":     self.agent_id,
            "name":         self.name,
            "description":  self.description,
            "version":      self.version,
            "capabilities": [c.value for c in self.capabilities],
        }


# ── Message Bus ──────────────────────────────────────────────────────────────

class A2AMessageBus:
    """
    In-process async message bus.
    Each agent owns a dedicated asyncio.Queue for incoming messages.
    """

    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._log:    List[A2AMessage]         = []

    # ── Registration ─────────────────────────────────────────────────────────

    def register(self, agent_id: str) -> asyncio.Queue:
        if agent_id not in self._queues:
            self._queues[agent_id] = asyncio.Queue(maxsize=200)
        return self._queues[agent_id]

    # ── Send ─────────────────────────────────────────────────────────────────

    async def send(self, msg: A2AMessage) -> None:
        self._log.append(msg)

        if not msg.to_agent or msg.message_type == MessageType.BROADCAST:
            # Broadcast — deliver to everyone except sender
            coros = [
                self._put(q, msg)
                for aid, q in self._queues.items()
                if aid != msg.from_agent
            ]
            if coros:
                await asyncio.gather(*coros, return_exceptions=True)
        else:
            q = self._queues.get(msg.to_agent)
            if q:
                await self._put(q, msg)

    async def _put(self, q: asyncio.Queue, msg: A2AMessage):
        try:
            await asyncio.wait_for(q.put(msg), timeout=3.0)
        except asyncio.TimeoutError:
            pass  # drop on full queue

    # ── Receive ──────────────────────────────────────────────────────────────

    async def receive(self, agent_id: str, timeout: float = 5.0) -> Optional[A2AMessage]:
        q = self._queues.get(agent_id)
        if not q:
            return None
        try:
            return await asyncio.wait_for(q.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    # ── Inspection ───────────────────────────────────────────────────────────

    def message_log(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self._log[-100:]]


# ── Singletons ───────────────────────────────────────────────────────────────

message_bus = A2AMessageBus()
