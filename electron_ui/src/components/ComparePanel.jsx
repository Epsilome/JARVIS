import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { Search, Cpu, Monitor, HardDrive, MemoryStick, X, Plus, Scale, Trash2, Database } from 'lucide-react';
import { getHardwareDatabase } from '../api';

const TYPE_ICONS = {
    cpu: Cpu,
    gpu: Monitor,
    ssd: HardDrive,
    ram: MemoryStick,
    unknown: Cpu
};

const TYPE_COLORS = {
    cpu: '#00BFFF',
    gpu: '#00FF88',
    ssd: '#FF6B6B',
    ram: '#FFD93D',
    unknown: '#888'
};

// 3D Tilt Card Component
const TiltCard = ({ children, className = '' }) => {
    const x = useMotionValue(0);
    const y = useMotionValue(0);

    const mouseX = useSpring(x, { stiffness: 500, damping: 100 });
    const mouseY = useSpring(y, { stiffness: 500, damping: 100 });

    const rotateX = useTransform(mouseY, [-0.5, 0.5], ["8deg", "-8deg"]);
    const rotateY = useTransform(mouseX, [-0.5, 0.5], ["-8deg", "8deg"]);

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

const ComparePanel = () => {
    const [compareSlots, setCompareSlots] = useState([]);
    const [selectedSlotIndex, setSelectedSlotIndex] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [typeFilter, setTypeFilter] = useState('all');
    const [database, setDatabase] = useState({ cpus: [], gpus: [], ssds: [], ram: [], total: 0 });
    const [dbLoading, setDbLoading] = useState(true);
    const searchRef = useRef(null);

    useEffect(() => {
        loadDatabase();
    }, []);

    const loadDatabase = async () => {
        setDbLoading(true);
        try {
            const data = await getHardwareDatabase('all', 10000);
            setDatabase(data);
        } catch (err) {
            console.error('Failed to load hardware database:', err);
        }
        setDbLoading(false);
    };

    useEffect(() => {
        if (!searchQuery.trim() || searchQuery.length < 2) {
            setSearchResults([]);
            return;
        }

        const query = searchQuery.toLowerCase().trim();
        const allItems = [
            ...database.cpus,
            ...database.gpus,
            ...database.ssds,
            ...database.ram
        ];

        let itemsToSearch = allItems;
        if (typeFilter !== 'all') {
            itemsToSearch = allItems.filter(item => item.type === typeFilter);
        }

        const filtered = itemsToSearch.filter(item =>
            item.name?.toLowerCase().includes(query)
        );

        filtered.sort((a, b) => (b.score || 0) - (a.score || 0));
        setSearchResults(filtered.slice(0, 50));
    }, [searchQuery, typeFilter, database]);

    const addToComparison = (item) => {
        if (selectedSlotIndex !== null && compareSlots[selectedSlotIndex] === null) {
            const newSlots = [...compareSlots];
            newSlots[selectedSlotIndex] = item;
            setCompareSlots(newSlots);
            setSelectedSlotIndex(null);
        } else {
            const emptyIndex = compareSlots.findIndex(s => s === null);
            if (emptyIndex !== -1) {
                const newSlots = [...compareSlots];
                newSlots[emptyIndex] = item;
                setCompareSlots(newSlots);
            } else if (compareSlots.length < 8) {
                setCompareSlots([...compareSlots, item]);
            }
        }
    };

    const selectSlot = (index) => {
        if (compareSlots[index] === null) {
            setSelectedSlotIndex(selectedSlotIndex === index ? null : index);
        }
    };

    const removeSlot = (index) => {
        setCompareSlots(compareSlots.filter((_, i) => i !== index));
    };

    const clearAll = () => {
        setCompareSlots([]);
    };

    const filledSlots = compareSlots.filter(Boolean);
    const maxScore = Math.max(...filledSlots.map(s => s.score || 0), 1);

    const getDatabaseItems = () => {
        switch (typeFilter) {
            case 'cpu': return database.cpus;
            case 'gpu': return database.gpus;
            case 'ssd': return database.ssds;
            case 'ram': return database.ram;
            default: return [
                ...database.gpus.slice(0, 15),
                ...database.cpus.slice(0, 15),
                ...database.ssds.slice(0, 15),
                ...database.ram.slice(0, 15)
            ];
        }
    };

    const getFilteredCount = () => {
        switch (typeFilter) {
            case 'cpu': return database.cpus.length;
            case 'gpu': return database.gpus.length;
            case 'ssd': return database.ssds.length;
            case 'ram': return database.ram.length;
            default: return database.cpus.length + database.gpus.length + database.ssds.length + database.ram.length;
        }
    };

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: { opacity: 1, transition: { staggerChildren: 0.05, delayChildren: 0.1 } }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 15 },
        visible: { opacity: 1, y: 0 }
    };

    return (
        <motion.div
            className="flex flex-col h-full"
            initial="hidden"
            animate="visible"
            variants={containerVariants}
        >
            {/* Header */}
            <motion.div
                variants={itemVariants}
                className="flex justify-between items-end mb-4 border-b border-jarvis-cyan/20 pb-2"
            >
                <h2 className="text-lg font-orbitron text-jarvis-cyan tracking-wider flex items-center gap-2 drop-shadow-[0_0_10px_rgba(0,240,255,0.3)]">
                    <Scale size={20} />
                    HARDWARE COMPARE
                </h2>
                <div className="flex gap-2">
                    {['all', 'cpu', 'gpu', 'ssd', 'ram'].map(type => (
                        <motion.button
                            key={type}
                            onClick={() => setTypeFilter(type)}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className={`px-3 py-1 text-xs rounded border transition-all duration-300 ${typeFilter === type
                                ? 'border-jarvis-cyan bg-jarvis-cyan/20 text-jarvis-cyan shadow-[0_0_10px_rgba(0,240,255,0.2)]'
                                : 'border-gray-600 text-gray-400 hover:border-gray-500'
                                }`}
                        >
                            {type.toUpperCase()}
                        </motion.button>
                    ))}
                </div>
            </motion.div>

            {/* Comparison Slots */}
            <motion.div variants={itemVariants} className="flex flex-wrap gap-3 mb-4">
                <AnimatePresence mode="popLayout">
                    {compareSlots.map((slot, index) => (
                        <motion.div
                            key={index}
                            className="w-[calc(25%-0.75rem)] min-w-[140px]"
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8, x: -20 }}
                            layout
                        >
                            <CompareSlot
                                item={slot}
                                index={index}
                                onRemove={() => removeSlot(index)}
                                onSelect={() => selectSlot(index)}
                                isSelected={selectedSlotIndex === index}
                                maxScore={maxScore}
                            />
                        </motion.div>
                    ))}
                </AnimatePresence>
                {compareSlots.length < 8 && (
                    <motion.button
                        onClick={() => setCompareSlots([...compareSlots, null])}
                        whileHover={{ borderColor: 'rgba(0, 240, 255, 0.5)' }}
                        className="w-[calc(25%-0.75rem)] min-w-[140px] h-[120px] border-2 border-dashed border-gray-600 rounded-lg flex flex-col items-center justify-center gap-2 text-gray-500 hover:text-jarvis-cyan transition-colors"
                    >
                        <Plus size={24} />
                        <span className="text-xs font-orbitron">ADD SLOT</span>
                    </motion.button>
                )}
            </motion.div>

            {/* Clear button */}
            <AnimatePresence>
                {filledSlots.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="flex justify-end mb-3"
                    >
                        <motion.button
                            onClick={clearAll}
                            whileHover={{ color: '#f87171' }}
                            className="text-xs text-gray-500 flex items-center gap-1 transition-colors"
                        >
                            <Trash2 size={12} />
                            Clear All
                        </motion.button>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Performance Comparison */}
            <AnimatePresence>
                {filledSlots.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl p-5 mb-4 shadow-lg"
                    >
                        <h3 className="text-sm font-orbitron text-gray-400 mb-4 flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-jarvis-cyan animate-pulse" />
                            PERFORMANCE COMPARISON
                        </h3>
                        <div className="space-y-3">
                            {filledSlots.map((item, i) => {
                                const percentage = ((item.score || 0) / maxScore) * 100;
                                return (
                                    <div key={i} className="flex items-center gap-3">
                                        <span className="w-32 text-xs text-gray-300 truncate">{item.name}</span>
                                        <div className="flex-1 h-6 bg-black/50 rounded-lg overflow-hidden border border-white/5">
                                            <motion.div
                                                className="h-full flex items-center justify-end pr-3"
                                                initial={{ width: 0 }}
                                                animate={{ width: `${percentage}%` }}
                                                transition={{ duration: 1, ease: "easeOut", delay: i * 0.1 }}
                                                style={{
                                                    background: `linear-gradient(90deg, ${TYPE_COLORS[item.type]}22, ${TYPE_COLORS[item.type]})`,
                                                    boxShadow: `0 0 15px ${TYPE_COLORS[item.type]}40`
                                                }}
                                            >
                                                <span className="text-[10px] text-white font-mono font-bold">
                                                    {(item.score || 0).toLocaleString()}
                                                </span>
                                            </motion.div>
                                        </div>
                                        <motion.span
                                            className="text-[10px] px-2 py-1 rounded-lg font-bold"
                                            style={{ backgroundColor: `${TYPE_COLORS[item.type]}20`, color: TYPE_COLORS[item.type] }}
                                            animate={{ opacity: [0.7, 1, 0.7] }}
                                            transition={{ duration: 2, repeat: Infinity }}
                                        >
                                            {item.type.toUpperCase()}
                                        </motion.span>
                                    </div>
                                );
                            })}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Hardware Database Browser */}
            <motion.div
                variants={itemVariants}
                className="flex-1 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden flex flex-col min-h-0 shadow-lg"
            >
                {/* Search Header */}
                <div className="p-4 border-b border-white/5 flex items-center gap-3">
                    <Database size={16} className="text-jarvis-cyan/60" />
                    <div className="flex-1 flex items-center gap-2 bg-black/40 rounded-xl px-4 py-2 border border-white/5">
                        <Search size={14} className="text-gray-500" />
                        <input
                            ref={searchRef}
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search hardware..."
                            className="flex-1 bg-transparent border-none text-sm text-white placeholder:text-gray-500 focus:outline-none"
                        />
                        {searchQuery && (
                            <motion.button
                                onClick={() => setSearchQuery('')}
                                whileHover={{ scale: 1.1 }}
                                className="text-gray-500 hover:text-jarvis-cyan"
                            >
                                <X size={14} />
                            </motion.button>
                        )}
                    </div>
                    <span className="text-xs text-gray-500 font-mono">{getFilteredCount()} items</span>
                </div>

                {/* Database List */}
                <motion.div
                    className="flex-1 overflow-y-auto p-3 space-y-1 min-h-0 custom-scrollbar"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                >
                    {dbLoading ? (
                        <motion.div
                            className="text-center py-8 text-jarvis-cyan text-sm font-orbitron"
                            animate={{ opacity: [0.5, 1, 0.5] }}
                            transition={{ duration: 1.5, repeat: Infinity }}
                        >
                            Loading hardware database...
                        </motion.div>
                    ) : searchQuery.length >= 2 ? (
                        searchResults.length > 0 ? (
                            searchResults.map((item, i) => (
                                <motion.div key={i} variants={itemVariants}>
                                    <DatabaseItem item={item} onAdd={addToComparison} />
                                </motion.div>
                            ))
                        ) : (
                            <div className="text-center py-4 text-gray-500 text-sm">No results found</div>
                        )
                    ) : (
                        getDatabaseItems().map((item, i) => (
                            <motion.div key={i} variants={itemVariants}>
                                <DatabaseItem item={item} onAdd={addToComparison} />
                            </motion.div>
                        ))
                    )}
                </motion.div>
            </motion.div>
        </motion.div>
    );
};

