import logging
import json
import contextlib
import io
import os
from tavily import TavilyClient
from dotenv import load_dotenv

# Load env to get API Key
load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Global Cache for Search Results
LAST_SEARCH_RESULTS = []
LAST_SEARCH_QUERY = ""

def search_web(query: str) -> str:
    """
    Searches the web using Tavily (AI-Optimized Search).
    Returns clean results with titles, URLs, and relevant content snippets.
    """
    global LAST_SEARCH_RESULTS, LAST_SEARCH_QUERY
    logger.info(f"Tool Call: search_web('{query}')")
    LAST_SEARCH_QUERY = query
    
    if not TAVILY_API_KEY:
        return "Error: TAVILY_API_KEY not found in .env. Please configure it."

    try:
        # Initialize client
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
        
        # Search with context optimization
        # search_depth="basic" is faster/cheaper, "advanced" is deeper
        response = tavily.search(query=query, search_depth="basic", max_results=7)
        results = response.get("results", [])
        
        if not results:
            LAST_SEARCH_RESULTS = []
            return "SYSTEM: No results found. DO NOT make up links."
        
        LAST_SEARCH_RESULTS = results
        summary = f"Web Search Results for '{query}' (Indices [1-{len(results)}]):\n"
        
        for i, r in enumerate(results, 1):
            summary += f"{i}. {r['title']}\n   URL: {r['url']}\n   Snippet: {r['content'][:200]}...\n\n"
            
        return summary
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return f"Error searching web with Tavily: {e}"

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


