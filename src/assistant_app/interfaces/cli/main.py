# src/assistant_app/interfaces/cli/main.py
import asyncio
from datetime import datetime, timedelta
import typer
from collections import defaultdict


# ── updated import paths to match your new layout ───────────────────────────────
from assistant_app.interfaces.scheduler.scheduler import scheduler

from assistant_app.services.memory import init_memory, set_pref, get_pref
from assistant_app.services.reminders import (
    add_once, add_interval, add_cron, list_jobs, cancel,
)
from assistant_app.adapters.nlu.time_parse import parse_when, parse_every

from assistant_app.services.movies import top_horror
from assistant_app.services.movies_seen import mark_seen, unmark_seen, all_seen, is_seen_map

from assistant_app.services.prayer import get_today_timings, schedule_today_prayers
from assistant_app.config.settings import settings

from assistant_app.domain.benchmarks import is_gpu_at_least_5060
from assistant_app.domain.benchmarks import value_score
from assistant_app.domain.benchmarks import value_breakdown
from assistant_app.domain.benchmarks import value_score_work
from assistant_app.domain.benchmarks_loader import refresh_cpu_cache
from assistant_app.domain.benchmarks_loader import refresh_gpu_cache

from assistant_app.services.prices import search_all
from assistant_app.usecases.search_prices import search_all_async
# ────────────────────────────────────────────────────────────────────────────────

app = typer.Typer(help="Local Desktop Assistant")
movies_app = typer.Typer(help="Movie suggestions & watched list")
app.add_typer(movies_app, name="movies")

@app.callback()
def _start():
    init_memory()
    # catch up missed jobs (<=10min late), then ensure scheduler is running
    for j in scheduler.get_jobs():
        if j.next_run_time and j.next_run_time < datetime.now() and datetime.now() - j.next_run_time < timedelta(minutes=10):
            try:
                j.func(**(j.kwargs or {}))
            except Exception as e:
                print("[catchup]", j.id, e)
    if not scheduler.running:
        scheduler.start()

@app.command()
def start():
    """Keep the assistant running in the background (scheduler, etc.)."""
    typer.echo("Assistant running. Press Ctrl+C to exit.")
    try:
        import time
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        typer.echo("Shutting down...")
        scheduler.shutdown()

@app.command()
def pref(key: str, value: str):
    """Set a preference. Example: assistant pref country MA"""
    set_pref(key, value)
    typer.echo(f"Set {key}={value}")

@app.command()
def remind(text: str, when: str = "", every: str = "", cron: str = ""):
    """
    Examples:
      assistant remind "Drink water" --every "2h"
      assistant remind "Call mom" "tomorrow 13:00"
      assistant remind "Standup" --cron "0 9 * * MON-FRI"
    """
    if every:
        kwargs = parse_every(every)
        if not kwargs:
            typer.echo("Invalid --every. Try 30m, 2h, 1d, 1w.")
            raise typer.Exit(1)
        res = add_interval(text, **kwargs)
        typer.echo(f"Interval: {res}")
        return

    if cron:
        res = add_cron(text, cron)
        typer.echo(f"CRON: {res}")
        return

    dt, _ = parse_when(when)
    if not dt:
        typer.echo("Couldn’t parse 'when'.")
        raise typer.Exit(1)
    res = add_once(text, dt)
    typer.echo(f"Once: {res}")

@app.command("eye-care")
def eye_care(times: str = "12:00,16:00,20:00", reset: bool = True):
    """
    Schedule eye-care reminders (default: daily at 12:00, 16:00, 20:00).
    """
    from assistant_app.services.reminders import add_daily, cancel_prefix

    if reset:
        removed = cancel_prefix("eye_")
        typer.echo(f"Removed {removed} existing eye-care jobs.")

    scheduled = []
    for t in [x.strip() for x in times.split(",") if x.strip()]:
        try:
            hh, mm = map(int, t.split(":"))
        except ValueError:
            typer.echo(f"Invalid time format: {t}. Use HH:MM (24h).")
            raise typer.Exit(1)
        job_id = f"eye_{hh:02d}{mm:02d}"
        res = add_daily("Use eye-cleaning product", hh, mm, job_id=job_id)
        scheduled.append((job_id, f"{hh:02d}:{mm:02d}"))

    typer.echo("Eye-care schedule:")
    for jid, at in scheduled:
        typer.echo(f"  {jid} -> daily at {at}")

@app.command("reminders")
def reminders_list():
    """List scheduled reminders/jobs."""
    rows = list_jobs()
    if not rows:
        typer.echo("No jobs.")
        return
    for jid, trig, next_run in rows:
        typer.echo(f"{jid} | {trig} | next: {next_run}")

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
def prices(query: str, country: str = ""):
    """Search laptop prices via your scraper plugins. Example: assistant prices "16GB i5" --country FR"""
    results = search_all(query, country_hint=country or None)
    if not results:
        typer.echo("No results (yet). Add scrapers in src/assistant_app/adapters/scrapers/")
        raise typer.Exit(0)
    for p in results:
        typer.echo(f"[{p.store} {p.country}] {p.title} — {p.price} {p.currency}\n  {p.url}\n  specs: {p.specs}\n")

