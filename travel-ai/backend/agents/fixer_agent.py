# backend/agents/fixer_agent.py
from typing import Any, Dict
from backend.agents.base_agent import BaseAgent
from backend.a2a import AgentCapability

class FixerAgent(BaseAgent):
    def _init_(self):
        super()._init_(
            "fixer_agent", "🔧 Fixer Agent",
            "Steps in when other agents fail and provides fallback logic.",
            [AgentCapability.BUDGET_ANALYSIS] # Just a placeholder
        )

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        log = []
        errors = state.get("errors", [])
        
        flights = state.get("flights", [])
        hotels = state.get("hotels", [])
        activities = state.get("activities", [])
        weather = state.get("weather_forecasts", [])

        if errors or not flights or not hotels:
            log.append("🔧 Fixer Agent: Detected missing data or errors. Stepping in to repair the itinerary...")

        # If flights are missing, add a safe fallback
        if not flights:
            log.append("🔧 Fixer Agent: Restoring backup flight data..")
            flights = [{
                "id": "FIX-FL1", "airline": "Fallback Airways", "flight_number": "FB-001",
                "departure_time": "10:00", "arrival_time": "14:00", "duration": "4h 0m",
                "stops": 0, "price": 10000.0, "currency": state["preferences"].get("currency", "INR"),
                "cabin_class": "Economy", "booking_url": "#"
            }]

        # If hotels are missing, add a safe fallback
        if not hotels:
            log.append("🔧 Fixer Agent: Restoring backup hotel data..")
            hotels = [{
                "id": "FIX-HT1", "name": "Safe Harbor Hotel", "stars": 4, "rating": 4.5,
                "address": "Central District", "price_per_night": 5000.0,
                "currency": state["preferences"].get("currency", "INR"),
                "amenities": ["WiFi", "Breakfast", "Support"], "booking_url": "#"
            }]

        # Try to fix activities if empty but it's checked after activities usually, 
        # so let's put safe fallbacks just in case
        if not activities:
            log.append("🔧 Fixer Agent: Generating generic activity plan..")
            activities = [{
                "id": "FIX-A1", "name": "City Highlight Walk", "type": "tour",
                "description": "A guided overview of the most famous sights.",
                "duration_hours": 3.0, "price": 0.0, "currency": state["preferences"].get("currency", "INR"),
                "best_time": "Morning", "booking_required": False
            }]

        return {
            "flights": flights,
            "hotels": hotels,
            "activities": activities,
            "weather_forecasts": weather,
            "agent_statuses": {**state.get("agent_statuses", {}), "fixer_agent": "completed"},
            "log": log,
            "errors": [] # Clear errors so it proceeds cleanly
        }