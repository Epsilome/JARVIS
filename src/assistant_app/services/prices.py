from __future__ import annotations
import importlib, math, asyncio, inspect
from typing import Iterable, List
from loguru import logger
from assistant_app.adapters.scrapers import SCRAPERS  # dict[str, scraper]
from assistant_app.domain.benchmarks import value_score
from assistant_app.domain.models import Product
from assistant_app.services.cache import load_store_results, save_store_results


def search_products(query: str, category: str = "general", country_hint: str = "FR") -> List[Product]:
    """
    Search for products with smart category logic (like the CLI).
    Category: 'gaming', 'work', 'general'.
    """
    final_query = query
    if category == "gaming":
        # Ensure gaming keywords if not present
        if "rtx" not in query.lower() and "gtx" not in query.lower() and "gaming" not in query.lower():
            final_query += " rtx"
    elif category == "work":
        # French retail context: 'professionnel' helps filter out toys/accessories
        terms = ["professionnel", "pro", "business", "thinkpad", "latitude", "macbook"]
        if not any(t in query.lower() for t in terms):
            final_query += " professionnel"
    
    # Use Async Search for parallel scraping (Performance Boost)
    # We wrap it in asyncio.run() because this function is called synchronously by tools/CLI
    try:
        # Check if we are already in an event loop (unlikely for sync CLI/Tools, but possible)
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # We are in an async context, but this function is sync.
                # Ideally we should strictly separate sync/async paths.
                # For now, falling back to sync search_all to avoid "This event loop is already running"
                results = search_all(final_query, country_hint=country_hint)
            else:
                results = asyncio.run(search_all_async(final_query))
        except RuntimeError:
             results = asyncio.run(search_all_async(final_query))
    except Exception as e:
        logger.warning(f"Async search failed, falling back to sync: {e}")
        results = search_all(final_query, country_hint=country_hint)
    
    # Heuristic: Filter noise (Air fryers, accessories) based on price
    clean_results = []
    for p in results:
        price = getattr(p, "price", 0.0) or 0.0
        if category == "gaming" and price < 400:
            continue # Gaming PCs/Laptops are definitely > 400
        if category == "work" and price < 200:
            continue # Work laptops are rarely < 200
        clean_results.append(p)

    return clean_results

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
    for name, scraper in SCRAPERS.items():
        try:
            items = list(_run_scraper(scraper, query))
        except Exception as e:
            logger.error(f"[scraper] {name}: {e}")
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
        logger.error(f"[scraper] {name}: {e}")
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