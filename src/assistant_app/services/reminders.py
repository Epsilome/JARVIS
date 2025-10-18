from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from assistant_app.interfaces.scheduler.scheduler import scheduler
from assistant_app.adapters.persistence.db import Base, engine, SessionLocal

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime
from .notify import toast
from apscheduler.triggers.cron import CronTrigger


@dataclass
class ReminderResult:
    job_id: str
    message: str
    when: str

class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String(255))
    when: Mapped[datetime] = mapped_column(DateTime)
    recurrence: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

Base.metadata.create_all(bind=engine)

def _notify(text: str):
    toast("Reminder", text)

def add_interval(text:str, **kw):
    job = scheduler.add_job(_notify, "interval",
                            next_run_time=datetime.now()+timedelta(seconds=5),
                            kwargs={"text": text}, **kw)
    return ReminderResult(job.id, text, f"interval {kw}")

def add_daily(text: str, hour: int, minute: int, job_id: str | None = None):
    """
    Schedule a toast every day at HH:MM.
    If job_id is provided, we'll allow replace_existing to keep ids stable.
    """
    trig = CronTrigger(hour=hour, minute=minute)
    job = scheduler.add_job(
        _notify,
        trigger=trig,
        kwargs={"text": text},
        id=job_id,
        replace_existing=True,
    )
    return ReminderResult(job.id, text, f"daily {hour:02d}:{minute:02d}")

def add_cron(text:str, expr:str):
    trig = CronTrigger.from_crontab(expr)   # e.g. "0 21 * * *"
    job = scheduler.add_job(_notify, trigger=trig, kwargs={"text": text})
    return ReminderResult(job.id, text, f"cron {expr}")

def add_once(text: str, when: datetime) -> ReminderResult:
    with SessionLocal() as db:
        r = Reminder(text=text, when=when)
        db.add(r); db.commit(); db.refresh(r)
    job = scheduler.add_job(_notify, "date", run_date=when, args=[text], id=f"rem_{r.id}")
    return ReminderResult(job.id, text, when.isoformat())

def add_recurring(text: str, every_minutes: int) -> ReminderResult:
    # Simple recurring example: every N minutes
    job = scheduler.add_job(_notify, "interval", minutes=every_minutes, next_run_time=datetime.now()+timedelta(seconds=5), args=[text])
    return ReminderResult(job.id, text, f"every {every_minutes} minutes")

def list_jobs():
    return [ (j.id, str(j.trigger), j.next_run_time) for j in scheduler.get_jobs() ]

def cancel(job_id: str) -> bool:
    try:
        scheduler.remove_job(job_id); return True
    except Exception:
        return False

def cancel_prefix(prefix: str) -> int:
    """
    Cancel all jobs whose id starts with prefix. Returns count removed.
    """
    removed = 0
    for j in list(scheduler.get_jobs()):
        if j.id and j.id.startswith(prefix):
            try:
                scheduler.remove_job(j.id)
                removed += 1
            except Exception:
                pass
    return removed