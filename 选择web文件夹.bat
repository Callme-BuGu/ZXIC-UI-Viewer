@echo off
title ZXIC-UI-Viewer - 选择 web 文件夹
cd /d "%~dp0"
echo ==============================================
echo   ZXIC-UI-Viewer - 请选择 web 文件夹
echo   (选择后自动启动服务并打开浏览器)
echo ==============================================
echo.

set "WEBDIR="
for /f "usebackq delims=" %%i in (`powershell -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0select_web_folder.ps1"`) do set "WEBDIR=%%i"

if not defined WEBDIR (
    echo 未选择文件夹，已退出。
    pause
    exit /b 1
)

echo 已选择: %WEBDIR%
echo.

netstat -ano | findstr ":8123" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo Starting local server...
    start "wifi-backend" /min mock_server.exe "%WEBDIR%"
    ping -n 3 127.0.0.1 >nul
) else (
    echo Server already running.
)

start "" "http://127.0.0.1:8123/index.html?t=%random%"
echo.
echo Browser opened. You can close this window.
ping -n 6 127.0.0.1 >nul
