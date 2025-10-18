from __future__ import annotations
import importlib, math
from typing import Iterable
from assistant_app.adapters.scrapers import ALL as SCRAPERS  # dict[str, scraper]
from assistant_app.domain.benchmarks import value_score




SCRAPER_MODULES = [
    "assistant_app.scrapers.cdiscount_fr",
    # "assistant_app.scrapers.fnac_fr",
    # "assistant_app.scrapers.darty_fr",
]

def _value_score(p):
    # Pass title + specs (joined) + price
    specs_text = ""
    try:
        if isinstance(p.specs, dict):
            specs_text = " ".join(f"{k}:{v}" for k, v in p.specs.items() if v)
        else:
            specs_text = str(p.specs or "")
    except Exception:
        specs_text = str(p.specs or "")
    return value_score(p.title, specs_text, getattr(p, "price", 0.0) or 0.0)

def _normalize(products):
    return sorted(products, key=_value_score, reverse=True)

def _iter_scrapers():
    if isinstance(SCRAPERS, dict):
        yield from SCRAPERS.items()
    else:
        for i, s in enumerate(SCRAPERS):
            name = getattr(s, "NAME", None) or getattr(s, "__name__", None) or f"s{i}"
            yield name, s

def _run_scraper(scraper, query: str):
    if hasattr(scraper, "search") and callable(scraper.search):
        return scraper.search(query)
    import asyncio
    if hasattr(scraper, "search_async") and callable(scraper.search_async):
        return asyncio.run(scraper.search_async(query))
    if hasattr(scraper, "_search_async") and callable(scraper._search_async):
        return asyncio.run(scraper._search_async(query))
    raise RuntimeError(f"Scraper {scraper} has no recognized entrypoint")

def search_all(query: str, country_hint: str | None = None):
    target_country = country_hint or None
    products = []
    for name, scraper in _iter_scrapers():
        try:
            items = list(_run_scraper(scraper, query))
        except Exception as e:
            print(f"[scraper] {name}: {e}")
            continue
        if target_country:
            items = [p for p in items if getattr(p, "country", None) == target_country]
        products.extend(items)

    seen, out = set(), []
    for p in products:
        key = (p.url or "").split("?", 1)[0]
        if key in seen: 
            continue
        seen.add(key)
        out.append(p)
    return out