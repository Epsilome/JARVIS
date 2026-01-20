# assistant_app/domain/benchmarks.py
from __future__ import annotations
import math
import re
import json
import pathlib
import sys
import contextlib
import io
import sqlite3
from typing import Optional, Dict

try:
    from assistant_app.domain.cpu_registry import LaptopCPUBase
except ImportError:
    LaptopCPUBase = None

try:
    from dbgpu.src import DBGPU
except ImportError:
    DBGPU = None

try:
    from assistant_app.domain.ssd_registry import SSDRegistry
except ImportError:
    SSDRegistry = None

try:
    from assistant_app.domain.ram_registry import RAMRegistry
except ImportError:
    RAMRegistry = None

CURRENT_FILE = pathlib.Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3] # Goes up to 'JARVIS'

# We explicitly look for the cache in the project root
DATA_DIR = PROJECT_ROOT / ".bench_cache"

# Fallback: check CWD if the above doesn't exist (e.g. if running flat)
if not DATA_DIR.exists():
    DATA_DIR = pathlib.Path(".bench_cache")

CPU_CACHE_PATH = DATA_DIR / "cpu_ranks.json"
GPU_CACHE_PATH = DATA_DIR / "gpu_ranks.json"

REFRESH_RE = re.compile(r"(\d{2,3})\s*hz", re.I)
STORAGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(tb|to|t|gb|go)\s*(?:ssd|nvme)?", re.I)
TGP_RE = re.compile(r"(\d{2,3})\s*W", re.I)
RAM_RE = re.compile(r"(\d{1,3})\s*(?:go|gb)\b", re.I)


# Lazy-loaded registries
_CPU_REGISTRY = None
_GPU_REGISTRY = None
_SSD_REGISTRY = None
_RAM_REGISTRY = None

def get_cpu_registry():
    global _CPU_REGISTRY
    if _CPU_REGISTRY is None:
        if LaptopCPUBase:
            try:
                _CPU_REGISTRY = LaptopCPUBase.get_instance()
            except ImportError:
                _CPU_REGISTRY = False
        else:
            _CPU_REGISTRY = False
    return _CPU_REGISTRY if _CPU_REGISTRY else None

def get_gpu_registry():
    global _GPU_REGISTRY
    if _GPU_REGISTRY is None:
        if DBGPU:
            try:
                # Suppress initialization noise
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    _GPU_REGISTRY = DBGPU()
            except ImportError:
                _GPU_REGISTRY = False
        else:
            _GPU_REGISTRY = False
    return _GPU_REGISTRY if _GPU_REGISTRY else None

def get_ssd_registry():
    global _SSD_REGISTRY
    if _SSD_REGISTRY is None:
        if SSDRegistry:
            try:
                _SSD_REGISTRY = SSDRegistry.get_instance()
            except ImportError:
                _SSD_REGISTRY = False
        else:
            _SSD_REGISTRY = False
    return _SSD_REGISTRY if _SSD_REGISTRY else None

def get_ram_registry():
    global _RAM_REGISTRY
    if _RAM_REGISTRY is None:
        if RAMRegistry:
            try:
                _RAM_REGISTRY = RAMRegistry.get_instance()
            except ImportError:
                _RAM_REGISTRY = False
        else:
            _RAM_REGISTRY = False
    return _RAM_REGISTRY if _RAM_REGISTRY else None

