# backend/api/routes.py
import asyncio
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator

import structlog
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from backend.api.schemas import TravelRequest
from backend.graph.workflow import workflow
from backend.a2a import agent_registry, message_bus

log    = structlog.get_logger()
router = APIRouter()

# In-memory session store (swap for Redis in prod)
_sessions: dict = {}


# ── Generate ─────────────────────────────────────────────────────────────────

@router.post("/generate")
async def generate(req: TravelRequest):
    """Start itinerary generation. Returns session_id immediately."""
    sid = str(uuid.uuid4())

    state = {
        "session_id":       sid,
        "preferences":      req.model_dump(),
        "flights":          [],
        "hotels":           [],
        "activities":       [],
        "weather_forecasts":[],
        "day_plans":        [],
        "budget_breakdown": None,
        "final_itinerary":  None,
        "a2a_messages":     [],
        "agent_statuses":   {},
        "errors":           [],
        "log":              [],
        "created_at":       datetime.utcnow().isoformat(),
        "completed_at":     None,
        "duration_seconds": None,
    }

    _sessions[sid] = {"status": "running", "state": state}
    asyncio.create_task(_run(sid, state))

    return {"session_id": sid, "status": "started",
            "message": f"Planning trip to {req.destination}"}


async def _run(sid: str, initial: dict):
    try:
        final = await workflow.ainvoke(initial)
        _sessions[sid] = {"status": "completed", "state": final}
        log.info("workflow.done", sid=sid,
                 secs=final.get("duration_seconds", 0))
    except Exception as exc:
        log.error("workflow.error", sid=sid, error=str(exc))
        _sessions[sid] = {"status": "error", "state": initial, "error": str(exc)}


# ── Stream (SSE) ──────────────────────────────────────────────────────────────

@router.get("/stream/{sid}")
async def stream(sid: str):
    """Server-Sent Events: delivers log lines + final result."""
    if sid not in _sessions:
        raise HTTPException(404, "Session not found")

    async def events() -> AsyncGenerator:
        sent   = 0
        waited = 0
        while waited < 180:          # 3 min hard timeout
            sess  = _sessions.get(sid, {})
            state = sess.get("state", {})
            lines = state.get("log", [])

            # Stream new log lines
            while sent < len(lines):
                yield {
                    "event": "log",
                    "data":  json.dumps({
                        "message":        lines[sent],
                        "agent_statuses": state.get("agent_statuses", {}),
                    }),
                }
                sent += 1

            if sess.get("status") == "completed":
                yield {"event": "done", "data": json.dumps({"session_id": sid, "state": state})}
                return
            elif sess.get("status") == "error":
                yield {"event": "error", "data": json.dumps({"error": sess.get("error", "Unknown")})}
                return

            await asyncio.sleep(0.4)
            waited += 0.4

        yield {"event": "error", "data": json.dumps({"error": "Timeout"})}

    return EventSourceResponse(events())


# ── Result ────────────────────────────────────────────────────────────────────

@router.get("/result/{sid}")
async def result(sid: str):
    if sid not in _sessions:
        raise HTTPException(404, "Session not found")
    return _sessions[sid]


# ── Inspector endpoints ───────────────────────────────────────────────────────

@router.get("/agents")
async def agents():
    return {"agents": agent_registry.all()}


@router.get("/a2a/log")
async def a2a_log():
    return {"messages": message_bus.message_log()}


@router.get("/mcp/tools")
async def mcp_tools():
    from backend.mcp_servers.amadeus_mcp import amadeus_mcp
    from backend.mcp_servers.weather_mcp import weather_mcp
    return {
        "servers": [
            {**amadeus_mcp.info(), "tools": amadeus_mcp.list_tools()},
            {**weather_mcp.info(), "tools": weather_mcp.list_tools()},
        ]
    }


@router.get("/health")
async def health():
    return {"status": "ok", "agents": len(agent_registry.all()), "ts": datetime.utcnow().isoformat()}
