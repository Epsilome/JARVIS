"""
JARVIS FastAPI Backend
Bridges Python assistant services to the Electron frontend.
"""

import sys
import os
import asyncio

# Load .env file for environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src to path so we can import assistant_app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import scheduled jobs (auto-registers daily cache refresh)
try:
    import assistant_app.services.cache_refresh
except ImportError:
    pass  # Should not happen, but safe to ignore if file missing

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="JARVIS API",
    description="Backend API for JARVIS Personal Assistant",
    version="1.0.0"
)

# CORS - Allow Electron/Vite dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELS ====================

class ChatRequest(BaseModel):
    message: str
    speak_response: bool = False  # If true, use Kokoro TTS to speak the response

class ChatResponse(BaseModel):
    response: str
    success: bool = True

class MovieItem(BaseModel):
    tmdb_id: str
    title: str
    year: str
    rating: Optional[float] = None
    poster: Optional[str] = None
    overview: str

class SystemHealth(BaseModel):
    cpu: float
    ram: float
    ram_used_gb: float
    ram_total_gb: float
    battery: str
    disk: float
    gpu: Optional[float] = None

# ==================== ENDPOINTS ====================

@app.get("/api/status")
async def get_status():
    """Health check / heartbeat endpoint."""
    return {"status": "online", "service": "JARVIS API"}


@app.get("/api/system", response_model=SystemHealth)
async def get_system_stats():
    """Get system health statistics (CPU, RAM, Battery, Disk)."""
    try:
        import psutil
        
        cpu_pct = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        ram_pct = mem.percent
        ram_used_gb = round(mem.used / (1024**3), 1)
        ram_total_gb = round(mem.total / (1024**3), 1)
        
        battery = psutil.sensors_battery()
        batt_str = "Desktop"
        if battery:
            plugged = "Charging" if battery.power_plugged else "Discharging"
            batt_str = f"{battery.percent}% ({plugged})"
        
        disk = psutil.disk_usage('/')
        
        # GPU Usage (NVIDIA via pynvml - more reliable than GPUtil)
        gpu_pct = None
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                # Get the last GPU (usually the dedicated NVIDIA GPU if Intel iGPU is GPU 0)
                handle = pynvml.nvmlDeviceGetHandleByIndex(device_count - 1)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_pct = util.gpu
            pynvml.nvmlShutdown()
        except Exception as e:
            logger.debug(f"GPU monitoring unavailable: {e}")
        
        return SystemHealth(
            cpu=cpu_pct,
            ram=ram_pct,
            ram_used_gb=ram_used_gb,
            ram_total_gb=ram_total_gb,
            battery=batt_str,
            disk=disk.percent,
            gpu=gpu_pct
        )
    except Exception as e:
        logger.error(f"System stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/movies", response_model=list[MovieItem])
