#!/bin/bash
# RetailVision AI - Complete Local Startup Script
# Starts all services in correct order: PostgreSQL, Redis, Backend, Frontend

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000
REDIS_PORT=6379
POSTGRES_PORT=5432
POSTGRES_USER="retailvision"
POSTGRES_PASSWORD="retailvision_dev"
POSTGRES_DB="retailvision_db"

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   RetailVision AI - Complete Local Startup${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Function to check if port is available
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}✗ Port $port ($service) is already in use${NC}"
        return 1
    fi
    return 0
}

# Function to wait for service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}Waiting for $service to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            echo -e "${GREEN}✓ $service is ready (attempt $attempt/$max_attempts)${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done
    
    echo -e "${RED}✗ $service failed to start${NC}"
    return 1
}

# Step 1: Check prerequisites
echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"
check_port $POSTGRES_PORT "PostgreSQL" || exit 1
check_port $REDIS_PORT "Redis" || exit 1
check_port $BACKEND_PORT "Backend" || exit 1
check_port $FRONTEND_PORT "Frontend" || exit 1
echo -e "${GREEN}✓ All ports available${NC}"
echo ""

# Step 2: Start PostgreSQL (using Docker if available)
echo -e "${BLUE}Step 2: Starting PostgreSQL...${NC}"
if command -v docker &> /dev/null; then
    docker run -d \
        --name retailvision_postgres \
        -e POSTGRES_USER=$POSTGRES_USER \
        -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
        -e POSTGRES_DB=$POSTGRES_DB \
        -p $POSTGRES_PORT:5432 \
        postgres:15 \
        2>/dev/null || true
    
    sleep 2
    if wait_for_service localhost $POSTGRES_PORT "PostgreSQL"; then
        export DATABASE_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:$POSTGRES_PORT/$POSTGRES_DB"
        echo -e "${GREEN}✓ PostgreSQL started${NC}"
    else
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Docker not found, assuming PostgreSQL is running${NC}"
    export DATABASE_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:$POSTGRES_PORT/$POSTGRES_DB"
fi
echo ""

# Step 3: Start Redis (using Docker if available)
echo -e "${BLUE}Step 3: Starting Redis...${NC}"
if command -v docker &> /dev/null; then
    docker run -d \
        --name retailvision_redis \
        -p $REDIS_PORT:6379 \
        redis:7-alpine \
        2>/dev/null || true
    
    sleep 2
    if wait_for_service localhost $REDIS_PORT "Redis"; then
        export REDIS_URL="redis://localhost:$REDIS_PORT/0"
        echo -e "${GREEN}✓ Redis started${NC}"
    else
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Docker not found, assuming Redis is running${NC}"
    export REDIS_URL="redis://localhost:$REDIS_PORT/0"
fi
echo ""

# Step 4: Install backend dependencies
echo -e "${BLUE}Step 4: Setting up backend...${NC}"
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Create necessary directories
mkdir -p /tmp/retailvision/{data,logs,models}
export DATA_DIR="/tmp/retailvision/data"
export MODELS_DIR="/tmp/retailvision/models"
export LOGS_DIR="/tmp/retailvision/logs"

echo -e "${GREEN}✓ Backend dependencies installed${NC}"
echo ""

# Step 5: Start backend in background
echo -e "${BLUE}Step 5: Starting backend...${NC}"
cd "$BACKEND_DIR"
export ENVIRONMENT=development
export DEBUG=true
export BACKEND_HOST="0.0.0.0"
export BACKEND_PORT=$BACKEND_PORT
export FRONTEND_URL="http://localhost:$FRONTEND_PORT"

nohup python3 -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $BACKEND_PORT \
    --reload \
    > "$LOGS_DIR/backend.log" 2>&1 &

BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

if wait_for_service localhost $BACKEND_PORT "Backend"; then
    echo -e "${GREEN}✓ Backend started${NC}"
else
    echo -e "${RED}✗ Backend failed to start${NC}"
    cat "$LOGS_DIR/backend.log"
    exit 1
fi
echo ""

# Step 6: Install frontend dependencies
echo -e "${BLUE}Step 6: Setting up frontend...${NC}"
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install -q
fi
echo -e "${GREEN}✓ Frontend dependencies ready${NC}"
echo ""

# Step 7: Start frontend in background
echo -e "${BLUE}Step 7: Starting frontend...${NC}"
export NEXT_PUBLIC_API_URL="http://localhost:$BACKEND_PORT"
export NEXT_PUBLIC_WS_URL="ws://localhost:$BACKEND_PORT"

nohup npm run dev \
    > "$LOGS_DIR/frontend.log" 2>&1 &

FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

if wait_for_service localhost $FRONTEND_PORT "Frontend"; then
    echo -e "${GREEN}✓ Frontend started${NC}"
else
    echo -e "${RED}✗ Frontend failed to start${NC}"
    cat "$LOGS_DIR/frontend.log"
    exit 1
fi
echo ""

# Step 8: Display startup summary
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Service Status:${NC}"
echo -e "  ${GREEN}✓${NC} PostgreSQL:   ${BLUE}postgres://localhost:$POSTGRES_PORT/${POSTGRES_DB}${NC}"
echo -e "  ${GREEN}✓${NC} Redis:        ${BLUE}redis://localhost:$REDIS_PORT${NC}"
echo -e "  ${GREEN}✓${NC} Backend:      ${BLUE}http://localhost:$BACKEND_PORT${NC}"
echo -e "  ${GREEN}✓${NC} Frontend:     ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo -e "  API Docs:          ${BLUE}http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "  Health Check:      ${BLUE}http://localhost:$BACKEND_PORT/health${NC}"
echo -e "  Dashboard:         ${BLUE}http://localhost:$FRONTEND_PORT/dashboard${NC}"
echo -e "  Testing Page:      ${BLUE}http://localhost:$FRONTEND_PORT/testing${NC}"
echo ""
echo -e "${YELLOW}Process IDs:${NC}"
echo -e "  Backend:  $BACKEND_PID"
echo -e "  Frontend: $FRONTEND_PID"
echo ""
echo -e "${YELLOW}To stop services, run:${NC}"
echo -e "  ${BLUE}scripts/stop-all.sh${NC}"
echo ""

# Save PIDs for cleanup
echo "$BACKEND_PID" > "$PROJECT_ROOT/.pids"
echo "$FRONTEND_PID" >> "$PROJECT_ROOT/.pids"

# Keep script running
echo -e "${YELLOW}Monitoring services... (Press Ctrl+C to stop)${NC}"
wait
