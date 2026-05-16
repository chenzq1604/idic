const { contextBridge, ipcRenderer } = require('electron')

/**
 * preload 脚本 - 安全地将 Electron API 暴露给前端
 */
contextBridge.exposeInMainWorld('electronAPI', {
    getAppVersion: () => ipcRenderer.invoke('get-app-version'),
    getMinimizeToTray: () => ipcRenderer.invoke('get-minimize-to-tray'),
    setMinimizeToTray: (value) => ipcRenderer.invoke('set-minimize-to-tray', value)
})
