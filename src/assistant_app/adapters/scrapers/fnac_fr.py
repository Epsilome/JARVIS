# import asyncio, re, os
# from bs4 import BeautifulSoup
# from assistant_app.adapters.scrapers.browser import browser, safe_goto, autoscroll
# from assistant_app.domain.models import Product
# from assistant_app.domain.specs import extract_gpu, parse_price_eur


# SEARCH_URL = "https://www.fnac.com/SearchResult/ResultList.aspx?SCat=0%211&Search={query}"

# async def _search_async(query: str) -> list[Product]:
#     out = []
#     async with browser(headless=False) as ctx:
#         page = await ctx.new_page()
#         await safe_goto(
#             page,
#             SEARCH_URL.format(query=query.replace(" ", "+")),
#             wait_selector="[data-testid='product-item'] a[data-testid='product-item-link'], .Article-itemGroup a.Article-title",
#             name="fnac",
#         )
#         await autoscroll(page, steps=10, pause=0.3)

#         soup = BeautifulSoup(await page.content(), "lxml")
#         cards = soup.select("[data-testid='product-item'], .Article-itemGroup, li.Article-item, div.Article-item")

#         for card in cards:
#             link_el  = card.select_one("a[data-testid='product-item-link'], a.Article-title, a[href*='/p-']")
#             title_el = card.select_one("[data-testid='product-item-title'], .Article-title")
#             price_el = card.select_one("[data-testid='product-price'], .userPrice, [data-testid='pricing-zone'], .f-priceBox-price")

#             title = (title_el.get_text(' ', strip=True) if title_el else '').strip()
#             url = (link_el["href"] if link_el and link_el.has_attr("href") else "").strip()
#             if url and not url.startswith("http"):
#                 url = f"https://www.fnac.com{url}"

#             price = parse_price_eur(price_el.get_text(' ', strip=True) if price_el else "")
#             if title and url and price:
#                 out.append(Product("Fnac", "FR", title, price, "EUR", url, {"gpu": extract_gpu(title)}))
#     return out

# def search(query: str) -> list[Product]:
#     return asyncio.run(_search_async(query))
