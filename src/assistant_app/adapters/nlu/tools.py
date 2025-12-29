import logging
import json
import contextlib
import io
from duckduckgo_search import DDGS

try:
    from dbgpu.src import DBGPU
except ImportError:
    DBGPU = None

from assistant_app.domain.benchmarks import get_cpu_specs, get_gpu_specs, get_cached_specs, save_cached_specs
from assistant_app.services.prices import search_products
from assistant_app.adapters.scrapers.specs import search_specs
from assistant_app.domain.cpu_registry import LaptopCPUBase
from assistant_app.domain.ram_registry import RAMRegistry
from assistant_app.domain.ssd_registry import SSDRegistry
from assistant_app.domain.review_rag import ReviewIntelligence
from assistant_app.services.ingestion.review_ingest import ReviewIngestor
from assistant_app.adapters.system_control import (
    set_volume, lock_screen, minimize_all, open_app as sys_open_app, focus_window
)
from assistant_app.services.reminders import add_once
from assistant_app.adapters.nlu.time_parse import parse_when
from assistant_app.adapters.system_health import get_system_health

logger = logging.getLogger(__name__)

def set_reminder(task: str, when: str = "1 minute") -> str:
    """
    Sets a reminder for a specific task at a given time or time delta.
    Input 'when' can be 'in 5 minutes', 'tomorrow at 10am', '17:00', etc.
    """
    logger.info(f"Tool Call: set_reminder('{task}', '{when}')")
    try:
        dt, _ = parse_when(when)
        
        if not dt:
             return f"Could not parse the time '{when}'. Please try a different format (e.g. 'in 10 minutes', 'at 5pm')."
             
        add_once(task, dt)
        return f"Reminder set: I will remind you to '{task}' at {dt.strftime('%H:%M')}."
    except Exception as e:
        logger.error(f"Reminder error: {e}")
        return f"Failed to set reminder: {e}"

def delete_reminder(partial_text: str) -> str:
    """
    Deletes a reminder if the text matches.
    """
    logger.info(f"Tool Call: delete_reminder('{partial_text}')")
    # Fuzzy match logic
    from assistant_app.interfaces.scheduler.scheduler import scheduler
    
    found = []
    # Search for job with matching text kwarg
    for job in scheduler.get_jobs():
        txt = job.kwargs.get('text', '').lower()
        if partial_text.lower() in txt:
             found.append(job)
             
    if not found:
        return f"No active reminders found matching '{partial_text}'."
        
    deleted_count = 0
    for job in found:
        try:
            job.remove()
            deleted_count += 1
        except: pass
        
    return f"Removed {deleted_count} reminder(s) containing '{partial_text}'."

def get_active_reminders() -> str:
    """
    Returns a list of all currently scheduled reminders.
    """
    logger.info("Tool Call: get_active_reminders()")
    from assistant_app.interfaces.scheduler.scheduler import scheduler
    
    jobs = scheduler.get_jobs()
    if not jobs:
        return "You have no active reminders."
        
    summary = f"Found {len(jobs)} active reminders:\n"
    for job in jobs:
        # job.id is usually 'rem_ID' or 'eye_HHMM'
        # job.kwargs['text'] holds the message for Cron/Interval
        # job.args[0] holds the message for Date/Once
        txt = job.kwargs.get('text')
        if not txt and job.args:
            txt = job.args[0]
        if not txt:
            txt = 'Unknown Task'
            
        next_run = job.next_run_time.strftime("%H:%M") if job.next_run_time else "Unknown Time"
        summary += f"- '{txt}' at {next_run} (ID: {job.id})\n"
        
    return summary

def lookup_hardware(query: str) -> str:
    """
    Looks up hardware specifications and benchmark scores from the local database.
    Useful for questions like "What is the score of RTX 4090?" or "Specs of Ryzen 9".
    """
    logger.info(f"Tool Call: lookup_hardware('{query}')")
    
    # Handle comparisons (e.g. "RTX 4090 vs 3080")
    if " vs " in query.lower():
        parts = query.lower().split(" vs ")
        results = []
        for p in parts:
            results.append(lookup_hardware(p.strip()))
        return "\n\n".join(results)
    
    # Try CPU first
    cpu = get_cpu_specs(query)
    if cpu:
        price_str = f"Price: ${cpu['price']}" if cpu['price'] > 0 else ""
        return f"Found CPU: {cpu['name']}\nMark: {cpu['mark']}\nRank: {cpu['rank']}\n{price_str}".strip()
    
    # Try GPU
    gpu = get_gpu_specs(query)
    if gpu:
        price_str = f"Price: ${gpu['price']}" if gpu['price'] > 0 else ""
        return f"Found GPU: {gpu['name']}\nMark: {gpu['mark']}\nRank: {gpu['rank']}\n{price_str}".strip()
    
    return f"No hardware found matching '{query}' in the database."

