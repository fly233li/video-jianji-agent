@echo off
chcp 65001 >nul
title 小飞龙批量剪辑 - 环境安装

cd /d "%~dp0"

echo ============================================
echo  小飞龙批量剪辑 - 一键环境安装
echo ============================================
echo.

:: ---------- 检测 Python ----------
echo [1/4] 检测 Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到 Python，请先安装 Python 3.10+
    echo         下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo.

:: ---------- 检测 ffmpeg ----------
echo [2/4] 检测 ffmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] 未找到系统 ffmpeg，尝试本地路径...
    if exist "C:\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe" (
        echo   找到本地 ffmpeg
    ) else (
        echo [INFO] 请确保 ffmpeg 已安装并在 PATH 中
        echo         下载地址: https://ffmpeg.org/download.html
        echo.
    )
) else (
    ffmpeg -version | findstr "ffmpeg" && echo.
)

:: ---------- 安装 Python 依赖 ----------
echo [3/4] 安装 Python 依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)
echo   完成
echo.

:: ---------- 构建前端 ----------
echo [4/4] 检测前端构建...
if exist "frontend\dist\index.html" (
    echo   前端已构建，跳过
) else (
    echo   未检测到前端构建产物，尝试构建...
    where npm >nul 2>&1
    if %errorlevel% equ 0 (
        cd frontend
        call npm install
        call npm run build
        cd ..
        echo   前端构建完成
    ) else (
        echo [INFO] 未找到 npm，跳过前端构建
        echo         需手动在 frontend 目录执行: npm install ^&^& npm run build
    )
)

echo.
echo ============================================
echo  环境安装完成！
echo  运行 start_web.bat 启动服务
echo ============================================
echo.
pause
