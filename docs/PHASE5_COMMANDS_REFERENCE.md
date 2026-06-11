# PHASE 5 COMMAND REFERENCE

## Quick Commands

### Start Backend

```bash
# Linux/macOS (best for quick start)
chmod +x scripts/phase5_start_backend.sh
./scripts/phase5_start_backend.sh

# Windows
scripts\phase5_start_backend.bat

# Manual (with full control)
python3 -m venv venv
source venv/bin/activate          # Linux/macOS
# OR: venv\Scripts\activate.bat   # Windows
pip install -r backend/requirements.txt
docker-compose up -d
cd backend
python3 -m uvicorn app.main:app --reload
```

### Test Everything

```bash
# Run integration tests
python backend/test_phase5.py

# Expected: ~21 tests, all passing
```

---

## API Testing Commands

### Health Check (No Auth)
```bash
# Returns service status
curl http://localhost:8000/health
```

### With API Key Header
```bash
API_KEY="demo-key-12345"

# Replace {{ENDPOINT}} with actual endpoint
curl -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/{{ENDPOINT}}
```

---

## Analytics API

### Get Overview
```bash
curl -H "X-API-Key: demo-key-12345" \
  http://localhost:8000/api/v1/analytics/overview
```

**Response**:
```json
{
  "success": true,
  "data": {
    "total_customers_today": 42,
    "active_customers": 15,
    "total_interactions": 128,
    "avg_dwell_time_seconds": 245
  },
  "timestamp": "2026-05-30T10:30:00Z"
}
```

### Get Dwell Time for Zone
```bash
curl -H "X-API-Key: demo-key-12345" \
  http://localhost:8000/api/v1/analytics/dwell-time/zone_001
```

### Get All Zone Analytics
```bash
curl -H "X-API-Key: demo-key-12345" \
  http://localhost:8000/api/v1/analytics/zones
```

### Get Interaction Analytics
```bash
curl -H "X-API-Key: demo-key-12345" \
  http://localhost:8000/api/v1/analytics/interactions
```

---

## Events API

### Get Recent Events (Last Hour)
```bash
curl -H "X-API-Key: demo-key-12345" \
  "http://localhost:8000/api/v1/events/recent?skip=0&limit=50"
```

### Get Events (Custom Hours)
```bash
# Get events from last 24 hours
curl -H "X-API-Key: demo-key-12345" \
  "http://localhost:8000/api/v1/events?hours=24&skip=0&limit=100"

# Pagination parameters:
# skip=0 (offset)
# limit=50 (results per page)
```

---

## System API

### Health Check (With Auth)
```bash
curl -H "X-API-Key: demo-key-12345" \
  http://localhost:8000/api/v1/system/health
```

**Response**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "database": "connected",
    "redis": "connected",
    "service": "running"
  }
}
```

### Get Metrics
```bash
curl -H "X-API-Key: demo-key-12345" \
  http://localhost:8000/api/v1/system/metrics
```

### Get Status
```bash
curl -H "X-API-Key: demo-key-12345" \
  http://localhost:8000/api/v1/system/status
```

---

## Customers API

### List Customers
```bash
curl -H "X-API-Key: demo-key-12345" \
  "http://localhost:8000/api/v1/customers?skip=0&limit=10"
```

### Get Customer Details
```bash
curl -H "X-API-Key: demo-key-12345" \
  http://localhost:8000/api/v1/customers/{{customer_id}}
```

### Create Customer
```bash
curl -X POST \
  -H "X-API-Key: demo-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "external_id": "ext_12345",
    "phone": "+1-555-1234"
  }' \
  http://localhost:8000/api/v1/customers
```

### Update Customer
```bash
curl -X PUT \
  -H "X-API-Key: demo-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_tier": "vip",
    "is_active": true
  }' \
  http://localhost:8000/api/v1/customers/{{customer_id}}
```

---

## Alerts API

### List Active Alerts
```bash
curl -H "X-API-Key: demo-key-12345" \
  "http://localhost:8000/api/v1/alerts?skip=0&limit=50"
