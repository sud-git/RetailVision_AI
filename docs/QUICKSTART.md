# Development Quick Start Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- GPU optional (NVIDIA CUDA for acceleration)

## One-Command Setup

### Linux/macOS
```bash
bash scripts/dev-setup.sh
```

### Windows
```batch
scripts\dev-setup.bat
```

This will:
1. ✅ Check Docker and Docker Compose
2. ✅ Create `.env` file
3. ✅ Create required directories
4. ✅ Start all services

## Service Status

After setup, check services:

```bash
# View running containers
docker-compose -f docker-compose.dev.yml ps

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# View specific service logs
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend
```

## Access Services

Once running:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | React Dashboard |
| Backend API | http://localhost:8000 | FastAPI |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Health | http://localhost:8000/health | Health Check |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache |

## Common Commands

### Backend Development

```bash
# Backend shell
docker exec -it retailvision_backend_dev bash

# Backend Python shell
docker exec -it retailvision_backend_dev python

# Backend logs
docker-compose -f docker-compose.dev.yml logs -f backend

# Restart backend
docker-compose -f docker-compose.dev.yml restart backend
```

### Frontend Development

```bash
# Frontend shell
docker exec -it retailvision_frontend_dev sh

# Frontend logs
docker-compose -f docker-compose.dev.yml logs -f frontend

# Restart frontend
docker-compose -f docker-compose.dev.yml restart frontend
```

### Database

```bash
# Database shell
docker exec -it retailvision_postgres_dev psql -U retailvision retailvision_db

# View tables
\dt

# Exit database
\q
```

### Redis

```bash
# Redis CLI
docker exec -it retailvision_redis_dev redis-cli

# Ping
PING

# List keys
KEYS *

# Exit Redis
EXIT
```

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Docker Issues

```bash
# Clean up Docker
docker system prune -a

# Rebuild images
docker-compose -f docker-compose.dev.yml build --no-cache

# Full reset (careful!)
docker-compose -f docker-compose.dev.yml down -v
bash scripts/dev-setup.sh
```

### Database Connection Error

```bash
# Check database is running
docker exec retailvision_postgres_dev psql -U retailvision -d retailvision_db -c "SELECT 1"

# View database logs
docker-compose -f docker-compose.dev.yml logs postgres
```

### Frontend Not Loading

```bash
# Check frontend is running
curl http://localhost:3000

# View frontend logs
docker-compose -f docker-compose.dev.yml logs frontend

# Check environment variables
docker exec retailvision_frontend_dev env | grep NEXT_PUBLIC
```

## Stop Services

```bash
# Stop all services (keeps data)
docker-compose -f docker-compose.dev.yml down

# Stop and remove data
docker-compose -f docker-compose.dev.yml down -v
```

## Next Steps

1. Read [README.md](../README.md) for overview
2. Check [ARCHITECTURE.md](../docs/ARCHITECTURE.md) for design
3. Start Phase 2: Video ingestion pipeline
4. Add your CCTV stream URL to `.env`

## File Structure

After setup, your directory looks like:

```
RetailVision-AI/
├── .env                    # Your configuration (don't commit!)
├── data/                   # Video files & data
├── logs/                   # Application logs
├── models/                 # ML models
├── backend/               # FastAPI backend
├── frontend/              # Next.js frontend
└── docker-compose.dev.yml # Development config
```

## Tips

- 🔄 Frontend hot-reloads on code changes
- 📝 Backend logs are in `/logs` directory
- 💾 Database data persists in Docker volumes
- 🔧 Modify `.env` to change configuration
- 📊 API docs at http://localhost:8000/docs

Happy coding! 🚀
