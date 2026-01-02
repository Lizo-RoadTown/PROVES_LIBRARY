@echo off
echo Starting PROVES Notion Webhook Server...
echo.
echo This will open TWO windows:
echo   1. Webhook Server (port 8000)
echo   2. ngrok tunnel
echo.
echo Keep BOTH windows open for webhooks to work!
echo.
pause

REM Start webhook server in new window
start "Webhook Server" cmd /k "cd /d C:\Users\LizO5\PROVES_LIBRARY\notion\scripts && python notion_webhook_server.py"

REM Wait 3 seconds for server to start
timeout /t 3 /nobreak

REM Start ngrok in new window
start "ngrok Tunnel" cmd /k "ngrok http 8000 --url https://unsplendourously-unhearable-daniell.ngrok-free.dev"

echo.
echo Both servers are starting...
echo Check the two new windows that opened.
echo.
echo To stop: Close both windows
echo.
pause
