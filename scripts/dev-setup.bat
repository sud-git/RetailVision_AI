@echo off
REM RetailVision AI - Development Setup Script (Windows)
REM Initializes the development environment

echo.
echo 🚀 RetailVision AI - Development Setup
echo ========================================

REM Check Docker
where docker >nul 2>nul
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker first.
    exit /b 1
)

REM Check Docker Compose
where docker-compose >nul 2>nul
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ✅ .env file created. Update it with your configuration.
)

REM Create required directories
echo 📁 Creating required directories...
if not exist data mkdir data
if not exist logs mkdir logs
if not exist models mkdir models

REM Start development services
echo 🐳 Starting Docker services...
docker-compose -f docker-compose.dev.yml up -d

echo.
echo ✅ Development environment is ready!
echo.
echo 📍 Service URLs:
echo    - Frontend: http://localhost:3000
echo    - Backend API: http://localhost:8000
echo    - API Docs: http://localhost:8000/docs
echo    - PostgreSQL: localhost:5432
echo    - Redis: localhost:6379
echo.
echo 📖 Next steps:
echo    1. Update .env file with your configuration
echo    2. View logs: docker-compose -f docker-compose.dev.yml logs -f
echo    3. Stop services: docker-compose -f docker-compose.dev.yml down
echo.
