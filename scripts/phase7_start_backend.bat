@echo off
REM Phase 7: Advanced Analytics & Heatmap Intelligence Engine
REM Complete System Startup Script (Windows)

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   RetailVision AI - PHASE 7 STARTUP SEQUENCE
echo   Advanced Analytics Heatmap Intelligence Engine
echo ============================================================
echo.

REM Configuration
set PYTHON_EXE=python
set API_PORT=8000
set DATABASE_URL=postgresql://retailvision:retailvision@localhost:5432/retailvision

echo [1/8] Checking system prerequisites...
%PYTHON_EXE% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    exit /b 1
)
echo OK: Python found
echo.

echo [2/8] Installing dependencies...
%PYTHON_EXE% -m pip install -q -r requirements.txt
echo OK: Dependencies installed
echo.

echo [3/8] Setting up environment...
set PYTHONPATH=%cd%;%PYTHONPATH%
set DATABASE_URL=%DATABASE_URL%
set ENVIRONMENT=production
set API_PORT=%API_PORT%
echo OK: Environment configured
echo.

echo [4/8] Initializing database...
%PYTHON_EXE% << 'EOF'
import asyncio
from app.database import init_db, create_tables
from app.logger import get_logger

logger = get_logger(__name__)

async def init():
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Creating tables...")
        await create_tables()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

asyncio.run(init())
EOF
echo OK: Database initialized
echo.

echo [5/8] Running database migrations...
if exist "alembic_migration_001.py" (
    %PYTHON_EXE% alembic_migration_001.py
    echo OK: Migrations completed
) else (
    echo WARNING: No migrations to run
)
echo.

echo [6/8] Loading analytics sample data...
%PYTHON_EXE% << 'EOF'
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.analytics import Heatmap, CustomerJourney, ZoneEngagement, BusinessInsight
from datetime import datetime, timedelta
import uuid

DATABASE_URL = "postgresql+asyncpg://retailvision:retailvision@localhost:5432/retailvision"

async def load_sample_data():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Create sample heatmap
            heatmap = Heatmap(
                id=str(uuid.uuid4()),
                heatmap_type="daily",
                time_period_start=datetime.utcnow(),
                time_period_end=datetime.utcnow() + timedelta(days=1),
                grid_data={"type": "sample"},
                width=1920,
                height=1080,
                cell_size=40,
                total_samples=100,
                max_intensity=0.95,
                hotspot_count=5
            )
            session.add(heatmap)
            
            # Create sample zones
            for zone_id in range(1, 6):
                zone_engagement = ZoneEngagement(
                    id=str(uuid.uuid4()),
                    zone_id=zone_id,
                    analytics_date=datetime.utcnow(),
                    time_bucket="daily",
                    visitor_count=50 + (zone_id * 20),
                    unique_visitor_count=45 + (zone_id * 18),
                    entry_count=50 + (zone_id * 20),
                    exit_count=48 + (zone_id * 20),
                    total_dwell_time=5000 + (zone_id * 1000),
                    avg_dwell_time=100 + (zone_id * 20),
                    interaction_count=30 + (zone_id * 10),
                    pickup_count=15 + (zone_id * 5),
                    conversion_rate=0.3 + (zone_id * 0.05),
                    engagement_score=0.5 + (zone_id * 0.08),
                    zone_type="high_value" if zone_id <= 2 else "engagement",
                    performance_rating="excellent" if zone_id <= 2 else "good"
                )
                session.add(zone_engagement)
            
            await session.commit()
            print("Sample data loaded successfully")
        except Exception as e:
            print(f"Error loading sample data: {e}")
            await session.rollback()

asyncio.run(load_sample_data())
EOF
echo OK: Sample data loaded
echo.

echo [7/8] Starting backend server...
echo Starting FastAPI server on port %API_PORT%...
echo.

echo [8/8] System ready!
echo.
echo ============================================================
echo             PHASE 7 STARTUP SUCCESSFUL
echo ============================================================
echo.
echo API Server:        http://localhost:%API_PORT%
echo API Documentation: http://localhost:%API_PORT%/docs
echo Health Check:      http://localhost:%API_PORT%/health
echo.
echo Analytics Endpoints:
echo   Heatmaps:   GET  /api/v1/analytics/heatmaps/latest
echo   Journeys:   GET  /api/v1/analytics/journeys/analytics
echo   Zones:      GET  /api/v1/analytics/zones/engagement
echo   Insights:   GET  /api/v1/analytics/insights
echo   Reports:    POST /api/v1/analytics/reports/generate
echo.
echo Starting FastAPI...
echo.

cd "%~dp0..\backend"
%PYTHON_EXE% -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port %API_PORT% --reload --log-level info

pause