def lookup_detailed_specs(product_name: str) -> str:
    """
    Looks up detailed specifications (VRAM, TDP, Cores, etc.) from dbgpu or web/cache.
    Use this for technical questions like "TDP of RTX 4090" or "How much VRAM".
    """
    logger.info(f"Tool Call: lookup_detailed_specs('{product_name}')")
    
    # 1. Try DBGPU (Fastest, Local, Accurate for GPUs)
    try:
        if DBGPU:
            # Suppress "GPU not found" noise for CPU queries
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                try:
                    db = DBGPU()
                    gpu_data = db.get_gpu(product_name)
                except:
                    gpu_data = None
        else:
            gpu_data = None

        if gpu_data and hasattr(gpu_data, '__dict__'):
             clean_data = {k: v for k, v in gpu_data.__dict__.items() if not k.startswith('_') and v is not None}
             if clean_data:
                 return f"Specs for {product_name} (Source: DBGPU):\n{json.dumps(clean_data, indent=2, default=str)}"
    except Exception as e:
        # Debug log only
        logging.getLogger(__name__).debug(f"DBGPU Lookup info: {e}")

    # 2. Try CPU Registry for CPUs
    try:
        cpu_reg = LaptopCPUBase.get_instance()
        cpu_data = cpu_reg.get_cpu(product_name)
        if cpu_data:
            return f"Specs for {product_name} (Source: CPU Registry):\n{json.dumps(cpu_data, indent=2)}"
    except Exception as e:
        logger.warning(f"CPU Registry lookup failed: {e}")

    # Heuristic: Check for RAM keywords to prioritize RAM Registry
    is_ram_query = any(k in product_name.lower() for k in ["ram", "ddr", "mhz", "memory", "cl16", "cl18", "dimm"])

    if is_ram_query:
        try:
            from assistant_app.domain.ram_registry import RAMRegistry
            ram_reg = RAMRegistry.get_instance()
            clean_q = product_name.lower().replace("specs of", "").replace("specs", "").strip()
            ram_data = ram_reg.get_ram(clean_q)
            if ram_data:
                 return f"Specs for {product_name} (Source: RAM Registry):\n{json.dumps(ram_data, indent=2)}"
        except Exception: pass

    # 3. Try SSD Registry
    try:
        ssd_reg = SSDRegistry.get_instance()
        # Clean query for best match (e.g. remove "specs of")
        clean_q = product_name.lower().replace("specs of", "").replace("specs", "").strip()
        ssd_data = ssd_reg.get_ssd(clean_q)
        if ssd_data:
             return f"Specs for {product_name} (Source: SSD Registry):\n{json.dumps(ssd_data, indent=2)}"
    except Exception as e:
        logger.warning(f"SSD Registry lookup failed: {e}")

    # 4. Try RAM Registry (Fallback if not caught by keyword)
    if not is_ram_query:
        try:
            ram_reg = RAMRegistry.get_instance()
            clean_q = product_name.lower().replace("specs of", "").replace("specs", "").strip()
            ram_data = ram_reg.get_ram(clean_q)
            if ram_data:
                 return f"Specs for {product_name} (Source: RAM Registry):\n{json.dumps(ram_data, indent=2)}"
        except Exception as e:
            logger.warning(f"RAM Registry lookup failed: {e}")

    # 5. Check Local Cache (for non-GPU/CPU/SSD/RAM items or previously scraped stuff)
    cached = get_cached_specs(product_name)
    if cached:
        logger.info("Found specs in cache.")
        return f"Specs for {product_name} (Cached):\n{cached}"
    
    # 3. Search Web & Extract (Fallback)
    specs = search_specs(product_name)
    if specs:
        # Cache it
        save_cached_specs(product_name, specs)
        return f"Specs for {product_name} (Web):\n{specs}"
    
    return f"Could not find detailed specs for '{product_name}'."

