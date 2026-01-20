import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { Plus, Trash2, Clock, Bell, X } from 'lucide-react';
import { getReminders, createReminder, deleteReminder } from '../api';

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

const RemindersPanel = () => {
    const [reminders, setReminders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [newReminder, setNewReminder] = useState({ text: '', hour: 9, minute: 0 });
    const [creating, setCreating] = useState(false);

    const fetchReminders = async () => {
        try {
            const data = await getReminders();
            setReminders(data);
        } catch (err) {
            console.error('Failed to fetch reminders:', err);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchReminders();
    }, []);

    const handleCreate = async () => {
        if (!newReminder.text.trim()) return;
        setCreating(true);
        try {
            await createReminder(newReminder.text, newReminder.hour, newReminder.minute);
            setNewReminder({ text: '', hour: 9, minute: 0 });
            setShowForm(false);
            fetchReminders();
        } catch (err) {
            console.error('Failed to create reminder:', err);
        }
        setCreating(false);
    };

    const handleDelete = async (jobId) => {
        setReminders(reminders.filter(r => r.job_id !== jobId));
        try {
            await deleteReminder(jobId);
        } catch (err) {
            console.error('Failed to delete reminder:', err);
            fetchReminders();
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
        visible: { opacity: 1, y: 0, scale: 1 }
    };

    const formVariants = {
        hidden: { opacity: 0, height: 0, marginBottom: 0 },
        visible: { opacity: 1, height: 'auto', marginBottom: 24 },
        exit: { opacity: 0, height: 0, marginBottom: 0 }
    };

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <motion.div
                    className="text-jarvis-cyan font-orbitron text-lg tracking-widest"
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                >
                    LOADING REMINDERS...
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
                <Bell size={28} className="text-jarvis-cyan" />
                <h2 className="text-2xl font-orbitron text-jarvis-cyan tracking-widest drop-shadow-[0_0_10px_rgba(0,240,255,0.4)]">
                    REMINDERS
                </h2>
                <span className="text-sm text-gray-400 font-mono ml-2">// {reminders.length} ACTIVE</span>
            </motion.div>

            {/* Add Reminder Button */}
            <AnimatePresence mode="wait">
                {!showForm && (
                    <motion.div
                        key="add-btn"
                        variants={itemVariants}
                        exit={{ opacity: 0, scale: 0.9 }}
                        className="mb-6"
                    >
                        <motion.button
                            onClick={() => setShowForm(true)}
                            whileHover={{ backgroundColor: 'rgba(0, 240, 255, 0.1)' }}
                            whileTap={{ scale: 0.99 }}
                            className="w-full px-6 py-4 bg-black/40 backdrop-blur-xl border border-jarvis-cyan/30 border-dashed rounded-2xl text-jarvis-cyan font-orbitron text-sm hover:border-jarvis-cyan/60 transition-all duration-300 flex items-center justify-center gap-3"
                        >
                            <Plus size={20} />
                            NEW REMINDER
                        </motion.button>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* New Reminder Form */}
            <AnimatePresence>
                {showForm && (
                    <motion.div
                        key="form"
                        variants={formVariants}
                        initial="hidden"
                        animate="visible"
                        exit="exit"
                        className="overflow-hidden"
                    >
                        <div className="bg-black/50 backdrop-blur-xl border border-jarvis-cyan/30 rounded-2xl p-6 space-y-4 shadow-lg">
                            <div className="flex justify-between items-center">
                                <h3 className="text-sm font-orbitron text-jarvis-cyan">CREATE REMINDER</h3>
                                <motion.button
                                    onClick={() => setShowForm(false)}
                                    whileHover={{ scale: 1.1 }}
                                    whileTap={{ scale: 0.9 }}
                                    className="p-1 text-gray-400 hover:text-white"
                                >
                                    <X size={18} />
                                </motion.button>
                            </div>
                            <input
                                type="text"
                                value={newReminder.text}
                                onChange={(e) => setNewReminder({ ...newReminder, text: e.target.value })}
                                placeholder="Reminder text..."
                                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-gray-500 font-mono focus:outline-none focus:border-jarvis-cyan/50 text-sm"
                            />
                            <div className="flex items-center gap-4">
                                <Clock size={16} className="text-gray-400" />
                                <span className="text-gray-400 text-sm font-mono">Time:</span>
                                <input
                                    type="number"
                                    min="0"
                                    max="23"
                                    value={newReminder.hour}
                                    onChange={(e) => setNewReminder({ ...newReminder, hour: parseInt(e.target.value) || 0 })}
                                    className="w-16 bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-center font-mono focus:outline-none focus:border-jarvis-cyan/50"
                                />
                                <span className="text-jarvis-cyan text-xl font-bold">:</span>
                                <input
                                    type="number"
                                    min="0"
                                    max="59"
                                    value={newReminder.minute}
                                    onChange={(e) => setNewReminder({ ...newReminder, minute: parseInt(e.target.value) || 0 })}
                                    className="w-16 bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-center font-mono focus:outline-none focus:border-jarvis-cyan/50"
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <motion.button
                                    onClick={handleCreate}
                                    disabled={creating || !newReminder.text.trim()}
                                    whileHover={{ backgroundColor: 'rgba(0, 240, 255, 0.25)' }}
                                    whileTap={{ scale: 0.99 }}
                                    className="flex-1 px-4 py-3 bg-jarvis-cyan/20 border border-jarvis-cyan/50 rounded-xl text-jarvis-cyan font-orbitron text-sm hover:border-jarvis-cyan transition-all duration-300 disabled:opacity-50"
                                >
                                    CREATE
                                </motion.button>
                                <motion.button
                                    onClick={() => setShowForm(false)}
                                    whileTap={{ scale: 0.99 }}
                                    className="px-6 py-3 bg-black/40 border border-gray-600 rounded-xl text-gray-400 font-orbitron text-sm hover:text-white hover:border-gray-400 transition-all duration-300"
                                >
                                    CANCEL
                                </motion.button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Reminders List */}
            <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
                <AnimatePresence mode="popLayout">
                    {reminders.length === 0 ? (
                        <motion.div
                            key="empty"
                            variants={itemVariants}
                            className="text-gray-500 text-center py-12 font-orbitron"
                        >
                            <Bell size={48} className="mx-auto mb-4 opacity-30" />
                            <p className="tracking-widest">NO ACTIVE REMINDERS</p>
                            <p className="text-xs mt-2 text-gray-600">Click above to create one</p>
                        </motion.div>
                    ) : (
                        reminders.map((reminder) => (
                            <motion.div
                                key={reminder.job_id}
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
                                                <p className="text-jarvis-cyan font-orbitron text-sm tracking-wide">{reminder.job_id}</p>
                                                <p className="text-gray-400 text-xs mt-1 font-mono">{reminder.trigger}</p>
                                                {reminder.next_run && (
                                                    <motion.p
                                                        className="text-xs text-gray-500 mt-2 flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-lg w-fit"
                                                        animate={{ opacity: [0.7, 1, 0.7] }}
                                                        transition={{ duration: 2, repeat: Infinity }}
                                                    >
                                                        <Clock size={12} className="text-jarvis-cyan" />
                                                        Next: {reminder.next_run}
                                                    </motion.p>
                                                )}
                                            </div>
                                            <motion.button
                                                onClick={() => handleDelete(reminder.job_id)}
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

export default RemindersPanel;
