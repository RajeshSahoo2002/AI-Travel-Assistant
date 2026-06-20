# backend/api/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional


class TravelRequest(BaseModel):
    origin:           str   = Field(..., example="Mumbai")
    destination:      str   = Field(..., example="Paris")
    departure_date:   str   = Field(..., example="2025-06-15")
    return_date:      Optional[str] = Field(None, example="2025-06-22")
    adults:           int   = Field(1, ge=1, le=9)
    budget:           float = Field(100000)
    currency:         str   = Field("INR")
    travel_style:     str   = Field("comfort")   # budget | comfort | luxury
    interests:        List[str] = Field(["culture", "food"])
    accommodation_type: str = Field("hotel")
