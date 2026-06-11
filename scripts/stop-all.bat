@echo off
REM RetailVision AI - Stop All Services (Windows)

setlocal enabledelayedexpansion

echo.
echo ========================================================
echo    Stopping RetailVision AI Services (Windows)
echo ========================================================
echo.

echo Stopping backend processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq RetailVision Backend" >nul 2>&1 || true

echo Stopping frontend processes...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq RetailVision Frontend" >nul 2>&1 || true

echo Stopping Docker containers...
docker stop retailvision_postgres >nul 2>&1 || true
docker stop retailvision_redis >nul 2>&1 || true
docker rm retailvision_postgres >nul 2>&1 || true
docker rm retailvision_redis >nul 2>&1 || true

echo.
echo [OK] All services stopped
echo.
