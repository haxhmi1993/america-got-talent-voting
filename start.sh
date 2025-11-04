#!/bin/bash

# AGT Voting System - Quick Start Script
# This script helps you get the system up and running quickly

set -e

echo "🎬 AGT Voting System - Quick Start"
echo "=================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "   Visit: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

echo "✅ Docker is installed"

# Check if .env exists, if not copy from .env.example
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please review .env file and update FINGERPRINT_SALT for production use!"
else
    echo "✅ .env file exists"
fi

echo ""
echo "🚀 Starting services with Docker Compose..."
echo ""

# Start services
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo ""
echo "🏥 Checking service health..."

if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend health check failed. Checking logs..."
    docker-compose logs backend | tail -20
fi

if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "⚠️  Frontend may still be starting up..."
fi

echo ""
echo "🎉 System is starting up!"
echo ""
echo "📍 Access points:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Health:    http://localhost:8000/health"
echo "   Metrics:   http://localhost:8000/metrics"
echo ""
echo "📊 View logs:"
echo "   All:       docker-compose logs -f"
echo "   Backend:   docker-compose logs -f backend"
echo "   Frontend:  docker-compose logs -f frontend"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
echo "🧪 Run tests:"
echo "   docker-compose exec backend pytest -v"
echo ""
echo "Sample contestants available:"
echo "   Smith, Johnson, Williams, Brown, Jones"
echo "   Garcia, Martinez, Rodriguez, Wilson, Anderson"
echo ""
echo "Happy voting! 🗳️"
