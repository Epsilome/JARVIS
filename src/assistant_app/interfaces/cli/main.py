# trunk-ignore-all(isort)
# src/assistant_app/interfaces/cli/main.py
import asyncio, json, logging, signal, sys, time
from pathlib import Path
from datetime import datetime, timedelta
import typer
from loguru import logger
from assistant_app.adapters.console_manager import console, print_table, print_panel, create_table, print_success, print_error, print_warning
from collections import defaultdict


# ── updated import paths to match your new layout ───────────────────────────────
from assistant_app.interfaces.scheduler.scheduler import scheduler

from assistant_app.services.memory import init_memory, set_pref, get_pref, get_profile_db
from assistant_app.services.reminders import (
    add_once, add_interval, add_cron, list_jobs, cancel,
)
from assistant_app.adapters.nlu.time_parse import parse_when, parse_every

from assistant_app.services.movies import top_horror, _tmdb_external_ids
from assistant_app.services.movies_seen import mark_seen, unmark_seen, all_seen, is_seen_map

from assistant_app.adapters.system_control import (
    set_volume, lock_screen, minimize_all, open_app as sys_open_app
)

from assistant_app.services.prayer import get_today_timings, schedule_today_prayers
from assistant_app.config.settings import settings

from assistant_app.domain.benchmarks import is_gpu_at_least_5060
from assistant_app.domain.benchmarks import value_score
from assistant_app.domain.benchmarks import value_breakdown
from assistant_app.domain.benchmarks import value_score_work
from assistant_app.domain.benchmarks_loader import refresh_cpu_cache
from assistant_app.domain.benchmarks_loader import refresh_gpu_cache

from assistant_app.services.prices import search_all, search_all_async

from assistant_app.adapters.nlu.speech_recognition import listen_and_recognize
from assistant_app.services.voice_command import process_voice_command
# ────────────────────────────────────────────────────────────────────────────────

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Global suppression of annoying third-party logs
logging.getLogger("phonemizer").setLevel(logging.CRITICAL)
logging.getLogger("phonemizer.backend.espeak.wrapper").setLevel(logging.CRITICAL)

app = typer.Typer(help="Local Desktop Assistant")
movies_app = typer.Typer(help="Movie suggestions & watched list")
app.add_typer(movies_app, name="movies")

system_app = typer.Typer(help="System controls (volume, lock, open apps)")
app.add_typer(system_app, name="system")

@app.callback()
def _start():
    init_memory()
    # catch up missed jobs (<=10min late), then ensure scheduler is running
    for j in scheduler.get_jobs():
        if j.next_run_time and j.next_run_time < datetime.now() and datetime.now() - j.next_run_time < timedelta(minutes=10):
            try:
                j.func(**(j.kwargs or {}))
            except Exception as e:
                logger.error(f"[catchup] Job {j.id} failed: {e}")
    if not scheduler.running:
        scheduler.start()

@app.command()
def start():
    """Keep the assistant running in the background (scheduler, etc.)."""
    typer.echo("Assistant running. Press Ctrl+C to exit.")
    
    stop_event = asyncio.Event()

    def signal_handler(sig, frame):
        typer.echo("\nShutting down...")
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Keep main thread alive
    try:
        signal.pause()
    except AttributeError:
        # Windows doesn't support signal.pause()

        while True:
            # Force scheduler to wake up and check DB for new jobs every 15s
            # (BackgroundScheduler doesn't autorefresh ext changes easily)
            if scheduler.running:
                scheduler.wakeup()
            time.sleep(15)

@app.command()
def listen(loop: bool = True):
    """
    Start listening for voice commands.
    """
    typer.echo("Listening for commands... (say 'stop' to exit)")
    typer.echo("Listening for commands... (say 'stop' to exit)")
    while True:
        try:
            text = listen_and_recognize()
            if text:
                process_voice_command(text)
                # Short pause to prevent mic from hearing the end of the TTS response
                # Increased to 1.5s to be safe against echo
                time.sleep(1.5) 
        except (KeyboardInterrupt, typer.Exit):
            typer.echo("\nStopping listener.")
            break
        except Exception as e:
            logger.error(f"Listener Loop Error: {e}")
            time.sleep(1) # Prevent tight loop on error
            
        if not loop:
            break

