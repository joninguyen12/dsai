# Seattle Congestion Dashboard

Shiny app to **explore current or historical congestion** and **request a summary**. Calls the Congestion REST API (database → API → dashboard).

## Prerequisites

1. **API running** — from `05_hackathon`: `uvicorn api.main:app --reload` (and `.env` with Supabase credentials).
2. **Optional:** set `CONGESTION_API_URL` or `API_URL` in `.env` if the API is not at `http://127.0.0.1:8000`.

## Run

From `05_hackathon` you **must** use the project venv’s Python (otherwise you may get `ModuleNotFoundError` for pandas/plotly because Anaconda’s Python runs instead).

**Option 1 — run script (recommended):**
```bash
cd 05_hackathon
./run_dashboard.sh
```

**Option 2 — venv Python explicitly:**
```bash
cd 05_hackathon
.venv/bin/python -m shiny run dashboard/app.py --port 8001
```

**First time:** install deps in the venv:  
`pip install -r requirements.txt` (with `source .venv/bin/activate`) or  
`.venv/bin/pip install -r requirements.txt`

Open the URL shown (e.g. http://127.0.0.1:8001).

## Features

- **Time range:** Last 24 hours, Last 7 days, or custom date range.
- **Location:** Filter by intersection (dropdown from API).
- **Min congestion:** Slider 0–100 (severity filter).
- **Top congested:** Table of top N most congested readings in the selected window.
- **Explore readings:** Interactive Plotly chart of congestion over time (location, time, severity).
- **Request summary:** Button to fetch aggregate stats (count, avg congestion, avg speed) for the selected time range.

## Date limits

The seed script (`scripts/generate_congestion_data.py`) fills **the last 7 days** of data from when you run it. The dashboard’s custom date range is limited to **today minus 7 days through today** so the picker stays within that window. If you need a different window, re-run the script or change `DAYS_BACK` in the script.
