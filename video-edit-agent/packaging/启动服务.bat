@echo off
chcp 65001 >nul
title VideoEditAgent
cd /d "%~dp0"

echo ============================================
echo   Video Edit Agent v2.0
echo ============================================
echo.
echo Starting server, please wait...
echo.

start /B "" "%~dp0VideoEditAgent.exe"

echo.
echo Server started!
echo Visit http://localhost:8000
echo.
echo Close this window to stop the server.
echo.
pause
