import re
from assistant_app.domain.benchmarks import match_gpu  

_PRICE_TOKEN = re.compile(
    r'\d(?:[\d\u00A0\u202F ]{0,6})(?:[.,]\d{1,2})?\s*€',
    re.I
)

def normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()

def parse_price_eur(text: str) -> float | None:
    if not text:
        return None
    # normalize whitespace
    t = (text.replace('\u202f', ' ')
             .replace('\u00a0', ' ')
             .replace('\xa0',  ' '))
    prices = []
    for m in _PRICE_TOKEN.finditer(t):
        token = m.group(0)                # ← always exists
        token = (token.replace('€', '')
                      .replace(' ', '')
                      .replace('\u202f', '')
                      .replace('\u00a0', '')
                      .replace('\xa0', ''))
        token = token.replace(',', '.')   # decimal
        try:
            prices.append(float(token))
        except ValueError:
            pass
    return min(prices) if prices else None

def extract_gpu(text: str) -> str | None:
    # rely on the same regex rules used by benchmarks
    return match_gpu(normalize_text(text))

# Keep these if other callers use them, otherwise you can delete:
def parse_ram_gb(text: str) -> int:
    m = re.search(r"(\d{2,3})\s*(?:go?|gb)\b", normalize_text(text))
    return int(m.group(1)) if m else 0

def parse_cpu_tier(text: str) -> int:
    t = normalize_text(text)
    if re.search(r"\bi9\b|\b13900|\b14900|\b15900|\bryzen\s*9\b", t): return 3
    if re.search(r"\bi7\b|\b13700|\b14700|\b15700|\bryzen\s*7\b", t): return 2
    if re.search(r"\bi5\b|\b13500|\b14500|\b15500|\bryzen\s*5\b", t): return 1
    return 0
