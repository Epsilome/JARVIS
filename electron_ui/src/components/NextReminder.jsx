import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Bell, Clock } from 'lucide-react';
import { getReminders } from '../api';

const NextReminder = () => {
    const [nextReminder, setNextReminder] = useState(null);
    const [countdown, setCountdown] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchReminders = async () => {
            try {
                const data = await getReminders();
                if (data && data.length > 0) {
                    // Find the reminder with the earliest next_run
                    const sorted = data
                        .filter(r => r.next_run)
                        .sort((a, b) => new Date(a.next_run) - new Date(b.next_run));

                    if (sorted.length > 0) {
                        setNextReminder(sorted[0]);
                    } else {
                        setNextReminder(null);
                    }
                } else {
                    setNextReminder(null);
                }
            } catch (err) {
                console.error('Reminders fetch error:', err);
            }
            setLoading(false);
        };

        fetchReminders();
        const interval = setInterval(fetchReminders, 60000); // Refresh every minute
        return () => clearInterval(interval);
    }, []);

    // Countdown timer
    useEffect(() => {
        if (!nextReminder?.next_run) {
            setCountdown('');
            return;
        }

        const updateCountdown = () => {
            const now = new Date();
            const target = new Date(nextReminder.next_run);
            const diff = target - now;

            if (diff <= 0) {
                setCountdown('Now!');
                return;
            }

            const hours = Math.floor(diff / (1000 * 60 * 60));
            const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const secs = Math.floor((diff % (1000 * 60)) / 1000);

            if (hours > 0) {
                setCountdown(`${hours}h ${mins}m`);
            } else if (mins > 0) {
                setCountdown(`${mins}m ${secs}s`);
            } else {
                setCountdown(`${secs}s`);
            }
        };

        updateCountdown();
        const timer = setInterval(updateCountdown, 1000);
        return () => clearInterval(timer);
    }, [nextReminder]);

    const accentStyle = { color: 'var(--accent-color)' };
    const borderStyle = { border: '1px solid rgba(var(--accent-color-rgb), 0.3)' };

    // Extract reminder text from trigger description
    const getReminderText = (trigger) => {
        if (!trigger) return 'Reminder';
        // Trigger format might be like "cron[minute='30', hour='14']" or similar
        return trigger.split('[')[0] || 'Reminder';
    };

    if (loading) {
        return (
            <div className="rounded-xl p-4 bg-black/40 backdrop-blur-md" style={borderStyle}>
                <div className="text-xs text-gray-500 animate-pulse">Loading...</div>
            </div>
        );
    }

    if (!nextReminder) {
        return null; // Don't show widget if no reminders
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl p-4 bg-black/40 backdrop-blur-md"
            style={borderStyle}
        >
            <h3 className="text-xs font-orbitron tracking-wider mb-3 flex items-center gap-2" style={accentStyle}>
                <Bell size={14} />
                NEXT REMINDER
            </h3>

            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Clock size={18} className="text-yellow-400" />
                        <motion.div
                            className="absolute -inset-1 rounded-full bg-yellow-400/20"
                            animate={{ scale: [1, 1.3, 1], opacity: [0.3, 0.1, 0.3] }}
                            transition={{ duration: 1.5, repeat: Infinity }}
                        />
                    </div>
                    <div>
                        <div className="text-xs text-gray-500">
                            {new Date(nextReminder.next_run).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-lg font-orbitron text-yellow-400">{countdown}</div>
                </div>
            </div>
        </motion.div>
    );
};

export default NextReminder;
