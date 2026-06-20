# backend/mcp_servers/weather_mcp.py
from typing import Any, Dict, List


TOOLS = [
    {
        "name": "get_weather_forecast",
        "description": "Get daily weather forecast for a destination.",
        "inputSchema": {
            "type": "object",
            "required": ["destination", "start_date"],
            "properties": {
                "destination": {"type": "string"},
                "start_date":  {"type": "string", "description": "YYYY-MM-DD"},
                "num_days":    {"type": "integer", "default": 7},
            },
        },
    },
]


class WeatherMCPServer:
    NAME    = "weather-forecast-mcp"
    VERSION = "1.0.0"

    def __init__(self):
        from backend.tools.weather_tools import weather_tools
        self._tools = weather_tools

    def list_tools(self) -> List[Dict]:
        return TOOLS

    async def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "get_weather_forecast":
            data = await self._tools.get_forecast(
                destination = args["destination"],
                start_date  = args["start_date"],
                num_days    = args.get("num_days", 7),
            )
            return {"ok": True, "data": data}
        return {"ok": False, "error": f"Unknown tool: {name}"}

    def info(self) -> Dict[str, Any]:
        return {"name": self.NAME, "version": self.VERSION, "tools": len(TOOLS)}


weather_mcp = WeatherMCPServer()
