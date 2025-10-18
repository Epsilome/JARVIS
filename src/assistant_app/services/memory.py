from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, Session
from assistant_app.adapters.persistence.db import Base, engine, SessionLocal

class Pref(Base):
    __tablename__ = "prefs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    value: Mapped[str] = mapped_column(Text)

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
