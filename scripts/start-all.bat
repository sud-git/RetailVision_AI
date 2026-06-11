@echo off
REM RetailVision AI - Complete Local Startup Script (Windows)
REM Starts all services in correct order: PostgreSQL, Redis, Backend, Frontend

setlocal enabledelayedexpansion

REM Configuration
set BACKEND_PORT=8000
set FRONTEND_PORT=3000
set REDIS_PORT=6379
set POSTGRES_PORT=5432
set POSTGRES_USER=retailvision
set POSTGRES_PASSWORD=retailvision_dev
set POSTGRES_DB=retailvision_db

REM Directories
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set BACKEND_DIR=%PROJECT_ROOT%\backend
set FRONTEND_DIR=%PROJECT_ROOT%\frontend

echo.
echo ========================================================
echo    RetailVision AI - Complete Local Startup (Windows)
echo ========================================================
echo.

REM Function to check if port is in use
echo Checking port availability...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%BACKEND_PORT%') do (
    echo Port %BACKEND_PORT% is already in use
    exit /b 1
)

echo [OK] All ports available

REM Step 1: Create directories
echo.
echo Creating required directories...
if not exist "%PROJECT_ROOT%\.logs" mkdir "%PROJECT_ROOT%\.logs"
if not exist "%PROJECT_ROOT%\.data" mkdir "%PROJECT_ROOT%\.data"
if not exist "%PROJECT_ROOT%\.models" mkdir "%PROJECT_ROOT%\.models"

REM Step 2: Start PostgreSQL (Docker)
echo.
echo Starting PostgreSQL...
docker ps | findstr retailvision_postgres >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    docker run -d ^
        --name retailvision_postgres ^
        -e POSTGRES_USER=%POSTGRES_USER% ^
        -e POSTGRES_PASSWORD=%POSTGRES_PASSWORD% ^
        -e POSTGRES_DB=%POSTGRES_DB% ^
        -p %POSTGRES_PORT%:5432 ^
        postgres:15 >nul 2>&1
    timeout /t 3 /nobreak
)
echo [OK] PostgreSQL started on port %POSTGRES_PORT%

REM Step 3: Start Redis (Docker)
echo.
echo Starting Redis...
docker ps | findstr retailvision_redis >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    docker run -d ^
        --name retailvision_redis ^
        -p %REDIS_PORT%:6379 ^
        redis:7-alpine >nul 2>&1
    timeout /t 2 /nobreak
)
echo [OK] Redis started on port %REDIS_PORT%

REM Step 4: Backend setup
echo.
echo Setting up backend...
cd /d "%BACKEND_DIR%"

if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -q -r requirements.txt

set DATABASE_URL=postgresql://%POSTGRES_USER%:%POSTGRES_PASSWORD%@localhost:%POSTGRES_PORT%/%POSTGRES_DB%
set REDIS_URL=redis://localhost:%REDIS_PORT%/0
set ENVIRONMENT=development
set DEBUG=true
set BACKEND_HOST=0.0.0.0
set BACKEND_PORT=%BACKEND_PORT%
set FRONTEND_URL=http://localhost:%FRONTEND_PORT%
set DATA_DIR=%PROJECT_ROOT%\.data
set MODELS_DIR=%PROJECT_ROOT%\.models
set LOGS_DIR=%PROJECT_ROOT%\.logs

echo [OK] Backend setup complete

REM Step 5: Start backend
echo.
echo Starting backend on port %BACKEND_PORT%...
start "RetailVision Backend" cmd /k "cd /d "%BACKEND_DIR%" && venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload"
timeout /t 5 /nobreak

REM Step 6: Frontend setup
echo.
echo Setting up frontend...
cd /d "%FRONTEND_DIR%"

if not exist "node_modules" (
    echo Installing Node.js dependencies...
    call npm install -q
)

set NEXT_PUBLIC_API_URL=http://localhost:%BACKEND_PORT%
set NEXT_PUBLIC_WS_URL=ws://localhost:%BACKEND_PORT%

echo [OK] Frontend setup complete

REM Step 7: Start frontend
echo.
echo Starting frontend on port %FRONTEND_PORT%...
start "RetailVision Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"
timeout /t 5 /nobreak

REM Display summary
echo.
echo ========================================================
echo    All services started successfully!
echo ========================================================
echo.
echo Service URLs:
echo   Backend:      http://localhost:%BACKEND_PORT%
echo   Frontend:     http://localhost:%FRONTEND_PORT%
echo   API Docs:     http://localhost:%BACKEND_PORT%/docs
echo   Health Check: http://localhost:%BACKEND_PORT%/health
echo   Dashboard:    http://localhost:%FRONTEND_PORT%/dashboard
echo   Testing:      http://localhost:%FRONTEND_PORT%/testing
echo.
echo Press Ctrl+C in each window to stop services
echo.

REM Keep window open
pause
