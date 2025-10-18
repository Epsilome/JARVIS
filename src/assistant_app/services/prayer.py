from datetime import datetime, timedelta
import requests
from assistant_app.config.settings import settings
from .reminders import add_once
from .notify import toast

BASE = "https://api.aladhan.com/v1"

def get_today_timings(city: str, country: str, method: int = 2, school: int = 0, madhab: int | None = None):
    """
    Returns dict of today's timings (Fajr, Dhuhr, Asr, Maghrib, Isha, etc.)
    method: 2=ISNA, 3=MWL, 4=Umm Al-Qura, 5=Egyptian, etc.
    school (madhab) for Asr: 0=Shafi (default), 1=Hanafi
    """
    params = {"city": city, "country": country, "method": method, "school": school}
    r = requests.get(f"{BASE}/timingsByCity", params=params, timeout=20)
    r.raise_for_status()
    data = r.json()["data"]["timings"]
    # Clean seconds/timezone suffixes like "13:10 (+01)"
    clean = {k: v.split(" ")[0] for k, v in data.items()}
    return clean

def schedule_today_prayers(city: str, country: str, method: int = 2, school: int = 0, only: list[str] | None = None):
    """
    Schedules remaining prayers for today as one-off reminders (toasts).
    """
    times = get_today_timings(city, country, method, school)
    today = datetime.now().date()
    now = datetime.now()

    def parse_hhmm(s: str):
        hh, mm = map(int, s.split(":")[:2])
        return datetime.combine(today, datetime.min.time()).replace(hour=hh, minute=mm)

    keys = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    if only: keys = [k for k in keys if k in only]

    scheduled = []
    for k in keys:
        t = parse_hhmm(times[k])
        if t > now:
            add_once(f"{k} prayer time", t)
            scheduled.append((k, t.strftime("%H:%M")))
    if not scheduled:
        toast("Prayer times", "All remaining prayers for today have passed.")
    return scheduled
