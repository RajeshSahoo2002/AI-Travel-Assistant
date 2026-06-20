# backend/tools/amadeus_tools.py
"""
Amadeus Travel API wrapper.

Uses the official amadeus-python SDK when real credentials are provided.
Falls back to rich mock data automatically for local development / demos.
"""
import asyncio
from typing import Any, Dict, List, Optional


# ── Mock data ────────────────────────────────────────────────────────────────

MOCK_FLIGHTS = [
    {
        "id": "FL001", "airline": "Air India", "flight_number": "AI-202",
        "departure_time": "06:00", "arrival_time": "14:30",
        "duration": "8h 30m", "stops": 0,
        "price": 45000.0, "currency": "INR", "cabin_class": "Economy",
        "booking_url": "https://www.airindia.com",
    },
    {
        "id": "FL002", "airline": "IndiGo", "flight_number": "6E-501",
        "departure_time": "09:15", "arrival_time": "17:45",
        "duration": "8h 30m", "stops": 1,
        "price": 32000.0, "currency": "INR", "cabin_class": "Economy",
        "booking_url": "https://www.goindigo.in",
    },
    {
        "id": "FL003", "airline": "Emirates", "flight_number": "EK-505",
        "departure_time": "23:00", "arrival_time": "10:30+1",
        "duration": "11h 30m", "stops": 1,
        "price": 58000.0, "currency": "INR", "cabin_class": "Business",
        "booking_url": "https://www.emirates.com",
    },
    {
        "id": "FL004", "airline": "Fiji Airways", "flight_number": "FJ505",
        "departure_time": "01:00", "arrival_time": "11:30+1",
        "duration": "11h 30m", "stops": 1,
        "price": 58000.0, "currency": "INR", "cabin_class": "Premium Economy",
        "booking_url": "https://www.fijiairways.com",
        "source": "mock",
    },
    {
        "id": "FL005", "airline": "Japan Airlines", "flight_number": "JL505",
        "departure_time": "14:30", "arrival_time": "12:30+1",
        "duration": "11h 30m", "stops": 1,
        "price": 58000.0, "currency": "INR", "cabin_class": "Premium Economy",
        "booking_url": "https://www.jal.com",
        "source": "mock",
    },
]

MOCK_HOTELS = [
    {
        "id": "HT001", "name": "Grand Hyatt", "stars": 5, "rating": 4.7,
        "address": "Grand Hyatt Plaza, Destination City",
        "price_per_night": 12000.0, "currency": "INR",
        "amenities": ["WiFi", "Pool", "Spa", "Restaurant", "Gym"],
        "booking_url": "https://www.hyatt.com",
        "latitude": 48.8566, "longitude": 2.3522,
    },
    {
        "id": "HT002", "name": "Boutique Heritage Hotel", "stars": 4, "rating": 4.5,
        "address": "Old Town, Destination City",
        "price_per_night": 7500.0, "currency": "INR",
        "amenities": ["WiFi", "Breakfast", "Bar", "Rooftop"],
        "booking_url": "https://www.booking.com",
        "latitude": 48.8546, "longitude": 2.3495,
    },
    {
        "id": "HT003", "name": "City Centre Inn", "stars": 3, "rating": 4.2,
        "address": "Central Business District",
        "price_per_night": 3500.0, "currency": "INR",
        "amenities": ["WiFi", "Parking"],
        "booking_url": "https://www.hotels.com",
        "latitude": 48.8600, "longitude": 2.3550,
    },
    {
        "id": "HT004", "name": "Aman Tokyo", "stars": 5, "rating": 4.9,
        "address": "Otemachi Tower, Tokyo, Japan",
        "price_per_night": 95000.0, "currency": "INR",
        "amenities": ["WiFi", "Spa", "Pool", "City View", "Fine Dining"],
        "booking_url": "https://www.aman.com",
        "latitude": 35.6852, "longitude": 139.7641,
    },
    {
        "id": "HT005", "name": "Ritz-Carlton Kyoto", "stars": 5, "rating": 4.8,
        "address": "Kamogawa River, Kyoto, Japan",
        "price_per_night": 85000.0, "currency": "INR",
        "amenities": ["WiFi", "Onsen Spa", "River View", "Restaurant"],
        "booking_url": "https://www.ritzcarlton.com",
        "latitude": 35.0116, "longitude": 135.7681,
    },
    {
        "id": "HT006", "name": "Four Seasons Mexico City", "stars": 5, "rating": 4.8,
        "address": "Paseo de la Reforma, Mexico City, Mexico",
        "price_per_night": 45000.0, "currency": "INR",
        "amenities": ["WiFi", "Courtyard", "Pool", "Bar", "Spa"],
        "booking_url": "https://www.fourseasons.com",
        "latitude": 19.4244, "longitude": -99.1751,
    },
    {
        "id": "HT007", "name": "Xcaret Arte Cancun", "stars": 4, "rating": 4.6,
        "address": "Riviera Maya, Cancun, Mexico",
        "price_per_night": 38000.0, "currency": "INR",
        "amenities": ["WiFi", "All-Inclusive", "Beachfront", "Pool"],
        "booking_url": "https://www.hotelxcaret.com",
        "latitude": 20.5807, "longitude": -87.1197,
    },
]

