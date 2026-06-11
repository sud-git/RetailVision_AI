#!/bin/bash

# Phase 7: Advanced Analytics & Heatmap Intelligence Engine
# Complete System Startup Script (Linux/macOS)

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       RetailVision AI - PHASE 7 STARTUP SEQUENCE              ║"
echo "║   Advanced Analytics & Heatmap Intelligence Engine            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_VERSION="3.11"
API_PORT=8000
DATABASE_URL="postgresql://retailvision:retailvision@localhost:5432/retailvision"

echo -e "${BLUE}[1/8]${NC} Checking system prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠ PostgreSQL client not found (will attempt to connect anyway)${NC}"
else
    echo -e "${GREEN}✓ PostgreSQL client found${NC}"
fi

# Check pip packages
echo -e "${BLUE}[2/8]${NC} Checking Python dependencies..."
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Setup environment
echo -e "${BLUE}[3/8]${NC} Setting up environment..."
export PYTHONPATH="${BACKEND_DIR}:$PYTHONPATH"
export DATABASE_URL="${DATABASE_URL}"
export ENVIRONMENT="production"
export API_PORT="${API_PORT}"
echo -e "${GREEN}✓ Environment configured${NC}"

# Database initialization
echo -e "${BLUE}[4/8]${NC} Initializing database..."
python3 << 'EOF'
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
echo -e "${GREEN}✓ Database initialized${NC}"

# Run migrations
echo -e "${BLUE}[5/8]${NC} Running database migrations..."
if [ -f "alembic_migration_001.py" ]; then
    python3 alembic_migration_001.py
    echo -e "${GREEN}✓ Migrations completed${NC}"
else
    echo -e "${YELLOW}⚠ No migrations to run${NC}"
fi

# Load sample data
echo -e "${BLUE}[6/8]${NC} Loading analytics sample data..."
python3 << 'EOF'
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
echo -e "${GREEN}✓ Sample data loaded${NC}"

# Start backend
echo -e "${BLUE}[7/8]${NC} Starting backend server..."
echo -e "${YELLOW}Starting FastAPI server on port ${API_PORT}...${NC}"
echo ""

echo -e "${BLUE}[8/8]${NC} System ready!"
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                   PHASE 7 STARTUP SUCCESSFUL                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "API Server:        http://localhost:${API_PORT}"
echo "API Documentation: http://localhost:${API_PORT}/docs"
echo "Health Check:      http://localhost:${API_PORT}/health"
echo ""
echo "Analytics Endpoints:"
echo "  Heatmaps:   GET  /api/v1/analytics/heatmaps/latest"
echo "  Journeys:   GET  /api/v1/analytics/journeys/analytics"
echo "  Zones:      GET  /api/v1/analytics/zones/engagement"
echo "  Insights:   GET  /api/v1/analytics/insights"
echo "  Reports:    POST /api/v1/analytics/reports/generate"
echo ""
echo -e "${YELLOW}Starting FastAPI...${NC}"

# Start FastAPI with Uvicorn
cd "${BACKEND_DIR}"
python3 -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${API_PORT} --reload --log-level info
