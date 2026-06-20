# backend/agents/budget_agent.py
from datetime import datetime
from typing import Any, Dict
from backend.agents.base_agent import BaseAgent
from backend.a2a import AgentCapability


class BudgetAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "budget_agent", "💰 Budget Agent",
            "Analyses and optimises budget across all travel components",
            [AgentCapability.BUDGET_ANALYSIS],
        )

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        p        = state["preferences"]
        budget   = float(p.get("budget", 100000))
        currency = p.get("currency", "INR")
        flights  = state.get("flights", [])
        hotels   = state.get("hotels", [])
        activities = state.get("activities", [])
        log      = [f"💰 Budget Agent: Analysing costs for {currency} {budget:,.0f} budget..."]

        # Trip duration
        try:
            dep    = datetime.strptime(p["departure_date"], "%Y-%m-%d")
            nights = (datetime.strptime(p["return_date"], "%Y-%m-%d") - dep).days if p.get("return_date") else 3
        except (ValueError, TypeError):
            nights = 3

        adults            = p.get("adults", 1)
        flight_cost       = min((f["price"] for f in flights), default=0) * adults
        hotel_pn          = min((h["price_per_night"] for h in hotels), default=0)
        hotel_cost        = hotel_pn * nights
        activity_cost     = sum(a["price"] for a in activities[:nights * 2])
        meal_cost         = nights * adults * 3 * 500
        transport_cost    = nights * 300
        total             = flight_cost + hotel_cost + activity_cost + meal_cost + transport_cost
        remaining         = budget - total

        breakdown = {
            "flights":       flight_cost,
            "accommodation": hotel_cost,
            "activities":    activity_cost,
            "meals":         meal_cost,
            "transport":     transport_cost,
            "miscellaneous": max(remaining * 0.05, 0),
            "total":         total,
            "currency":      currency,
            "within_budget": total <= budget,
            "remaining":     remaining,
        }

        status = ("✅ Within budget!" if total <= budget
                  else f"⚠️ Over by {currency} {abs(remaining):,.0f}")
        log.append(f"💰 Budget Agent: {status} Estimated total: {currency} {total:,.0f}")

        await self.send_msg("itinerary_agent", "budget_analysis",
                            {"breakdown": breakdown, "within_budget": total <= budget})

        return {
            "budget_breakdown": breakdown,
            "agent_statuses": {**state.get("agent_statuses", {}), "budget_agent": "completed"},
            "log": log,
        }
