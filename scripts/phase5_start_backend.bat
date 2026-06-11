@echo off
REM PHASE 5 Backend Platform - Complete Setup and Startup Guide (Windows)

setlocal enabledelayedexpansion

color 0F
cls
echo.
echo ======================================================================
echo RetailVision AI - PHASE 5: Complete Backend Platform
echo ======================================================================
echo.

REM Check Python
echo [1/8] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)
echo OK - Python found
echo.

REM Create virtual environment
echo [2/8] Setting up Python virtual environment...
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo OK - Virtual environment activated
echo.

REM Install dependencies
echo [3/8] Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -q -r backend\requirements.txt
echo OK - Dependencies installed
echo.

REM Check .env file
echo [4/8] Checking environment configuration...
if not exist ".env" (
    echo Creating .env file from template...
    if exist ".env.example" (
        copy .env.example .env
        echo OK - .env created
    ) else (
        echo ERROR: .env.example not found
        pause
        exit /b 1
    )
) else (
    echo OK - .env file exists
)
echo.

REM Start Docker services
echo [5/8] Starting Docker services...
docker-compose -f docker-compose.yml up -d
echo Waiting 10 seconds for services...
timeout /t 10 /nobreak
echo OK - Docker services started
echo.

REM Create/migrate database
echo [6/8] Setting up database...
cd backend
python -c "
import asyncio
from app.database import init_db, create_tables

async def setup():
    await init_db()
    await create_tables()
    print('OK - Database tables created')

asyncio.run(setup())
"
cd ..
echo.

REM Start backend
echo [7/8] Starting backend service...
echo.
cd backend
echo Launching FastAPI server on port 8000...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd ..

REM This line won't execute if uvicorn is running, but we need it for cleanup
pause
exit /b 0
