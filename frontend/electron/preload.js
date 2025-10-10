const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // You can expose APIs here if needed
  platform: process.platform,
  versions: process.versions,
  
  // Example: Expose a method to show a native dialog
  showMessage: (message) => {
    ipcRenderer.invoke('show-message', message);
  }
});

// Expose environment variables safely
contextBridge.exposeInMainWorld('process', {
  env: {
    NODE_ENV: process.env.NODE_ENV,
    ELECTRON_IS_DEV: process.env.ELECTRON_IS_DEV
  }
});