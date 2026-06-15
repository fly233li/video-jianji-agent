@echo off
chcp 65001 >nul
title 小飞龙批量剪辑

cd /d "%~dp0"

:: ========== 自动检测 Python ==========
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" (
    set PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe
) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
    set PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe
) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" (
    set PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe
) else (
    echo [ERROR] 未找到 Python，请先安装 Python 3.10+
    echo         下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo 使用 Python: %PYTHON%

:: ========== 检测 ffmpeg ==========
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    if exist "C:\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe" (
        set PATH=C:\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\bin;%PATH%
    )
)
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到 ffmpeg，请确保 ffmpeg 已安装并加入 PATH
    pause
    exit /b 1
)
echo FFmpeg 已就绪

:: ========== 检查前端构建 ==========
if not exist "frontend\dist\index.html" (
    echo [INFO] 前端未构建，尝试构建...
    if exist "frontend\node_modules" (
        cd frontend
        call npm run build
        cd ..
    ) else (
        echo [ERROR] 请先运行 setup.bat 安装环境
        pause
        exit /b 1
    )
)

:: ========== 启动服务 ==========
echo.
echo ============================================
echo  服务启动中，请稍候...
echo  访问 http://localhost:8000
echo  按 Ctrl+C 停止服务
echo ============================================
echo.

%PYTHON% -m uvicorn api.app:app --host 127.0.0.1 --port 8000 --log-level warning

pause
