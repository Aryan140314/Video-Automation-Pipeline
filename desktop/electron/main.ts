import { app, BrowserWindow, ipcMain, shell } from 'electron'
import path from 'path'
import fs from 'fs'
import { spawn, ChildProcess } from 'child_process'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

process.env.DIST = path.join(__dirname, '../dist')
process.env.VITE_PUBLIC = app.isPackaged ? process.env.DIST : path.join(process.env.DIST, '../public')

let win: BrowserWindow | null = null
let pythonProcess: ChildProcess | null = null
const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']

function findPythonBinary(workspaceRoot: string): string {
  const localAppData = process.env.LOCALAPPDATA || path.join(process.env.USERPROFILE || '', 'AppData', 'Local')

  const candidates = [
    // 1. Packaged embedded runtime inside resources
    path.join(process.resourcesPath, 'runtime', 'python.exe'),
    path.join(process.resourcesPath, 'runtime', 'Scripts', 'python.exe'),
    path.join(process.resourcesPath, '.venv', 'Scripts', 'python.exe'),
    // 2. Project development venv
    'E:\\TTS\\.venv\\Scripts\\python.exe',
    path.join(workspaceRoot, '.venv', 'Scripts', 'python.exe'),
    path.join(workspaceRoot, '..', '.venv', 'Scripts', 'python.exe'),
    // 3. User Local AppData runtime
    path.join(localAppData, 'TTS-Studio', 'runtimes', '.venv', 'Scripts', 'python.exe'),
    path.join(localAppData, 'TTS-Studio', 'runtimes', 'python.exe'),
    // 4. System PATH fallbacks
    'python.exe',
    'python'
  ]

  for (const c of candidates) {
    if (c && fs.existsSync(c)) {
      console.log(`[Main] Using Python interpreter: ${c}`)
      return c
    }
  }

  console.warn('[Main] No specific venv python found, falling back to system python')
  return 'python'
}

function startPythonBackend() {
  const isDev = !app.isPackaged
  const workspaceRoot = isDev
    ? path.resolve(__dirname, '../../')
    : path.resolve(process.resourcesPath)

  let pythonScript = path.join(workspaceRoot, 'scripts', 'desktop_server.py')
  if (!fs.existsSync(pythonScript)) {
    // In packaged mode, scripts may live directly under resources/scripts
    const resourceScript = path.join(process.resourcesPath || '', 'scripts', 'desktop_server.py')
    if (fs.existsSync(resourceScript)) {
      pythonScript = resourceScript
    }
  }

  const pythonBin = findPythonBinary(workspaceRoot)

  console.log(`[Main] Launching Python backend: ${pythonBin} ${pythonScript}`)
  
  try {
    pythonProcess = spawn(pythonBin, [pythonScript, '8000'], {
      cwd: workspaceRoot,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
        PYTHONPATH: [
          path.join(workspaceRoot, 'scripts'),
          process.env.PYTHONPATH || ''
        ].join(path.delimiter)
      },
      stdio: 'pipe'
    })

    pythonProcess.stdout?.on('data', (data) => {
      console.log(`[Python Server] ${data.toString().trim()}`)
    })

    pythonProcess.stderr?.on('data', (data) => {
      console.error(`[Python Server Error] ${data.toString().trim()}`)
    })

    pythonProcess.on('error', (err) => {
      console.error(`[Main] Failed to spawn Python process: ${err.message}`)
    })

    pythonProcess.on('close', (code) => {
      console.log(`[Python Server] Exited with code ${code}`)
    })
  } catch (err: any) {
    console.error(`[Main] Exception while spawning python: ${err.message}`)
  }
}

function createWindow() {
  win = new BrowserWindow({
    width: 1360,
    height: 900,
    minWidth: 1100,
    minHeight: 750,
    backgroundColor: '#090d16',
    title: 'TTS Studio — Zero-Shot Neural Voice Cloning',
    frame: true,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.mjs'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  })

  win.webContents.on('did-finish-load', () => {
    win?.webContents.send('main-process-message', (new Date).toLocaleString())
  })

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https:') || url.startsWith('http:')) {
      shell.openExternal(url)
    }
    return { action: 'deny' }
  })

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL)
  } else {
    win.loadFile(path.join(process.env.DIST, 'index.html'))
  }
}

app.on('window-all-closed', () => {
  if (pythonProcess) {
    console.log('[Main] Terminating Python server process...')
    pythonProcess.kill()
    pythonProcess = null
  }
  if (process.platform !== 'darwin') {
    app.quit()
    win = null
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

app.whenReady().then(() => {
  startPythonBackend()
  createWindow()
})

app.on('will-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
})
