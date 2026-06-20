# backend/tools/travel_tools.py
"""
Multi-Provider Travel Tools
============================
Supports 4 providers in a priority chain. Set TRAVEL_PROVIDER in .env to choose.

  TRAVEL_PROVIDER=amadeus       → Amadeus API (requires paid/sandbox key)
  TRAVEL_PROVIDER=duffel        → Duffel API   (modern, free sandbox)
  TRAVEL_PROVIDER=opentripmap   → OpenTripMap + RapidAPI (fully free)
  TRAVEL_PROVIDER=mock          → Rich mock data, no API key needed (default)

The class auto-detects which provider to use based on which keys are present.
Falls back to rich mock data if no keys are configured.
"""

import asyncio
import httpx
from typing import Any, Dict, List, Optional


# ════════════════════════════════════════════════════════════════════
#  RICH MOCK DATA  (used when no API keys are configured)
# ════════════════════════════════════════════════════════════════════

MOCK_FLIGHTS = [
    {
        "id": "FL001", "airline": "Air India",  "flight_number": "AII202",
        "departure_time": "06:00", "arrival_time": "14:30",
        "duration": "8h 30m",  "stops": 0,
        "price": 45000.0, "currency": "INR", "cabin_class": "Business",
        "booking_url": "https://www.airindia.com",
        "source": "mock",
    },
    {
        "id": "FL002", "airline": "IndiGo", "flight_number": "6EE501",
        "departure_time": "09:15", "arrival_time": "17:45",
        "duration": "8h 30m",  "stops": 1,
        "price": 5000.0, "currency": "INR", "cabin_class": "Business",
        "booking_url": "https://www.goindigo.in",
        "source": "mock",
    },
    {
        "id": "FL003", "airline": "Emirates", "flight_number": "EK505",
        "departure_time": "23:00",
        "duration": "11h 30m", "stops": 1,
        "price": 40000.0, "currency": "INR", "cabin_class": "Economy",
        "booking_url": "https://www.emirates.com",
        "source": "mock",
    },
    {
        "id": "FL004", "airline": "Fiji Airways", "flight_number": "FJ505",
        "departure_time": "01:00",
        "duration": "11h 30m", "stops": 2,
        "price": 20000.0, "currency": "INR", "cabin_class": "Premium Economy",
        "booking_url": "https://www.fijiairways.com",
        "source": "mock",
    },
    {
        "id": "FL005", "airline": "Japan Airlines", "flight_number": "JL505",
        "departure_time": "14:30",
        "duration": "11h 30m", "stops": 1,
        "price": 15000.0, "currency": "INR", "cabin_class": "Premium Economy",
        "booking_url": "https://www.jal.com",
        "source": "mock",
    },
]

