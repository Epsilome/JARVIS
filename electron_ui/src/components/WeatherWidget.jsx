import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Cloud, Sun, CloudRain, Snowflake, Wind, RefreshCw, MapPin, Moon } from 'lucide-react';
import { getWeather, getPrayerTimes } from '../api';

// Animated Weather Icon Components
const AnimatedSun = () => (
    <div className="relative w-8 h-8">
        <motion.div
            className="absolute inset-0 flex items-center justify-center"
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        >
            <Sun className="text-yellow-400" size={32} />
        </motion.div>
        <motion.div
            className="absolute inset-0 rounded-full"
            style={{ backgroundColor: 'rgba(250, 204, 21, 0.3)' }}
            animate={{ scale: [1, 1.3, 1], opacity: [0.3, 0.1, 0.3] }}
            transition={{ duration: 2, repeat: Infinity }}
        />
    </div>
);

const AnimatedRain = () => (
    <div className="relative w-8 h-8 overflow-hidden">
        <Cloud className="text-gray-400 relative z-10" size={28} />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-4 overflow-hidden">
            {[0, 1, 2].map(i => (
                <motion.div
                    key={i}
                    className="absolute w-0.5 h-2 bg-blue-400 rounded-full"
                    style={{ left: `${i * 8 + 4}px` }}
                    animate={{ y: [-8, 16], opacity: [1, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.2 }}
                />
            ))}
        </div>
    </div>
);

const AnimatedSnow = () => (
    <div className="relative w-8 h-8 overflow-hidden">
        <Cloud className="text-gray-300 relative z-10" size={28} />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-6 overflow-hidden">
            {[0, 1, 2, 3].map(i => (
                <motion.div
                    key={i}
                    className="absolute w-1.5 h-1.5 bg-white rounded-full"
                    style={{ left: `${i * 7 + 2}px` }}
                    animate={{ y: [-6, 20], x: [0, 3, -3, 0], opacity: [1, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.3 }}
                />
            ))}
        </div>
    </div>
);

const AnimatedCloudy = () => (
    <div className="relative w-8 h-8">
        <motion.div
            animate={{ x: [-2, 2, -2] }}
            transition={{ duration: 4, repeat: Infinity }}
        >
            <Cloud className="text-gray-300" size={32} />
        </motion.div>
    </div>
);

const AnimatedWind = () => (
    <div className="relative w-8 h-8">
        <Wind className="text-cyan-300" size={32} />
        {[0, 1, 2].map(i => (
            <motion.div
                key={i}
                className="absolute h-0.5 bg-cyan-300/50 rounded-full"
                style={{ top: `${10 + i * 8}px`, left: 0, width: `${12 + i * 4}px` }}
                animate={{ x: [0, 20], opacity: [0, 1, 0] }}
                transition={{ duration: 1, repeat: Infinity, delay: i * 0.3 }}
            />
        ))}
    </div>
);

const WeatherWidget = () => {
    const [weather, setWeather] = useState(null);
    const [prayerTimes, setPrayerTimes] = useState(null);
    const [nextPrayer, setNextPrayer] = useState(null);
    const [loading, setLoading] = useState(false);
    const [city, setCity] = useState('Casablanca');

    const fetchData = async () => {
        setLoading(true);
        try {
            const [weatherData, prayerData] = await Promise.all([
                getWeather(city.trim(), ''),
                getPrayerTimes(city.trim(), '')
            ]);
            setWeather(weatherData);
            setPrayerTimes(prayerData);
        } catch (err) {
            console.error(err);
        }
        setLoading(false);
    };

    // Calculate next prayer
    useEffect(() => {
        if (!prayerTimes) return;

        const calculateNextPrayer = () => {
            const now = new Date();
            const currentMinutes = now.getHours() * 60 + now.getMinutes();

            // API returns lowercase: fajr, dhuhr, asr, maghrib, isha
            const prayers = [
                { name: 'Fajr', key: 'fajr' },
                { name: 'Dhuhr', key: 'dhuhr' },
                { name: 'Asr', key: 'asr' },
                { name: 'Maghrib', key: 'maghrib' },
                { name: 'Isha', key: 'isha' }
            ];

            for (const prayer of prayers) {
                const time = prayerTimes[prayer.key];
                if (time) {
                    const [h, m] = time.split(':').map(Number);
                    const prayerMinutes = h * 60 + m;
                    if (prayerMinutes > currentMinutes) {
                        const diffMinutes = prayerMinutes - currentMinutes;
                        const hours = Math.floor(diffMinutes / 60);
                        const mins = diffMinutes % 60;
                        setNextPrayer({
                            name: prayer.name,
                            time: time,
                            countdown: hours > 0 ? `${hours}h ${mins}m` : `${mins}m`
                        });
                        return;
                    }
                }
            }
            // All prayers passed, show Fajr for tomorrow
            setNextPrayer({
                name: 'Fajr',
                time: prayerTimes.fajr,
                countdown: 'tomorrow'
            });
        };

        calculateNextPrayer();
        const interval = setInterval(calculateNextPrayer, 60000);
        return () => clearInterval(interval);
    }, [prayerTimes]);

    useEffect(() => {
        fetchData();
    }, []);

    const getWeatherIcon = (description) => {
        const desc = description?.toLowerCase() || '';
        if (desc.includes('rain') || desc.includes('drizzle')) return <AnimatedRain />;
        if (desc.includes('snow')) return <AnimatedSnow />;
        if (desc.includes('cloud')) return <AnimatedCloudy />;
        if (desc.includes('wind')) return <AnimatedWind />;
        return <AnimatedSun />;
    };

    const accentStyle = { color: 'var(--accent-color)' };
    const borderStyle = { border: '1px solid rgba(var(--accent-color-rgb), 0.3)' };
    const borderDimStyle = { border: '1px solid rgba(var(--accent-color-rgb), 0.2)' };

    return (
        <div className="space-y-4 mb-4">
            {/* Weather Card */}
            <div
                className="rounded-xl p-4 bg-black/40 backdrop-blur-md"
                style={borderStyle}
            >
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-orbitron tracking-wider flex items-center gap-2" style={accentStyle}>
                        <Cloud size={16} />
                        WEATHER
                    </h3>
                    <button
                        onClick={fetchData}
                        disabled={loading}
                        className="p-1.5 rounded-lg transition-colors disabled:opacity-50 hover:bg-white/5"
                    >
                        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} style={accentStyle} />
                    </button>
                </div>

                {/* City Input */}
                <div className="flex gap-2 mb-3">
                    <div className="relative flex-1">
                        <MapPin size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500" />
                        <input
                            type="text"
                            value={city}
                            onChange={(e) => setCity(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && fetchData()}
                            placeholder="City..."
                            className="w-full bg-black/40 rounded pl-7 pr-2 py-1.5 text-xs text-white placeholder:text-gray-500 focus:outline-none"
                            style={borderDimStyle}
                        />
                    </div>
                    <button
                        onClick={fetchData}
                        className="px-3 py-1.5 rounded text-xs transition-colors"
                        style={{
                            ...borderStyle,
                            ...accentStyle,
                            backgroundColor: 'rgba(var(--accent-color-rgb), 0.1)'
                        }}
                    >
                        CHECK
                    </button>
                </div>

                {/* Weather Display */}
                {loading ? (
                    <div className="text-center py-4">
                        <div className="animate-pulse text-xs" style={accentStyle}>FETCHING...</div>
                    </div>
                ) : weather ? (
                    <div className="flex items-center gap-4">
                        <div className="relative">
                            {getWeatherIcon(weather.description)}
                        </div>
                        <div className="flex-1">
                            <div className="text-2xl font-orbitron text-white">
                                {Math.round(weather.temp)}°C
                            </div>
                            <div className="text-xs text-gray-400 capitalize">{weather.description}</div>
                            <div className="text-xs" style={{ color: 'rgba(var(--accent-color-rgb), 0.6)' }}>{weather.city}</div>
                        </div>
                        <div className="text-right">
                            <div className="text-xs text-gray-500">Humidity</div>
                            <div className="text-sm" style={accentStyle}>{weather.humidity}%</div>
                        </div>
                    </div>
                ) : null}
            </div>

            {/* Prayer Times Card */}
            {nextPrayer && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-xl p-4 bg-black/40 backdrop-blur-md"
                    style={borderStyle}
                >
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="relative">
                                <Moon size={20} style={accentStyle} />
                                <motion.div
                                    className="absolute -inset-1 rounded-full"
                                    style={{ backgroundColor: 'rgba(var(--accent-color-rgb), 0.2)' }}
                                    animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.1, 0.3] }}
                                    transition={{ duration: 2, repeat: Infinity }}
                                />
                            </div>
                            <div>
                                <div className="text-xs text-gray-500 font-orbitron">NEXT PRAYER</div>
                                <div className="text-sm font-bold text-white">{nextPrayer.name}</div>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-lg font-orbitron" style={accentStyle}>{nextPrayer.time}</div>
                            <div className="text-xs text-gray-400">in {nextPrayer.countdown}</div>
                        </div>
                    </div>
                </motion.div>
            )}
        </div>
    );
};

export default WeatherWidget;

