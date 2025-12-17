import pandas as pd
from difflib import get_close_matches
import os

# Adjust paths to where we downloaded them
DATA_DIR = r"d:\JARVIS\data\cpu_specs"
INTEL_CSV = os.path.join(DATA_DIR, "Intel.csv")
AMD_CSV = os.path.join(DATA_DIR, "AMD.csv")

class LaptopCPUBase:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, intel_path=INTEL_CSV, amd_path=AMD_CSV):
        self.db = []
        self.lookup = {}
        self.names = []
        
        # Load Data
        print("Loading CPU Registry...")
        try:
            self.intel = pd.read_csv(intel_path)
            self.amd = pd.read_csv(amd_path)
            self._process_intel()
            self._process_amd()
            
            self.lookup = {item['name'].lower(): item for item in self.db}
            self.names = list(self.lookup.keys())
            print(f"Loaded {len(self.db)} CPU models.")
            
        except Exception as e:
            print(f"Error loading CPU registry: {e}")

    def _process_intel(self):
        # CONFIRMED HEADERS: "CpuName", "TotalCores", "TotalThreads", "ProcessorBaseFrequency", "MaxTurboFrequency", "Cache"
        try:
            # Regex: Use non-capturing groups (?:...) to avoid warnings
            intel_mobile = self.intel[self.intel['CpuName'].str.contains(r'i\d-\d+(?:U|H|HX|P|G7)|Atom|Celeron N|Pentium N', regex=True, na=False)]
            
            for _, row in intel_mobile.iterrows():
                self.db.append({
                    "name": row['CpuName'],
                    "manufacturer": "Intel",
                    "cores": row.get('TotalCores', 'N/A'),
                    "threads": row.get('TotalThreads', 'N/A'),
                    "base_clock": row.get('ProcessorBaseFrequency', 'N/A'),
                    "boost_clock": row.get('MaxTurboFrequency', 'N/A'),
                    "cache": row.get('Cache', 'N/A'),
                    "tdp": row.get('TDP', 'N/A'),
                    "score": 0 
                })
        except Exception as e:
            print(f"Error processing Intel data: {e}")

    def _process_amd(self):
        try:
            # CONFIRMED HEADERS: "Model", "# of CPU Cores", "# of Threads", "Base Clock", "Max. Boost Clock", "L1 Cache"
            # Regex: Non-capturing group
            amd_mobile = self.amd[self.amd['Model'].str.contains(r'\d+(?:U|H|HS|HX)', regex=True, na=False)]
            
            for _, row in amd_mobile.iterrows():
                self.db.append({
                    "name": row['Model'],
                    "manufacturer": "AMD",
                    "cores": row.get('# of CPU Cores', 'N/A'),
                    "threads": row.get('# of Threads', 'N/A'),
                    "base_clock": row.get('Base Clock', 'N/A'),
                    "boost_clock": row.get('Max. Boost Clock', 'N/A'),
                    "cache": row.get('L1 Cache', 'N/A'), # L3 is often better but if L1 is what we have...
                    "score": 0 
                })
        except Exception as e:
            print(f"Error processing AMD data: {e}")

    def get_cpu(self, query):
        """Fuzzy search to find the CPU details"""
        if not self.names: return None
        
        # clean query
        q = query.lower().strip()
        
        # Try direct lookup
        if q in self.lookup:
            return self.lookup[q]
            
        # Try fuzzy
        matches = get_close_matches(q, self.names, n=1, cutoff=0.4)
        if matches:
            return self.lookup[matches[0]]
        return None

