import pandas as pd
from difflib import get_close_matches
import os
import glob

RAM_DATA_DIR = r"d:\JARVIS\data\ram_specs"

class RAMRegistry:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, data_dir=RAM_DATA_DIR):
        self.db = []
        self.lookup = {}
        self.names = []
        self._load_data(data_dir)
    
    def _load_data(self, data_dir):
        if not os.path.exists(data_dir):
            print(f"RAM Registry Warning: Directory not found at {data_dir}")
            return
            
        csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
        
        for csv_path in csv_files:
            try:
                df = pd.read_csv(csv_path)
                # Headers: Memory Name, Latency (ns), Read Uncached (GB/s), Write (GB/s), Price (USD)
                
                for _, row in df.iterrows():
                    name = str(row.get('Memory Name', '')).strip()
                    if not name or name.lower() == 'nan': continue
                    
                    latency = row.get('Latency (ns)')
                    read_speed = row.get('Read Uncached (GB/s)')
                    write_speed = row.get('Write (GB/s)')
                    price = row.get('Price (USD)')
                    
                    # Determine type from filename (DDR4 vs DDR5)
                    ram_type = "Unknown"
                    if "DDR4" in os.path.basename(csv_path): ram_type = "DDR4"
                    elif "DDR5" in os.path.basename(csv_path): ram_type = "DDR5"

                    entry = {
                        "name": name,
                        "type": ram_type,
                        "latency_ns": latency,
                        "read_gb_s": read_speed,
                        "write_gb_s": write_speed,
                        "price": price
                    }
                    
                    self.db.append(entry)
                    # Normalize key for lookup
                    self.lookup[name.lower()] = entry
                    
            except Exception as e:
                print(f"Error loading RAM CSV {csv_path}: {e}")
                
        self.names = list(self.lookup.keys())
        print(f"Loaded {len(self.db)} RAM modules from {len(csv_files)} files.")

    def get_ram(self, query):
        """Fuzzy search for RAM model"""
        if not self.names: return None
        
        q = query.lower().strip()
        
        # Exact match
        if q in self.lookup:
            return self.lookup[q]
            
        # Fuzzy match
        matches = get_close_matches(q, self.names, n=1, cutoff=0.6)
        if matches:
            return self.lookup[matches[0]]
            
        return None
