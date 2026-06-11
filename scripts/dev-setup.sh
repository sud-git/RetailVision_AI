#!/bin/bash

# RetailVision AI - Development Setup Script
# Initializes the development environment

set -e

echo "🚀 RetailVision AI - Development Setup"
echo "========================================"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Update it with your configuration."
fi

# Create required directories
echo "📁 Creating required directories..."
mkdir -p data logs models

# Start development services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.dev.yml up -d

echo ""
echo "✅ Development environment is ready!"
echo ""
echo "📍 Service URLs:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis: localhost:6379"
echo ""
echo "📖 Next steps:"
echo "   1. Update .env file with your configuration"
echo "   2. View logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "   3. Stop services: docker-compose -f docker-compose.dev.yml down"
echo ""