MOCK_HOTELS = [
    {
        "id": "HT001", "name": "Grand Hyatt", "stars": 5, "rating": 4.7,
        "address": "Grand Hyatt Plaza, City Centre",
        "price_per_night": 22000.0, "currency": "INR",
        "amenities": ["WiFi", "Pool", "Spa", "Restaurant", "Gym"],
        "booking_url": "https://www.hyatt.com",
        "latitude": 48.8566, "longitude": 2.3522,
        "source": "mock",
    },
    {
        "id": "HT002", "name": "Boutique Heritage Hotel", "stars": 4, "rating": 4.5,
        "address": "Old Town, Historic Quarter",
        "price_per_night": 25200.0, "currency": "INR",
        "amenities": ["WiFi", "Breakfast", "Bar", "Rooftop"],
        "booking_url": "https://www.booking.com",
        "latitude": 48.8546, "longitude": 2.3495,
        "source": "mock",
    },
    {
        "id": "HT003", "name": "City Centre Inn", "stars": 3, "rating": 4.2,
        "address": "Central Business District",
        "price_per_night": 3500.0, "currency": "INR",
        "amenities": ["WiFi", "Parking", "24hr Reception"],
        "booking_url": "https://www.hotels.com",
        "latitude": 48.8600, "longitude": 2.3550,
        "source": "mock",
    },
    {
        "id": "HT004", "name": "Aman Tokyo", "stars": 5, "rating": 4.9,
        "address": "Otemachi Tower, Tokyo, Japan",
        "price_per_night": 95000.0, "currency": "INR",
        "amenities": ["WiFi", "Spa", "Pool", "City View", "Fine Dining"],
        "booking_url": "https://www.aman.com",
        "latitude": 35.6852, "longitude": 139.7641,
        "source": "mock",
    },
    {
        "id": "HT005", "name": "Ritz-Carlton Kyoto", "stars": 5, "rating": 4.8,
        "address": "Kamogawa River, Kyoto, Japan",
        "price_per_night": 85000.0, "currency": "INR",
        "amenities": ["WiFi", "Onsen Spa", "River View", "Restaurant"],
        "booking_url": "https://www.ritzcarlton.com",
        "latitude": 35.0116, "longitude": 135.7681,
        "source": "mock",
    },
    {
        "id": "HT006", "name": "Four Seasons Mexico City", "stars": 5, "rating": 4.8,
        "address": "Paseo de la Reforma, Mexico City, Mexico",
        "price_per_night": 45000.0, "currency": "INR",
        "amenities": ["WiFi", "Courtyard", "Pool", "Bar", "Spa"],
        "booking_url": "https://www.fourseasons.com",
        "latitude": 19.4244, "longitude": -99.1751,
        "source": "mock",
    },
    {
        "id": "HT007", "name": "Xcaret Arte Cancun", "stars": 4, "rating": 4.6,
        "address": "Riviera Maya, Cancun, Mexico",
        "price_per_night": 38000.0, "currency": "INR",
        "amenities": ["WiFi", "All-Inclusive", "Beachfront", "Pool"],
        "booking_url": "https://www.hotelxcaret.com",
        "latitude": 20.5807, "longitude": -87.1197,
        "source": "mock",
    },
    {
        "id": "HT008", "name": "Eurostars Barcelona Central", "stars": 4, "rating": 4.6,
        "address": "Barcelona, Spain",
        "price_per_night": 27554.0, "currency": "INR",
        "amenities": ["WiFi", "All-Inclusive", "Beachfront", "Pool"],
        "booking_url": "https://www.eurostars.com",
        "latitude": 41.3851, "longitude": 2.1734,
        "source": "mock",
    },
    {
        "id": "HT009", "name": "The Wall Street Hotel", "stars": 5, "rating": 4.6,
        "address": "New York City, USA",
        "price_per_night": 43335.0, "currency": "INR",
        "amenities": ["WiFi", "All-Inclusive", "GYM", "Pool"],
        "booking_url": "https://www.wallstreethotel.com",
        "latitude": 40.7128, "longitude": -74.0060,
        "source": "mock",
    },
]

