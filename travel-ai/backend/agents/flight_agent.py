# backend/agents/flight_agent.py
import json, re
from typing import Any, Dict, List
from backend.agents.base_agent import BaseAgent
from backend.a2a import AgentCapability
from backend.mcp_servers.amadeus_mcp import amadeus_mcp
#from backend.agents.base_agent import Agent           # ensure correct import
from backend.agents.base_agent import AgentCapability # if needed by the class

class FlightAgent(BaseAgent):                       # ensure it inherits Agent
    def __init__(self):
        super().__init__(
            "flight_agent", "✈️ Flight Agent",
            "Searches and ranks flights via Amadeus MCP",
            [AgentCapability.FLIGHT_SEARCH],
        )

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        p    = state["preferences"]
        dest = p["destination"]
        orig = p["origin"]

        log = [f"✈️ Flight Agent: Searching {orig} → {dest}..."]

        # MCP tool calls
        orig_code = (await amadeus_mcp.call_tool("get_city_code", {"city": orig})).get("code", orig[:3].upper())
        dest_code = (await amadeus_mcp.call_tool("get_city_code", {"city": dest})).get("code", dest[:3].upper())

        cabin = {"budget": "ECONOMY", "comfort": "ECONOMY", "luxury": "BUSINESS"}.get(
            p.get("travel_style", "comfort"), "ECONOMY"
        )
        result = await amadeus_mcp.call_tool("search_flights", {
            "origin":         orig_code,
            "destination":    dest_code,
            "departure_date": p["departure_date"],
            "return_date":    p.get("return_date"),
            "adults":         p.get("adults", 1),
            "travel_class":   cabin,
            "max_results":    5,
        })
        flights = result.get("data", [])

        # LLM ranking
        if flights:
            flights = await self._rank(flights, p)

        log.append(
            f"✈️ Flight Agent: Found {len(flights)} flights. "
            + (f"Best fare: {flights[0]['currency']} {flights[0]['price']:,.0f}" if flights else "")
        )

        # A2A → notify BudgetAgent
        await self.send_msg("budget_agent", "flight_search", {
            "cheapest": flights[-1]["price"] if flights else 0,
            "currency": flights[0]["currency"] if flights else p.get("currency", "INR"),
        })

        return {
            "flights": flights,
            "agent_statuses": {**state.get("agent_statuses", {}), "flight_agent": "completed"},
            "log": log,
        }

    async def _rank(self, flights: List[Dict], prefs: Dict) -> List[Dict]:
        system = "You are a flight expert. Rank flights for this traveller. Return ONLY a JSON array of IDs best-to-worst."
        user   = (
            f"Budget: {prefs.get('currency','INR')} {prefs.get('budget',100000)}\n"
            f"Style: {prefs.get('travel_style','comfort')}\n\n"
            + json.dumps([{"id":f["id"],"airline":f["airline"],"stops":f["stops"],"price":f["price"]} for f in flights])
        )
        try:
            raw  = await self.think(system, user)
            ids  = json.loads(re.search(r'\[.*?\]', raw, re.DOTALL).group())
            lut  = {f["id"]: f for f in flights}
            ranked = [lut[i] for i in ids if i in lut]
            ranked += [f for f in flights if f["id"] not in set(ids)]
            return ranked
        except Exception:
            return sorted(flights, key=lambda x: x["price"])
