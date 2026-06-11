#!/bin/bash
# PHASE 5 Backend Platform - Complete Setup and Startup Guide

echo "======================================================================"
echo "RetailVision AI - PHASE 5: Complete Backend Platform"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check dependencies
echo -e "${BLUE}[1/8] Checking dependencies...${NC}"
command -v python3 &> /dev/null || { echo -e "${RED}Python 3 not found${NC}"; exit 1; }
command -v pip &> /dev/null || { echo -e "${RED}pip not found${NC}"; exit 1; }
echo -e "${GREEN}✓ Dependencies OK${NC}"
echo ""

# Create virtual environment if needed
echo -e "${BLUE}[2/8] Checking Python environment...${NC}"
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Install/upgrade dependencies
echo -e "${BLUE}[3/8] Installing dependencies...${NC}"
pip install --upgrade pip
pip install -q -r backend/requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Check environment file
echo -e "${BLUE}[4/8] Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env created from template${NC}"
    else
        echo -e "${RED}✗ .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi
echo ""

# Start Docker services
echo -e "${BLUE}[5/8] Starting Docker services...${NC}"
docker-compose -f docker-compose.yml up -d
echo "Waiting for services to be ready..."
sleep 10
echo -e "${GREEN}✓ Docker services started${NC}"
echo ""

# Apply database migrations
echo -e "${BLUE}[6/8] Applying database migrations...${NC}"
cd backend
python3 -c "
import asyncio
from app.database import init_db, create_tables

async def setup():
    await init_db()
    await create_tables()
    print('✓ Database tables created')

asyncio.run(setup())
"
cd ..
echo -e "${GREEN}✓ Database ready${NC}"
echo ""

# Start backend service
echo -e "${BLUE}[7/8] Starting backend service...${NC}"
cd backend
echo "Starting FastAPI server..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
sleep 5

# Verify backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend service running on http://localhost:8000${NC}"
else
    echo -e "${RED}✗ Backend service failed to start${NC}"
    kill $BACKEND_PID
    exit 1
fi
echo ""

# Show available endpoints
echo -e "${BLUE}[8/8] Service Summary${NC}"
echo "======================================================================"
echo -e "${GREEN}✓ RetailVision AI PHASE 5 is running!${NC}"
echo ""
echo "Available Endpoints:"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • ReDoc: http://localhost:8000/redoc"
echo "  • Health Check: http://localhost:8000/health"
echo ""
echo "API Routes (Phase 5):"
echo "  • Analytics: GET /api/v1/analytics/overview"
echo "  • Events: GET /api/v1/events"
echo "  • System: GET /api/v1/system/health"
echo "  • Customers: GET /api/v1/customers"
echo "  • Alerts: GET /api/v1/alerts"
echo ""
echo "WebSocket:"
echo "  • Live Events: ws://localhost:8000/ws"
echo ""
echo "Database Services:"
echo "  • PostgreSQL: localhost:5432"
echo "  • Redis: localhost:6379"
echo ""
echo "API Key (for testing):"
echo "  • X-API-Key: demo-key-12345"
echo ""
echo "Example Requests:"
echo "  curl -H 'X-API-Key: demo-key-12345' http://localhost:8000/api/v1/analytics/overview"
echo "  curl -H 'X-API-Key: demo-key-12345' http://localhost:8000/api/v1/system/health"
echo "  curl -H 'X-API-Key: demo-key-12345' http://localhost:8000/api/v1/events"
echo ""
echo "To stop the backend, press Ctrl+C"
echo "To stop Docker services: docker-compose down"
echo "======================================================================"

# Keep the script running
wait $BACKEND_PID
