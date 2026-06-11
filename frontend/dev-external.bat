@echo off
REM Frontend Development Server - External Access Configuration
REM This script starts the Next.js dev server with proper host binding

echo.
echo 🚀 Starting RetailVision AI Frontend - External Access Mode
echo ==========================================================
echo.

REM Get local IP address
for /f "tokens=2 delims=: " %%a in ('ipconfig ^| find "IPv4"') do set LOCAL_IP=%%a

REM Trim whitespace
set LOCAL_IP=%LOCAL_IP: =%

if "%LOCAL_IP%"=="" (
  set LOCAL_IP=localhost
)

echo 📍 Access Points:
echo    Local:    http://localhost:3000
echo    Network:  http://%LOCAL_IP%:3000
echo.

echo 📦 Starting Next.js dev server...
echo.

npm run dev
