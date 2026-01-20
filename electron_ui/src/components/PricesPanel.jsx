
import React, { useState, useEffect, useRef } from 'react';
import { Search, Laptop, ShoppingCart, ExternalLink, TrendingUp, Sparkles, ScanLine } from 'lucide-react';
import { getLaptops } from '../api';
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from 'framer-motion';

const PricesPanel = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [category, setCategory] = useState('gaming');
    const [laptops, setLaptops] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [budget, setBudget] = useState(1500);

    const handleSearch = async () => {
        if (!searchQuery.trim() && !category) return;
        setLoading(true);
        setError(null);
        try {
            const query = searchQuery.trim() || `laptop ${category} `;
            const data = await getLaptops(query, category, budget);
            setLaptops(data.results || []);
        } catch (err) {
            setError('Failed to search laptops. Please try again.');
            console.error(err);
        }
        setLoading(false);
    };

    // Initial search on mount
    useEffect(() => { handleSearch(); }, []);

    // Search when category or budget changes
    useEffect(() => {
        const timer = setTimeout(() => { handleSearch(); }, 800); // Debounce slightly longer for slider
        return () => clearTimeout(timer);
    }, [category, budget]);

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.08
            }
        }
    };

    const itemVariants = {
        hidden: { y: 20, opacity: 0, scale: 0.95 },
        visible: { y: 0, opacity: 1, scale: 1 }
    };

    return (
        <div className="flex flex-col h-full bg-gradient-to-br from-black/20 to-transparent p-2 relative overflow-hidden">
            {/* Cyber Grid Background (Subtle) */}
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 pointer-events-none"></div>

            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-between items-end mb-6 border-b border-jarvis-cyan/20 pb-4 relative z-10"
            >
                <h2 className="text-xl font-orbitron text-jarvis-cyan tracking-widest flex items-center gap-2 drop-shadow-[0_0_10px_rgba(0,255,255,0.3)]">
                    <Laptop size={24} className="stroke-[1.5]" />
                    LAPTOP FINDER
                </h2>
                <div className="text-xs text-gray-400 font-mono bg-jarvis-cyan/5 px-2 py-1 rounded border border-jarvis-cyan/10">
                    {laptops.length} SIGNALS
                </div>
            </motion.div>

            {/* Search Controls */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="flex flex-col gap-4 mb-6 backdrop-blur-md bg-black/40 p-4 rounded-xl border border-white/5 relative z-10"
            >
                {/* Controls Content (Same as before but cleaner structure) */}
                <div className="flex gap-3">
                    <div className="flex-1 relative group">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-jarvis-cyan transition-colors" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                            placeholder="Type & Press Enter..."
                            className="w-full bg-black/40 border border-jarvis-cyan/20 rounded-lg pl-10 pr-4 py-3 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-jarvis-cyan/50 focus:bg-black/60 transition-all font-mono"
                        />
                    </div>
                    <button
                        onClick={handleSearch}
                        disabled={loading}
                        className="px-6 py-2 bg-jarvis-cyan/10 border border-jarvis-cyan/50 rounded-lg text-jarvis-cyan font-orbitron text-sm hover:bg-jarvis-cyan/20 hover:shadow-[0_0_15px_rgba(0,255,255,0.2)] transition-all disabled:opacity-50"
                    >
                        {loading ? 'SCANNING' : 'SEARCH'}
                    </button>
                </div>
                <div className="flex gap-4 items-center">
                    <select
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        className="bg-black/40 border border-jarvis-cyan/20 rounded-lg px-4 py-2 text-sm text-gray-300 focus:outline-none focus:border-jarvis-cyan/50 hover:bg-black/60 cursor-pointer transition-all"
                    >
                        <option value="gaming">🎮 Gaming</option>
                        <option value="work">💼 Work</option>
                        <option value="general">📦 General</option>
                    </select>
                    <div className="flex-1 flex items-center gap-4 bg-black/40 border border-jarvis-cyan/20 rounded-lg px-4 py-2">
                        <span className="text-xs text-gray-400 font-mono">BUDGET:</span>
                        <input
                            type="range"
                            min="500" max="4000" step="100"
                            value={budget}
                            onChange={(e) => setBudget(Number(e.target.value))}
                            className="flex-1 accent-jarvis-cyan h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                        />
                        <span className="text-sm text-jarvis-cyan font-orbitron w-16 text-right">{budget}€</span>
                    </div>
                </div>
            </motion.div>

            {/* Error State */}
            <AnimatePresence>
                {error && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="text-center py-4 text-red-400 text-sm bg-red-500/10 rounded-lg mb-4 border border-red-500/20"
                    >
                        {error}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Loading State */}
            {loading && (
                <div className="flex-1 flex flex-col items-center justify-center gap-4">
                    <div className="relative w-16 h-16">
                        <div className="absolute inset-0 border-4 border-jarvis-cyan/20 rounded-full"></div>
                        <div className="absolute inset-0 border-4 border-jarvis-cyan border-t-transparent rounded-full animate-spin"></div>
                    </div>
                    <div className="text-jarvis-cyan animate-pulse font-orbitron tracking-widest text-sm">SCANNING RETAILERS...</div>
                </div>
            )}

            {/* Results Grid */}
            {!loading && laptops.length > 0 && (
                <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar relative z-10 pb-4"
                >
                    {laptops.map((laptop, index) => (
                        <TiltCard key={index} laptop={laptop} rank={index + 1} variants={itemVariants} />
                    ))}
                </motion.div>
            )}

            {/* Empty State */}
            {!loading && laptops.length === 0 && !error && (
                <div className="flex-1 flex items-center justify-center opacity-50">
                    <div className="text-center text-gray-500">
                        <ScanLine size={64} className="mx-auto mb-4 opacity-20 animate-pulse" />
                        <p className="font-orbitron text-lg tracking-widest">NO SIGNALS ACQUIRED</p>
                        <p className="text-xs mt-2 font-mono">Adjust search parameters</p>
                    </div>
                </div>
            )}
        </div>
    );
};

