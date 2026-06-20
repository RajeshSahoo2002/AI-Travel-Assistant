# ✈️ AI Travel Itinerary Recommendation System

End-to-end AI travel planner using **LangGraph + MCP + A2A + LLM (Claude/OpenAI/Gemini) + Amadeus API**.

---

## 🏗️ Architecture

```
Browser (HTML/CSS/JS)
        │  HTTP + SSE (streaming)
        ▼
FastAPI Backend (port 8000)
        │
   LangGraph Workflow
   ┌────┴─────────────────────────────┐
   │          Parallel Execution      │
   ▼                  ▼               ▼
FlightAgent      HotelAgent     WeatherAgent
   │  (MCP→Amadeus)   │  (MCP→Amadeus)  │ (MCP→OpenWeather)
   └──────────┬────────┘               │
              │◄──────────────────────┘
              ▼  [A2A messaging between agents]
        ActivityAgent
              ▼
         BudgetAgent
              ▼
       ItineraryAgent (LLM compose)
              ▼
         Final Result → SSE → Browser
```

---

## 📁 Project Structure

```
travel-ai/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── config.py                # Settings / env vars
│   ├── requirements.txt
│   ├── agents/
│   │   ├── base_agent.py        # Base A2A agent
│   │   ├── flight_agent.py
│   │   ├── hotel_agent.py
│   │   ├── activity_agent.py
│   │   ├── weather_agent.py
│   │   ├── budget_agent.py
│   │   └── itinerary_agent.py
│   ├── mcp_servers/
│   │   ├── amadeus_mcp.py       # Amadeus as MCP tool server
│   │   └── weather_mcp.py       # Weather as MCP tool server
│   ├── a2a/
│   │   ├── protocol.py          # A2A message types & bus
│   │   └── registry.py          # Agent registry
│   ├── graph/
│   │   ├── state.py             # LangGraph state schema
│   │   └── workflow.py          # LangGraph graph definition
│   ├── tools/
│   │   ├── amadeus_tools.py     # Amadeus SDK wrapper
│   │   └── weather_tools.py     # Weather API wrapper
│   └── api/
│       ├── routes.py            # FastAPI endpoints
│       └── schemas.py           # Pydantic models
└── frontend/
    ├── index.html               # Main UI (single file)
    ├── style.css                # Styles
    └── app.js                   # JavaScript logic
```

---

## ⚙️ Setup

### 1. Get API Keys (all free tiers available)
- **Amadeus**: https://developers.amadeus.com (free sandbox)
- **Anthropic**: https://console.anthropic.com
- **OpenWeatherMap**: https://openweathermap.org/api (free)

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env         # fill in your API keys
uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
# Just open in browser — no build step needed!
open frontend/index.html
# OR serve with Python:
cd frontend && python -m http.server 3000
# Then visit http://localhost:3000
```

---

## 🔑 Environment Variables (.env)

```
AMADEUS_CLIENT_ID=your_id
AMADEUS_CLIENT_SECRET=your_secret
ANTHROPIC_API_KEY=your_key
OPENWEATHER_API_KEY=your_key
LLM_PROVIDER=anthropic
```

---

## 🌐 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/generate` | Start itinerary generation |
| GET  | `/api/stream/{id}` | SSE stream of agent updates |
| GET  | `/api/result/{id}` | Get final result |
| GET  | `/api/agents` | List all registered agents |
| GET  | `/api/mcp/tools` | List all MCP tools |
| GET  | `/health` | Health check |

---

## 🧠 How Each Technology Is Used

| Technology | Role in This System |
|------------|-------------------|
| **LangGraph** | Orchestrates agent workflow as a directed graph with parallel nodes |
| **MCP** | Amadeus & Weather APIs exposed as standardized tool servers |
| **A2A Protocol** | Agents send typed messages to each other (e.g. FlightAgent → BudgetAgent) |
| **LLM (Claude)** | Activity curation, flight ranking, itinerary narrative composition |
| **Amadeus API** | Real flight offers, hotel search, city code lookup |