MOCK_ACTIVITIES = {
    "paris": [
        {"id": "A01", "name": "Eiffel Tower", "type": "landmark",
         "description": "Iconic iron lattice tower on the Champ de Mars. Book summit tickets in advance.", "duration_hours": 3.0, "price": 2500.0, "currency": "INR", "best_time": "Afternoon", "booking_required": True},
        {"id": "A02", "name": "Louvre Museum", "type": "museum",
         "description": "World's largest art museum — Mona Lisa, Venus de Milo, 35,000+ works.", "duration_hours": 4.0, "price": 1800.0, "currency": "INR", "best_time": "Morning", "booking_required": True},
        {"id": "A03", "name": "Seine River Cruise", "type": "experience",
         "description": "1-hour twilight cruise past Notre-Dame, Louvre, and Eiffel Tower.", "duration_hours": 1.0, "price": 1500.0, "currency": "INR", "best_time": "Evening", "booking_required": False},
        {"id": "A04", "name": "Montmartre & Sacré-Cœur", "type": "neighborhood",
         "description": "Artistic hilltop quarter with iconic basilica and street painters.", "duration_hours": 3.0, "price": 0.0, "currency": "INR", "best_time": "Afternoon", "booking_required": False},
        {"id": "A05", "name": "French Cooking Class", "type": "food",
         "description": "Learn croissants & boeuf bourguignon with a professional chef.", "duration_hours": 3.0, "price": 5000.0, "currency": "INR", "best_time": "Morning", "booking_required": True},
    ],
    "london": [
        {"id": "L01", "name": "British Museum", "type": "museum",
         "description": "8 million works spanning 2 million years of world history.", "duration_hours": 4.0, "price": 0.0, "currency": "INR", "best_time": "Morning", "booking_required": False},
        {"id": "L02", "name": "Tower of London", "type": "landmark",
         "description": "Historic castle on the Thames housing the Crown Jewels.", "duration_hours": 3.0, "price": 3500.0, "currency": "INR", "best_time": "Morning", "booking_required": True},
        {"id": "L03", "name": "Thames River Cruise", "type": "experience",
         "description": "Scenic boat ride past Big Ben, Tower Bridge & the Shard.", "duration_hours": 1.5, "price": 1800.0, "currency": "INR", "best_time": "Afternoon", "booking_required": False},
        {"id": "L04", "name": "Borough Market Food Tour", "type": "food",
         "description": "London's oldest food market — artisan cheeses, street food, spices.", "duration_hours": 2.0, "price": 0.0, "currency": "INR", "best_time": "Morning", "booking_required": False},
    ],
    "dubai": [
        {"id": "D01", "name": "Burj Khalifa Observation Deck", "type": "landmark",
         "description": "World's tallest building — 360° views from the 148th floor.", "duration_hours": 2.0, "price": 4500.0, "currency": "INR", "best_time": "Evening", "booking_required": True},
        {"id": "D02", "name": "Desert Safari", "type": "adventure",
         "description": "Dune bashing, camel riding, BBQ dinner under the stars.", "duration_hours": 6.0, "price": 5000.0, "currency": "INR", "best_time": "Afternoon", "booking_required": True},
        {"id": "D03", "name": "Gold Souk & Spice Souk", "type": "shopping",
         "description": "Traditional markets — gold jewellery, exotic spices, perfumes.", "duration_hours": 2.0, "price": 0.0, "currency": "INR", "best_time": "Morning", "booking_required": False},
        {"id": "D04", "name": "Dubai Museum of the Future", "type": "museum",
         "description": "Stunning torus-shaped building exploring future civilisation.", "duration_hours": 2.0, "price": 3600.0, "currency": "INR", "best_time": "Afternoon", "booking_required": True},
    ],
    "barcelona": [
        {"id": "B01", "name": "Sagrada Familia","type": "landmark",
         "description": "Iconic basilica designed by Antoni Gaudí, still under construction.",
         "duration_hours": 2.0, "price": 1500, "currency": "INR", "best_time": "Morning",   "booking_required": True,
         "latitude": 41.4036, "longitude": 2.1744},
        {"id": "B02", "name": "Park Güell", "type": "landmark",
         "description": "Colorful park with architectural elements by Gaudí.",
         "duration_hours": 2.5, "price": 1200, "currency": "INR", "best_time": "Afternoon", "booking_required": True,
         "latitude": 41.4145, "longitude": 2.1527},
        {"id": "B03", "name": "La Boqueria Market","type": "food",
         "description": "Famous market with fresh produce, tapas, and local delicacies.",
         "duration_hours": 2.0, "price": 1000, "currency": "INR", "best_time": "Morning",   "booking_required": False,
         "latitude": 41.3825, "longitude": 2.1710},
        {"id": "B04", "name": "Casa Batlló","type": "landmark",
         "description": "Modernist building designed by Antoni Gaudí, known for its unique architecture.",
         "duration_hours": 1.5, "price": 800,  "currency": "INR", "best_time": "Afternoon", "booking_required": True,
         "latitude": 41.3917, "longitude": 2.1649},
    ],
    "bangkok": [
        {"id": "B01", "name": "Grand Palace & Wat Phra Kaew","type": "landmark",
         "description": "Thailand's most sacred temple complex. Home of the Emerald Buddha.",
         "duration_hours": 3.0, "price": 1200, "currency": "INR", "best_time": "Morning",   "booking_required": False,
         "latitude": 13.7500, "longitude": 100.4914},
        {"id": "B02", "name": "Floating Market Tour", "type": "experience",
         "description": "Damnoen Saduak floating market — fresh fruit, pad thai, traditional boats.",
         "duration_hours": 4.0, "price": 2500, "currency": "INR", "best_time": "Morning",   "booking_required": True,
         "latitude": 13.5214, "longitude": 100.0748},
        {"id": "B03", "name": "Street Food Walk – Yaowarat","type": "food",
         "description": "Bangkok's Chinatown at night — roast duck, mango sticky rice, oyster omelette.",
         "duration_hours": 2.5, "price": 1000, "currency": "INR", "best_time": "Evening",   "booking_required": False,
         "latitude": 13.7399, "longitude": 100.5136},
        {"id": "B04", "name": "Wat Arun (Temple of Dawn)","type": "landmark",
         "description": "Iconic riverside temple encrusted with colourful porcelain mosaic.",
         "duration_hours": 1.5, "price": 500,  "currency": "INR", "best_time": "Afternoon", "booking_required": False,
         "latitude": 13.7436, "longitude": 100.4888},
    ],
    "delhi": [
        {"id": "D01", "name": "Red Fort","type": "landmark",
         "description": "Historic fort in the city of Delhi, India.",
         "duration_hours": 3.0, "price": 1200, "currency": "INR", "best_time": "Morning",   "booking_required": False,
         "latitude": 28.6562, "longitude": 77.2410},
        {"id": "D02", "name": "Qutub Minar", "type": "historical",
         "description": "Tallest brick minaret in the world, a UNESCO World Heritage Site.",
         "duration_hours": 2.0, "price": 800, "currency": "INR", "best_time": "Morning",   "booking_required": True,
         "latitude": 28.5244, "longitude": 77.1855},
         {"id": "D03", "name": "India Gate", "type": "landmark",
          "description": "War memorial located in the heart of New Delhi.",
          "duration_hours": 1.5, "price": 0, "currency": "INR", "best_time": "Afternoon", "booking_required": False,
          "latitude": 28.6129, "longitude": 77.2295}
        ],
          "mexico city": [
        {"id": "MX01", "name": "Chapultepec Castle","type": "landmark",
         "description": "Historic castle with museums and beautiful views of the city.",
         "duration_hours": 3.0, "price": 200, "currency": "MXN", "best_time": "Morning",   "booking_required": True,
         "latitude": 19.4200, "longitude": -99.1810},
        {"id": "MX02", "name": "Frida Kahlo Museum",    "type": "museum",
         "description": "Explore the life and works of the iconic Mexican artist.",
         "duration_hours": 2.0, "price": 150, "currency": "MXN", "best_time": "Morning",   "booking_required": True,
         "latitude": 19.3550, "longitude": -99.1620},
        {"id": "MX03", "name": "Chapultepec Park",    "type": "nature",
         "description": "843 acres of urban parkland — lakes, gardens, and cultural attractions.",
         "duration_hours": 3.0, "price": 0,    "currency": "MXN", "best_time": "Morning",   "booking_required": False,
         "latitude": 19.4200, "longitude": -99.1810},
        {"id": "MX04", "name": "Metropolitan Museum",  "type": "museum",
         "description": "One of the world's greatest art museums — 2 million works across 5,000 years.",
         "duration_hours": 4.0, "price": 2800, "currency": "MXN", "best_time": "Morning",   "booking_required": False,
         "latitude": 19.3550, "longitude": -99.1620},
        {"id": "MX05", "name": "Brooklyn Bridge Walk & DUMBO","type": "neighborhood",
         "description": "Walk the iconic bridge, explore DUMBO's cobblestone streets and food scene.",
         "duration_hours": 3.0, "price": 0,    "currency": "MXN", "best_time": "Afternoon", "booking_required": False,
         "latitude": 19.4200, "longitude": -99.1810},
        {"id": "MX06", "name": "High Line & Chelsea Market","type": "experience",
         "description": "Elevated park on old rail tracks with art, gardens, and amazing city views.",
         "duration_hours": 2.5, "price": 0,    "currency": "MXN", "best_time": "Afternoon", "booking_required": False,
         "latitude": 19.3550, "longitude": -99.1620},
    ],
    "default": [
        {"id": "G01", "name": "City Walking Tour", "type": "tour",
         "description": "Explore highlights with a knowledgeable local guide.", "duration_hours": 3.0, "price": 800.0, "currency": "INR", "best_time": "Morning", "booking_required": False},
        {"id": "G02", "name": "Local Food Market", "type": "food",
         "description": "Discover local flavours and culinary traditions.", "duration_hours": 2.0, "price": 500.0, "currency": "INR", "best_time": "Morning", "booking_required": False},
        {"id": "G03", "name": "Cultural Museum", "type": "museum",
         "description": "Dive into the rich history and culture of the region.", "duration_hours": 2.5, "price": 600.0, "currency": "INR", "best_time": "Afternoon", "booking_required": False},
        {"id": "G04", "name": "Sunset Viewpoint", "type": "nature",
         "description": "Best vantage point in the city for the golden hour.", "duration_hours": 1.5, "price": 0.0, "currency": "INR", "best_time": "Evening", "booking_required": False},
        {"id": "G05", "name": "Evening Street Food Walk", "type": "food",
         "description": "Local street food scene — try the must-have bites.", "duration_hours": 2.0, "price": 700.0, "currency": "INR", "best_time": "Evening", "booking_required": False},
    ],
}

