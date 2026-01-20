import React, { useState, useRef } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { Star, Eye, EyeOff, Check, ExternalLink } from 'lucide-react';

const MovieCard = ({ title, year, posterUrl, rating, overview, tmdbId, imdbId, isWatched = false, onMarkWatched }) => {
    const [watched, setWatched] = useState(isWatched);
    const [loading, setLoading] = useState(false);

    // 3D Tilt Logic
    const x = useMotionValue(0);
    const y = useMotionValue(0);
    const mouseX = useSpring(x, { stiffness: 500, damping: 100 });
    const mouseY = useSpring(y, { stiffness: 500, damping: 100 });
    const rotateX = useTransform(mouseY, [-0.5, 0.5], ["15deg", "-15deg"]);
    const rotateY = useTransform(mouseX, [-0.5, 0.5], ["-15deg", "15deg"]);

    const handleMouseMove = (e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const width = rect.width;
        const height = rect.height;
        const xPct = (e.clientX - rect.left) / width - 0.5;
        const yPct = (e.clientY - rect.top) / height - 0.5;
        x.set(xPct);
        y.set(yPct);
    };

    const handleMouseLeave = () => {
        x.set(0);
        y.set(0);
    };

    const handleMarkWatched = async (e) => {
        e.stopPropagation();
        if (loading) return;
        setLoading(true);
        try {
            if (onMarkWatched) {
                await onMarkWatched(tmdbId, imdbId, title, year, !watched);
            }
            setWatched(!watched);
        } catch (err) {
            console.error('Failed to mark movie:', err);
        }
        setLoading(false);
    };

    const handleCardClick = () => {
        const url = tmdbId ? `https://www.themoviedb.org/movie/${tmdbId}` : imdbId ? `https://www.imdb.com/title/${imdbId}` : null;
        if (url) window.open(url, '_blank', 'noopener,noreferrer');
    };

    return (
        <motion.div
            className="group relative w-full aspect-[2/3] perspective-1000 cursor-pointer"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            style={{
                rotateX,
                rotateY,
                transformStyle: "preserve-3d",
            }}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            onClick={handleCardClick}
        >
            {/* Card Content */}
            <div className="w-full h-full bg-black/40 border border-jarvis-cyan/20 rounded-xl overflow-hidden relative transition-all duration-300 shadow-xl group-hover:shadow-[0_0_30px_rgba(0,240,255,0.2)] transform-gpu translate-z-10 backdrop-blur-sm">

                {/* Internal Gradient Glow */}
                <div className="absolute inset-0 bg-gradient-to-tr from-jarvis-cyan/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

                {/* Poster Image */}
                <div className="absolute inset-0 z-0">
                    <img src={posterUrl} alt={title} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity duration-500 scale-100 group-hover:scale-105" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-90"></div>
                </div>

                {/* Watch Button (Top Right) */}
                <button
                    onClick={handleMarkWatched}
                    disabled={loading}
                    className={`absolute top-2 right-2 p-2 rounded-full backdrop-blur-md transition-all z-20 ${watched
                        ? 'bg-green-500/80 text-white border border-green-400 shadow-[0_0_10px_rgba(34,197,94,0.5)]'
                        : 'bg-black/60 text-gray-300 border border-jarvis-cyan/30 hover:bg-jarvis-cyan/20 hover:text-jarvis-cyan'
                        }`}
                    title={watched ? 'Watched' : 'Mark as watched'}
                >
                    {loading ? (
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    ) : watched ? (
                        <Check size={16} />
                    ) : (
                        <Eye size={16} />
                    )}
                </button>

                {/* Watched Badge */}
                {watched && (
                    <div className="absolute top-2 left-2 px-2 py-0.5 bg-green-500/80 text-white text-[10px] font-orbitron rounded-full backdrop-blur-md z-20 shadow-[0_0_10px_rgba(34,197,94,0.4)]">
                        ARCHIVED
                    </div>
                )}

                {/* Info Overlay (Always visible at bottom, expands on hover) */}
                <div className="absolute bottom-0 left-0 right-0 p-4 transform translate-y-1 group-hover:translate-y-0 transition-transform z-10">
                    <div className="flex justify-between items-start">
                        <h3 className="text-white font-bold font-orbitron text-lg leading-tight drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)] group-hover:text-jarvis-cyan transition-colors">
                            {title}
                        </h3>
                        <span className="text-[10px] font-mono text-gray-300 border border-white/20 bg-black/50 px-1.5 py-0.5 rounded backdrop-blur-sm">
                            {year}
                        </span>
                    </div>

                    {/* Rating Badge */}
                    <div className="flex items-center space-x-1 mt-1">
                        <Star size={12} fill="#FFC107" className="text-yellow-400 drop-shadow-sm" />
                        <span className="text-sm font-bold font-mono text-gray-200">{rating}</span>
                    </div>

                    {/* Overview (Hidden by default, slides up) */}
                    <div className="h-0 group-hover:h-auto overflow-hidden transition-all duration-300">
                        <p className="text-xs text-gray-300 font-mono mt-2 line-clamp-4 border-t border-jarvis-cyan/30 pt-2 bg-black/80 backdrop-blur-md p-2 rounded">
                            {overview}
                        </p>
                    </div>
                </div>

                {/* Holographic Scanline Overlay */}
                <div className="absolute inset-0 bg-[url('https://media.giphy.com/media/xT0xezQGU5xBeaKpDE/giphy.gif')] opacity-0 group-hover:opacity-10 mix-blend-overlay pointer-events-none transition-opacity duration-300"></div>
                <div className="absolute inset-0 border border-jarvis-cyan/0 group-hover:border-jarvis-cyan/50 transition-colors duration-300 rounded-xl pointer-events-none"></div>
            </div>
        </motion.div>
    );
};

export default MovieCard;
