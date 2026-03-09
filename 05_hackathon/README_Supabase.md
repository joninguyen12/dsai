# Congestion database scripts

Seed the Supabase congestion tables (Greater Seattle freeway intersections + synthetic readings).

## Setup

```bash
cd 05_hackathon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `05_hackathon` with your Supabase credentials (from Project Settings -> API):

```
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_KEY=your-anon-public-key
```

Or export them: `export SUPABASE_URL=... SUPABASE_KEY=...`

## Run

1. Seed locations (18 intersections):  
   `python scripts/seed_locations.py`

2. Generate congestion data (7 days, 15-min intervals):  
   `python scripts/generate_congestion_data.py`
