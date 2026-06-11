#!/bin/bash
# RetailVision AI - Stop All Services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   RetailVision AI - Stopping Services${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Stop backend processes
echo -e "${YELLOW}Stopping backend processes...${NC}"
pkill -f "uvicorn app.main" || true
pkill -f "python.*backend" || true

# Stop frontend processes
echo -e "${YELLOW}Stopping frontend processes...${NC}"
pkill -f "npm run dev" || true
pkill -f "node.*next" || true

# Stop Docker containers
echo -e "${YELLOW}Stopping Docker containers...${NC}"
docker stop retailvision_postgres 2>/dev/null || true
docker stop retailvision_redis 2>/dev/null || true
docker rm retailvision_postgres 2>/dev/null || true
docker rm retailvision_redis 2>/dev/null || true

# Clean up PID file
rm -f "$PROJECT_ROOT/.pids"

echo -e "${GREEN}✓ All services stopped${NC}"
echo ""