// Comparison Slot Component with 3D Tilt
const CompareSlot = ({ item, index, onRemove, onSelect, isSelected, maxScore }) => {
    if (!item) {
        return (
            <motion.div
                onClick={onSelect}
                whileHover={{ borderColor: 'rgba(0, 240, 255, 0.4)' }}
                className={`border-2 border-dashed rounded-xl h-32 flex flex-col items-center justify-center bg-black/30 backdrop-blur cursor-pointer transition-all relative group ${isSelected
                    ? 'border-jarvis-cyan bg-jarvis-cyan/10'
                    : 'border-gray-700'
                    }`}
            >
                <motion.button
                    onClick={(e) => { e.stopPropagation(); onRemove(); }}
                    whileHover={{ scale: 1.2, color: '#f87171' }}
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-gray-500"
                >
                    <X size={12} />
                </motion.button>
                <Plus size={20} className={isSelected ? 'text-jarvis-cyan' : 'text-gray-600'} />
                <span className={`text-[10px] mt-1 font-orbitron ${isSelected ? 'text-jarvis-cyan' : 'text-gray-600'}`}>
                    {isSelected ? 'SELECTED' : `SLOT ${index + 1}`}
                </span>
            </motion.div>
        );
    }

    const Icon = TYPE_ICONS[item.type] || Cpu;
    const percentage = ((item.score || 0) / maxScore) * 100;

    return (
        <TiltCard>
            <div
                className="border rounded-xl h-32 p-3 bg-black/50 backdrop-blur-xl flex flex-col relative group overflow-hidden shadow-lg"
                style={{ borderColor: `${TYPE_COLORS[item.type]}40` }}
            >
                {/* Hover glow */}
                <div
                    className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                    style={{ background: `radial-gradient(circle at center, ${TYPE_COLORS[item.type]}10, transparent)` }}
                />

                <motion.button
                    onClick={onRemove}
                    whileHover={{ scale: 1.2, color: '#f87171' }}
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-gray-500 z-10"
                >
                    <X size={12} />
                </motion.button>

                <motion.div
                    className="absolute top-2 left-2 px-2 py-0.5 rounded-lg text-[8px] font-bold"
                    style={{ backgroundColor: `${TYPE_COLORS[item.type]}20`, color: TYPE_COLORS[item.type] }}
                    animate={{ opacity: [0.8, 1, 0.8] }}
                    transition={{ duration: 2, repeat: Infinity }}
                >
                    {item.type.toUpperCase()}
                </motion.div>

                <div className="flex-1 flex flex-col items-center justify-center mt-3 relative z-10">
                    <Icon size={20} style={{ color: TYPE_COLORS[item.type] }} />
                    <h3 className="text-[11px] text-white text-center mt-1 line-clamp-2 leading-tight">{item.name}</h3>
                </div>

                <div className="text-center relative z-10">
                    <div className="text-lg font-orbitron font-bold" style={{ color: TYPE_COLORS[item.type] }}>
                        {(item.score || 0).toLocaleString()}
                    </div>
                </div>

                <div className="h-1.5 bg-black/60 rounded-full mt-1 overflow-hidden">
                    <motion.div
                        className="h-full rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${percentage}%` }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        style={{
                            backgroundColor: TYPE_COLORS[item.type],
                            boxShadow: `0 0 8px ${TYPE_COLORS[item.type]}`
                        }}
                    />
                </div>
            </div>
        </TiltCard>
    );
};