```

### Get Critical Alerts Only
```bash
curl -H "X-API-Key: demo-key-12345" \
  "http://localhost:8000/api/v1/alerts/critical"
```

---

## WebSocket Commands

### Connect
```bash
# Install wscat (if needed)
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws
```

### Subscribe to Channel
```
# In wscat terminal:
subscribe:events
subscribe:interactions
subscribe:anomalies
subscribe:alerts
```

### Test Connection
```
ping
# Server responds: {"type": "pong"}
```

### Unsubscribe
```
unsubscribe:events
```

### WebSocket Message Format
```json
{
  "type": "event",
  "event_type": "shelf_interaction",
  "channel": "interactions",
  "data": {
    "customer_id": "uuid",
    "zone_id": "zone_001",
    "interaction_type": "entry"
  },
  "timestamp": "2026-05-30T10:30:00Z"
}
```

---

## Docker Commands

### Check Services
```bash
docker-compose ps
```

### View Logs
```bash
# Backend
docker-compose logs backend

# Database
docker-compose logs postgres

# Redis
docker-compose logs redis

# Follow logs (live)
docker-compose logs -f backend
```

### Restart Services
```bash
docker-compose restart

# Or specific service
docker-compose restart postgres
docker-compose restart redis
```

### Stop Services
```bash
docker-compose down

# With volume cleanup
docker-compose down -v
```

---

## Database Commands

### Connect to PostgreSQL
```bash
# From terminal
psql -h localhost -U postgres -d retailvision

# Then run SQL:
\dt                              # List tables
SELECT * FROM customers LIMIT 5; # Query table
\q                               # Exit
```

### Connect to Redis
```bash
# From terminal
redis-cli

# In redis-cli:
KEYS "retail:*"           # List all retail keys
XLEN retail:interactions  # Length of stream
XREAD COUNT 10 STREAMS retail:interactions 0  # Read events
```

### View Database Schema
```bash
# In psql:
\d customers              # Show table structure
\d+ tracking_sessions     # Show with indexes
\di                       # List all indexes
```

---

## API Key & Security

### Valid Demo Keys
```
demo-key-12345    # 1000 requests/min (full access)
test-key-67890    # 100 requests/min (read-only)
```

### Test Missing API Key (Should be 401)
```bash
curl http://localhost:8000/api/v1/analytics/overview
```

### Test Invalid API Key (Should be 403)
```bash
curl -H "X-API-Key: invalid-key" \
  http://localhost:8000/api/v1/analytics/overview
```

### Test Rate Limiting
```bash
# Create a small script to test rate limits
for i in {1..1100}; do
  curl -H "X-API-Key: demo-key-12345" \
    http://localhost:8000/api/v1/system/health
  echo "Request $i"
done
# Should get 429 after 1000 requests in window
```

---

## Documentation URLs

### OpenAPI Documentation
```
http://localhost:8000/docs       # Interactive Swagger UI
http://localhost:8000/redoc      # ReDoc documentation
http://localhost:8000/openapi.json  # OpenAPI JSON
```

---

## Troubleshooting Commands

### Check Python Version
```bash
python3 --version  # Must be 3.11+
```

### Check Dependencies
```bash
pip list | grep -E "fastapi|sqlalchemy|pydantic|redis"
```

### Reinstall Dependencies
```bash
pip install --force-reinstall -r backend/requirements.txt
```

### Clear Cache
```bash
# Linux/macOS
find . -type d -name __pycache__ -exec rm -r {} +
find . -type d -name .pytest_cache -exec rm -r {} +

# Windows
for /d /r . %d in (__pycache__) do @if exist "%d" rmdir /s /q "%d"
```

### Check Port Usage
```bash
# Linux/macOS
lsof -i :8000       # See what's using port 8000
lsof -ti:8000 | xargs kill -9  # Kill it

# Windows
netstat -ano | findstr :8000   # Find PID using port 8000
taskkill /PID {{PID}} /F       # Kill by PID
```

### Check Backend Logs
```bash
# If running in foreground, see real-time logs
# If running in Docker
docker-compose logs -f backend

