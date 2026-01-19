import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Clock, Bell } from 'lucide-react';
import { getReminders, createReminder, deleteReminder } from '../api';

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
        try {
            await deleteReminder(jobId);
            setReminders(reminders.filter(r => r.job_id !== jobId));
        } catch (err) {
            console.error('Failed to delete reminder:', err);
        }
    };

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <div className="text-jarvis-cyan animate-pulse font-orbitron">LOADING REMINDERS...</div>
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col overflow-hidden animate-in fade-in duration-500">
            <h2 className="text-2xl font-orbitron text-jarvis-cyan mb-4 tracking-wider border-b border-jarvis-cyan/20 pb-2 flex items-center gap-3">
                <Bell size={24} />
                REMINDERS // <span className="text-sm text-gray-400">{reminders.length} ACTIVE</span>
            </h2>

            {/* Add Reminder Button/Form */}
            {!showForm ? (
                <button
                    onClick={() => setShowForm(true)}
                    className="mb-4 px-4 py-3 bg-jarvis-cyan/10 border border-jarvis-cyan/30 rounded-lg text-jarvis-cyan hover:bg-jarvis-cyan/20 transition-colors flex items-center gap-2 w-fit"
                >
                    <Plus size={18} />
                    NEW REMINDER
                </button>
            ) : (
                <div className="mb-4 bg-black/40 border border-jarvis-cyan/30 rounded-lg p-4 space-y-3">
                    <input
                        type="text"
                        value={newReminder.text}
                        onChange={(e) => setNewReminder({ ...newReminder, text: e.target.value })}
                        placeholder="Reminder text..."
                        className="w-full bg-black/40 border border-jarvis-cyan/20 rounded-lg px-4 py-2 text-white placeholder:text-gray-500 font-mono focus:outline-none focus:border-jarvis-cyan/60"
                    />
                    <div className="flex items-center gap-4">
                        <label className="text-gray-400 text-sm">Time:</label>
                        <input
                            type="number"
                            min="0"
                            max="23"
                            value={newReminder.hour}
                            onChange={(e) => setNewReminder({ ...newReminder, hour: parseInt(e.target.value) || 0 })}
                            className="w-16 bg-black/40 border border-jarvis-cyan/20 rounded px-2 py-1 text-white text-center"
                        />
                        <span className="text-jarvis-cyan">:</span>
                        <input
                            type="number"
                            min="0"
                            max="59"
                            value={newReminder.minute}
                            onChange={(e) => setNewReminder({ ...newReminder, minute: parseInt(e.target.value) || 0 })}
                            className="w-16 bg-black/40 border border-jarvis-cyan/20 rounded px-2 py-1 text-white text-center"
                        />
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={handleCreate}
                            disabled={creating || !newReminder.text.trim()}
                            className="px-4 py-2 bg-jarvis-cyan/20 border border-jarvis-cyan/40 rounded-lg text-jarvis-cyan hover:bg-jarvis-cyan/30 transition-colors disabled:opacity-50"
                        >
                            CREATE
                        </button>
                        <button
                            onClick={() => setShowForm(false)}
                            className="px-4 py-2 bg-black/40 border border-gray-600 rounded-lg text-gray-400 hover:text-white transition-colors"
                        >
                            CANCEL
                        </button>
                    </div>
                </div>
            )}

            {/* Reminders List */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                {reminders.length === 0 ? (
                    <div className="text-gray-500 text-center py-8 font-orbitron">NO ACTIVE REMINDERS</div>
                ) : (
                    reminders.map((reminder) => (
                        <div
                            key={reminder.job_id}
                            className="group bg-black/40 border border-jarvis-cyan/20 rounded-lg p-4 hover:border-jarvis-cyan/40 transition-colors"
                        >
                            <div className="flex justify-between items-start">
                                <div className="flex-1">
                                    <p className="text-jarvis-cyan font-orbitron text-sm">{reminder.job_id}</p>
                                    <p className="text-gray-400 text-xs mt-1 font-mono">{reminder.trigger}</p>
                                    {reminder.next_run && (
                                        <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                                            <Clock size={12} />
                                            Next: {reminder.next_run}
                                        </p>
                                    )}
                                </div>
                                <button
                                    onClick={() => handleDelete(reminder.job_id)}
                                    className="p-2 text-gray-500 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default RemindersPanel;
