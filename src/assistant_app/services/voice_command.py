import re
import typer
from thefuzz import process as fuzz_process

# from assistant_app.services.movies import top_horror
# from assistant_app.services.prices import search_all
# from assistant_app.domain.benchmarks import value_score, value_score_work
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
    text = text.lower()
    
    # Define intents and their keywords/phrases
    intents = {
        "prayer": ["prayer times", "when is fajr", "when is isha", "prayer schedule"],
        "watched_movies": ["watched movies", "movies i have seen", "seen movies", "what did i watch"],
        "eye_care": ["start eye care", "enable eye care", "eye protection"],
        "list_reminders": ["show reminders", "list reminders", "my reminders", "what do i have to do"],
        "remind": ["remind me", "set reminder", "remember to"],
        "stop": ["stop", "exit", "quit", "shut down", "terminate"]
    }

    # Flatten for fuzzy matching
    all_phrases = []
    for intent, phrases in intents.items():
        all_phrases.extend(phrases)

    # Find best match
    best_match, score = fuzz_process.extractOne(text, all_phrases)
    typer.echo(f"DEBUG: Best match: '{best_match}' (Score: {score})")
    
    # Threshold for fuzzy match
    if score < 90:
        # Fallback to keyword matching if fuzzy score is low
        matched_intent = None
    else:
        # Map phrase back to intent
        matched_intent = next((k for k, v in intents.items() if best_match in v), None)

    # --- Logic Dispatch ---

    # Prayer Times
    if matched_intent == "prayer":
        city = settings.DEFAULT_CITY or "Casablanca"
        country = settings.DEFAULT_COUNTRY or "MA"
        times = get_today_timings(city, country, 2, 0)
        respond(f"Here are the prayer times for {city}.")
        for k in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
            typer.echo(f"  {k}: {times[k]}")
        return

    # Watched Movies
    if matched_intent == "watched_movies":
        rows = all_seen()
        if not rows:
            respond("You haven't marked any movies as watched yet.")
        else:
            respond(f"You have watched {len(rows)} movies. Here are the last 5:")
            for r in rows[:5]:
                typer.echo(f"✓ {r.title} ({r.year})")
        return

    # Eye Care
    if matched_intent == "eye_care":
        times = ["12:00", "16:00", "20:00"]
        cancel_prefix("eye_")
        for t in times:
            hh, mm = map(int, t.split(":"))
            job_id = f"eye_{hh:02d}{mm:02d}"
            add_daily("Use eye-cleaning product", hh, mm, job_id=job_id)
        respond(f"Eye care reminders enabled for {', '.join(times)}.")
        return

    # List Reminders
    if matched_intent == "list_reminders":
        rows = list_jobs()
        if not rows:
            respond("You have no active reminders.")
        else:
            respond(f"You have {len(rows)} reminders.")
            for jid, trig, next_run in rows:
                typer.echo(f"  • {jid} | {next_run}")
        return



    # Reminders (Set new) - Keep regex/keyword for this as it has variable content
    if "remind" in text or matched_intent == "remind":
        clean_text = re.sub(r"^remind (me )?(to )?", "", text).strip()
        dt, remainder = parse_when(clean_text)
        if dt:
            add_once(clean_text, dt)
            respond(f"I've set a reminder for {dt.strftime('%H:%M')}.")
        else:
            respond("I heard you want a reminder, but I couldn't understand the time.")
        return

    # Stop/Exit
    if matched_intent == "stop":
        respond("Goodbye.")
        raise typer.Exit()

    # Fallback to Ollama
    respond("Let me think about that...")
    answer = ask_ollama(text)
    if answer:
        respond(answer)
    else:
        respond("I'm sorry, I couldn't process that.")
