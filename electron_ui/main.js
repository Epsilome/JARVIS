const { app, BrowserWindow } = require('electron')
const path = require('path')

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 900,
        minWidth: 900,
        minHeight: 700,
        frame: true, // Enable native window controls (maximize, minimize, close)
        transparent: false, // Disable transparency (required when frame: true on some systems)
        backgroundColor: '#0a0a0a', // Dark background
        titleBarStyle: 'hidden', // Hide title bar but keep window controls (macOS)
        titleBarOverlay: { // Windows 10/11 overlay controls
            color: '#0a0a0a',
            symbolColor: '#00F0FF',
            height: 32
        },
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false, // Simplified for this prototype
        }
    })

    // Development: Load Vite dev server
    // Production: Load built file
    // For this setup, we'll try dev server first
    win.loadURL('http://localhost:3000').catch(() => {
        win.loadFile(path.join(__dirname, 'dist', 'index.html'))
    })
}

app.whenReady().then(() => {
    createWindow()

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow()
        }
    })
})

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit()
    }
})