@app.command()
def pref():
    """
    Show stored user profile context (contextual memory).
    """
    profile = get_profile_db()
    
    if not profile:
        print_warning("No user profile found in memory.")
        return

    # Filter out empty keys for cleaner display
    clean_profile = {k: v for k, v in profile.items() if v}
    if not clean_profile:
         print_warning("User profile exists but is empty.")
         return

    print_panel(json.dumps(clean_profile, indent=2), title="Active User Context")

@app.command()
def ask(
    query: str,
    speak: bool = typer.Option(False, "--speak", "-s", help="Speak the response aloud."),
):
    """
    Send a text query to the assistant (CLI mode). 
    Useful for debugging or silent interaction.
    """
    process_voice_command(query, speak_response=speak)



@app.command()
def remind(text: str = "", when: str = "", every: str = "", cron: str = "", preset: str = ""):
    """
    Set a reminder.
    Examples:
      assistant remind "Drink water" "in 10m"
      assistant remind "Standup" --cron "0 9 * * MON-FRI"
      assistant remind --preset eye-care
    """
    if preset:
        if preset.lower() == "eye-care":
            # Reusing eye_care logic (calling the function directly or duplicating for now)
            eye_care(reset=True)
            return
        else:
            print_error(f"Unknown preset: {preset}")
            return

    if not text:
        print_error("Missing argument 'TEXT'.")
        raise typer.Exit(1)

    if every:
        kwargs = parse_every(every)
        if not kwargs:
            print_error("Invalid --every. Try 30m, 2h, 1d, 1w.")
            raise typer.Exit(1)
        res = add_interval(text, **kwargs)
        print_success(f"Interval set: {res}")
        return

    if cron:
        res = add_cron(text, cron)
        print_success(f"CRON set: {res}")
        return

    dt, _ = parse_when(when)
    if not dt:
        print_error("Couldn’t parse 'when'.")
        raise typer.Exit(1)
    res = add_once(text, dt)
    print_success(f"Reminder set for {dt.strftime('%H:%M')}: {text}")

@app.command("eye-care")
def eye_care(times: str = "12:00,16:00,20:00", reset: bool = True):
    """
    Schedule eye-care reminders.
    """
    if reset:
        removed = cancel_prefix("eye_")
        # print_success(f"Removed {removed} existing eye-care jobs.") # Optional verbosity

    scheduled = []
    for t in [x.strip() for x in times.split(",") if x.strip()]:
        try:
            hh, mm = map(int, t.split(":"))
        except ValueError:
            print_error(f"Invalid time format: {t}. Use HH:MM (24h).")
            raise typer.Exit(1)
        job_id = f"eye_{hh:02d}{mm:02d}"
        res = add_daily("Use eye-cleaning product", hh, mm, job_id=job_id)
        scheduled.append((job_id, f"{hh:02d}:{mm:02d}"))

    table = create_table("Eye Care Schedule", ["Job ID", "Time"])
    for jid, at in scheduled:
        table.add_row(jid, at)
    print_table(table)
    print_success("Eye care reminders scheduled.")

@app.command("reminders")
def reminders_list():
    """List scheduled reminders/jobs."""
    rows = list_jobs()
    if not rows:
        print_warning("No active reminders.")
        return
    
    table = create_table("Active Reminders", ["ID", "Trigger", "Next Run"])
    for jid, trig, next_run in rows:
        table.add_row(jid, str(trig), str(next_run))
    print_table(table)

@app.command()
def cancel_job(job_id: str):
    """Cancel a scheduled job by id."""
    ok = cancel(job_id)
    typer.echo("Cancelled." if ok else "Not found.")

@app.command()
def movies(limit: int = 7, min_vote: float = 6.5, year_from: int = 2010):
    """Recommend top horror movies (TMDb)."""
    for m in top_horror(limit=limit, min_vote=min_vote, year_from=year_from):
        typer.echo(f"{m['title']} ({m['year']}) ★ {m['rating']}\n  {m['overview']}\n")

