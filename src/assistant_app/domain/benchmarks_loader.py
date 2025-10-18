# assistant_app/domain/benchmarks_loader.py
from __future__ import annotations
import json, pathlib, re, time, random
from typing import Dict, Iterable, Optional
import requests
from bs4 import BeautifulSoup
from assistant_app.domain.benchmarks import _norm, CPU_CACHE_PATH, GPU_CACHE_PATH

# Conservative desktop headers + small jitter to reduce bot flags
BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

PASSMARK_URL = "https://www.cpubenchmark.net/laptop.html"
GPU_MEGA_URL = "https://www.videocardbenchmark.net/GPU_mega_page.html"
CPU_MEGA_URL = "https://www.cpubenchmark.net/CPU_mega_page.html"


FALLBACK_CPU_RANKS: Dict[str, float] = {

    "i9-14900hx": 89, "i7-14700hx": 83, "i7-14700h": 71,
    "i9-13900hx": 79, "i9-13900h": 73, "i7-13700hx": 71, "i7-13700h": 67,
    "i7-13650hx": 67, "i7-13620h": 59, "i5-13500h": 56, "i5-13420h": 50,
    "ultra 9 185h": 76, "ultra 7 155h": 69, "ultra 5 125h": 57,
    "ryzen 9 7945hx": 92, "ryzen 7 7845hx": 79, "ryzen 9 7940hs": 77, "ryzen 7 7840hs": 71,
    "ryzen 7 8845hs": 75, "ryzen 7 8840hs": 73, "ryzen 7 7735hs": 59, "ryzen 5 7535hs": 53,
    "i9-12900hx": 71, "i9-12900h": 67, "i7-12800h": 63, "i7-12700h": 59, "i7-12650h": 54, "i5-12500h": 50,
    "ryzen 9 6900hx": 62, "ryzen 7 6800h": 57, "ryzen 5 6600h": 47,
}

def _get(url: str, *, tries: int = 3) -> requests.Response | None:
    for i in range(tries):
        try:
            hdrs = dict(BASE_HEADERS)
            # tiny jitter in header to look less botty
            if i:
                hdrs["User-Agent"] = hdrs["User-Agent"].replace("Chrome/124.0", f"Chrome/124.{random.randint(1,9)}")
            r = requests.get(url, headers=hdrs, timeout=30)
            if r.status_code == 200:
                return r
        except Exception:
            pass
        time.sleep(1.0 + 0.3 * i)
    return None

def _extract_cpu_key(text: str) -> Optional[str]:
    t = _norm(text)
    m = re.search(r"(ultra[-\s]?[579][-\s]?\d{3}h)\b", t)
    if m: return _norm(m.group(1).replace(" -", "-").replace("  ", " "))
    m = re.search(r"(i[579])[-\s]?(\d{4,5})(h|hx)\b", t)
    if m: return f"{m.group(1)}-{m.group(2)}{m.group(3)}".lower()
    m = re.search(r"ryzen\s*([3579])[-\s]?(\d{3,4}0)(hs|hx|h|u)\b(?:\s*pro)?", t, re.I)
    if m: return f"amd ryzen {m.group(1)} {m.group(2)}{m.group(3)}"
    m = re.search(r"ryzen\s*([3579])[-\s]?(\d{2,4})(h|hs|hx|u)?\b", t, re.I)
    if m:
        suf = m.group(3) or ""
        return f"amd ryzen {m.group(1)} {m.group(2)}{suf}".strip()
    m = re.search(r"ryzen\s*([3579])\s*ai\s*(hx|h|u)?\s*(\d{3})\b", t, re.I)
    if m:
        tier, suf, num = m.group(1), (m.group(2) or ""), m.group(3)
        return f"amd ryzen ai {tier} {suf} {num}".strip()
    return None

def _find_cpu_mega_table(soup: BeautifulSoup):
    """
    Find the big 'CPU Mega List' table (columns include 'CPU Name', 'CPU Mark').
    Meant to work against 'Webpage, Complete' saves.
    """
    for table in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
        if not headers:
            first = table.find("tr")
            if first:
                headers = [c.get_text(" ", strip=True).lower()
                           for c in first.find_all(["th", "td"])]
        if headers and ("cpu name" in " ".join(headers)) and any("cpu mark" in h for h in headers):
            return table, headers
    return None, []