MOCK_ACTIVITIES: Dict[str, List[Dict]] = {
    "paris": [
        {"id": "P01", "name": "Eiffel Tower",          "type": "landmark",
         "description": "Iconic iron lattice tower. Book summit tickets in advance for the best views.",
         "duration_hours": 3.0, "price": 2500, "currency": "INR", "best_time": "Afternoon", "booking_required": True,
         "latitude": 48.8584, "longitude": 2.2945},
        {"id": "P02", "name": "Louvre Museum",         "type": "museum",
         "description": "World's largest art museum. Mona Lisa, Venus de Milo, 35,000+ masterpieces.",
         "duration_hours": 4.0, "price": 1800, "currency": "INR", "best_time": "Morning",   "booking_required": True,
         "latitude": 48.8606, "longitude": 2.3376},
        {"id": "P03", "name": "Seine River Cruise",    "type": "experience",
         "description": "1-hour twilight cruise passing Notre-Dame, the Louvre, and an illuminated Eiffel Tower.",
         "duration_hours": 1.0, "price": 1500, "currency": "INR", "best_time": "Evening",   "booking_required": False,
         "latitude": 48.8583, "longitude": 2.3469},
        {"id": "P04", "name": "Montmartre Walk",       "type": "neighborhood",
         "description": "Explore the bohemian hilltop neighbourhood, street artists, and Sacré-Cœur basilica.",
         "duration_hours": 3.0, "price": 0,    "currency": "INR", "best_time": "Afternoon", "booking_required": False,
         "latitude": 48.8867, "longitude": 2.3431},
        {"id": "P05", "name": "French Cooking Class",  "type": "food",
         "description": "Learn croissants, coq au vin, and crème brûlée with a professional Parisian chef.",
         "duration_hours": 3.0, "price": 5000, "currency": "INR", "best_time": "Morning",   "booking_required": True,
         "latitude": 48.8640, "longitude": 2.3410},
    ],
    "london": [
        {"id": "L01", "name": "British Museum",        "type": "museum",
         "description": "8 million artefacts spanning 2 million years of world history. Free entry.",
         "duration_hours": 4.0, "price": 0,    "currency": "INR", "best_time": "Morning",   "booking_required": False,
         "latitude": 51.5194, "longitude": -0.1270},
        {"id": "L02", "name": "Tower of London",       "type": "landmark",
         "description": "900-year-old royal fortress housing the Crown Jewels. Book online to skip the queue.",
         "duration_hours": 3.0, "price": 3500, "currency": "INR", "best_time": "Morning",   "booking_required": True,
         "latitude": 51.5081, "longitude": -0.0759},
        {"id": "L03", "name": "Thames River Cruise",   "type": "experience",
         "description": "Scenic boat ride past Big Ben, Tower Bridge, the Shard, and Greenwich.",
         "duration_hours": 1.5, "price": 1800, "currency": "INR", "best_time": "Afternoon", "booking_required": False,
         "latitude": 51.5074, "longitude": -0.1196},
        {"id": "L04", "name": "Borough Market",        "type": "food",
         "description": "London's oldest food market — artisan bread, cheese, street food, craft beer.",
         "duration_hours": 2.0, "price": 0,    "currency": "INR", "best_time": "Morning",   "booking_required": False,
         "latitude": 51.5055, "longitude": -0.0910},
        {"id": "L05", "name": "Notting Hill Walk",     "type": "neighborhood",
         "description": "Colourful terraced houses, Portobello Road antique market, indie cafés.",
         "duration_hours": 2.5, "price": 0,    "currency": "INR", "best_time": "Afternoon", "booking_required": False,
         "latitude": 51.5160, "longitude": -0.2015},
    ],
    "dubai": [
        {"id": "D01", "name": "Burj Khalifa Deck",     "type": "landmark",
         "description": "World's tallest building — 360° views from the 148th-floor observation deck.",
         "duration_hours": 2.0, "price": 4500, "currency": "INR", "best_time": "Evening",   "booking_required": True,
         "latitude": 25.1972, "longitude": 55.2744},
        {"id": "D02", "name": "Desert Safari",         "type": "adventure",
         "description": "Dune bashing in a 4x4, camel ride, belly dancing, BBQ dinner under the stars.",
         "duration_hours": 6.0, "price": 5000, "currency": "INR", "best_time": "Afternoon", "booking_required": True,
         "latitude": 24.9857, "longitude": 55.3522},
        {"id": "D03", "name": "Gold & Spice Souks",    "type": "shopping",
         "description": "Traditional markets: glittering gold jewellery, exotic spices, oud perfumes.",
         "duration_hours": 2.0, "price": 0,    "currency": "INR", "best_time": "Morning",   "booking_required": False,
         "latitude": 25.2631, "longitude": 55.2992},
        {"id": "D04", "name": "Museum of the Future",  "type": "museum",
         "description": "Stunning torus-shaped building showcasing AI, space, and future civilisation.",
         "duration_hours": 2.5, "price": 3600, "currency": "INR", "best_time": "Afternoon", "booking_required": True,
         "latitude": 25.2197, "longitude": 55.2814},
        {"id": "D05", "name": "Dubai Creek Dhow Cruise","type": "experience",
         "description": "Traditional wooden dhow dinner cruise on Dubai Creek with live entertainment.",
         "duration_hours": 2.0, "price": 2800, "currency": "INR", "best_time": "Evening",   "booking_required": True,
         "latitude": 25.2637, "longitude": 55.3089},
    ],
    "singapore": [
        {"id": "S01", "name": "Gardens by the Bay",    "type": "nature",
         "description": "Futuristic Supertree Grove and Cloud Forest domes. Spectacular light show at night.",
         "duration_hours": 3.0, "price": 2000, "currency": "INR", "best_time": "Evening",   "booking_required": False,
         "latitude": 1.2816, "longitude": 103.8636},
        {"id": "S02", "name": "Marina Bay Sands SkyPark","type": "landmark",
         "description": "Iconic infinity pool and observation deck atop the 57th-floor hotel.",
         "duration_hours": 1.5, "price": 2500, "currency": "INR", "best_time": "Afternoon", "booking_required": True,
         "latitude": 1.2834, "longitude": 103.8607},
        {"id": "S03", "name": "Hawker Centre Food Tour","type": "food",
         "description": "Maxwell or Lau Pa Sat hawker centres — chilli crab, laksa, char kway teow.",
         "duration_hours": 2.0, "price": 800,  "currency": "INR", "best_time": "Evening",   "booking_required": False,
         "latitude": 1.2803, "longitude": 103.8456},
        {"id": "S04", "name": "Sentosa Island",        "type": "experience",
         "description": "Universal Studios, Adventure Cove waterpark, beach clubs, cable car.",
         "duration_hours": 6.0, "price": 5500, "currency": "INR", "best_time": "Morning",   "booking_required": True,
         "latitude": 1.2494, "longitude": 103.8303},
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
          "latitude": 28.6129, "longitude": 77.2295},
         {"id": "D04", "name": "Chandni Chowk Street Food Tour", "type": "food",
          "description": "Guided tasting tour of Delhi's most famous historic food street featuring chaat, parathas, and jalebis.",
          "duration_hours": 3.0, "price": 1500, "currency": "INR", "best_time": "Evening", "booking_required": True,
          "latitude": 28.6505, "longitude": 77.2303},
         {"id": "D05", "name": "Luxury Ayurvedic Spa Retreat", "type": "wellness & relaxation",
          "description": "Traditional Ayurvedic massages and relaxation therapies in a serene wellness center.",
          "duration_hours": 2.5, "price": 4500, "currency": "INR", "best_time": "Afternoon", "booking_required": True,
          "latitude": 28.5355, "longitude": 77.2410}],
    "new york": [
        {"id": "NY01", "name": "Statue of Liberty & Ellis Island","type": "landmark",
         "description": "Ferry to Liberty Island and Ellis Island immigration museum. Book in advance.",
         "duration_hours": 4.0, "price": 3500, "currency": "INR", "best_time": "Morning",   "booking_required": True,
         "latitude": 40.6892, "longitude": -74.0445},
        {"id": "NY02", "name": "Central Park Walk",    "type": "nature",
         "description": "843 acres of urban parkland — Bethesda Terrace, Strawberry Fields, The Mall.",
         "duration_hours": 3.0, "price": 0,    "currency": "INR", "best_time": "Morning",   "booking_required": False,
         "latitude": 40.7851, "longitude": -73.9683},
        {"id": "NY03", "name": "Metropolitan Museum",  "type": "museum",
         "description": "One of the world's greatest art museums — 2 million works across 5,000 years.",
         "duration_hours": 4.0, "price": 2800, "currency": "INR", "best_time": "Morning",   "booking_required": False,
         "latitude": 40.7794, "longitude": -73.9632},
        {"id": "NY04", "name": "Brooklyn Bridge Walk & DUMBO","type": "neighborhood",
         "description": "Walk the iconic bridge, explore DUMBO's cobblestone streets and food scene.",
         "duration_hours": 3.0, "price": 0,    "currency": "INR", "best_time": "Afternoon", "booking_required": False,
         "latitude": 40.7061, "longitude": -73.9969},
        {"id": "NY05", "name": "High Line & Chelsea Market","type": "experience",
         "description": "Elevated park on old rail tracks with art, gardens, and amazing city views.",
         "duration_hours": 2.5, "price": 0,    "currency": "INR", "best_time": "Afternoon", "booking_required": False,
         "latitude": 40.7480, "longitude": -74.0048},
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
        {"id": "G01", "name": "City Walking Tour",     "type": "tour",
         "description": "Explore the city's highlights and hidden gems with a knowledgeable local guide.",
         "duration_hours": 3.0, "price": 800,  "currency": "INR", "best_time": "Morning",   "booking_required": False,
         "latitude": 0, "longitude": 0},
        {"id": "G02", "name": "Local Food Market",     "type": "food",
         "description": "Discover local flavours, street food, and culinary traditions at the central market.",
         "duration_hours": 2.0, "price": 500,  "currency": "INR", "best_time": "Morning",   "booking_required": False,
         "latitude": 0, "longitude": 0},
        {"id": "G03", "name": "Cultural Museum",       "type": "museum",
         "description": "Dive into the rich history, art, and culture of the destination.",
         "duration_hours": 2.5, "price": 600,  "currency": "INR", "best_time": "Afternoon", "booking_required": False,
         "latitude": 0, "longitude": 0},
        {"id": "G04", "name": "Sunset Viewpoint",      "type": "nature",
         "description": "Catch a breathtaking sunset from the city's most iconic viewpoint.",
         "duration_hours": 1.5, "price": 0,    "currency": "INR", "best_time": "Evening",   "booking_required": False,
         "latitude": 0, "longitude": 0},
        {"id": "G05", "name": "Evening Street Food Walk","type": "food",
         "description": "Guided walk through the best street food stalls and night market.",
         "duration_hours": 2.0, "price": 700,  "currency": "INR", "best_time": "Evening",   "booking_required": False,
         "latitude": 0, "longitude": 0},
        {"id": "G06", "name": "Day Trip to Countryside","type": "adventure",
         "description": "Escape the city — scenic landscapes, local villages, and nature trails.",
         "duration_hours": 8.0, "price": 2000, "currency": "INR", "best_time": "Morning",   "booking_required": True,
         "latitude": 0, "longitude": 0},
    ],
}

