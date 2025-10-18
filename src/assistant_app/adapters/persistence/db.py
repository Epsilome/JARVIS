from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from assistant_app.config.settings import settings

class Base(DeclarativeBase): pass

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
