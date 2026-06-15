const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const { spawn, execSync } = require('child_process');
const path = require('path');
const http = require('http');

let mainWindow = null;
let backendProcess = null;
const isDev = !app.isPackaged;
const BACKEND_URL = 'http://localhost:8000';

// ─── Backend lifecycle ───────────────────────────────────────────────

function findPython() {
  const candidates = [
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python313', 'python.exe'),
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python312', 'python.exe'),
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python311', 'python.exe'),
    'C:\\Python313\\python.exe',
    'C:\\Python312\\python.exe',
    'python',
    'py -3',
  ];
  for (const cmd of candidates) {
    try {
      execSync(`"${cmd}" --version`, { windowsHide: true, stdio: 'ignore' });
      return cmd;
    } catch (_) {}
  }
  return null;
}

function getBackendConfig() {
  if (isDev) {
    const python = findPython();
    if (!python) {
      dialog.showErrorBox('Python 未找到', '开发模式需要 Python，请安装 Python 3.11+');
      app.quit();
      return null;
    }
    return {
      cmd: python,
      args: ['-m', 'api.server'],
      cwd: path.join(__dirname, '..'),
      name: `python api.server (${python})`,
    };
  }
  const exeDir = path.join(process.resourcesPath, '视频剪辑助手');
  return {
    cmd: path.join(exeDir, '视频剪辑助手.exe'),
    args: [],
    cwd: exeDir,
    name: '视频剪辑助手.exe',
  };
}

