from __future__ import annotations
import asyncio, re
from bs4 import BeautifulSoup
from assistant_app.domain.models import Product
from assistant_app.adapters.scrapers.browser import browser, safe_goto
from assistant_app.domain.specs import parse_price_eur
from assistant_app.domain.benchmarks import match_cpu, match_gpu, parse_tgp_w

SEARCH_URL = "https://www.cdiscount.com/search/10/{query}.html#_his_"


def _clean_url(raw: str) -> str:
    u = (raw or "").strip()
    if not u:
        return u
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return "https://www.cdiscount.com" + u
    if "://www.cdiscount.com//www.cdiscount.com/" in u:
        u = u.replace("://www.cdiscount.com//www.cdiscount.com/", "://www.cdiscount.com/")
    return u

def _safe(fn, s):
    try:
        return fn(s)
    except Exception as e:
        print(f"[specs] {fn.__name__} failed: {e}")
        return None

def _build_specs(title: str) -> dict:
    return {
        "cpu":   _safe(match_cpu, title),
        "gpu":   _safe(match_gpu, title),
        "tgp_w": _safe(parse_tgp_w, title),   # ← likely source of “no such group”
    }

async def _search_async(query: str) -> list[Product]:
    out: list[Product] = []
    async with browser(headless=False) as ctx:
        page = await ctx.new_page()

        # Land and accept consent if present; don't over-constrain the wait selector
        await safe_goto(page, SEARCH_URL.format(query=query.replace(" ", "+")), wait_selector="body", name="cdiscount")

        # Try to see if any likely product nodes exist (repeat a few times)
        ok = False
        for _ in range(24):  # ~12s
            cnt = await page.locator(
                "article[data-e2e='offer-item'], article.offerWrapper, [data-e2e='lplr-title'], article h2"
            ).count()
            if cnt > 0:
                ok = True
                break
            await page.wait_for_timeout(500)

        # Lazy load: scroll a few times
        last_h = 0
        for _ in range(14):
            h = await page.evaluate("document.body.scrollHeight")
            if h == last_h:
                break
            last_h = h
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(450)

        # Debug: how many nodes do our selectors see?
        sel_sets = [
            "article[data-e2e='offer-item']",
            "article.offerWrapper",
            "[data-e2e='lplr-title']",
            "article h2",
        ]

        for sel in sel_sets:
            try:
                c = await page.locator(sel).count()
                print(f"[scraper] Cdiscount: selector {sel!r} -> {c} nodes")
            except Exception:
                pass

        data = []
        try:
            data = await page.evaluate(
                r"""
                () => {
                const items = [];
                const seen = new Set();

                const cards = Array.from(document.querySelectorAll(
                    "article[data-e2e='offer-item'], article.offerWrapper, article:has(h2)"
                ));

                // Looks like "699,99 €", "1 199,00 €" etc.
                const EUR_RE = /\d[\d\u00A0\u202F]{0,6}(?:[.,]\d{1,2})?\s*€/;

                for (const card of cards) {
                    // Skip obvious sponsor slots
                    const s = card.querySelector(".sponsor, [class*='sponsor']");
                    if (s && /sponsor/i.test(s.textContent || "")) continue;

                    // Title
                    const tEl = card.querySelector('[data-e2e="lplr-title"]') || card.querySelector("h2");
                    const title = (tEl?.textContent || "").replace(/\s+/g, " ").trim();
                    if (title.length < 6) continue;

                    // Href (article wrapped by <a> OR first anchor inside)
                    const a = card.closest("a[href]") || card.querySelector("a[href]");
                    const href = a ? (a.href || a.getAttribute("href") || "") : "";
                    if (!href) continue;

                    // ---- PRICE extraction (prefer the structured price block) ----

                    let priceText = "";
                    const pb = card.querySelector('[data-e2e="lplr-price"]');
                    if (pb) {
                    const pInner = pb.querySelector(".price") || pb;
                    const txt = (pInner.textContent || "").replace(/\s+/g, " ").trim();
                    if (EUR_RE.test(txt)) priceText = txt;
                    if (!priceText) {
                        const parts = Array.from(pb.querySelectorAll("*"))
                        .map(n => (n.textContent || "").replace(/\s+/g, " ").trim());
                        const lastEuro = parts.filter(t => EUR_RE.test(t)).pop();
                        if (lastEuro) priceText = lastEuro;
                    }
                    }
                    if (!priceText) {
                    for (const n of card.querySelectorAll("span,div,strong,b,p")) {
                        const t = (n.textContent || "").replace(/\s+/g, " ").trim();
                        if (EUR_RE.test(t)) priceText = t;  // keep last euro-looking token
                    }
                    }

                    if (!seen.has(href)) {
                    seen.add(href);
                    items.push({ href, title, priceText });
                    }
                }

                return items;
                }
                """
            )
        except Exception as e:
            print(f"[scraper] cdiscount evaluate failed: {e!r}")
            data = []

        # --- Fallback: parse static HTML with BeautifulSoup -----------------
        if not data:
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")
            nodes = soup.select("article[data-e2e='offer-item'], article.offerWrapper, article:has(h2)")
            print(f"[scraper] Cdiscount fallback soup nodes: {len(nodes)}")
            data = []
            for card in nodes:
                t_el = card.select_one('[data-e2e="lplr-title"]') or card.select_one("h2")
                title = (t_el.get_text(" ", strip=True) if t_el else "").strip()
                a_el = card.find("a", href=True)
                href = a_el["href"] if a_el else ""
                price_el = card.select_one('[data-e2e="lplr-price"]') or card.select_one(".price")
                price_text = (price_el.get_text(" ", strip=True) if price_el else "") or ""
                if not price_text:
                    # last-resort scan
                    for n in card.select("span,div,strong,b,p"):
                        txt = (n.get_text(" ", strip=True) or "").strip()
                        if "€" in txt:
                            price_text = txt
                if title and href:
                    data.append({"href": href, "title": title, "priceText": price_text})


        # --- Build Product list; log drops to diagnose range filters --------
        seen = set()
        drops = 0
        for row in data or []:
            href = _clean_url((row.get("href") or "").strip())
            title = (row.get("title") or "").strip()
            price_text = (row.get("priceText") or "").strip()
            price = parse_price_eur(price_text)

            if not (href and title and price):
                print(f"[drop] href={href!r} title={title[:60]!r} price_text={price_text!r}")
                drops += 1
                continue

            key = href.split("?", 1)[0]
            if key in seen:
                continue
            seen.add(key)

            specs = _build_specs(title)
            out.append(Product("Cdiscount", "FR", title, price, "EUR", href, {**specs}))

        print(f"[scraper] Cdiscount kept {len(out)} items; dropped {drops} with no parseable price/title/url")
    return out

def search(query: str) -> list[Product]:
    return asyncio.run(_search_async(query))