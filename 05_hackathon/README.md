# Seattle Congestion Insights App

An end-to-end system that surfaces congestion patterns for key Seattle freeway locations. It implements the midterm-required pipeline:

- A **Supabase PostgreSQL database** that stores synthetic congestion data (locations and time-stamped readings).
- A **FastAPI** service that exposes that database through a REST API.
- A **Python Shiny** dashboard for exploring hotspots, trends, and tables.
- An **AI-powered summary** layer (Ollama Cloud) that turns data slices into human-readable bullet points.

**Live app:** [Seattle Congestion Insights on Posit Connect](https://connect.systems-apps.com/content/8e824744-21c9-4638-a9a8-c4507cf7947f)

---

## Table of Contents

- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [Environment Variables (.env)](#environment-variables-env)
- [Key Components](#key-components)
- [Data Flow](#data-flow)
- [Usage Guide](#usage-guide)
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

Create a `.env` file in `05_hackathon/` (same folder as `requirements.txt`). See [Environment Variables (.env)](#environment-variables-env) for the full reference. Minimal local setup:

```bash
# Supabase (congestion database)
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_KEY=your-anon-public-key

# Optional: override API URL for the Shiny dashboard
CONGESTION_API_URL=http://127.0.0.1:8000

# Ollama Cloud for AI summaries (used by ai_summary.py and the dashboard)
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_API_KEY=your-ollama-api-key
OLLAMA_MODEL=gpt-oss:120b
```

You can also export these in your shell instead of using `.env`.

### 3. Seed or load congestion data

You have two options:

- **Use the provided scripts** in `scripts/` to seed Supabase with a realistic synthetic dataset (18 locations, 7 days of 15-min readings).
- **Use the small test CSVs** in `test/` for quick demos or unit tests:
  - Import `test/locations.csv` into the `locations` table.
  - Import one or more of:
    - `test/readings_dataset1.csv`
    - `test/readings_dataset2.csv`
    - `test/readings_dataset3.csv`
  - See `test/README.md` for details.

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

At a high level, the system has four core components that form the required end-to-end pipeline:

1. **Database – Supabase/Postgres**
   - Hosts the `locations` and `congestion_readings` tables.
   - Can be seeded via scripts or the `test/` CSVs.
2. **REST API – FastAPI (`main.py`)**
   - Reads from Supabase using the REST interface and exposes congestion-focused endpoints.
3. **Dashboard – Python Shiny (`app.py`)**
   - Calls the REST API, visualizes congestion, and lets a user select windows/locations.
4. **AI – Ollama Cloud (`ai_summary.py`)**
   - Receives a compact JSON slice from the dashboard and returns a short, actionable summary.

This matches the midterm DL challenge specification: **Supabase database → REST API → dashboard → AI model**.

**Conceptual diagram:**

```mermaid
graph TB
    subgraph Data["Data Layer (Supabase/Postgres)"]
        D1[locations table]
        D2[congestion_readings table]
    end

    subgraph API["API Layer (FastAPI, api/main.py)"]
        A1[/GET /locations/]
        A2[/GET /readings/]
        A3[/GET /readings/top/]
        A4[/GET /readings/summary/]
    end

    subgraph App["App Layer (Shiny dashboard, dashboard/app.py)"]
        U1[Controls: time window, location]
        U2[Traffic Hotspots table]
        U3[Explore Trends chart]
        U4[AI Summary view]
    end

    subgraph AI["AI Service (ai_summary.py + Ollama Cloud)"]
        L1[summarize_congestion_data()]
    end

    D1 --> A1
    D2 --> A2
    D2 --> A3
    D2 --> A4

    A1 --> U1
    A1 --> U2
    A2 --> U3
    A2 --> U4
    A3 --> U2
    A2 --> L1
    L1 --> U4
```

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

### Core Files

- **`main.py`** — FastAPI application:
  - Loads Supabase credentials from environment/.env.
  - Defines helper functions for paginated Supabase queries.
  - Exposes endpoints:
    - `GET /locations`
    - `GET /locations/{id}`
    - `GET /readings`
    - `GET /readings/top`
    - `GET /readings/summary`

- **`app.py`** — Python Shiny dashboard:
  - Connects to the FastAPI service via `CONGESTION_API_URL`.
  - Provides a sidebar for time range and location filters.
  - Tabs for:
    - **🚨 Traffic Hotspots** — Top N most congested points.
    - **📈 Explore Trends** — Time-series congestion index trends, with downsampling and pagination-aware warnings.
    - **🤖 AI Summary** — AI-generated narrative of congestion conditions using enriched readings + location metadata.

- **`ai_summary.py`** — AI summary helper:
  - Builds system/user prompts tailored to traffic operations.
  - Sends JSON payloads to Ollama Cloud via HTTP.
  - Exposes `summarize_congestion_data(data, question=None, model=None)` for use by the dashboard or CLI.

### Supporting Files

- **`test/`** — Ready-to-import CSV test data for quick demos and regression tests.
- **`seed_locations.py`**, **`generate_congestion_data.py`** — Seed Supabase locations and synthetic readings.
- **`.env`** — Local configuration (see [Environment Variables (.env)](#environment-variables-env)); not committed to Git.

---

## 📊 Data Flow

End-to-end flow for the main dashboard path (database → API → dashboard → AI):

1. **Database (Supabase)**
   - Supabase/Postgres hosts `locations` and `congestion_readings`.
   - Data is seeded either via `scripts/` or the CSVs in `test/`.

2. **API layer (FastAPI)**
   - Reads from Supabase via the PostgREST interface.
   - Dashboard calls `GET /locations` to populate the location dropdown.
   - When a time window (and optional location) is selected, the dashboard:
     - Calls `GET /readings/top` for the hotspots table.
     - Uses a helper to repeatedly call `GET /readings` with `limit`/`offset` for the trends chart and AI view.
     - Optionally calls `GET /readings/summary` when you want a quick aggregate snapshot.

3. **Dashboard (Python Shiny)**
   - `app.py`:
     - Converts raw JSON into pandas DataFrames.
     - Joins readings with locations for human-friendly labels.
     - Aggregates readings to hourly means for trend plots (per-location or all locations).
     - Renders interactive Plotly charts and data tables.

4. **AI summary (Ollama Cloud)**
   - The AI tab:
     - Uses the same time window + location filters as the trends view.
     - Enriches readings with intersection, city, and neighborhood from `locations`.
     - Sends the enriched JSON to `summarize_congestion_data()` in `ai_summary.py`.
   - `ai_summary.py`:
     - Constructs a concise system prompt for a “traffic operations assistant”.
     - Sends a non-streaming request to Ollama Cloud.
     - Returns 2–6 Markdown bullet points, which the dashboard lightly formats as HTML.

## 📖 Usage Guide

### API usage examples

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

### Dashboard usage

1. **Open the dashboard** in your browser after running `shiny run dashboard/app.py`.
2. In the **sidebar**:
   - Select a **Time Range**:
     - `Last 24 Hours`, `Last 7 Days`, or a **Custom Range** (bounded by data window).
   - Optionally choose a **Location** (or “All locations” for a network-wide view).
3. In **🚨 Traffic Hotspots**:
   - Adjust “Display # of Entries” to show up to 50 rows.
   - Inspect the table columns:
     - Timestamp, intersection, city, neighborhood, congestion %, speed.
4. In **📈 Explore Trends**:
   - View congestion index vs. time (hourly averages).
   - When “All locations” is selected, each line represents a location; the legend shows names.
   - Read the disclaimer under the chart when many readings are loaded (pagination/truncation note).
5. In **🤖 AI Summary**:
   - Click the tab to generate a summary for the current filters.
   - Wait a few seconds for the AI response.
   - Read bullet points grouped into sections such as worst hotspots, clearer routes, and trends vs. typical.

### AI summary CLI usage (optional)

You can also call the AI summary helper directly:

```bash
cd 05_hackathon
source .venv/bin/activate

python seattle-congestion-app/ai_summary.py path/to/readings_window.json
```

Or override the question:

```bash
python seattle-congestion-app/ai_summary.py data/readings_window.json \
  --question "How does congestion here compare to a typical weekday PM peak?"
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

### Configuration & environment

- The API will raise a clear error at startup if `SUPABASE_URL` or `SUPABASE_KEY` is missing.
- The AI summary functions will raise a clear error if `OLLAMA_API_KEY` is not set.
- The Shiny dashboard defaults `API_URL` to `http://127.0.0.1:8000` but you can point it to any deployment via `CONGESTION_API_URL`.

### Testing & iteration tips

- Use the `test/` CSV datasets for fast, repeatable runs without regenerating the full synthetic dataset.
- Start with `readings_dataset1.csv` to verify the hotspots and trends tabs.
- Then add `readings_dataset3.csv` to exercise pagination, multi-location trends, and richer AI summaries.
- Use FastAPI docs (`/docs`) to quickly try query parameters before wiring them into the dashboard.

