import React, { useState, useEffect, useRef } from 'react';
import { Search, Cpu, Monitor, HardDrive, MemoryStick, X, Plus, Scale, Trash2, Database, ChevronDown } from 'lucide-react';
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

const ComparePanel = () => {
    const [compareSlots, setCompareSlots] = useState([]);
    const [selectedSlotIndex, setSelectedSlotIndex] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [typeFilter, setTypeFilter] = useState('all');
    const [database, setDatabase] = useState({ cpus: [], gpus: [], ssds: [], ram: [], total: 0 });
    const [dbLoading, setDbLoading] = useState(true);
    const [expandedSection, setExpandedSection] = useState('gpu');
    const searchRef = useRef(null);

    // Load hardware database on mount
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

    // Search hardware - filter local database instead of calling API
    useEffect(() => {
        if (!searchQuery.trim() || searchQuery.length < 2) {
            setSearchResults([]);
            return;
        }

        // Filter local database
        const query = searchQuery.toLowerCase().trim();
        const allItems = [
            ...database.cpus,
            ...database.gpus,
            ...database.ssds,
            ...database.ram
        ];

        // Filter by type if not 'all'
        let itemsToSearch = allItems;
        if (typeFilter !== 'all') {
            itemsToSearch = allItems.filter(item => item.type === typeFilter);
        }

        // Filter by search query
        const filtered = itemsToSearch.filter(item =>
            item.name?.toLowerCase().includes(query)
        );

        // Sort by score descending
        filtered.sort((a, b) => (b.score || 0) - (a.score || 0));

        setSearchResults(filtered.slice(0, 50));
    }, [searchQuery, typeFilter, database]);

    // Add item to comparison - fill selected empty slot or append
    const addToComparison = (item) => {
        // If a slot is selected and it's empty, fill it
        if (selectedSlotIndex !== null && compareSlots[selectedSlotIndex] === null) {
            const newSlots = [...compareSlots];
            newSlots[selectedSlotIndex] = item;
            setCompareSlots(newSlots);
            setSelectedSlotIndex(null);
        } else {
            // Find first empty slot
            const emptyIndex = compareSlots.findIndex(s => s === null);
            if (emptyIndex !== -1) {
                const newSlots = [...compareSlots];
                newSlots[emptyIndex] = item;
                setCompareSlots(newSlots);
            } else if (compareSlots.length < 8) {
                // No empty slots, add new one
                setCompareSlots([...compareSlots, item]);
            }
        }
    };

    // Select an empty slot to fill
    const selectSlot = (index) => {
        if (compareSlots[index] === null) {
            setSelectedSlotIndex(selectedSlotIndex === index ? null : index);
        }
    };

    // Remove item from slot
    const removeSlot = (index) => {
        setCompareSlots(compareSlots.filter((_, i) => i !== index));
    };

    // Clear all slots
    const clearAll = () => {
        setCompareSlots([]);
    };

    // Get max score for bar scaling (filter out null slots)
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

    return (
        <div className="flex flex-col h-full animate-in slide-in-from-bottom duration-500">
            {/* Header */}
            <div className="flex justify-between items-end mb-4 border-b border-jarvis-cyan/20 pb-2">
                <h2 className="text-lg font-orbitron text-jarvis-cyan tracking-wider flex items-center gap-2">
                    <Scale size={20} />
                    HARDWARE COMPARE
                </h2>
                <div className="flex gap-2">
                    {['all', 'cpu', 'gpu', 'ssd', 'ram'].map(type => (
                        <button
                            key={type}
                            onClick={() => setTypeFilter(type)}
                            className={`px-3 py-1 text-xs rounded border transition-colors ${typeFilter === type
                                ? 'border-jarvis-cyan bg-jarvis-cyan/20 text-jarvis-cyan'
                                : 'border-gray-600 text-gray-400 hover:border-gray-500'
                                }`}
                        >
                            {type.toUpperCase()}
                        </button>
                    ))}
                </div>
            </div>

            {/* SECTION 1: Comparison Slots */}
            <div className="flex flex-wrap gap-3 mb-4">
                {compareSlots.map((slot, index) => (
                    <div key={index} className="w-[calc(25%-0.75rem)] min-w-[140px]">
                        <CompareSlot
                            item={slot}
                            index={index}
                            onRemove={() => removeSlot(index)}
                            onSelect={() => selectSlot(index)}
                            isSelected={selectedSlotIndex === index}
                            maxScore={maxScore}
                        />
                    </div>
                ))}
                {compareSlots.length < 8 && (
                    <button
                        onClick={() => setCompareSlots([...compareSlots, null])}
                        className="w-[calc(25%-0.75rem)] min-w-[140px] h-[120px] border-2 border-dashed border-gray-600 hover:border-jarvis-cyan/50 rounded-lg flex flex-col items-center justify-center gap-2 text-gray-500 hover:text-jarvis-cyan transition-colors"
                    >
                        <Plus size={24} />
                        <span className="text-xs font-orbitron">ADD SLOT</span>
                    </button>
                )}
            </div>

            {/* Clear button */}
            {filledSlots.length > 0 && (
                <div className="flex justify-end mb-3">
                    <button
                        onClick={clearAll}
                        className="text-xs text-gray-500 hover:text-red-400 flex items-center gap-1 transition-colors"
                    >
                        <Trash2 size={12} />
                        Clear All
                    </button>
                </div>
            )}

            {/* SECTION 2: Performance Comparison */}
            {filledSlots.length > 0 && (
                <div className="bg-black/30 border border-jarvis-cyan/20 rounded-lg p-4 mb-4">
                    <h3 className="text-sm font-orbitron text-gray-400 mb-3">PERFORMANCE COMPARISON</h3>
                    <div className="space-y-2">
                        {filledSlots.map((item, i) => {
                            const percentage = ((item.score || 0) / maxScore) * 100;
                            return (
                                <div key={i} className="flex items-center gap-3">
                                    <span className="w-28 text-xs text-gray-300 truncate">{item.name}</span>
                                    <div className="flex-1 h-5 bg-black/50 rounded overflow-hidden">
                                        <div
                                            className="h-full transition-all duration-500 flex items-center justify-end pr-2"
                                            style={{
                                                width: `${percentage}%`,
                                                background: `linear-gradient(90deg, ${TYPE_COLORS[item.type]}44, ${TYPE_COLORS[item.type]})`
                                            }}
                                        >
                                            <span className="text-[10px] text-white font-mono">{(item.score || 0).toLocaleString()}</span>
                                        </div>
                                    </div>
                                    <span
                                        className="text-[10px] px-1.5 py-0.5 rounded font-bold"
                                        style={{ backgroundColor: `${TYPE_COLORS[item.type]}20`, color: TYPE_COLORS[item.type] }}
                                    >
                                        {item.type.toUpperCase()}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* SECTION 3: Hardware Database Browser */}
            <div className="flex-1 bg-black/30 border border-jarvis-cyan/20 rounded-lg overflow-hidden flex flex-col min-h-0">
                {/* Search Header */}
                <div className="p-3 border-b border-jarvis-cyan/10 flex items-center gap-3">
                    <Database size={16} className="text-jarvis-cyan/60" />
                    <div className="flex-1 flex items-center gap-2 bg-black/40 rounded px-3 py-1.5">
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
                            <button
                                onClick={() => setSearchQuery('')}
                                className="text-gray-500 hover:text-jarvis-cyan"
                            >
                                <X size={14} />
                            </button>
                        )}
                    </div>
                    <span className="text-xs text-gray-500">{database.total} items</span>
                </div>

                {/* Database List */}
                <div className="flex-1 overflow-y-auto p-2 space-y-1 min-h-0">
                    {dbLoading ? (
                        <div className="text-center py-8 text-jarvis-cyan animate-pulse text-sm">Loading hardware database...</div>
                    ) : searchQuery.length >= 2 ? (
                        // Show search results (locally filtered, instant)
                        searchResults.length > 0 ? (
                            searchResults.map((item, i) => (
                                <DatabaseItem key={i} item={item} onAdd={addToComparison} />
                            ))
                        ) : (
                            <div className="text-center py-4 text-gray-500 text-sm">No results found</div>
                        )
                    ) : (
                        // Show database browser
                        getDatabaseItems().map((item, i) => (
                            <DatabaseItem key={i} item={item} onAdd={addToComparison} />
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

// Comparison Slot Component
const CompareSlot = ({ item, index, onRemove, onSelect, isSelected, maxScore }) => {
    if (!item) {
        return (
            <div
                onClick={onSelect}
                className={`border-2 border-dashed rounded-lg h-32 flex flex-col items-center justify-center bg-black/20 cursor-pointer transition-all relative group ${isSelected
                        ? 'border-jarvis-cyan bg-jarvis-cyan/10'
                        : 'border-gray-700 hover:border-gray-500'
                    }`}
            >
                {/* Remove button for empty slot */}
                <button
                    onClick={(e) => { e.stopPropagation(); onRemove(); }}
                    className="absolute top-1.5 right-1.5 opacity-0 group-hover:opacity-100 transition-opacity text-gray-500 hover:text-red-400"
                >
                    <X size={12} />
                </button>
                <Plus size={20} className={isSelected ? 'text-jarvis-cyan' : 'text-gray-600'} />
                <span className={`text-[10px] mt-1 ${isSelected ? 'text-jarvis-cyan' : 'text-gray-600'}`}>
                    {isSelected ? 'SELECTED' : `SLOT ${index + 1}`}
                </span>
            </div>
        );
    }

    const Icon = TYPE_ICONS[item.type] || Cpu;
    const percentage = ((item.score || 0) / maxScore) * 100;

    return (
        <div
            className="border rounded-lg h-32 p-3 bg-black/40 flex flex-col relative group"
            style={{ borderColor: `${TYPE_COLORS[item.type]}40` }}
        >
            {/* Remove button */}
            <button
                onClick={onRemove}
                className="absolute top-1.5 right-1.5 opacity-0 group-hover:opacity-100 transition-opacity text-gray-500 hover:text-red-400"
            >
                <X size={12} />
            </button>

            {/* Type badge */}
            <div
                className="absolute top-1.5 left-1.5 px-1.5 py-0.5 rounded text-[8px] font-bold"
                style={{ backgroundColor: `${TYPE_COLORS[item.type]}20`, color: TYPE_COLORS[item.type] }}
            >
                {item.type.toUpperCase()}
            </div>

            {/* Icon and name */}
            <div className="flex-1 flex flex-col items-center justify-center mt-3">
                <Icon size={20} style={{ color: TYPE_COLORS[item.type] }} />
                <h3 className="text-[11px] text-white text-center mt-1 line-clamp-2 leading-tight">{item.name}</h3>
            </div>

            {/* Score */}
            <div className="text-center">
                <div className="text-lg font-orbitron" style={{ color: TYPE_COLORS[item.type] }}>
                    {(item.score || 0).toLocaleString()}
                </div>
            </div>

            {/* Mini bar */}
            <div className="h-1 bg-gray-800 rounded mt-1 overflow-hidden">
                <div
                    className="h-full"
                    style={{
                        width: `${percentage}%`,
                        backgroundColor: TYPE_COLORS[item.type]
                    }}
                />
            </div>
        </div>
    );
};

// Database Item Component
const DatabaseItem = ({ item, onAdd }) => {
    const Icon = TYPE_ICONS[item.type] || Cpu;
    const isAdded = false; // Could track if already in comparison

    return (
        <button
            onClick={() => onAdd(item)}
            className="w-full flex items-center gap-3 px-3 py-2 rounded hover:bg-jarvis-cyan/10 text-left transition-colors group"
        >
            <Icon size={16} style={{ color: TYPE_COLORS[item.type] }} />
            <span className="flex-1 text-sm text-white truncate">{item.name}</span>

            {/* Specs preview */}
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
                className="text-[9px] px-1.5 py-0.5 rounded font-semibold"
                style={{ backgroundColor: `${TYPE_COLORS[item.type]}15`, color: TYPE_COLORS[item.type] }}
            >
                {item.type.toUpperCase()}
            </span>
            <Plus
                size={14}
                className="text-gray-600 group-hover:text-jarvis-cyan transition-colors"
            />
        </button>
    );
};

export default ComparePanel;