GPU_ALIASES = {
    # Normalize spacing/case and make sure we include “geforce”/“laptop gpu” where needed
    # 50-series
    "rtx 5090": "geforce rtx 5090 laptop gpu",
    "rtx 5080": "geforce rtx 5080 laptop gpu",
    "rtx 5070 ti": "geforce rtx 5070 ti laptop gpu",
    "rtx 5070": "geforce rtx 5070 laptop gpu",
    "rtx 5060": "geforce rtx 5060 laptop gpu",
    "rtx 5050": "geforce rtx 5050 laptop gpu",
    # 40-series
    "rtx 4090": "geforce rtx 4090 laptop gpu",
    "rtx 4080": "geforce rtx 4080 laptop gpu",
    "rtx 4070": "geforce rtx 4070 laptop gpu",
    "rtx 4060": "geforce rtx 4060 laptop gpu",
    "rtx 4050": "geforce rtx 4050 laptop gpu",
    # 30-series (mobile)
    "rtx 3080 ti": "geforce rtx 3080 ti laptop gpu",
    "rtx 3080": "geforce rtx 3080 laptop gpu",
    "rtx 3070 ti": "geforce rtx 3070 ti laptop gpu",
    "rtx 3070": "geforce rtx 3070 laptop gpu",
    "rtx 3060": "geforce rtx 3060 laptop gpu",
    "rtx 3050 ti": "geforce rtx 3050 ti laptop gpu",
    "rtx 3050 6gb": "geforce rtx 3050 6gb laptop gpu",
    "rtx 3050 4gb": "geforce rtx 3050 4gb laptop gpu",
    "rtx 3050 a": "geforce rtx 3050 a laptop gpu",

    # Ada workstation
    "rtx 5000 ada generation": "rtx 5000 ada generation laptop gpu",
    "rtx 4000 ada generation": "rtx 4000 ada generation laptop gpu",
    "rtx 3500 ada generation": "rtx 3500 ada generation laptop gpu",
    "rtx 3000 ada generation": "rtx 3000 ada generation laptop gpu",
    "rtx 2000 ada generation": "rtx 2000 ada generation laptop gpu",
    "rtx 1000 ada generation": "rtx 1000 ada generation laptop gpu",

    # Blackwell “RTX Pro”
    "rtx pro 3000 blackwell generation": "rtx pro 3000 blackwell generation laptop gpu",
    "rtx pro 2000 blackwell generation": "rtx pro 2000 blackwell generation laptop gpu",
    "rtx pro 1000 blackwell generation": "rtx pro 1000 blackwell generation laptop gpu",
    "rtx pro 500 blackwell generation":  "rtx pro 500 blackwell generation laptop gpu",

    # A-series workstation (include memory sizes if present in the title)
    "rtx a5500": "rtx a5500 laptop gpu",
    "rtx a5000": "rtx a5000 laptop gpu",
    "rtx a4500": "rtx a4500 laptop gpu",
    "rtx a4000": "rtx a4000 laptop gpu",
    "rtx a3000 12gb": "rtx a3000 12gb laptop gpu",
    "rtx a3000": "rtx a3000 laptop gpu",
    "rtx a2000 8gb": "rtx a2000 8gb laptop gpu",
    "rtx a2000": "rtx a2000 laptop gpu",
    "rtx a1000 6gb": "rtx a1000 6gb laptop gpu",
    "rtx a1000": "rtx a1000 laptop gpu",

    # AMD dGPUs
    "rx 7900m": "radeon rx 7900m",
    "rx 7800m": "radeon rx 7800m",
    "rx 7600m xt": "radeon rx 7600m xt",
    "rx 7600m": "radeon rx 7600m",
    "rx 7600s": "radeon rx 7600s",
    "rx 6850m xt": "radeon rx 6850m xt",
    "rx 6850m": "radeon rx 6850m",
    "rx 6800m": "radeon rx 6800m",
    "rx 6800s": "radeon rx 6800s",
    "rx 6700m": "radeon rx 6700m",
    "rx 6700s": "radeon rx 6700s",
    "rx 6650m xt": "radeon rx 6650m xt",
    "rx 6650m": "radeon rx 6650m",
    "rx 6600m": "radeon rx 6600m",
    "rx 6500m": "radeon rx 6500m",

    # Common iGPUs / Intel Arc
    "radeon 780m": "radeon 780m",
    "radeon 760m": "radeon 760m",
    "radeon 680m": "radeon 680m",
    "radeon 660m": "radeon 660m",
    "radeon 610m": "radeon 610m",
    "intel arc a770m": "intel arc a770m",
}

# ----------------------------
# Regex helpers
# ----------------------------
CPU_PATTERNS = [
    r"(?:intel(?:\(r\))?\s*core(?:™)?\s*)?(i[3579])[-\s]?(\d{4,5})(h|hx)\b",
    r"(?:intel(?:\(r\))?\s*core(?:™)?\s*)?(ultra)[-\s]?([579])[-\s]?(\d{3})h\b",
    r"(ryzen)[-\s]?([579])[-\s]?(\d{4,5})(hs|hx|h)\b",
    r"ryzen\s*[3579]\s*(\d{3,4})(hs|hx|h|u)?\b",
]

