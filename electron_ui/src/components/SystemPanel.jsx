import React, { useState, useEffect } from 'react';
import { Volume2, VolumeX, Play, Pause, SkipForward, SkipBack } from 'lucide-react';
import { setVolume, controlMedia, getSystemHealth } from '../api';

const SystemPanel = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [volume, setVolumeState] = useState(50);
    const [isMuted, setIsMuted] = useState(false);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const data = await getSystemHealth();
                setStats(data);
            } catch (err) {
                console.error('System stats error:', err);
            }
            setLoading(false);
        };
        fetchStats();
        const interval = setInterval(fetchStats, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleVolumeChange = async (e) => {
        const newVolume = parseInt(e.target.value);
        setVolumeState(newVolume);
        try {
            await setVolume(newVolume);
        } catch (err) {
            console.error('Volume set error:', err);
        }
    };

    const handleMediaControl = async (action) => {
        try {
            await controlMedia(action);
            if (action === 'mute') setIsMuted(!isMuted);
        } catch (err) {
            console.error('Media control error:', err);
        }
    };

    const StatBar = ({ label, value }) => (
        <div className="mb-4">
            <div className="flex justify-between text-xs mb-1.5">
                <span className="text-gray-400 font-orbitron tracking-wider">{label}</span>
                <span style={{ color: 'var(--accent-color)' }}>{Math.round(value)}%</span>
            </div>
            <div
                className="h-2 bg-black/60 rounded-full overflow-hidden"
                style={{ border: '1px solid rgba(var(--accent-color-rgb), 0.3)' }}
            >
                <div
                    className="h-full transition-all duration-500"
                    style={{
                        width: `${value}%`,
                        background: `linear-gradient(90deg, rgba(var(--accent-color-rgb), 0.5), var(--accent-color))`,
                        boxShadow: '0 0 8px rgba(var(--accent-color-rgb), 0.4)'
                    }}
                ></div>
            </div>
        </div>
    );

    // Reusable style objects
    const cardStyle = {
        border: '1px solid rgba(var(--accent-color-rgb), 0.2)',
        boxShadow: '0 0 15px rgba(var(--accent-color-rgb), 0.05), inset 0 0 30px rgba(var(--accent-color-rgb), 0.02)'
    };

    const headerStyle = { color: 'var(--accent-color)' };
    const subHeaderStyle = { color: 'rgba(var(--accent-color-rgb), 0.8)' };
    const borderDimStyle = { borderColor: 'rgba(var(--accent-color-rgb), 0.1)' };

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <div className="animate-pulse font-orbitron" style={headerStyle}>LOADING SYSTEM DATA...</div>
            </div>
        );
    }

    return (
        <div className="flex-1 overflow-y-auto animate-in fade-in duration-500">
            <h2
                className="text-2xl font-orbitron mb-6 tracking-wider pb-2"
                style={{ ...headerStyle, borderBottom: '1px solid rgba(var(--accent-color-rgb), 0.2)' }}
            >
                SYSTEM DIAGNOSTICS
            </h2>

            <div className="grid grid-cols-2 gap-6">
                {/* System Stats */}
                <div className="rounded-xl p-5 bg-black/40 backdrop-blur-md" style={cardStyle}>
                    <h3 className="text-sm font-orbitron mb-4" style={subHeaderStyle}>RESOURCES</h3>
                    {stats ? (
                        <>
                            <StatBar label="CPU LOAD" value={stats.cpu} />
                            <StatBar label="RAM USAGE" value={stats.ram} />
                            <StatBar label="DISK USAGE" value={stats.disk} />
                        </>
                    ) : (
                        <div className="text-gray-500 text-sm">No data</div>
                    )}
                </div>

                {/* System Info */}
                <div className="rounded-xl p-5 bg-black/40 backdrop-blur-md" style={cardStyle}>
                    <h3 className="text-sm font-orbitron mb-4" style={subHeaderStyle}>INFO</h3>
                    {stats && (
                        <div className="space-y-3">
                            <div className="flex justify-between items-center py-2" style={{ ...borderDimStyle, borderBottom: '1px solid rgba(var(--accent-color-rgb), 0.1)' }}>
                                <span className="text-gray-400 text-xs font-orbitron">BATTERY</span>
                                <span className="font-mono text-sm" style={headerStyle}>{stats.battery}</span>
                            </div>
                            <div className="flex justify-between items-center py-2" style={{ ...borderDimStyle, borderBottom: '1px solid rgba(var(--accent-color-rgb), 0.1)' }}>
                                <span className="text-gray-400 text-xs font-orbitron">RAM USED</span>
                                <span className="font-mono text-sm" style={headerStyle}>{stats.ram_used_gb} / {stats.ram_total_gb} GB</span>
                            </div>
                            <div className="flex justify-between items-center py-2">
                                <span className="text-gray-400 text-xs font-orbitron">API STATUS</span>
                                <span className="text-green-400 font-mono text-sm">ONLINE</span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Volume Control */}
                <div className="rounded-xl p-5 bg-black/40 backdrop-blur-md" style={cardStyle}>
                    <h3 className="text-sm font-orbitron mb-4" style={subHeaderStyle}>VOLUME CONTROL</h3>
                    <div className="flex items-center gap-4 mb-4">
                        <button
                            onClick={() => handleMediaControl('mute')}
                            className="p-2 rounded-lg transition-colors"
                            style={{
                                border: isMuted ? '1px solid rgba(239, 68, 68, 0.5)' : '1px solid rgba(var(--accent-color-rgb), 0.3)',
                                backgroundColor: isMuted ? 'rgba(239, 68, 68, 0.1)' : 'transparent'
                            }}
                        >
                            {isMuted ? <VolumeX size={20} className="text-red-400" /> : <Volume2 size={20} style={headerStyle} />}
                        </button>
                        <input
                            type="range"
                            min="0"
                            max="100"
                            value={volume}
                            onChange={handleVolumeChange}
                            className="flex-1 h-2 rounded-lg appearance-none cursor-pointer"
                            style={{
                                background: `linear-gradient(to right, var(--accent-color) ${volume}%, rgba(var(--accent-color-rgb), 0.2) ${volume}%)`
                            }}
                        />
                        <span className="font-mono text-sm w-12 text-right" style={headerStyle}>{volume}%</span>
                    </div>
                </div>

                {/* Media Controls */}
                <div className="rounded-xl p-5 bg-black/40 backdrop-blur-md" style={cardStyle}>
                    <h3 className="text-sm font-orbitron mb-4" style={subHeaderStyle}>MEDIA CONTROLS</h3>
                    <div className="flex items-center justify-center gap-4">
                        <button
                            onClick={() => handleMediaControl('prev')}
                            className="p-3 rounded-lg transition-colors hover:bg-white/5"
                            style={{ border: '1px solid rgba(var(--accent-color-rgb), 0.3)' }}
                        >
                            <SkipBack size={20} style={headerStyle} />
                        </button>
                        <button
                            onClick={() => handleMediaControl('play_pause')}
                            className="p-4 rounded-full transition-colors hover:bg-white/5"
                            style={{
                                border: '2px solid rgba(var(--accent-color-rgb), 0.5)',
                                boxShadow: '0 0 15px rgba(var(--accent-color-rgb), 0.3)'
                            }}
                        >
                            <Play size={24} style={headerStyle} />
                        </button>
                        <button
                            onClick={() => handleMediaControl('next')}
                            className="p-3 rounded-lg transition-colors hover:bg-white/5"
                            style={{ border: '1px solid rgba(var(--accent-color-rgb), 0.3)' }}
                        >
                            <SkipForward size={20} style={headerStyle} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SystemPanel;

