import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { Plus, Trash2, FileText, StickyNote } from 'lucide-react';
import { getNotes, createNote, deleteNote } from '../api';

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

const NotesPanel = () => {
    const [notes, setNotes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [newNote, setNewNote] = useState('');
    const [creating, setCreating] = useState(false);

    const fetchNotes = async () => {
        try {
            const data = await getNotes();
            setNotes(data);
        } catch (err) {
            console.error('Failed to fetch notes:', err);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchNotes();
    }, []);

    const handleCreate = async () => {
        if (!newNote.trim()) return;
        setCreating(true);
        try {
            await createNote(newNote);
            setNewNote('');
            fetchNotes();
        } catch (err) {
            console.error('Failed to create note:', err);
        }
        setCreating(false);
    };

    const handleDelete = async (id) => {
        setNotes(notes.filter(n => n.id !== id));
        try {
            await deleteNote(id);
        } catch (err) {
            console.error('Failed to delete note:', err);
            fetchNotes(); // Revert on error
        }
    };

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.08, delayChildren: 0.1 }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20, scale: 0.95 },
        visible: { opacity: 1, y: 0, scale: 1 },
        exit: { opacity: 0, x: -50, scale: 0.9, transition: { duration: 0.2 } }
    };

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <motion.div
                    className="text-jarvis-cyan font-orbitron text-lg tracking-widest"
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                >
                    LOADING NOTES...
                </motion.div>
            </div>
        );
    }

    return (
        <motion.div
            className="flex-1 flex flex-col overflow-hidden px-2"
            initial="hidden"
            animate="visible"
            variants={containerVariants}
        >
            {/* Header */}
            <motion.div variants={itemVariants} className="flex items-center gap-3 mb-6 pb-4 border-b border-jarvis-cyan/20">
                <FileText size={28} className="text-jarvis-cyan" />
                <h2 className="text-2xl font-orbitron text-jarvis-cyan tracking-widest drop-shadow-[0_0_10px_rgba(0,240,255,0.4)]">
                    NOTES
                </h2>
                <span className="text-sm text-gray-400 font-mono ml-2">// {notes.length} ENTRIES</span>
            </motion.div>

            {/* New Note Input */}
            <motion.div variants={itemVariants} className="mb-6">
                <div className="flex gap-3 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl p-4 shadow-lg">
                    <input
                        type="text"
                        value={newNote}
                        onChange={(e) => setNewNote(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                        placeholder="Type a new note..."
                        className="flex-1 bg-transparent border-none text-white placeholder:text-gray-500 font-mono focus:outline-none text-sm"
                    />
                    <motion.button
                        onClick={handleCreate}
                        disabled={creating || !newNote.trim()}
                        whileHover={{ scale: 1.05, boxShadow: '0 0 15px rgba(0, 240, 255, 0.3)' }}
                        whileTap={{ scale: 0.95 }}
                        className="px-5 py-2 bg-jarvis-cyan/10 border border-jarvis-cyan/40 rounded-xl text-jarvis-cyan font-orbitron text-sm hover:bg-jarvis-cyan/20 transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                        <Plus size={16} />
                        ADD
                    </motion.button>
                </div>
            </motion.div>

            {/* Notes List */}
            <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
                <AnimatePresence mode="popLayout">
                    {notes.length === 0 ? (
                        <motion.div
                            key="empty"
                            variants={itemVariants}
                            className="text-gray-500 text-center py-12 font-orbitron"
                        >
                            <StickyNote size={48} className="mx-auto mb-4 opacity-30" />
                            <p className="tracking-widest">NO NOTES YET</p>
                            <p className="text-xs mt-2 text-gray-600">Start typing above to create one</p>
                        </motion.div>
                    ) : (
                        notes.map((note) => (
                            <motion.div
                                key={note.id}
                                variants={itemVariants}
                                exit={{ opacity: 0, x: -100, scale: 0.8 }}
                                layout
                            >
                                <TiltCard>
                                    <div className="group bg-black/50 backdrop-blur-xl border border-white/10 rounded-2xl p-5 hover:border-jarvis-cyan/30 transition-all duration-300 relative overflow-hidden shadow-lg">
                                        {/* Hover glow */}
                                        <div className="absolute inset-0 bg-gradient-to-br from-jarvis-cyan/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

                                        <div className="flex justify-between items-start relative z-10">
                                            <div className="flex-1">
                                                <p className="text-white font-mono whitespace-pre-wrap text-sm leading-relaxed">{note.content}</p>
                                                <p className="text-xs text-gray-500 mt-3 font-orbitron tracking-wider">{note.created_at}</p>
                                            </div>
                                            <motion.button
                                                onClick={() => handleDelete(note.id)}
                                                whileHover={{ scale: 1.2, color: '#f87171' }}
                                                whileTap={{ scale: 0.9 }}
                                                className="p-2 text-gray-500 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                                            >
                                                <Trash2 size={16} />
                                            </motion.button>
                                        </div>
                                    </div>
                                </TiltCard>
                            </motion.div>
                        ))
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
};

export default NotesPanel;
