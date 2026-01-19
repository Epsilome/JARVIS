import React, { useState, useEffect } from 'react';
import { Settings, MapPin, Volume2, VolumeX, Key, Save, Check, AlertCircle, RefreshCw } from 'lucide-react';
import { getConfig, updateConfig, getAvailableVoices } from '../api';

const ConfigPanel = () => {
    const [config, setConfig] = useState(null);
    const [voices, setVoices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    // Local edits
    const [edits, setEdits] = useState({});

    // Load config on mount
    useEffect(() => {
        loadConfig();
        loadVoices();
    }, []);

    const loadConfig = async () => {
        try {
            const data = await getConfig();
            setConfig(data);

            // Apply saved theme on load
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

            // Apply theme immediately
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

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-pulse font-orbitron" style={{ color: 'var(--accent-color)' }}>LOADING CONFIGURATION...</div>
            </div>
        );
    }

    const hasChanges = Object.keys(edits).length > 0;

    return (
        <div className="flex flex-col h-full animate-in slide-in-from-bottom duration-500">
            {/* Header */}
            <div
                className="flex justify-between items-end mb-6 pb-2"
                style={{ borderBottom: '1px solid rgba(var(--accent-color-rgb), 0.2)' }}
            >
                <h2 className="text-lg font-orbitron tracking-wider flex items-center gap-2" style={{ color: 'var(--accent-color)' }}>
                    <Settings size={20} />
                    CONFIGURATION
                </h2>
                <button
                    onClick={handleSave}
                    disabled={!hasChanges || saving}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all"
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
                    {saving ? <RefreshCw size={16} className="animate-spin" /> : saved ? <Check size={16} /> : <Save size={16} />}
                    {saving ? 'SAVING...' : saved ? 'SAVED!' : 'SAVE CHANGES'}
                </button>
            </div>

            <div className="flex-1 overflow-y-auto pr-2 space-y-6">
                {/* Location Settings */}
                <SettingSection icon={MapPin} title="LOCATION">
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
                <SettingSection icon={Volume2} title="TEXT TO SPEECH">
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
                <SettingSection icon={Settings} title="THEME">
                    <div>
                        <label className="block text-xs text-gray-500 mb-2">Accent Color</label>
                        <div className="flex gap-3">
                            {[
                                { id: 'cyan', color: '#00F0FF', label: 'Cyan' },
                                { id: 'green', color: '#00FF88', label: 'Green' },
                                { id: 'purple', color: '#A855F7', label: 'Purple' },
                                { id: 'amber', color: '#FFB800', label: 'Amber' },
                                { id: 'red', color: '#FF6B6B', label: 'Red' }
                            ].map(theme => (
                                <button
                                    key={theme.id}
                                    onClick={() => updateField('theme_accent', theme.id)}
                                    className={`w-10 h-10 rounded-full border-2 transition-all ${getCurrentValue('theme_accent') === theme.id
                                        ? 'border-white scale-110 shadow-lg'
                                        : 'border-gray-600 hover:border-gray-400'
                                        }`}
                                    style={{ backgroundColor: theme.color }}
                                    title={theme.label}
                                />
                            ))}
                        </div>
                    </div>
                </SettingSection>

                {/* API Keys Status */}
                <SettingSection icon={Key} title="API KEYS STATUS">
                    <div className="grid grid-cols-2 gap-3">
                        {Object.entries(config?.api_keys_status || {}).map(([key, configured]) => (
                            <div
                                key={key}
                                className="flex items-center gap-3 px-4 py-3 bg-black/30 rounded-lg"
                                style={{ border: '1px solid rgba(var(--accent-color-rgb), 0.2)' }}
                            >
                                {configured ? (
                                    <Check size={16} className="text-green-400" />
                                ) : (
                                    <AlertCircle size={16} className="text-yellow-400" />
                                )}
                                <span className="text-sm text-gray-300 uppercase">{key}</span>
                                <span className={`ml-auto text-xs ${configured ? 'text-green-400' : 'text-yellow-400'}`}>
                                    {configured ? 'CONFIGURED' : 'MISSING'}
                                </span>
                            </div>
                        ))}
                    </div>
                </SettingSection>

                {/* Model Info */}
                <SettingSection icon={Settings} title="SYSTEM INFO">
                    <div className="grid grid-cols-2 gap-4">
                        <div
                            className="px-4 py-3 bg-black/30 rounded-lg"
                            style={{ border: '1px solid rgba(var(--accent-color-rgb), 0.2)' }}
                        >
                            <div className="text-xs text-gray-500">LLM Model</div>
                            <div className="text-sm font-mono" style={{ color: 'var(--accent-color)' }}>{config?.ollama_model || 'Unknown'}</div>
                        </div>
                    </div>
                </SettingSection>
            </div>
        </div>
    );
};

// Section wrapper
const SettingSection = ({ icon: Icon, title, children }) => (
    <div
        className="bg-black/20 rounded-lg p-4"
        style={{ border: '1px solid rgba(var(--accent-color-rgb), 0.2)' }}
    >
        <h3 className="flex items-center gap-2 text-sm font-orbitron text-gray-400 mb-4">
            <Icon size={16} style={{ color: 'var(--accent-color)' }} />
            {title}
        </h3>
        {children}
    </div>
);

// Text input
const SettingInput = ({ label, value, onChange, placeholder }) => (
    <div>
        <label className="block text-xs text-gray-500 mb-1">{label}</label>
        <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className="w-full bg-black/40 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:outline-none"
            style={{ border: '1px solid rgba(var(--accent-color-rgb), 0.3)' }}
        />
    </div>
);

// Toggle switch
const SettingToggle = ({ label, description, value, onChange }) => (
    <div className="flex items-center justify-between">
        <div>
            <div className="text-sm text-white">{label}</div>
            {description && <div className="text-xs text-gray-500">{description}</div>}
        </div>
        <button
            onClick={() => onChange(!value)}
            className="w-12 h-6 rounded-full transition-colors relative"
            style={{ backgroundColor: value ? 'var(--accent-color)' : '#4b5563' }}
        >
            <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${value ? 'right-1' : 'left-1'
                }`} />
        </button>
    </div>
);

// Select dropdown
const SettingSelect = ({ label, value, onChange, options }) => (
    <div>
        <label className="block text-xs text-gray-500 mb-1">{label}</label>
        <select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-full bg-black/40 rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
            style={{ border: '1px solid rgba(var(--accent-color-rgb), 0.3)' }}
        >
            {options.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
        </select>
    </div>
);

export default ConfigPanel;