GPU_PATTERNS = [
    # GeForce RTX laptop (50/40/30 series; optional "ti"; optional "laptop/mobile gpu")
    r"(?:geforce\s+)?rtx\s*(50(?:90|80|70(?:\s*ti)?|60|50))(?:\s+laptop|\s+mobile)?\s+gpu",
    r"(?:geforce\s+)?rtx\s*(40(?:90|80|70|60|50))(?:\s+laptop|\s+mobile)?\s+gpu",
    r"(?:geforce\s+)?rtx\s*(30(?:80(?:\s*ti)?|70(?:\s*ti)?|60|50(?:\s*ti)?))(?:\s+laptop|\s+mobile)?\s+gpu",

    # Workstation Ada “RTX <N>000 Ada Generation Laptop GPU”
    r"rtx\s*(?:pro\s*)?(5000|4000|3500|3000|2000|1000)\s*ada\s*generation(?:\s+laptop)?\s+gpu",

    # Blackwell mobile “RTX Pro <N>000 Blackwell Generation Laptop GPU”
    r"rtx\s*pro\s*(3000|2000|1000|500)\s*blackwell\s*generation(?:\s+laptop)?\s+gpu",

    # Older workstation A-series (“RTX A5000 Laptop GPU”, “RTX A3000 12GB Laptop GPU”, etc.)
    r"rtx\s*a(5500|5000|4500|4000|3000|2000|1000)(?:\s*(\d+)\s*gb)?(?:\s+laptop)?\s+gpu",

    # Max-Q suffixes (Ampere/Turing mobile)
    r"(?:geforce\s+)?rtx\s*(20(?:80|70)|30(?:80|70))\s*(?:super\s*)?with\s*max[-\s]?q\s*design",
    r"(?:geforce\s+)?rtx\s*(20(?:80|70))\s*\(mobile\)",

    # AMD Radeon RX mobile
    r"radeon\s*rx\s*(7900m|7800m|7600m\s*xt|7600m|7600s|6850m\s*xt|6850m|6800m|6800s|6700m|6700s|6650m\s*xt|6650m|6600m|6500m)",

    # iGPUs we see a lot
    r"(radeon\s*(?:890m|880m|840m|780m|760m|680m|660m|610m))",
    r"(intel\s*arc\s*a770m)",

    # GTX/Quadro catch-alls (covers many legacy keys in your cache)
    r"(?:geforce\s*gtx\s*(?:3080|2080|2070|2060|1660\s*ti|1650(?:\s*ti)?|1080|1070|1060|980m|970m|965m|960m|950m|880m|870m|860m|850m|780m|775m|770m|765m|760m|680m|670m|660m|580m|560m|460m)(?:\s*with\s*max[-\s]?q\s*design|\s*\(mobile\))?)",
    r"(quadro\s*(?:rtx|p|t|m)\s*\w+(?:\s*with\s*max[-\s]?q\s*design)?)",
]


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()

def match_cpu(text: str) -> Optional[str]:

    n = _norm(text)
    
    # ---- Apple M-series -----------------------------------------------------
    # e.g., "Apple M4 Pro 12 Core", "Apple M3 8-Core"
    m = re.search(r"apple\s*m(\d)\s*(max|pro)?\s*(\d+)?\s*core?", n, re.I)
    if m:
        gen = m.group(1)
        tier = f" {m.group(2)}" if m.group(2) else ""
        cores = f" {m.group(3)} core" if m.group(3) else ""
        return f"apple m{gen}{tier}{cores}".strip()

    # ---- Qualcomm Snapdragon X ----------------------------------------------
    # e.g., "Snapdragon X Elite - X1E-84-100", "Snapdragon X Plus"
    m = re.search(r"(qualcomm\s*)?snapdragon\s*x\s*(elite|plus)\b(?:\s*-\s*([\w-]+))?", n, re.I)
    if m:
        tier = m.group(2)
        code = f" - {m.group(3)}" if m.group(3) else ""
        return f"qualcomm snapdragon x {tier}{code}".strip()

    # ---- Intel Core Ultra (H/HX/U/V) ----------------------------------------
    # e.g., "Intel Core Ultra 7 165H", "Ultra-9 285HX", "Ultra 7 256V"
    m = re.search(r"(?:intel\s*)?(?:core\s*)?ultra[-\s]?([579])[-\s]?(\d{3})(h|hx|u|v)\b", n, re.I)
    if m:
        return f"intel core ultra {m.group(1)} {m.group(2)}{m.group(3)}"

    # ---- New Intel Core branding (Core 5/7/9 … 210H/150U etc.) --------------
    # e.g., "Intel Core 5 210H", "Core 7 150U", "Core 9 270H"
    m = re.search(r"(?:intel\s*)?core\s*([3579])\s*(\d{3})(h|u)\b", n, re.I)
    if m:
        return f"intel core {m.group(1)} {m.group(2)}{m.group(3)}"

    # ---- Legacy Intel i5/i7/i9 H/HX -----------------------------------------
    m = re.search(r"(i[3579])[-\s]?(\d{4,5})(h|hx)\b", n, re.I)
    if m:
        return f"{m.group(1)}-{m.group(2)}{m.group(3)}".lower()

    # ---- Legacy Intel i3/i5/i7/i9 U/G/M suffix (laptops) --------------------
    # e.g., "i5-6200U", "i5 4300U", "i7-1065G7", "i5-8250U"
    m = re.search(r"(i[3579])[-\s]?(\d{4,5})(u|g\d?|m)\b", n, re.I)
    if m:
        return f"{m.group(1)}-{m.group(2)}{m.group(3)}".lower()

    # ---- Intel Celeron (work laptops/budget) --------------------------------
    # e.g., "Celeron N4000", "Celeron N5100", "Celeron J4125", "Celeron 1.10 GHz"
    m = re.search(r"celeron\s*([njg]?\d{4,5})\b", n, re.I)
    if m:
        return f"intel celeron {m.group(1)}".lower()
    # Fallback for just "Celeron" without model
    if "celeron" in n:
        return "intel celeron"

    # ---- Intel Pentium (budget laptops) -------------------------------------
    # e.g., "Pentium N5000", "Pentium Gold 7505"
    m = re.search(r"pentium\s*(?:gold|silver|n)?\s*(\d{4,5})\b", n, re.I)
    if m:
        return f"intel pentium {m.group(1)}".lower()
    if "pentium" in n:
        return "intel pentium"

