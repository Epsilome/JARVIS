import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, MapPin, Volume2, Key, Save, Check, AlertCircle, RefreshCw } from 'lucide-react';
import { getConfig, updateConfig, getAvailableVoices } from '../api';

const ConfigPanel = () => {
    const [config, setConfig] = useState(null);
    const [voices, setVoices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [edits, setEdits] = useState({});

    useEffect(() => {
        loadConfig();
        loadVoices();
    }, []);

    const loadConfig = async () => {
        try {
            const data = await getConfig();
            setConfig(data);
            if (data.theme_accent) {
                document.documentElement.setAttribute('data-theme', data.theme_accent);
            }
            setLoading(false);
        } catch (err) {
            console.error(err);
            setLoading(false);
        }
    };

    const loadVoices = async () => {
        try {
            const data = await getAvailableVoices();
            setVoices(data.voices || []);
        } catch (err) {
            console.error(err);
        }
    };

    const handleSave = async () => {
        if (Object.keys(edits).length === 0) return;

        setSaving(true);
        try {
            await updateConfig(edits);
            if (edits.theme_accent) {
                document.documentElement.setAttribute('data-theme', edits.theme_accent);
            }
            setConfig({ ...config, ...edits });
            setEdits({});
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        } catch (err) {
            console.error(err);
        }
        setSaving(false);
    };

    const updateField = (key, value) => {
        setEdits({ ...edits, [key]: value });
    };

    const getCurrentValue = (key) => {
        return edits[key] !== undefined ? edits[key] : config?.[key];
    };

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: { opacity: 1, transition: { staggerChildren: 0.1, delayChildren: 0.1 } }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <motion.div
                    className="font-orbitron text-lg tracking-widest"
                    style={{ color: 'var(--accent-color)' }}
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                >
                    LOADING CONFIGURATION...
                </motion.div>
            </div>
        );
    }

    const hasChanges = Object.keys(edits).length > 0;

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
                className="flex justify-between items-end mb-6 pb-2"
                style={{ borderBottom: '1px solid rgba(var(--accent-color-rgb), 0.2)' }}
            >
                <h2 className="text-lg font-orbitron tracking-wider flex items-center gap-2 drop-shadow-[0_0_10px_rgba(var(--accent-color-rgb),0.4)]" style={{ color: 'var(--accent-color)' }}>
                    <Settings size={20} />
                    CONFIGURATION
                </h2>
                <motion.button
                    onClick={handleSave}
                    disabled={!hasChanges || saving}
                    whileHover={hasChanges ? { scale: 1.02 } : {}}
                    whileTap={hasChanges ? { scale: 0.98 } : {}}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-orbitron transition-all"
                    style={hasChanges ? {
                        backgroundColor: 'rgba(var(--accent-color-rgb), 0.2)',
                        border: '1px solid var(--accent-color)',
                        color: 'var(--accent-color)'
                    } : {
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        color: '#6b7280',
                        cursor: 'not-allowed'
                    }}
                >
                    <AnimatePresence mode="wait">
                        {saving ? (
                            <motion.div key="saving" initial={{ rotate: 0 }} animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>
                                <RefreshCw size={16} />
                            </motion.div>
                        ) : saved ? (
                            <motion.div key="saved" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
                                <Check size={16} />
                            </motion.div>
                        ) : (
                            <Save size={16} />
                        )}
                    </AnimatePresence>
                    {saving ? 'SAVING...' : saved ? 'SAVED!' : 'SAVE CHANGES'}
                </motion.button>
            </motion.div>

            <div className="flex-1 overflow-y-auto pr-2 space-y-5 custom-scrollbar">
                {/* Location Settings */}
                <SettingSection icon={MapPin} title="LOCATION" variants={itemVariants}>
                    <div className="grid grid-cols-2 gap-4">
                        <SettingInput
                            label="Default City"
                            value={getCurrentValue('default_city') || ''}
                            onChange={(v) => updateField('default_city', v)}
                            placeholder="e.g. Casablanca"
                        />
                        <SettingInput
                            label="Default Country"
                            value={getCurrentValue('default_country') || ''}
                            onChange={(v) => updateField('default_country', v)}
                            placeholder="e.g. MA"
                        />
                    </div>
                </SettingSection>

                {/* Voice Settings */}
                <SettingSection icon={Volume2} title="TEXT TO SPEECH" variants={itemVariants}>
                    <div className="space-y-4">
                        <SettingToggle
                            label="TTS Enabled"
                            description="JARVIS speaks responses when voice mode is active"
                            value={getCurrentValue('tts_enabled') ?? true}
                            onChange={(v) => updateField('tts_enabled', v)}
                        />
                        <SettingSelect
                            label="Voice"
                            value={getCurrentValue('tts_voice') || 'af_bella'}
                            onChange={(v) => updateField('tts_voice', v)}
                            options={voices.map(v => ({ value: v.id, label: v.name }))}
                        />
                    </div>
                </SettingSection>

                {/* Theme Settings */}
                <SettingSection icon={Settings} title="THEME" variants={itemVariants}>
                    <div>
                        <label className="block text-xs text-gray-500 mb-3 font-orbitron">Accent Color</label>
                        <div className="flex gap-4">
                            {[
                                { id: 'cyan', color: '#00F0FF', label: 'Cyan' },
                                { id: 'green', color: '#00FF88', label: 'Green' },
                                { id: 'purple', color: '#A855F7', label: 'Purple' },
                                { id: 'amber', color: '#FFB800', label: 'Amber' },
                                { id: 'red', color: '#FF6B6B', label: 'Red' }
                            ].map(theme => (
                                <motion.button
                                    key={theme.id}
                                    onClick={() => updateField('theme_accent', theme.id)}
                                    whileHover={{ scale: 1.1 }}
                                    whileTap={{ scale: 0.95 }}
                                    className={`relative w-12 h-12 rounded-full border-2 transition-all ${getCurrentValue('theme_accent') === theme.id
                                        ? 'border-white shadow-lg'
                                        : 'border-gray-600 hover:border-gray-400'
                                        }`}
                                    style={{ backgroundColor: theme.color }}
                                    title={theme.label}
                                >
                                    {getCurrentValue('theme_accent') === theme.id && (
                                        <motion.div
                                            className="absolute inset-0 rounded-full"
                                            style={{ boxShadow: `0 0 20px ${theme.color}` }}
                                            animate={{ opacity: [0.5, 1, 0.5] }}
                                            transition={{ duration: 1.5, repeat: Infinity }}
                                        />
                                    )}
                                </motion.button>
                            ))}
                        </div>
                    </div>
                </SettingSection>

                {/* API Keys Status */}
                <SettingSection icon={Key} title="API KEYS STATUS" variants={itemVariants}>
                    <div className="grid grid-cols-2 gap-3">
                        {Object.entries(config?.api_keys_status || {}).map(([key, configured], i) => (
                            <motion.div
                                key={key}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: i * 0.05 }}
                                className="flex items-center gap-3 px-4 py-3 bg-black/40 backdrop-blur rounded-xl border border-white/5"
                            >
                                <motion.div
                                    animate={configured ? {} : { scale: [1, 1.2, 1] }}
                                    transition={{ duration: 2, repeat: configured ? 0 : Infinity }}
                                >
                                    {configured ? (
                                        <Check size={16} className="text-green-400" />
                                    ) : (
                                        <AlertCircle size={16} className="text-yellow-400" />
                                    )}
                                </motion.div>
                                <span className="text-sm text-gray-300 uppercase font-mono">{key}</span>
                                <span className={`ml-auto text-xs font-bold ${configured ? 'text-green-400' : 'text-yellow-400'}`}>
                                    {configured ? 'OK' : 'MISSING'}
                                </span>
                            </motion.div>
                        ))}
                    </div>
                </SettingSection>

                {/* Model Info */}
                <SettingSection icon={Settings} title="SYSTEM INFO" variants={itemVariants}>
                    <div className="grid grid-cols-2 gap-4">
                        <motion.div
                            className="px-4 py-4 bg-black/40 backdrop-blur rounded-xl border border-white/5"
                            whileHover={{ borderColor: 'rgba(var(--accent-color-rgb), 0.3)' }}
                        >
                            <div className="text-xs text-gray-500 font-orbitron mb-1">LLM Model</div>
                            <div className="text-sm font-mono font-bold" style={{ color: 'var(--accent-color)' }}>
                                {config?.ollama_model || 'Unknown'}
                            </div>
                        </motion.div>
                    </div>
                </SettingSection>
            </div>
        </motion.div>
    );
};

