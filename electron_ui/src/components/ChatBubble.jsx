import React from 'react';
import { motion } from 'framer-motion';

const ChatBubble = ({ message, isUser }) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.3 }}
            className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}
        >
            <div className={`max-w-[80%] relative group ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>

                {/* Header Label */}
                <span className={`text-[10px] font-orbitron mb-1 tracking-widest ${isUser ? 'text-right text-jarvis-cyan' : 'text-left text-jarvis-alert'}`}>
                    {isUser ? 'USER // AUTHORIZED' : 'JARVIS // SYSTEM'}
                </span>

                {/* Bubble Container */}
                <div
                    className={`
                        relative p-4 backdrop-blur-md border 
                        ${isUser
                            ? 'bg-jarvis-cyan/5 border-jarvis-cyan/30 rounded-l-xl rounded-tr-md'
                            : 'bg-jarvis-alert/5 border-jarvis-alert/30 rounded-r-xl rounded-tl-md'
                        }
                        shadow-[0_0_15px_rgba(0,0,0,0.2)]
                        hover:shadow-[0_0_20px_rgba(0,240,255,0.1)] transition-shadow duration-300
                    `}
                >
                    {/* Decorative Corner Lines */}
                    <div className={`absolute top-0 w-2 h-2 border-t border-l ${isUser ? 'border-jarvis-cyan -left-1 -top-1' : 'border-jarvis-alert -left-1 -top-1'}`}></div>
                    <div className={`absolute bottom-0 w-2 h-2 border-b border-r ${isUser ? 'border-jarvis-cyan -right-1 -bottom-1' : 'border-jarvis-alert -right-1 -bottom-1'}`}></div>

                    {/* Message Content */}
                    <p className={`font-mono text-sm leading-relaxed ${isUser ? 'text-gray-100' : 'text-gray-200'}`}>
                        {message}
                    </p>
                </div>
            </div>
        </motion.div>
    );
};

export default ChatBubble;
