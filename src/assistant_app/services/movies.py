import os, time, requests, hashlib
from dataclasses import dataclass
from assistant_app.config.settings import settings

TMDB = "https://api.themoviedb.org/3"
OMDB = "https://www.omdbapi.com"

@dataclass
class Movie:
    tmdb_id: str
    imdb_id: str | None
    title: str
    year: str
    tmdb_vote: float | None
    imdb_rating: float | None
    overview: str

def _tmdb_get(path: str, params: dict):
    params = dict(params or {})
    if not settings.TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY missing. Put it in .env")
    params["api_key"] = settings.TMDB_API_KEY
    r = requests.get(f"{TMDB}{path}", params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def _tmdb_external_ids(tmdb_id: str) -> dict:
    return _tmdb_get(f"/movie/{tmdb_id}/external_ids", {})

def _omdb_rating(imdb_id: str) -> float | None:
    key = os.getenv("OMDB_API_KEY", "")
    if not key: return None
    try:
        r = requests.get(OMDB, params={"i": imdb_id, "apikey": key}, timeout=20)
        r.raise_for_status()
        data = r.json()
        val = data.get("imdbRating")
        try: return float(val) if val and val != "N/A" else None
        except: return None
    except Exception:
        return None

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
    })["results"]

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
                # polite tiny delay so we don't hammer OMDb free tier
                time.sleep(0.2)
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
