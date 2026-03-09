# Seattle Congestion REST API

Exposes congestion data **by location, time window, and severity** (Supabase → REST API).

## Database tables

The API reads from two Supabase (PostgreSQL) tables.

### `locations`

Freeway intersections or segments in the greater Seattle area.

| Column        | Type         | Description                                      |
|---------------|--------------|--------------------------------------------------|
| `id`          | uuid         | Primary key (auto-generated).                    |
| `name`        | text         | Display name (e.g. "I-5 & I-90 Interchange").   |
| `freeway`     | text         | Freeway or route (e.g. I-5, I-90, SR-520).      |
| `cross_street`| text         | Cross street or interchange.                     |
| `direction`   | text         | Direction of travel (e.g. NB, SB, EB, WB).      |
| `city`        | text         | City (e.g. Seattle, Bellevue).                  |
| `neighborhood`| text         | Neighborhood or area.                           |
| `latitude`    | numeric(9,6) | Latitude.                                       |
| `longitude`   | numeric(9,6) | Longitude.                                      |
| `is_active`   | boolean      | Whether the location is active.                 |
| `created_at`  | timestamptz  | Row creation time (UTC).                        |

### `congestion_readings`

Time-series congestion readings per location.

| Column             | Type          | Description                                           |
|--------------------|---------------|-------------------------------------------------------|
| `id`               | bigserial     | Primary key.                                         |
| `location_id`      | uuid          | Foreign key to `locations.id`.                        |
| `observed_at`      | timestamptz   | Timestamp of the reading (UTC).                      |
| `congestion_index` | smallint      | Congestion level 0–100 (higher = worse).              |
| `speed_mph`        | numeric(5,2)  | Average speed in mph.                                 |
| `vehicle_count`    | integer       | Approximate vehicle count.                            |
| `travel_time_index`| numeric(5,2)  | Ratio vs free-flow (1.0 = normal; >1 = slower).      |
| `is_incident`      | boolean       | Whether the reading reflects an incident.             |
| `data_source`      | text          | Source of the data (e.g. synthetic_v1).              |
| `created_at`       | timestamptz   | Row creation time (UTC).                             |

Unique constraint: one row per `(location_id, observed_at)`.

## Run

From `05_hackathon` (with `.env` set: `SUPABASE_URL`, `SUPABASE_KEY`):

```bash
uvicorn api.main:app --reload
```

- API: http://127.0.0.1:8000  
- Docs: http://127.0.0.1:8000/docs  

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/locations` | List locations. Query: `?freeway=I-5` `?city=Seattle` |
| GET | `/locations/{id}` | One location by UUID |
| GET | `/readings` | Readings (paged). Query: `location_id`, `from`, `to` (ISO), `min_congestion`, `max_congestion`, `limit`, `offset` |
| GET | `/readings/top` | Top N most congested in time window. Query: `limit`, `from`, `to`, `location_id`, `min_congestion` |
| GET | `/readings/summary` | Aggregate stats for window. Query: `from`, `to` (for dashboard/AI) |

## Example queries

- All locations on I-5: `GET /locations?freeway=I-5`
- Readings at a location: `GET /readings?location_id=<uuid>`
- Last 7 days: `GET /readings?from=2025-03-01T00:00:00Z&to=2025-03-08T23:59:59Z`
- High severity only (≥ 70): `GET /readings?min_congestion=70`
- Top 10 congested now: `GET /readings/top?limit=10`
