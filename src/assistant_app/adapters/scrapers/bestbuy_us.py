# assistant_app/adapters/bestbuy_us.py
from __future__ import annotations
import os, math, requests
from typing import Iterable, List
from assistant_app.domain.models import Product
from assistant_app.domain.benchmarks import match_cpu, match_gpu, parse_tgp_w

BESTBUY_API = "https://api.bestbuy.com/v1/products"
# Laptops category id per Best Buy docs
LAPTOP_CAT = "abcat0502000"  # categoryPath.id=abcat0502000

def _build_specs(title: str) -> dict:
    return {
        "cpu":   match_cpu(title),
        "gpu":   match_gpu(title),
        "tgp_w": parse_tgp_w(title),
    }

def _canon(url: str) -> str:
    if not url:
        return ""
    return url.split("?", 1)[0].rstrip("/")

def _fetch_page(api_key: str, query_filters: str, page: int, page_size: int = 100) -> dict:
    params = {
        "apiKey": api_key,
        "format": "json",
        # only take attributes we actually need; 'url' is Best Buy's click-through URL
        "show": "sku,name,salePrice,regularPrice,url,shortDescription,manufacturer,modelNumber",
        "pageSize": page_size,
        "page": page,
        # don’t sort server-side; we’ll score client-side
    }
    url = f"{BESTBUY_API}({query_filters})"
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def search_laptops_us(min_price: float, max_price: float, max_results: int = 200) -> List[Product]:
    """
    Query Best Buy US for laptops in a price range.
    Returns Product objects compatible with your scorers.
    """
    api_key = os.getenv("BESTBUY_API_KEY") or os.getenv("BBY_API_KEY")
    if not api_key:
        raise RuntimeError("Set BESTBUY_API_KEY (or BBY_API_KEY) in your environment.")

    # Best Buy Products API filter syntax: products(<cond1>&<cond2>...)
    # Docs show 'show=' attribute selection and paging via page/pageSize. Responses are JSON with 'products' list. :contentReference[oaicite:2]{index=2}
    # Laptops category id: abcat0502000. 
    filt = (
        f'categoryPath.id={LAPTOP_CAT}'
        f'&salePrice>={min_price:.2f}&salePrice<={max_price:.2f}'
        f'&type=HardGood&active=true&onlineAvailability=true'
    )

    out: List[Product] = []
    seen = set()
    page = 1
    page_size = 100
    while True:
        data = _fetch_page(api_key, filt, page=page, page_size=page_size)
        products = data.get("products") or []
        for p in products:
            title = (p.get("name") or "").strip()
            price = p.get("salePrice")
            url = (p.get("url") or "").strip()  # Best Buy returns expiring click URLs :contentReference[oaicite:4]{index=4}
            if not (title and isinstance(price, (int, float)) and url):
                continue
            key = _canon(url)
            if key in seen:
                continue
            seen.add(key)
            specs = _build_specs(title)
            out.append(Product("BestBuy", "US", title, float(price), "USD", url, specs))

            if len(out) >= max_results:
                return out

        total_pages = int(data.get("totalPages") or 1)
        if page >= total_pages:
            break
        page += 1

    return out