CITY_CODES = {
    "mumbai": "BOM", "bhubaneswar": "BBI", "delhi": "DEL", "bangalore": "BLR", "bengaluru": "BLR",
    "chennai": "MAA", "kolkata": "CCU", "hyderabad": "HYD", "ahmedabad": "AMD",
    "paris": "CDG", "london": "LHR", "dubai": "DXB", "new york": "JFK",
    "new york city": "JFK", "singapore": "SIN", "tokyo": "NRT", "bangkok": "BKK", "kuala lumpur": "KUL",
    "bali": "DPS", "sydney": "SYD", "los angeles": "LAX", "rome": "FCO", "nadi": "NAN",
    "barcelona": "BCN", "amsterdam": "AMS", "istanbul": "IST", "cairo": "CAI",
    "nairobi": "NBO", "johannesburg": "JNB", "toronto": "YYZ", "miami": "MIA", "mexico city": "MEX"
}


# ════════════════════════════════════════════════════════════════════
#  PROVIDER: DUFFEL  (https://duffel.com — free sandbox, no credit card)
# ════════════════════════════════════════════════════════════════════

class DuffelProvider:
    """
    Duffel is a modern flight booking API — better DX than Amadeus, free sandbox.
    Docs: https://duffel.com/docs
    Sandbox token starts with 'duffel_test_'
    """
    BASE = "https://api.duffel.com"

    def _init_(self, token: str):
        self.token = token
        self.headers = {
            "Authorization":  f"Bearer {token}",
            "Duffel-Version": "v2",
            "Content-Type":   "application/json",
            "Accept":         "application/json",
        }

    async def search_flights(
        self, origin: str, destination: str, departure_date: str,
        adults: int = 1, cabin_class: str = "economy", max_results: int = 5,
    ) -> List[Dict]:
        payload = {
            "data": {
                "slices": [{"origin": origin, "destination": destination, "departure_date": departure_date}],
                "passengers": [{"type": "adult"}] * adults,
                "cabin_class": cabin_class,
            }
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(f"{self.BASE}/air/offer_requests", json=payload, headers=self.headers)
            r.raise_for_status()
            request_id = r.json()["data"]["id"]

            offers = await client.get(
                f"{self.BASE}/air/offers?offer_request_id={request_id}&limit={max_results}",
                headers=self.headers,
            )
            offers.raise_for_status()
            return self._parse(offers.json()["data"])

    def _parse(self, offers: List[Dict]) -> List[Dict]:
        results = []
        for o in offers[:5]:
            try:
                sl  = o["slices"][0]
                seg = sl["segments"][0]
                results.append({
                    "id":             o["id"],
                    "airline":        seg["marketing_carrier"]["name"],
                    "flight_number":  f"{seg['marketing_carrier']['iata_code']}-{seg['marketing_carrier_flight_number']}",
                    "departure_time": seg["departing_at"][11:16],
                    "arrival_time":   sl["segments"][-1]["arriving_at"][11:16],
                    "duration":       f"{sl['duration'][:2]}h {sl['duration'][3:5]}m",
                    "stops":          len(sl["segments"]) - 1,
                    "price":          float(o["total_amount"]),
                    "currency":       o["total_currency"],
                    "cabin_class":    o["cabin_class"].title(),
                    "booking_url":    "https://duffel.com",
                    "source":         "duffel",
                })
            except (KeyError, IndexError):
                continue
        return results or MOCK_FLIGHTS


# ════════════════════════════════════════════════════════════════════
#  PROVIDER: OPENTRIPMAP  (https://opentripmap.io — 5000 req/day free)
# ════════════════════════════════════════════════════════════════════

class OpenTripMapProvider:
    """
    OpenTripMap: best free POI + hotel-adjacent data.
    Free API key: https://opentripmap.io/register
    5,000 requests / day free tier.
    """
    BASE = "https://api.opentripmap.com/0.1/en"

    def _init_(self, api_key: str):
        self.key = api_key

    async def get_places(self, destination: str, kinds: str = "interesting_places",
                         radius: int = 10000, limit: int = 10) -> List[Dict]:
        """Get POIs (activities, attractions) for a destination."""
        async with httpx.AsyncClient(timeout=15) as client:
            # Step 1: geocode the city
            geo = await client.get(
                f"{self.BASE}/places/geoname",
                params={"name": destination, "apikey": self.key},
            )
            geo.raise_for_status()
            g = geo.json()
            lat, lon = g["lat"], g["lon"]

            # Step 2: fetch POIs around the city
            pois = await client.get(
                f"{self.BASE}/places/radius",
                params={
                    "radius":   radius,
                    "lon":      lon,
                    "lat":      lat,
                    "kinds":    kinds,
                    "limit":    limit,
                    "apikey":   self.key,
                },
            )
            pois.raise_for_status()
            return self._parse_activities(pois.json().get("features", []))

    def _parse_activities(self, features: List[Dict]) -> List[Dict]:
        results = []
        for i, f in enumerate(features):
            props = f.get("properties", {})
            coords = f.get("geometry", {}).get("coordinates", [0, 0])
            results.append({
                "id":               f"OTM{i:03d}",
                "name":             props.get("name", "Unnamed Place"),
                "type":             (props.get("kinds", "attraction").split(",")[0]).replace("_", " "),
                "description":      f"Rated {props.get('rate','?')}/7 on OpenTripMap. {props.get('kinds','')}",
                "duration_hours":   2.0,
                "price":            0.0,
                "currency":         "INR",
                "best_time":        "Morning",
                "booking_required": False,
                "latitude":         coords[1] if len(coords) > 1 else 0,
                "longitude":        coords[0],
                "source":           "opentripmap",
            })
        return results

    async def get_hotels(self, destination: str, limit: int = 6) -> List[Dict]:
        """Get accommodation near a destination using OpenTripMap."""
        return await self.get_places(
            destination,
            kinds  = "accomodations",
            limit  = limit,
        )


# ════════════════════════════════════════════════════════════════════
#  PROVIDER: FOURSQUARE  (https://foursquare.com/developer — 950 calls/day free)
# ════════════════════════════════════════════════════════════════════

class FoursquareProvider:
    """
    Foursquare Places API — 950 free calls/day, great for activities & restaurants.
    Free key: https://foursquare.com/developer/
    """
    BASE = "https://api.foursquare.com/v3"

    def _init_(self, api_key: str):
        self.headers = {
            "Authorization": api_key,
            "Accept":        "application/json",
        }

    async def get_places(self, destination: str, categories: str = "16000",
                         limit: int = 10) -> List[Dict]:
        """
        Category IDs (Foursquare):
          16000 = Arts & Entertainment
          13000 = Dining & Drinking
          19000 = Outdoors & Recreation
          17000 = Retail (shopping)
        """
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{self.BASE}/places/search",
                params={
                    "near":       destination,
                    "categories": categories,
                    "limit":      limit,
                    "sort":       "POPULARITY",
                },
                headers=self.headers,
            )
            r.raise_for_status()
            return self._parse(r.json().get("results", []))

    def _parse(self, results: List[Dict]) -> List[Dict]:
        parsed = []
        for i, place in enumerate(results):
            cats = place.get("categories", [{}])
            cat  = cats[0].get("name", "Attraction") if cats else "Attraction"
            loc  = place.get("geocodes", {}).get("main", {})
            parsed.append({
                "id":               f"FSQ{i:03d}",
                "name":             place.get("name", "Unknown"),
                "type":             cat.lower().replace(" ", "_"),
                "description":      f"{place.get('name','')} — {cat} in {place.get('location',{}).get('locality','')}",
                "duration_hours":   2.0,
                "price":            0.0,
                "currency":         "INR",
                "best_time":        "Afternoon",
                "booking_required": False,
                "latitude":         loc.get("latitude", 0),
                "longitude":        loc.get("longitude", 0),
                "source":           "foursquare",
            })
        return parsed


