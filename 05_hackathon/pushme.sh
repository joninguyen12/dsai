#!/bin/bash
# pushme.sh

# Push the Seattle Congestion FastAPI app to Posit Connect

# Install rsconnect package for Python
pip install --upgrade rsconnect-python

# Navigate to this app folder (if run from repo root)
cd "$(dirname "$0")"

# Load environment with CONNECT_SERVER and CONNECT_API_KEY
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
else
  echo ".env file with CONNECT_SERVER and CONNECT_API_KEY not found in 05_hackathon."
  echo "Create it based on your other Posit examples, then re-run this script."
  exit 1
fi

# Push the FastAPI app to Posit Connect, using main:app to match manifest
rsconnect deploy fastapi \
  --server "$CONNECT_SERVER" \
  --api-key "$CONNECT_API_KEY" \
  --entrypoint main:app ./