def _find_gpu_table(soup: BeautifulSoup):
    """
    Find the big GPU table (columns include 'Videocard Name' and 'G3D Mark').
    Works against 'Webpage, Complete' saves.
    """
    for table in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
        if not headers:
            first = table.find("tr")
            if first:
                headers = [c.get_text(" ", strip=True).lower() for c in first.find_all(["th","td"])]
        if headers and ("videocard name" in " ".join(headers)) and any("g3d" in h for h in headers):
            return table, headers
    return None, []

def _extract_cpu_mega_from_soup(soup: BeautifulSoup) -> Dict[str, float]:
    """
    Parse the PassMark CPU Mega List from a *local* HTML file.
    Keep only laptop parts (Category contains 'laptop').
    Normalize CPU Mark so the highest mark on the page becomes 100.0.
    """
    table, headers = _find_cpu_mega_table(soup)
    if not table:
        return {}

    # column indexes we care about
    name_idx = mark_idx = cat_idx = None
    for i, h in enumerate(headers):
        if "cpu name" in h:
            name_idx = i
        elif "cpu mark" in h:
            mark_idx = i
        elif "category" in h:
            cat_idx = i

    if name_idx is None or mark_idx is None:
        return {}

    rows: list[tuple[str, float]] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if len(cells) <= max(name_idx, mark_idx):
            continue

        name = cells[name_idx].get_text(" ", strip=True)
        mark = _safe_float(cells[mark_idx].get_text(" ", strip=True))
        category = cells[cat_idx].get_text(" ", strip=True) if (cat_idx is not None and cat_idx < len(cells)) else ""

        if not name or mark is None:
            continue

        # filter to laptop only (e.g., "Laptop" or "Desktop, Laptop")
        if "laptop" not in _norm(category):
            continue

        nkey = _display_name_key(name)
        rows.append((nkey, float(mark)))

    if not rows:
        return {}

    top = max(v for _, v in rows)
    if top <= 0:
        return {}

    # normalize to 0..100 (top == 100.0)
    return {k: (v / top) * 100.0 for k, v in rows}

def _extract_gpu_from_soup(soup: BeautifulSoup) -> Dict[str, float]:
    """
    Parse the mega GPU page. We keep 'mobile' / laptop GPUs:
      - name contains 'laptop'  OR
      - 'category' column contains 'mobile'
    Score = PassMark G3D Mark, normalized to 0..100 by top value on the page.
    """
    table, headers = _find_gpu_table(soup)
    if not table:
        return {}

    # Column indexes we care about
    name_idx = None
    g3d_idx = None
    cat_idx = None
    for i, h in enumerate(headers):
        if "videocard" in h and "name" in h:
            name_idx = i
        elif "g3d" in h:
            g3d_idx = i
        elif "category" in h:
            cat_idx = i

    if name_idx is None or g3d_idx is None:
        return {}

    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if len(cells) <= max(name_idx, g3d_idx):
            continue
        name = cells[name_idx].get_text(" ", strip=True)
        g3d = _safe_float(cells[g3d_idx].get_text(" ", strip=True))
        category = cells[cat_idx].get_text(" ", strip=True) if (cat_idx is not None and cat_idx < len(cells)) else ""

        if not name or g3d is None:
            continue

        n = _norm(name.replace("™", "").replace("®", ""))
        c = _norm(category)

        # Keep laptop/mobile class only
        is_mobile = ("laptop" in n) or ("mobile" in c)
        if not is_mobile:
            continue

        rows.append((n, float(g3d)))

    if not rows:
        return {}

    top = max(v for _, v in rows)
    if top <= 0:
        return {}

    # Normalize 0..100
    return {name: (score / top) * 100.0 for name, score in rows}

def _safe_float(x: str) -> Optional[float]:
    x = (x or "").replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)", x)
    return float(m.group(1)) if m else None

def _display_name_key(text: str) -> str:
    # Keep *everything* but normalize whitespace/casing and strip trademark symbols
    t = _norm(text)
    t = t.replace("™", "").replace("®", "")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _rank_to_0_100(values):
    vmin, vmax = min(values), max(values)
    span = max(1e-9, (vmax - vmin))
    return [(v - vmin) * 100.0 / span for v in values]