@app.command()
def prices(query: str, country: str = "", mode: str = ""):
    """
    Search prices. Modes: gaming, work.
    Example: assistant prices "rtx 4060" --mode gaming
    """
    # Simple query expansion based on mode
    if mode.lower() == "gaming":
        pass # query += " rtx" # Maybe too aggressive?
    elif mode.lower() == "work":
        pass 
        
    with console.status(f"[bold green]Searching for '{query}'..."):
        results = search_all(query, country_hint=country or None)

    if not results:
        print_warning("No results found.")
        return

    table = create_table(f"Results for '{query}'", ["Store", "Product", "Price", "Specs"])
    for p in results:
        specs_str = str(p.specs or "")[:50] # Truncate
        if len(str(p.specs or "")) > 50: specs_str += "..."
        
        table.add_row(
            f"[{p.country}] {p.store}",
            f"[link={p.url}]{p.title[:60]}...[/link]" if len(p.title) > 60 else f"[link={p.url}]{p.title}[/link]",
            f"[bold green]{p.price} {p.currency}[/bold green]",
            specs_str
        )
    print_table(table)

@app.command("pray")
def pray(city: str = "", country: str = "", method: int = 2, school: int = 0, schedule: bool = False):
    """Show prayer times."""
    city = city or settings.DEFAULT_CITY or "Casablanca"
    country = country or settings.DEFAULT_COUNTRY or "MA"
    
    with console.status("Fetching prayer times..."):
        times = get_today_timings(city, country, method, school)

    table = create_table(f"Prayer Times: {city}, {country}", ["Prayer", "Time"])
    for k in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
        table.add_row(k, times[k])
    print_table(table)

    if schedule:
        scheduled = schedule_today_prayers(city, country, method, school)
        if scheduled:
            print_success(f"Scheduled {len(scheduled)} prayers.")

@movies_app.command("list")
def movies_list(limit: int = 15, year_from: int = 2000, min_votes: int = 200, show_overview: bool = False):
    """List top-rated horror movies."""
    seen = is_seen_map()
    rows = top_horror(limit=limit, year_from=year_from, min_votes=min_votes)
    for idx, m in enumerate(rows, 1):
        star = "✓" if (m.imdb_id and m.imdb_id in seen) else " "
        if m.imdb_rating is not None and 0 < m.imdb_rating <= 10:
            rating = m.imdb_rating
            src = "IMDb"
        else:
            rating = m.tmdb_vote
            src = "TMDb (fallback)"
        typer.echo(f"{idx:2d}. [{star}] {m.title} ({m.year}) — {rating:.1f} {src}  [tmdb:{m.tmdb_id}{f', {m.imdb_id}' if m.imdb_id else ''}]")
        if show_overview and m.overview:
            typer.echo(f"    {m.overview}")
    

@movies_app.command("mark")
def movies_mark(imdb_id: str = "", tmdb_id: str = "", title: str = "", year: str = ""):
    """Mark as watched by IMDb id (ttxxxxxxx) or TMDb id (numeric) + optional title/year."""
    if not imdb_id and not tmdb_id:
        typer.echo("Provide --imdb-id or --tmdb-id")
        raise typer.Exit(1)

    if not imdb_id and tmdb_id:
        try:

            imdb_id = _tmdb_external_ids(tmdb_id).get("imdb_id") or ""
        except Exception:
            imdb_id = ""

    if not imdb_id:
        typer.echo("Could not resolve IMDb id; still marking with empty imdb_id (won't dedupe).")

    ok = mark_seen(tmdb_id or "", imdb_id or "", title or "", year or "")
    typer.echo("Marked." if ok else "Already marked.")

@movies_app.command("unmark")
def movies_unmark(imdb_id: str):
    """Remove a watched mark by IMDb id."""
    ok = unmark_seen(imdb_id)
    typer.echo("Removed." if ok else "Not found.")

@movies_app.command("watched")
def movies_watched():
    """Show your watched list (latest first)."""
    rows = all_seen()
    if not rows:
        typer.echo("No watched movies yet.")
        return
    for r in rows:
        typer.echo(f"✓ {r.title} ({r.year}) — {r.imdb_id or 'no-imdb'}  [tmdb:{r.tmdb_id}]  at {r.marked_at:%Y-%m-%d}")

