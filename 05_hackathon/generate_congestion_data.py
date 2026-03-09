# generate_congestion_data.py
# Generate synthetic congestion readings for all locations (7 days, 15-min intervals)
# Run after seed_locations.py. Set SUPABASE_URL and SUPABASE_KEY in .env or export them.

import os
import random
import requests
from datetime import datetime, timedelta, timezone

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
    "Prefer": "return=minimal",
}

DAYS_BACK = 7
INTERVAL_MINUTES = 15
HOURLY_BASELINE = [
    25, 22, 20, 18, 22, 35, 55, 72, 78, 70, 65, 60,
    62, 68, 72, 75, 78, 80, 75, 68, 55, 42, 32, 28,
]

def main():
    rng = random.Random(42)
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/locations",
        params={"select": "id", "order": "name.asc"},
        headers={**HEADERS, "Prefer": "return=representation"},
        timeout=30,
    )
    r.raise_for_status()
    locs = r.json()
    if not locs:
        raise SystemExit("No locations found. Run scripts/seed_locations.py first.")
    location_ids = [row["id"] for row in locs]

    start = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
    start = start.replace(minute=(start.minute // INTERVAL_MINUTES) * INTERVAL_MINUTES, second=0, microsecond=0)
    end = datetime.now(timezone.utc)
    url = f"{SUPABASE_URL}/rest/v1/congestion_readings"
    batch, batch_size = [], 500
    ts = start

    while ts <= end:
        hour_utc = ts.hour
        base = HOURLY_BASELINE[hour_utc % 24]
        for i, loc_id in enumerate(location_ids):
            loc_bias = (i % 5) * 3
            congestion_index = max(0, min(100, base + loc_bias + rng.randint(-8, 10)))
            speed = round(65.0 - (congestion_index / 100.0) * 55.0 + rng.uniform(-2, 2), 2)
            tti = round(1.0 + (congestion_index / 100.0) * 1.2 + rng.uniform(-0.05, 0.05), 2)
            batch.append({
                "location_id": loc_id,
                "observed_at": ts.isoformat(),
                "congestion_index": congestion_index,
                "speed_mph": speed,
                "vehicle_count": 500 + congestion_index * 20 + rng.randint(-50, 100),
                "travel_time_index": tti,
                "is_incident": False,
                "data_source": "synthetic_v1",
            })
            if len(batch) >= batch_size:
                requests.post(url, json=batch, headers=HEADERS, timeout=60).raise_for_status()
                print(f"Inserted batch up to {batch[-1]['observed_at']}")
                batch = []
        ts += timedelta(minutes=INTERVAL_MINUTES)

    if batch:
        requests.post(url, json=batch, headers=HEADERS, timeout=60).raise_for_status()
        print(f"Inserted final batch ({len(batch)} rows).")
    print(f"\nDone. Readings from {start.isoformat()} to {end.isoformat()} for {len(location_ids)} locations.")

if __name__ == "__main__":
    main()
