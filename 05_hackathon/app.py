# dashboard/app.py
# Shiny dashboard: explore current/historical congestion and request a summary
# Connects to the Congestion REST API. Run: shiny run dashboard/app.py (from 05_hackathon)

import os
import re
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from shiny import reactive, render
from shiny.express import input, ui
from shinywidgets import render_plotly

# Ensure project root (for ai_summary.py) is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from ai_summary import summarize_congestion_data

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

API_URL = (os.getenv("CONGESTION_API_URL") or os.getenv("API_URL") or "http://127.0.0.1:8000").rstrip("/")

PAGE_SIZE = 2000
MAX_PAGES = 50  # safety cap; enough for our synthetic dataset windows


def api_get(path: str, params: dict | None = None) -> tuple[list | dict | None, str | None]:
    """GET from the congestion API. Returns (data, error_message)."""
    try:
        r = requests.get(f"{API_URL}{path}", params=params or {}, timeout=15)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.RequestException as e:
        return None, str(e)


def api_get_all_readings(params: dict) -> tuple[list | None, str | None, bool]:
    """Fetch all readings for a window via API pagination (limit/offset)."""
    rows: list = []
    offset = 0
    truncated = False
    for _ in range(MAX_PAGES):
        page_params = dict(params)
        page_params["limit"] = PAGE_SIZE
        page_params["offset"] = offset
        data, err = api_get("/readings", page_params)
        if err:
            return None, err, False
        if not data:
            break
        if not isinstance(data, list):
            return None, "Unexpected API response for /readings", False
        rows.extend(data)
        if len(data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    # If we hit the safety cap and kept receiving full pages, we likely truncated the requested window.
    if offset >= PAGE_SIZE * (MAX_PAGES - 1) and len(rows) >= PAGE_SIZE * MAX_PAGES:
        truncated = True
    return rows, None, truncated


def _format_ai_text_as_html(text: str) -> str:
    """Lightweight formatting: convert **bold** markers to <strong> for display."""
    if not text:
        return ""
    # Replace Markdown-style bold with <strong> tags
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

# Reactive: fetch locations once for dropdown
@reactive.calc
def locations_list():
    data, err = api_get("/locations")
    if err:
        return []
    return data if isinstance(data, list) else []


# Data window: seed script generates last 7 days. Use same window for custom picker limits.
def _data_date_limits():
    now = datetime.now(timezone.utc)
    return (now - timedelta(days=7)).date(), now.date()


def make_time_range(preset: str):
    now = datetime.now(timezone.utc)
    if preset == "24h":
        start = now - timedelta(hours=24)
    elif preset == "7d":
        start = now - timedelta(days=7)
    else:
        return None, None
    return start.strftime("%Y-%m-%dT%H:%M:%SZ"), now.strftime("%Y-%m-%dT%H:%M:%SZ")


# UI — keep page_opts minimal; render our own header below
ui.page_opts(title="", fillable=True)

# Remove stray boolean text ("True"/"False") and also strip card-like borders/background
ui.tags.script(
    """
    (function() {
      function removeBoolText() {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
        let n;
        while ((n = walker.nextNode())) {
          const txt = n.textContent && n.textContent.trim();
          if (txt === 'True' || txt === 'False') {
            const parent = n.parentNode;
            if (parent) parent.removeChild(n);
          }
        }
      }
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', removeBoolText);
      } else {
        removeBoolText();
      }
    })();
    """
)

ui.tags.style(
    """
    /* Remove card-like outline around sidebar + main area */
    .bslib-layout-sidebar,
    .bslib-layout-sidebar > .bslib-layout-sidebar-main,
    .bslib-layout-sidebar > .bslib-layout-sidebar-sidebar {
      border: none !important;
      box-shadow: none !important;
      background-color: transparent !important;
      min-height: 100vh;
    }

    /* Center and bold the top header text */
    header,
    .bslib-page-title {
      text-align: center !important;
    }

    header h1,
    .bslib-page-title h1 {
      font-weight: 700;
    }

    /* Bold table headings */
    table thead th {
      font-weight: 700;
    }

    html, body {
      height: 100%;
      background-color: #ffffff;
      margin: 0;
      padding: 0;
      font-size: 1.05rem;
    }

    /* Slightly larger font for sidebar labels and inputs */
    .sidebar .form-label,
    .sidebar .form-control,
    .sidebar .form-select,
    .sidebar .selectize-input,
    .sidebar .form-check-label {
      font-size: 1.05rem;
    }

    /* Sidebar section title ("⚙️ Controls") – between main title and labels */
    .sidebar h3 {
      font-size: 1.25rem;
      font-weight: 600;
    }

    /* Slightly larger font for tab labels and main content */
    .nav-tabs .nav-link,
    .nav-pills .nav-link,
    .tab-pane {
      font-size: 1.05rem;
    }

    /* Larger header */
    header h1,
    .bslib-page-title h1 {
      font-size: 1.6rem;
    }

    /* Disclaimer box under Explore Trends */
    .trend-disclaimer {
      background-color: #DBECFF;
      border: 1px solid #60A5FA;
      border-radius: 6px;
      padding: 0.5rem 0.75rem;
      margin-top: 0.75rem;
      font-size: 0.95rem;
    }

    /* AI summary text block */
    .ai-summary-text {
      font-size: 1.0rem;
      line-height: 1.4;
    }
    """
)

with ui.layout_sidebar(fillable=True):
    with ui.sidebar(open="always"):
        # About section first
        ui.tags.div(
            ui.tags.h3("💡 About", class_="mb-2"),
            ui.tags.p(
                "This dashboard surfaces congestion patterns across key Seattle freeway locations. "
                "Use the controls to focus on a time window or specific intersection, then explore hotspots, trends, "
                "and AI-generated summaries to understand current and typical traffic conditions."
                "Note: The AI summary is generated using the data from the selected time window and filters. It may take a few seconds to generate.",
                class_="text-muted mb-3",
            ),
        )

        ui.tags.hr(class_="my-3")

        # Controls section after About
        ui.tags.div(
            ui.tags.h3("⚙️ Controls", class_="mb-3"),
        )
        ui.input_select(
            "time_preset",
            "Time Range",
            {"24h": "Last 24 Hours", "7d": "Last 7 Days", "custom": "Custom Range"},
            selected="7d",
        )
        with ui.panel_conditional("input.time_preset === 'custom'"):
            _start, _end = _data_date_limits()
            ui.input_date_range(
                "date_range",
                "From – To",
                start=_start,
                end=_end,
                min=_start,
                max=_end,
            )
            ui.tags.p(
                f"Data window: {_start} to {_end} (last 7 days).",
                class_="text-muted small mt-1",
            )
        ui.input_select(
            "location_id",
            "Location",
            choices={"": "All Locations"},
            selected="",
        )

    ui.tags.header(
        ui.tags.h1("🚗 Seattle Congestion Insights", class_="h3 mb-0"),
        class_="text-center mb-3",
        style="font-weight: bold;",
    )

    with ui.navset_card_pill():
        with ui.nav_panel("🚨 Traffic Hotspots"):
            ui.div(
                ui.input_numeric(
                    "top_n",
                    "Display # of Entries (max. 50):",
                    value=10,
                    min=1,
                    max=50,
                ),
                class_="d-flex align-items-center mb-3",
                style="gap: 0.25rem;",
            )

            @render.data_frame
            def top_table():
                from_, to_ = time_from_to()
                if not from_ or not to_:
                    return pd.DataFrame({"Message": ["Select a time range."]})
                params = {"from": from_, "to": to_, "limit": input.top_n()}
                if input.location_id():
                    params["location_id"] = input.location_id()
                data, err = api_get("/readings/top", params)
                if err:
                    return pd.DataFrame({"Error": [err]})
                if not data:
                    return pd.DataFrame({"Message": ["No readings in this window."]})
                df = pd.DataFrame(data)
                # Join location metadata so the table can show name/city/neighborhood
                loc_rows = [r for r in locations_list() if isinstance(r, dict) and r.get("id")]
                name_map = {r["id"]: r.get("name") for r in loc_rows}
                city_map = {r["id"]: r.get("city") for r in loc_rows}
                neighborhood_map = {r["id"]: r.get("neighborhood") for r in loc_rows}
                if "location_id" in df.columns:
                    df["name"] = df["location_id"].map(name_map)
                    df["city"] = df["location_id"].map(city_map)
                    df["neighborhood"] = df["location_id"].map(neighborhood_map)

                df.insert(0, "#", range(1, len(df) + 1))

                # Keep only the requested columns (in order)
                for col in ["observed_at", "name", "city", "neighborhood", "congestion_index", "speed_mph"]:
                    if col not in df.columns:
                        df[col] = None
                df = df[["#", "observed_at", "name", "city", "neighborhood", "congestion_index", "speed_mph"]]
                df = df.rename(
                    columns={
                        "observed_at": "Date/Time",
                        "name": "Intersection",
                        "city": "City",
                        "neighborhood": "Neighborhood",
                        "congestion_index": "Congestion (%)",
                        "speed_mph": "Average Speed (mph)",
                    }
                )
                return render.DataGrid(df)

        with ui.nav_panel("📈 Explore Trends"):
            chart_note = reactive.Value("")

            @render_plotly
            def readings_chart():
                def _empty_fig(msg: str):
                    chart_note.set("")
                    return go.Figure().update_layout(
                        annotations=[dict(text=msg, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14))],
                        xaxis=dict(visible=False),
                        yaxis=dict(visible=False),
                        height=400,
                    )

                from_, to_ = time_from_to()
                if not from_ or not to_:
                    return _empty_fig("Select a time range.")
                params = {"from": from_, "to": to_}
                if input.location_id():
                    params["location_id"] = input.location_id()
                data, err, truncated = api_get_all_readings(params)
                if err:
                    return _empty_fig(f"Error: {err}")
                if not data:
                    return _empty_fig("No readings match filters.")
                df = pd.DataFrame(data)
                locs = {r["id"]: r.get("name", r["id"]) for r in locations_list() if isinstance(r, dict)}
                if "location_id" in df.columns and locs:
                    df["location"] = df["location_id"].map(locs)
                df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True)
                df = df.sort_values("observed_at")

                # Downsample to hourly points so wider time windows stay readable
                df["hour"] = df["observed_at"].dt.floor("h")
                if "location" in df.columns and df["location"].nunique() > 1:
                    df = (
                        df.groupby(["hour", "location"], as_index=False)
                        .agg(congestion_index=("congestion_index", "mean"))
                        .sort_values("hour")
                    )
                else:
                    df = (
                        df.groupby(["hour"], as_index=False)
                        .agg(congestion_index=("congestion_index", "mean"))
                        .sort_values("hour")
                    )

                # Use milliseconds since epoch so Plotly treats x as date and applies tickformat
                df["x_ms"] = (df["hour"].astype("int64") // 1_000_000).astype("int")

                if "location" in df.columns and df["location"].nunique() > 1:
                    fig = px.line(
                        df,
                        x="x_ms",
                        y="congestion_index",
                        color="location",
                        title="Congestion Trends by Location (hourly)",
                        labels={"x_ms": "Date/Time", "congestion_index": "Congestion (%)", "location": "Location"},
                    )
                else:
                    loc_label = df["location"].iloc[0] if "location" in df.columns and len(df) else "Location"
                    fig = px.line(
                        df,
                        x="x_ms",
                        y="congestion_index",
                        title=f"Congestion Trends for {loc_label} (hourly)",
                        labels={"x_ms": "Date/Time", "congestion_index": "Congestion (%)"},
                    )
                x_min_ms = int(df["x_ms"].min())
                x_max_ms = int(df["x_ms"].max())

                # Note/disclaimer under the chart (only when "All locations" is selected)
                if not input.location_id():
                    shown_from = df["hour"].min()
                    shown_to = df["hour"].max()
                    shown_hours = int(((shown_to - shown_from).total_seconds() // 3600) + 1) if pd.notna(shown_from) and pd.notna(shown_to) else 0
                    msg = f"DISCLAIMER: Data limit reached. Displayed span of data is from {shown_from:%Y-%m-%d %H:%M} to {shown_to:%Y-%m-%d %H:%M} UTC (~{shown_hours} hours)."
                    if truncated:
                        msg += f" Data fetch cap reached (max {PAGE_SIZE * MAX_PAGES:,} raw readings), so the earliest part of the selected window may be omitted."
                    chart_note.set(msg)
                else:
                    chart_note.set("")

                fig.update_layout(
                    title_x=0.5,
                    xaxis_rangeslider_visible=True,
                    hovermode="x unified",
                    height=400,
                    margin=dict(t=50, b=50, l=50, r=50),
                    xaxis=dict(
                        type="date",
                        range=[x_min_ms, x_max_ms],
                        tickformat="%b %d\n%H:%M",
                    ),
                )
                fig.update_yaxes(range=[0, 100])
                return fig

            @render.ui
            def readings_note_ui():
                note = chart_note()
                if not note:
                    return ui.tags.div()
                return ui.tags.div(note, class_="trend-disclaimer")

        with ui.nav_panel("🤖 AI Summary"):

            @render.ui
            def ai_summary_ui():
                from_, to_ = time_from_to()
                if not from_ or not to_:
                    return ui.tags.p("Select a time range first.")

                params = {"from": from_, "to": to_}
                if input.location_id():
                    params["location_id"] = input.location_id()

                rows, api_err, _ = api_get_all_readings(params)
                if api_err:
                    return ui.tags.div(ui.tags.p(f"API error: {api_err}", class_="text-danger"), class_="alert alert-warning")
                if not rows:
                    return ui.tags.p("No readings in this window to summarize.")

                # Enrich rows with human-readable location metadata (intersection, city, neighborhood)
                loc_rows = [r for r in locations_list() if isinstance(r, dict) and r.get("id")]
                loc_index = {r["id"]: r for r in loc_rows}
                enriched = []
                for r in rows:
                    lid = r.get("location_id")
                    meta = loc_index.get(lid, {}) if lid else {}
                    enriched.append(
                        {
                            "intersection": meta.get("name") or lid,
                            "city": meta.get("city"),
                            "neighborhood": meta.get("neighborhood"),
                            "observed_at": r.get("observed_at"),
                            "congestion_index": r.get("congestion_index"),
                            "speed_mph": r.get("speed_mph"),
                        }
                    )

                try:
                    question = (
                        "Summarize congestion for this time window and filters using the JSON rows. "
                        "Each row has intersection, city, neighborhood, observed_at, congestion_index, and speed_mph.\n\n"
                        "Write 3–6 short bullet points, using Markdown with bold section labels like "
                        "'**Worst hotspots**', '**Clear routes**', '**Trends vs typical**'. "
                        "Focus on human-readable intersection and area names, not IDs."
                    )
                    text = summarize_congestion_data(enriched, question=question)
                except Exception as e:
                    return ui.tags.div(ui.tags.p(f"AI error: {e}", class_="text-danger"), class_="alert alert-warning")

                if not text:
                    text = "(AI returned an empty summary.)"

                formatted = _format_ai_text_as_html(text)

                return ui.tags.div(
                    ui.tags.div(
                        ui.HTML(formatted),
                        class_="bg-light p-3 border rounded ai-summary-text",
                        style="white-space: pre-wrap;",
                    ),
                )


# Populate location dropdown when locations load
@reactive.effect
def _update_location_choices():
    locs = locations_list()
    choices = {"": "All locations"}
    for row in locs:
        if isinstance(row, dict) and row.get("id") and row.get("name"):
            choices[row["id"]] = row["name"]
    ui.update_select("location_id", choices=choices, selected="")


@reactive.calc
def time_from_to():
    preset = input.time_preset()
    if preset == "custom":
        dr = input.date_range()
        try:
            if dr is not None and len(dr) >= 2:
                start, end = dr[0], dr[1]
                if start and end:
                    from_ = datetime(start.year, start.month, start.day, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    to_ = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    return from_, to_
        except (TypeError, IndexError, AttributeError):
            pass
        # Fallback: use data window when custom picker not ready
        start_d, end_d = _data_date_limits()
        from_ = datetime(start_d.year, start_d.month, start_d.day, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        to_ = datetime(end_d.year, end_d.month, end_d.day, 23, 59, 59, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return from_, to_
    return make_time_range(preset or "7d")



