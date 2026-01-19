"""
PassMark HTML Scraper v2
Extracts CPU, GPU, and SSD benchmark data from saved PassMark HTML pages
"""

from bs4 import BeautifulSoup
import csv
import re
import os

def scrape_cpus(html_path):
    """Extract CPU names and PassMark scores from the HTML file."""
    print(f"Reading {html_path}...")
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    cpus = []
    
    # Pattern: <a href="...cpubenchmark.net/cpu...">CPU Name</a></td><td>cores</td><td...>SCORE</td>
    # The benchmark data is in table rows with links
    pattern = r'<a\s+href="[^"]*cpubenchmark\.net/cpu[^"]*"[^>]*>([^<]+)</a>\s*</td>\s*<td[^>]*>(\d+)</td>\s*<td[^>]*>\s*(\d[\d,]*)'
    
    matches = re.findall(pattern, html, re.IGNORECASE)
    print(f"Found {len(matches)} matches with pattern 1")
    
    if not matches:
        # Alternative pattern - simpler
        pattern2 = r'cpubenchmark\.net/cpu[^"]*"[^>]*>([^<]+)</a>.*?<td[^>]*>(\d[\d,]+)</td>'
        matches = re.findall(pattern2, html, re.IGNORECASE | re.DOTALL)
        print(f"Found {len(matches)} matches with pattern 2")
    
    for match in matches:
        if len(match) >= 2:
            name = match[0].strip()
            # Score might be in position 2 or 1 depending on pattern
            score_text = match[-1] if len(match) >= 3 else match[1]
            score = int(score_text.replace(',', '')) if score_text else 0
            
            # Filter out header rows and invalid entries
            if name and not any(x in name.lower() for x in ['cpu name', 'processor', 'benchmark']):
                cpus.append({'name': name, 'score': score})
    
    # Deduplicate by name
    seen = set()
    unique_cpus = []
    for cpu in cpus:
        if cpu['name'] not in seen:
            seen.add(cpu['name'])
            unique_cpus.append(cpu)
    
    print(f"Extracted {len(unique_cpus)} unique CPUs")
    
    # Sort by score descending
    unique_cpus.sort(key=lambda x: x['score'], reverse=True)
    
    return unique_cpus

def scrape_gpus(html_path):
    """Extract GPU names and PassMark scores."""
    print(f"Reading {html_path}...")
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    gpus = []
    
    # Pattern for GPU: videocardbenchmark.net/video_lookup.php?gpu=...
    # Score is in first td after the name link - class="sorting_1" contains the score
    pattern = r'<a\s+href="[^"]*videocardbenchmark\.net/video_lookup\.php[^"]*"[^>]*>([^<]+)</a>\s*</td>\s*<td[^>]*>(\d[\d,]*)</td>'
    matches = re.findall(pattern, html, re.IGNORECASE)
    print(f"Found {len(matches)} GPU matches")
    
    for name, score_text in matches:
        name = name.strip()
        score = int(score_text.replace(',', '')) if score_text else 0
        if name and len(name) > 3 and score > 0:
            gpus.append({'name': name, 'score': score})
    
    # Deduplicate
    seen = set()
    unique = []
    for item in gpus:
        if item['name'] not in seen:
            seen.add(item['name'])
            unique.append(item)
    
    unique.sort(key=lambda x: x['score'], reverse=True)
    print(f"Extracted {len(unique)} unique GPUs")
    
    # Show top 5
    print("Top 5 GPUs:")
    for gpu in unique[:5]:
        print(f"  {gpu['name']}: {gpu['score']}")
    
    return unique

def scrape_ssds(html_path):
    """Extract SSD/Drive names and PassMark scores."""
    print(f"Reading {html_path}...")
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    drives = []
    
    # Pattern for drives
    pattern = r'<a\s+href="[^"]*hdd_mega_page|harddrivebenchmark[^"]*"[^>]*>([^<]+)</a>.*?<td[^>]*>(\d[\d,]+)</td>'
    matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
    print(f"Found {len(matches)} drive matches")
    
    for name, score_text in matches:
        name = name.strip()
        score = int(score_text.replace(',', '')) if score_text else 0
        if name and len(name) > 3:
            drives.append({'name': name, 'score': score})
    
    # Deduplicate
    seen = set()
    unique = []
    for item in drives:
        if item['name'] not in seen:
            seen.add(item['name'])
            unique.append(item)
    
    unique.sort(key=lambda x: x['score'], reverse=True)
    print(f"Extracted {len(unique)} unique drives")
    return unique

def save_to_csv(data, output_path):
    """Save extracted data to CSV."""
    if not data:
        print(f"No data to save to {output_path}")
        return
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'score'])
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Saved {len(data)} items to {output_path}")

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Scrape CPUs
    cpu_html = os.path.join(base_path, 'ALL_CPU', 'PassMark - CPU Benchmarks - CPU Mega Page - Detailed List of Benchmarked CPUs.html')
    if os.path.exists(cpu_html):
        cpus = scrape_cpus(cpu_html)
        save_to_csv(cpus, os.path.join(base_path, 'data', 'passmark_cpus.csv'))
        # Show sample
        print("\nTop 10 CPUs:")
        for cpu in cpus[:10]:
            print(f"  {cpu['name']}: {cpu['score']}")
    
    # Scrape GPUs
    gpu_html = os.path.join(base_path, 'ALL_GPU', 'PassMark - Video Card (GPU) Benchmarks - GPU Mega Page - Detailed List of Benchmarked Videocards.html')
    if os.path.exists(gpu_html):
        gpus = scrape_gpus(gpu_html)
        save_to_csv(gpus, os.path.join(base_path, 'data', 'passmark_gpus.csv'))
    
    # Scrape SSDs
    ssd_html = os.path.join(base_path, 'ALL_SSD', 'PassMark - Hard Drive Benchmarks - Drive Mega Page - Detailed List of Benchmarked Storage Drives.html')
    if os.path.exists(ssd_html):
        ssds = scrape_ssds(ssd_html)
        save_to_csv(ssds, os.path.join(base_path, 'data', 'passmark_ssds.csv'))
    
    print("\n✅ Done! Check the data/ folder for CSV files.")