@app.command("prices-gaming")
def prices_gaming(
    min_price: int = 1000,
    max_price: int = 2000,
    limit: int = 10,
    country: str = "FR",
    explain: bool = False,
    out: str | None = None,
):
    """
    Best gaming laptop deals scored by CPU/GPU(TGP)/Display/RAM/SSD/OS
    normalized by price. No hard GPU filter; uses value_score.

    Use --explain to print a per-item score breakdown.
    """

    queries = [
        "pc portable gamer rtx",
        # "gaming laptop rtx",
    ]

    def _specs_text(p):
            try:
                if isinstance(p.specs, dict):
                    # Safely get TGP if it exists
                    tgp = p.specs.get("tgp_w")
                    # Create a string of "key:value" for valid spec items
                    pairs = " ".join(f"{k}:{v}" for k, v in p.specs.items() if v)
                    extra = f" TGP {tgp}W" if tgp else ""
                    # Combine Title + Specs + Extra info
                    return (p.title + " " + pairs + extra).strip()
                
                # Fallback if specs is not a dict
                return (p.title + " " + str(p.specs or "")).strip()
            except Exception:
                return p.title

    # Robust generator: one adapter error shouldn't stop the whole run
    def _safe_iter_search(q: str):
        try:
            for p in search_all(q, country_hint=country):
                yield p
        except Exception as e:
            typer.secho(f"[prices-gaming] query {q!r} failed: {e}", fg="yellow")

    # Canonicalize URL for cross-query de-duplication
    def _canon(url: str) -> str:
        if not url:
            return ""
        base = url.split("?", 1)[0].rstrip("/")
        if "#mpos=" in base:
            base = base.split("#mpos=", 1)[0]
        return base

    seen, items = set(), []
    dbg_counts: dict[tuple[str, str], int] = {}
    dbg_dropped_price = 0
    dbg_total_seen = 0

    for q in queries:
        per_query_seen = 0
        for p in _safe_iter_search(q):
            dbg_total_seen += 1
            per_query_seen += 1
            price = getattr(p, "price", None)
            if not price or not (min_price <= price <= max_price):
                dbg_dropped_price += 1
                continue
            key = _canon(p.url or "")
            if not key or key in seen:
                continue
            seen.add(key)
            items.append(p)
            k = (q, getattr(p, "store", "?"))
            dbg_counts[k] = dbg_counts.get(k, 0) + 1
        typer.secho(f"[prices-gaming] {q!r}: considered {per_query_seen} items", fg="blue")

    if not items:
        typer.echo(
            f"No deals found between €{min_price}–€{max_price} in {country}. "
            f"(saw {dbg_total_seen}, dropped by price: {dbg_dropped_price})"
        )
        raise typer.Exit(0)

    # ---- rank & print --------------------------------------------------------
    items.sort(
        key=lambda p: value_score(p.title, _specs_text(p), p.price or 0.0),
        reverse=True,
    )
    results = items[:limit]

    # Helpful summary of which queries contributed
    typer.secho("Breakdown by query/store (kept after price filter & de-dupe):", fg="cyan")
    for (q, store), n in sorted(dbg_counts.items(), key=lambda x: (-x[1], x[0][0], x[0][1])):
        typer.echo(f"  • {store:10s} {n:3d} from {q!r}")
    typer.secho(
        f"Totals: kept={len(items)}  seen={dbg_total_seen}  dropped_by_price={dbg_dropped_price}\n",
        fg="cyan",
    )

    # Small helper to print a readable breakdown line
    def _pretty_breakdown(title: str, specs_text: str, price_eur: float) -> str:
            try:
                bd = value_breakdown(title, specs_text, price_eur)
            except Exception as e:
                return f"     ↳ (breakdown unavailable: {e})"

            # Compute component contributions (raw × weight)
            # Compute component contributions (raw × weight)
            # NOTE: benchmarks.py returns the *weighted* contribution in *_w keys.
            # We do NOT need to multiply raw * weight again.
            gpu_c = bd.get("gpu_w", 0)
            cpu_c = bd.get("cpu_w", 0)
            ram_c = bd.get("ram_w", 0)
            disp_c = bd.get("disp_w", 0)
            ssd_c = bd.get("ssd_w", 0)
            os_c = bd.get("os_w", 0)

            penalty  = bd.get("penalty", 0.0)
            score    = bd.get("score", 0.0)

            parts = [
                f"GPU({bd.get('gpu_raw',0):.0f})={gpu_c:.1f}",
                f"CPU({bd.get('cpu_raw',0):.0f})={cpu_c:.1f}",
                f"RAM(T{bd.get('ram_tier',0)})={ram_c:.1f}",
                f"SCR({bd.get('hz',0)}Hz/{bd.get('panel','')})={disp_c:.1f}",
                f"SSD({bd.get('storage_gb',0)})={ssd_c:.1f}",
                f"OS={os_c:.1f}",
            ]
            
            line = " | ".join(parts)
            
            # Show the formula: (sum of weighted components) / penalty
            raw_sum = gpu_c + cpu_c + ram_c + disp_c + ssd_c + os_c
            formula = f"({raw_sum:.2f} / {penalty:.2f})"
            
            return f"     ↳ {line} | Sum={raw_sum:.2f} | Pen={penalty:.2f} → {formula} = {score:.3f}"

    typer.echo(f"🎯 Best gaming laptop deals in {country} — €{min_price}–€{max_price}:")
    for i, p in enumerate(results, 1):
        gpu = p.specs.get("gpu") if isinstance(p.specs, dict) else None
        cpu = p.specs.get("cpu") if isinstance(p.specs, dict) else None
        specs_text = _specs_text(p)
        score = value_score(p.title, specs_text, p.price or 0.0)
        typer.echo(
            f"{i:2d}. [{p.store}] {p.title}\n"
            f"    {p.price:.0f} € — score {score:.3f}"
            f" — GPU: {gpu or '?'} — CPU: {cpu or '?'}\n"
            f"    {p.url}"
        )
        if explain:
            typer.echo(_pretty_breakdown(p.title, specs_text, p.price or 0.0))
        typer.echo("")  # blank line for readability
        # Build a clean, serializable payload for streamlit / later reuse
    payload = []
    for rank, p in enumerate(results, 1):
        specs_text = _specs_text(p)
        score = value_score(p.title, specs_text, p.price or 0.0)
        item = {
            "rank": rank,
            "store": p.store,
            "country": p.country,
            "title": p.title,
            "price_eur": float(p.price or 0.0),
            "currency": p.currency,
            "url": p.url,
            "specs": (p.specs if isinstance(p.specs, dict) else {"raw": str(p.specs)}),
            "score": float(score),
        }
        if explain:
            try:
                item["breakdown"] = value_breakdown(p.title, specs_text, p.price or 0.0)
            except Exception:
                item["breakdown"] = None
        payload.append(item)

    # Decide output path
    if out:
        out_path = Path(out)
    else:
        out_dir = Path(".scraper_artifacts")
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"prices_gaming_{ts}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        # ensure_ascii=False writes real UTF-8 (no \uXXXX escapes), good for FR text. :contentReference[oaicite:0]{index=0}
        json.dump(payload, f, indent=2, ensure_ascii=False)

    typer.secho(f"Saved {len(payload)} rows → {out_path}", fg="green")


