/**
 * API Client for JARVIS Backend
 * Provides methods to communicate with the FastAPI server.
 */

const API_BASE = 'http://localhost:8000';

// ==================== STATUS ====================

export async function getStatus() {
    const res = await fetch(`${API_BASE}/api/status`);
    if (!res.ok) throw new Error('API offline');
    return res.json();
}

// ==================== SYSTEM ====================

export async function getSystemHealth() {
    const res = await fetch(`${API_BASE}/api/system`);
    if (!res.ok) throw new Error('Failed to fetch system stats');
    return res.json();
}

// ==================== MOVIES ====================

export async function getMovies(limit = 20, query = '') {
    const url = query
        ? `${API_BASE}/api/movies?query=${encodeURIComponent(query)}&limit=${limit}`
        : `${API_BASE}/api/movies?limit=${limit}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch movies');
    return res.json();
}

// ==================== CHAT ====================

export async function sendChat(message, speakResponse = false) {
    const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, speak_response: speakResponse })
    });
    if (!res.ok) throw new Error('Chat request failed');
    return res.json();
}

// ==================== WEATHER ====================

export async function getWeather(city = 'Casablanca', country = 'MA') {
    const res = await fetch(`${API_BASE}/api/weather?city=${city}&country=${country}`);
    if (!res.ok) throw new Error('Failed to fetch weather');
    return res.json();
}

// ==================== PRAYER TIMES ====================

export async function getPrayerTimes(city = 'Casablanca', country = 'MA') {
    const res = await fetch(`${API_BASE}/api/prayer?city=${city}&country=${country}`);
    if (!res.ok) throw new Error('Failed to fetch prayer times');
    return res.json();
}

// ==================== REMINDERS ====================

export async function getReminders() {
    const res = await fetch(`${API_BASE}/api/reminders`);
    if (!res.ok) throw new Error('Failed to fetch reminders');
    return res.json();
}

export async function createReminder(text, hour, minute) {
    const res = await fetch(`${API_BASE}/api/reminders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, hour, minute })
    });
    if (!res.ok) throw new Error('Failed to create reminder');
    return res.json();
}

export async function deleteReminder(jobId) {
    const res = await fetch(`${API_BASE}/api/reminders/${jobId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete reminder');
    return res.json();
}

// ==================== NOTES ====================

export async function getNotes() {
    const res = await fetch(`${API_BASE}/api/notes`);
    if (!res.ok) throw new Error('Failed to fetch notes');
    return res.json();
}

export async function createNote(content) {
    const res = await fetch(`${API_BASE}/api/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
    });
    if (!res.ok) throw new Error('Failed to create note');
    return res.json();
}

export async function deleteNote(noteId) {
    const res = await fetch(`${API_BASE}/api/notes/${noteId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete note');
    return res.json();
}

// ==================== VOLUME & MEDIA ====================

export async function setVolume(level) {
    const res = await fetch(`${API_BASE}/api/volume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level })
    });
    if (!res.ok) throw new Error('Failed to set volume');
    return res.json();
}

export async function controlMedia(action) {
    const res = await fetch(`${API_BASE}/api/media/${action}`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to control media');
    return res.json();
}

// ==================== PRICES ====================

export async function searchPrices(query, category = 'general') {
    const res = await fetch(`${API_BASE}/api/prices?query=${encodeURIComponent(query)}&category=${category}`);
    if (!res.ok) throw new Error('Failed to search prices');
    return res.json();
}

// ==================== MOVIES WATCHED ====================

export async function getWatchedMovies() {
    const res = await fetch(`${API_BASE}/api/movies/watched`);
    if (!res.ok) throw new Error('Failed to get watched movies');
    return res.json();
}

export async function markMovieWatched(tmdbId, imdbId, title, year) {
    const res = await fetch(`${API_BASE}/api/movies/watched`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tmdb_id: tmdbId, imdb_id: imdbId, title, year })
    });
    if (!res.ok) throw new Error('Failed to mark movie');
    return res.json();
}

export async function unmarkMovieWatched(imdbId) {
    const res = await fetch(`${API_BASE}/api/movies/watched/${imdbId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to unmark movie');
    return res.json();
}

// ==================== LAPTOPS / PRICES ====================

export async function getLaptops(query = 'laptop gamer', category = 'gaming', budget = 1500) {
    const url = `${API_BASE}/api/laptops?query=${encodeURIComponent(query)}&category=${category}&budget=${budget}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch laptops');
    return res.json();
}

// ==================== WAKE WORD ====================

export async function startWakeWord() {
    const res = await fetch(`${API_BASE}/api/wake-word/start`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to start wake word');
    return res.json();
}

export async function stopWakeWord() {
    const res = await fetch(`${API_BASE}/api/wake-word/stop`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to stop wake word');
    return res.json();
}

export async function getWakeWordStatus() {
    const res = await fetch(`${API_BASE}/api/wake-word/status`);
    if (!res.ok) throw new Error('Failed to get wake word status');
    return res.json();
}

// WebSocket URL for wake word
export const WAKE_WORD_WS_URL = 'ws://localhost:8000/ws/wake-word';

// ==================== HARDWARE ====================

export async function searchHardware(query, type = 'all') {
    const res = await fetch(`${API_BASE}/api/hardware/search?query=${encodeURIComponent(query)}&type=${type}`);
    if (!res.ok) throw new Error('Failed to search hardware');
    return res.json();
}

export async function compareHardware(names) {
    const res = await fetch(`${API_BASE}/api/hardware/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(names)
    });
    if (!res.ok) throw new Error('Failed to compare hardware');
    return res.json();
}

export async function getHardwareDatabase(type = 'all', limit = 100) {
    const res = await fetch(`${API_BASE}/api/hardware/database?type=${type}&limit=${limit}`);
    if (!res.ok) throw new Error('Failed to get hardware database');
    return res.json();
}

// ==================== CONFIG ====================

export async function getConfig() {
    const res = await fetch(`${API_BASE}/api/config`);
    if (!res.ok) throw new Error('Failed to get config');
    return res.json();
}

export async function updateConfig(updates) {
    const res = await fetch(`${API_BASE}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
    });
    if (!res.ok) throw new Error('Failed to update config');
    return res.json();
}

export async function getAvailableVoices() {
    const res = await fetch(`${API_BASE}/api/config/voices`);
    if (!res.ok) throw new Error('Failed to get voices');
    return res.json();
}