# ════════════════════════════════════════════════════════════════════
#  PROVIDER: AVIATIONSTACK  (https://aviationstack.com — 500 req/month free)
# ════════════════════════════════════════════════════════════════════

class AviationstackProvider:
    """
    Aviationstack: real-time flight schedules & routes.
    Free tier: 500 req/month. Good for route lookup.
    Docs: https://aviationstack.com/documentation
    """
    BASE = "https://api.aviationstack.com/v1"

    def _init_(self, api_key: str):
        self.key = api_key

    async def search_flights(
        self, origin: str, destination: str, departure_date: str,
        limit: int = 5,
    ) -> List[Dict]:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{self.BASE}/flights",
                params={
                    "access_key":  self.key,
                    "dep_iata":    origin,
                    "arr_iata":    destination,
                    "flight_date": departure_date,
                    "limit":       limit,
                },
            )
            r.raise_for_status()
            return self._parse(r.json().get("data", []))

    def _parse(self, data: List[Dict]) -> List[Dict]:
        results = []
        for i, f in enumerate(data):
            dep   = f.get("departure", {})
            arr   = f.get("arrival",   {})
            al    = f.get("airline",   {})
            fl    = f.get("flight",    {})
            results.append({
                "id":             f"AVS{i:03d}",
                "airline":        al.get("name", "Unknown"),
                "flight_number":  fl.get("iata", "??"),
                "departure_time": (dep.get("scheduled") or "")[-8:-3] or "TBD",
                "arrival_time":   (arr.get("scheduled") or "")[-8:-3] or "TBD",
                "duration":       "varies",
                "stops":          0,
                "price":          35000.0,   # Aviationstack free tier has no pricing
                "currency":       "INR",
                "cabin_class":    "Economy",
                "booking_url":    "https://www.aviationstack.com",
                "source":         "aviationstack",
            })
        return results or MOCK_FLIGHTS


