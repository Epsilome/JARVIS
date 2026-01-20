import React, { useState, useEffect } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { Volume2, VolumeX, Play, SkipForward, SkipBack, Cpu, HardDrive, MemoryStick, Zap, Activity } from 'lucide-react';
import { setVolume, controlMedia, getSystemHealth } from '../api';

// Radial Gauge Component
const RadialGauge = ({ value, label, icon: Icon, color = 'cyan' }) => {
    const radius = 40;
    const stroke = 6;
    const normalizedRadius = radius - stroke / 2;
    const circumference = normalizedRadius * 2 * Math.PI;
    const strokeDashoffset = circumference - (value / 100) * circumference;

    const colorMap = {
        cyan: { main: '#00f0ff', glow: 'rgba(0, 240, 255, 0.5)', bg: 'rgba(0, 240, 255, 0.1)' },
        purple: { main: '#a855f7', glow: 'rgba(168, 85, 247, 0.5)', bg: 'rgba(168, 85, 247, 0.1)' },
        green: { main: '#22c55e', glow: 'rgba(34, 197, 94, 0.5)', bg: 'rgba(34, 197, 94, 0.1)' },
    };
    const c = colorMap[color] || colorMap.cyan;

    return (
        <div className="flex flex-col items-center">
            <div className="relative" style={{ width: radius * 2, height: radius * 2 }}>
                <svg width={radius * 2} height={radius * 2} className="transform -rotate-90">
                    {/* Background circle */}
                    <circle
                        stroke={c.bg}
                        fill="transparent"
                        strokeWidth={stroke}
                        r={normalizedRadius}
                        cx={radius}
                        cy={radius}
                    />
                    {/* Animated progress circle */}
                    <motion.circle
                        stroke={c.main}
                        fill="transparent"
                        strokeWidth={stroke}
                        strokeLinecap="round"
                        r={normalizedRadius}
                        cx={radius}
                        cy={radius}
                        initial={{ strokeDashoffset: circumference }}
                        animate={{ strokeDashoffset }}
                        transition={{ duration: 1.5, ease: "easeOut" }}
                        style={{
                            strokeDasharray: circumference,
                            filter: `drop-shadow(0 0 6px ${c.glow})`,
                        }}
                    />
                </svg>
                {/* Center content */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <Icon size={16} style={{ color: c.main }} className="mb-0.5" />
                    <span className="text-lg font-bold font-orbitron" style={{ color: c.main }}>
                        {Math.round(value)}%
                    </span>
                </div>
                {/* Pulsing glow ring */}
                <motion.div
                    className="absolute inset-0 rounded-full pointer-events-none"
                    style={{ border: `1px solid ${c.main}`, opacity: 0.3 }}
                    animate={{ scale: [1, 1.15, 1], opacity: [0.3, 0.1, 0.3] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                />
            </div>
            <span className="text-xs text-gray-400 font-orbitron mt-2 tracking-wider">{label}</span>
        </div>
    );
};

// 3D Tilt Card Component
const TiltCard = ({ children, className = '' }) => {
    const x = useMotionValue(0);
    const y = useMotionValue(0);

    const mouseX = useSpring(x, { stiffness: 500, damping: 100 });
    const mouseY = useSpring(y, { stiffness: 500, damping: 100 });

    const rotateX = useTransform(mouseY, [-0.5, 0.5], ["10deg", "-10deg"]);
    const rotateY = useTransform(mouseX, [-0.5, 0.5], ["-10deg", "10deg"]);

    const handleMouseMove = (e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const xPct = (e.clientX - rect.left) / rect.width - 0.5;
        const yPct = (e.clientY - rect.top) / rect.height - 0.5;
        x.set(xPct);
        y.set(yPct);
    };

    const handleMouseLeave = () => {
        x.set(0);
        y.set(0);
    };

    return (
        <motion.div
            style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            className={`perspective-1000 ${className}`}
        >
            {children}
        </motion.div>
    );
};

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

    const cardVariants = {
        hidden: { opacity: 0, y: 30, scale: 0.95 },
        visible: { opacity: 1, y: 0, scale: 1 }
    };

    const cardStyle = "rounded-2xl p-6 bg-black/50 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)] relative overflow-hidden group";
    const cardGlow = "absolute inset-0 bg-gradient-to-br from-jarvis-cyan/5 via-transparent to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none";

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <motion.div
                    className="font-orbitron text-jarvis-cyan text-lg tracking-widest"
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                >
                    INITIALIZING DIAGNOSTICS...
                </motion.div>
            </div>
        );
    }

    return (
        <motion.div
            className="flex-1 overflow-y-auto px-4 py-2"
            initial="hidden"
            animate="visible"
            variants={{
                hidden: { opacity: 0 },
                visible: { opacity: 1, transition: { staggerChildren: 0.15, delayChildren: 0.1 } }
            }}
        >
            {/* Header */}
            <motion.div
                variants={cardVariants}
                className="flex items-center gap-3 mb-8 pb-4 border-b border-jarvis-cyan/20"
            >
                <Activity size={28} className="text-jarvis-cyan" />
                <h2 className="text-2xl font-orbitron tracking-widest text-jarvis-cyan drop-shadow-[0_0_10px_rgba(0,240,255,0.4)]">
                    SYSTEM DIAGNOSTICS
                </h2>
                <motion.div
                    className="w-2 h-2 rounded-full bg-green-400 ml-auto"
                    animate={{ scale: [1, 1.3, 1], opacity: [1, 0.7, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                />
                <span className="text-xs text-green-400 font-mono">LIVE</span>
            </motion.div>

            <div className="grid grid-cols-2 gap-6">
                {/* Resource Gauges */}
                <motion.div variants={cardVariants}>
                    <TiltCard>
                        <div className={cardStyle}>
                            <div className={cardGlow} />
                            <h3 className="text-sm font-orbitron mb-6 text-jarvis-cyan/80 flex items-center gap-2">
                                <Zap size={14} />
                                RESOURCE MONITOR
                            </h3>
                            {stats ? (
                                <div className="flex justify-around items-center">
                                    <RadialGauge value={stats.cpu} label="CPU" icon={Cpu} color="cyan" />
                                    <RadialGauge value={stats.ram} label="RAM" icon={MemoryStick} color="purple" />
                                    <RadialGauge value={stats.disk} label="DISK" icon={HardDrive} color="green" />
                                </div>
                            ) : (
                                <div className="text-gray-500 text-sm text-center">No data</div>
                            )}
                        </div>
                    </TiltCard>
                </motion.div>

                {/* System Info */}
                <motion.div variants={cardVariants}>
                    <TiltCard>
                        <div className={cardStyle}>
                            <div className={cardGlow} />
                            <h3 className="text-sm font-orbitron mb-4 text-jarvis-cyan/80">SYSTEM INFO</h3>
                            {stats && (
                                <div className="space-y-4">
                                    <div className="flex justify-between items-center py-2 border-b border-white/5">
                                        <span className="text-gray-400 text-xs font-orbitron">BATTERY</span>
                                        <span className="font-mono text-sm text-jarvis-cyan">{stats.battery}</span>
                                    </div>
                                    <div className="flex justify-between items-center py-2 border-b border-white/5">
                                        <span className="text-gray-400 text-xs font-orbitron">RAM USED</span>
                                        <span className="font-mono text-sm text-jarvis-cyan">{stats.ram_used_gb} / {stats.ram_total_gb} GB</span>
                                    </div>
                                    <div className="flex justify-between items-center py-2">
                                        <span className="text-gray-400 text-xs font-orbitron">API STATUS</span>
                                        <div className="flex items-center gap-2">
                                            <motion.div
                                                className="w-2 h-2 rounded-full bg-green-400"
                                                animate={{ opacity: [1, 0.5, 1] }}
                                                transition={{ duration: 1, repeat: Infinity }}
                                            />
                                            <span className="text-green-400 font-mono text-sm">ONLINE</span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </TiltCard>
                </motion.div>

                {/* Volume Control */}
                <motion.div variants={cardVariants}>
                    <TiltCard>
                        <div className={cardStyle}>
                            <div className={cardGlow} />
                            <h3 className="text-sm font-orbitron mb-4 text-jarvis-cyan/80">VOLUME CONTROL</h3>
                            <div className="flex items-center gap-4">
                                <motion.button
                                    onClick={() => handleMediaControl('mute')}
                                    whileHover={{ scale: 1.1 }}
                                    whileTap={{ scale: 0.95 }}
                                    className={`p-3 rounded-xl transition-colors border ${isMuted ? 'border-red-500/50 bg-red-500/10' : 'border-jarvis-cyan/30 bg-jarvis-cyan/5'}`}
                                >
                                    {isMuted ? <VolumeX size={20} className="text-red-400" /> : <Volume2 size={20} className="text-jarvis-cyan" />}
                                </motion.button>
                                <div className="flex-1 relative">
                                    <input
                                        type="range"
                                        min="0"
                                        max="100"
                                        value={volume}
                                        onChange={handleVolumeChange}
                                        className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-jarvis-cyan bg-white/10"
                                    />
                                </div>
                                <span className="font-mono text-lg w-14 text-right text-jarvis-cyan font-bold">{volume}%</span>
                            </div>
                        </div>
                    </TiltCard>
                </motion.div>

                {/* Media Controls */}
                <motion.div variants={cardVariants}>
                    <TiltCard>
                        <div className={cardStyle}>
                            <div className={cardGlow} />
                            <h3 className="text-sm font-orbitron mb-4 text-jarvis-cyan/80">MEDIA CONTROLS</h3>
                            <div className="flex items-center justify-center gap-6">
                                <motion.button
                                    onClick={() => handleMediaControl('prev')}
                                    whileHover={{ scale: 1.15, boxShadow: '0 0 15px rgba(0, 240, 255, 0.3)' }}
                                    whileTap={{ scale: 0.9 }}
                                    className="p-3 rounded-xl transition-colors border border-jarvis-cyan/30 bg-jarvis-cyan/5"
                                >
                                    <SkipBack size={20} className="text-jarvis-cyan" />
                                </motion.button>
                                <motion.button
                                    onClick={() => handleMediaControl('play_pause')}
                                    whileHover={{ scale: 1.1, boxShadow: '0 0 25px rgba(0, 240, 255, 0.5)' }}
                                    whileTap={{ scale: 0.95 }}
                                    className="p-5 rounded-full transition-colors border-2 border-jarvis-cyan bg-jarvis-cyan/10 shadow-[0_0_20px_rgba(0,240,255,0.3)]"
                                >
                                    <Play size={28} className="text-jarvis-cyan" />
                                </motion.button>
                                <motion.button
                                    onClick={() => handleMediaControl('next')}
                                    whileHover={{ scale: 1.15, boxShadow: '0 0 15px rgba(0, 240, 255, 0.3)' }}
                                    whileTap={{ scale: 0.9 }}
                                    className="p-3 rounded-xl transition-colors border border-jarvis-cyan/30 bg-jarvis-cyan/5"
                                >
                                    <SkipForward size={20} className="text-jarvis-cyan" />
                                </motion.button>
                            </div>
                        </div>
                    </TiltCard>
                </motion.div>
            </div>
        </motion.div>
    );
};

export default SystemPanel;
