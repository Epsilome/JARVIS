from contextlib import asynccontextmanager
import asyncio, os, time, pathlib  
from playwright.async_api import async_playwright, TimeoutError as PWTimeout, Error as PWError


UA = os.getenv("SCRAPER_USER_AGENT", "")
DELAY = float(os.getenv("SCRAPER_DELAY_SEC", "0.8"))
TIMEOUT = int(os.getenv("SCRAPER_REQUEST_TIMEOUT", "25")) * 1000
HEADLESS = os.getenv("SCRAPER_HEADLESS", "1") not in ("0", "false", "False")
DEBUG = os.getenv("SCRAPER_DEBUG", "0") in ("1", "true", "True")

CONSENT_BUTTON_TEXTS = [
    "Tout accepter", "J'accepte", "Accepter", "Continuer", "OK", "Accept all",
]

CONSENT_SELECTORS = [
    "button#didomi-notice-agree-button",
    "[id^='didomi'] button[aria-label*='accept' i]",
    "button[aria-label*='accept' i]",
    "button:has-text('Tout accepter')",
    "button:has-text(\"J'accepte\")",
    "button:has-text('Accepter')",
    "button:has-text('Continuer')",
]

ART_DIR = pathlib.Path(".scraper_artifacts")
ART_DIR.mkdir(exist_ok=True)

def _log(msg: str):
    if DEBUG: print(f"[scraper] {msg}")

async def save_artifact(page, name: str, folder=".scraper_artifacts"):
    os.makedirs(folder, exist_ok=True)
    ts = int(time.time())
    png = os.path.join(folder, f"{name}_{ts}.png")
    html = os.path.join(folder, f"{name}_{ts}.html")
    try:
        await page.screenshot(path=png, full_page=True)
    except Exception:
        pass
    try:
        html_str = await page.content()
        with open(html, "w", encoding="utf-8") as f:
            f.write(html_str)
    except Exception:
        pass
    print(f"[scraper] Saved {png} and {html}")


@asynccontextmanager
async def browser(*, headless: bool = True, storage_state_path: str | None = None):
    """
    Creates a BrowserContext. If storage_state_path is provided:
    - loads cookies/localStorage from the file if it exists
    - saves updated state back to that file on exit
    """
    async with async_playwright() as pw:
        b = await pw.chromium.launch(headless=headless)
        ctx = await b.new_context(
            storage_state=(storage_state_path if storage_state_path and os.path.exists(storage_state_path) else None)
        )
        try:
            yield ctx
        finally:
            if storage_state_path:
                os.makedirs(os.path.dirname(storage_state_path), exist_ok=True)
                await ctx.storage_state(path=storage_state_path)
            await ctx.close()
            await b.close()

async def _try_click_consent_on(page_or_frame, remaining: int) -> int:
    if remaining <= 0:
        return 0
    clicked = 0
    for sel in CONSENT_SELECTORS:
        if clicked >= remaining:
            break
        try:
            btn = await page_or_frame.query_selector(sel)
            if btn:
                _log(f"Found consent via selector: {sel}")
                await btn.click()
                clicked += 1
        except Exception:
            continue
    return clicked

async def _handle_consent(page, max_clicks: int = 2):
    clicks = 0
    try:
        clicks += await _try_click_consent_on(page, max_clicks - clicks)
    except Exception:
        pass
    for frame in page.frames:
        if clicks >= max_clicks:
            break
        try:
            clicks += await _try_click_consent_on(frame, max_clicks - clicks)
        except Exception:
            pass

async def safe_goto(page, url: str, wait_selector: str | None = None, name: str = "page",
                    consent_delay_ms: int | None = None, consent_max_clicks: int = 2):

    _log(f"GOTO {url}")
    await page.goto(url, timeout=TIMEOUT, wait_until="domcontentloaded")

    if consent_delay_ms:
        await page.wait_for_timeout(consent_delay_ms)

    await _handle_consent(page, max_clicks=consent_max_clicks)

    if wait_selector:
        try:
            await page.wait_for_selector(wait_selector, timeout=TIMEOUT)
        except Exception:
            _log(f"wait_selector timed out: {wait_selector}")
            await _save_artifact(page, name)


    await asyncio.sleep(DELAY)
    if DEBUG:

        ts = int(time.time())
        ART_DIR = pathlib.Path(".scraper_artifacts"); ART_DIR.mkdir(exist_ok=True)
        try:
            await page.screenshot(path=str(ART_DIR / f"{name}_{ts}.png"), full_page=True)
            (ART_DIR / f"{name}_{ts}.html").write_text(await page.content(), encoding="utf-8")
            _log(f"Saved {ART_DIR / f'{name}_{ts}.png'} and {ART_DIR / f'{name}_{ts}.html'}")
        except Exception as e:
            _log(f"artifact save failed: {e}")

async def autoscroll(page, steps: int = 8, pause: float = 0.4):
    """Scroll down to trigger lazy loaded results."""
    for _ in range(steps):
        await page.mouse.wheel(0, 2500)
        await asyncio.sleep(pause)
