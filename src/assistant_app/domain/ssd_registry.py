import pandas as pd
from difflib import get_close_matches
import os

# Path to the specific CSV
SSD_CSV_PATH = r"d:\JARVIS\data\ssd_specs\Copy of SSDs - Master List.csv"

class SSDRegistry:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, csv_path=SSD_CSV_PATH):
        self.db = []
        self.lookup = {}
        self.names = []
        self._load_data(csv_path)
    
    def _load_data(self, csv_path):
        if not os.path.exists(csv_path):
            print(f"SSD Registry Warning: File not found at {csv_path}")
            return
            
        try:
            # Use 'on_bad_lines' to skip messy rows if needed (or just let pandas handle it)
            df = pd.read_csv(csv_path)
            
            # Identify columns
            # Expected: Brand, Model, Interface, DRAM, NAND Type, "R/W (Up to, in MB/s)" ...
            
            # Simple normalization helper
            def clean_val(v):
                if pd.isna(v) or str(v).lower() == 'nan': return None
                return str(v).strip()

            for _, row in df.iterrows():
                brand = clean_val(row.get('Brand'))
                model = clean_val(row.get('Model'))
                
                if not brand or not model: continue
                
                # "Samsung 990 Pro" style name
                full_name = f"{brand} {model}"
                
                # Parse Stats
                dram = clean_val(row.get('DRAM'))
                nand = clean_val(row.get('NAND Type'))
                controller = clean_val(row.get('Controller'))
                
                # Speed is messy: "7450/6900" or just "7450"
                speed_str = clean_val(row.get('R/W (Up to, in MB/s)'))
                read_speed = "N/A"
                write_speed = "N/A"
                if speed_str:
                    parts = speed_str.split('/')
                    if len(parts) >= 1: read_speed = parts[0].strip()
                    if len(parts) >= 2: write_speed = parts[1].strip()

                entry = {
                    "name": full_name,
                    "brand": brand,
                    "model": model,
                    "interface": clean_val(row.get('Interface')),
                    "dram": dram,
                    "nand": nand,
                    "controller": controller,
                    "read_speed": read_speed,
                    "write_speed": write_speed,
                    "capacity": clean_val(row.get('Capacities')),
                    "category": clean_val(row.get('Categories'))
                }
                
                self.db.append(entry)
                self.lookup[full_name.lower()] = entry
                
            self.names = list(self.lookup.keys())
            print(f"Loaded {len(self.db)} SSDs from Master List.")
            
        except Exception as e:
            print(f"Error loading SSD Registry: {e}")

    def get_ssd(self, query):
        """Fuzzy search for SSD model"""
        if not self.names: return None
        
        q = query.lower().strip()
        
        # Exact match
        if q in self.lookup:
            return self.lookup[q]
            
        # Fuzzy match
        # Prefer longer matches to distinguish "SN850" vs "SN850X" correctly?
        # get_close_matches finds robust matches
        matches = get_close_matches(q, self.names, n=3, cutoff=0.8)
        if matches:
            # Pick best match?
            # 990 Pro match "Samsung 990 Pro" -> perfect
            return self.lookup[matches[0]]
            
        return None
