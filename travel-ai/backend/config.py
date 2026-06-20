# backend/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Amadeus (original) ──────────────────────────────────────────
    amadeus_client_id:     str = ""
    amadeus_client_secret: str = ""
    amadeus_hostname:      str = "test"

    # ── Duffel (recommended Amadeus alternative) ────────────────────
    # Free sandbox: https://duffel.com
    # Token format: duffel_test_xxxxxxxxxxxx
    duffel_token: str = ""

    # ── Aviationstack (flight schedules, 500 req/month free) ────────
    # https://aviationstack.com
    aviationstack_key: str = ""

    # ── OpenTripMap (POI + hotels, 5000 req/day free) ───────────────
    # https://opentripmap.io/register
    opentripmap_key: str = ""

    # ── Foursquare Places (activities, 950 calls/day free) ──────────
    # https://foursquare.com/developer
    foursquare_key: str = ""

    # ── LLM ─────────────────────────────────────────────────────────
    anthropic_api_key: str = ""
    openai_api_key:    str = ""
    groq_api_key:      str = ""
    llm_provider:      str = "groq"   # anthropic | openai
    llm_model:         str = "llama-3.1-8b-instant"

    # ── Weather (OpenWeatherMap, 1000 req/day free) ──────────────────
    openweather_api_key: str = ""

    # ── App ──────────────────────────────────────────────────────────
    frontend_origin: str  = "http://localhost:3000"
    debug:           bool = True

    class Config:
        env_file            = ".env"
        env_file_encoding   = "utf-8"
        extra               = "ignore"


settings = Settings()
