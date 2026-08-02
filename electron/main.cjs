const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

app.commandLine.appendSwitch('disable-gpu-cache');
app.commandLine.appendSwitch('disable-disk-cache');

// Single instance lock (match tordownloaderElectron pattern)
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

let mainWindow = null;
let pythonProcess = null;
const BACKEND_PORT = 8765;

function getPythonPath() {
    const venvPython = path.join(__dirname, '..', 'venv', 'Scripts', 'python.exe');
    if (fs.existsSync(venvPython)) {
        return venvPython;
    }
    return 'python';
}

function startPythonBackend() {
    const pythonPath = getPythonPath();
    const serverPath = path.join(__dirname, '..', 'backend', 'server.py');
    
    console.log('Starting Python backend...');
    console.log('Python path:', pythonPath);
    console.log('Server path:', serverPath);
    
    pythonProcess = spawn(pythonPath, [serverPath], {
        env: { ...process.env, PORT: String(BACKEND_PORT) },
        stdio: ['ignore', 'pipe', 'pipe'],
        shell: true
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`[Python] ${data.toString()}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`[Python Error] ${data.toString()}`);
    });

    pythonProcess.on('error', (err) => {
        console.error('Failed to start Python backend:', err);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python backend exited with code ${code}`);
        pythonProcess = null;
    });
}

function stopPythonBackend() {
    if (pythonProcess) {
        console.log('Stopping Python backend...');
        pythonProcess.kill();
        pythonProcess = null;
    }
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 900,
        minHeight: 600,
        autoHideMenuBar: true,
        webPreferences: {
            preload: path.join(__dirname, 'preload.cjs'),
            contextIsolation: true,
            nodeIntegration: false,
            sandbox: false,
            webSecurity: false
        },
        title: 'VidAutoDown',
        show: false,
        backgroundColor: '#0a0a0a'
    });

    mainWindow.setMenu(null);

    const indexPath = path.join(__dirname, '..', 'dist', 'index.html');
    console.log('Loading index from:', indexPath);
    
    mainWindow.loadFile(indexPath);

    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
        console.error('Failed to load:', errorCode, errorDescription);
    });

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.whenReady().then(() => {
    startPythonBackend();
    
    setTimeout(() => {
        createWindow();
    }, 2000);

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    stopPythonBackend();
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    stopPythonBackend();
});

ipcMain.handle('select-folder', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openDirectory', 'createDirectory']
    });
    if (result.canceled || result.filePaths.length === 0) {
        return null;
    }
    return result.filePaths[0];
});

ipcMain.handle('open-folder', async (event, folderPath) => {
    shell.openPath(folderPath);
});

ipcMain.handle('open-external', async (event, url) => {
    shell.openExternal(url);
});

ipcMain.handle('get-backend-url', () => {
    return `http://127.0.0.1:${BACKEND_PORT}`;
});