CITY_CODES = {
    "mumbai": "BOM", "delhi": "DEL", "bangalore": "BLR", "chennai": "MAA",
    "kolkata": "CCU", "hyderabad": "HYD", "ahmedabad": "AMD",
    "paris": "PAR", "london": "LON", "dubai": "DXB",
    "new york": "NYC", "new york city": "NYC",
    "singapore": "SIN", "tokyo": "TYO", "bangkok": "BKK",
    "bali": "DPS", "sydney": "SYD", "los angeles": "LAX",
    "rome": "ROM", "barcelona": "BCN", "amsterdam": "AMS",
}


# ── Main class ───────────────────────────────────────────────────────────────

class AmadeusTools:
    """Wrapper that tries the real SDK first, falls back to mock data."""

    def _init_(self):
        self._client = None
        self._mock   = True
        self._init()

    def _init(self):
        try:
            from amadeus import Client
            from backend.config import settings
            if settings.amadeus_client_id not in ("", "test_client_id", "your_amadeus_client_id"):
                self._client = Client(
                    client_id     = settings.amadeus_client_id,
                    client_secret = settings.amadeus_client_secret,
                    hostname      = settings.amadeus_hostname,
                )
                self._mock = False
        except Exception:
            pass

    # ── City code ─────────────────────────────────────────────────────────────

    async def get_city_code(self, city: str) -> str:
        code = CITY_CODES.get(city.lower().strip())
        if code:
            return code
        if not self._mock and self._client:
            try:
                loop = asyncio.get_event_loop()
                resp = await loop.run_in_executor(
                    None,
                    lambda: self._client.reference_data.locations.get(
                        keyword=city, subType="CITY"
                    ),
                )
                if resp.data:
                    return resp.data[0]["iataCode"]
            except Exception:
                pass
        return city[:3].upper()

    # ── Flights ───────────────────────────────────────────────────────────────

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        travel_class: str = "ECONOMY",
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        if self._mock:
            await asyncio.sleep(0.4)
            return MOCK_FLIGHTS

        try:
            loop   = asyncio.get_event_loop()
            kwargs = {
                "originLocationCode":      origin,
                "destinationLocationCode": destination,
                "departureDate":           departure_date,
                "adults":                  adults,
                "travelClass":             travel_class,
                "max":                     max_results,
            }
            if return_date:
                kwargs["returnDate"] = return_date

            resp = await loop.run_in_executor(
                None, lambda: self._client.shopping.flight_offers_search.get(**kwargs)
            )
            return self._parse_flights(resp.data)
        except Exception:
            return MOCK_FLIGHTS

    def _parse_flights(self, data: List[Dict]) -> List[Dict]:
        results = []
        for offer in data:
            try:
                itin  = offer["itineraries"][0]
                seg0  = itin["segments"][0]
                segN  = itin["segments"][-1]
                price = offer["price"]
                results.append({
                    "id":             offer["id"],
                    "airline":        seg0["carrierCode"],
                    "flight_number":  f"{seg0['carrierCode']}-{seg0['number']}",
                    "departure_time": seg0["departure"]["at"][11:16],
                    "arrival_time":   segN["arrival"]["at"][11:16],
                    "duration":       itin["duration"].replace("PT", "").lower(),
                    "stops":          len(itin["segments"]) - 1,
                    "price":          float(price["total"]),
                    "currency":       price["currency"],
                    "cabin_class":    "Economy",
                    "booking_url":    "https://www.amadeus.com",
                })
            except (KeyError, IndexError):
                continue
        return results or MOCK_FLIGHTS

    # ── Hotels ───────────────────────────────────────────────────────────────

    async def search_hotels(
        self,
        city_code: str,
        check_in: str,
        check_out: str,
        adults: int = 1,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        if self._mock:
            await asyncio.sleep(0.4)
            return MOCK_HOTELS

        try:
            loop = asyncio.get_event_loop()

            def _sync():
                ids = self._client.reference_data.locations.hotels.by_city.get(
                    cityCode=city_code, radius=5, radiusUnit="KM", ratings=[3, 4, 5]
                ).data
                hotel_ids = [h["hotelId"] for h in ids[:15]]
                return self._client.shopping.hotel_offers_search.get(
                    hotelIds=",".join(hotel_ids[:10]),
                    checkInDate=check_in,
                    checkOutDate=check_out,
                    adults=adults,
                ).data

            data = await loop.run_in_executor(None, _sync)
            parsed = self._parse_hotels(data)
            return parsed[:max_results] if parsed else MOCK_HOTELS
        except Exception:
            return MOCK_HOTELS

    def _parse_hotels(self, data: List[Dict]) -> List[Dict]:
        results = []
        for item in data:
            try:
                h     = item.get("hotel", {})
                offer = (item.get("offers") or [{}])[0]
                price = offer.get("price", {})
                results.append({
                    "id":               h.get("hotelId", ""),
                    "name":             h.get("name", "Hotel"),
                    "stars":            int(h.get("rating", 3)),
                    "rating":           4.0,
                    "address":          (h.get("address") or {}).get("lines", [""])[0],
                    "price_per_night":  float(price.get("total", 0)),
                    "currency":         price.get("currency", "USD"),
                    "amenities":        h.get("amenities", [])[:6],
                    "booking_url":      "https://www.amadeus.com",
                    "latitude":         h.get("latitude", 0.0),
                    "longitude":        h.get("longitude", 0.0),
                })
            except (KeyError, TypeError):
                continue
        return results

    # ── Activities ───────────────────────────────────────────────────────────

    async def get_activities(self, destination: str) -> List[Dict[str, Any]]:
        """Returns curated activity list for the destination."""
        await asyncio.sleep(0.2)
        key = destination.lower().strip()
        for k, v in MOCK_ACTIVITIES.items():
            if k in key or key in k:
                return v
        return MOCK_ACTIVITIES["default"]


amadeus_tools = AmadeusTools()