# backend/agents/base_agent.py
"""
Base class for all travel agents.
Handles: A2A messaging, LLM calls, self-registration.
"""
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.a2a import (
    A2AMessage, AgentCard, AgentCapability, MessageType,
    message_bus, agent_registry,
)
from backend.config import settings


def build_llm():
    """Return the configured LLM (Claude, GPT, or Groq)."""
    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model       = settings.llm_model,
            api_key     = settings.anthropic_api_key,
            temperature = 0.1,
            max_tokens  = 2048,
        )
    elif settings.llm_provider == "groq" and settings.groq_api_key:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model       = settings.llm_model,
            api_key     = settings.groq_api_key,
            temperature = 0.1,
            max_tokens  = 2048,
        )
    elif settings.openai_api_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=settings.llm_model if settings.llm_provider == "openai" else "gpt-4o", 
                          api_key=settings.openai_api_key,
                          temperature=0.1, max_tokens=2048)
    raise RuntimeError(
        "No LLM key found. Set GROQ_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY in .env"
    )


class BaseAgent(ABC):
    """
    Every agent:
      1. Registers an AgentCard in the A2A registry on init.
      2. Gets a dedicated inbox queue on the A2A message bus.
      3. Can call self.think() to invoke the LLM.
      4. Can call self.send_msg() / self.broadcast() to communicate via A2A.
      5. Must implement execute(state) -> dict.
    """

    def _init_(
        self,
        agent_id:     str,
        name:         str,
        description:  str,
        capabilities: List[AgentCapability],
    ):
        self.agent_id    = agent_id
        self.name        = name
        self.status      = "idle"
        self._llm        = None   # lazy-loaded

        # Register in A2A registry
        card = AgentCard(
            agent_id     = agent_id,
            name         = name,
            description  = description,
            capabilities = capabilities,
        )
        agent_registry.register(card)

        # Register on message bus (get personal inbox)
        message_bus.register(agent_id)

    # ── LLM (lazy) ───────────────────────────────────────────────────────────

    @property
    def llm(self):
        if self._llm is None:
            self._llm = build_llm()
        return self._llm

    async def think(self, system: str, user: str) -> str:
        from langchain_core.messages import SystemMessage, HumanMessage
        resp = await self.llm.ainvoke([SystemMessage(content=system), HumanMessage(content=user)])
        return resp.content

    # ── A2A helpers ──────────────────────────────────────────────────────────

    async def send_msg(
        self, to: str, capability: str, payload: Dict[str, Any],
        mtype: MessageType = MessageType.NOTIFICATION,
    ) -> str:
        msg = A2AMessage(
            from_agent   = self.agent_id,
            to_agent     = to,
            message_type = mtype,
            capability   = capability,
            payload      = payload,
        )
        await message_bus.send(msg)
        return msg.id

    async def broadcast(self, capability: str, payload: Dict[str, Any]):
        msg = A2AMessage(
            from_agent   = self.agent_id,
            to_agent     = "",
            message_type = MessageType.BROADCAST,
            capability   = capability,
            payload      = payload,
        )
        await message_bus.send(msg)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Override in each subclass to do the actual work."""

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Wraps execute() with status updates, A2A events, error handling."""
        self.status = "running"
        t0 = datetime.utcnow()

        await self.broadcast("context_share", {
            "event": "started", "agent": self.agent_id,
        })

        try:
            result = await self.execute(state)
            self.status = "completed"
            dur = (datetime.utcnow() - t0).total_seconds()
            await self.broadcast("context_share", {
                "event": "completed", "agent": self.agent_id, "duration": dur,
            })
            return result
        except Exception as exc:
            self.status = "error"
            await self.broadcast("context_share", {
                "event": "error", "agent": self.agent_id, "error": str(exc),
            })
            return {
                "errors": [f"[{self.agent_id}] {exc}"],
                "log":    [f"⚠️ {self.name} error: {exc}"],
            }