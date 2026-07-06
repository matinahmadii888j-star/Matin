import os
import requests

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


def search_poster(title: str):
    """Best-effort poster lookup on TMDB. Returns a poster URL or None if not found.
    (Description text is no longer sourced from here — see ai.py.)"""
    if not TMDB_API_KEY:
        return None
    try:
        resp = requests.get(
            TMDB_SEARCH_URL,
            params={"api_key": TMDB_API_KEY, "query": title},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return None
        poster_path = results[0].get("poster_path")
        return f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None
    except Exception:
        return None
