const { app, BrowserWindow, ipcMain, clipboard } = require('electron');
const path = require('path');
const fs = require('fs');

// Note: Ensure your Python script and Electron share the same file location
const HISTORY_FILE = path.join(__dirname, 'clipboard_history.json');

// --- Helper Functions ---
function getHistory() {
  try {
    if (!fs.existsSync(HISTORY_FILE)) return [];
    const rawData = fs.readFileSync(HISTORY_FILE, 'utf-8');
    if (!rawData) return [];
    const history = JSON.parse(rawData);
    if (!Array.isArray(history)) return [];
    
    return history.map(item => {
      if (typeof item === 'string') return { text: item, timestamp: new Date().toISOString() };
      if (item && typeof item === 'object') {
        return { 
          text: String(item.text || item.content || ''), 
          timestamp: String(item.timestamp || new Date().toISOString()) 
        };
      }
      return { text: '', timestamp: new Date().toISOString() };
    });
  } catch (error) {
    console.error('Error reading history:', error);
    return [];
  }
}

function saveHistory(history) {
  try {
    if (!Array.isArray(history)) {
      console.error('saveHistory: Expected array, got', typeof history);
      return;
    }
    // Enforce a limit to keep the file size manageable
    const limitedHistory = history.slice(0, 50);
    fs.writeFileSync(HISTORY_FILE, JSON.stringify(limitedHistory, null, 2));
  } catch (error) {
    console.error('Error saving history:', error);
  }
}

// --- Main Window Setup ---
let mainWindow;
let clipboardInterval;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  mainWindow.loadFile('index.html');
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// --- Lifecycle & Sync ---
app.whenReady().then(() => {
  createWindow();

  // Ensure file exists for watcher
  if (!fs.existsSync(HISTORY_FILE)) {
    saveHistory([]);
  }

  // 1. File Watcher: Detect changes from Python CLI
  fs.watch(HISTORY_FILE, (eventType) => {
    if (eventType === 'change' && mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('history-updated');
    }
  });

  // 2. Clipboard Monitor: Track changes inside the GUI process
  let lastClipboardContent = clipboard.readText();
  clipboardInterval = setInterval(() => {
    const current = clipboard.readText();
    if (current && current !== lastClipboardContent && current.trim() !== '') {
      lastClipboardContent = current;
      const history = getHistory();
      // Check if already exists in recent history to avoid duplicates
      if (!history.some(item => item.text === current)) {
        history.unshift({ text: current, timestamp: new Date().toISOString() });
        saveHistory(history);
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('history-updated');
        }
      }
    }
  }, 500); // 500ms for more responsive tracking
});

// --- IPC Handlers ---
ipcMain.handle('get-history', () => getHistory());
ipcMain.on('save-history', (event, history) => saveHistory(history));
ipcMain.handle('clear-clipboard', () => clipboard.clear());
ipcMain.on('quit-app', () => app.quit());

app.on('window-all-closed', () => {
  if (clipboardInterval) clearInterval(clipboardInterval);
  if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', () => {
  if (clipboardInterval) clearInterval(clipboardInterval);
});