import json, os, re, datetime
from pathlib import Path
from typing import Iterable, List, Optional
from assistant_app.domain.models import Product

# where cached files live
CACHE_ROOT = Path(".cache/prices")

def _slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9\-_.]+", "", s)
    return s[:140]

def _today_str() -> str:
    return datetime.date.today().isoformat()

def _dated_dir(date_str: Optional[str] = None) -> Path:
    return CACHE_ROOT / (date_str or _today_str())

def _file_path(query: str, store: str, date_str: Optional[str] = None) -> Path:
    q = _slugify(query)
    st = _slugify(store)
    return _dated_dir(date_str) / f"{q}__{st}.json"

def save_store_results(query: str, store: str, items: Iterable[Product], date_str: Optional[str] = None) -> Path:
    """Write one store's results to cache (query+store scoped)."""
    d = _dated_dir(date_str)
    d.mkdir(parents=True, exist_ok=True)
    fp = _file_path(query, store, date_str)
    payload = {
        "query": query,
        "store": store,
        "date": date_str or _today_str(),
        "items": [p.to_dict() for p in items],  # requires Product.to_dict()
    }
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return fp

def load_store_results(query: str, store: str, date_str: Optional[str] = None) -> Optional[List[Product]]:
    """Load one store's results for a given day. Returns None if missing."""
    fp = _file_path(query, store, date_str)
    if not fp.exists():
        return None
    try:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Product.from_dict(x) for x in data.get("items", [])]
    except Exception:
        return None

def load_latest_store_results(query: str, store: str, lookback_days: int = 7) -> Optional[List[Product]]:
    """Find the newest available cached results within the lookback window."""
    today = datetime.date.today()
    for i in range(lookback_days + 1):
        d = (today - datetime.timedelta(days=i)).isoformat()
        items = load_store_results(query, store, d)
        if items:
            return items
    return None
