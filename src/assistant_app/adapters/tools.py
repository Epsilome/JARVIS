import logging
import json
from duckduckgo_search import DDGS
from assistant_app.domain.benchmarks import get_cpu_specs, get_gpu_specs, get_cached_specs, save_cached_specs
from assistant_app.services.prices import search_all
from assistant_app.adapters.scrapers.specs import search_specs

logger = logging.getLogger(__name__)

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
        return f"Found CPU: {cpu['name']}\nMark: {cpu['mark']}\nRank: {cpu['rank']}\nPrice: ${cpu['price']}"
    
    # Try GPU
    gpu = get_gpu_specs(query)
    if gpu:
        return f"Found GPU: {gpu['name']}\nMark: {gpu['mark']}\nRank: {gpu['rank']}\nPrice: ${gpu['price']}"
    
    return f"No hardware found matching '{query}' in the database."

def lookup_detailed_specs(product_name: str) -> str:
    """
    Looks up detailed specifications (VRAM, TDP, Cores, etc.) from dbgpu or web/cache.
    Use this for technical questions like "TDP of RTX 4090" or "How much VRAM".
    """
    logger.info(f"Tool Call: lookup_detailed_specs('{product_name}')")
    
    # 1. Try DBGPU (Fastest, Local, Accurate for GPUs)
    try:
        from dbgpu.src import DBGPU
        import contextlib
        import io
        
        # Suppress "GPU not found" noise for CPU queries
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                db = DBGPU()
                gpu_data = db.get_gpu(product_name)
            except:
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
        from assistant_app.domain.cpu_registry import LaptopCPUBase
        cpu_reg = LaptopCPUBase.get_instance()
        cpu_data = cpu_reg.get_cpu(product_name)
        if cpu_data:
            return f"Specs for {product_name} (Source: CPU Registry):\n{json.dumps(cpu_data, indent=2)}"
    except Exception as e:
        logger.warning(f"CPU Registry lookup failed: {e}")

    # 3. Check Local Cache (for non-GPU items or previously scraped stuff)
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

def get_live_price(product: str) -> str:
    """
    Searches for live prices of a product from online retailers.
    Useful for "How much is X?" or "Price of Y".
    """
    logger.info(f"Tool Call: get_live_price('{product}')")
    try:
        results = search_all(product, country_hint="FR") # Default to FR as per user context
        if not results:
            return "No live prices found."
        
        # Sort by price
        results.sort(key=lambda x: x.price or float('inf'))
        
        summary = f"Found {len(results)} deals for '{product}':\n"
        for p in results[:5]:
            summary += f"- {p.title}: {p.price} € ({p.store})\n"
        return summary
    except Exception as e:
        logger.error(f"Price search error: {e}")
        return f"Error searching prices: {e}"

AVAILABLE_TOOLS = {
    "lookup_hardware": lookup_hardware,
    "lookup_detailed_specs": lookup_detailed_specs,
    "search_web": search_web,
    "get_live_price": get_live_price
}
