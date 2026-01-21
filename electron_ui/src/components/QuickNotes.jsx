import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileText, Plus } from 'lucide-react';
import { getNotes } from '../api';

const QuickNotes = () => {
    const [notes, setNotes] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchNotes = async () => {
            try {
                const data = await getNotes();
                // Get latest 3 notes
                setNotes(data.slice(-3).reverse());
            } catch (err) {
                console.error('Notes fetch error:', err);
            }
            setLoading(false);
        };

        fetchNotes();
        // Refresh notes every 30 seconds
        const interval = setInterval(fetchNotes, 30000);
        return () => clearInterval(interval);
    }, []);

    const accentStyle = { color: 'var(--accent-color)' };
    const borderStyle = { border: '1px solid rgba(var(--accent-color-rgb), 0.3)' };

    const truncate = (text, maxLen = 50) => {
        if (!text) return '';
        return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
    };

    return (
        <div
            className="rounded-xl p-4 bg-black/40 backdrop-blur-md"
            style={borderStyle}
        >
            <h3 className="text-xs font-orbitron tracking-wider mb-3 flex items-center gap-2" style={accentStyle}>
                <FileText size={14} />
                QUICK NOTES
            </h3>

            <div className="space-y-2">
                {loading ? (
                    <div className="text-xs text-gray-500 animate-pulse">Loading...</div>
                ) : notes.length === 0 ? (
                    <div className="text-xs text-gray-500 italic">No notes yet</div>
                ) : (
                    notes.map((note, i) => (
                        <motion.div
                            key={note.id || i}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.1 }}
                            className="p-2 rounded bg-black/30 border border-white/5"
                        >
                            <p className="text-xs text-gray-300 leading-relaxed">
                                {truncate(note.content)}
                            </p>
                            {note.created_at && (
                                <p className="text-[9px] text-gray-600 mt-1 font-mono">
                                    {new Date(note.created_at).toLocaleDateString()}
                                </p>
                            )}
                        </motion.div>
                    ))
                )}
            </div>

            {/* Quick add hint */}
            <div className="mt-3 pt-2 border-t border-white/5">
                <div className="flex items-center gap-1 text-[10px] text-gray-600">
                    <Plus size={10} />
                    <span>Use Notes tab to add more</span>
                </div>
            </div>
        </div>
    );
};

export default QuickNotes;
