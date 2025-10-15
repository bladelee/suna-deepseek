#!/bin/bash

# Start Local Docker Sandbox Development Environment
# This script sets up the local development environment with Docker-based sandboxes

set -e

echo "🚀 Starting Local Docker Sandbox Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check Docker socket permissions
if [ ! -S /var/run/docker.sock ]; then
    echo "❌ Docker socket not found at /var/run/docker.sock"
    echo "   This usually means Docker is not running or not accessible"
    exit 1
fi

# Check if current user can access Docker
if ! docker ps > /dev/null 2>&1; then
    echo "⚠️  Current user cannot access Docker. This might be a permission issue."
    echo "   You may need to add your user to the docker group:"
    echo "   sudo usermod -aG docker $USER"
    echo "   Then log out and log back in, or run: newgrp docker"
    echo ""
    echo "   Or run this script with sudo (not recommended for production)"
    echo "   sudo $0"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if required files exist
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from example..."
    if [ -f "docker-sandbox.env.example" ]; then
        cp docker-sandbox.env.example .env
        echo "✅ Created .env from docker-sandbox.env.example"
        echo "📝 Please edit .env file with your configuration before continuing."
        echo "   Press Enter when ready to continue..."
        read
    else
        echo "❌ docker-sandbox.env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Pull latest images
echo "📥 Pulling latest Docker images..."
docker-compose -f docker-compose.docker-sandbox.yml pull

# Start services
echo "🔧 Starting services..."
docker-compose -f docker-compose.docker-sandbox.yml up -d redis

# Wait for Redis to be healthy
echo "⏳ Waiting for Redis to be ready..."
until docker-compose -f docker-compose.docker-sandbox.yml exec -T redis redis-cli ping > /dev/null 2>&1; do
    echo "   Waiting for Redis..."
    sleep 2
done
echo "✅ Redis is ready"

# Start backend services
echo "🔧 Starting backend services..."
docker-compose -f docker-compose.docker-sandbox.yml up -d api worker

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check API health
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ API service is healthy"
else
    echo "⚠️  API service health check failed, but it may still be starting up"
fi

# Check worker health
if docker-compose -f docker-compose.docker-sandbox.yml exec -T worker uv run worker_health.py > /dev/null 2>&1; then
    echo "✅ Worker service is healthy"
else
    echo "⚠️  Worker service health check failed, but it may still be starting up"
fi

echo ""
echo "🎉 Local Docker Sandbox Development Environment is ready!"
echo ""
echo "📋 Service URLs:"
echo "   API: http://localhost:8000"
echo "   Redis: localhost:6379"
echo ""
echo "🔧 Management Commands:"
echo "   View logs: docker-compose -f docker-compose.docker-sandbox.yml logs -f"
echo "   Stop services: docker-compose -f docker-compose.docker-sandbox.yml down"
echo "   Restart services: docker-compose -f docker-compose.docker-sandbox.yml restart"
echo ""
echo "🐳 Docker Sandbox Features:"
echo "   - Local Docker containers as sandboxes"
echo "   - No external Daytona dependency"
echo "   - Full isolation and security"
echo "   - Easy debugging and development"
echo ""
echo "📚 Next Steps:"
echo "   1. Configure your .env file with API keys"
echo "   2. Test the API endpoints"
echo "   3. Create your first sandbox"
echo ""
echo "Happy coding! 🚀"
