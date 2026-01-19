import React, { useState, useEffect } from 'react';
import { Mic, Home, Settings, Activity, Bell, FileText, Film, Send, Laptop, Scale } from 'lucide-react';
import VoiceVisualizer from './components/VoiceVisualizer';
import ChatWindow from './components/ChatWindow';
import MovieCard from './components/MovieCard';
import NotesPanel from './components/NotesPanel';
import RemindersPanel from './components/RemindersPanel';
import WeatherWidget from './components/WeatherWidget';
import SystemPanel from './components/SystemPanel';
import PricesPanel from './components/PricesPanel';
import ComparePanel from './components/ComparePanel';
import ConfigPanel from './components/ConfigPanel';
import { getMovies, sendChat, getStatus, markMovieWatched, unmarkMovieWatched, getWatchedMovies, startWakeWord, stopWakeWord, WAKE_WORD_WS_URL } from './api';

// Draggable Title Bar
const TitleBar = ({ apiStatus }) => (
    <div className="h-8 flex items-center px-4 space-x-4 border-b border-jarvis-cyan/30 bg-jarvis-black/80 select-none z-50 relative" style={{ WebkitAppRegion: 'drag' }}>
        <div className={`w-1 h-4 ${apiStatus === 'online' ? 'bg-jarvis-cyan' : 'bg-red-500'} animate-pulse glow-accent-sm`}></div>
        <div className="text-jarvis-cyan text-[10px] font-orbitron tracking-widest flex-1 opacity-80">
            SYSTEM STATUS: {apiStatus === 'online' ? 'NOMINAL' : 'OFFLINE'} // PROTOCOL 7: ACTIVE // {apiStatus === 'online' ? 'CONNECTED' : 'DISCONNECTED'}
        </div>
        <div className="flex space-x-2" style={{ WebkitAppRegion: 'no-drag' }}>
            <div className="w-2 h-2 rounded-full bg-jarvis-cyan/50 hover:bg-jarvis-cyan cursor-pointer transition-colors glow-accent-sm"></div>
            <div className="w-2 h-2 rounded-full bg-red-500/50 hover:bg-red-500 cursor-pointer transition-colors shadow-[0_0_5px_#ff0000]"></div>
        </div>
    </div>
);

// Navigation Rail
const NavRail = ({ active, setActive }) => {
    const items = [
        { id: 'home', icon: Home, label: 'HOME' },
        { id: 'movies', icon: Film, label: 'MOVIES' },
        { id: 'prices', icon: Laptop, label: 'LAPTOPS' },
        { id: 'compare', icon: Scale, label: 'COMPARE' },
        { id: 'system', icon: Activity, label: 'SYSTEM' },
        { id: 'notes', icon: FileText, label: 'NOTES' },
        { id: 'reminders', icon: Bell, label: 'REMIND' },
        { id: 'settings', icon: Settings, label: 'CONFIG' },
    ];

    return (
        <div className="w-20 bg-black/60 border-r border-jarvis-cyan/20 flex flex-col items-center py-4 space-y-6 backdrop-blur-md relative z-40 overflow-y-auto min-h-0">
            <div className="absolute right-0 top-0 bottom-0 w-[1px] bg-gradient-to-b from-transparent via-jarvis-cyan/50 to-transparent"></div>
            {items.map((item) => {
                const Icon = item.icon;
                const isActive = active === item.id;
                return (
                    <div
                        key={item.id}
                        className={`group flex flex-col items-center cursor-pointer transition-all duration-300 ${isActive ? '' : 'opacity-40 hover:opacity-80'}`}
                        onClick={() => setActive(item.id)}
                    >
                        <div className={`p-3 rounded-lg mb-2 relative transition-all duration-300 ${isActive ? 'bg-jarvis-cyan/10 glow-accent border border-jarvis-cyan/30' : 'border border-transparent'}`}>
                            <Icon size={22} className={isActive ? 'text-jarvis-cyan' : 'text-cyan-100'} />
                            {isActive && <div className="absolute inset-0 bg-jarvis-cyan/10 blur-sm rounded-lg"></div>}
                        </div>
                        <span className={`text-[9px] font-orbitron tracking-widest transition-colors ${isActive ? 'text-jarvis-cyan' : 'text-gray-400'}`}>
                            {item.label}
                        </span>
                    </div>
                );
            })}
        </div>
    );
};