@app.command("prices-debug")
def prices_debug(query: str, explain: bool = False):
    items = asyncio.run(search_all_async(query))

    # group by store
    by_store = defaultdict(list)
    for p in items:
        by_store[p.store].append(p)

    per_store = 10

    def _specs_text(p):
        # Build a compact text blob the scorer can use (title + specs + TGP if any)
        try:
            if isinstance(p.specs, dict):
                tgp = p.specs.get("tgp_w")
                spec_pairs = " ".join(f"{k}:{v}" for k, v in p.specs.items() if v)
                extra = f" TGP {tgp}W" if tgp else ""
                return (p.title + " " + spec_pairs + extra).strip()
            return (p.title + " " + str(p.specs or "")).strip()
        except Exception:
            return p.title

    # show top N per store, sorted by value_score
    for store in sorted(by_store.keys()):
        rows = by_store[store]
        rows = sorted(
            rows,
            key=lambda p: value_score(p.title, _specs_text(p), p.price or 0.0),
            reverse=True,
        )
        total = len(rows)
        typer.echo(f"\n[{store}] top {min(per_store, total)} of {total}")
        for p in rows[:per_store]:
            typer.echo(f"  • {p.title} | {p.price:.2f} € | GPU={p.specs.get('gpu')} | "
                       f"CPU={p.specs.get('cpu')} | {p.url}")
            if explain:
                bd = value_breakdown(p.title, _specs_text(p), p.price or 0.0)
                typer.echo(
                    "     ↳ score={score:.3f}  [gpu_raw={gpu_raw:.1f} (w={gpu_w:.2f}), "
                    "cpu_raw={cpu_raw:.1f} (w={cpu_w:.2f}), ram_tier={ram_tier} (w={ram_w:.2f}), "
                    "penalty={penalty:.2f}]".format(**bd)
                )

