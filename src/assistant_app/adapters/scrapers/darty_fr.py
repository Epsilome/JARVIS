# import asyncio, re, os
# from bs4 import BeautifulSoup
# from assistant_app.domain.models import Product
# from assistant_app.adapters.scrapers.browser import browser, safe_goto, autoscroll
# from assistant_app.domain.specs import extract_gpu, parse_price_eur

# SEARCH_URL = "https://www.darty.com/nav/recherche?text={query}"
# STATE_FILE = ".sessions/darty_state.json"

# async def _search_async(query: str) -> list[Product]:
#     out: list[Product] = []

#     async with browser(headless=False, storage_state_path=STATE_FILE) as ctx:
#         page = await ctx.new_page()

#         block_rx = re.compile(
#             r"(googletagmanager|doubleclick|facebook|criteo|adobedtm|tagcommander|matomo|optimizely|hotjar|appdynamics)",
#             re.I,
#         )
#         try:
#             await page.route("**/*", lambda route, req: route.abort() if block_rx.search(req.url) else route.continue_())
#         except Exception:
#             pass

#         await safe_goto(
#             page,
#             SEARCH_URL.format(query=query.replace(" ", "+")),
#             wait_selector=".product-list .product a[data-automation-id='product_title'], .product-list .product a.name",
#             name="darty",
#             consent_delay_ms=2200,
#             consent_max_clicks=1,
#         )


#         challenge_sel = (
#             "iframe[src*='captcha'], .geetest_holder, .geetest_panel, "
#             "[id*='captcha'], .tcaptcha, .gt_slider, .slider, .geetest_canvas_bg"
#         )
#         if await page.locator(challenge_sel).count():
#             print("[darty] challenge detected — please solve it in the opened browser. It will be remembered.")
#             await page.wait_for_selector(".product-list .product a[data-automation-id='product_title'], .product-list .product a.name", timeout=120_000)
#         # -------------------------------------------------------------

#         await autoscroll(page, steps=12, pause=0.35)
#         html = await page.content()
#         soup = BeautifulSoup(html, "lxml")

#         cards = soup.select(".product-list .product[data-automation-id='product_list_item'], .product-list .product")
#         for card in cards:
#             link_el = card.select_one(
#                 "a[data-automation-id='product_title'][href], a.name[href], .column.left a.link[href]"
#             )
#             title_el = card.select_one(
#                 "a[data-automation-id='product_title'] .reference, "
#                 "a[data-automation-id='product_title'], "
#                 "a.name, "
#                 ".column.center .reference"
#             )
#             price_el = card.select_one("[data-automation-id='product_price'], .price_container .price_product .price")

#             title = (title_el.get_text(" ", strip=True) if title_el else "").strip()
#             href = (link_el["href"] if link_el and link_el.has_attr("href") else "").strip()
#             if href and not href.startswith("http"):
#                 href = f"https://www.darty.com{href}"

#             price_txt = price_el.get_text(" ", strip=True) if price_el else ""
#             price = parse_price_eur(price_txt)

#             if not (title and href and price):
#                 continue

#             out.append(
#                 Product(
#                     store="Darty",
#                     country="FR",
#                     title=title,
#                     price=price,
#                     currency="EUR",
#                     url=href,
#                     specs={"gpu": extract_gpu(title)},
#                 )
#             )
#     return out

# def search(query: str) -> list[Product]:
#     return asyncio.run(_search_async(query))
