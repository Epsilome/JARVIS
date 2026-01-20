"""
Simple JSON-based Review Storage

Replaces ChromaDB to avoid crashes. Uses simple keyword matching for retrieval.
"""
import os
import json
import requests
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

REVIEWS_DIR = Path(r"d:\JARVIS\data\reviews")
REVIEWS_DIR.mkdir(parents=True, exist_ok=True)

STEADY_BASE_URL = "https://api.steadyapi.com/v1"


def _get_reviews_file(product_name: str) -> Path:
    """Get the path to the reviews JSON file for a product."""
    safe_name = "".join(c if c.isalnum() else "_" for c in product_name.lower())
    return REVIEWS_DIR / f"{safe_name}.json"


def fetch_reddit_reviews(product_name: str, limit: int = 10) -> List[str]:
    """Fetch comments/posts from Reddit via SteadyAPI."""
    api_key = os.getenv("STEADY_API_KEY")
    if not api_key:
        logger.warning("STEADY_API_KEY not found.")
        return []
    
    headers = {"Authorization": f"Bearer {api_key}"}
    reviews = []
    
    search_url = f"{STEADY_BASE_URL}/reddit/search"
    params = {
        "search": f"{product_name} review",
        "sortType": "relevance",
        "filter": "posts",
        "limit": limit
    }
    
    try:
        resp = requests.get(search_url, headers=headers, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get('body') or data.get('data') or []
            
            logger.info(f"Found {len(items)} Reddit items for {product_name}.")
            
            for item in items:
                title = item.get('title', '')
                body = item.get('selftext', '') or item.get('body', '')
                if title:
                    reviews.append(f"Reddit: {title}\n{body}".strip())
    except Exception as e:
        logger.error(f"Reddit fetch failed: {e}")
    
    return reviews


def fetch_youtube_transcripts(product_name: str, limit: int = 2) -> List[str]:
    """Scrape YouTube search for video IDs and get transcripts."""
    from youtube_transcript_api import YouTubeTranscriptApi
    import re
    
    reviews = []
    try:
        # Simple scrape to get video IDs
        query_encoded = product_name.replace(" ", "+") + "+review"
        search_url = f"https://www.youtube.com/results?search_query={query_encoded}"
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(search_url, headers=headers, timeout=10)
        
        # Regex to find video IDs
        video_ids = re.findall(r"watch\?v=(\S{11})", resp.text)
        unique_ids = list(set(video_ids))[:limit]
        
        for vid in unique_ids:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(vid)
                full_text = " ".join([t['text'] for t in transcript])
                reviews.append(f"YouTube Video {vid}: {full_text}")
            except Exception:
                continue 
                
    except Exception as e:
        logger.error(f"YouTube fetch failed: {e}")
        
    return reviews


def ingest_reviews(product_name: str) -> bool:
    """Fetch and store reviews for a product."""
    logger.info(f"Ingesting reviews for {product_name}...")
    
    reddit_reviews = fetch_reddit_reviews(product_name)
    youtube_reviews = fetch_youtube_transcripts(product_name)
    
    all_reviews = reddit_reviews + youtube_reviews
    
    if not all_reviews:
        logger.info(f"No reviews found for {product_name}.")
        return False
    
    # Store in JSON file
    file_path = _get_reviews_file(product_name)
    data = {
        "product": product_name,
        "reviews": all_reviews,
        "count": len(all_reviews)
    }
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Stored {len(all_reviews)} reviews for {product_name} in {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save reviews: {e}")
        return False


def get_reviews(product_name: str) -> List[str]:
    """Get stored reviews for a product."""
    file_path = _get_reviews_file(product_name)
    
    if not file_path.exists():
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("reviews", [])
    except Exception as e:
        logger.error(f"Failed to load reviews: {e}")
        return []


def analyze_reviews(product_name: str, reviews: List[str]) -> Dict:
    """Use Ollama to analyze the reviews and extract pros/cons."""
    if not reviews:
        return None
    
    context = "\n---\n".join(reviews[:10])  # Limit to 10 reviews
    
    prompt = f"""You are a Tech Review Summarizer.
Analyze these reviews for '{product_name}' and provide:
1. Pros (list of positive points)
2. Cons (list of negative points)  
3. Verdict (Buy/Avoid/Wait)

Reviews:
{context[:4000]}

Respond in this JSON format:
{{"pros": ["point1", "point2"], "cons": ["point1", "point2"], "verdict": "Buy/Avoid/Wait"}}"""

    try:
        resp = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json={
                "model": "qwen2.5:3b",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            },
            timeout=60
        )
        if resp.status_code == 200:
            content = resp.json().get("message", {}).get("content", "")
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
    
    return None
