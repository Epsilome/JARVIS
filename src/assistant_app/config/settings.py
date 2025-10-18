# src/assistant_app/core/config.py
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()  # loads .env into process env

class Settings(BaseModel):
    APP_ENV: str = os.getenv("APP_ENV", "dev")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///assistant.db")

    TMDB_API_KEY: str | None = os.getenv("TMDB_API_KEY")

    # Scraper tuning
    SCRAPER_USER_AGENT: str = os.getenv("SCRAPER_USER_AGENT", "assistant/1.0 (+local)")
    SCRAPER_REQUEST_TIMEOUT: int = int(os.getenv("SCRAPER_REQUEST_TIMEOUT", "20"))
    SCRAPER_MAX_CONCURRENCY: int = int(os.getenv("SCRAPER_MAX_CONCURRENCY", "3"))
    ROTATING_PROXY_URL: str | None = os.getenv("ROTATING_PROXY_URL")

    DEFAULT_COUNTRY: str = os.getenv("DEFAULT_COUNTRY", "FR")

settings = Settings()
