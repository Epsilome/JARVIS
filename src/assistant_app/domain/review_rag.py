import instructor
from pydantic import BaseModel, Field
from openai import OpenAI
import chromadb
import logging
import os
from assistant_app.config.settings import settings

logger = logging.getLogger(__name__)

class ProsCons(BaseModel):
    pros: list[str] = Field(description="List of positive aspects extracted from reviews.")
    cons: list[str] = Field(description="List of negative aspects extracted from reviews.")
    verdict: str = Field(description="A concise summary verdict (Buy/Avoid/Wait).")
    confidence: float = Field(default=0.5, description="Confidence score 0.0-1.0 based on review quantity/consistency.")

class ReviewIntelligence:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        try:
            self.chroma = chromadb.PersistentClient(path=r"d:\JARVIS\data\chroma_db")
            # No embedding function (manual handling)
            self.collection = self.chroma.get_or_create_collection(
                "product_reviews",
                embedding_function=None
            )
        except Exception as e:
            logger.error(f"ChromaDB init failed: {e}")
            self.collection = None

        # Setup Instructor with Ollama
        try:
             self.client = instructor.patch(OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama"
            ), mode=instructor.Mode.MD_JSON)
        except Exception as e:
            logger.error(f"LLM init failed: {e}")
            self.client = None

    def get_opinions(self, product_name: str) -> ProsCons | None:
        """Retrieve reviews and generate a summary."""
        if not self.collection or not self.client:
            logger.warning("Review Intelligence not available (DB or LLM down).")
            return None
            
        # 1. Retrieve
        try:
            # Manual embedding for query
            import requests
            def _get_emb(t):
                try:
                    r = requests.post("http://127.0.0.1:11434/api/embeddings", json={"model": "qwen2.5:3b", "prompt": t}, timeout=5)
                    if r.status_code==200: return r.json().get("embedding")
                except: pass
                return None
            
            q_emb = _get_emb(f"{product_name} reviews opinion")
            
            if q_emb:
                results = self.collection.query(
                    query_embeddings=[q_emb],
                    n_results=15,
                    where={"product": product_name}
                )
            else:
                logger.warning("Failed to embed query.")
                return None

        except Exception as e:
            logger.warning(f"Chroma query failed: {e}")
            return None

        docs = results.get('documents', [[]])[0]
        if not docs:
            logger.info(f"No reviews found for {product_name} in DB.")
            return None
            
        context = "\n---\n".join(docs)
        
        # 2. Analyze
        prompt = f"""
        You are a Tech Review Summarizer.
        Analyze the provided reviews for '{product_name}'.
        
        OUTPUT RULES:
        1. Extract 'pros' and 'cons' as simple lists of strings.
        2. Do NOT wrap strings in objects (e.g. NO {{"string": "text"}}). 
        3. Example Pros: ["Great screen", "Fast CPU"]
        4. Verdict: Concise summary.
        
        Reviews:
        {context[:8000]} 
        """
        
        try:
            resp = self.client.chat.completions.create(
                model=settings.OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": "You extracts structured opinions from text. Output valid JSON matching the schema."},
                    {"role": "user", "content": prompt}
                ],
                response_model=ProsCons
            )
            return resp
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return None