# ---- AMD Ryzen AI family (FIXED) --------------------
    # Matches: "Ryzen AI 9 HX 370", "Ryzen AI 7 360", "Ryzen 7 AI 350" (some retailers flip it)
    # We made 'hx/h/u' optional, and 'max/pro' optional.
    # This handles the "Ryzen AI 7 360" case where '360' is the number and there is no suffix.
    m = re.search(
        r"ryzen\s*(?:ai\s*([3579])|([3579])\s*ai)\s*(?:(max\+?|max\+\s*pro|max\s*pro|pro)\s*)?(?:(hx|h|u)\s*)?(\d{3})\b",
        n, re.I
    )
    if m:
        # Group 1 or 2 is the tier (e.g. "7" or "9")
        tier = m.group(1) or m.group(2)
        flavor = m.group(3) or ""  # max/pro
        flavor = flavor.replace("+ ", "+").replace("  ", " ").strip()
        suffix = m.group(4) or ""  # hx/h/u (can be empty)
        num = m.group(5)           # 370, 360, 350
            
        pieces = ["amd ryzen ai"]
        if flavor: pieces.append(flavor)
        pieces.append(tier)
        if suffix: pieces.append(suffix)
        pieces.append(num)
        return " ".join(pieces).strip()

    # ---- AMD Ryzen classic (Catch 4-digit, optional suffix)
    m = re.search(r"ryzen\s*([3579])\s*(\d{4})(h|hs|hx|u|c)?\b", n, re.I)
    if m:
        return f"amd ryzen {m.group(1)} {m.group(2)}{m.group(3)}"

    # ---- AMD Ryzen 3-digit (e.g. Ryzen 7 260)
    m = re.search(r"ryzen\s*([3579])\s*(\d{3})(h|hs|hx|u)?\b", n, re.I)
    if m:
        suf = m.group(3) or ""
        return f"amd ryzen {m.group(1)} {m.group(2)}{suf}".strip()

    return None

def _canon_gpu_from_match(s: str) -> str:
    """Turn a raw regex match into the canonical string we want."""
    t = _norm(s)
    t = t.replace("geforce ", "")  # we’ll add it back where needed below
    # try alias direct hit first
    if t in GPU_ALIASES:
        return GPU_ALIASES[t]

    # series buckets
    m = re.match(r"rtx\s*(\d{4})(?:\s*ti)?", t)
    if m:
        base = f"rtx {m.group(1)}"
        if "ti" in t:
            base += " ti"
        # GeForce laptop GPUs
        return GPU_ALIASES.get(base, f"geforce {base} laptop gpu")

    # Ada/Blackwell/workstation fallbacks
    if "ada generation" in t:
        m = re.search(r"(?:rtx\s*)?(pro\s*)?(\d{4}|\d{3})\s*ada\s*generation", t)
        if m:
            base = ("rtx " + ("" if not m.group(1) else "pro ") + m.group(2) + " ada generation laptop gpu").replace("  ", " ")
            return base
    if "blackwell generation" in t and "rtx" in t:
        m = re.search(r"rtx\s*pro\s*(\d{3,4})\s*blackwell\s*generation", t)
        if m:
            return f"rtx pro {m.group(1)} blackwell generation laptop gpu"

    # A-series with optional size
    m = re.match(r"rtx\s*a(\d{4})(?:\s*(\d+)\s*gb)?", t)
    if m:
        size = f" {m.group(2)}gb" if m.group(2) else ""
        return f"rtx a{m.group(1)}{size} laptop gpu"

    # AMD RX mobile straight pass-through via aliases already covers most
    if t.startswith("radeon"):
        return GPU_ALIASES.get(t, t)

    # Intel Arc mobile
    if t.startswith("intel arc"):
        return "intel arc a770m"

    # Legacy GTX/Quadro: use the match as-is; containment will work with cache
    return t

