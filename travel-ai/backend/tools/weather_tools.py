# backend/tools/weather_tools.py
import asyncio
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List


MOCK_CONDITIONS = [
    ("Sunny", "☀️"), ("Partly Cloudy", "⛅"), ("Clear", "🌤️"),
    ("Cloudy", "☁️"), ("Light Rain", "🌦️"), ("Windy", "💨"),
]


class WeatherTools:

    def __init__(self):
        from backend.config import settings
        self.api_key  = settings.openweather_api_key
        self.use_mock = not self.api_key or self.api_key == "your_openweather_api_key"

    async def get_forecast(
        self, destination: str, start_date: str, num_days: int = 7
    ) -> List[Dict[str, Any]]:
        if self.use_mock:
            return self._mock(start_date, num_days)

        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                geo = await client.get(
                    "http://api.openweathermap.org/geo/1.0/direct",
                    params={"q": destination, "limit": 1, "appid": self.api_key},
                )
                g = geo.json()
                if not g:
                    return self._mock(start_date, num_days)
                lat, lon = g[0]["lat"], g[0]["lon"]

                fc = await client.get(
                    "https://api.openweathermap.org/data/2.5/forecast",
                    params={"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"},
                )
                return self._parse(fc.json(), start_date, num_days)
        except Exception:
            return self._mock(start_date, num_days)

    def _parse(self, data: Dict, start_date: str, num_days: int) -> List[Dict]:
        by_day: Dict[str, list] = {}
        for item in data.get("list", []):
            d = item["dt_txt"][:10]
            by_day.setdefault(d, []).append(item)

        results = []
        start = datetime.strptime(start_date, "%Y-%m-%d")
        for i in range(min(num_days, len(by_day))):
            ds   = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            rows = by_day.get(ds, [])
            if rows:
                mid = rows[len(rows) // 2]
                w   = mid["weather"][0]
                results.append({
                    "date":                ds,
                    "condition":           w["description"].title(),
                    "icon":                "☀️",
                    "temp_high":           max(r["main"]["temp"] for r in rows),
                    "temp_low":            min(r["main"]["temp"] for r in rows),
                    "precipitation_chance": int(mid.get("pop", 0) * 100),
                    "humidity":            mid["main"]["humidity"],
                })
        return results or self._mock(start_date, num_days)

    def _mock(self, start_date: str, num_days: int) -> List[Dict]:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        return [
            {
                "date":                (start + timedelta(days=i)).strftime("%Y-%m-%d"),
                "condition":           cond,
                "icon":                icon,
                "temp_high":           round(random.uniform(22, 34), 1),
                "temp_low":            round(random.uniform(14, 21), 1),
                "precipitation_chance": random.randint(5, 40),
                "humidity":            random.randint(50, 78),
            }
            for i, (cond, icon) in enumerate(
                [random.choice(MOCK_CONDITIONS) for _ in range(num_days)]
            )
        ]


weather_tools = WeatherTools()