async def get_movies(limit: int = 20, year_from: int = 2000, query: Optional[str] = None):
    """Fetch top horror movies or search TMDB."""
    try:
        from assistant_app.services.movies import top_horror, search_movies
        
        if query:
            movies = search_movies(query, limit=limit)
        else:
            movies = top_horror(limit=limit, year_from=year_from)
        
        return [
            MovieItem(
                tmdb_id=m.tmdb_id,
                title=m.title,
                year=m.year,
                rating=m.imdb_rating or m.tmdb_vote,
                poster=f"https://image.tmdb.org/t/p/w500{m.poster_path}" if m.poster_path else None,
                overview=m.overview
            )
            for m in movies
        ]
    except Exception as e:
        logger.error(f"Movies fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MOVIES WATCHED ====================

class MovieWatchedItem(BaseModel):
    tmdb_id: str
    imdb_id: str
    title: str
    year: str
    marked_at: Optional[str] = None

class MovieMarkRequest(BaseModel):
    tmdb_id: str
    imdb_id: str
    title: str
    year: str = ""

@app.get("/api/movies/watched", response_model=list[MovieWatchedItem])
async def get_watched_movies():
    """Get all movies marked as watched."""
    try:
        from assistant_app.services.movies_seen import all_seen
        movies = all_seen()
        return [
            MovieWatchedItem(
                tmdb_id=m.tmdb_id,
                imdb_id=m.imdb_id,
                title=m.title,
                year=m.year,
                marked_at=m.marked_at.isoformat() if m.marked_at else None
            )
            for m in movies
        ]
    except Exception as e:
        logger.error(f"Watched movies error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/movies/watched")
async def mark_movie_watched(movie: MovieMarkRequest):
    """Mark a movie as watched."""
    try:
        from assistant_app.services.movies_seen import mark_seen
        result = mark_seen(movie.tmdb_id, movie.imdb_id, movie.title, movie.year)
        return {"success": result, "message": "Movie marked as watched" if result else "Movie already in list"}
    except Exception as e:
        logger.error(f"Mark movie error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/movies/watched/{imdb_id}")
async def unmark_movie_watched(imdb_id: str):
    """Remove a movie from watched list."""
    try:
        from assistant_app.services.movies_seen import unmark_seen
        result = unmark_seen(imdb_id)
        return {"success": result, "message": "Movie removed" if result else "Movie not found"}
    except Exception as e:
        logger.error(f"Unmark movie error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message through JARVIS."""
    try:
        # Import the Ollama adapter for conversational AI
        from assistant_app.adapters.nlu.ollama_adapter import ask_ollama
        
        message = request.message.strip()
        if not message:
            return ChatResponse(response="Please provide a message.", success=False)
        
        # Simple keyword handling for common commands
        msg_lower = message.lower()
        
        # Prayer times
        if any(k in msg_lower for k in ["prayer", "fajr", "isha", "maghrib"]):
            from assistant_app.services.prayer import get_today_timings
            from assistant_app.config.settings import settings
            city = settings.DEFAULT_CITY or "Casablanca"
            country = settings.DEFAULT_COUNTRY or "MA"
            times = get_today_timings(city, country, 2, 0)
            prayer_str = ", ".join([f"{k}: {times[k]}" for k in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]])
            return ChatResponse(response=f"Prayer times for {city}: {prayer_str}")
        
        # System status
        if any(k in msg_lower for k in ["system", "cpu", "ram", "health"]):
            from assistant_app.adapters.system_health import get_system_health
            health = get_system_health()
            if request.speak_response:
                from assistant_app.adapters.nlu.tts_kokoro import speak
                speak(health)
            return ChatResponse(response=health)
        
        # Fallback to Ollama LLM
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, ask_ollama, message)
        
        if response:
            # Speak response if requested (voice mode)
            if request.speak_response:
                from assistant_app.adapters.nlu.tts_kokoro import speak
                # Run TTS in background thread to not block response
                loop.run_in_executor(None, speak, response)
            return ChatResponse(response=response)
        else:
            return ChatResponse(response="I'm sorry, I couldn't process that request.", success=False)
            
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(response=f"Error: {str(e)}", success=False)


# ==================== WEATHER ====================

class WeatherResponse(BaseModel):
    city: str
    temp: float
    description: str
    humidity: int
    country: str