@app.command("pray")
def pray(city: str = "", country: str = "", method: int = 2, school: int = 0, schedule: bool = False):
    """Show today's prayer times and optionally schedule the remaining ones."""
    city = city or "Casablanca"
    country = country or settings.DEFAULT_COUNTRY or "MA"
    times = get_today_timings(city, country, method, school)
    typer.echo(f"Prayer times for {city}, {country} (method {method}):")
    for k in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
        typer.echo(f"  {k}: {times[k]}")
    if schedule:
        scheduled = schedule_today_prayers(city, country, method, school)
        if scheduled:
            typer.echo("Scheduled:")
            for name, at in scheduled:
                typer.echo(f"  {name} at {at}")

@movies_app.command("list")
def movies_list(limit: int = 15, year_from: int = 2000, min_votes: int = 200, show_overview: bool = False):
    """List top-rated horror movies."""
    seen = is_seen_map()
    rows = top_horror(limit=limit, year_from=year_from, min_votes=min_votes)
    for idx, m in enumerate(rows, 1):
        star = "✓" if (m.imdb_id and m.imdb_id in seen) else " "
        rating = m.imdb_rating if m.imdb_rating is not None else m.tmdb_vote
        src = "IMDb" if m.imdb_rating is not None else "TMDb"
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
            from assistant_app.services.movies import _tmdb_external_ids
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
    min_price: int = 500,
    max_price: int = 1500,
    limit: int = 10,
    country: str = "FR",
):
    """
    Best gaming laptop deals scored by CPU/GPU(TGP)/Display/RAM/SSD/OS
    and normalized by price. No hard GPU filter; uses value_score.
    """

    # Use multiple phrasings so we don't depend on one SERP
    queries = [
        "pc portable gamer rtx",
        "pc portable gamer",
        "ordinateur portable gamer",
        "gaming laptop rtx",
        "gaming laptop",
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

    # Make generator robust: one bad adapter/regex shouldn't kill the loop
    def _safe_iter_search(q: str):
        try:
            for p in search_all(q, country_hint=country):
                yield p
        except Exception as e:
            # Keep going even if an adapter explodes (e.g. "no such group")
            typer.secho(f"[prices-gaming] query {q!r} failed: {e}", fg="yellow")

    # Canonicalize URL for de-dupe across queries/adapters
    def _canon(url: str) -> str:
        if not url:
            return ""
        base = url.split("?", 1)[0].rstrip("/")
        # strip cdiscount tracking anchors like #mpos=..|cd, keep stable path only
        if "#mpos=" in base:
            base = base.split("#mpos=", 1)[0]
        return base

    seen = set()
    items = []
    dbg_counts = {}           # (query, store) -> kept
    dbg_dropped_price = 0     # dropped due to price filter
    dbg_total_seen = 0

    for q in queries:
        per_query_seen = 0
        for p in _safe_iter_search(q):
            dbg_total_seen += 1
            per_query_seen += 1
            price = getattr(p, "price", None)

            # Price gate
            if not price or not (min_price <= price <= max_price):
                dbg_dropped_price += 1
                continue

            key = _canon(p.url or "")
            if not key or key in seen:
                continue
            seen.add(key)
            items.append(p)

            # per (query, store) accounting
            k = (q, getattr(p, "store", "?"))
            dbg_counts[k] = dbg_counts.get(k, 0) + 1

        typer.secho(f"[prices-gaming] {q!r}: considered {per_query_seen} items", fg="blue")

    if not items:
        typer.echo(f"No deals found between €{min_price}–€{max_price} in {country}. "
                   f"(saw {dbg_total_seen}, dropped by price: {dbg_dropped_price})")
        raise typer.Exit(0)

    # ---- rank & print --------------------------------------------------------
    items.sort(
        key=lambda p: value_score(p.title, _specs_text(p), p.price or 0.0),
        reverse=True,
    )
    results = items[:limit]

    # helpful summary so you can see “who contributed”
    typer.secho("Breakdown by query/store (kept after price filter & de-dupe):", fg="cyan")
    for (q, store), n in sorted(dbg_counts.items(), key=lambda x: (-x[1], x[0][0], x[0][1])):
        typer.echo(f"  • {store:10s}  {n:3d}  from {q!r}")
    typer.secho(f"Totals: kept={len(items)}  seen={dbg_total_seen}  dropped_by_price={dbg_dropped_price}\n", fg="cyan")

    typer.echo(f"🎯 Best gaming laptop deals in {country} — €{min_price}–€{max_price}:")
    for i, p in enumerate(results, 1):
        gpu = p.specs.get("gpu") if isinstance(p.specs, dict) else None
        cpu = p.specs.get("cpu") if isinstance(p.specs, dict) else None
        score = value_score(p.title, _specs_text(p), p.price or 0.0)
        typer.echo(
            f"{i:2d}. [{p.store}] {p.title}\n"
            f"    {p.price:.0f} € — score {score:.3f}"
            f" — GPU: {gpu or '?'} — CPU: {cpu or '?'}\n"
            f"    {p.url}\n"
        )




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
    """
    path = refresh_gpu_cache(gpu_html_path=from_html)
    typer.echo(f"GPU benchmark cache written to: {path}")

if __name__ == "__main__":
    app()
