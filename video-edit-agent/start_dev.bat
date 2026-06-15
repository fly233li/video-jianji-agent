@echo off
chcp 65001 >nul
title 小飞龙批量剪辑 - Dev Mode

cd /d "%~dp0"

:: ========== 自动检测 Python ==========
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" (
    set PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe
) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
    set PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe
) else (
    echo [ERROR] 未找到 Python
    pause
    exit /b 1
)

:: ========== 检测 ffmpeg ==========
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    if exist "C:\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe" (
        set PATH=C:\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\bin;%PATH%
    )
)

:: 启动后端
echo [1/2] 启动 API 后端 (http://localhost:8000)...
start "VideoEdit-API" cmd /c "%PYTHON% -m uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload --log-level info"

:: 启动前端
echo [2/2] 启动前端开发服务器 (http://localhost:5173)...
cd frontend
start "VideoEdit-Frontend" cmd /c "npm run dev"
cd ..

timeout /t 5 /nobreak >nul
start http://localhost:5175

echo.
echo ============================================
echo  开发模式已启动
echo  前端: http://localhost:5173
echo  API:  http://localhost:8000
echo  关闭此窗口即可停止服务
echo ============================================
echo.

pause

taskkill /FI "WINDOWTITLE eq VideoEdit-API" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq VideoEdit-Frontend" /F >nul 2>&1
