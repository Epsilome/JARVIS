import dateparser
import re

def parse_when(text: str):
    # Returns a naive datetime or None. For recurring, use simple keywords for now.
    dt = dateparser.parse(text)
    recurrence = None
    # crude recurring hints; replace with better rules later
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