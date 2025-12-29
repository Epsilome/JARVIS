import dateparser
import re
from datetime import datetime

def parse_when(text: str):
    # Fix "after X minutes" -> "in X minutes"
    text = re.sub(r'\bafter\s+(\d+)\s+', r'in \1 ', text, flags=re.IGNORECASE)
    
    # Force future preference
    dt = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime.now()})
    
    recurrence = None
    lower = text.lower()
    if "every" in lower or "each" in lower:
        recurrence = lower
    return dt, recurrence

def parse_every(s: str) -> dict | None:
    m = re.fullmatch(r"(\d+)\s*(m|h|d|w)", s.strip(), re.I)
    if not m: return None
    n, unit = int(m.group(1)), m.group(2).lower()
    return {"minutes": n} if unit=="m" else \
           {"hours": n} if unit=="h" else \
           {"days": n} if unit=="d" else {"weeks": n}