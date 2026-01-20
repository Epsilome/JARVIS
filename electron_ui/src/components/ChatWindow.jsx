import React, { useRef, useEffect } from 'react';
import ChatBubble from './ChatBubble';

const ChatWindow = ({ messages }) => {
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div
            className="flex-1 rounded-lg bg-black/40 backdrop-blur-md p-4 relative overflow-hidden flex flex-col min-h-0"
            style={{ border: '1px solid rgba(var(--accent-color-rgb), 0.2)' }}
        >
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
            <div
                className="mt-4 pt-4 flex items-center opacity-50"
                style={{ borderTop: '1px solid rgba(var(--accent-color-rgb), 0.2)' }}
            >
                <div className="w-2 h-2 animate-pulse mr-2" style={{ backgroundColor: 'var(--accent-color)' }}></div>
                <span className="text-xs font-mono" style={{ color: 'rgba(var(--accent-color-rgb), 0.5)' }}>LISTENING FOR AUDIO INPUT...</span>
            </div>
        </div>
    );
};

export default ChatWindow;
