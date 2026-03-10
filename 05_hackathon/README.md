# Seattle Congestion Insights App

End-to-end system for Seattle-area freeway congestion: **Supabase → FastAPI → Shiny dashboard → AI summary** (Ollama Cloud).

**Live app:** [Seattle Congestion Insights on Posit Connect](https://connect.systems-apps.com/content/8e824744-21c9-4638-a9a8-c4507cf7947f)

---

## Table of Contents

- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [Environment Variables (.env)](#environment-variables-env)
- [Key Components](#key-components)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Development Notes](#development-notes)

---

## 🚀 Quick Start

### 1. Set up Python environment

From the course repo root:

```bash
cd 05_hackathon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in `05_hackathon/` with the variables listed in [Environment Variables (.env)](#environment-variables-env). You can also export them in your shell.

### 3. Seed or load congestion data

Run from `05_hackathon/`: `python seed_locations.py` then `python generate_congestion_data.py` (18 locations, 7 days of 15-min readings). For quick demos you can instead import the CSVs (`locations.csv`, `readings_dataset1.csv`, etc.) into Supabase; see `CODEBOOK.md` for table definitions.

### 4. Run the FastAPI service

From `05_hackathon/`:

```bash
uvicorn main:app --reload
```

Then visit:

- OpenAPI docs: `http://127.0.0.1:8000/docs`
- Root endpoint: `http://127.0.0.1:8000/`

### 5. Run the Shiny dashboard

From `05_hackathon/` (recommended: use the script so the project venv is used):

```bash
./run_dashboard.sh
```

Or explicitly:

```bash
shiny run app.py
```

Open the URL shown (e.g. `http://127.0.0.1:8001`).

## 🏗️ System Architecture

Four components form the pipeline: **Database → API → Dashboard → AI**.

| Layer | Technology | Role |
|-------|-------------|------|
| **Database** | Supabase (Postgres) | Stores `locations` and `congestion_readings`; seeded by scripts or CSVs. |
| **API** | FastAPI (`main.py`) | PostgREST → REST endpoints for locations and readings. |
| **Dashboard** | Shiny (`app.py`) | Time/location filters; Hotspots table, Trends chart, AI Summary tab. |
| **AI** | Ollama Cloud (`ai_summary.py`) | Turns a JSON slice into Markdown bullet-point summaries. |

**Data flow:** Supabase → API (dashboard calls `/locations`, `/readings`, `/readings/top`) → dashboard (DataFrames, Plotly, enrichment) → AI tab (Ollama). See [Key Components](#key-components) for file-level roles.

---

## 🔐 Environment Variables (.env)

Define these in a `.env` file in `05_hackathon/` (or export in your shell). Do not commit `.env` to Git.

| Variable | Required | Used by | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | Yes (API) | FastAPI | Supabase project URL, e.g. `https://YOUR_REF.supabase.co` (no trailing slash). |
| `SUPABASE_KEY` | Yes (API) | FastAPI | Supabase anon or service role key (from Project Settings → API). |
| `CONGESTION_API_URL` | No | Shiny app | Base URL of the congestion API. Default: `http://127.0.0.1:8000`. On Posit Connect, set to the deployed API content URL. |
| `API_URL` | No | Shiny app | Fallback if `CONGESTION_API_URL` is not set; same meaning. |
| `OLLAMA_BASE_URL` | No | ai_summary | Ollama Cloud base URL. Default: `https://ollama.com`. |
| `OLLAMA_API_KEY` | Yes (AI) | ai_summary | API key for Ollama Cloud (required for AI summary tab). |
| `OLLAMA_MODEL` | No | ai_summary | Model name, e.g. `gpt-oss:120b`. |
| `CONNECT_SERVER` | Deploy | pushme.sh / push_shiny.sh | Posit Connect server URL for `rsconnect deploy`. |
| `CONNECT_API_KEY` | Deploy | pushme.sh / push_shiny.sh | Posit Connect API key for deployment. |

---

## 🧩 Key Components

| File | Role |
|------|------|
| `main.py` | FastAPI app: Supabase → REST endpoints (`/locations`, `/readings`, `/readings/top`, `/readings/summary`). |
| `app.py` | Shiny dashboard: time/location filters, Traffic Hotspots table, Explore Trends chart, AI Summary tab. |
| `ai_summary.py` | Ollama Cloud client; `summarize_congestion_data()` for the AI tab. |
| `seed_locations.py` | Seeds `locations` table. |
| `generate_congestion_data.py` | Generates 7 days of synthetic `congestion_readings`. |

See [System Architecture](#system-architecture) for the pipeline; `CODEBOOK.md` for API and variable details.

---

## 📖 Usage

Run commands are in [Quick Start](#quick-start). Below: using the API and the dashboard.

### API (curl)

With the FastAPI service running at `http://127.0.0.1:8000`:

```bash
# List all locations
curl "http://127.0.0.1:8000/locations"

# Filter locations by freeway
curl "http://127.0.0.1:8000/locations?freeway=I-5"

# Readings for a specific location and time window
curl "http://127.0.0.1:8000/readings?location_id=loc-1&from=2025-03-03T08:00:00Z&to=2025-03-03T09:00:00Z"

# Top 10 most congested readings in last hour
curl "http://127.0.0.1:8000/readings/top?limit=10"

# Summary stats for a time window
curl "http://127.0.0.1:8000/readings/summary?from=2025-03-01T00:00:00Z&to=2025-03-02T00:00:00Z"
```

### Dashboard

Sidebar: **Time Range** (24h / 7d / custom) and **Location**. Tabs: **Traffic Hotspots** (top-N table), **Explore Trends** (hourly chart), **AI Summary** (Ollama bullets).

### AI summary CLI (optional)

```bash
cd 05_hackathon && source .venv/bin/activate
python ai_summary.py path/to/readings_window.json
# Or: python ai_summary.py data/readings_window.json --question "Your question"
```

## 📁 Project Structure

Key parts of this app within the course repo:

```text
05_hackathon/
├── main.py                     # FastAPI service (congestion API)
├── app.py                      # Shiny dashboard UI + server
├── ai_summary.py               # Ollama Cloud helper for AI summaries
├── seed_locations.py           # Seed Supabase locations table
├── generate_congestion_data.py # Generate synthetic congestion readings
├── requirements.txt            # Python dependencies
├── manifest.json               # Posit Connect manifest (Shiny or API)
├── manifestme.sh               # Generate manifest for Shiny
├── push_shiny.sh               # Deploy Shiny app to Posit Connect
├── pushme.sh                   # Deploy FastAPI app to Posit Connect
├── run_dashboard.sh            # Run Shiny dashboard locally
├── locations.csv               # Optional test locations
├── readings_dataset1.csv       # Optional test readings
├── readings_dataset2.csv
├── readings_dataset3.csv
├── CODEBOOK.md                 # Data & API variable reference
└── README.md                   # This file
```

---

## 📝 Development Notes

### Dependencies

The hackathon environment uses Python 3.9+ with the following key packages (see `requirements.txt` for exact versions):

- `fastapi`, `uvicorn` — API framework and ASGI server.
- `requests` — HTTP client for Supabase and AI calls.
- `python-dotenv` — Optional `.env` loading.
- `shiny`, `shinywidgets`, `plotly`, `pandas` — Dashboard framework and plotting stack.

### Testing & iteration tips

- Use the `test/` CSV datasets for fast, repeatable runs without regenerating the full synthetic dataset.
- Start with `readings_dataset1.csv` to verify the hotspots and trends tabs.
- Then add `readings_dataset3.csv` to exercise pagination, multi-location trends, and richer AI summaries.
- Use FastAPI docs (`/docs`) to quickly try query parameters before wiring them into the dashboard.

