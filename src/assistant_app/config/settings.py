# src/assistant_app/core/config.py
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()  # loads .env into process env
# print(f"DEBUG: DEFAULT_COUNTRY in env: {os.environ.get('DEFAULT_COUNTRY')}")

class Settings(BaseModel):
    APP_ENV: str = os.getenv("APP_ENV", "dev")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///assistant.db")

    TMDB_API_KEY: str | None = os.getenv("TMDB_API_KEY")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")

    # Scraper tuning
    SCRAPER_USER_AGENT: str = os.getenv("SCRAPER_USER_AGENT", "assistant/1.0 (+local)")
    SCRAPER_REQUEST_TIMEOUT: int = int(os.getenv("SCRAPER_REQUEST_TIMEOUT", "20"))
    SCRAPER_MAX_CONCURRENCY: int = int(os.getenv("SCRAPER_MAX_CONCURRENCY", "3"))
    ROTATING_PROXY_URL: str | None = os.getenv("ROTATING_PROXY_URL")

    DEFAULT_COUNTRY: str = os.getenv("DEFAULT_COUNTRY", "MA")
    DEFAULT_CITY: str = os.getenv("DEFAULT_CITY", "Casablanca")

settings = Settings()
