@echo off
chcp 65001 >nul
title 视频剪辑助手 - 打包构建

cd /d "%~dp0.."
set PROJECT=%CD%
:: 自动检测 Python
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" (
    set PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe
) else (
    echo [ERROR] 未找到 Python
    pause
    exit /b 1
)
set DIST_DIR=%PROJECT%\dist\视频剪辑助手
:: 自动检测 Inno Setup Compiler
where iscc >nul 2>&1
if %errorlevel% equ 0 (
    set ISCC=iscc
) else if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "D:\Inno Setup 6\ISCC.exe" (
    set ISCC="D:\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else (
    set ISCC=
)

echo ============================================
echo   视频剪辑助手 v2.0 — 打包构建
echo ============================================
echo.

:: Step 1: 构建前端
echo [1/7] 构建前端...
cd frontend
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] 前端构建失败
    pause
    exit /b 1
)
cd ..
echo [OK] 前端构建完成
echo.

:: Step 2: 清理旧的构建
echo [2/7] 清理旧的构建...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%PROJECT%\build" rmdir /s /q "%PROJECT%\build"
echo [OK] 清理完成
echo.

:: Step 3: PyInstaller 打包
echo [3/7] PyInstaller 打包 Python 后端（耗时约 1-2 分钟）...
"%PYTHON%" -m PyInstaller packaging\build.spec --noconfirm
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller 打包失败
    pause
    exit /b 1
)
echo [OK] PyInstaller 打包完成
echo.

:: Step 4: 复制数据文件
echo [4/7] 复制数据文件到输出目录...

:: config.py
copy "%PROJECT%\config.py" "%DIST_DIR%\" >nul
echo   [OK] config.py

:: logo.ico（程序图标）
copy "%PROJECT%\logo.ico" "%DIST_DIR%\" >nul
echo   [OK] logo.ico

:: 前端 dist（放入 frontend/dist/ 以匹配路径解析）
if exist "%DIST_DIR%\frontend" rmdir /s /q "%DIST_DIR%\frontend"
mkdir "%DIST_DIR%\frontend\dist"
xcopy /E /I /Q "%PROJECT%\frontend\dist\*" "%DIST_DIR%\frontend\dist\" >nul
echo   [OK] frontend/dist

:: fonts.conf
copy "%PROJECT%\fonts.conf" "%DIST_DIR%\" >nul
echo   [OK] fonts.conf

:: ffmpeg（自动检测路径）
set FFMPEG_SRC=C:\tools\ffmpeg\ffmpeg-master-latest-win64-gpl\bin
if not exist "%FFMPEG_SRC%\ffmpeg.exe" (
    where ffmpeg >nul 2>&1 && for /f "tokens=*" %%i in ('where ffmpeg') do set "FFMPEG_SRC=%%~dpi"
)
copy "%FFMPEG_SRC%\ffmpeg.exe" "%DIST_DIR%\" >nul
echo   [OK] ffmpeg.exe
copy "%FFMPEG_SRC%\ffprobe.exe" "%DIST_DIR%\" >nul
echo   [OK] ffprobe.exe

:: 启动服务.bat
copy "%PROJECT%\packaging\启动服务.bat" "%DIST_DIR%\" >nul
echo   [OK] 启动服务.bat

echo [OK] 数据文件复制完成
echo.

:: Step 5: Inno Setup 安装程序
echo [5/7] 创建 Windows 安装程序（Inno Setup）...
if "%ISCC%"=="" (
    echo [SKIP] 未找到 ISCC.exe，跳过安装程序创建
    echo    安装 Inno Setup: winget install JRSoftware.InnoSetup
) else (
    %ISCC% packaging\installer.iss >nul 2>&1
    if %errorlevel% neq 0 (
        echo [WARNING] Inno Setup 安装程序创建失败（错误码: %errorlevel%）
        echo    请确认 Inno Setup 已安装: winget install JRSoftware.InnoSetup
    ) else (
        echo [OK] 安装程序已创建
    )
)
echo.

:: Step 6: 创建 ZIP 便携包
echo [6/7] 创建 ZIP 便携包...
cd "%PROJECT%\dist"
if exist "视频剪辑助手_v2.0_便携版.zip" del "视频剪辑助手_v2.0_便携版.zip"
powershell -NoProfile -Command "Compress-Archive -Path '%DIST_DIR%\*' -DestinationPath '%PROJECT%\dist\视频剪辑助手_v2.0_便携版.zip'" >nul 2>&1
echo [OK] ZIP 便携包已创建
echo.

:: Step 7: Electron 桌面安装程序
echo [7/7] 创建 Electron 桌面安装程序...
cd "%PROJECT%"
if exist "%PROJECT%\node_modules\.package-lock.json" (
    call npm run electron:build >nul 2>&1
    if exist "%PROJECT%\dist_electron\视频剪辑助手 Setup 2.0.0.exe" (
        echo [OK] Electron 安装程序已创建
    ) else (
        echo [WARNING] Electron 安装程序创建失败
        echo    请确认已安装依赖: cd "%PROJECT%" ^&^& npm install
    )
) else (
    echo [SKIP] Electron 未安装（缺少 node_modules），跳过
    echo    如需 Electron 桌面版: cd "%PROJECT%" ^&^& npm install ^&^& npm run electron:build
)
echo.

echo ============================================
echo   构建完成！
echo.
echo   [1] 可执行文件:
echo       %DIST_DIR%
echo       运行 "视频剪辑助手.exe" 或 "启动服务.bat" 即可使用
echo.
echo   [2] Inno Setup 安装程序:
echo       %PROJECT%\dist\视频剪辑助手_v2.0_安装程序.exe
echo       双击安装，自动创建桌面快捷方式和开始菜单
echo.
echo   [3] Electron 桌面安装程序:
echo       %PROJECT%\dist_electron\视频剪辑助手 Setup 2.0.0.exe
echo       原生桌面窗口，无需浏览器，含自动更新支持
echo.
echo   [4] 便携版 ZIP:
echo       %PROJECT%\dist\视频剪辑助手_v2.0_便携版.zip
echo       解压到目标电脑，运行 "启动服务.bat"
echo.
echo   文件大小:
for %%f in ("%DIST_DIR%\视频剪辑助手.exe") do echo     视频剪辑助手.exe: %%~zf 字节
for %%f in ("%PROJECT%\dist\视频剪辑助手_v2.0_安装程序.exe") do if exist "%%f" echo     Inno Setup 安装程序: %%~zf 字节
for %%f in ("%PROJECT%\dist_electron\视频剪辑助手 Setup 2.0.0.exe") do if exist "%%f" echo     Electron 安装程序: %%~zf 字节
for %%f in ("%PROJECT%\dist\视频剪辑助手_v2.0_便携版.zip") do echo     ZIP: %%~zf 字节
echo.
echo   目标电脑要求:
echo     - Windows 10/11
echo     - 无需安装 Python
echo     - 无需安装 ffmpeg
echo ============================================
echo.
pause
