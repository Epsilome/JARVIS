from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, Session
from assistant_app.adapters.persistence.db import Base, engine, SessionLocal

class Pref(Base):
    __tablename__ = "prefs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    value: Mapped[str] = mapped_column(Text)

class UserProfile(Base):
    __tablename__ = "user_profile"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Using a single row for the active user, but modeling properly
    username: Mapped[str] = mapped_column(String(64), unique=True, default="user")
    
    budget: Mapped[str] = mapped_column(String(32), nullable=True) # e.g. "1200 EUR"
    region: Mapped[str] = mapped_column(String(10), nullable=True) # e.g. "FR"
    usage: Mapped[str] = mapped_column(String(255), nullable=True) # e.g. "Gaming, Work"
    preferred_brand: Mapped[str] = mapped_column(String(64), nullable=True)

def init_memory():
    Base.metadata.create_all(bind=engine)

def set_pref(key: str, value: str):
    with SessionLocal() as db:
        pref = db.query(Pref).filter(Pref.key == key).one_or_none()
        if pref: pref.value = value
        else: db.add(Pref(key=key, value=value))
        db.commit()

def get_pref(key: str, default: str | None = None) -> str | None:
    with SessionLocal() as db:
        pref = db.query(Pref).filter(Pref.key == key).one_or_none()
        return pref.value if pref else default

def update_profile_db(data: dict):
    """Updates the single user profile with the provided fields."""
    with SessionLocal() as db:
        # Assuming single user system for now
        profile = db.query(UserProfile).first()
        if not profile:
            profile = UserProfile(username="user")
            db.add(profile)
        
        for key, val in data.items():
            if hasattr(profile, key) and val is not None:
                setattr(profile, key, str(val) if val else None)
        
        db.commit()
        return True

def get_profile_db() -> dict:
    """Returns the user profile as a dictionary."""
    with SessionLocal() as db:
        profile = db.query(UserProfile).first()
        if not profile:
            return {}
        
        return {
            "budget": profile.budget,
            "region": profile.region,
            "usage": profile.usage,
            "preferred_brand": profile.preferred_brand
        }
