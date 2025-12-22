from __future__ import annotations
import importlib, math, asyncio, inspect
from typing import Iterable, List
from assistant_app.adapters.scrapers import ALL as SCRAPERS  # dict[str, scraper]
from assistant_app.domain.benchmarks import value_score
from assistant_app.domain.models import Product
from assistant_app.services.cache import load_store_results, save_store_results




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

async def _run_scraper_async(scraper, name: str, query: str) -> List[Product]:
    try:
        # Prefer explicit async entrypoint if present
        if hasattr(scraper, "search_async") and inspect.iscoroutinefunction(scraper.search_async):
            items = await scraper.search_async(query)
        else:
            # Handle `search` being either sync or async
            search_fn = getattr(scraper, "search", None)
            if search_fn is None:
                # Last-resort: internal async (avoid if possible, but await it if it exists)
                internal = getattr(scraper, "_search_async", None)
                if internal and inspect.iscoroutinefunction(internal):
                    items = await internal(query)
                else:
                    raise TypeError(f"{name}: no usable search entrypoint")
            elif inspect.iscoroutinefunction(search_fn):
                items = await search_fn(query)
            else:
                # sync search() -> run in thread so we don't nest event loops
                items = await asyncio.to_thread(search_fn, query)

        # cache on success
        try:
            save_store_results(query, name, items)
        except Exception:
            pass

        return items or []
    except Exception as e:
        print(f"[scraper] {name}: {e}")
        return []

async def search_all_async(query: str, use_cache: bool = True, force_refresh: bool = False) -> List[Product]:
    results: List[Product] = []
    to_fetch = []

    if use_cache and not force_refresh:
        for name, scraper in SCRAPERS.items():
            cached = None
            try:
                cached = load_store_results(query, name)
            except Exception:
                cached = None
            if cached:
                results.extend(cached)
            else:
                to_fetch.append((name, scraper))
    else:
        to_fetch = list(SCRAPERS.items())

    tasks = [asyncio.create_task(_run_scraper_async(scraper, name, query)) for name, scraper in to_fetch]
    fetched_lists = await asyncio.gather(*tasks, return_exceptions=False)
    for lst in fetched_lists:
        results.extend(lst)

    return results