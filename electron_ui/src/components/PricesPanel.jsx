import React, { useState, useEffect } from 'react';
import { Search, Laptop, ShoppingCart, ExternalLink, TrendingUp, Cpu, Monitor, MemoryStick } from 'lucide-react';
import { getLaptops } from '../api';

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
            const query = searchQuery.trim() || `laptop ${category}`;
            const data = await getLaptops(query, category, budget);
            setLaptops(data.results || []);
        } catch (err) {
            setError('Failed to search laptops. Please try again.');
            console.error(err);
        }
        setLoading(false);
    };

    // Initial search on mount
    useEffect(() => {
        handleSearch();
    }, []);

    // Search when category or budget changes
    useEffect(() => {
        const timer = setTimeout(() => {
            handleSearch();
        }, 500);
        return () => clearTimeout(timer);
    }, [category, budget, searchQuery]);

    return (
        <div className="flex flex-col h-full animate-in slide-in-from-bottom duration-500">
            {/* Header */}
            <div className="flex justify-between items-end mb-6 border-b border-jarvis-cyan/20 pb-2">
                <h2 className="text-lg font-orbitron text-jarvis-cyan tracking-wider flex items-center gap-2">
                    <Laptop size={20} />
                    LAPTOP FINDER
                </h2>
                <div className="text-xs text-gray-500 font-mono">
                    {laptops.length} RESULTS
                </div>
            </div>

            {/* Search Controls */}
            <div className="flex gap-3 mb-6">
                {/* Search Input */}
                <div className="flex-1 relative">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        placeholder="Search laptops..."
                        className="w-full bg-black/40 border border-jarvis-cyan/30 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-jarvis-cyan/60"
                    />
                </div>

                {/* Category Selector */}
                <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="bg-black/40 border border-jarvis-cyan/30 rounded-lg px-4 py-2.5 text-sm text-jarvis-cyan focus:outline-none focus:border-jarvis-cyan/60"
                >
                    <option value="gaming">🎮 Gaming</option>
                    <option value="work">💼 Work</option>
                    <option value="general">📦 General</option>
                </select>

                {/* Budget Slider */}
                <div className="flex items-center gap-2 bg-black/40 border border-jarvis-cyan/30 rounded-lg px-4 py-2">
                    <span className="text-xs text-gray-400">Max:</span>
                    <input
                        type="range"
                        min="500"
                        max="3000"
                        step="100"
                        value={budget}
                        onChange={(e) => setBudget(Number(e.target.value))}
                        className="w-24 accent-jarvis-cyan"
                    />
                    <span className="text-sm text-jarvis-cyan font-mono w-16">{budget}€</span>
                </div>

                {/* Search Button */}
                <button
                    onClick={handleSearch}
                    disabled={loading}
                    className="px-5 py-2.5 bg-jarvis-cyan/10 border border-jarvis-cyan/50 rounded-lg text-jarvis-cyan hover:bg-jarvis-cyan/20 transition-colors disabled:opacity-50"
                >
                    {loading ? 'Searching...' : 'SEARCH'}
                </button>
            </div>

            {/* Error State */}
            {error && (
                <div className="text-center py-4 text-red-400 text-sm">{error}</div>
            )}

            {/* Loading State */}
            {loading && (
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-jarvis-cyan animate-pulse font-orbitron">SCANNING RETAILERS...</div>
                </div>
            )}

            {/* Results Grid */}
            {!loading && laptops.length > 0 && (
                <div className="flex-1 overflow-y-auto pr-2 space-y-3">
                    {laptops.map((laptop, index) => (
                        <LaptopCard key={index} laptop={laptop} rank={index + 1} />
                    ))}
                </div>
            )}

            {/* Empty State */}
            {!loading && laptops.length === 0 && !error && (
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center text-gray-500">
                        <ShoppingCart size={48} className="mx-auto mb-4 opacity-30" />
                        <p className="font-orbitron text-sm">NO LAPTOPS FOUND</p>
                        <p className="text-xs mt-1">Try adjusting your search or budget</p>
                    </div>
                </div>
            )}
        </div>
    );
};

const LaptopCard = ({ laptop, rank }) => {
    const openUrl = () => {
        if (laptop.url) {
            window.open(laptop.url, '_blank');
        }
    };

    // Parse specs for display (basic parsing)
    const name = laptop.name || 'Unknown Laptop';
    const price = laptop.price || 0;
    const store = laptop.store || 'Unknown Store';
    const score = laptop.score || 0;

    return (
        <div className="group border border-jarvis-cyan/20 rounded-lg p-4 bg-black/30 hover:border-jarvis-cyan/50 hover:bg-black/50 transition-all duration-300">
            <div className="flex items-start gap-4">
                {/* Rank Badge */}
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg font-bold ${rank <= 3 ? 'bg-jarvis-cyan/20 text-jarvis-cyan' : 'bg-gray-800 text-gray-400'
                    }`}>
                    #{rank}
                </div>

                {/* Main Info */}
                <div className="flex-1 min-w-0">
                    <h3 className="text-white font-medium text-sm truncate group-hover:text-jarvis-cyan transition-colors">
                        {name}
                    </h3>
                    <div className="flex items-center gap-3 mt-2">
                        <span className="text-jarvis-cyan font-orbitron text-lg">{price}€</span>
                        <span className="text-xs text-gray-500">{store}</span>
                        {score > 0 && (
                            <div className="flex items-center gap-1 bg-green-500/20 px-2 py-0.5 rounded text-xs text-green-400">
                                <TrendingUp size={12} />
                                Score: {score.toFixed(2)}
                            </div>
                        )}
                    </div>
                </div>

                {/* Open Button */}
                <button
                    onClick={openUrl}
                    className="opacity-0 group-hover:opacity-100 p-2 bg-jarvis-cyan/10 rounded-lg transition-opacity"
                >
                    <ExternalLink size={18} className="text-jarvis-cyan" />
                </button>
            </div>
        </div>
    );
};

export default PricesPanel;