function startBackend() {
  const cfg = getBackendConfig();
  if (!cfg) return;

  backendProcess = spawn(cfg.cmd, cfg.args, {
    cwd: cfg.cwd,
    windowsHide: true,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  backendProcess.stdout.on('data', (d) => process.stdout.write(`[backend] ${d}`));
  backendProcess.stderr.on('data', (d) => process.stderr.write(`[backend] ${d}`));
  backendProcess.on('exit', (code) => {
    console.log(`[backend] exited (code ${code})`);
    backendProcess = null;
  });

  console.log(`[electron] started ${cfg.name} (pid ${backendProcess.pid})`);
}

function stopBackend() {
  if (!backendProcess) return;
  try {
    execSync(`taskkill /F /T /PID ${backendProcess.pid}`, { windowsHide: true });
  } catch (_) {}
  backendProcess = null;
}

function waitForBackend(retries = 45) {
  return new Promise((resolve, reject) => {
    const check = (n) => {
      http.get(`${BACKEND_URL}/api/health`, (res) => resolve())
        .on('error', () => {
          n >= retries
            ? reject(new Error('Backend did not start in time'))
            : setTimeout(() => check(n + 1), 1000);
        });
    };
    check(0);
  });
}

// ─── Custom title bar injection ──────────────────────────────────────

const TITLEBAR_CSS = `
#electron-titlebar {
  position: fixed; top: 0; left: 0; right: 0; height: 34px;
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(238, 243, 247, 0.4);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  z-index: 999999; user-select: none;
  -webkit-app-region: drag;
  border-bottom: 1px solid rgba(255, 255, 255, 0.35);
}
.titlebar-drag {
  display: flex; align-items: center; gap: 8px;
  padding-left: 14px; flex: 1; min-width: 0;
}
.titlebar-icon { border-radius: 3px; flex-shrink: 0; width: 18px; height: 18px; }
.titlebar-title {
  color: rgba(0,0,0,0.75); font-size: 13px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.titlebar-controls { display: flex; height: 100%; -webkit-app-region: no-drag; }
.control-btn {
  width: 46px; height: 100%; border: none; background: transparent;
  color: rgba(60,70,85,0.5); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  border-radius: 8px; margin: 4px 2px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); outline: none;
  position: relative; overflow: hidden;
  -webkit-app-region: no-drag;
}
.control-btn svg { width: 12px; height: 12px; }
.control-btn:hover { background: rgba(255,255,255,0.4); color: rgba(30,40,55,0.8);
  box-shadow: 0 4px 16px rgba(0,0,0,0.06); transform: translateY(-1px); }
.control-btn.minimize:hover { background: rgba(255,255,255,0.45); }
.control-btn.maximize:hover { background: rgba(255,255,255,0.45); }
.control-btn.close:hover { background: rgba(232,17,35,0.8); color: #fff;
  box-shadow: 0 4px 16px rgba(232,17,35,0.25); }
.control-btn:active { background: rgba(255,255,255,0.55); transform: translateY(0) scale(0.96); }
.control-btn.close:active { background: rgba(191,15,29,0.85); }
body { padding-top: 34px !important; margin: 0 !important; }
html, body { overflow: hidden !important; }
.app-layout { height: calc(100vh - 34px) !important; }

/* Lock sidebar — fixed, full height, scroll menu if needed */
.app-sidebar {
  position: fixed !important;
  left: 0 !important;
  top: 34px !important;
  bottom: 0 !important;
  height: auto !important;
  z-index: 999 !important;
}
.app-sidebar .el-menu {
  overflow-y: auto !important;
}
.app-main {
  margin-left: 200px !important;
}
`;

function getTitlebarHTML(isMaximized) {
  const maxIcon = isMaximized
    ? '<svg viewBox="0 0 12 12"><rect x="3" y="1" width="7.5" height="7.5" fill="none" stroke="currentColor" stroke-width="1"/><rect x="1.5" y="3.5" width="7.5" height="7.5" fill="none" stroke="currentColor" stroke-width="1"/></svg>'
    : '<svg viewBox="0 0 12 12"><rect x="2" y="2" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1"/></svg>';
  return `
    <div id="electron-titlebar">
      <div class="titlebar-drag"></div>
      <div class="titlebar-controls">
        <button class="control-btn minimize" onclick="window.electronAPI.windowControls.minimize()" title="最小化">
          <svg viewBox="0 0 12 12"><rect x="2" y="5.5" width="8" height="1" fill="currentColor"/></svg>
        </button>
        <button class="control-btn maximize" id="tb-maxbtn" onclick="window.electronAPI.windowControls.maximize()" title="最大化">
          ${maxIcon}
        </button>
        <button class="control-btn close" onclick="window.electronAPI.windowControls.close()" title="关闭">
          <svg viewBox="0 0 12 12"><path d="M3 3l6 6M9 3l-6 6" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
        </button>
      </div>
    </div>
  `;
}

function injectTitleBar() {
  if (!mainWindow) return;
  try {
    mainWindow.webContents.insertCSS(TITLEBAR_CSS);
    mainWindow.webContents.executeJavaScript(`
      (function() {
        if (document.getElementById('electron-titlebar')) return;
        document.body.insertAdjacentHTML('afterbegin', ${JSON.stringify(getTitlebarHTML(mainWindow.isMaximized()))});

        // Listen for maximize state changes from main process
        if (window.electronAPI && window.electronAPI.windowControls && window.electronAPI.windowControls.onMaximizedChanged) {
          window.electronAPI.windowControls.onMaximizedChanged(function(isMax) {
            var btn = document.getElementById('tb-maxbtn');
            if (!btn) return;
            if (isMax) {
              btn.innerHTML = '<svg viewBox="0 0 12 12"><rect x="3" y="1" width="7.5" height="7.5" fill="none" stroke="currentColor" stroke-width="1"/><rect x="1.5" y="3.5" width="7.5" height="7.5" fill="none" stroke="currentColor" stroke-width="1"/></svg>';
              btn.title = '还原';
            } else {
              btn.innerHTML = '<svg viewBox="0 0 12 12"><rect x="2" y="2" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1"/></svg>';
              btn.title = '最大化';
            }
          });
        }
      })();
    `);
  } catch (err) {
    console.error('[electron] title bar injection failed:', err.message);
  }
}

// ─── Window ──────────────────────────────────────────────────────────

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    icon: path.join(__dirname, '..', 'logo.ico'),
    show: false,
    title: '视频剪辑助手',
    frame: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // IPC — window controls
  ipcMain.on('window:minimize', () => mainWindow?.minimize());
  ipcMain.on('window:maximize', () => {
    if (mainWindow?.isMaximized()) mainWindow.unmaximize();
    else mainWindow?.maximize();
  });
  ipcMain.on('window:close', () => mainWindow?.close());

  // Forward maximize state to renderer
  mainWindow.on('maximize', () =>
    mainWindow?.webContents.send('window:maximized-changed', true));
  mainWindow.on('unmaximize', () =>
    mainWindow?.webContents.send('window:maximized-changed', false));

  // Clear cache and inject custom title bar
  mainWindow.webContents.session.clearCache().catch(() => {});
  mainWindow.webContents.on('did-finish-load', injectTitleBar);

  mainWindow.loadURL(BACKEND_URL);
  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) execSync(`start "" "${url}"`);
    return { action: 'deny' };
  });
}

// ─── App lifecycle ───────────────────────────────────────────────────

app.on('ready', async () => {
  startBackend();
  try {
    await waitForBackend();
    console.log('[electron] backend is ready');
    createWindow();
  } catch (err) {
    console.error('[electron] backend failed to start:', err.message);
    dialog.showErrorBox('启动失败', `后端服务未能正常启动，请检查日志。\n\n${err.message}`);
    app.quit();
  }
});

app.on('window-all-closed', () => { stopBackend(); app.quit(); });
app.on('before-quit', () => stopBackend());