@app.command("prices-work")
def prices_work(
    min_price: int = 250,
    max_price: int = 700,
    limit: int = 10,
    country: str = "FR",
):
    """
    Best office/work laptop deals scored for productivity (CPU > Display > RAM > SSD > OS, tiny GPU bonus),
    normalized by price. No gaming-GPU filter.
    """

    # Broad, office-y queries (FR + generic)
    queries = [
        "pc portable bureautique",
        "pc portable travail",
        "ordinateur portable ssd 16 go",
        "ultrabook windows 11",
        "laptop i5 16gb",
        "laptop ryzen 7 16gb",
        "ordinateur portable professionnel",
    ]

    def _specs_text(p):
        try:
            if isinstance(p.specs, dict):
                tgp = p.specs.get("tgp_w")
                pairs = " ".join(f"{k}:{v}" for k, v in p.specs.items() if v)
                extra = f" TGP {tgp}W" if tgp else ""
                return (p.title + " " + pairs + extra).strip()
            return (p.title + " " + str(p.specs or "")).strip()
        except Exception:
            return p.title

    # collect, price-filter, de-dupe
    seen, items = set(), []
    for q in queries:
        for p in search_all(q, country_hint=country):
            price = getattr(p, "price", None)
            if not price or not (min_price <= price <= max_price):
                continue
            key = (p.url or "").split("?", 1)[0]
            if key in seen:
                continue
            seen.add(key)
            items.append(p)

    if not items:
        typer.echo(f"No work-laptop deals found between €{min_price}–€{max_price} in {country}.")
        raise typer.Exit(0)

    # rank by work-centric score
    items.sort(
        key=lambda p: value_score_work(p.title, _specs_text(p), p.price or 0.0),
        reverse=True,
    )
    results = items[:limit]

    typer.echo(f"🧑‍💼 Best work laptop deals in {country} — €{min_price}–€{max_price}:")
    for i, p in enumerate(results, 1):
        score = value_score_work(p.title, _specs_text(p), p.price or 0.0)
        cpu = (p.specs.get("cpu") if isinstance(p.specs, dict) else None) or "?"
        ram = "?"
        if isinstance(p.specs, dict):
            ram = p.specs.get("ram") or ram
        typer.echo(
            f"{i:2d}. [{p.store}] {p.title}\n"
            f"    {p.price:.0f} € — score {score:.3f} — CPU: {cpu}\n"
            f"    {p.url}\n"
        )

@app.command("refresh-cpu-bench")
def refresh_cpu_bench(from_html: str = typer.Option(
    None, "--from-html",
    help="Path to a locally saved PassMark laptop CPU page (HTML)."
)):
    """
    Fetch & cache a large laptop-CPU ranking table for scoring.
    If --from-html is provided, parse that local PassMark HTML instead of live web.
    """
    path = refresh_cpu_cache(passmark_html_path=from_html)
    typer.echo(f"CPU benchmark cache written to: {path}")

@app.command("refresh-gpu-bench")
def refresh_gpu_bench(
    from_html: str = typer.Option(
        None, "--from-html",
        help="Path to a locally saved PassMark GPU mega page (HTML)."
    )
):
    """
    Parse a locally saved PassMark GPU mega page and cache laptop/mobile GPU ranks (0..100).
    Also updates the SQL database for 'lookup_hardware' tool.
    """
    # 1. Update JSON Cache (0-100 normalization for scoring)
    path = refresh_gpu_cache(gpu_html_path=from_html)
    typer.echo(f"GPU benchmark cache written to: {path}")

    # 2. Update SQLite DB (Raw marks for lookup)
    if from_html:
        from assistant_app.services.ingestion.ingest_benchmarks import ingest_gpu_from_path
        ingest_gpu_from_path(Path(from_html))
        typer.echo("GPU SQLite database updated.")

@system_app.command()
def lock():
    """Lock the workstation instantly."""
    lock_screen()
    print_success("System locked.")

@system_app.command()
def volume(level: int):
    """Set system volume (0-100)."""
    if set_volume(level):
        print_success(f"Volume set to {level}%.")
    else:
        print_error("Failed to set volume.")

@system_app.command()
def open(app_name: str):
    """Open an application via search."""
    sys_open_app(app_name)
    print_success(f"Opening '{app_name}'...")

@system_app.command()
def minimize():
    """Minimize all windows (Show Desktop)."""
    minimize_all()
    print_success("Windows minimized.")

if __name__ == "__main__":
    app()
