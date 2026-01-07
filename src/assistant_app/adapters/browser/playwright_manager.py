import threading
import queue
from playwright.sync_api import sync_playwright, Playwright, Browser, Page
from typing import Optional, Any
from loguru import logger
import time

import atexit

class PlaywrightManager:
    """
    Runs Playwright in a dedicated thread to avoid conflicts with the main asyncio loop.
    All interactions are done via a thread-safe Queue.
    """
    _instance = None
    _queue = queue.Queue()
    _thread = None
    _ready = threading.Event()
    
    # Internal state (only accessed by worker thread)
    _playwright: Optional[Playwright] = None
    _browser: Optional[Browser] = None
    _page: Optional[Page] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PlaywrightManager, cls).__new__(cls)
            cls._instance._start_worker()
            atexit.register(cls._instance.stop)
        return cls._instance

    def stop(self):
        """Clean shutdown (called on exit)."""
        logger.info("Stopping Playwright Manager...")
        self.close() # Submit close task
        # Wait briefly then kill?
        # The worker loop handles the close task.

    def _start_worker(self):
        """Starts the background worker thread."""
        logger.info("Starting Playwright Worker Thread...")
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="PlaywrightWorker")
        self._thread.start()

    def _worker_loop(self):
        """Dedicated loop for Playwright operations."""
        # Lazy load: Do not init here. Wait for first task.
        
        self._ready.set()
        
        while True:
            try:
                task = self._queue.get()
                if task is None: break # Poison pill
                
                func, args, result_queue = task
                try:
                    res = func(*args)
                    result_queue.put({"status": "success", "result": res})
                except Exception as e:
                    logger.error(f"Worker Task Failed: {e}")
                    result_queue.put({"status": "error", "error": e})
                finally:
                    self._queue.task_done()
            except Exception as e:
                logger.error(f"Worker Loop Error: {e}")

    def _init_internal(self):
        """Internal initialization (Runs on Worker Thread)."""
        logger.info("Initializing INTERNAL Playwright...")
        self._playwright = sync_playwright().start()
        try:
            self._browser = self._playwright.chromium.launch(headless=False, channel="chrome", args=["--start-maximized"])
        except:
             logger.warning("Chrome not found, using bundled Chromium.")
             self._browser = self._playwright.chromium.launch(headless=False, args=["--start-maximized"])
        
        # Use a persistent context if possible, or just a new one
        self._browser.on("disconnected", lambda: self._handle_disconnect())
        context = self._browser.new_context(no_viewport=True)
        self._page = context.new_page() # Keep one 'active' page reference, though we might have many

    def _handle_disconnect(self):
        logger.warning("Browser disconnected! Resetting state.")
        self._browser = None
        self._page = None

    def _recover_if_needed(self):
        """Checks if browser is dead and restarts it."""
        if not self._browser or not self._browser.is_connected():
            logger.warning("Browser appears disconnected. Attempting restart...")
            try:
                if self._browser: 
                    try: self._browser.close()
                    except: pass
                if self._playwright:
                    try: self._playwright.stop()
                    except: pass
            except: pass
            self._init_internal()

    def _submit_task(self, func, *args) -> Any:
        """Submits a task to the worker and waits for result."""
        if not self._ready.is_set():
             self._ready.wait(timeout=10)
        
        res_q = queue.Queue()
        self._queue.put((func, args, res_q))
        
        try:
            res = res_q.get(timeout=30)
            if res["status"] == "success":
                return res["result"]
            else:
                # If error is "Target page, context or browser has been closed", we should trigger recovery?
                # But we are in the main thread here. The worker already tried and failed.
                # The worker should handle recovery ideally.
                # Let's just raise for now.
                raise res["error"]
        except queue.Empty:
            logger.error("Playwright Task Timeout")
            return None

    # --- Public API (Proxies) ---

    def initialize(self):
        self._ready.wait(timeout=5)

    def new_tab(self, url: str):
        """Opens a URL in a NEW tab."""
        def _action(u):
            self._recover_if_needed()
            # Get default context or create new
            if not self._browser.contexts:
                 ctx = self._browser.new_context(no_viewport=True)
            else:
                 ctx = self._browser.contexts[0]
                 
            p = ctx.new_page()
            self._page = p # Update active page reference
            logger.info(f"Opening new tab: {u}")
            p.goto(u)
            p.bring_to_front()
            
        self._submit_task(_action, url)

    def open_url(self, url: str):
        """Opens URL. Defaults to new tab to avoid losing state."""
        self.new_tab(url)

    def get_page_content(self) -> str:
        def _action():
            self._recover_if_needed()
            if not self._page or self._page.is_closed():
                 # Try to find any open page
                 if self._browser.contexts and self._browser.contexts[0].pages:
                      self._page = self._browser.contexts[0].pages[-1]
                 else:
                      return ""
            return self._page.evaluate("document.body.innerText")
        return self._submit_task(_action) or ""

    def scroll(self, direction: str):
        def _action(d):
            if not self._page or self._page.is_closed(): return
            delta = 600 if d == "down" else -600
            self._page.mouse.wheel(0, delta)
        self._submit_task(_action, direction)

    def go_back(self):
        def _action():
            if self._page: self._page.go_back()
        self._submit_task(_action)

    def refresh(self):
        def _action():
            if self._page: self._page.reload()
        self._submit_task(_action)

    def close_tab(self, index: int = None):
        """Closes the current tab or a specific tab by 1-based index."""
        def _action(idx):
            if not self._browser or not self._browser.contexts: return
            
            pages = self._browser.contexts[0].pages
            target_page = None
            
            if idx is not None:
                # 1-based index
                if 1 <= idx <= len(pages):
                    target_page = pages[idx - 1]
                else:
                    logger.warning(f"Tab index {idx} out of range (1-{len(pages)})")
                    return
            else:
                target_page = self._page
            
            if target_page and not target_page.is_closed():
                # If we are closing the active page, switch reference
                is_active = (target_page == self._page)
                target_page.close()
                
                # Update Pages list after close
                pages = self._browser.contexts[0].pages
                if is_active:
                     if pages:
                          self._page = pages[-1]
                          self._page.bring_to_front()
                     else:
                          self._page = None
                          
        self._submit_task(_action, index)

    def close_all_tabs(self):
        """Closes ALL tabs in the default context."""
        def _action():
            if self._browser and self._browser.contexts:
                for page in self._browser.contexts[0].pages:
                    try: page.close()
                    except: pass
                self._page = None
        self._submit_task(_action)

    def close(self):
        def _action():
            if self._browser: self._browser.close()
            if self._playwright: self._playwright.stop()
        self._submit_task(_action)

browser_manager = PlaywrightManager()
