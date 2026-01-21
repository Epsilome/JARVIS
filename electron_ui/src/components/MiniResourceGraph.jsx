import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Cpu } from 'lucide-react';
import { getSystemHealth } from '../api';

const MiniResourceGraph = () => {
    const [history, setHistory] = useState({ cpu: [], ram: [], gpu: [] });
    const maxPoints = 20;

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const data = await getSystemHealth();
                setHistory(prev => ({
                    cpu: [...prev.cpu.slice(-(maxPoints - 1)), data.cpu],
                    ram: [...prev.ram.slice(-(maxPoints - 1)), data.ram],
                    gpu: [...prev.gpu.slice(-(maxPoints - 1)), data.gpu ?? 0]
                }));
            } catch (err) {
                console.error('Stats fetch error:', err);
            }
        };

        fetchStats();
        const interval = setInterval(fetchStats, 2000);
        return () => clearInterval(interval);
    }, []);

    const createPath = (values, height = 28) => {
        if (values.length < 2) return '';
        const width = 100;
        const step = width / (maxPoints - 1);

        return values.map((v, i) => {
            const x = i * step;
            const y = height - (v / 100) * height;
            return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
        }).join(' ');
    };

    const accentStyle = { color: 'var(--accent-color)' };
    const borderStyle = { border: '1px solid rgba(var(--accent-color-rgb), 0.3)' };

    const ResourceLine = ({ label, values, color, gradientId }) => (
        <div>
            <div className="flex justify-between items-center mb-1">
                <span className="text-[10px] text-gray-500 font-orbitron">{label}</span>
                <span className="text-xs font-mono" style={{ color }}>
                    {values.length > 0 ? `${Math.round(values[values.length - 1])}%` : '--'}
                </span>
            </div>
            <div className="h-7 bg-black/30 rounded overflow-hidden relative">
                <svg viewBox="0 0 100 28" className="w-full h-full" preserveAspectRatio="none">
                    <defs>
                        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={color} stopOpacity="0.4" />
                            <stop offset="100%" stopColor={color} stopOpacity="0.05" />
                        </linearGradient>
                    </defs>
                    {values.length > 1 && (
                        <>
                            <path
                                d={`${createPath(values)} L 100 28 L 0 28 Z`}
                                fill={`url(#${gradientId})`}
                            />
                            <motion.path
                                d={createPath(values)}
                                fill="none"
                                stroke={color}
                                strokeWidth="1.5"
                                initial={{ pathLength: 0 }}
                                animate={{ pathLength: 1 }}
                                transition={{ duration: 0.5 }}
                            />
                        </>
                    )}
                </svg>
            </div>
        </div>
    );

    return (
        <div
            className="rounded-xl p-4 bg-black/40 backdrop-blur-md"
            style={borderStyle}
        >
            <h3 className="text-xs font-orbitron tracking-wider mb-3 flex items-center gap-2" style={accentStyle}>
                <Cpu size={14} />
                RESOURCES
            </h3>

            <div className="space-y-2">
                <ResourceLine label="CPU" values={history.cpu} color="var(--accent-color)" gradientId="cpuGrad" />
                <ResourceLine label="RAM" values={history.ram} color="#a855f7" gradientId="ramGrad" />
                <ResourceLine label="GPU" values={history.gpu} color="#22c55e" gradientId="gpuGrad" />
            </div>
        </div>
    );
};

export default MiniResourceGraph;
