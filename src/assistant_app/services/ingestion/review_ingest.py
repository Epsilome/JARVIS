import os
import requests
import chromadb
import logging
import re
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHROMA_PATH = r"d:\JARVIS\data\chroma_db"
STEADY_BASE_URL = "https://api.steadyapi.com/v1"

class ReviewIngestor:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(name="product_reviews")
        self.api_key = os.getenv("STEADY_API_KEY")
        if not self.api_key:
            logger.warning("STEADY_API_KEY not found in env.")

    def fetch_reddit_reviews(self, product_name: str, limit: int = 5) -> List[str]:
        """Fetch comments/posts from Reddit via SteadyAPI."""
        if not self.api_key: return []
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        reviews = []
        
        # 1. Search for threads
        search_url = f"{STEADY_BASE_URL}/reddit/search"
        params = {
            "search": f"{product_name} review",
            "sortType": "relevance",
            "filter": "posts",
            "limit": limit
        }
        
        try:
            resp = requests.get(search_url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                # SteadyAPI returns {'meta': ..., 'body': [...]}
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    # Check 'body' first, then 'data', then fallback
                    items = data.get('body') or data.get('data') or []
                
                logger.info(f"Found {len(items)} Reddit items.")
                
                for item in items:
                    # Capture Title and Selftext
                    title = item.get('title', '')
                    body = item.get('selftext', '') or item.get('body', '') 
                    
                    if title: reviews.append(f"Reddit Title: {title}\n{body}")
                    
                    # Ideally we'd fetch comments too, but this is a good start
        except Exception as e:
            logger.error(f"Reddit fetch failed: {e}")
            
        return reviews

    def fetch_youtube_transcripts(self, product_name: str, limit: int = 2) -> List[str]:
        """Scrape YouTube search for video IDs and get transcripts."""
        reviews = []
        try:
            # Simple scrape to get video IDs (avoiding API quota/key complexity for now)
            # User suggested youtube-transcript-api which needs IDs
            query_encoded = product_name.replace(" ", "+") + "+review"
            search_url = f"https://www.youtube.com/results?search_query={query_encoded}"
            
            # Use headers to look like a browser
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(search_url, headers=headers)
            
            # Regex to find video IDs
            video_ids = re.findall(r"watch\?v=(\S{11})", resp.text)
            unique_ids = list(set(video_ids))[:limit]
            
            for vid in unique_ids:
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(vid)
                    # Combine text
                    full_text = " ".join([t['text'] for t in transcript])
                    reviews.append(f"YouTube Video {vid}: {full_text}")
                except Exception:
                    continue # No captions or other error
                    
        except Exception as e:
            logger.error(f"YouTube fetch failed: {e}")
            
        return reviews

    def ingest_product(self, product_name: str):
        """Fetch and store reviews for a product."""
        logger.info(f"Ingesting reviews for {product_name}...")
        
        # Fetch
        reddit_texts = self.fetch_reddit_reviews(product_name)
        youtube_texts = self.fetch_youtube_transcripts(product_name)
        
        all_texts = reddit_texts + youtube_texts
        
        if not all_texts:
            logger.info("No reviews found.")
            return
            
        # Store in Chroma
        ids = [f"{product_name}_{i}" for i in range(len(all_texts))]
        metadatas = [{"product": product_name, "source": "reddit" if i < len(reddit_texts) else "youtube"} for i in range(len(all_texts))]
        
        # Simple usage: add documents directly (Chroma uses default embedding model by default)
        try:
             self.collection.add(
                documents=all_texts,
                metadatas=metadatas,
                ids=ids
            )
             logger.info(f"Stored {len(all_texts)} review chunks.")
        except Exception as e:
            logger.error(f"Chroma add failed: {e}")

if __name__ == "__main__":
    # Test run
    ingestor = ReviewIngestor()
    ingestor.ingest_product("Zephyrus G14")
