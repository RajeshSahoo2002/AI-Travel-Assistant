# backend/main.py
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.api.routes import router

structlog.configure(processors=[
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.dev.ConsoleRenderer(),
])

app = FastAPI(
    title="AI Travel Itinerary System",
    description="LangGraph + MCP + A2A + Amadeus + LLM",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
async def startup():
    # Eagerly import workflow so all agents register in A2A registry
    from backend.graph.workflow import workflow   # noqa
    structlog.get_logger().info(
        "server.ready",
        llm=settings.llm_provider,
        amadeus="live" if settings.amadeus_client_id not in ("", "test_client_id", "your_amadeus_client_id") else "mock",
    )


@app.get("/")
async def root():
    return {
        "name": "AI Travel Itinerary System",
        "docs": "/docs",
        "health": "/api/health",
        "stack": ["LangGraph", "MCP", "A2A", "Amadeus", "Claude LLM"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