// System Monitor Component
const SystemMonitor = ({ stats, loading }) => {
    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <div className="text-jarvis-cyan animate-pulse font-orbitron">LOADING SYSTEM DATA...</div>
            </div>
        );
    }

    if (!stats) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <div className="text-red-400 font-orbitron">SYSTEM OFFLINE</div>
            </div>
        );
    }

    const StatBar = ({ label, value, color = 'jarvis-cyan' }) => (
        <div className="mb-6">
            <div className="flex justify-between text-xs mb-2">
                <span className="text-gray-400 font-orbitron tracking-wider">{label}</span>
                <span className={`text-${color}`}>{value}%</span>
            </div>
            <div className="h-2 bg-black/60 rounded-full overflow-hidden border border-jarvis-cyan/20">
                <div
                    className={`h-full bg-gradient-to-r from-${color}/50 to-${color} transition-all duration-500`}
                    style={{ width: `${value}%` }}
                ></div>
            </div>
        </div>
    );

    return (
        <div className="flex-1 p-6 animate-in fade-in duration-500">
            <h2 className="text-2xl font-orbitron text-jarvis-cyan mb-6 tracking-wider border-b border-jarvis-cyan/20 pb-2">
                SYSTEM DIAGNOSTICS
            </h2>
            <div className="grid grid-cols-2 gap-8">
                <div className="border border-jarvis-cyan/20 rounded-xl p-6 bg-black/40 backdrop-blur-md">
                    <StatBar label="CPU LOAD" value={stats.cpu} />
                    <StatBar label="RAM USAGE" value={stats.ram} />
                    <StatBar label="DISK USAGE" value={stats.disk} />
                </div>
                <div className="border border-jarvis-cyan/20 rounded-xl p-6 bg-black/40 backdrop-blur-md space-y-4">
                    <div className="flex justify-between items-center py-3 border-b border-jarvis-cyan/10">
                        <span className="text-gray-400 text-sm font-orbitron">BATTERY</span>
                        <span className="text-jarvis-cyan font-mono">{stats.battery}</span>
                    </div>
                    <div className="flex justify-between items-center py-3 border-b border-jarvis-cyan/10">
                        <span className="text-gray-400 text-sm font-orbitron">RAM USED</span>
                        <span className="text-jarvis-cyan font-mono">{stats.ram_used_gb} / {stats.ram_total_gb} GB</span>
                    </div>
                    <div className="flex justify-between items-center py-3">
                        <span className="text-gray-400 text-sm font-orbitron">API STATUS</span>
                        <span className="text-green-400 font-mono">ONLINE</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

const App = () => {
    const [activeTab, setActiveTab] = useState('home');
    const [isListening, setIsListening] = useState(false);
    const [apiStatus, setApiStatus] = useState('checking');
    const [messages, setMessages] = useState([
        { sender: 'jarvis', text: 'Protocol 7 initiated. Cyber-security subsystems are online. Awaiting directive.' },
    ]);
    const [inputText, setInputText] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [movies, setMovies] = useState([]);
    const [moviesLoading, setMoviesLoading] = useState(false);
    const [watchedList, setWatchedList] = useState(new Set());
    const [systemStats, setSystemStats] = useState(null);
    const [systemLoading, setSystemLoading] = useState(false);

    // Voice Mode State
    const [voiceModeEnabled, setVoiceModeEnabled] = useState(false);
    const [wakeWordActive, setWakeWordActive] = useState(false);


    // Handler to mark movie as watched
    const handleMarkWatched = async (tmdbId, imdbId, title, year, shouldMark) => {
        try {
            if (shouldMark) {
                await markMovieWatched(tmdbId, imdbId || `tt${tmdbId}`, title, year);
                setWatchedList(prev => new Set([...prev, imdbId || `tt${tmdbId}`]));
            } else {
                await unmarkMovieWatched(imdbId || `tt${tmdbId}`);
                setWatchedList(prev => {
                    const next = new Set(prev);
                    next.delete(imdbId || `tt${tmdbId}`);
                    return next;
                });
            }
        } catch (err) {
            console.error('Mark watched error:', err);
        }
    };

    // Check API status on mount
    // Check API status on mount
    useEffect(() => {
        const checkApi = async () => {
            try {
                await getStatus();
                setApiStatus('online');
            } catch {
                setApiStatus('offline');
            }
        };
        checkApi();

        // Initial fetch
        fetchMovies();

        // Fetch movies watched
        const fetchWatched = async () => {
            try {
                const watched = await getWatchedMovies();
                setWatchedList(new Set(watched.map(m => m.imdb_id)));
            } catch (e) {
                console.error("Failed to load watched movies", e);
            }
        };
        fetchWatched();
    }, []);

    // Debounced Search Effect
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchMovies(searchQuery);
        }, 500);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    const fetchMovies = async (query = '') => {
        setMoviesLoading(true);
        try {
            const data = await getMovies(20, query);
            setMovies(data);
        } catch (error) {
            console.error('Failed to fetch movies:', error);
        }
        setMoviesLoading(false);
    };

    // Voice Mode WebSocket Connection
    useEffect(() => {
        if (!voiceModeEnabled) return;

        let ws = null;
        let reconnectTimer = null;

        const connect = () => {
            ws = new WebSocket(WAKE_WORD_WS_URL);

            ws.onopen = () => {
                console.log('Wake word WebSocket connected');
                setWakeWordActive(true);
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.event === 'wake_word') {
                        console.log('🎤 Wake word detected! Starting voice recognition...');
                        // Trigger the actual mic activation (speech recognition)
                        // We use a custom event since toggleMic isn't in scope here
                        window.dispatchEvent(new CustomEvent('jarvis-wake-word'));
                    }
                } catch (e) {
                    console.error('Wake word message parse error:', e);
                }
            };

            ws.onclose = () => {
                console.log('Wake word WebSocket disconnected');
                setWakeWordActive(false);
                // Reconnect if still enabled
                if (voiceModeEnabled) {
                    reconnectTimer = setTimeout(connect, 3000);
                }
            };

            ws.onerror = (e) => {
                console.error('Wake word WebSocket error:', e);
            };
        };

        // Start wake word detection on backend
        startWakeWord()
            .then(() => connect())
            .catch(e => console.error('Failed to start wake word:', e));

        return () => {
            if (ws) ws.close();
            if (reconnectTimer) clearTimeout(reconnectTimer);
            stopWakeWord().catch(e => console.error('Failed to stop wake word:', e));
        };
    }, [voiceModeEnabled]);

    const toggleVoiceMode = () => {
        setVoiceModeEnabled(prev => !prev);
    };

    // Listen for wake word event and trigger mic activation
    useEffect(() => {
        const handleWakeWord = () => {
            console.log('Wake word event received, triggering toggleMic');
            // Directly call the speech recognition logic
            if (!isListening) {
                toggleMicRef.current?.();
            }
        };

        window.addEventListener('jarvis-wake-word', handleWakeWord);
        return () => window.removeEventListener('jarvis-wake-word', handleWakeWord);
    }, [isListening]);

    // Reference to toggleMic for wake word access
    const toggleMicRef = React.useRef(null);

    // Keep ref updated with latest toggleMic function
    useEffect(() => {
        toggleMicRef.current = toggleMic;
    });

    // Fetch system stats when System tab is active
    useEffect(() => {
        if (activeTab === 'system') {
            const fetchStats = async () => {
                setSystemLoading(true);
                try {
                    const stats = await getSystemHealth();
                    setSystemStats(stats);
                } catch (err) {
                    console.error('System stats fetch failed:', err);
                }
                setSystemLoading(false);
            };
            fetchStats();
            const interval = setInterval(fetchStats, 5000);
            return () => clearInterval(interval);
        }
    }, [activeTab]);

    const handleSendMessage = async () => {
        if (!inputText.trim()) return;

        const userMessage = inputText.trim();
        setInputText('');
        setMessages(prev => [...prev, { sender: 'user', text: userMessage }]);

        try {
            // Pass voiceModeEnabled to trigger TTS on response
            const response = await sendChat(userMessage, voiceModeEnabled);
            setMessages(prev => [...prev, { sender: 'jarvis', text: response.response }]);
        } catch (err) {
            setMessages(prev => [...prev, { sender: 'jarvis', text: 'Error: Unable to process request. Is the API server running?' }]);
        }
    };

    // Web Speech API for voice recognition
    const toggleMic = () => {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            setMessages(prev => [...prev, {
                sender: 'jarvis',
                text: 'Speech recognition is not supported in this browser. Please use Chrome or Edge.'
            }]);
            return;
        }

        if (isListening) {
            setIsListening(false);
            return;
        }

        setIsListening(true);
        setMessages(prev => [...prev, { sender: 'jarvis', text: '🎤 Listening... Speak now.' }]);

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.continuous = false;
        recognition.interimResults = true; // Show partial results
        recognition.maxAlternatives = 1;

        let finalTranscript = '';
        let hasResult = false;

        recognition.onresult = (event) => {
            let interimTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                    hasResult = true;
                } else {
                    interimTranscript += transcript;
                }
            }
        };

        recognition.onend = async () => {
            setIsListening(false);

            if (hasResult && finalTranscript.trim()) {
                // Remove the "Listening..." message and add actual transcript
                setMessages(prev => {
                    const filtered = prev.filter(m => m.text !== '🎤 Listening... Speak now.');
                    return [...filtered, { sender: 'user', text: finalTranscript }];
                });

                // Send to API with TTS if in voice mode
                try {
                    const response = await sendChat(finalTranscript, voiceModeEnabled);
                    setMessages(prev => [...prev, { sender: 'jarvis', text: response.response }]);
                } catch (err) {
                    setMessages(prev => [...prev, { sender: 'jarvis', text: 'Error processing voice command.' }]);
                }
            } else {
                // Remove the "Listening..." message
                setMessages(prev => prev.filter(m => m.text !== '🎤 Listening... Speak now.'));
            }
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            setIsListening(false);

            // Remove listening message
            setMessages(prev => prev.filter(m => m.text !== '🎤 Listening... Speak now.'));

            // Show helpful error messages based on error type
            const errorMessages = {
                'no-speech': 'No speech detected. Please click the mic and speak clearly.',
                'aborted': 'Voice input was cancelled.',
                'audio-capture': 'No microphone found. Please check your microphone settings.',
                'not-allowed': 'Microphone access denied. Please allow microphone permissions.',
                'network': 'Network error. Please check your internet connection.'
            };

            const message = errorMessages[event.error] || `Voice error: ${event.error}`;
            setMessages(prev => [...prev, { sender: 'jarvis', text: message }]);
        };

        try {
            recognition.start();
        } catch (err) {
            setIsListening(false);
            setMessages(prev => [...prev, { sender: 'jarvis', text: 'Failed to start voice recognition.' }]);
        }
    };

    return (
        <div className="bg-[#050505] w-screen h-screen text-white overflow-hidden font-mono selection:bg-jarvis-cyan/30 selection:text-white flex flex-col">
            {/* Ambient Background Glow */}
            <div className="absolute top-0 left-0 w-1/2 h-1/2 bg-blue-900/10 blur-[80px] pointer-events-none rounded-full"></div>
            <div className="absolute bottom-0 right-0 w-1/2 h-1/2 bg-jarvis-cyan/5 blur-[80px] pointer-events-none rounded-full"></div>

            {/* Border Frame */}
            <div className="absolute inset-0 border border-jarvis-cyan/50 rounded-lg pointer-events-none z-[60]"></div>

            <TitleBar apiStatus={apiStatus} />

            <div className="flex-1 grid grid-cols-[80px_1fr] overflow-hidden min-h-0 relative">
                <NavRail active={activeTab} setActive={setActiveTab} />

                <main className="relative flex flex-col p-6 space-y-4 min-h-0 overflow-hidden">

                    {activeTab === 'home' && (
                        <>
                            {/* Weather Widget - Top Right */}
                            <div className="absolute top-6 right-6 w-72 z-10">
                                <WeatherWidget />
                            </div>

                            <div className="flex-1 min-h-0 flex flex-col pr-80">
                                <ChatWindow messages={messages} />
                            </div>

                            {/* Chat Input */}
                            <div className="h-12 shrink-0 flex items-center gap-3 border border-jarvis-cyan/30 bg-black/40 rounded-lg px-4 backdrop-blur-md">
                                <input
                                    type="text"
                                    value={inputText}
                                    onChange={(e) => setInputText(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                                    placeholder="Enter command..."
                                    className="flex-1 bg-transparent border-none outline-none text-white placeholder:text-gray-500 font-mono"
                                />
                                <button
                                    onClick={handleSendMessage}
                                    className="p-2 hover:bg-jarvis-cyan/10 rounded-lg transition-colors"
                                >
                                    <Send size={18} className="text-jarvis-cyan" />
                                </button>
                            </div>

                            {/* Visualizer */}
                            <div className="h-32 shrink-0 relative flex flex-col items-center justify-center border border-jarvis-cyan/30 bg-black/40 rounded-xl overflow-hidden backdrop-blur-md">
                                <div className="absolute top-3 left-5 text-[10px] text-jarvis-cyan/80 font-bold tracking-widest font-orbitron flex items-center">
                                    <span className={`w-2 h-2 rounded-full mr-2 ${isListening ? 'bg-red-500 animate-pulse' : 'bg-gray-600'}`}></span>
                                    AUDIO: {isListening ? 'ACTIVE' : 'STANDBY'}
                                </div>
                                <div className="w-full h-full pt-6 pb-10 px-12">
                                    <VoiceVisualizer isActive={isListening} />
                                </div>

                                {/* Voice Mode Toggle */}
                                <div
                                    onClick={toggleVoiceMode}
                                    className={`absolute bottom-3 left-5 px-3 py-1.5 rounded-full border text-[9px] font-orbitron tracking-wider cursor-pointer transition-all duration-300 ${voiceModeEnabled ? 'border-green-500 bg-green-500/20 text-green-400' : 'border-gray-600 bg-black/40 text-gray-500 hover:border-jarvis-cyan/50'}`}
                                >
                                    {voiceModeEnabled ? '🎤 VOICE ACTIVE' : '🔇 WAKE WORD OFF'}
                                </div>

                                {/* Mic Button */}
                                <div onClick={toggleMic} className={`absolute bottom-3 w-12 h-12 rounded-full border-2 flex items-center justify-center cursor-pointer transition-all duration-300 z-50 ${isListening ? 'border-jarvis-alert bg-jarvis-alert/10 scale-110' : 'border-jarvis-cyan bg-jarvis-cyan/5 hover:scale-105'}`}>
                                    <Mic size={20} className={isListening ? 'text-jarvis-alert' : 'text-jarvis-cyan'} />
                                </div>
                            </div>
                        </>
                    )}

                    {activeTab === 'movies' && (
                        <div className="flex-1 overflow-y-auto pr-2 animate-in slide-in-from-bottom duration-500">
                            <div className="flex justify-between items-end mb-6 border-b border-jarvis-cyan/20 pb-2">
                                <h2 className="text-2xl font-orbitron text-jarvis-cyan tracking-wider">
                                    HORROR VAULT // <span className="text-sm text-gray-400">{moviesLoading ? 'LOADING...' : `${movies.length} ENTRIES`}</span>
                                </h2>
                                <div className="relative">
                                    <input
                                        type="text"
                                        placeholder="SEARCH ARCHIVES..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="bg-black/50 border border-jarvis-cyan/30 text-jarvis-cyan px-3 py-1 rounded text-sm font-mono focus:outline-none focus:border-jarvis-cyan w-64 placeholder-jarvis-cyan/30"
                                    />
                                    <div className="absolute right-2 top-1.5 w-2 h-2 rounded-full bg-jarvis-cyan/50 animate-pulse"></div>
                                </div>
                            </div>

                            {moviesLoading ? (
                                <div className="flex items-center justify-center h-64">
                                    <div className="text-jarvis-cyan animate-pulse font-orbitron">
                                        {searchQuery ? 'SEARCHING DATABASE...' : 'FETCHING DATA FROM TMDB...'}
                                    </div>
                                </div>
                            ) : (
                                <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 pb-10">
                                    {movies.map((m, i) => (
                                        <MovieCard
                                            key={i}
                                            title={m.title}
                                            year={m.year}
                                            rating={m.rating?.toFixed(1)}
                                            posterUrl={m.poster}
                                            overview={m.overview}
                                            tmdbId={m.tmdb_id}
                                            imdbId={m.imdb_id || `tt${m.tmdb_id}`}
                                            isWatched={watchedList.has(m.imdb_id || `tt${m.tmdb_id}`)}
                                            onMarkWatched={handleMarkWatched}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'prices' && (
                        <PricesPanel />
                    )}

                    {activeTab === 'system' && (
                        <SystemPanel />
                    )}

                    {activeTab === 'notes' && (
                        <NotesPanel />
                    )}

                    {activeTab === 'reminders' && (
                        <RemindersPanel />
                    )}

                    {activeTab === 'compare' && (
                        <ComparePanel />
                    )}

                    {activeTab === 'settings' && (
                        <ConfigPanel />
                    )}
                </main>
            </div>

            <div
                className="absolute inset-0 pointer-events-none z-50 opacity-[0.03]"
                style={{
                    backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 240, 255, 0.03) 2px, rgba(0, 240, 255, 0.03) 4px)',
                    backgroundSize: '100% 4px'
                }}
            ></div>
        </div>
    );
};

export default App;
