# apps/streamlit_gaming_rankings.py
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from assistant_app.domain.benchmarks import (
    _load_cpu_cache, _load_gpu_cache, match_cpu, match_gpu, _norm, value_breakdown
)
import numpy as np
import pandas as pd
import streamlit as st

GENERIC_PREFIX_TOKEN = re.compile(r"(?i)^(?:pc|portable|gamer|gaming|ordinateur|laptop|notebook)\s+")
STOPWORDS = {"pc", "portable", "gamer", "gaming", "ordinateur", "laptop", "notebook"}

def short_title(title: str) -> str:
    if not isinstance(title, str):
        return ""
    head = re.split(r"\s*\|\s*", title, maxsplit=1)[0]
    chunks = re.split(r"\s+[–—-]\s+", head)
    head = " ".join(chunks[:2]) if len(chunks) >= 2 else chunks[0]
    while True:
        new_head = GENERIC_PREFIX_TOKEN.sub("", head).strip()
        if new_head == head: break
        head = new_head
    toks = [t for t in head.split() if t]
    while toks and toks[0].lower() in STOPWORDS: toks.pop(0)
    head = " ".join(toks)
    head = re.sub(r"\s+", " ", head).strip()
    return (head[:32] + "…") if len(head) > 32 else head

# --- build ordinal ranks from cached PassMark tables --------------------------
cpu_cache = _load_cpu_cache()   # {normalized_name: score 0..100}
gpu_cache = _load_gpu_cache()   # {normalized_name: score 0..100}

# Convert 0..100 scores into ordinal ranks (1 = best) for each cache
def _to_rank_index(cache: dict[str, float]) -> dict[str, int]:
    ordered = sorted(cache.items(), key=lambda kv: kv[1], reverse=True)
    return {k: i + 1 for i, (k, _) in enumerate(ordered)}

cpu_rank_idx_map = _to_rank_index(cpu_cache)
gpu_rank_idx_map = _to_rank_index(gpu_cache)

# Find the *best matching* cache key for a given name using your match_* helpers
def _closest_cpu_key(name):
    if not isinstance(name, str) or not name.strip():
        return None
    key = _norm(match_cpu(name) or name)
    if key in cpu_cache:
        return key
    candidates = [(k, v) for k, v in cpu_cache.items() if (k in key or key in k)]
    return max(candidates, key=lambda kv: kv[1])[0] if candidates else None

def _closest_gpu_key(name):
    if not isinstance(name, str) or not name.strip():
        return None
    key = _norm(match_gpu(name) or name)
    if key in gpu_cache:
        return key
    candidates = [(k, v) for k, v in gpu_cache.items() if (k in key or key in k)]
    return max(candidates, key=lambda kv: kv[1])[0] if candidates else None

# --- Helper to get detailed scoring breakdown for the dataframe ---
def get_breakdown_cols(row):
    # Reconstruct the specs string used in main.py
    specs = row.get("specs")
    specs_text = ""
    if isinstance(specs, dict):
        tgp = specs.get("tgp_w")
        pairs = " ".join(f"{k}:{v}" for k, v in specs.items() if v)
        extra = f" TGP {tgp}W" if tgp else ""
        specs_text = (row["title"] + " " + pairs + extra).strip()
    else:
        specs_text = (row["title"] + " " + str(specs or "")).strip()

    bd = value_breakdown(row["title"], specs_text, row["price_eur"])
    
    return pd.Series({
        "cpu_raw": bd.get("cpu_raw", 0),
        "gpu_raw": bd.get("gpu_raw", 0),
        "ram_tier": bd.get("ram_tier", 0),
        "storage_gb": bd.get("storage_gb", 0),
        "disp_raw": bd.get("disp_raw", 0),
        "os_w": bd.get("os_w", 0),
    })
st.set_page_config(page_title="Gaming Laptop Rankings", layout="wide")

st.title("🎯 Gaming Laptop Rankings")
st.caption("Loaded from the JSON your CLI exported.")

# --- Load data (uploader or path input) ---------------------------------------
left, right = st.columns([2, 1])
with left:
    uploaded = st.file_uploader("Upload a JSON export from `prices-gaming`", type=["json"])
with right:
    default_path = st.text_input("...or paste a JSON file path", value="")

data = None
if uploaded is not None:
    data = json.load(uploaded)
elif default_path:
    p = Path(default_path)
    if p.exists():
        data = json.loads(Path(default_path).read_text(encoding="utf-8"))

if not data:
    st.info("Upload or select a JSON file to view rankings.")
    st.stop()

# --- Normalize to a DataFrame -------------------------------------------------
df = pd.json_normalize(data)

# Helpful computed columns
df["price"] = df["price_eur"]
df["brand"] = df["title"].str.extract(r"^(?P<brand>[A-Za-zÀ-ÿ0-9]+)", expand=True)
df["domain"] = df["url"].apply(lambda u: urlparse(u).netloc)

# --- Apply breakdown to get detailed columns ---
breakdown_df = df.apply(get_breakdown_cols, axis=1)
df = pd.concat([df, breakdown_df], axis=1)

# Filters
with st.sidebar:
    st.header("Filters")
    min_p, max_p = float(df["price"].min()), float(df["price"].max())
    price_range = st.slider("Price (€)", min_value=int(min_p), max_value=int(max_p),
                            value=(int(min_p), int(max_p)))
    brand_filter = st.multiselect("Brand", sorted(df["brand"].dropna().unique().tolist()))
    q = st.text_input("Search in title", "")

mask = (df["price"].between(price_range[0], price_range[1]))
if brand_filter:
    mask &= df["brand"].isin(brand_filter)
if q:
    mask &= df["title"].str.contains(q, case=False, na=False)
view = df.loc[mask].copy().sort_values("score", ascending=False)

# Map each laptop to ordinal CPU/GPU rank from cache (1 = best, bigger = worse)
view["cpu_key"] = view["specs.cpu"].apply(_closest_cpu_key)
view["gpu_key"] = view["specs.gpu"].apply(_closest_gpu_key)
view["cpu_rank_idx"] = view["cpu_key"].apply(lambda k: cpu_rank_idx_map.get(k) if k else None)
view["gpu_rank_idx"] = view["gpu_key"].apply(lambda k: gpu_rank_idx_map.get(k) if k else None)
view["short_title"] = view["title"].apply(short_title)

# Summary
st.subheader("Top results")
st.write(f"Showing **{len(view)}** of {len(df)} items. Sorted by `score` desc.")

# Table (interactive)
visible_cols = [
    "score", "price", "title", "url",
    "specs.cpu", "cpu_rank_idx",
    "specs.gpu", "gpu_rank_idx",
    "specs.tgp_w",
    "ram_tier", "storage_gb", "disp_raw", "os_w"
]
# Clean Table Display
st.dataframe(
    view[visible_cols].rename(columns={
        "specs.cpu": "cpu",
        "cpu_rank_idx": "C.Rank",
        "specs.gpu": "gpu",
        "gpu_rank_idx": "G.Rank",
        "specs.tgp_w": "TGP",
        "ram_tier": "RAM(T)",
        "storage_gb": "SSD(GB)",
        "disp_raw": "Scrn",
        "os_w": "OS"
    }),
    use_container_width=True,
    hide_index=True,
    column_config={
        "url": st.column_config.LinkColumn("link", display_text="open"),
        "score": st.column_config.NumberColumn("Score", format="%.3f"),
        "price": st.column_config.NumberColumn("Price", format="%d €"),
    },
)