// Database Item Component
const DatabaseItem = ({ item, onAdd }) => {
    const Icon = TYPE_ICONS[item.type] || Cpu;

    return (
        <motion.button
            onClick={() => onAdd(item)}
            whileHover={{ backgroundColor: 'rgba(0, 240, 255, 0.08)' }}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all group"
        >
            <Icon size={16} style={{ color: TYPE_COLORS[item.type] }} />
            <span className="flex-1 text-sm text-white truncate">{item.name}</span>

            {item.specs && (
                <span className="text-[10px] text-gray-500 hidden md:block truncate max-w-32">
                    {item.type === 'cpu' && item.specs.cores && `${item.specs.cores}C`}
                    {item.type === 'gpu' && item.specs.vram && `${item.specs.vram}`}
                    {item.type === 'ssd' && item.specs.speeds && `${item.specs.speeds}`}
                    {item.type === 'ram' && item.specs.read_speed && `${item.specs.read_speed} GB/s`}
                </span>
            )}

            <span className="text-xs text-gray-400 font-mono w-16 text-right">{(item.score || 0).toLocaleString()}</span>
            <span
                className="text-[9px] px-2 py-1 rounded-lg font-semibold"
                style={{ backgroundColor: `${TYPE_COLORS[item.type]}15`, color: TYPE_COLORS[item.type] }}
            >
                {item.type.toUpperCase()}
            </span>
            <motion.div
                whileHover={{ scale: 1.2 }}
                className="text-gray-600 group-hover:text-jarvis-cyan transition-colors"
            >
                <Plus size={14} />
            </motion.div>
        </motion.button>
    );
};

export default ComparePanel;
