## Test datasets for Seattle congestion app

This folder contains small, ready-to-import CSVs that exercise the main features of the Seattle congestion API and Shiny dashboard. They are meant for local development, demos, and regression checks.

- **Target tables**: `locations` and `congestion_readings` in your Supabase/Postgres database.
- **Import format**: Standard CSV with a header row and UTF-8 text.

### 1. `locations.csv`

**Purpose**: Seed a small set of freeway locations around Seattle that are referenced by all three test datasets.

**Columns** (table: `locations`):

- `id`: Stable ID used by `congestion_readings.location_id` (e.g., `loc-1`).
- `name`: Human-readable intersection name (e.g., `NB I-5 @ Seneca`).
- `city`: City name (e.g., `Seattle`).
- `neighborhood`: Neighborhood or area.
- `freeway`: Freeway identifier (e.g., `I-5`, `SR-520`).

Import this first into the `locations` table so that all reading datasets can resolve their foreign keys.

### 2. `readings_dataset1.csv` — Weekday morning rush (core functionality)

**Scenario**: A single weekday morning (March 3, 2025) between 08:00–08:30 UTC, with three locations showing typical AM peak congestion, including a severe incident downtown.

**Columns** (table: `congestion_readings`):

- `id`: Unique ID for the reading row (e.g., `r1`).
- `location_id`: Foreign key to `locations.id` (e.g., `loc-1`).
- `observed_at`: ISO 8601 timestamp in UTC (e.g., `2025-03-03T08:15:00Z`).
- `congestion_index`: 0–100 congestion severity (higher = worse).
- `speed_mph`: Approximate average speed in miles per hour.
- `vehicle_count`: Simple volume proxy for that 15-minute interval.
- `travel_time_index`: Ratio versus free-flow travel time (1.0 = free flow, 2.0 = twice as long).
- `is_incident`: `true` or `false`, flagging major incidents.

**What it demonstrates**:

- `/locations` list and filters (e.g., by `city` or `freeway`).
- `/readings` filtering by `location_id`, time window, and `min_congestion`.
- `/readings/top` for a short window, surfacing the worst congestion (the incident at `loc-1`).
- Dashboard tabs:
  - **Traffic Hotspots**: Table of top congested points with joined location metadata.
  - **Explore Trends**: Short-time-series line plots over a half-hour window.

### 3. `readings_dataset2.csv` — Weekend midday (clear routes)

**Scenario**: Weekend midday conditions (March 9, 2025) with low congestion and no incidents across the same three core locations.

**Columns**: Same schema as `readings_dataset1.csv` (`congestion_readings`).

**What it demonstrates**:

- “Happy path” with low congestion (values near 0–20) and higher speeds.
- `/readings` and `/readings/top` correctly showing near–free-flow traffic.
- Dashboard trends tab rendering flat, low congestion curves and validating the UI when there are no spikes or incidents.

### 4. `readings_dataset3.csv` — Mixed multi-day history (hotspots, trends, AI summary)

**Scenario**: A richer, multi-location history covering multiple days (starting March 1–2, 2025) with:

- Morning and evening rush-hour peaks.
- Off-peak low congestion overnight.
- A few explicit incident spikes (`is_incident = true`).
- Additional locations (`loc-4`, `loc-5`) to broaden the map of hotspots.

**Columns**: Same schema as `readings_dataset1.csv` (`congestion_readings`).

**What it demonstrates**:

- `/readings` pagination and the dashboard’s `api_get_all_readings` helper.
- **Explore Trends**:
  - Hourly aggregation and downsampling.
  - Multi-location comparison when “All locations” is selected.
  - The disclaimer text about truncated windows when a lot of raw readings are loaded.
- **AI Summary**:
  - Produces meaningful bullet-point narratives about:
    - Worst hotspots by location and time.
    - Clearer routes and times of day.
    - High-level patterns across several days.

### How to use these files

1. **Seed locations**  
   - In Supabase (or psql), import `locations.csv` into the `locations` table.

2. **Load one or more reading datasets**  
   - Import any of `readings_dataset1.csv`, `readings_dataset2.csv`, or `readings_dataset3.csv` into the `congestion_readings` table.
   - You can load them separately for focused tests or combine them all for a richer history.

3. **Run the API and dashboard**  
   - Start the FastAPI service (`uvicorn api.main:app --reload`) and confirm `/locations` and `/readings` return data.
   - Start the Shiny app (`shiny run dashboard/app.py`) and explore:
     - **Traffic Hotspots** for top-N congested observations.
     - **Explore Trends** for time-series behavior.
     - **AI Summary** for natural-language explanations of the selected window.

These CSVs are deliberately small so you can quickly reset and reload them as you iterate on features or debug the system.

