#!/bin/bash
# push_shiny.sh
#
# Deploy the Seattle Congestion Shiny dashboard (Shiny for Python)
# to Posit Connect as a separate app from the FastAPI API.

set -e

# Install / upgrade rsconnect for Python
pip install --upgrade rsconnect-python

# Navigate to this app folder (if run from repo root)
cd "$(dirname "$0")"

# Load Posit Connect credentials: CONNECT_SERVER and CONNECT_API_KEY
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
else
  echo ".env file with CONNECT_SERVER and CONNECT_API_KEY not found in 05_hackathon."
  echo "Create it based on your other Posit examples, then re-run this script."
  exit 1
fi

# Deploy as a Shiny for Python app. The --new flag forces creation of a NEW
# content item (separate from the FastAPI API), even if this folder was
# previously deployed as another app mode.
rsconnect deploy shiny \
  --server "$CONNECT_SERVER" \
  --api-key "$CONNECT_API_KEY" \
  --new \
  .