def search_web(query: str) -> str:
    """
    Searches the web using DuckDuckGo.
    Useful for recent events, movies, news, or general knowledge not in the database.
    """
    logger.info(f"Tool Call: search_web('{query}')")
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found."
        
        summary = ""
        for r in results:
            summary += f"- {r['title']}: {r['body']} ({r['href']})\n"
        return summary
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"Error searching web: {e}"

def get_live_price(product: str, category: str = "general") -> str:
    """
    Searches for live prices of a product from online retailers.
    Useful for "How much is X?" or "Price of Y".
    Category can be 'gaming' (adds RTX query logic), 'work', or 'general'.
    """
    logger.info(f"Tool Call: get_live_price('{product}', category='{category}')")
    
    # Fallback for empty product (LLM extraction failure)
    search_term = product
    if not search_term or not search_term.strip():
        if category == "gaming": search_term = "pc portable gamer"
        elif category == "work": search_term = "pc portable professionnel"
        else: search_term = "pc portable"
        logger.info(f"Product was empty. Defaulting to '{search_term}'.")

    try:
        results = search_products(search_term, category=category, country_hint="FR") # Default to FR
        if not results:
            return "No live prices found."
        
        # Sort by price
        results.sort(key=lambda x: x.price or float('inf'))
        
        summary = f"Found {len(results)} deals for '{product}' ({category}):\n"
        for p in results[:5]:
            summary += f"- {p.title}: {p.price} € ({p.store})\n"
        return summary
    except Exception as e:
        logger.error(f"Price search error: {e}")
        return f"Error searching prices: {e}"

def get_product_opinions(product_name: str) -> str:
    """
    Gets qualitative "Pros & Cons" by analyzing Reddit/YouTube reviews.
    Useful for: "Is the screen bright?", "Does it overheat?", "Reviews of X".
    """
    logger.info(f"Tool Call: get_product_opinions('{product_name}')")
    try:
        rag = ReviewIntelligence.get_instance()
        opinions = rag.get_opinions(product_name)
        
        if not opinions:
            logger.info(f"Ingesting fresh reviews for {product_name}...")
            ingestor = ReviewIngestor()
            ingestor.ingest_product(product_name)
            opinions = rag.get_opinions(product_name)
            
        if opinions:
            # Format nicely
            md = f"### Opinions on {product_name}\n"
            md += f"**Verdict**: {opinions.verdict} (Confidence: {opinions.confidence})\n\n"
            md += "**Pros**:\n" + "\n".join([f"- {p}" for p in opinions.pros]) + "\n\n"
            md += "**Cons**:\n" + "\n".join([f"- {c}" for c in opinions.cons])
            return md
            
        return "No sufficient user reviews found to form an opinion."
    except Exception as e:
        logger.error(f"Opinion RAG failed: {e}")
        return f"Could not analyze opinions: {e}"

def open_application(app_name: str) -> str:
    """Opens a Windows application by name."""
    logger.info(f"Tool Call: open_application('{app_name}')")
    sys_open_app(app_name)
    return f"Opening {app_name}..."

def set_system_volume(level: int) -> str:
    """Sets system volume (0-100)."""
    logger.info(f"Tool Call: set_system_volume({level})")
    if set_volume(level):
        return f"Volume set to {level}%."
    return "Failed to set volume. Check logs."

def bring_window_to_front(title: str) -> str:
    """Focuses a specific window."""
    logger.info(f"Tool Call: bring_window_to_front('{title}')")
    if focus_window(title):
        return f"Focused window matching '{title}'."
    return f"Could not find or focus window '{title}'."

def system_lock() -> str:
    """Locks the workstation."""
    logger.info("Tool Call: system_lock()")
    lock_screen()
    return "Locking screen."

def minimize_windows() -> str:
    """Minimizes all windows."""
    logger.info("Tool Call: minimize_windows()")
    minimize_all()
    return "All windows minimized."

AVAILABLE_TOOLS = {
    "lookup_hardware": lookup_hardware,
    "lookup_detailed_specs": lookup_detailed_specs,
    "search_web": search_web,
    "get_live_price": get_live_price,
    "get_product_opinions": get_product_opinions,
    "set_reminder": set_reminder,
    "delete_reminder": delete_reminder,
    "get_active_reminders": get_active_reminders,
    "get_system_health": get_system_health,
    "open_application": open_application,
    "set_system_volume": set_system_volume,
    "system_lock": system_lock,
    "minimize_windows": minimize_windows,
    "bring_window_to_front": bring_window_to_front
}
