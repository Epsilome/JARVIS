# src/assistant_app/usecases/search_prices.py
import asyncio
import inspect
from typing import List
from assistant_app.adapters.scrapers import SCRAPERS
from assistant_app.domain.models import Product
from assistant_app.services.cache import load_store_results, save_store_results  # your cache helpers

async def _run_scraper(scraper, name: str, query: str) -> List[Product]:
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
                # sync search() → run in thread so we don't nest event loops
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

    tasks = [asyncio.create_task(_run_scraper(scraper, name, query)) for name, scraper in to_fetch]
    fetched_lists = await asyncio.gather(*tasks, return_exceptions=False)
    for lst in fetched_lists:
        results.extend(lst)

    return results
