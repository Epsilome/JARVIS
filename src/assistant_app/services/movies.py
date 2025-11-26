import json, os, time, requests, hashlib
from dataclasses import dataclass
from pathlib import Path
from assistant_app.config.settings import settings

TMDB = "https://api.themoviedb.org/3"
OMDB = "https://www.omdbapi.com"

# Simple on-disk cache for HTTP JSON responses
CACHE_DIR = Path(".http_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _cache_path(prefix: str, key_parts: dict) -> Path:
    """Build a stable filename from a prefix + sorted key parts."""
    raw = prefix + json.dumps(key_parts, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{prefix}_{h}.json"


def _cache_load(path: Path, ttl_seconds: int | None) -> dict | None:
    """Return cached JSON if fresh enough."""
    if not path.exists():
        return None
    if ttl_seconds is not None:
        age = time.time() - path.stat().st_mtime
        if age > ttl_seconds:
            return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _cache_save(path: Path, data: dict) -> None:
    try:
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

@dataclass
class Movie:
    tmdb_id: str
    imdb_id: str | None
    title: str
    year: str
    tmdb_vote: float | None
    imdb_rating: float | None
    overview: str

def _tmdb_get(path: str, params: dict, *, cache_ttl: int | None = None):
    """
    GET helper for TMDb, with optional JSON cache.

    cache_ttl in seconds:
      - None  -> no caching
      - 3600  -> 1 hour, etc.
    """
    params = dict(params or {})
    if not settings.TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY missing. Put it in .env")
    params["api_key"] = settings.TMDB_API_KEY

    cache_key = {"path": path, "params": params}
    cache_file = _cache_path("tmdb", cache_key)

    if cache_ttl is not None:
        cached = _cache_load(cache_file, cache_ttl)
        if cached is not None:
            return cached

    r = requests.get(f"{TMDB}{path}", params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    if cache_ttl is not None:
        _cache_save(cache_file, data)
    return data


def _tmdb_external_ids(tmdb_id: str) -> dict:
    # External IDs almost never change; cache for 30 days
    return _tmdb_get(f"/movie/{tmdb_id}/external_ids", {}, cache_ttl=30 * 24 * 3600)


def _omdb_rating(imdb_id: str) -> float | None:
    key = os.getenv("OMDB_API_KEY", "")
    if not key:
        return None

    cache_key = {"imdb_id": imdb_id}
    cache_file = _cache_path("omdb", cache_key)

    # 1. If cached, we return IMMEDIATELY (No sleep!)
    cached = _cache_load(cache_file, ttl_seconds=7 * 24 * 3600)
    if isinstance(cached, dict) and "rating" in cached:
        return cached["rating"]

    try:
        r = requests.get(OMDB, params={"i": imdb_id, "apikey": key}, timeout=20)
        r.raise_for_status()
        
        # 2. MOVE SLEEP HERE. Only sleep if we actually hit the API.
        time.sleep(0.2) 
        
        data = r.json()
        val = data.get("imdbRating")
        rating = float(val) if val and val != "N/A" else None
    except Exception:
        rating = None

    _cache_save(cache_file, {"rating": rating})
    return rating


def top_horror(limit: int = 20, year_from: int = 2000, min_votes: int = 200) -> list[Movie]:
    """Fetch horror list from TMDb; enrich with IMDb ratings when possible."""
    data = _tmdb_get("/discover/movie", {
        "with_genres": "27",
        "sort_by": "vote_average.desc",
        "vote_count.gte": min_votes,
        "include_adult": "false",
        "language": "en-US",
        "page": 1,
        "primary_release_date.gte": f"{year_from}-01-01",
    },
    cache_ttl=6 * 3600,  # 6 hours cache for the list
    )["results"]

    picks = data[:limit]
    out: list[Movie] = []
    for m in picks:
        tmdb_id = str(m["id"])
        title = m["title"]
        year = (m.get("release_date") or "")[:4]
        tmdb_vote = float(m.get("vote_average") or 0)

        imdb_id = None
        imdb = None
        try:
            ext = _tmdb_external_ids(tmdb_id)
            imdb_id = ext.get("imdb_id")
            if imdb_id:
                imdb = _omdb_rating(imdb_id)
        except Exception:
            pass

        out.append(Movie(
            tmdb_id=tmdb_id,
            imdb_id=imdb_id,
            title=title,
            year=year,
            tmdb_vote=tmdb_vote,
            imdb_rating=imdb,
            overview=m.get("overview") or ""
        ))
    # Sort by IMDb when present, else TMDb
    out.sort(key=lambda x: (x.imdb_rating if x.imdb_rating is not None else x.tmdb_vote or 0), reverse=True)
    return out
