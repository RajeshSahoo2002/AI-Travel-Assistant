# backend/mcp_servers/amadeus_mcp.py
"""
Travel MCP Server
==================
Exposes all travel data providers (Amadeus / Duffel / OpenTripMap /
Foursquare / mock) as a unified set of MCP tools.
Agents call this server — they never touch the provider SDKs directly.
"""
from typing import Any, Dict, List


TOOLS = [
    {
        "name": "search_flights",
        "description": "Search available flight offers between two cities.",
        "inputSchema": {
            "type": "object",
            "required": ["origin", "destination", "departure_date"],
            "properties": {
                "origin":         {"type": "string", "description": "IATA origin code, e.g. BOM"},
                "destination":    {"type": "string", "description": "IATA destination code, e.g. CDG"},
                "departure_date": {"type": "string", "description": "YYYY-MM-DD"},
                "return_date":    {"type": "string", "description": "YYYY-MM-DD (optional)"},
                "adults":         {"type": "integer", "default": 1},
                "travel_class":   {"type": "string", "default": "ECONOMY"},
                "max_results":    {"type": "integer", "default": 5},
            },
        },
    },
    {
        "name": "search_hotels",
        "description": "Search hotels in a destination city.",
        "inputSchema": {
            "type": "object",
            "required": ["city_code", "check_in", "check_out"],
            "properties": {
                "city_code":   {"type": "string"},
                "check_in":    {"type": "string"},
                "check_out":   {"type": "string"},
                "adults":      {"type": "integer", "default": 1},
                "max_results": {"type": "integer", "default": 5},
            },
        },
    },
    {
        "name": "get_activities",
        "description": "Get tourist activities and attractions for a destination.",
        "inputSchema": {
            "type": "object",
            "required": ["destination"],
            "properties": {
                "destination": {"type": "string"},
            },
        },
    },
    {
        "name": "get_city_code",
        "description": "Convert a city name to IATA code.",
        "inputSchema": {
            "type": "object",
            "required": ["city"],
            "properties": {"city": {"type": "string"}},
        },
    },
]


class AmadeusMCPServer:
    """Unified MCP server — routes to whichever travel provider is configured."""

    NAME    = "travel-data-mcp"
    VERSION = "2.0.0"

    def __init__(self):
        from backend.tools.travel_tools import travel_tools
        self._t = travel_tools

    def list_tools(self) -> List[Dict]:
        return TOOLS

    async def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name == "search_flights":
                return {"ok": True, "data": await self._t.search_flights(**args)}
            elif name == "search_hotels":
                return {"ok": True, "data": await self._t.search_hotels(**args)}
            elif name == "get_activities":
                return {"ok": True, "data": await self._t.get_activities(**args)}
            elif name == "get_city_code":
                return {"ok": True, "code": await self._t.get_city_code(**args)}
            return {"ok": False, "error": f"Unknown tool: {name}"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def info(self) -> Dict[str, Any]:
        return {"name": self.NAME, "version": self.VERSION, "tools": len(TOOLS)}


amadeus_mcp = AmadeusMCPServer()
