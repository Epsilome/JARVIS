import React, { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ChatBubble from './ChatBubble';

const TypingIndicator = () => (
    <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="flex items-start gap-2 mb-4"
    >
        <div className="flex flex-col items-start">
            <span className="text-[10px] font-orbitron mb-1 tracking-widest text-jarvis-alert">
                JARVIS // PROCESSING
            </span>
            <div className="flex items-center gap-2 px-4 py-3 bg-jarvis-alert/5 border border-jarvis-alert/30 rounded-r-xl rounded-tl-md backdrop-blur-md">
                <motion.div
                    className="flex gap-1.5"
                >
                    {[0, 1, 2].map((i) => (
                        <motion.div
                            key={i}
                            className="w-2 h-2 rounded-full bg-jarvis-alert"
                            animate={{
                                y: [0, -6, 0],
                                opacity: [0.4, 1, 0.4]
                            }}
                            transition={{
                                duration: 0.8,
                                repeat: Infinity,
                                delay: i * 0.15,
                                ease: "easeInOut"
                            }}
                        />
                    ))}
                </motion.div>
            </div>
        </div>
    </motion.div>
);

const ChatWindow = ({ messages, isTyping = false }) => {
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isTyping]);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex-1 rounded-2xl bg-black/40 backdrop-blur-xl p-5 relative overflow-hidden flex flex-col min-h-0 shadow-lg"
            style={{ border: '1px solid rgba(var(--accent-color-rgb), 0.15)' }}
        >
            {/* Background Grid */}
            <div className="absolute inset-0 grid-bg opacity-5 pointer-events-none" />

            {/* Subtle gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/20 pointer-events-none" />

            <div className="flex-1 overflow-y-auto pr-2 space-y-2 custom-scrollbar relative z-10">
                <AnimatePresence mode="popLayout">
                    {messages.map((msg, idx) => (
                        <ChatBubble
                            key={idx}
                            message={msg.text}
                            isUser={msg.sender === 'user'}
                        />
                    ))}
                </AnimatePresence>

                <AnimatePresence>
                    {isTyping && <TypingIndicator />}
                </AnimatePresence>

                <div ref={bottomRef} />
            </div>

            {/* Input Indicator */}
            <motion.div
                className="mt-4 pt-4 flex items-center relative z-10"
                style={{ borderTop: '1px solid rgba(var(--accent-color-rgb), 0.1)' }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
            >
                <motion.div
                    className="w-2 h-2 rounded-full mr-3"
                    style={{ backgroundColor: 'var(--accent-color)' }}
                    animate={{
                        scale: [1, 1.3, 1],
                        opacity: [0.5, 1, 0.5]
                    }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                />
                <span className="text-xs font-mono tracking-wider" style={{ color: 'rgba(var(--accent-color-rgb), 0.5)' }}>
                    LISTENING FOR AUDIO INPUT...
                </span>
            </motion.div>
        </motion.div>
    );
};

export default ChatWindow;
