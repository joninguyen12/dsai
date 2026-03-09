from datetime import datetime, timedelta, timezone
from typing import Optional

import os
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_PUBLIC_KEY") or ""

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_KEY in .env. Get from Supabase -> Project Settings -> API.")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

app = FastAPI(
    title="Seattle Congestion API",
    description="Expose congestion data by location, time window, and severity.",
    version="0.1.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def supabase_get(table: str, params: Optional[dict] = None) -> list:
    """GET from a Supabase table with PostgREST query params."""
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()


def supabase_get_all(table: str, params: dict, page_size: int = 2000, max_pages: int = 100) -> list:
    """Fetch all rows for a query via PostgREST pagination (limit/offset)."""
    out: list = []
    offset = 0
    for _ in range(max_pages):
        page_params = dict(params)
        page_params["limit"] = page_size
        page_params["offset"] = offset
        rows = supabase_get(table, page_params)
        if not rows:
            break
        out.extend(rows)
        if len(rows) < page_size:
            break
        offset += page_size
    return out


@app.get("/locations", summary="List locations (optional filters)")
def list_locations(
    freeway: Optional[str] = Query(None, description="Filter by freeway, e.g. I-5"),
    city: Optional[str] = Query(None, description="Filter by city"),
):
    """List intersections. Optionally filter by freeway or city."""
    params = {"select": "*", "order": "name.asc"}
    if freeway:
        params["freeway"] = f"eq.{freeway}"
    if city:
        params["city"] = f"eq.{city}"
    return supabase_get("locations", params)


@app.get("/locations/{location_id}", summary="Get one location")
def get_location(location_id: str):
    """Get a single location by ID."""
    data = supabase_get("locations", {"id": f"eq.{location_id}", "select": "*"})
    if not data:
        raise HTTPException(status_code=404, detail="Location not found")
    return data[0]


@app.get("/readings", summary="Query congestion readings")
def get_readings(
    location_id: Optional[str] = Query(None, description="Filter by location UUID"),
    from_time: Optional[str] = Query(None, alias="from", description="Start of time window (ISO datetime)"),
    to_time: Optional[str] = Query(None, alias="to", description="End of time window (ISO datetime)"),
    min_congestion: Optional[int] = Query(None, ge=0, le=100, description="Minimum congestion_index (severity)"),
    max_congestion: Optional[int] = Query(None, ge=0, le=100, description="Maximum congestion_index (severity)"),
    limit: int = Query(500, ge=1, le=2000, description="Max number of rows"),
    offset: int = Query(0, ge=0, le=200000, description="Pagination offset (for fetching full windows)"),
):
    """Get congestion readings with filters: location, time window, severity (congestion_index)."""
    params = {
        "select": "id,location_id,observed_at,congestion_index,speed_mph,vehicle_count,travel_time_index,is_incident",
        "order": "observed_at.desc",
        "limit": limit,
        "offset": offset,
    }
    if location_id:
        params["location_id"] = f"eq.{location_id}"
    if from_time and to_time:
        params["and"] = f"(observed_at.gte.{from_time},observed_at.lte.{to_time})"
    elif from_time:
        params["observed_at"] = f"gte.{from_time}"
    elif to_time:
        params["observed_at"] = f"lte.{to_time}"
    if min_congestion is not None:
        params["congestion_index"] = f"gte.{min_congestion}"
    if max_congestion is not None:
        params["congestion_index"] = f"lte.{max_congestion}"
    return supabase_get("congestion_readings", params)


@app.get("/readings/top", summary="Top N most congested")
def get_top_congested(
    limit: int = Query(10, ge=1, le=50, description="Number of top readings to return"),
    from_time: Optional[str] = Query(None, alias="from", description="Start of window (ISO); default: last 1 hour"),
    to_time: Optional[str] = Query(None, alias="to", description="End of window (ISO); default: now"),
    location_id: Optional[str] = Query(None, description="Optional location UUID filter"),
    min_congestion: Optional[int] = Query(None, ge=0, le=100, description="Minimum congestion_index (severity)"),
):
    """Return the readings with highest congestion_index in the given time window (or latest hour)."""
    to_ = to_time or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if not from_time:
        from_dt = datetime.now(timezone.utc) - timedelta(hours=1)
        from_ = from_dt.isoformat().replace("+00:00", "Z")
    else:
        from_ = from_time
    params = {
        "select": "id,location_id,observed_at,congestion_index,speed_mph,travel_time_index",
        "and": f"(observed_at.gte.{from_},observed_at.lte.{to_})",
        "order": "congestion_index.desc",
        "limit": limit,
    }
    if location_id:
        params["location_id"] = f"eq.{location_id}"
    if min_congestion is not None:
        params["congestion_index"] = f"gte.{min_congestion}"
    return supabase_get("congestion_readings", params)


@app.get("/readings/summary", summary="Aggregate summary for a time window")
def get_readings_summary(
    from_time: Optional[str] = Query(None, alias="from", description="Start (ISO datetime)"),
    to_time: Optional[str] = Query(None, alias="to", description="End (ISO datetime); default: now"),
):
    """Return counts and simple stats for the time window (for dashboard or AI)."""
    to_ = to_time or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    from_ = from_time or "1900-01-01T00:00:00Z"
    params = {
        "select": "congestion_index,speed_mph,location_id",
        "and": f"(observed_at.gte.{from_},observed_at.lte.{to_})",
    }
    rows = supabase_get("congestion_readings", params)
    if not rows:
        return {"from": from_, "to": to_, "count": 0, "avg_congestion": None, "avg_speed_mph": None}
    n = len(rows)
    avg_cong = sum(r.get("congestion_index") or 0 for r in rows) / n
    speeds = [r.get("speed_mph") for r in rows if r.get("speed_mph") is not None]
    avg_speed = sum(speeds) / len(speeds) if speeds else None
    return {
        "from": from_,
        "to": to_,
        "count": n,
        "avg_congestion": round(avg_cong, 2),
        "avg_speed_mph": round(avg_speed, 2) if avg_speed is not None else None,
    }


@app.get("/")
def root():
    return {
        "message": "Seattle Congestion API",
        "docs": "/docs",
        "endpoints": [
            "GET /locations?freeway=&city=",
            "GET /locations/{id}",
            "GET /readings?location_id=&from=&to=&min_congestion=&max_congestion=&limit=&offset=",
            "GET /readings/top?limit=&from=&to=&location_id=&min_congestion=",
            "GET /readings/summary?from=&to=",
        ],
    }

