# backend/graph/workflow.py
"""
LangGraph Workflow
==================
Defines a directed graph where each node is an agent.
FlightAgent, HotelAgent, WeatherAgent run in PARALLEL via asyncio.gather.
Then: Activity → Budget → Itinerary (sequential, depend on prior outputs).

Graph shape:
  START
    │
    ▼
 initialize
    │
    ▼
 parallel_search  ◄── FlightAgent + HotelAgent + WeatherAgent (concurrent)
    │
    ▼
 activities
    │
    ▼
  budget
    │
    ▼
 compose_itinerary
    │
    ▼
   END
"""
import asyncio
from datetime import datetime
from typing import Any, Dict

import structlog
from langgraph.graph import StateGraph, START, END

from backend.graph.state import TravelState
from backend.agents.flight_agent    import FlightAgent
from backend.agents.hotel_agent     import HotelAgent
from backend.agents.weather_agent   import WeatherAgent
from backend.agents.activity_agent  import ActivityAgent
from backend.agents.budget_agent    import BudgetAgent
from backend.agents.itinerary_agent import ItineraryAgent

log = structlog.get_logger()

# ── Instantiate agents (singletons, registers them in A2A registry) ──────────
_flight    = FlightAgent()
_hotel     = HotelAgent()
_weather   = WeatherAgent()
_activity  = ActivityAgent()
_budget    = BudgetAgent()
_itinerary = ItineraryAgent()


# ── Node functions ────────────────────────────────────────────────────────────

async def initialize(state: TravelState) -> Dict[str, Any]:
    log.info("graph.initialize", session=state["session_id"])
    return {
        "agent_statuses": {
            "flight_agent":    "pending",
            "hotel_agent":     "pending",
            "weather_agent":   "pending",
            "activity_agent":  "pending",
            "budget_agent":    "pending",
            "itinerary_agent": "pending",
        },
        "log": [
            f"🚀 Starting AI travel planning for **{state['preferences']['destination']}**",
            "🤖 Launching 6 specialised AI agents...",
        ],
        "created_at": datetime.utcnow().isoformat(),
    }


async def parallel_search(state: TravelState) -> Dict[str, Any]:
    """Run flight, hotel, weather agents concurrently."""
    results = await asyncio.gather(
        _flight.run(state),
        _hotel.run(state),
        _weather.run(state),
        return_exceptions=True,
    )
    merged: Dict[str, Any] = {
        "flights": [], "hotels": [], "weather_forecasts": [],
        "log": [], "errors": [], "agent_statuses": {},
    }
    for r in results:
        if isinstance(r, Exception):
            merged["errors"].append(str(r))
        else:
            merged["flights"]           += r.get("flights", [])
            merged["hotels"]            += r.get("hotels", [])
            merged["weather_forecasts"] += r.get("weather_forecasts", [])
            merged["log"]               += r.get("log", [])
            merged["errors"]            += r.get("errors", [])
            merged["agent_statuses"].update(r.get("agent_statuses", {}))
    return merged


async def activities(state: TravelState) -> Dict[str, Any]:
    return await _activity.run(state)


async def budget(state: TravelState) -> Dict[str, Any]:
    return await _budget.run(state)


async def compose_itinerary(state: TravelState) -> Dict[str, Any]:
    result = await _itinerary.run(state)
    dur    = (datetime.utcnow() - datetime.fromisoformat(state["created_at"])).total_seconds()
    result["duration_seconds"] = dur
    return result


# ── Build + compile ───────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(TravelState)
    g.add_node("initialize",         initialize)
    g.add_node("parallel_search",    parallel_search)
    g.add_node("activities",         activities)
    g.add_node("budget",             budget)
    g.add_node("compose_itinerary",  compose_itinerary)

    g.add_edge(START,               "initialize")
    g.add_edge("initialize",        "parallel_search")
    g.add_edge("parallel_search",   "activities")
    g.add_edge("activities",        "budget")
    g.add_edge("budget",            "compose_itinerary")
    g.add_edge("compose_itinerary", END)

    return g.compile()


workflow = build_graph()
