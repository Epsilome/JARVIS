import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Star, Eye, EyeOff, Check, ExternalLink } from 'lucide-react';

const MovieCard = ({ title, year, posterUrl, rating, overview, tmdbId, imdbId, isWatched = false, onMarkWatched }) => {
    const [watched, setWatched] = useState(isWatched);
    const [loading, setLoading] = useState(false);

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
        // Open TMDB link, fallback to IMDB
        const url = tmdbId
            ? `https://www.themoviedb.org/movie/${tmdbId}`
            : imdbId
                ? `https://www.imdb.com/title/${imdbId}`
                : null;
        if (url) {
            window.open(url, '_blank', 'noopener,noreferrer');
        }
    };

    return (
        <motion.div
            className="group relative w-full aspect-[2/3] perspective-1000 cursor-pointer"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ scale: 1.05, zIndex: 10 }}
            transition={{ duration: 0.3 }}
            onClick={handleCardClick}
        >
            {/* Card Content */}
            <div className="w-full h-full bg-black border border-jarvis-cyan/30 rounded overflow-hidden relative transition-all duration-300 group-hover:border-jarvis-cyan group-hover:shadow-[0_0_20px_rgba(0,240,255,0.3)]">

                {/* Poster Image */}
                <div className="absolute inset-0">
                    <img src={posterUrl} alt={title} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div>
                </div>

                {/* Watch Button (Top Right) */}
                <button
                    onClick={handleMarkWatched}
                    disabled={loading}
                    className={`absolute top-2 right-2 p-2 rounded-full backdrop-blur-md transition-all z-20 ${watched
                        ? 'bg-green-500/80 text-white border border-green-400'
                        : 'bg-black/50 text-gray-300 border border-jarvis-cyan/30 hover:bg-jarvis-cyan/20 hover:text-jarvis-cyan'
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
                    <div className="absolute top-2 left-2 px-2 py-0.5 bg-green-500/80 text-white text-[10px] font-orbitron rounded-full backdrop-blur-md z-20">
                        WATCHED
                    </div>
                )}

                {/* External Link Indicator */}
                <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity z-20">
                    <div className="p-1.5 bg-black/60 rounded-full backdrop-blur-md border border-jarvis-cyan/30">
                        <ExternalLink size={12} className="text-jarvis-cyan" />
                    </div>
                </div>

                {/* Info Overlay (Always visible at bottom, expands on hover) */}
                <div className="absolute bottom-0 left-0 right-0 p-4 transform translate-y-2 group-hover:translate-y-0 transition-transform">
                    <div className="flex justify-between items-start">
                        <h3 className="text-jarvis-cyan font-bold font-orbitron text-lg leading-tight shadow-black drop-shadow-md">{title}</h3>
                        <span className="text-xs font-mono text-gray-400 border border-gray-600 px-1 rounded">{year}</span>
                    </div>

                    {/* Rating Badge */}
                    <div className="flex items-center space-x-1 text-jarvis-alert mt-1">
                        <Star size={12} fill="#FFC107" />
                        <span className="text-sm font-bold font-mono">{rating}</span>
                    </div>

                    {/* Overview (Hidden by default, slides up) */}
                    <div className="h-0 group-hover:h-auto overflow-hidden transition-all duration-300">
                        <p className="text-xs text-gray-300 font-mono mt-2 line-clamp-4 border-t border-jarvis-cyan/30 pt-2 bg-black/80 backdrop-blur-sm">
                            {overview}
                        </p>
                    </div>
                </div>

                {/* Holographic Scanline Overlay */}
                <div className="absolute inset-0 bg-[url('https://media.giphy.com/media/xT0xezQGU5xBeaKpDE/giphy.gif')] opacity-0 group-hover:opacity-10 mix-blend-overlay pointer-events-none transition-opacity"></div>
            </div>
        </motion.div>
    );
};

export default MovieCard;
