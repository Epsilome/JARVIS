/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'jarvis-cyan': 'var(--accent-color)',
                'jarvis-black': '#050505',
                'jarvis-alert': '#FFC107',
                'jarvis-dim': 'rgba(var(--accent-color-rgb), 0.1)',
            },
            fontFamily: {
                orbitron: ['Orbitron', 'sans-serif'],
                mono: ['Roboto Mono', 'monospace'],
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'glow': 'glow 2s ease-in-out infinite alternate',
            },
            keyframes: {
                glow: {
                    '0%': { boxShadow: '0 0 5px var(--accent-color)' },
                    '100%': { boxShadow: '0 0 20px var(--accent-color), 0 0 10px var(--accent-color)' },
                }
            }
        },
    },
    plugins: [],
}