@app.get("/api/weather", response_model=WeatherResponse)
async def get_weather(city: str = "Casablanca", country: str = "MA"):
    """Get current weather for a city."""
    try:
        from assistant_app.services.weather_service import get_weather_sync
        w = get_weather_sync(city, country)
        return WeatherResponse(
            city=w['city'],
            temp=w['temp'],
            description=w['description'],
            humidity=w['humidity'],
            country=w.get('country', country)
        )
    except Exception as e:
        logger.error(f"Weather error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PRAYER TIMES ====================

class PrayerTimesResponse(BaseModel):
    city: str
    fajr: str
    dhuhr: str
    asr: str
    maghrib: str
    isha: str

@app.get("/api/prayer", response_model=PrayerTimesResponse)
async def get_prayer_times(city: str = "Casablanca", country: str = "MA"):
    """Get today's prayer times for a city."""
    try:
        from assistant_app.services.prayer import get_today_timings
        times = get_today_timings(city, country, 2, 0)
        return PrayerTimesResponse(
            city=city,
            fajr=times.get("Fajr", ""),
            dhuhr=times.get("Dhuhr", ""),
            asr=times.get("Asr", ""),
            maghrib=times.get("Maghrib", ""),
            isha=times.get("Isha", "")
        )
    except Exception as e:
        logger.error(f"Prayer times error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== REMINDERS ====================

class ReminderItem(BaseModel):
    job_id: str
    trigger: str
    next_run: Optional[str] = None

class ReminderCreate(BaseModel):
    text: str
    hour: int
    minute: int

class ReminderResponse(BaseModel):
    job_id: str
    message: str
    when: str

@app.get("/api/reminders", response_model=list[ReminderItem])
async def list_reminders():
    """Get all active reminders."""
    try:
        from assistant_app.interfaces.scheduler.scheduler import scheduler
        
        # Ensure scheduler is started
        if not scheduler.running:
            scheduler.start()
        
        jobs = scheduler.get_jobs()
        result = []
        for j in jobs:
            next_run = None
            try:
                next_run = str(j.next_run_time) if j.next_run_time else None
            except:
                pass
            result.append(ReminderItem(
                job_id=str(j.id) if j.id else "unknown",
                trigger=str(j.trigger) if j.trigger else "unknown",
                next_run=next_run
            ))
        return result
    except Exception as e:
        logger.error(f"List reminders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reminders", response_model=ReminderResponse)
async def create_reminder(reminder: ReminderCreate):
    """Create a daily reminder at specified time."""
    try:
        from assistant_app.services.reminders import add_daily
        result = add_daily(reminder.text, reminder.hour, reminder.minute)
        return ReminderResponse(
            job_id=result.job_id,
            message=result.message,
            when=result.when
        )
    except Exception as e:
        logger.error(f"Create reminder error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/reminders/{job_id}")
async def delete_reminder(job_id: str):
    """Cancel a reminder by job ID."""
    try:
        from assistant_app.services.reminders import cancel
        success = cancel(job_id)
        return {"success": success, "job_id": job_id}
    except Exception as e:
        logger.error(f"Delete reminder error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NOTES ====================

class NoteItem(BaseModel):
    id: int
    content: str
    created_at: str

class NoteCreate(BaseModel):
    content: str

@app.get("/api/notes", response_model=list[NoteItem])
async def list_notes():
    """Get all saved notes."""
    try:
        from assistant_app.services.memory import get_notes_db
        notes = get_notes_db()
        return [NoteItem(**n) for n in notes]
    except Exception as e:
        logger.error(f"List notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/notes")
async def create_note(note: NoteCreate):
    """Create a new note."""
    try:
        from assistant_app.services.memory import add_note_db
        result = add_note_db(note.content)
        return {"success": True, "message": result}
    except Exception as e:
        logger.error(f"Create note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: int):
    """Delete a note by ID."""
    try:
        from assistant_app.services.memory import delete_note_db
        success = delete_note_db(note_id)
        return {"success": success, "note_id": note_id}
    except Exception as e:
        logger.error(f"Delete note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== VOLUME CONTROL ====================

class VolumeRequest(BaseModel):
    level: int  # 0-100

@app.post("/api/volume")
async def set_volume(request: VolumeRequest):
    """Set system volume level (0-100)."""
    try:
        from assistant_app.adapters.system_control import set_volume as sys_set_volume
        result = sys_set_volume(request.level)
        return {"success": True, "level": request.level, "message": result}
    except Exception as e:
        logger.error(f"Volume control error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/media/{action}")
async def control_media(action: str):
    """Control media playback. Actions: play_pause, next, prev, stop, mute"""
    try:
        from assistant_app.adapters.system_control import control_media as sys_control_media
        result = sys_control_media(action)
        return {"success": True, "action": action, "message": result}
    except Exception as e:
        logger.error(f"Media control error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PRICES ====================

class ProductItem(BaseModel):
    name: str
    price: Optional[float] = None
    url: Optional[str] = None
    store: Optional[str] = None
    currency: str = "EUR"

class PricesResponse(BaseModel):
    query: str
    category: str
    results: list[ProductItem]
    count: int

@app.get("/api/prices", response_model=PricesResponse)
async def search_prices(query: str, category: str = "general"):
    """Search for product prices across multiple stores."""
    try:
        from assistant_app.services.prices import search_all_async
        
        # Add category-specific keywords
        final_query = query
        if category == "gaming":
            if "rtx" not in query.lower() and "gtx" not in query.lower() and "gaming" not in query.lower():
                final_query += " rtx"
        elif category == "work":
            terms = ["professionnel", "pro", "business", "thinkpad"]
            if not any(t in query.lower() for t in terms):
                final_query += " professionnel"
        
        # Use async version directly - no asyncio.run() needed
        products = await search_all_async(final_query)
        
        # Filter by price based on category
        filtered = []
        for p in products:
            price = getattr(p, "price", 0.0) or 0.0
            if category == "gaming" and price < 400:
                continue
            if category == "work" and price < 200:
                continue
            filtered.append(ProductItem(
                name=getattr(p, "name", "Unknown"),
                price=getattr(p, "price", None),
                url=getattr(p, "url", None),
                store=getattr(p, "store", None),
                currency=getattr(p, "currency", "EUR")
            ))
        
        return PricesResponse(
            query=query,
            category=category,
            results=filtered[:20],  # Limit to 20 results
            count=len(filtered)
        )
    except Exception as e:
        logger.error(f"Prices search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LAPTOPS (with scoring) ====================

class LaptopItem(BaseModel):
    name: str
    price: Optional[float]
    url: Optional[str]
    store: Optional[str]
    score: Optional[float]
    cpu: Optional[str]
    gpu: Optional[str]
    ram: Optional[str]
    storage: Optional[str]
    display: Optional[str]

class LaptopsResponse(BaseModel):
    query: str
    category: str
    budget: int
    results: list[LaptopItem]
    count: int

@app.get("/api/laptops", response_model=LaptopsResponse)
async def search_laptops(query: str = "", category: str = "gaming", budget: int = 1500):
    """Search for laptops with value scoring."""
    try:
        from assistant_app.services.prices import search_products
        from assistant_app.domain.benchmarks import value_breakdown, match_cpu, match_gpu
        import re
        
        # Build search query - ALWAYS include laptop keywords
        base_term = "pc portable"  # French for laptop
        
        if category == "gaming":
            category_term = "gamer rtx"
        elif category == "work":
            category_term = "professionnel"
        else:
            category_term = ""
        
        # User query (brand/model filter)
        user_query = query.strip() if query else ""
        
        # Combine: "pc portable gamer rtx lenovo" for gaming lenovo search
        search_term = f"{base_term} {category_term} {user_query}".strip()
        
        logger.info(f"Laptop search: '{search_term}', budget={budget}")
        
        # Run scraper in thread pool
        loop = asyncio.get_running_loop()
        products = await loop.run_in_executor(None, search_products, search_term, category, "FR")
        
        if not products:
            return LaptopsResponse(query=query, category=category, budget=budget, results=[], count=0)
        
        # Keywords that indicate a product is actually a laptop
        laptop_keywords = [
            "laptop", "portable", "notebook", "pc portable", "ordinateur portable",
            "gaming", "gamer", "vivobook", "ideapad", "thinkpad", "legion", "nitro",
            "aspire", "pavilion", "envy", "spectre", "zenbook", "tuf", "rog", "predator",
            "katana", "raider", "cyborg", "creator", "swift", "chromebook", "surface laptop",
            "macbook", "inspiron", "latitude", "precision", "xps", "g15", "g16", "loq"
        ]
        
        # Keywords that indicate NOT a laptop (exclude these)
        exclude_keywords = [
            "iphone", "ipad", "smartphone", "tablette", "tablet", "écran", "monitor",
            "souris", "mouse", "clavier", "keyboard", "casque", "headset", "webcam",
            "imprimante", "printer", "lave-linge", "washing", "aspirateur", "vacuum",
            "fourchette", "fork", "cuiseur", "cooker", "refrigerateur", "fridge",
            "accessoire", "housse", "case", "sac", "bag", "chargeur standalone",
            "batterie externe", "power bank", "câble", "cable", "adaptateur seul",
            "support", "stand", "dock seul", "hub seul", "mini cooper", "voiture"
        ]
        
        # Filter and score
        scored_results = []
        for p in products:
            price = p.price or 0
            title = (p.title or p.name or "").lower()
            
            # Skip if price out of range
            if price > budget or price < 200:
                continue
            
            # Skip if contains exclude keywords
            if any(kw in title for kw in exclude_keywords):
                continue
            
            # Only include if contains laptop keywords OR has CPU/GPU
            has_laptop_keyword = any(kw in title for kw in laptop_keywords)
            has_cpu = match_cpu(title) is not None
            has_gpu = match_gpu(title) is not None
            
            if not (has_laptop_keyword or has_cpu or has_gpu):
                continue
            
            specs = getattr(p, "description", "") or ""
            
            try:
                breakdown = value_breakdown(p.title or p.name or "", specs, price)
                cpu = match_cpu(p.title or "") or ""
                gpu = match_gpu(p.title or "") or ""
                
                # Format RAM/Storage/Display from breakdown
                ram_labels = {0: "8GB", 1: "16GB", 2: "32GB", 3: "64GB+"}
                ram = ram_labels.get(breakdown.get("ram_tier", 0), "?GB")
                storage = f"{breakdown.get('storage_gb', 0)}GB" if breakdown.get('storage_gb', 0) > 0 else ""
                display = f"{breakdown.get('hz', 0)}Hz" if breakdown.get('hz', 0) > 0 else ""
                
                scored_results.append({
                    "product": p,
                    "score": breakdown.get("score", 0),
                    "cpu": cpu,
                    "gpu": gpu,
                    "ram": ram,
                    "storage": storage,
                    "display": display
                })
            except Exception as e:
                logger.debug(f"Scoring error for {title}: {e}")
                scored_results.append({
                    "product": p,
                    "score": 0,
                    "cpu": "", "gpu": "", "ram": "", "storage": "", "display": ""
                })
        
        # Sort by score
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Build response
        results = []
        for item in scored_results[:20]:
            p = item["product"]
            results.append(LaptopItem(
                name=p.title or p.name or "Unknown",
                price=p.price,
                url=getattr(p, "url", None),
                store=getattr(p, "store", None),
                score=item["score"],
                cpu=item["cpu"],
                gpu=item["gpu"],
                ram=item["ram"],
                storage=item["storage"],
                display=item["display"]
            ))
        
        return LaptopsResponse(
            query=query,
            category=category,
            budget=budget,
            results=results,
            count=len(results)
        )
    except Exception as e:
        logger.error(f"Laptop search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WAKE WORD ====================

from fastapi import WebSocket, WebSocketDisconnect
import threading

# Global state for wake word
wake_word_listener = None
wake_word_active = False
connected_websockets: list[WebSocket] = []

def wake_word_loop():
    """Background thread that listens for wake word and notifies connected clients."""
    global wake_word_listener, wake_word_active
    
    try:
        from assistant_app.adapters.nlu.wake_word import WakeWordListener
        wake_word_listener = WakeWordListener()
        
        if not wake_word_listener.porcupine:
            logger.error("Wake word engine failed to initialize")
            return
            
        logger.info("Wake word thread started")
        
        while wake_word_active:
            # Check for wake word (blocking with timeout)
            try:
                if wake_word_listener.porcupine:
                    pcm = wake_word_listener.audio_stream.read(
                        wake_word_listener.porcupine.frame_length,
                        exception_on_overflow=False
                    )
                    import struct
                    pcm = struct.unpack_from("h" * wake_word_listener.porcupine.frame_length, pcm)
                    
                    keyword_index = wake_word_listener.porcupine.process(pcm)
                    if keyword_index >= 0:
                        logger.info("🎤 Wake word 'Jarvis' detected!")
                        # Notify all connected WebSocket clients
                        for ws in connected_websockets[:]:
                            try:
                                import asyncio
                                asyncio.run(ws.send_json({"event": "wake_word", "keyword": "jarvis"}))
                            except Exception as e:
                                logger.debug(f"Failed to notify client: {e}")
            except Exception as e:
                logger.debug(f"Wake word loop iteration error: {e}")
                
    except Exception as e:
        logger.error(f"Wake word thread error: {e}")
    finally:
        if wake_word_listener:
            wake_word_listener.close()
        logger.info("Wake word thread stopped")

@app.post("/api/wake-word/start")
async def start_wake_word():
    """Start listening for wake word in background."""
    global wake_word_active
    
    if wake_word_active:
        return {"status": "already_running", "message": "Wake word detection is already active"}
    
    wake_word_active = True
    thread = threading.Thread(target=wake_word_loop, daemon=True)
    thread.start()
    
    return {"status": "started", "message": "Wake word detection started. Say 'Jarvis' to activate."}

@app.post("/api/wake-word/stop")
async def stop_wake_word():
    """Stop wake word detection."""
    global wake_word_active
    
    wake_word_active = False
    return {"status": "stopped", "message": "Wake word detection stopped"}

@app.get("/api/wake-word/status")
async def wake_word_status():
    """Get wake word detection status."""
    return {"active": wake_word_active, "keyword": "jarvis"}

@app.websocket("/ws/wake-word")
async def websocket_wake_word(websocket: WebSocket):
    """WebSocket endpoint for real-time wake word notifications."""
    await websocket.accept()
    connected_websockets.append(websocket)
    logger.info(f"Wake word WebSocket connected. Total connections: {len(connected_websockets)}")
    
    try:
        while True:
            # Keep connection alive, receive any client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)
        logger.info(f"Wake word WebSocket disconnected. Total connections: {len(connected_websockets)}")


# ==================== HARDWARE COMPARE ====================

class HardwareItem(BaseModel):
    name: str
    type: str  # cpu, gpu, ssd, ram
    score: Optional[float] = None
    specs: Dict[str, Any] = {}

class HardwareSearchResponse(BaseModel):
    query: str
    results: list[HardwareItem]
    count: int

class HardwareCompareResponse(BaseModel):
    items: list[HardwareItem]

@app.get("/api/hardware/search", response_model=HardwareSearchResponse)
async def search_hardware(query: str, type: str = "all"):
    """Search for hardware components by name."""
    try:
        from assistant_app.domain.benchmarks import (
            GPU_ALIASES, gpu_score, cpu_score, get_gpu_specs, get_cpu_specs
        )
        
        results = []
        query_lower = query.lower().strip()
        
        if len(query_lower) < 2:
            return HardwareSearchResponse(query=query, results=[], count=0)
        
        # Search GPUs first (most common use case)
        if type in ["all", "gpu"]:
            # Search GPU_ALIASES
            for short_name, full_name in GPU_ALIASES.items():
                if query_lower in short_name or query_lower in full_name.lower():
                    score = gpu_score(full_name) or 0
                    specs = get_gpu_specs(full_name) or {}
                    results.append(HardwareItem(
                        name=short_name.upper(),
                        type="gpu",
                        score=score,
                        specs={
                            "full_name": full_name,
                            "vram": specs.get("vram"),
                            "tdp": specs.get("tdp")
                        }
                    ))
        
        # Search CPUs - common patterns
        if type in ["all", "cpu"]:
            # Common CPU patterns to search
            cpu_patterns = [
                "i9-14900", "i9-13900", "i7-14700", "i7-13700", "i7-12700",
                "i5-14600", "i5-13600", "i5-12600", "i5-14400", "i5-13400",
                "ryzen 9 7945hx", "ryzen 9 7940hx", "ryzen 7 7840hs", "ryzen 7 7840hx",
                "ryzen 7 7735hs", "ryzen 5 7640hs", "ryzen 5 7535hs",
                "ultra 9 185h", "ultra 7 155h", "ultra 5 125h",
            ]
            for cpu_name in cpu_patterns:
                if query_lower in cpu_name.lower():
                    score = cpu_score(cpu_name) or 0
                    specs = get_cpu_specs(cpu_name) or {}
                    results.append(HardwareItem(
                        name=cpu_name.upper(),
                        type="cpu",
                        score=score,
                        specs=specs
                    ))
        
        # Sort by score descending, remove zero scores
        results = [r for r in results if r.score and r.score > 0]
        results.sort(key=lambda x: x.score or 0, reverse=True)
        
        return HardwareSearchResponse(
            query=query,
            results=results[:30],
            count=len(results)
        )
    except Exception as e:
        logger.error(f"Hardware search error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/hardware/compare", response_model=HardwareCompareResponse)
async def compare_hardware(names: list[str] = Body(...)):
    """Compare multiple hardware items by name."""
    try:
        from assistant_app.domain.benchmarks import get_cpu_specs, get_gpu_specs
        
        results = []
        for name in names[:4]:  # Max 4 items
            # Try CPU first
            cpu_data = get_cpu_specs(name)
            if cpu_data:
                results.append(HardwareItem(
                    name=name,
                    type="cpu",
                    score=cpu_data.get('passmark', cpu_data.get('score', 0)),
                    specs=cpu_data
                ))
                continue
            
            # Try GPU
            gpu_data = get_gpu_specs(name)
            if gpu_data:
                results.append(HardwareItem(
                    name=name,
                    type="gpu",
                    score=gpu_data.get('passmark', gpu_data.get('g3d_mark', 0)),
                    specs=gpu_data
                ))
                continue
            
            # Not found
            results.append(HardwareItem(name=name, type="unknown", score=0, specs={}))
        
        return HardwareCompareResponse(items=results)
    except Exception as e:
        logger.error(f"Hardware compare error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class HardwareDatabaseResponse(BaseModel):
    cpus: list[dict]
    gpus: list[dict]
    ssds: list[dict]
    ram: list[dict]
    total: int

@app.get("/api/hardware/database", response_model=HardwareDatabaseResponse)
async def get_hardware_database(type: str = "all", limit: int = 100):
    """Load hardware data from PassMark CSV files for browsing."""
    import csv
    from pathlib import Path
    
    base_path = Path(__file__).parent.parent / "data"
    cpus, gpus, ssds, ram_items = [], [], [], []
    
    try:
        # Load CPUs from PassMark CSV (primary source with real benchmark scores)
        if type in ["all", "cpu"]:
            cpu_path = base_path / "passmark_cpus.csv"
            if cpu_path.exists():
                with open(cpu_path, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        name = row.get('name', '').strip()
                        score = int(row.get('score', 0) or 0)
                        if name:
                            cpus.append({
                                'name': name,
                                'type': 'cpu',
                                'score': score,
                                'specs': {'brand': 'Intel' if 'Intel' in name else 'AMD' if any(x in name for x in ['AMD', 'Ryzen', 'EPYC', 'Athlon']) else 'Other'}
                            })
            cpus = cpus[:limit]
        
        # Load GPUs from PassMark CSV
        if type in ["all", "gpu"]:
            gpu_path = base_path / "passmark_gpus.csv"
            if gpu_path.exists():
                with open(gpu_path, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        name = row.get('name', '').strip()
                        score = int(row.get('score', 0) or 0)
                        if name:
                            gpus.append({
                                'name': name,
                                'type': 'gpu',
                                'score': score,
                                'specs': {'brand': 'NVIDIA' if any(x in name for x in ['GeForce', 'RTX', 'GTX', 'Quadro', 'Tesla']) else 'AMD' if 'Radeon' in name else 'Intel' if 'Intel' in name else 'Other'}
                            })
            gpus = gpus[:limit]
        
        # Load SSDs from PassMark CSV (has real benchmark scores)
        if type in ["all", "ssd"]:
            ssd_path = base_path / "passmark_ssds.csv"
            if ssd_path.exists():
                with open(ssd_path, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        name = row.get('name', '').strip()
                        score = int(row.get('score', 0) or 0)
                        if name:
                            ssds.append({
                                'name': name,
                                'type': 'ssd',
                                'score': score,
                                'specs': {}
                            })
            ssds = ssds[:limit]
        
        # Load RAM from DDR5.csv and DDR4.csv (keep existing - no PassMark data available)
        if type in ["all", "ram"]:
            for ram_file in ["DDR5.csv", "DDR4.csv"]:
                ram_path = base_path / "ram_specs" / ram_file
                if ram_path.exists():
                    with open(ram_path, 'r', encoding='utf-8', errors='ignore') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            name = row.get('Memory Name', '').strip()
                            if not name:
                                continue
                            latency = row.get('Latency (ns)', '')
                            read_speed = row.get('Read Uncached (GB/s)', '')
                            write_speed = row.get('Write (GB/s)', '')
                            price = row.get('Price (USD)', '')
                            # Score based on read speed
                            score = 0
                            if read_speed:
                                try:
                                    score = int(float(read_speed.replace(',', '').strip()) * 100)
                                except:
                                    pass
                            ram_items.append({
                                'name': name,
                                'type': 'ram',
                                'score': score,
                                'specs': {
                                    'latency': latency,
                                    'read_speed': read_speed,
                                    'write_speed': write_speed,
                                    'price': price
                                }
                            })
            ram_items.sort(key=lambda x: x.get('score', 0) or 0, reverse=True)
            ram_items = ram_items[:limit]
        
        total = len(cpus) + len(gpus) + len(ssds) + len(ram_items)
        return HardwareDatabaseResponse(cpus=cpus, gpus=gpus, ssds=ssds, ram=ram_items, total=total)
    
    except Exception as e:
        logger.error(f"Hardware database error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CONFIG ====================

class ConfigResponse(BaseModel):
    default_city: str
    default_country: str
    tts_enabled: bool
    tts_voice: str
    theme_accent: str
    ollama_model: str
    stt_model: str
    tts_model: str
    api_keys_status: Dict[str, bool]

class ConfigUpdate(BaseModel):
    default_city: Optional[str] = None
    default_country: Optional[str] = None
    tts_enabled: Optional[bool] = None
    tts_voice: Optional[str] = None
    theme_accent: Optional[str] = None

def _read_env_file():
    """Read .env file as dict."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    env_dict = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_dict[key.strip()] = value.strip()
    return env_dict, env_path

def _write_env_file(env_dict, env_path):
    """Write dict back to .env file."""
    with open(env_path, 'w') as f:
        for key, value in env_dict.items():
            f.write(f"{key}={value}\n")

@app.get("/api/config", response_model=ConfigResponse)
async def get_config():
    """Get current configuration."""
    try:
        env_dict, _ = _read_env_file()
        
        return ConfigResponse(
            default_city=env_dict.get('DEFAULT_CITY', 'Casablanca'),
            default_country=env_dict.get('DEFAULT_COUNTRY', 'MA'),
            tts_enabled=env_dict.get('TTS_ENABLED', 'true').lower() == 'true',
            tts_voice=env_dict.get('TTS_VOICE', 'af_bella'),
            theme_accent=env_dict.get('THEME_ACCENT', 'cyan'),
            ollama_model=env_dict.get('OLLAMA_MODEL', 'qwen2.5:3b'),
            stt_model='large-v3-turbo',  # Faster Whisper model
            tts_model='Kokoro',  # Kokoro TTS engine
            api_keys_status={
                "tmdb": bool(env_dict.get('TMDB_API_KEY')),
                "weather": bool(env_dict.get('DEFAULT_CITY')),  # Weather works via wttr.in without API key
                "porcupine": bool(env_dict.get('PORCUPINE_ACCESS_KEY')),
                "tavily": bool(env_dict.get('TAVILY_API_KEY')),
            }
        )
    except Exception as e:
        logger.error(f"Config read error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config")
async def update_config(update: ConfigUpdate):
    """Update configuration and persist to .env."""
    try:
        env_dict, env_path = _read_env_file()
        
        if update.default_city is not None:
            env_dict['DEFAULT_CITY'] = update.default_city
        if update.default_country is not None:
            env_dict['DEFAULT_COUNTRY'] = update.default_country
        if update.tts_enabled is not None:
            env_dict['TTS_ENABLED'] = 'true' if update.tts_enabled else 'false'
        if update.tts_voice is not None:
            env_dict['TTS_VOICE'] = update.tts_voice
        if update.theme_accent is not None:
            env_dict['THEME_ACCENT'] = update.theme_accent
        
        _write_env_file(env_dict, env_path)
        
        # Hot-reload TTS if voice changed
        if update.tts_voice is not None:
            try:
                from assistant_app.adapters.nlu.tts_kokoro import reload_voice
                reload_voice(update.tts_voice)
                logger.info(f"TTS voice hot-reloaded to: {update.tts_voice}")
            except Exception as e:
                logger.warning(f"Could not hot-reload TTS voice: {e}")
        
        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        logger.error(f"Config update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Available Kokoro voices for the UI
KOKORO_VOICES = [
    {"id": "af_bella", "name": "Bella (Female)", "language": "en"},
    {"id": "af_nicole", "name": "Nicole (Female)", "language": "en"},
    {"id": "af_sarah", "name": "Sarah (Female)", "language": "en"},
    {"id": "am_adam", "name": "Adam (Male)", "language": "en"},
    {"id": "am_michael", "name": "Michael (Male)", "language": "en"},
    {"id": "bf_emma", "name": "Emma (British Female)", "language": "en-gb"},
    {"id": "bm_george", "name": "George (British Male)", "language": "en-gb"},
]

@app.get("/api/config/voices")
async def get_available_voices():
    """Get list of available TTS voices."""
    return {"voices": KOKORO_VOICES}


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting JARVIS API Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