# Last 50 lines
docker-compose logs --tail 50 backend
```

### Test Database Connection
```bash
python3 -c "
import asyncio
from backend.app.database import init_db
asyncio.run(init_db())
print('Database connected!')
"
```

### Test Redis Connection
```bash
python3 -c "
import asyncio
import redis.asyncio as redis
async def test():
    r = await redis.from_url('redis://localhost:6379')
    await r.ping()
    print('Redis connected!')
asyncio.run(test())
"
```

---

## Batch Request Examples

### Using jq (JSON processor)
```bash
# Get all customers, filter to emails only
curl -H "X-API-Key: demo-key-12345" \
  http://localhost:8000/api/v1/customers | jq '.data[].email'

# Get analytics, pretty print
curl -H "X-API-Key: demo-key-12345" \
  http://localhost:8000/api/v1/analytics/overview | jq '.'
```

### Using Python
```python
import httpx
import asyncio

async def fetch_analytics():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/analytics/overview",
            headers={"X-API-Key": "demo-key-12345"}
        )
        return response.json()

result = asyncio.run(fetch_analytics())
print(result)
```

---

## Performance Testing

### Simple Load Test
```bash
# Test 100 requests
for i in {1..100}; do
  curl -s -H "X-API-Key: demo-key-12345" \
    http://localhost:8000/api/v1/analytics/overview > /dev/null
  echo "Request $i"
done
```

### Using Apache Bench (ab)
```bash
# 1000 requests, 10 concurrent
ab -n 1000 -c 10 \
  -H "X-API-Key: demo-key-12345" \
  http://localhost:8000/api/v1/analytics/overview
```

### Using wrk (load testing tool)
```bash
wrk -t4 -c100 -d10s \
  -H "X-API-Key: demo-key-12345" \
  http://localhost:8000/api/v1/analytics/overview
```

---

## Monitoring & Metrics

### Check Active Connections
```bash
# PostgreSQL
psql -c "SELECT * FROM pg_stat_activity;"

# Redis
redis-cli INFO connections
```

### Monitor Real-Time Metrics
```bash
# Redis memory usage
redis-cli INFO memory

# Database connections
docker exec postgres psql -U postgres -c \
  "SELECT count(*) FROM pg_stat_activity;"
```

---

## Cleanup & Reset

### Full Reset (Caution!)
```bash
# Stop services
docker-compose down -v

# Remove cache
rm -rf backend/__pycache__
rm -rf .pytest_cache

# Restart
./scripts/phase5_start_backend.sh
```

### Reset Database Only
```bash
# Remove volume
docker volume rm retailvision_postgres_data

# Restart services
docker-compose restart postgres
```

### Clear Redis Cache
```bash
redis-cli FLUSHALL  # WARNING: Clears all Redis data
```

---

## Common Workflows

### Daily Startup
```bash
# Check services are running
docker-compose ps

# If not running
docker-compose up -d

# Start backend
./scripts/phase5_start_backend.sh
```

### Run Tests
```bash
cd backend
python test_phase5.py
```

### Check System Health
```bash
curl -H "X-API-Key: demo-key-12345" \
  http://localhost:8000/api/v1/system/health | jq .
```

### Monitor Live Events
```bash
# Terminal 1: Start backend
./scripts/phase5_start_backend.sh

# Terminal 2: Connect WebSocket and monitor
wscat -c ws://localhost:8000/ws
subscribe:events
# Now events stream in real-time
```

---

## Environment Variables

### .env File Location
```
backend/.env
```

### Key Variables
```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/retailvision
REDIS_URL=redis://localhost:6379
API_KEY_1=demo-key-12345
API_KEY_1_RATE_LIMIT=1000
DEBUG=true
ENVIRONMENT=development
```

### Change Config
```bash
# Edit .env file
nano backend/.env

# Restart backend to apply
docker-compose restart
```

---

**Phase 5 Commands Reference Complete!** 🚀

For more details, see:
- `docs/PHASE5_COMPLETE.md` - Full documentation
- `PHASE5_QUICKSTART.md` - Quick start guide
- `PHASE5_COMPLETION_SUMMARY.md` - Completion report
