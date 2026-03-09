# seed_locations.py
# Seed Seattle-area freeway intersections into Supabase locations table
# Run from 05_hackathon. Set SUPABASE_URL and SUPABASE_KEY in .env or export them.

import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_PUBLIC_KEY") or ""

if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit("Set SUPABASE_URL and SUPABASE_KEY in .env or export them. Get from Supabase -> Project Settings -> API.")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

LOCATIONS = [
    {"name": "I-5 & I-90 Interchange", "freeway": "I-5", "cross_street": "I-90", "direction": "NB/SB", "city": "Seattle", "neighborhood": "Downtown", "latitude": 47.6097, "longitude": -122.3331},
    {"name": "I-5 & SR-520 Interchange", "freeway": "I-5", "cross_street": "SR-520", "direction": "NB/SB", "city": "Seattle", "neighborhood": "Montlake", "latitude": 47.6448, "longitude": -122.3256},
    {"name": "I-5 & James St", "freeway": "I-5", "cross_street": "James St", "direction": "NB", "city": "Seattle", "neighborhood": "Downtown", "latitude": 47.6062, "longitude": -122.3321},
    {"name": "I-5 & NE 45th St", "freeway": "I-5", "cross_street": "NE 45th St", "direction": "NB/SB", "city": "Seattle", "neighborhood": "Wallingford", "latitude": 47.6603, "longitude": -122.3203},
    {"name": "I-5 & Northgate Way", "freeway": "I-5", "cross_street": "Northgate Way", "direction": "NB/SB", "city": "Seattle", "neighborhood": "Northgate", "latitude": 47.7036, "longitude": -122.3256},
    {"name": "I-5 & NE 145th St", "freeway": "I-5", "cross_street": "NE 145th St", "direction": "NB/SB", "city": "Seattle", "neighborhood": "Shoreline", "latitude": 47.7311, "longitude": -122.3197},
    {"name": "I-90 & Rainier Ave", "freeway": "I-90", "cross_street": "Rainier Ave", "direction": "EB/WB", "city": "Seattle", "neighborhood": "Mount Baker", "latitude": 47.5842, "longitude": -122.3014},
    {"name": "I-90 & Mercer Island", "freeway": "I-90", "cross_street": "Island Crest Way", "direction": "EB/WB", "city": "Mercer Island", "neighborhood": "Mercer Island", "latitude": 47.5708, "longitude": -122.2269},
    {"name": "I-90 & Bellevue Way", "freeway": "I-90", "cross_street": "Bellevue Way", "direction": "EB/WB", "city": "Bellevue", "neighborhood": "Bellevue", "latitude": 47.6103, "longitude": -122.2003},
    {"name": "SR-520 & Montlake Blvd", "freeway": "SR-520", "cross_street": "Montlake Blvd", "direction": "EB/WB", "city": "Seattle", "neighborhood": "Montlake", "latitude": 47.6472, "longitude": -122.3042},
    {"name": "SR-520 & 92nd Ave NE", "freeway": "SR-520", "cross_street": "92nd Ave NE", "direction": "EB/WB", "city": "Clyde Hill", "neighborhood": "Clyde Hill", "latitude": 47.6381, "longitude": -122.2286},
    {"name": "I-405 & I-90 Interchange", "freeway": "I-405", "cross_street": "I-90", "direction": "NB/SB", "city": "Bellevue", "neighborhood": "Bellevue", "latitude": 47.5831, "longitude": -122.1686},
    {"name": "I-405 & NE 8th St", "freeway": "I-405", "cross_street": "NE 8th St", "direction": "NB/SB", "city": "Bellevue", "neighborhood": "Bellevue", "latitude": 47.6136, "longitude": -122.1864},
    {"name": "I-405 & SR-520", "freeway": "I-405", "cross_street": "SR-520", "direction": "NB/SB", "city": "Bellevue", "neighborhood": "Bellevue", "latitude": 47.6389, "longitude": -122.1917},
    {"name": "I-5 & SR-518 (SeaTac)", "freeway": "I-5", "cross_street": "SR-518", "direction": "NB/SB", "city": "SeaTac", "neighborhood": "SeaTac", "latitude": 47.4606, "longitude": -122.2911},
    {"name": "I-5 & SR-167", "freeway": "I-5", "cross_street": "SR-167", "direction": "NB/SB", "city": "Federal Way", "neighborhood": "Federal Way", "latitude": 47.3072, "longitude": -122.3208},
    {"name": "SR-99 & Denny Way", "freeway": "SR-99", "cross_street": "Denny Way", "direction": "NB/SB", "city": "Seattle", "neighborhood": "South Lake Union", "latitude": 47.6192, "longitude": -122.3503},
    {"name": "SR-99 & West Seattle Bridge", "freeway": "SR-99", "cross_street": "West Seattle Bridge", "direction": "NB/SB", "city": "Seattle", "neighborhood": "Sodo", "latitude": 47.5642, "longitude": -122.3528},
]

def main():
    url = f"{SUPABASE_URL}/rest/v1/locations"
    for loc in LOCATIONS:
        row = {
            "name": loc["name"], "freeway": loc["freeway"], "cross_street": loc.get("cross_street"),
            "direction": loc.get("direction"), "city": loc["city"], "neighborhood": loc.get("neighborhood"),
            "latitude": loc.get("latitude"), "longitude": loc.get("longitude"), "is_active": True,
        }
        r = requests.post(url, json=row, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        print(f"Inserted: {loc['name']} (id: {data[0]['id']})")
    print(f"\nDone. Inserted {len(LOCATIONS)} locations.")

if __name__ == "__main__":
    main()
