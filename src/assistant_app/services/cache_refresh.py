"""
Scheduled Cache Refresh Job

Runs daily to pre-scrape common laptop queries, so users get instant results
when they first open the Laptops tab each day.
"""
import logging
from assistant_app.interfaces.scheduler.scheduler import scheduler
from assistant_app.services.prices import search_products
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Queries to pre-cache daily
DAILY_CACHE_QUERIES = [
    ("pc portable gamer rtx", "gaming"),
    ("pc portable professionnel", "work"),
    ("pc portable", "general"),
]

def refresh_laptop_cache():
    """Pre-scrape common laptop searches to warm up the cache."""
    logger.info("Starting daily laptop cache refresh...")
    
    for query, category in DAILY_CACHE_QUERIES:
        try:
            logger.info(f"Pre-caching: {query} ({category})")
            results = search_products(query, category=category)
            logger.info(f"Cached {len(results)} results for {query}")
        except Exception as e:
            logger.error(f"Cache refresh failed for {query}: {e}")
    
    logger.info("Daily cache refresh complete.")

def register_cache_job():
    """Register the daily cache refresh job with the scheduler."""
    # Check if job already exists
    existing = scheduler.get_job("daily_cache_refresh")
    if existing:
        logger.info("Daily cache job already registered.")
        return
    
    # Run at 6:00 AM daily (when user is likely to wake up)
    trigger = CronTrigger(hour=6, minute=0)
    
    scheduler.add_job(
        refresh_laptop_cache,
        trigger=trigger,
        id="daily_cache_refresh",
        name="Daily Laptop Cache Refresh",
        replace_existing=True
    )
    logger.info("Registered daily cache refresh job (runs at 6:00 AM).")

# Auto-register when module is imported
try:
    register_cache_job()
except Exception as e:
    logger.warning(f"Could not register cache job: {e}")
