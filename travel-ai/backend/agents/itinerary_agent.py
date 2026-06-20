# backend/agents/itinerary_agent.py
import json, re
from datetime import datetime, timedelta
from typing import Any, Dict, List
from backend.agents.base_agent import BaseAgent
from backend.a2a import AgentCapability


class ItineraryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "itinerary_agent", "📋 Itinerary Agent",
            "Composes the final personalised day-by-day travel plan using LLM",
            [AgentCapability.ITINERARY_COMPOSE],
        )

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        p    = state["preferences"]
        dest = p["destination"]
        log  = [f"📋 Itinerary Agent: Composing personalised {dest} itinerary..."]

        # Calculate trip length
        try:
            dep      = datetime.strptime(p["departure_date"], "%Y-%m-%d")
            num_days = (datetime.strptime(p["return_date"], "%Y-%m-%d") - dep).days if p.get("return_date") else 3
            num_days = max(1, num_days)
        except (ValueError, TypeError):
            dep      = datetime.now()
            num_days = 3

        # Build day plans
        day_plans = self._build_days(state, dep, num_days)

        # LLM narrative
        final = await self._compose(state, day_plans, p, num_days)

        log.append(f"📋 Itinerary Agent: Your {num_days}-day {dest} itinerary is ready! 🎉")

        return {
            "day_plans":       day_plans,
            "final_itinerary": final,
            "agent_statuses":  {**state.get("agent_statuses", {}), "itinerary_agent": "completed"},
            "completed_at":    datetime.utcnow().isoformat(),
            "log":             log,
        }

    # ── Day planner ─────────────────────────────────────────────────────────

    def _build_days(self, state: Dict, start: datetime, num_days: int) -> List[Dict]:
        acts     = state.get("activities", [])
        weather  = state.get("weather_forecasts", [])
        per_day  = max(1, len(acts) // num_days) if acts else 2
        days     = []

        for i in range(num_days):
            date_str  = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            day_acts  = acts[i * per_day:(i + 1) * per_day]
            w         = weather[i] if i < len(weather) else None

            morning   = [a for a in day_acts if a.get("best_time") == "Morning"]
            afternoon = [a for a in day_acts if a.get("best_time") == "Afternoon"]
            evening   = [a for a in day_acts if a.get("best_time") == "Evening"]
            rest      = [a for a in day_acts if a not in morning + afternoon + evening]
            for j, a in enumerate(rest):
                [morning, afternoon, evening][j % 3].append(a)

            days.append({
                "date":               date_str,
                "day_number":         i + 1,
                "morning":            morning,
                "afternoon":          afternoon,
                "evening":            evening,
                "weather":            w,
                "estimated_daily_cost": sum(a["price"] for a in day_acts) + 1800,
            })
        return days

    # ── LLM composition ─────────────────────────────────────────────────────

    async def _compose(self, state, day_plans, prefs, num_days) -> Dict:
        flights = state.get("flights", [{}])
        hotels  = state.get("hotels", [{}])
        budget  = state.get("budget_breakdown", {})

        system = "You are an expert travel planner. Return ONLY valid JSON, no markdown."
        user   = f"""Create a travel summary for:
Destination: {prefs['destination']}
Origin: {prefs['origin']}
Duration: {num_days} days
Style: {prefs.get('travel_style','comfort')}
Interests: {', '.join(prefs.get('interests', ['sightseeing']))}
Budget: {prefs.get('currency','INR')} {prefs.get('budget',100000)}
Best flight: {flights[0].get('airline','TBD')} {prefs.get('currency','INR')} {flights[0].get('price',0):,.0f}
Best hotel: {hotels[0].get('name','TBD')} ({hotels[0].get('stars',3)}⭐)

Return this exact JSON:
{{
  "title": "catchy trip title",
  "tagline": "one-line description",
  "highlights": ["top 5 highlight strings"],
  "travel_tips": ["5 practical tips"],
  "local_cuisine": ["3-4 must-try dishes"],
  "cultural_notes": "2-3 cultural tips",
  "day_summaries": ["one sentence per day, {num_days} total"]
}}"""

        try:
            raw   = await self.think(system, user)
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                data.update({
                    "destination": prefs["destination"],
                    "origin":      prefs["origin"],
                    "num_days":    num_days,
                    "currency":    prefs.get("currency", "INR"),
                    "total_cost":  budget.get("total", 0),
                })
                return data
        except Exception:
            pass

        # Fallback
        return {
            "title":     f"Discover {prefs['destination']}",
            "tagline":   f"An unforgettable {num_days}-day adventure",
            "highlights":     [f"Explore {prefs['destination']}"],
            "travel_tips":    ["Book in advance", "Carry local currency", "Stay hydrated"],
            "local_cuisine":  ["Local specialties"],
            "cultural_notes": "Respect local customs.",
            "day_summaries":  [f"Day {i+1} in {prefs['destination']}" for i in range(num_days)],
            "destination": prefs["destination"],
            "origin":      prefs["origin"],
            "num_days":    num_days,
            "currency":    prefs.get("currency", "INR"),
            "total_cost":  budget.get("total", 0),
        }