def match_gpu(text: str) -> Optional[str]:
    n = _norm(text)
    # Try each pattern in order; return the most canonicalized name we can
    for pat in GPU_PATTERNS:
        m = re.search(pat, n, flags=re.I)
        if not m:
            continue
        # Use the whole match if available; otherwise join groups
        s = m.group(0)
        return _canon_gpu_from_match(s)

    # No regex hit; try a few quick alias probes (e.g., “4070” without “RTX”)
    quick = [
        (r"\b(50(?:90|80|70(?:\s*ti)?|60|50))\b", "rtx {}"),
        (r"\b(40(?:90|80|70|60|50))\b", "rtx {}"),
        (r"\b(30(?:80(?:\s*ti)?|70(?:\s*ti)?|60|50(?:\s*ti)?))\b", "rtx {}"),
        (r"\b(20(?:80(?:\s*ti)?|70(?:\s*ti)?|60|50(?:\s*ti)?))\b", "rtx {}"),
        (r"\b(7900m|7800m|7600m\s*xt|7600m|7600s|6850m\s*xt|6850m|6800m|6800s|6700m|6700s|6650m\s*xt|6650m|6600m|6500m)\b", "radeon rx {}"),
        (r"\b(780m|760m|680m|660m|610m)\b", "radeon {}"),
    ]
    for rx, fmt in quick:
        m = re.search(rx, n, flags=re.I)
        if m:
                val = m.group(1) if (m.lastindex and m.lastindex >= 1) else m.group(0)
                name = fmt.format(_norm(val)) if '{}' in fmt else fmt
                return _canon_gpu_from_match(name)

    return None

def parse_tgp_w(text: str) -> Optional[int]:
    m = TGP_RE.search(_norm(text))
    if not m: return None
    try: return int(m.group(1))
    except: return None

def parse_refresh_hz(text: str) -> Optional[int]:
    m = REFRESH_RE.search(_norm(text))
    if not m: return None
    try:
        hz = int(m.group(1))
        return hz if 60 <= hz <= 360 else None
    except:
        return None

def parse_panel_kind(text: str) -> str:
    t = _norm(text)
    if "oled" in t or "amoled" in t:
        return "oled"
    if "mini led" in t or "mini-led" in t or "miniled" in t:
        return "miniled"
    # treat IPS/VA as "ips" bucket for our purposes
    # Added WVA, UWVA, EWV, SVA, IGZO, Retina as IPS-like
    if any(x in t for x in ("ips", "va ", " va", "wva", "uwva", "ewv", "sva", "igzo", "retina")):
        return "ips"
    return ""

# Improved RAM regex: looks for digits followed by "go" or "gb"
def ram_tier_from_text(text: str) -> int:
    n = _norm(text)
    # Exclude VRAM (often listed near GPU) by trying to skip "rtx ... 8gb"
    # But simple approach first: find MAX memory mentioned that is a power of 2 usually
    best = 0
    for m in RAM_RE.finditer(n):
        val = int(m.group(1))
        # Sanity check: RAM is usually 8, 16, 24, 32, 48, 64
        if 8 <= val <= 128:
            best = max(best, val)
    
    if best >= 48: return 3
    if best >= 24: return 2
    if best >= 16: return 1
    return 0

# Improved storage regex to catch "512 Go", "1 To", "1TB"
def parse_storage_gb(text: str) -> int:
    best = 0
    for m in STORAGE_RE.finditer(_norm(text)):
        num = float(m.group(1))
        unit = m.group(2).lower()
        # If unit is small (GB/Go) use as is
        if unit.startswith(("g")):
            gb = int(num)
        else: # TB/To/T
            gb = int(num * 1024)
        
        # Filter out unlikely numbers (e.g. "16 go" is ram)
        # SSDs are usually 256, 512, 1000, 1024, 2000, 4000
        if gb >= 200 and gb < 16000:
            best = max(best, gb)
            
    # Fallback: look for "SSD <number>" without unit (common in some titles like "SSD 512")
    if best == 0:
        for m in re.finditer(r"ssd\s*(\d{3,4})\b", _norm(text)):
            gb = int(m.group(1))
            if gb >= 120 and gb < 16000:
                best = max(best, gb)
                
    return best

