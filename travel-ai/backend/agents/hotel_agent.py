# backend/agents/hotel_agent.py
from typing import Any, Dict
from backend.agents.base_agent import BaseAgent
from backend.a2a import AgentCapability
from backend.mcp_servers.amadeus_mcp import amadeus_mcp


class HotelAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "hotel_agent", "🏨 Hotel Agent",
            "Finds and recommends hotels via Amadeus MCP",
            [AgentCapability.HOTEL_SEARCH],
        )

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        p    = state["preferences"]
        dest = p["destination"]
        log  = [f"🏨 Hotel Agent: Searching hotels in {dest}..."]

        code_res  = await amadeus_mcp.call_tool("get_city_code", {"city": dest})
        city_code = code_res.get("code", dest[:3].upper())

        result = await amadeus_mcp.call_tool("search_hotels", {
            "city_code":   city_code,
            "check_in":    p["departure_date"],
            "check_out":   p.get("return_date", p["departure_date"]),
            "adults":      p.get("adults", 1),
            "max_results": 5,
        })
        hotels = result.get("data", [])

        # Filter by travel style
        style = p.get("travel_style", "comfort")
        stars_range = {"budget": (2, 3), "comfort": (3, 4), "luxury": (4, 5)}.get(style, (3, 5))
        filtered = [h for h in hotels if stars_range[0] <= h.get("stars", 3) <= stars_range[1]]
        hotels   = filtered or hotels

        log.append(f"🏨 Hotel Agent: Found {len(hotels)} hotels. Recommended: {hotels[0]['name']} ({hotels[0]['stars']}⭐)" if hotels else "🏨 Hotel Agent: Hotels loaded.")

        await self.send_msg("budget_agent", "hotel_search", {
            "cheapest_per_night":    min(h["price_per_night"] for h in hotels) if hotels else 0,
            "recommended_per_night": hotels[0]["price_per_night"] if hotels else 0,
        })

        return {
            "hotels": hotels,
            "agent_statuses": {**state.get("agent_statuses", {}), "hotel_agent": "completed"},
            "log": log,
        }
