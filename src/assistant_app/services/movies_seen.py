from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, UniqueConstraint
from assistant_app.adapters.persistence.db import Base, engine, SessionLocal

class MovieSeen(Base):
    __tablename__ = "movies_seen"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tmdb_id: Mapped[str] = mapped_column(String(12))     # numeric, but store as str
    imdb_id: Mapped[str] = mapped_column(String(12))     # e.g., tt1234567
    title: Mapped[str] = mapped_column(String(200))
    year: Mapped[str] = mapped_column(String(8), default="")
    marked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("imdb_id", name="uq_movies_seen_imdb"),)

Base.metadata.create_all(bind=engine)

def mark_seen(tmdb_id: str, imdb_id: str, title: str, year: str = ""):
    with SessionLocal() as db:
        exists = db.query(MovieSeen).filter(MovieSeen.imdb_id == imdb_id).one_or_none()
        if not exists:
            db.add(MovieSeen(tmdb_id=tmdb_id, imdb_id=imdb_id, title=title, year=year))
            db.commit()
            return True
        return False

def unmark_seen(imdb_id: str) -> bool:
    with SessionLocal() as db:
        row = db.query(MovieSeen).filter(MovieSeen.imdb_id == imdb_id).one_or_none()
        if not row: return False
        db.delete(row); db.commit(); return True

def all_seen():
    with SessionLocal() as db:
        return db.query(MovieSeen).order_by(MovieSeen.marked_at.desc()).all()

def is_seen_map():
    """Return a set of imdb_ids for quick ✓ marking."""
    with SessionLocal() as db:
        return {row.imdb_id for row in db.query(MovieSeen.imdb_id).all()}
