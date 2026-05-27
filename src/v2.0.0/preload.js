const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getHistory: () => ipcRenderer.invoke('get-history'),
  saveHistory: (history) => ipcRenderer.send('save-history', history),
  clearClipboard: () => ipcRenderer.invoke('clear-clipboard'),
  onHistoryUpdated: (callback) => ipcRenderer.on('history-updated', (_event, ...args) => callback(...args)),
  quitApp: () => ipcRenderer.send('quit-app')
});
