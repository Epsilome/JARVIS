import React, { useRef, useEffect } from 'react';
import ChatBubble from './ChatBubble';

const ChatWindow = ({ messages }) => {
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="flex-1 border border-jarvis-cyan/20 rounded-lg bg-black/40 backdrop-blur-md p-4 relative overflow-hidden flex flex-col min-h-0">
            {/* Background Grid */}
            <div className="absolute inset-0 grid-bg opacity-10 pointer-events-none"></div>

            <div className="flex-1 overflow-y-auto pr-2 space-y-4">
                {messages.map((msg, idx) => (
                    <ChatBubble
                        key={idx}
                        message={msg.text}
                        isUser={msg.sender === 'user'}
                    />
                ))}
                <div ref={bottomRef} />
            </div>

            {/* Input Placeholder (Visual Only for now) */}
            <div className="mt-4 pt-4 border-t border-jarvis-cyan/20 flex items-center opacity-50">
                <div className="w-2 h-2 bg-jarvis-cyan animate-pulse mr-2"></div>
                <span className="text-xs font-mono text-jarvis-cyan/50">LISTENING FOR AUDIO INPUT...</span>
            </div>
        </div>
    );
};

export default ChatWindow;
