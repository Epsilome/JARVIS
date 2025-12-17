import sqlite3
import re
from bs4 import BeautifulSoup
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parents[3]
DB_PATH = PROJECT_ROOT / "assistant.db"
CPU_HTML = PROJECT_ROOT / "CPU_mega_page.html"
GPU_HTML = PROJECT_ROOT / "GPU_mega_page.html"

def init_db():
    """Initialize the database with tables."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # CPU Table
    c.execute('''CREATE TABLE IF NOT EXISTS cpu_benchmarks (
                    name TEXT PRIMARY KEY,
                    mark INTEGER,
                    rank INTEGER,
                    price REAL,
                    samples INTEGER
                )''')
    
    # GPU Table
    c.execute('''CREATE TABLE IF NOT EXISTS gpu_benchmarks (
                    name TEXT PRIMARY KEY,
                    mark INTEGER,
                    rank INTEGER,
                    price REAL,
                    samples INTEGER
                )''')

    # Deep Specs Cache Table (New)
    c.execute('''CREATE TABLE IF NOT EXISTS hardware_specs (
                    name TEXT PRIMARY KEY,
                    specs_json TEXT,  -- JSON blob of detailed specs
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    conn.commit()
    return conn

def parse_passmark_html(file_path: Path, mark_col_idx: int):
    """Parses a PassMark HTML file and returns a list of dicts."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    logger.info(f"Parsing {file_path}...")
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")

    rows = soup.find_all("tr")
    logger.info(f"Found {len(rows)} rows. Processing...")

    data = []
    for i, row in enumerate(rows):
        cols = row.find_all("td")
        if len(cols) < 3:
            continue
        
        try:
            # Col 1: Name
            name_text = cols[1].get_text(strip=True)
            
            # Skip header rows
            if "Name" in name_text or not name_text:
                continue

            # Mark column varies
            mark_text = cols[mark_col_idx].get_text(strip=True).replace(",", "")
            if not mark_text.isdigit():
                continue
            mark = int(mark_text)

            # Rank is usually next to mark or we ignore it
            rank = 0

            # Price - look for $ in any column
            price = 0.0
            for col in cols:
                txt = col.get_text(strip=True)
                if "$" in txt:
                    clean_price = txt.replace("$", "").replace(",", "").replace("*", "")
                    try:
                        price = float(clean_price)
                    except:
                        pass
            
            data.append({
                "name": name_text,
                "mark": mark,
                "rank": rank,
                "price": price,
                "samples": 0
            })
            
        except Exception as e:
            continue
            
    return data

def ingest_data():
    conn = init_db()
    c = conn.cursor()

    # Ingest CPUs (Mark is Col 3)
    cpus = parse_passmark_html(CPU_HTML, 3)
    logger.info(f"Found {len(cpus)} CPUs.")
    for cpu in cpus:
        c.execute('''INSERT OR REPLACE INTO cpu_benchmarks (name, mark, rank, price, samples)
                     VALUES (?, ?, ?, ?, ?)''', 
                     (cpu["name"], cpu["mark"], cpu["rank"], cpu["price"], cpu["samples"]))
    
    # Ingest GPUs (Mark is Col 2)
    gpus = parse_passmark_html(GPU_HTML, 2)
    logger.info(f"Found {len(gpus)} GPUs.")
    for gpu in gpus:
        c.execute('''INSERT OR REPLACE INTO gpu_benchmarks (name, mark, rank, price, samples)
                     VALUES (?, ?, ?, ?, ?)''', 
                     (gpu["name"], gpu["mark"], gpu["rank"], gpu["price"], gpu["samples"]))

    conn.commit()
    conn.close()
    logger.info("Ingestion complete.")

if __name__ == "__main__":
    ingest_data()
