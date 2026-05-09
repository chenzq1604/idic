@echo off
chcp 65001 >nul
echo ============================================
echo   iDic 一键打包脚本
echo   输出: release/iDic Setup 1.0.0.exe
echo ============================================
echo.

:: 检查 conda 环境
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 conda
    pause
    exit /b 1
)

echo [1/4] 激活 conda 环境 idic...
call conda activate idic
if %errorlevel% neq 0 (
    echo [错误] 无法激活 idic 环境
    pause
    exit /b 1
)

echo [2/4] 打包 Python 后端 (PyInstaller)...
python build_backend.py
if %errorlevel% neq 0 (
    echo [错误] Python 后端打包失败
    pause
    exit /b 1
)

echo [3/4] 构建前端 (Vite)...
call npx vite build
if %errorlevel% neq 0 (
    echo [错误] 前端构建失败
    pause
    exit /b 1
)

echo [4/4] 打包 Electron 应用 (electron-builder)...
call npx electron-builder --win --publish never
if %errorlevel% neq 0 (
    echo [错误] Electron 打包失败
    pause
    exit /b 1
)

echo.
echo ============================================
echo   打包完成！
echo   安装包: release\iDic Setup 1.0.0.exe
echo   
echo   用户安装后只需双击 iDic 图标即可使用
echo   前端和后端会自动一起启动
echo ============================================
pause
