const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // 基础信息
  platform: process.platform,
  versions: process.versions,

  // 国际化相关
  getLocale: () => ipcRenderer.invoke('get-system-locale'),
  setLanguage: (language) => ipcRenderer.invoke('set-menu-language', language),

  // 系统对话框
  showMessageBox: async (options) => {
    return ipcRenderer.invoke('show-message-box', options);
  },

  showOpenDialog: async (options) => {
    return ipcRenderer.invoke('show-open-dialog', options);
  },

  showSaveDialog: async (options) => {
    return ipcRenderer.invoke('show-save-dialog', options);
  },

  // 其他消息
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