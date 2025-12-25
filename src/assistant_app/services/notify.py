try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError as e:
    print(f"[NOTIFY] Failed to import plyer: {e}")
    PLYER_AVAILABLE = False

from loguru import logger

def toast(title: str, msg: str):
    """
    Displays a desktop notification using Plyer.
    """
    # Always print to console/logs as well
    logger.info(f"[NOTIFY] {title}: {msg}")
    
    if PLYER_AVAILABLE:
        try:
            notification.notify(
                title=title,
                message=msg,
                app_name="JARVIS",
                timeout=10
            )
        except Exception as e:
            logger.error(f"[NOTIFY] Error showing toast: {e}")