// Section wrapper with animation
const SettingSection = ({ icon: Icon, title, children, variants }) => (
    <motion.div
        variants={variants}
        className="bg-black/40 backdrop-blur-xl rounded-2xl p-5 border border-white/10 shadow-lg relative overflow-hidden group"
    >
        {/* Hover glow */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

        <h3 className="flex items-center gap-2 text-sm font-orbitron text-gray-400 mb-4 relative z-10">
            <Icon size={16} style={{ color: 'var(--accent-color)' }} />
            {title}
        </h3>
        <div className="relative z-10">{children}</div>
    </motion.div>
);

// Text input
const SettingInput = ({ label, value, onChange, placeholder }) => (
    <div>
        <label className="block text-xs text-gray-500 mb-2 font-orbitron">{label}</label>
        <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className="w-full bg-black/40 rounded-xl px-4 py-3 text-sm text-white placeholder:text-gray-500 focus:outline-none border border-white/10 focus:border-[var(--accent-color)] transition-colors"
        />
    </div>
);

// Animated toggle switch
const SettingToggle = ({ label, description, value, onChange }) => (
    <div className="flex items-center justify-between">
        <div>
            <div className="text-sm text-white">{label}</div>
            {description && <div className="text-xs text-gray-500">{description}</div>}
        </div>
        <motion.button
            onClick={() => onChange(!value)}
            className="w-14 h-7 rounded-full transition-colors relative"
            style={{ backgroundColor: value ? 'var(--accent-color)' : '#4b5563' }}
            whileTap={{ scale: 0.95 }}
        >
            <motion.div
                className="absolute top-1 w-5 h-5 rounded-full bg-white shadow-md"
                animate={{ left: value ? 'calc(100% - 24px)' : '4px' }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
            />
        </motion.button>
    </div>
);

// Select dropdown
const SettingSelect = ({ label, value, onChange, options }) => (
    <div>
        <label className="block text-xs text-gray-500 mb-2 font-orbitron">{label}</label>
        <select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-full bg-black/40 rounded-xl px-4 py-3 text-sm text-white focus:outline-none border border-white/10 focus:border-[var(--accent-color)] transition-colors cursor-pointer"
        >
            {options.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
        </select>
    </div>
);

export default ConfigPanel;
