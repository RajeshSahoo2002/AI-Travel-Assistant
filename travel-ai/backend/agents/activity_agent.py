# backend/agents/activity_agent.py
import json, re
from typing import Any, Dict, List
from backend.agents.base_agent import BaseAgent
from backend.a2a import AgentCapability
from backend.mcp_servers.amadeus_mcp import amadeus_mcp


class ActivityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "activity_agent", "🎯 Activity Agent",
            "Curates activities using LLM + Amadeus MCP",
            [AgentCapability.ACTIVITY_SEARCH],
        )

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        p         = state["preferences"]
        dest      = p["destination"]
        interests = p.get("interests", ["sightseeing"])
        log       = [f"🎯 Activity Agent: Finding activities in {dest} for {', '.join(interests)}..."]

        result     = await amadeus_mcp.call_tool("get_activities", {"destination": dest})
        activities = result.get("data", [])

        if activities:
            activities = await self._curate(activities, interests, p)

        log.append(f"🎯 Activity Agent: Curated {len(activities)} activities matching your interests.")

        return {
            "activities": activities,
            "agent_statuses": {**state.get("agent_statuses", {}), "activity_agent": "completed"},
            "log": log,
        }

    async def _curate(self, activities: List[Dict], interests: List[str], prefs: Dict) -> List[Dict]:
        system = "You are a travel expert. Pick and rank activities matching traveller interests. Return ONLY a JSON array of activity IDs, best first."
        user   = (
            f"Interests: {', '.join(interests)}\nStyle: {prefs.get('travel_style','comfort')}\n\n"
            + json.dumps([{"id":a["id"],"name":a["name"],"type":a["type"],"price":a["price"]} for a in activities])
        )
        try:
            raw  = await self.think(system, user)
            ids  = json.loads(re.search(r'\[.*?\]', raw, re.DOTALL).group())
            lut  = {a["id"]: a for a in activities}
            ranked = [lut[i] for i in ids if i in lut]
            ranked += [a for a in activities if a["id"] not in set(ids)]
            return ranked
        except Exception:
            return activities
