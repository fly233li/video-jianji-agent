const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  windowControls: {
    minimize: () => ipcRenderer.send('window:minimize'),
    maximize: () => ipcRenderer.send('window:maximize'),
    close: () => ipcRenderer.send('window:close'),
    onMaximizedChanged: (callback) => {
      ipcRenderer.on('window:maximized-changed', (_event, isMaximized) => {
        callback(isMaximized);
      });
    },
  },
});
