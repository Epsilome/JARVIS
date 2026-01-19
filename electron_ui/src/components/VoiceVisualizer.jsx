import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

const VoiceVisualizer = ({ isActive = false }) => {
    // Generate bars for visualizer
    const bars = Array.from({ length: 40 });

    return (
        <div className="relative w-full h-full flex items-center justify-center overflow-hidden">
            {/* Background Grid/Holo Effect */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(0,240,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(0,240,255,0.05)_1px,transparent_1px)] bg-[size:20px_20px] opacity-30"></div>

            {/* Main Spectrum Container */}
            <div className="flex items-end justify-center gap-[2px] h-32 w-3/4 z-10">
                {bars.map((_, i) => (
                    <Bar key={i} index={i} isActive={isActive} />
                ))}
            </div>

            {/* Glowing Center Core */}
            <div className={`absolute bottom-[-50px] left-1/2 -translate-x-1/2 w-48 h-48 bg-jarvis-cyan blur-[100px] transition-opacity duration-500 ${isActive ? 'opacity-40' : 'opacity-10'}`}></div>
        </div>
    );
};

const Bar = ({ index, isActive }) => {
    // Mirror effect: Calculate distance from center (0 to 1)
    const center = 20;
    const dist = Math.abs(index - center);
    const normDist = 1 - (dist / center); // 1 at center, 0 at edges

    return (
        <motion.div
            className="w-2 rounded-t-sm bg-jarvis-cyan shadow-[0_0_10px_rgba(0,240,255,0.5)]"
            initial={{ height: "4px" }}
            animate={{
                height: isActive
                    ? [
                        `${10 + normDist * 20}%`,
                        `${10 + normDist * 80 + Math.random() * 30}%`,
                        `${10 + normDist * 20}%`
                    ]
                    : [`${5 + normDist * 5}%`, `${5 + normDist * 10}%`, `${5 + normDist * 5}%`],
                opacity: isActive ? 1 : 0.5,
                backgroundColor: isActive ? "#00F0FF" : "#005f66"
            }}
            transition={{
                duration: isActive ? 0.2 : 2,
                repeat: Infinity,
                repeatType: "reverse",
                delay: index * 0.02,
                ease: "easeInOut"
            }}
        />
    );
};

export default VoiceVisualizer;