from assistant_app.adapters.system_control import (
    set_volume, lock_screen, minimize_all, open_app as sys_open_app, focus_window,
    control_media as sys_media, control_browser as sys_browser, read_clipboard as sys_read_clipboard, 
    set_power_mode as sys_power, get_installed_applications as sys_get_apps
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

# Global Cache for Search Results
LAST_SEARCH_RESULTS = []
LAST_SEARCH_QUERY = ""


def open_search_result(index: int) -> str:
    """
    Opens the URL of a previously found search result by its index (1-based).
    """
    global LAST_SEARCH_RESULTS, LAST_SEARCH_QUERY
    logger.info(f"Tool Call: open_search_result({index})")
    
    # Fallback: If cache is empty but we have a query, try to re-run search (Self-Healing)
    if not LAST_SEARCH_RESULTS and LAST_SEARCH_QUERY:
        logger.info(f"Cache miss. Re-running search for '{LAST_SEARCH_QUERY}'...")
        search_web(LAST_SEARCH_QUERY)
    
    if not LAST_SEARCH_RESULTS:
        return "No previous search results found. Please search for something first."
        
    try:
        # Convert 1-based index to 0-based
        idx = int(index) - 1
        
        if 0 <= idx < len(LAST_SEARCH_RESULTS):
            # Robust key access: Try 'href' (DDGS/Normalized) then 'url' (Tavily Raw) then 'link' (Google)
            item = LAST_SEARCH_RESULTS[idx]
            target_url = item.get('href') or item.get('url') or item.get('link')
            title = item.get('title', 'Unknown Page')
            
            if not target_url:
                 return f"Error: Result #{index} has no valid URL."

            control_browser("new_tab", query=target_url)
            return f"Opened result #{index}: {title} ({target_url})"
        else:
            return f"Index {index} is out of range. Please choose between 1 and {len(LAST_SEARCH_RESULTS)}."
            
    except ValueError:
        return "Invalid index provided. Please provide a number."
    except Exception as e:
        logger.error(f"Error opening search result: {e}")
        return f"Error opening result: {e}"

def get_live_price(product: str, category: str = "general", price_max: float = None) -> str:
    """
    Searches for LIVE PRICES and DEALS of products from real online retailers like Cdiscount, Amazon, LDLC.
    USE THIS for:
    - "search for a laptop", "find me a gaming PC", "laptop gamer"
    - "price of X", "how much is X", "deals on X"
    - "buy a laptop for 1000 euros", "laptop under 1500"
    - ANY product shopping or price-related query
    
    Category: 'gaming' (adds RTX logic), 'work', or 'general'.
    price_max: Maximum price in EUR (e.g. 1500 for "laptop under 1500 euros")
    Returns actual prices in EUR from French retailers.
    
    DO NOT use search_web for product searches - use this tool instead!
    """
    logger.info(f"Tool Call: get_live_price('{product}', category='{category}', price_max={price_max})")
    
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
        
        # Scoring System with detailed breakdown
        from assistant_app.domain.benchmarks import value_breakdown, match_cpu, match_gpu
        
        # Filter by price_max if provided
        if price_max:
            results = [p for p in results if (p.price or 0) <= price_max]
            if not results:
                return f"No laptops found under {price_max} €. Try a higher budget."
        
        # Calculate scores for all items
        scored_results = []
        for p in results:
            # Use description if available, else just title
            specs = getattr(p, "description", "") or ""
            breakdown = value_breakdown(p.title, specs, p.price or 9999.0)
            scored_results.append((p, breakdown))
            
        # Sort by Score (Best first)
        scored_results.sort(key=lambda x: x[1]["score"], reverse=True)
        
        # Build detailed output
        summary = f"**Top {min(10, len(results))} Laptops for '{product}' ({category})**\n"
        summary += "Ranked by Value Score (Performance ÷ Price):\n\n"
        
        for i, (p, b) in enumerate(scored_results[:10], 1):
            # Extract detected components
            cpu = match_cpu(p.title) or "Unknown CPU"
            gpu = match_gpu(p.title) or "Unknown GPU"
            
            # Format RAM tier
            ram_labels = {0: "8GB", 1: "16GB", 2: "32GB", 3: "64GB+"}
            ram = ram_labels.get(b["ram_tier"], "?GB")
            
            # Format display
            display = f"{b['hz']}Hz {b['panel'].upper()}" if b['panel'] else f"{b['hz']}Hz"
            if b['hz'] == 0:
                display = "Standard"
            
            # Format storage
            storage = f"{b['storage_gb']}GB SSD" if b['storage_gb'] > 0 else "SSD"
            
            summary += f"**{i}. {p.title[:60]}{'...' if len(p.title) > 60 else ''}**\n"
            summary += f"   • Price: **{p.price} €** | Score: **{b['score']:.2f}**\n"
            summary += f"   • CPU: {cpu} (pts: {b['cpu_raw']:.0f})\n"
            summary += f"   • GPU: {gpu} (pts: {b['gpu_raw']:.0f})\n"
            summary += f"   • RAM: {ram} | Display: {display} | Storage: {storage}\n"
            summary += f"   • Store: {p.store}\n\n"
        
        return summary

    except Exception as e:
        logger.error(f"Price search error: {e}")
        return f"Error searching prices: {e}"

def get_weather(city: str, country: str = "") -> str:
    """Get weather for a city."""
    from assistant_app.services.weather_service import get_weather_sync
    try:
        w = get_weather_sync(city, country or None)
        return f"Weather in {w['city']}, {w['country']}: {w['temp']}°C, {w['description']}. Humidity: {w['humidity']}%."
    except Exception as e:
        return f"Could not get weather for {city}: {e}"

def get_joke(category: str = "Any") -> str:
    """
    Fetches a joke from the JokeAPI.
    Categories: 'Any', 'Dark', 'Programming', 'Misc', 'Pun', 'Spooky', 'Christmas'.
    Use 'Dark' ONLY if the user explicitly asks for dark/nsfw/edgy jokes.
    """
    logger.info(f"Tool Call: get_joke('{category}')")
    import requests
    
    try:
        # Determine URL based on category request
        if category.lower() in ["dark", "nsfw", "dirty", "adult"]:
            # Unfiltered
            url = "https://v2.jokeapi.dev/joke/Dark?type=single"
        else:
            # Safe Mode (Default)
            url = "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit&type=single"
            
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            joke = data.get("joke", "I can't think of a joke right now.")
            return joke
        else:
            return "I tried to fetch a joke, but the internet didn't laugh back."
            
    except Exception as e:
        logger.error(f"Joke API failed: {e}")
        return "Why did the AI cross the road? To get to the other side... of the firewall. (Fallback Joke)"

def get_product_opinions(product_name: str) -> str:
    """
    Gets qualitative "Pros & Cons" by analyzing Reddit/YouTube reviews.
    Useful for: "Is the screen bright?", "Does it overheat?", "Reviews of X".
    """
    logger.info(f"Tool Call: get_product_opinions('{product_name}')")
    try:
        # Use simple file-based storage (avoids ChromaDB crashes)
        from assistant_app.services.simple_reviews import (
            get_reviews, ingest_reviews, analyze_reviews
        )
        
        # Check if we have reviews stored
        reviews = get_reviews(product_name)
        
        if not reviews:
            logger.info(f"Ingesting fresh reviews for {product_name}...")
            success = ingest_reviews(product_name)
            if success:
                reviews = get_reviews(product_name)
        
        if not reviews:
            return "No sufficient user reviews found to form an opinion."
        
        # Analyze reviews with LLM
        analysis = analyze_reviews(product_name, reviews)
        
        if analysis:
            md = f"### Opinions on {product_name}\n"
            md += f"**Verdict**: {analysis.get('verdict', 'N/A')}\n\n"
            pros = analysis.get('pros', [])
            cons = analysis.get('cons', [])
            md += "**Pros**:\n" + "\n".join([f"- {p}" for p in pros]) + "\n\n"
            md += "**Cons**:\n" + "\n".join([f"- {c}" for c in cons])
            return md
        
        # Fallback: just return raw review snippets
        return f"Found {len(reviews)} reviews for {product_name}. Sample: {reviews[0][:200]}..."
        
    except Exception as e:
        logger.error(f"Opinion analysis failed: {e}")
        return f"Could not analyze opinions: {e}"

def open_application(app_name: str) -> str:
    """Opens a Windows application by name."""
    logger.info(f"Tool Call: open_application('{app_name}')")
    sys_open_app(app_name)
    return f"Opening {app_name}..."

def list_installed_applications() -> str:
    """Lists all installed applications found in the Start Menu."""
    logger.info("Tool Call: list_installed_applications()")
    apps = sys_get_apps()
    if not apps:
        return "No applications found in the Start Menu."
    
    # Return a comma-separated list, limited to first 100 to avoid token overflow
    return f"Found {len(apps)} applications. Here are some potentially openable apps:\n" + ", ".join(apps)


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

def control_media(action: str) -> str:
    """Controls media (play, pause, next, mute)."""
    logger.info(f"Tool Call: control_media('{action}')")
    sys_media(action)
    return f"Media command '{action}' sent."

def control_browser(action: str, query: str = None) -> str:
    """Controls browser tabs."""
    logger.info(f"Tool Call: control_browser('{action}', query='{query}')")
    sys_browser(action, query=query)
    return f"Browser command '{action}' sent."

def get_clipboard_content() -> str:
    """Reads system clipboard."""
    logger.info("Tool Call: get_clipboard_content()")
    return sys_read_clipboard()

def set_power_plan(mode: str) -> str:
    """Sets system power plan."""
    logger.info(f"Tool Call: set_power_plan('{mode}')")
    return sys_power(mode)

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

def open_multiple_search_results(indices: list[int]) -> str:
    """
    Opens multiple search results at once.
    Example: [1, 2, 3] opens the first 3 links in new tabs.
    """
    logger.info(f"Tool Call: open_multiple_search_results({indices})")
    
    if not indices:
        return "No indices provided."
        
    results_opened = []
    errors = []
    
    for idx in indices:
        res = open_search_result(idx)
        if "Opened" in res:
            results_opened.append(f"#{idx}")
        else:
            errors.append(f"#{idx} ({res})")
            
    summary = f"Opened {len(results_opened)} links: {', '.join(results_opened)}."
    if errors:
        summary += f"\nErrors: {', '.join(errors)}"
        
    return summary


def close_multiple_tabs(indices: list[int] | str) -> str:
    """
    Closes multiple tabs by their indices.
    Pass "all" to close all tabs.
    """
    logger.info(f"Tool Call: close_multiple_tabs({indices})")
    
    # Handle "all" or "any" keywords
    if isinstance(indices, str):
        lower_indices = indices.lower().strip()
        if lower_indices in ["all", "any", "every", "everything"]:
            control_browser("close_all_tabs")
            return "Closed all tabs."
        
        # Robust parsing - handle comma, space, or mixed separators
        try:
            # Handle "[1, 2]", "1, 2", "1 2 5", "1,2,5"
            import re
            clean = re.sub(r'[\[\]\'\"]', '', indices)  # Remove brackets/quotes
            # Split on comma, space, or "and"
            parts = re.split(r'[,\s]+|and', clean)
            indices_list = [int(x.strip()) for x in parts if x.strip().isdigit()]
        except Exception as e:
            return f"Error parsing indices: {e}"
    elif isinstance(indices, list):
        indices_list = [int(x) for x in indices if str(x).isdigit()]
    else:
        return "Invalid format for indices."

    if not indices_list: return "No valid indices provided."
    
    # Sort descending so closing index 5 doesn't shift index 2
    sorted_indices = sorted(indices_list, reverse=True)
    
    results = []
    for idx in sorted_indices:
        control_browser("close_tab", query=str(idx))
        results.append(str(idx))
    
    return f"Closed tabs: {', '.join(results)}"


# --- NOTES IMPLEMENTATION ---
from assistant_app.services.memory import add_note_db, get_notes_db, delete_note_db, update_note_db, init_memory

# Ensure memory DB is initialized (creates table if new)
# We call this safely; commonly done at app startup, but safe to call here if main didn't
try:
    init_memory()
except Exception: pass

LAST_FETCHED_NOTES = []

def take_note(content: str) -> str:
    """Saves a new note."""
    logger.info(f"Tool Call: take_note('{content}')")
    res = add_note_db(content)
    return f"Note saved: '{content}'"

def list_notes() -> str:
    """Lists all saved notes."""
    global LAST_FETCHED_NOTES
    logger.info("Tool Call: list_notes()")
    notes = get_notes_db()
    LAST_FETCHED_NOTES = notes
    
    if not notes:
        return "You have no notes saved."
        
    summary = "Here are your notes:\n"
    for i, n in enumerate(notes, 1):
        summary += f"{i}. [{n['created_at']}] {n['content']}\n"
    return summary

def delete_note(index: int) -> str:
    """Deletes a note by its list index (1-based)."""
    global LAST_FETCHED_NOTES
    logger.info(f"Tool Call: delete_note({index})")
    
    # Refresh cache to be safe, or used cached. 
    # Better to use cached to ensure index matches what user saw.
    if not LAST_FETCHED_NOTES:
        # Try to fetch if empty
        LAST_FETCHED_NOTES = get_notes_db()
        
    if not LAST_FETCHED_NOTES:
        return "No notes found to delete."
        
    try:
        idx = int(index) - 1
        if 0 <= idx < len(LAST_FETCHED_NOTES):
            note = LAST_FETCHED_NOTES[idx]
            if delete_note_db(note['id']):
                # Remove from local cache to keep sync
                LAST_FETCHED_NOTES.pop(idx)
                return f"Deleted note #{index}: '{note['content']}'"
            else:
                return "Failed to delete note from database."
        else:
            return f"Index {index} out of range (1-{len(LAST_FETCHED_NOTES)})."
    except Exception as e:
        return f"Error deleting note: {e}"

def update_note(index: int, new_content: str) -> str:
    """Updates a note by its list index."""
    global LAST_FETCHED_NOTES
    logger.info(f"Tool Call: update_note({index}, '{new_content}')")
    
    if not LAST_FETCHED_NOTES:
        LAST_FETCHED_NOTES = get_notes_db()
        
    if not LAST_FETCHED_NOTES:
         return "No notes found to update."
         
    try:
        idx = int(index) - 1
        if 0 <= idx < len(LAST_FETCHED_NOTES):
            note = LAST_FETCHED_NOTES[idx]
            if update_note_db(note['id'], new_content):
                 return f"Updated note #{index} to: '{new_content}'"
            else:
                 return "Failed to update note in database."
        else:
             return f"Index {index} out of range."
    except Exception as e:
         return f"Error updating note: {e}"


# --- MOVIES WATCHED IMPLEMENTATION ---
from assistant_app.services.movies_seen import all_seen, mark_seen, unmark_seen, is_seen_map

def get_movies_watched() -> str:
    """
    Returns all movies the user has marked as watched.
    Use this when user asks 'what movies have I watched', 'movies I've seen', 'my watched list'.
    """
    logger.info("Tool Call: get_movies_watched()")
    try:
        movies = all_seen()
        if not movies:
            return "You haven't marked any movies as watched yet."
        
        summary = f"You have watched {len(movies)} movies:\n"
        for m in movies[:10]:  # Show last 10
            summary += f"- {m.title} ({m.year})\n"
        
        if len(movies) > 10:
            summary += f"...and {len(movies) - 10} more."
        
        return summary
    except Exception as e:
        logger.error(f"Movies watched error: {e}")
        return f"Error getting watched movies: {e}"

def add_movie_watched(title: str, year: str = "", tmdb_id: str = "", imdb_id: str = "") -> str:
    """
    Marks a movie as watched. 
    Use this when user says 'I watched X', 'mark X as seen', 'add X to watched'.
    """
    logger.info(f"Tool Call: add_movie_watched('{title}', '{year}')")
    try:
        # Generate IDs if not provided
        if not tmdb_id:
            tmdb_id = f"manual_{hash(title) % 100000}"
        if not imdb_id:
            imdb_id = f"tt{hash(title) % 10000000:07d}"
        
        if mark_seen(tmdb_id, imdb_id, title, year):
            return f"Marked '{title}' ({year}) as watched."
        else:
            return f"'{title}' was already in your watched list."
    except Exception as e:
        logger.error(f"Mark movie error: {e}")
        return f"Error marking movie as watched: {e}"

def remove_movie_watched(title: str) -> str:
    """
    Removes a movie from the watched list.
    Use when user says 'remove X from watched', 'unmark X'.
    """
    logger.info(f"Tool Call: remove_movie_watched('{title}')")
    try:
        movies = all_seen()
        # Find by partial title match
        found = None
        for m in movies:
            if title.lower() in m.title.lower():
                found = m
                break
        
        if found and unmark_seen(found.imdb_id):
            return f"Removed '{found.title}' from your watched list."
        return f"Could not find '{title}' in your watched list."
    except Exception as e:
        logger.error(f"Remove movie error: {e}")
        return f"Error removing movie: {e}"


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
    "list_installed_applications": list_installed_applications,
    "set_system_volume": set_system_volume,
    "system_lock": system_lock,
    "minimize_windows": minimize_windows,
    "bring_window_to_front": bring_window_to_front,
    "control_media": control_media,
    "control_browser": control_browser,
    "read_clipboard": get_clipboard_content,
    "set_power_plan": set_power_plan,
    "open_search_result": open_search_result,
    "open_multiple_search_results": open_multiple_search_results,
    "take_note": take_note,
    "list_notes": list_notes,
    "delete_note": delete_note,
    "update_note": update_note,
    "close_multiple_tabs": close_multiple_tabs,
    # Movies watched tools
    "get_movies_watched": get_movies_watched,
    "add_movie_watched": add_movie_watched,
    "remove_movie_watched": remove_movie_watched,
    "get_weather": get_weather,
    "get_joke": get_joke,
}

