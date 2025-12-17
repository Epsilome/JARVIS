import logging
import json
import ollama
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from assistant_app.config.settings import settings

logger = logging.getLogger(__name__)

def fetch_url_text(url: str) -> str:
    """Fetches text content from a URL using BS4."""
    try:
        headers = {'User-Agent': settings.SCRAPER_USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Remove scripts and styles
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        # Limit text length for LLM context (approx 2000 words ~ 8k chars)
        return text[:12000]
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return ""

def search_specs(product_name: str) -> dict | None:
    """
    Searches the web for technical specifications and uses LLM to extract them.
    Returns a dict with vram, tdp, release_date, etc.
    """
    # Force US English and target TechPowerUp directly as it is the bible for GPU specs
    query = f"{product_name} specs site:techpowerup.com"
    logger.info(f"Spec Lookup: Searching for {query}")
    
    try:
        # 1. Search Web to get URL
        results = DDGS().text(query, max_results=1, backend="lite", region="us-en")
        
        if not results:
            # Fallback to broad search if strict site search fails
            query = f"{product_name} specs vram tdp"
            results = DDGS().text(query, max_results=1, backend="lite", region="us-en")
            
        if not results:
            logger.warning(f"No results found for {product_name}")
            return None
        
        url = results[0]['href']
        title = results[0]['title']
        logger.info(f"Fetching content from: {url}")
        
        # 2. Fetch full page content
        context_text = fetch_url_text(url)
        if not context_text:
            # Fallback to snippet if fetch fails
            context_text = results[0]['body']
        
        logger.debug(f"Context length: {len(context_text)} chars")
            
        # 3. Extract with LLM
        prompt = (
            f"Extract the technical specifications for '{product_name}' from the text below.\n"
            "Return ONLY a JSON object with these keys (find as many as possible):\n"
            "- 'vram': string (e.g. '24 GB GDDR6X')\n"
            "- 'tdp': string (look for 'TDP', 'Board Power', 'W' power rating)\n"
            "- 'release_date': string (Year or Date)\n"
            "- 'cuda_cores': string (look for 'Shading Units', 'Stream Processors', 'CUDA Cores')\n"
            "- 'boost_clock': string\n"
            "If not found, set to null.\n\n"
            f"Source Title: {title}\n"
            f"Context:\n{context_text[:12000]}"
        )
        
        logger.info("Extracting specs with Ollama...")
        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            format='json',
            options={'temperature': 0.0}
        )
        
        content = response['message']['content']
        logger.debug(f"Ollama Extraction Raw Output: {content}")
        
        data = json.loads(content)
        return data

    except Exception as e:
        logger.error(f"Error fetching specs: {e}")
        return None
