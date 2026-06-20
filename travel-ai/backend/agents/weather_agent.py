# backend/agents/weather_agent.py
from datetime import datetime, timedelta
from typing import Any, Dict
from backend.agents.base_agent import BaseAgent
from backend.a2a import AgentCapability
from backend.mcp_servers.weather_mcp import weather_mcp


class WeatherAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "weather_agent", "🌤️ Weather Agent",
            "Fetches weather forecasts via OpenWeatherMap MCP",
            [AgentCapability.WEATHER_FORECAST],
        )

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        p      = state["preferences"]
        dest   = p["destination"]
        start  = p["departure_date"]
        try:
            dep  = datetime.strptime(start, "%Y-%m-%d")
            ret  = datetime.strptime(p["return_date"], "%Y-%m-%d") if p.get("return_date") else dep + timedelta(days=3)
            days = max(1, (ret - dep).days + 1)
        except (ValueError, TypeError):
            days = 7

        log = [f"🌤️ Weather Agent: Getting {days}-day forecast for {dest}..."]

        result    = await weather_mcp.call_tool("get_weather_forecast", {
            "destination": dest, "start_date": start, "num_days": min(days, 7),
        })
        forecasts = result.get("data", [])

        # Share context with activity agent via A2A
        if forecasts:
            avg_hi = sum(f["temp_high"] for f in forecasts) / len(forecasts)
            rainy  = sum(1 for f in forecasts if f["precipitation_chance"] > 50)
            await self.send_msg("activity_agent", "weather_forecast", {
                "avg_temp_high": avg_hi, "rainy_days": rainy,
            })
            summary = f"Avg {avg_hi:.0f}°C. {'Expect some rain ☂️' if rainy > 1 else 'Mostly dry ☀️'}"
        else:
            summary = "Forecast unavailable"

        log.append(f"🌤️ Weather Agent: {summary}")

        return {
            "weather_forecasts": forecasts,
            "agent_statuses": {**state.get("agent_statuses", {}), "weather_agent": "completed"},
            "log": log,
        }
