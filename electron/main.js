const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;

function startBackendServer() {
  const isPackaged = app.isPackaged;
  const appDir = isPackaged ? process.resourcesPath : path.dirname(__dirname);
  const workspaceRoot = path.dirname(__dirname);

  // Candidate executable paths
  const venvPython = path.join(workspaceRoot, '.venv', 'Scripts', 'python.exe');
  const packagedExe = path.join(appDir, 'dist', 'backend_dist', 'tts_studio_backend', 'tts_studio_backend.exe');
  const mainScript = path.join(appDir, 'backend', 'main.py');

  let exePath = '';
  let args = [];
  let cwd = appDir;

  if (fs.existsSync(packagedExe)) {
    exePath = packagedExe;
    args = [];
  } else if (fs.existsSync(venvPython)) {
    exePath = venvPython;
    args = ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8000'];
    cwd = workspaceRoot;
  } else {
    exePath = 'python';
    args = ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8000'];
    cwd = appDir;
  }

  console.log(`[Electron Main] Spawning backend from CWD: ${cwd}`);
  console.log(`[Electron Main] Executable: ${exePath} Args: ${args.join(' ')}`);

  try {
    backendProcess = spawn(exePath, args, {
      cwd: cwd,
      stdio: 'inherit',
      env: { ...process.env, PYTHONIOENCODING: 'utf-8', TTS_STUDIO_PROD: isPackaged ? '1' : '0' }
    });

    backendProcess.on('error', (err) => {
      console.error('[Electron Main] Failed to start backend process:', err);
    });
  } catch (err) {
    console.error('[Electron Main] Spawn exception:', err);
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 860,
    minWidth: 1024,
    minHeight: 700,
    title: 'TTS Studio',
    backgroundColor: '#090d16',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  const isDev = !app.isPackaged && process.env.NODE_ENV === 'development';
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'));
  }
}

app.whenReady().then(() => {
  startBackendServer();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (backendProcess) {
    console.log('[Electron Main] Terminating backend process...');
    backendProcess.kill();
  }
  if (process.platform !== 'darwin') app.quit();
});
