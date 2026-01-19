import re
import typer

from assistant_app.services.reminders import add_once, list_jobs, add_daily, cancel_prefix
from assistant_app.adapters.nlu.time_parse import parse_when
from assistant_app.services.prayer import get_today_timings
from assistant_app.services.movies_seen import all_seen
from assistant_app.config.settings import settings
from assistant_app.adapters.nlu.tts_kokoro import speak
from assistant_app.adapters.nlu.ollama_adapter import ask_ollama
# Optional UI hook
try:
    from assistant_app.interfaces.gui.state import state
except ImportError:
    state = None

def respond(text: str, is_command=False, is_error=False):
    """
    Standard function to print to CLI and speak tts.
    Wraps it in [GUI:ASSISTANT:...] for the GUI to parse.
    """
    # 1. Print visual message
    # IMPORTANT: We encode newlines as literal \n so the GUI regex catches it as one line
    safe_text = text.replace('\n', '\\n')
    print(f"[GUI:ASSISTANT:{safe_text}]", flush=True)

    # 2. Stats update
    if is_command:
        print("[GUI:STATS:CMD:+1]", flush=True)
    if is_error:
        print("[GUI:STATS:ERR:+1]", flush=True)

    # 3. Print pretty to CLI
    typer.echo(f"🤖 {text}")
    
    # 4. Update GUI state (if available)
    if state:
        state.add_message("assistant", text)
        state.add_log(f"Response: {text[:30]}...")
        
    # 5. Speak
    speak(text)  # tts_kokoro handles markdown stripping

def process_voice_command(text: str, speak_response: bool = True):
    """
    Parses the voice command text and executes the corresponding action.
    """
    text = text.lower().strip()
    # Strip punctuation (.,!?) to ensure clean matching
    text = re.sub(r'[^\w\s]', '', text)
    typer.echo(f"DEBUG: Processing '{text}'")
    
    # Helper to send responses with current speak setting
    def reply(msg: str, is_command: bool = False, is_error: bool = False):
        respond(msg, is_command=is_command, is_error=is_error)

    # --- Priority Dispatch ---
    
    # 1. STOP/EXIT (Exact or simple match)
    if text in ["stop", "exit", "quit", "shut down", "terminate", "goodbye", "bye"]:
        reply("Goodbye.")
        raise typer.Exit()

    # 2. OTHER COMMANDS (Keyword Presence)
    # Only if specific unique phrases are found
    
    # Weather
    if "weather" in text or "temperature" in text or "how hot" in text:
        from assistant_app.services.weather_service import get_weather_sync
        city = settings.DEFAULT_CITY or "Casablanca"
        country = settings.DEFAULT_COUNTRY or "MA"
        
        # Check if user specified a city (simple heuristic)
        # e.g., "weather in london"
        words = text.split()
        if "in" in words:
            try:
                idx = words.index("in")
                if idx < len(words) - 1:
                    city = words[idx+1].capitalize()
            except: pass
            
        w = get_weather_sync(city, country)
        reply(f"Currently in {w['city']}, it is {w['temp']} degrees Celsius with {w['description']}. Humidity is {w['humidity']}%.")
        return

    # Jokes
    if "joke" in text or "funny" in text:
        import random
        jokes = [
            "Why did the AI cross the road? To optimize the pathfinding algorithm!",
            "I would tell you a UDP joke, but you might not get it.",
            "Why do programmers prefer dark mode? Because light attracts bugs.",
            "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
            "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
            "Why was the computer cold? It left its Windows open.",
            "I asked my specialized AI for a joke about the future... it said 'I'm still processing it'.",
        ]
        reply(random.choice(jokes))
        return

    # Prayer
    if any(k in text for k in ["prayer times", "when is fajr", "when is isha"]):
        city = settings.DEFAULT_CITY or "Casablanca"
        country = settings.DEFAULT_COUNTRY or "MA"
        times = get_today_timings(city, country, 2, 0)
        reply(f"Here are the prayer times for {city}.")
        for k in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
            typer.echo(f"  {k}: {times[k]}")
        return

    # Watched Movies
    if any(k in text for k in ["watched movies", "movies i have seen", "seen movies"]):
        rows = all_seen()
        if not rows:
            reply("You haven't marked any movies as watched yet.")
        else:
            reply(f"You have watched {len(rows)} movies. Here are the last 5:")
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
        reply(f"Eye care reminders enabled for {', '.join(times)}.")
        return

    # List Reminders
    if "list reminders" in text or "show reminders" in text or "my reminders" in text:
        rows = list_jobs()
        if not rows:
            reply("You have no active reminders.")
        else:
            reply(f"You have {len(rows)} reminders.")
            for jid, trig, next_run in rows:
                typer.echo(f"  • {jid} | {next_run}")
        return

    # 4. FALLBACK -> OLLAMA
    # If no specific command logic matched, assume it's a general query
    # This prevents "Tell me about..." from being caught by "remind me" regex/keywords
    answer = ask_ollama(text)
    if answer:
        reply(answer, is_command=True)
    else:
        reply("I'm sorry, I couldn't process that.", is_error=True)
    return


