#!/usr/bin/env bash
# Run the Shiny dashboard using the project venv (avoids Anaconda picking up the wrong Python)
cd "$(dirname "$0")"
.venv/bin/python -m shiny run dashboard/app.py --port 8001 "$@"