def _find_passmark_table(soup: BeautifulSoup):
    for table in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
        if not headers:
            first = table.find("tr")
            if first:
                headers = [c.get_text(" ", strip=True).lower() for c in first.find_all(["th","td"])]
        if any("cpu mark" in h for h in headers):
            return table
    return None

def _extract_passmark_from_soup(soup: BeautifulSoup) -> Dict[str, float]:
    raw: Dict[str, float] = {}

    for li in soup.select("li[id^='rk']"):
        name_el = li.select_one(".prdname")
        score_el = li.select_one(".count")
        if not name_el or not score_el:
            continue
        key = _display_name_key(name_el.get_text(" ", strip=True))
        score = _safe_float(score_el.get_text(" ", strip=True))
        if key and score is not None:
            raw[key] = float(score)

    if not raw:
        table = _find_passmark_table(soup) 
        if table:
            for tr in table.find_all("tr"):
                cells = tr.find_all(["td", "th"])
                if len(cells) < 2:
                    continue
                key = _display_name_key(cells[0].get_text(" ", strip=True))
                score = None
                for td in cells[1:]:
                    score = _safe_float(td.get_text(" ", strip=True))
                    if score is not None:
                        break
                if key and score is not None:
                    raw[key] = float(score)

    if not raw:
        return {}

    top = max(raw.values())
    return {k: (v / top) * 100.0 for k, v in raw.items()} if top > 0 else {}

def fetch_gpu_from_file(html_path: pathlib.Path) -> Dict[str, float]:
    """
    Load a *locally saved* PassMark GPU mega page (Webpage, Complete or HTML only).
    """
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")
    return _extract_gpu_from_soup(soup)

def refresh_gpu_cache(write_path: pathlib.Path = GPU_CACHE_PATH,
                      gpu_html_path: Optional[str] = None) -> pathlib.Path:
    """
    Build the GPU cache from a *local* mega page HTML file.
    (No live fetch here by design.)
    """
    if not gpu_html_path:
        raise RuntimeError("Please pass --from-html with a saved GPU mega page (HTML).")

    ranks = fetch_gpu_from_file(pathlib.Path(gpu_html_path))
    if not ranks:
        raise RuntimeError("No GPU data could be parsed from the provided HTML.")

    write_path.parent.mkdir(parents=True, exist_ok=True)
    with open(write_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "updated_at": int(time.time()),
                "source": {"passmark_gpu_mega": GPU_MEGA_URL},
                "ranks": ranks,
            },
            f, ensure_ascii=False, indent=2
        )
    return write_path

def fetch_passmark() -> Dict[str, float]:
    try:
        r = requests.get(PASSMARK_URL, headers=BASE_HEADERS, timeout=30)
        r.raise_for_status()
    except Exception:
        return {}
    soup = BeautifulSoup(r.text, "lxml")
    return _extract_passmark_from_soup(soup)

def fetch_cpu_mega_from_file(html_path: pathlib.Path) -> Dict[str, float]:
    """
    Load a *locally saved* PassMark CPU Mega List (Webpage, Complete or HTML only).
    """
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")
    return _extract_cpu_mega_from_soup(soup)

def fetch_passmark_from_file(html_path: pathlib.Path) -> Dict[str, float]:
    """
    Load a *locally saved* PassMark page (Webpage, Complete or HTML only) and parse it.
    """
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")
    return _extract_passmark_from_soup(soup)

def refresh_cpu_cache(write_path: pathlib.Path = CPU_CACHE_PATH,
                      passmark_html_path: Optional[str] = None) -> pathlib.Path:
    """
    Build the CPU cache from a *local* PassMark CPU Mega List HTML file.
    (No live fetch; pass --from-html.)
    """
    if not passmark_html_path:
        raise RuntimeError("Please pass --from-html with a saved CPU Mega List page (HTML).")

    ranks = fetch_cpu_mega_from_file(pathlib.Path(passmark_html_path))

    # As a safety net, fall back to your small hardcoded table if parsing fails
    if not ranks:
        ranks = dict(FALLBACK_CPU_RANKS)

    if not ranks:
        raise RuntimeError("No CPU data could be parsed from the provided HTML.")

    write_path.parent.mkdir(parents=True, exist_ok=True)
    with open(write_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "updated_at": int(time.time()),
                "source": {"passmark_cpu_mega": CPU_MEGA_URL},
                "ranks": ranks,
            },
            f, ensure_ascii=False, indent=2
        )
    return write_path