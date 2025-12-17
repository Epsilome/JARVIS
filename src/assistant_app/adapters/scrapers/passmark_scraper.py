import requests
import time
import re
import datetime

class Scraper:
    def __init__(self, domain="www.cpubenchmark.net"):
        #parse arguments and get a list of items
        if not domain in ["www.videocardbenchmark.net", "www.cpubenchmark.net", "www.harddrivebenchmark.net"]:
            raise ValueError("Invaid domain given.")
        self.domain = domain
        self.url = {
            "www.cpubenchmark.net": "https://www.cpubenchmark.net/CPU_mega_page.html",
            "www.videocardbenchmark.net": "https://www.videocardbenchmark.net/GPU_mega_page.html",
            "www.harddrivebenchmark.net": "https://www.harddrivebenchmark.net/hdd-mega-page.html"
        }[domain]
        self.items = []
        # Lazy scrape or explicit? The user's code calls self.scrape() in init.
        self.scrape()
    
    #search through the list
    def search(self, query, limit=None):
        query_split = query.lower().split(" ")

        #get number of matches for each word in the search query
        results = []
        for item in self.items:
            name_split = item["name"].lower().split(" ")
            matches = list(set(name_split)&set(query_split))
            if len(matches) > 0:
                results.append((item, len(matches)))

        #sort to get the most relavent results on top
        results = sorted(results, key=lambda x: x[1], reverse=True)

        if limit != None:
            results = results[:limit]
        return results

    #get a single item based on its id
    def get_item(self, item_id):
        for item in self.items:
            if int(item["id"]) == int(item_id):
                return item
        return None

    #download and cache the data
    def scrape(self):
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "referrer": self.url,
            "x-requested-with": "XMLHttpRequest",
            "accept": "application/json, text/javascript, */*; q=0.01",
        }
        # First request to get cookies/session?
        try:
             r1 = session.get(self.url, headers=headers)
        except Exception as e:
            print(f"Scraper Error (Initial GET): {e}")

        url2 = f"https://{self.domain}/data/?_={str(int(time.time()*1000))}"
        try:
            r2 = session.get(url2, headers=headers)
            r2.raise_for_status()
            data = r2.json()
            # The JSON structure usually has "data" key, but sometimes it's direct list?
            # User code: self.items = r2.json()["data"]
            if "data" in data:
                self.items = data["data"]
            else:
                self.items = data
        except Exception as e:
            print(f"Scraper Error (Data Fetch): {e}")
            self.items = []
        
        return self.items

    #get every item in the database, sorted by a specific critiera
    def get_sorted_list(self, sort_by="rank", order="descending", limit=None, item_type=None):
        results = []
        if not self.items: return []

        #define types for the values so that we know how to sort them
        if self.domain == "www.cpubenchmark.net":
            item_types = {
                "cat": "string",
                "cores": "number",
                "cpuCount": "number",
                "cpumark": "number",
                "date": "date",
                "href": "string",
                "id": "number",
                "logicals": "number",
                "name": "string",
                "output": "bool",
                "powerPerf": "number",
                "price": "number",
                "rank": "number",
                "samples": "number",
                "socket": "string",
                "speed": "number",
                "tdp": "number",
                "thread": "number",
                "threadValue": "number",
                "turbo": "number",
                "value": "number"
            }
        elif self.domain == "www.videocardbenchmark.net":
            item_types = {
                "bus": "string",
                "cat": "string",
                "coreClk": "number",
                "date": "date",
                "g2d": "number",
                "g3d": "number",
                "href": "string",
                "id": "number",
                "memClk": "speed",
                "memSize": "size",
                "name": "string",
                "output": "bool",
                "powerPerf": "number",
                "price": "number",
                "rank": "number",
                "samples": "number",
                "tdp": "number",
                "value": "number"
            }
        else:
             # HDD
             item_types = {} 

        if item_type == None:
            if sort_by in item_types:            
                item_type = item_types[sort_by]
            else:
                item_type = "string"

        #filter the items and assign a number to each one, unless it is a string
        for item in self.items:
            value = item.get(sort_by)
            if value == "NA" or value is None:
                continue

            if item_type == "string":
                results.append([item, str(value)])
            elif item_type == "number":
                if type(value) is int or type(value) is float:
                    results.append([item, float(value)])
                else:
                    result = re.sub(r"[^0123456789\.]", "", str(value))
                    if len(result) > 0:
                        results.append([item, float(result)])
            elif item_type == "bool":
                results.append([item, int(value)])
            # ... (Simpler implementation for now, skipping complex unit parsing if not strictly needed for basic scoring)
            # Keeping it robust:
            else:
                 results.append([item, value])

        #sort items
        if order == "descending":
            reverse = True
        else:
            reverse = False
        
        # Sort based on the extracted value (index 1)
        try:
            results.sort(key=lambda x: x[1], reverse=reverse)
        except:
            pass # sorting might fail on mixed types

        if limit != None:
            results = results[:limit]
        return results
