import React, { useState, useEffect } from 'react';
import { Cloud, Sun, CloudRain, Snowflake, Wind, RefreshCw, MapPin } from 'lucide-react';
import { getWeather } from '../api';

const WeatherWidget = () => {
    const [weather, setWeather] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [city, setCity] = useState('Casablanca');

    const fetchWeather = async () => {
        setLoading(true);
        setError(null);
        try {
            // Pass only city - let the API resolve the country
            const data = await getWeather(city.trim(), '');
            setWeather(data);
        } catch (err) {
            setError('Failed to fetch weather');
            console.error(err);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchWeather();
    }, []);

    const getWeatherIcon = (description) => {
        const desc = description?.toLowerCase() || '';
        if (desc.includes('rain')) return <CloudRain className="text-blue-400" size={32} />;
        if (desc.includes('snow')) return <Snowflake className="text-white" size={32} />;
        if (desc.includes('cloud')) return <Cloud className="text-gray-300" size={32} />;
        if (desc.includes('wind')) return <Wind className="text-cyan-300" size={32} />;
        return <Sun className="text-yellow-400" size={32} />;
    };

    const accentStyle = { color: 'var(--accent-color)' };
    const borderStyle = { border: '1px solid rgba(var(--accent-color-rgb), 0.3)' };
    const borderDimStyle = { border: '1px solid rgba(var(--accent-color-rgb), 0.2)' };

    return (
        <div
            className="rounded-xl p-4 bg-black/40 backdrop-blur-md mb-4"
            style={borderStyle}
        >
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-orbitron tracking-wider flex items-center gap-2" style={accentStyle}>
                    <Cloud size={16} />
                    WEATHER
                </h3>
                <button
                    onClick={fetchWeather}
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
                        onKeyDown={(e) => e.key === 'Enter' && fetchWeather()}
                        placeholder="City..."
                        className="w-full bg-black/40 rounded pl-7 pr-2 py-1.5 text-xs text-white placeholder:text-gray-500 focus:outline-none"
                        style={borderDimStyle}
                    />
                </div>
                <button
                    onClick={fetchWeather}
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
            ) : error ? (
                <div className="text-center py-4">
                    <div className="text-red-400 text-xs">{error}</div>
                </div>
            ) : weather ? (
                <div className="flex items-center gap-4">
                    <div className="relative">
                        {getWeatherIcon(weather.description)}
                        <div className="absolute -bottom-1 -right-1 w-3 h-3 rounded-full blur-sm" style={{ backgroundColor: 'rgba(var(--accent-color-rgb), 0.2)' }}></div>
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
    );
};

export default WeatherWidget;
