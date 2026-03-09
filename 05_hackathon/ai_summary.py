# ai_summary.py
# Generate AI summaries of congestion data slices
# Pairs with MIDTERM_DL_challenge.md / dashboard app
# DSAI tutorial scaffolding
#
# This script shows how to send a user-selected slice of congestion data
# (for example, a JSON response from the REST API) to an AI model
# and get back a short, actionable summary. It is designed to be simple,
# readable, and easy to hook into the API or dashboard later.

# 0. Setup #################################

import json
import os
from typing import Any, Dict, List, Optional, Union

import requests

try:
    # Load environment variables from .env if python-dotenv is installed
    from dotenv import load_dotenv  # type: ignore

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    # Safe to ignore if python-dotenv is not available
    pass


JsonLike = Union[Dict[str, Any], List[Any]]


# 1. Configuration ############################

OLLAMA_BASE_URL = (os.getenv("OLLAMA_BASE_URL") or "https://ollama.com").rstrip("/")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY") or ""
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL") or "gpt-oss:120b"


def _require_ollama_key() -> str:
    """Return the Ollama API key or raise a helpful error."""
    if not OLLAMA_API_KEY:
        raise RuntimeError(
            "OLLAMA_API_KEY is not set. Create a key at https://ollama.com/settings/keys "
            "and add it to your environment or .env file."
        )
    return OLLAMA_API_KEY


# 2. Prompt construction ############################

def build_system_prompt() -> str:
    """System instructions for the AI model."""
    return (
        "You are a traffic operations assistant for the Seattle metro area.\n"
        "You receive a small JSON payload describing congestion readings for one or more locations.\n"
        "Write a short, actionable summary for humans (2–5 bullet points). Be concise and specific.\n"
        "Focus on: where congestion is worst, where traffic is flowing well, how this period compares to typical,\n"
        "and any simple recommendations (routes to avoid, times to watch, or where conditions are improving).\n"
        "If the data is very limited, say so clearly."
    )


def build_user_prompt(
    data: JsonLike,
    question: Optional[str] = None,
) -> str:
    """Turn the user's data and question into a prompt string."""
    default_question = (
        "Using only the data below, summarize the congestion situation in a few bullet points. "
        "Mention worst locations, least congested areas, and any notable time-of-day patterns "
        "you can infer from the data."
    )
    q = (question or "").strip() or default_question
    json_blob = json.dumps(data, indent=2, sort_keys=True, default=str)
    return f"{q}\n\nData (JSON):\n{json_blob}"


# 3. Core function: summarize data ############################

def summarize_congestion_data(
    data: JsonLike,
    question: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Send a slice of congestion data to Ollama Cloud and return a text summary.

    Parameters
    ----------
    data:
        A Python dict or list representing the data you want summarized.
        Typically this is the JSON output from one of your REST API endpoints
        (e.g., /readings, /readings/top, or a custom aggregation).
    question:
        Optional natural-language question to steer the summary
        (e.g., 'Which intersections are currently most congested?').
        If omitted, a default actionable prompt is used.
    model:
        Optional Ollama model name. Defaults to OLLAMA_MODEL env var or 'gpt-oss:120b'.

    Returns
    -------
    str
        The AI-generated summary as plain text.
    """
    api_key = _require_ollama_key()
    base_url = OLLAMA_BASE_URL
    model_name = model or OLLAMA_MODEL

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(data, question)

    url = f"{base_url}/api/generate"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    body = resp.json()
    return (body.get("response") or "").strip()


# 4. CLI usage ############################

def _load_json_from_path(path: str) -> JsonLike:
    """Load JSON from a file path or '-' (stdin)."""
    if path == "-":
        return json.load(os.fdopen(0))
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    """
    Simple command-line interface:

    Examples
    --------
    1) Summarize JSON from a file containing API output:

        python ai_summary.py data/readings_window.json

    2) Summarize and override the question:

        python ai_summary.py data/readings_window.json \\
            --question "How does congestion in this window compare to typical rush hour?"
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate an AI summary for a JSON slice of congestion data using Ollama Cloud.",
    )
    parser.add_argument(
        "json_path",
        help="Path to a JSON file containing the data to summarize, or '-' to read JSON from stdin.",
    )
    parser.add_argument(
        "--question",
        help="Optional question/prompt for the AI. If omitted, a default actionable prompt is used.",
    )
    parser.add_argument(
        "--model",
        help=f"Optional Ollama model name (default: {OLLAMA_MODEL}).",
    )

    args = parser.parse_args()

    data = _load_json_from_path(args.json_path)
    summary = summarize_congestion_data(data, question=args.question, model=args.model)
    print(summary)


if __name__ == "__main__":
    main()

