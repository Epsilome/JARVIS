try:
    from win11toast import toast as w11_toast
    TOAST_AVAILABLE = True
except ImportError as e:
    TOAST_AVAILABLE = False

from loguru import logger

def toast(title: str, msg: str):
    """
    Displays a desktop notification using win11toast.
    """
    # Always print to console/logs as well
    logger.info(f"[NOTIFY] {title}: {msg}")
    
    if TOAST_AVAILABLE:
        try:
            # win11toast basic usage
            w11_toast(title, msg)
        except Exception as e:
            logger.error(f"[NOTIFY] Error showing toast: {e}")