def parse_os_bonus(text: str) -> float:
    t = _norm(text)
    # very small nudge if Windows is included; 0 if "sans windows", FreeDOS, etc.
    if "sans windows" in t or "freedos" in t or "no os" in t:
        return 0.0
    # Added win10/w10/w11 variants
    if any(x in t for x in ("windows", "win11", "win10", "w11", "w10", "win 11", "win 10")):
        return 0.2
    return 0.0
# ----------------------------
# CPU table: seed + (optional) cached big table
# ----------------------------
# ----------------------------
# Database Queries
# ----------------------------


DB_PATH = PROJECT_ROOT / "assistant.db"

def _get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_cpu_specs(name: str) -> Optional[dict]:
    """Query the database for CPU specs."""
    conn = _get_db_connection()
    try:
        # Try exact match first
        row = conn.execute("SELECT * FROM cpu_benchmarks WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
        if not row:
            # Fetch all potentially relevant rows
            rows = conn.execute("SELECT * FROM cpu_benchmarks WHERE name LIKE ?", (f"%{name}%",)).fetchall()
            if rows:
                # Rank matches: prefer shortest name that contains the query (e.g. "Core i5" vs "Core i5-1234")
                # But careful: "i5" matches "i5-12400", "i5-13400".
                # Best approach: Use levenshtein or just sort by length if query is specific?
                # Let's use simple logic: Sort by length of name (ascending), then score (descending)
                rows = [dict(r) for r in rows]
                rows.sort(key=lambda x: (len(x['name']), -x['mark']))
                return rows[0]
            row = None
        
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def get_cached_specs(name: str) -> Optional[dict]:
    """Query the `hardware_specs` table."""
    conn = _get_db_connection()
    try:
        row = conn.execute("SELECT specs_json FROM hardware_specs WHERE name = ?", (name,)).fetchone()
        if row:
            return json.loads(row["specs_json"])
        return None
    finally:
        conn.close()

def save_cached_specs(name: str, specs: dict):
    """Save specs to the `hardware_specs` table."""
    conn = _get_db_connection()
    try:
        conn.execute("INSERT OR REPLACE INTO hardware_specs (name, specs_json) VALUES (?, ?)", 
                     (name, json.dumps(specs)))
        conn.commit()
    finally:
        conn.close()

def get_gpu_specs(name: str) -> Optional[dict]:
    """Query the database for GPU specs."""
    conn = _get_db_connection()
    try:
        # Try exact match first
        row = conn.execute("SELECT * FROM gpu_benchmarks WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
        if not row:
            # Fetch all candidates
            # "LIMIT 20" to avoid huge dumps if query is "RTX"
            rows = conn.execute("SELECT * FROM gpu_benchmarks WHERE name LIKE ? LIMIT 50", (f"%{name}%",)).fetchall()
            if rows:
                candidates = [dict(r) for r in rows]
                # Filter: The name MUST contain the query (SQLite LIKE is case insensitive but verify)
                # Sort:
                # 1. Exact phrase match usually best?
                # 2. Shortest length (e.g. "RTX 3080" < "RTX 3080 Ti")
                # 3. Higher mark (tie-breaker)
                candidates.sort(key=lambda x: (len(x['name']), -x['mark']))
                
                # Check if we have a "Ti" or "Super" mismatch issue
                # If query doesn't have "Ti", but result does, it should be penalized if a non-Ti version exists.
                # The length sort handles this: "RTX 3080" (len 8) < "RTX 3080 Ti" (len 11)
                
                return candidates[0]
            row = None
            
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def _cpu_base() -> Dict[str, float]:
    # Legacy support if needed, or remove
    return {}

def _gpu_cache() -> Dict[str, float]:
    # Legacy support if needed, or remove
    return {}

# ----------------------------
# Scoring
# ----------------------------
def cpu_score(cpu_name: str | None) -> float:
    if not cpu_name: return 0.0
    
    # Try normalized match first
    matched = match_cpu(cpu_name) or cpu_name
    
    # Query DB
    spec = get_cpu_specs(matched)
    if spec:
        return float(spec['mark'])
        
    return 0.0

def gpu_score(gpu_name: str | None, context_text: str | None = None) -> float:
    if not gpu_name: return 0.0
    
    matched = match_gpu(gpu_name) or gpu_name
    spec = get_gpu_specs(matched)
    
    if spec:
        base = float(spec['mark'])
        # TGP adjustment
        tgp = parse_tgp_w((context_text or "") + " " + (gpu_name or "")) or 115
        tgp = max(60, min(140, tgp))
        factor = 0.84 + (tgp - 60) * (0.28 / 80.0)
        return base * factor
        
    return 0.0

def value_score(title: str, specs_text: str, price_eur: float) -> float:
    """
    Priority: CPU > GPU (TGP-aware) > Display > RAM > SSD > OS (tiny).
    We build a raw score then divide by a price penalty.
    """
    base_text = (title + " " + (specs_text or "")).strip()

    # 1) Core performance
    c = cpu_score(base_text)         # 0..100
    g = gpu_score(base_text, base_text)  # 0..~115 after TGP factor
    
    # --- DEEP SPECS BONUS (New) ---
    # Give bonuses for VRAM and Core counts if available
    deep_bonus = 0.0
    
    # GPU VRAM Bonus
    # Heuristic: 8GB is the new standard. 6GB is bare minimum.
    # +5 pts for 8GB, +10 for 12GB+, +15 for 16GB+
    try:
        gpu_reg = get_gpu_registry()
        if gpu_reg:
            gpu_name = match_gpu(base_text)
            if gpu_name:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    spec = gpu_reg.get_gpu(gpu_name)
                
                if spec:
                    # VRAM
                    # Check 'memory_size_gb' or 'vram'
                    vram = getattr(spec, 'memory_size_gb', None) or getattr(spec, 'vram', None)
                    if vram:
                        # Parse regex if string "8 GB"
                        if isinstance(vram, str):
                            m_v = re.search(r"(\d+)", vram)
                            vram = int(m_v.group(1)) if m_v else 0
                        
                        if vram >= 16: deep_bonus += 15.0
                        elif vram >= 12: deep_bonus += 10.0
                        elif vram >= 8: deep_bonus += 5.0
                        elif vram < 6: deep_bonus -= 5.0 # Penalty for 4GB in 2024
    except Exception:
        pass # specific lookup failed, ignore
        
    # CPU Cores Bonus
    # Heuristic: 6 cores is min for gaming. 8 is good. 14+ (P+E) is great.
    try:
        cpu_reg = get_cpu_registry()
        if cpu_reg:
            cpu_name = match_cpu(base_text)
            if cpu_name:
                spec = cpu_reg.get_cpu(cpu_name)
                if spec:
                    cores = spec.get('cores')
                    # 'cores' might be "14" or "6" (int or str)
                    try:
                        if cores and str(cores).lower() != 'n/a':
                            ic = int(float(cores))
                            if ic >= 14: deep_bonus += 8.0
                            elif ic >= 10: deep_bonus += 5.0
                            elif ic >= 8: deep_bonus += 2.0
                            elif ic < 6: deep_bonus -= 5.0
                    except: pass
    except Exception:
        pass

    # 2) Display
    panel = parse_panel_kind(base_text)
    hz = parse_refresh_hz(base_text) or 0
    disp = 0.0
    if panel == "oled":
        disp += 1.0   # fast response time/contrast; excellent perceived motion & HDR for gaming
    elif panel == "miniled":
        disp += 0.7   # great HDR, decent response depending on panel
    elif panel == "ips":
        disp += 0.3   # baseline

    if hz >= 240:      # very smooth; competitive titles
        disp += 0.7
    elif hz >= 165:
        disp += 0.5
    elif hz >= 144:
        disp += 0.4
    elif hz >= 120:
        disp += 0.2

    # 3) Memory
    r_tier = ram_tier_from_text(base_text)  # 0/1/2/3 for ~8/16/32/64+

    # 4) Storage (very small – FPS unaffected; helps UX & game loads)
    s_gb = parse_storage_gb(base_text)
    if s_gb >= 2000:
        s_bonus = 0.5
    elif s_gb >= 1000:
        s_bonus = 0.35
    elif s_gb >= 512:
        s_bonus = 0.2
    elif s_gb >= 256:
        s_bonus = 0.1
    else:
        s_bonus = 0.0

    # 5) OS (tiny nudge)
    os_bonus = parse_os_bonus(base_text)  # 0.0 or 0.2

    # Weights — CPU most important, then GPU (with TGP), then Display, then RAM, then SSD, then OS
    c_w = 5.0 * (c / 100.0)
    g_w = 4.0 * (g / 100.0)       # was 5; now CPU > GPU as requested
    d_w = 1.5 * disp              # max ~1.5–1.7 typically
    r_w = 1.0 * r_tier            # 0..3
    s_w = s_bonus                 # 0..0.5
    o_w = os_bonus                # 0..0.2

    raw = c_w + g_w + d_w + r_w + s_w + o_w

    # price penalty: reward good value in ~900–1500€; harsher > 2000€
    pen = math.log(max(price_eur, 300.0), 1.7)
    return raw / pen

def value_breakdown(title: str, specs_text: str, price_eur: float) -> dict:
    base_text = (title + " " + (specs_text or "")).strip()
    c = cpu_score(base_text)
    g = gpu_score(base_text, base_text)
    panel = parse_panel_kind(base_text)
    hz = parse_refresh_hz(base_text) or 0
    disp = 0.0
    if panel == "oled": disp += 1.0
    elif panel == "miniled": disp += 0.7
    elif panel == "ips": disp += 0.3
    if hz >= 240: disp += 0.7
    elif hz >= 165: disp += 0.5
    elif hz >= 144: disp += 0.4
    elif hz >= 120: disp += 0.2
    r_tier = ram_tier_from_text(base_text)
    s_gb = parse_storage_gb(base_text)
    if s_gb >= 2000: s_bonus = 0.5
    elif s_gb >= 1000: s_bonus = 0.35
    elif s_gb >= 512: s_bonus = 0.2
    elif s_gb >= 256: s_bonus = 0.1
    else: s_bonus = 0.0
    o_w = parse_os_bonus(base_text)

    c_w = 5.0 * (c / 100.0)
    g_w = 4.0 * (g / 100.0)
    d_w = 1.5 * disp
    r_w = 1.0 * r_tier
    s_w = s_bonus
    raw = c_w + g_w + d_w + r_w + s_w + o_w

    pen = math.log(max(price_eur, 300.0), 1.7)
    return {
        "cpu_raw": c, "gpu_raw": g, "panel": panel, "hz": hz, "ram_tier": r_tier,
        "storage_gb": s_gb, "disp_raw": disp,
        "gpu_w": g_w, "cpu_w": c_w, "disp_w": d_w, "ram_w": r_w, "ssd_w": s_w, "os_w": o_w,
        "penalty": pen, "score": raw / pen
    }
    
def is_gpu_at_least_5060(gpu_name: str | None) -> bool:
    g = (match_gpu(gpu_name or "") or "").strip()
    if not g: return False
    if g.startswith("rtx 50"): return any(v in g for v in ("5070", "5060"))
    if g.startswith("rtx 40"): return any(v in g for v in ("4090", "4080", "4070"))
    return "4060 ti" in g

# --- Work/office-centric value score: CPU > Display > RAM > SSD > OS (+tiny GPU bonus)
def value_score_work(title: str, specs_text: str, price_eur: float) -> float:
    base_text = (title + " " + (specs_text or "")).strip()

    # Core perf (CPU first)
    c = cpu_score(base_text)                 # 0..100
    g = gpu_score(base_text, base_text)      # 0..~115, but tiny weight for office

    # Display (panel quality matters more than high refresh for office)
    panel = parse_panel_kind(base_text)
    hz = parse_refresh_hz(base_text) or 0
    disp = 0.0
    if panel == "oled":       disp += 1.0
    elif panel == "miniled":  disp += 0.8
    elif panel == "ips":      disp += 0.4
    # refresh is nice for smoothness/eye comfort, but low weight for office
    if   hz >= 240: disp += 0.3
    elif hz >= 165: disp += 0.25
    elif hz >= 144: disp += 0.2
    elif hz >= 120: disp += 0.15

    # Memory / storage / OS
    r_tier = ram_tier_from_text(base_text)  # 0/1/2/3 ≈ 8/16/32/64+
    s_gb = parse_storage_gb(base_text)
    if   s_gb >= 2000: s_bonus = 0.6
    elif s_gb >= 1000: s_bonus = 0.45
    elif s_gb >=  512: s_bonus = 0.25
    elif s_gb >=  256: s_bonus = 0.1
    else:              s_bonus = 0.0
    o_bonus = parse_os_bonus(base_text)  # 0.0 or 0.2

    # Weights (office): CPU > Display > RAM > SSD > OS ; tiny GPU bonus
    c_w = 6.0 * (c / 100.0)
    d_w = 1.8 * disp
    r_w = 1.2 * r_tier
    s_w = s_bonus
    o_w = o_bonus
    g_w = 0.5 * (g / 100.0)  # small nudge if a dGPU exists

    raw = c_w + d_w + r_w + s_w + o_w + g_w

    # Slightly stronger price pressure to surface cheaper office machines
    pen = math.log(max(price_eur, 250.0), 1.75)
    return raw / pen
