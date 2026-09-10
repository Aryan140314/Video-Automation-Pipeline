import { contextBridge, ipcRenderer } from 'electron'

// Custom APIs for renderer
export const api = {
  getApiUrl: () => 'http://127.0.0.1:8000',
  onMainMessage: (callback: (message: string) => void) => {
    ipcRenderer.on('main-process-message', (_event, value) => callback(value))
  }
}

contextBridge.exposeInMainWorld('electronAPI', api)
