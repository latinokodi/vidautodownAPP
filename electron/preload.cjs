const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    selectFolder: () => ipcRenderer.invoke('select-folder'),
    openFolder: (path) => ipcRenderer.invoke('open-folder', path),
    openExternal: (url) => ipcRenderer.invoke('open-external', url),
    getBackendUrl: () => ipcRenderer.invoke('get-backend-url')
});