# ════════════════════════════════════════════════════════════════════
#  MAIN TravelTools CLASS  —  auto-selects provider
# ════════════════════════════════════════════════════════════════════

class TravelTools:
    """
    Drop-in replacement for AmadeusTools.
    Reads .env to decide which providers to use.
    Falls back gracefully all the way to rich mock data.
    """

    def _init_(self):
        from backend.config import settings as cfg
        self.cfg = cfg

        # Active providers (set lazily)
        self._flight_provider   = None
        self._activity_provider = None
        self._hotel_provider    = None
        self._mode              = "mock"

        self._init_providers()

    def _init_providers(self):
        cfg = self.cfg

        # ── Duffel (flights) ──────────────────────────────────────────
        if getattr(cfg, "duffel_token", "") and cfg.duffel_token not in ("", "your_duffel_token"):
            self._flight_provider = DuffelProvider(cfg.duffel_token)
            self._mode = "duffel"

        # ── Aviationstack (flights fallback) ─────────────────────────
        elif getattr(cfg, "aviationstack_key", "") and cfg.aviationstack_key not in ("", "your_aviationstack_key"):
            self._flight_provider = AviationstackProvider(cfg.aviationstack_key)
            self._mode = "aviationstack"

        # ── OpenTripMap (activities + hotels) ────────────────────────
        if getattr(cfg, "opentripmap_key", "") and cfg.opentripmap_key not in ("", "your_opentripmap_key"):
            self._activity_provider = OpenTripMapProvider(cfg.opentripmap_key)
            self._hotel_provider    = OpenTripMapProvider(cfg.opentripmap_key)

        # ── Foursquare (activities) ───────────────────────────────────
        elif getattr(cfg, "foursquare_key", "") and cfg.foursquare_key not in ("", "your_foursquare_key"):
            self._activity_provider = FoursquareProvider(cfg.foursquare_key)

        print(f"[TravelTools] flight={self._mode} | "
              f"activity={'opentripmap' if isinstance(self._activity_provider, OpenTripMapProvider) else 'foursquare' if isinstance(self._activity_provider, FoursquareProvider) else 'mock'} | "
              f"hotel={'opentripmap' if isinstance(self._hotel_provider, OpenTripMapProvider) else 'mock'}")

    # ── Public API ────────────────────────────────────────────────────────────

    async def get_city_code(self, city: str) -> str:
        return CITY_CODES.get(city.lower().strip(), city[:3].upper())

    async def search_flights(
        self, origin: str, destination: str, departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1, travel_class: str = "ECONOMY",
        max_results: int = 5,
    ) -> List[Dict]:
        if self._flight_provider:
            try:
                cabin = travel_class.lower().replace("_", " ")
                return await self._flight_provider.search_flights(
                    origin, destination, departure_date,
                    adults=adults, cabin_class=cabin, max_results=max_results,
                )
            except Exception as e:
                print(f"[TravelTools] flight provider error: {e} — using mock")
        await asyncio.sleep(0.3)
        return MOCK_FLIGHTS

    async def search_hotels(
        self, city_code: str, check_in: str, check_out: str,
        adults: int = 1, max_results: int = 5,
    ) -> List[Dict]:
        if self._hotel_provider:
            try:
                places = await self._hotel_provider.get_hotels(city_code, limit=max_results)
                if places:
                    return places
            except Exception as e:
                print(f"[TravelTools] hotel provider error: {e} — using mock")
        await asyncio.sleep(0.3)
        
        # Filter mock hotels based on destination / city code
        code = city_code.upper()
        if code in ["MEX", "CUN", "MEXICO"]:
            filtered = [h for h in MOCK_HOTELS if "Mexico" in h["address"]]
        elif code in ["TYO", "NRT", "HND", "JAP", "OSA", "UKY", "JAPAN"]:
            filtered = [h for h in MOCK_HOTELS if "Japan" in h["address"]]
        elif code in ["NYC", "NEW YORK", "NY", "USA"]:
            filtered = [h for h in MOCK_HOTELS if "New York" in h["address"]]
        else:
            # Default to the generic mock hotels (excluding specific geo ones)
            filtered = [h for h in MOCK_HOTELS if "Japan" not in h["address"] and "Mexico" not in h["address"] and "New York" not in h["address"]]

        return filtered[:max_results]

    async def get_activities(self, destination: str) -> List[Dict]:
        # First try live provider
        if self._activity_provider:
            try:
                acts = await self._activity_provider.get_places(destination)
                if acts:
                    return acts
            except Exception as e:
                print(f"[TravelTools] activity provider error: {e} — using mock")

        # Curated mock fallback
        await asyncio.sleep(0.2)
        dest_lower = destination.lower().strip()
        for key in MOCK_ACTIVITIES:
            if key in dest_lower or dest_lower in key:
                return MOCK_ACTIVITIES[key]
        return MOCK_ACTIVITIES["default"]

# ── Singleton ────────────────────────────────────────────────────────────────
travel_tools = TravelTools()