// 3D Tilt Card Component
const TiltCard = ({ laptop, rank, variants }) => {
    const x = useMotionValue(0);
    const y = useMotionValue(0);

    const mouseX = useSpring(x, { stiffness: 500, damping: 100 });
    const mouseY = useSpring(y, { stiffness: 500, damping: 100 });

    const rotateX = useTransform(mouseY, [-0.5, 0.5], ["17.5deg", "-17.5deg"]);
    const rotateY = useTransform(mouseX, [-0.5, 0.5], ["-17.5deg", "17.5deg"]);

    const handleMouseMove = (e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const width = rect.width;
        const height = rect.height;
        const mouseXVal = e.clientX - rect.left;
        const mouseYVal = e.clientY - rect.top;
        const xPct = mouseXVal / width - 0.5;
        const yPct = mouseYVal / height - 0.5;
        x.set(xPct);
        y.set(yPct);
    };

    const handleMouseLeave = () => {
        x.set(0);
        y.set(0);
    };

    const isTopRank = rank <= 3;
    const rankColor = isTopRank ? 'text-jarvis-cyan bg-jarvis-cyan/10 border-jarvis-cyan/30' : 'text-gray-500 bg-white/5 border-white/10';

    const openUrl = () => {
        if (laptop.url) window.open(laptop.url, '_blank');
    };

    return (
        <motion.div
            variants={variants}
            style={{
                rotateX,
                rotateY,
                transformStyle: "preserve-3d",
            }}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            className="perspective-1000 group relative"
        >
            <div className="relative border border-white/5 rounded-xl p-4 bg-black/40 backdrop-blur-md transition-all duration-300 overflow-hidden shadow-lg hover:shadow-jarvis-cyan/10">
                {/* Internal Gradient Glow */}
                <div className="absolute inset-0 bg-gradient-to-br from-jarvis-cyan/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

                <div className="flex items-start gap-4 relative z-10 transform-gpu translate-z-10">
                    {/* Rank Badge */}
                    <div className={`w - 12 h - 12 rounded - xl flex items - center justify - center text - xl font - bold font - orbitron border ${rankColor} `}>
                        #{rank}
                    </div>

                    <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-start">
                            <h3 className="text-gray-200 font-medium text-sm leading-tight group-hover:text-jarvis-cyan transition-colors line-clamp-2 pr-8">
                                {laptop.name || 'Unknown Unit'}
                            </h3>
                            <button onClick={openUrl} className="bg-jarvis-cyan/10 p-2 rounded-lg hover:bg-jarvis-cyan hover:text-black text-jarvis-cyan transition-all opacity-0 group-hover:opacity-100 absolute top-0 right-0">
                                <ExternalLink size={16} />
                            </button>
                        </div>

                        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-3">
                            <span className="text-xl font-bold text-white font-orbitron drop-shadow-[0_0_8px_rgba(255,255,255,0.2)]">
                                {laptop.price}€
                            </span>
                            <div className="flex items-center gap-2 text-xs text-gray-400 font-mono bg-white/5 px-2 py-1 rounded">
                                <ShoppingCart size={12} />
                                {laptop.store}
                            </div>
                            {laptop.score > 0 && (
                                <div className="flex items-center gap-1 bg-green-500/10 border border-green-500/20 px-2 py-1 rounded text-xs text-green-400 font-mono">
                                    <TrendingUp size={12} />
                                    {laptop.score.toFixed(1)}
                                </div>
                            )}
                            {isTopRank && (
                                <div className="flex items-center gap-1 bg-yellow-500/10 border border-yellow-500/20 px-2 py-1 rounded text-xs text-yellow-400 font-mono animate-pulse">
                                    <Sparkles size={12} />
                                    TOP DEAL
                                </div>
                            )}
                        </div>

                        {(laptop.cpu || laptop.gpu || laptop.ram || laptop.storage) && (
                            <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-white/5">
                                {laptop.cpu && <SpecBadge label="CPU" value={laptop.cpu} color="blue" />}
                                {laptop.gpu && <SpecBadge label="GPU" value={laptop.gpu} color="green" />}
                                {laptop.ram && <SpecBadge label="RAM" value={laptop.ram} color="purple" />}
                                {laptop.storage && <SpecBadge label="SSD" value={laptop.storage} color="orange" />}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

const SpecBadge = ({ label, value, color }) => {
    const colors = {
        blue: 'bg-blue-500/10 text-blue-300 border-blue-500/20',
        green: 'bg-green-500/10 text-green-300 border-green-500/20',
        purple: 'bg-purple-500/10 text-purple-300 border-purple-500/20',
        orange: 'bg-orange-500/10 text-orange-300 border-orange-500/20'
    };
    return (
        <span className={`px - 2 py - 1 rounded text - [10px] font - mono border ${colors[color]} uppercase tracking - tight`}>
            <span className="opacity-50 mr-1">{label}:</span>
            {value}
        </span>
    );
};

export default PricesPanel;
