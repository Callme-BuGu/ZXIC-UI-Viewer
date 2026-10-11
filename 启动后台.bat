@echo off
title ZXIC-UI-Viewer
cd /d "%~dp0"
echo ==============================================
echo   ZXIC-UI-Viewer - 中兴微随身WiFi 后台查看器
echo   地址: http://127.0.0.1:8123/index.html
echo   (任意密码登录，模拟模式，不连真实设备)
echo   Press Ctrl+C to stop the server
echo ==============================================
echo.
netstat -ano | findstr ":8123" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo Starting local server... (no Python needed)
    start "wifi-backend" /min mock_server.exe
    ping -n 3 127.0.0.1 >nul
) else (
    echo Server already running.
)
start "" "http://127.0.0.1:8123/index.html?t=%random%"
echo.
echo Browser opened. You can close this window.
ping -n 6 127.0.0.1 >nul
