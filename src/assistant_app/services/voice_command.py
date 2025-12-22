import re
import typer

from assistant_app.services.reminders import add_once, list_jobs, add_daily, cancel_prefix
from assistant_app.adapters.nlu.time_parse import parse_when
from assistant_app.services.prayer import get_today_timings
from assistant_app.services.movies_seen import all_seen
from assistant_app.config.settings import settings
from assistant_app.adapters.nlu.tts_kokoro import speak
from assistant_app.adapters.nlu.ollama_adapter import ask_ollama



def respond(text: str):
    """Echoes text to console and speaks it."""
    typer.echo(text)
    speak(text)

def process_voice_command(text: str):
    """
    Parses the voice command text and executes the corresponding action.
    """
    text = text.lower().strip()
    # Strip punctuation (.,!?) to ensure clean matching
    text = re.sub(r'[^\w\s]', '', text)
    typer.echo(f"DEBUG: Processing '{text}'")
    
    # --- Priority Dispatch ---
    
    # 1. STOP/EXIT (Exact or simple match)
    if text in ["stop", "exit", "quit", "shut down", "terminate"]:
        respond("Goodbye.")
        raise typer.Exit()

    # 2. REMINDER SETTING (Strict Regex)
    # Must start with "remind me" or "set reminder" or "remember to"
    if re.match(r"^(remind me|set reminder|remember to)", text):
        clean_text = re.sub(r"^(remind me (to )?|set reminder (to )?|remember to )", "", text).strip()
        dt, remainder = parse_when(clean_text)
        if dt:
            add_once(clean_text, dt)
            respond(f"I've set a reminder for {dt.strftime('%H:%M')}.")
        else:
            respond("I heard you want a reminder, but I couldn't understand the time.")
        return

    # 3. OTHER COMMANDS (Keyword Presence)
    # Only if specific unique phrases are found
    
    # Prayer
    if any(k in text for k in ["prayer times", "when is fajr", "when is isha"]):
        city = settings.DEFAULT_CITY or "Casablanca"
        country = settings.DEFAULT_COUNTRY or "MA"
        times = get_today_timings(city, country, 2, 0)
        respond(f"Here are the prayer times for {city}.")
        for k in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
            typer.echo(f"  {k}: {times[k]}")
        return

    # Watched Movies
    if any(k in text for k in ["watched movies", "movies i have seen", "seen movies"]):
        rows = all_seen()
        if not rows:
            respond("You haven't marked any movies as watched yet.")
        else:
            respond(f"You have watched {len(rows)} movies. Here are the last 5:")
            for r in rows[:5]:
                typer.echo(f"✓ {r.title} ({r.year})")
        return

    # Eye Care
    if "start eye care" in text or "enable eye care" in text:
        times = ["12:00", "16:00", "20:00"]
        cancel_prefix("eye_")
        for t in times:
            hh, mm = map(int, t.split(":"))
            job_id = f"eye_{hh:02d}{mm:02d}"
            add_daily("Use eye-cleaning product", hh, mm, job_id=job_id)
        respond(f"Eye care reminders enabled for {', '.join(times)}.")
        return

    # List Reminders
    if "list reminders" in text or "show reminders" in text or "my reminders" in text:
        rows = list_jobs()
        if not rows:
            respond("You have no active reminders.")
        else:
            respond(f"You have {len(rows)} reminders.")
            for jid, trig, next_run in rows:
                typer.echo(f"  • {jid} | {next_run}")
        return

    # 4. FALLBACK -> OLLAMA
    # If no specific command logic matched, assume it's a general query
    # This prevents "Tell me about..." from being caught by "remind me" regex/keywords
    answer = ask_ollama(text)
    if answer:
        respond(answer)
    else:
        respond("I'm sorry, I couldn't process that.")
    return


