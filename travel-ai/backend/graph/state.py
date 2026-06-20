# backend/graph/state.py
"""LangGraph state — single typed dict passed through every node."""
from typing import Annotated, Any, Dict, List, Optional
import operator
from typing_extensions import TypedDict


class TravelState(TypedDict):
    # ── Input ────────────────────────────────────────────────────────────────
    session_id:  str
    preferences: Dict[str, Any]          # raw request from user

    # ── Agent outputs ─────────────────────────────────────────────────────────
    flights:           List[Dict[str, Any]]
    hotels:            List[Dict[str, Any]]
    activities:        List[Dict[str, Any]]
    weather_forecasts: List[Dict[str, Any]]

    # ── Composed result ───────────────────────────────────────────────────────
    day_plans:        List[Dict[str, Any]]
    budget_breakdown: Optional[Dict[str, Any]]
    final_itinerary:  Optional[Dict[str, Any]]

    # ── A2A message log (accumulated) ─────────────────────────────────────────
    a2a_messages: Annotated[List[Dict[str, Any]], operator.add]

    # ── Workflow metadata ─────────────────────────────────────────────────────
    agent_statuses:    Dict[str, str]
    errors:            Annotated[List[str], operator.add]
    log:               Annotated[List[str], operator.add]   # streaming log lines
    created_at:        str
    completed_at:      Optional[str]
    duration_seconds:  Optional[float]
