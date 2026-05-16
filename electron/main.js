const { app, BrowserWindow, Menu, Tray, ipcMain } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const net = require('net')
const fs = require('fs')

let mainWindow
let tray = null
let backendProcess = null
let minimizeToTray = false

process.on('uncaughtException', (err) => {
    if (err.code === 'EPIPE') return
    console.error('Uncaught Exception:', err)
})

/**
 * 获取后端启动配置
 * 打包后: resources/backend/idic-backend/idic-backend.exe
 * 开发模式: 使用 python 运行 backend/main.py
 */
function getBackendConfig() {
    if (app.isPackaged) {
        const p1 = path.join(process.resourcesPath, 'backend', 'idic-backend', 'idic-backend.exe')
        const p2 = path.join(process.resourcesPath, 'backend', 'idic-backend.exe')
        if (fs.existsSync(p1)) return { cmd: p1, args: [] }
        if (fs.existsSync(p2)) return { cmd: p2, args: [] }
        return { cmd: p1, args: [] }
    }
    const projectRoot = path.join(__dirname, '..')
    const mainPy = path.join(projectRoot, 'backend', 'main.py')
    return { cmd: 'python', args: [mainPy], cwd: projectRoot }
}

/**
 * 启动 Python 后端服务
 */
function startBackend() {
    const config = getBackendConfig()
    console.log('启动后端:', config.cmd, config.args.join(' '))

    const options = {
        stdio: ['ignore', 'pipe', 'pipe'],
        env: { ...process.env }
    }
    if (config.cwd) {
        options.cwd = config.cwd
    }

    backendProcess = spawn(config.cmd, config.args, options)

    backendProcess.stdout.on('data', (data) => {
        console.log('[backend]', data.toString().trim())
    })

    backendProcess.stderr.on('data', (data) => {
        console.error('[backend]', data.toString().trim())
    })

    backendProcess.on('error', (err) => {
        console.error('后端启动失败:', err.message)
    })

    backendProcess.on('exit', (code) => {
        console.log('后端进程退出, code:', code)
        backendProcess = null
    })
}

/**
 * 停止 Python 后端服务
 */
function stopBackend() {
    if (backendProcess) {
        console.log('正在停止后端进程...')
        try {
            backendProcess.kill()
        } catch (e) {
            // ignore
        }
        backendProcess = null
    }
}

/**
 * 等待后端服务就绪
 */
function waitForBackend(maxRetries = 30, interval = 500) {
    return new Promise((resolve) => {
        let retries = 0
        const check = () => {
            const socket = new net.Socket()
            socket.setTimeout(1000)
            socket.on('connect', () => {
                socket.destroy()
                resolve(true)
            })
            socket.on('error', () => {
                socket.destroy()
                retries++
                if (retries >= maxRetries) {
                    resolve(false)
                } else {
                    setTimeout(check, interval)
                }
            })
            socket.on('timeout', () => {
                socket.destroy()
                retries++
                if (retries >= maxRetries) {
                    resolve(false)
                } else {
                    setTimeout(check, interval)
                }
            })
            socket.connect(8000, '127.0.0.1')
        }
        check()
    })
}

/**
 * 创建系统托盘
 */
function createTray() {
    const iconPath = path.join(__dirname, '..', 'public', 'icon.png')
    tray = new Tray(iconPath)

    const contextMenu = Menu.buildFromTemplate([
        { label: '显示 iDic', click: () => { showWindow() } },
        { type: 'separator' },
        { label: '退出', click: () => { app.quit() } }
    ])

    tray.setToolTip('iDic - 智能词典')
    tray.setContextMenu(contextMenu)

    tray.on('double-click', () => {
        showWindow()
    })
}

/**
 * 显示主窗口
 */
function showWindow() {
    if (mainWindow) {
        if (mainWindow.isMinimized()) {
            mainWindow.restore()
        }
        mainWindow.show()
        mainWindow.focus()
    }
}

/**
 * 加载托盘设置
 */
function loadTraySetting() {
    try {
        const settingsPath = path.join(app.getPath('userData'), 'idic_settings.json')
        if (fs.existsSync(settingsPath)) {
            const data = JSON.parse(fs.readFileSync(settingsPath, 'utf-8'))
            minimizeToTray = !!data.minimizeToTray
        }
    } catch (e) {
        minimizeToTray = false
    }
}

/**
 * 保存托盘设置
 */
function saveTraySetting(value) {
    minimizeToTray = value
    try {
        const settingsPath = path.join(app.getPath('userData'), 'idic_settings.json')
        let data = {}
        if (fs.existsSync(settingsPath)) {
            data = JSON.parse(fs.readFileSync(settingsPath, 'utf-8'))
        }
        data.minimizeToTray = value
        fs.writeFileSync(settingsPath, JSON.stringify(data, null, 2), 'utf-8')
    } catch (e) {
        console.error('保存托盘设置失败:', e)
    }
}

function createWindow() {
    const iconPath = path.join(__dirname, '..', 'public', 'icon.png')
    const preloadPath = path.join(__dirname, 'preload.js')

    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1200,
        minHeight: 700,
        icon: iconPath,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            webSecurity: false,
            preload: preloadPath
        },
        titleBarStyle: 'default',
        show: false
    })

    if (app.isPackaged) {
        mainWindow.loadFile(path.join(process.resourcesPath, 'frontend', 'index.html'))
    } else {
        mainWindow.loadURL('http://localhost:5173')
    }

    mainWindow.once('ready-to-show', () => {
        mainWindow.show()
    })

    mainWindow.setMenuBarVisibility(false)
    mainWindow.setAutoHideMenuBar(true)

    mainWindow.on('close', (event) => {
        if (minimizeToTray) {
            event.preventDefault()
            mainWindow.hide()
        }
    })

    mainWindow.on('closed', () => {
        mainWindow = null
    })
}

ipcMain.handle('get-app-version', () => {
    return app.getVersion()
})

ipcMain.handle('get-minimize-to-tray', () => {
    return minimizeToTray
})

ipcMain.handle('set-minimize-to-tray', (_, value) => {
    saveTraySetting(value)
    if (value && !tray) {
        createTray()
    }
    return true
})

app.on('ready', async () => {
    loadTraySetting()

    startBackend()

    console.log('等待后端启动...')
    const ready = await waitForBackend()
    if (ready) {
        console.log('后端已就绪!')
    } else {
        console.warn('后端启动超时，继续加载页面...')
    }

    if (minimizeToTray) {
        createTray()
    }

    createWindow()
})

app.on('window-all-closed', () => {
    if (!minimizeToTray) {
        stopBackend()
        if (process.platform !== 'darwin') {
            app.quit()
        }
    }
})

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow()
    }
})

app.on('before-quit', () => {
    stopBackend()
})
