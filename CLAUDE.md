# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kortix (formerly Suna) is an open-source platform for building, managing, and training AI agents. It consists of:
- **Backend**: Python/FastAPI service with agent orchestration, LLM integration, and tool system
- **Frontend**: Next.js/React dashboard for agent management and chat interfaces
- **Agent Runtime**: Docker-based isolated execution environments
- **Database**: Supabase for authentication, user management, and data storage

## Development Commands

### Setup & Installation
```bash
# Run the setup wizard (recommended first step)
python setup.py

# Start the platform (after setup)
python start.py

# Manual setup alternative
docker compose up -d  # Start all services
```

### Frontend Development
```bash
cd frontend
npm install          # Install dependencies
npm run dev         # Start development server
npm run build       # Build for production
npm run start       # Start production server
npm run lint        # Run ESLint
npm run format      # Format code with Prettier
npm run format:check # Check formatting
```

### Backend Development
```bash
cd backend

# Install dependencies with uv
uv sync

# Run API server
uv run api.py

# Run background worker
uv run dramatiq --processes 4 --threads 4 run_agent_background

# Run tests
uv run pytest
```

### Docker Commands
```bash
# Start all services
docker compose up -d

# Start specific services
docker compose up redis -d        # Just Redis
docker compose up api worker -d   # API and worker

# View logs
docker compose logs -f

# Stop services
docker compose down

# Check service status
docker compose ps
```

### Testing
```bash
# Backend tests
cd backend
uv run pytest

# Frontend tests (if available)
cd frontend
npm test
```

## Architecture Highlights

### Key Components
- **Backend API** (`/backend`): FastAPI service with LLM integration via LiteLLM
- **Frontend Dashboard** (`/frontend`): Next.js app with agent management UI
- **Agent Runtime**: Daytona/Docker-based sandboxed execution
- **Database**: Supabase with PostgreSQL and authentication
- **Caching**: Redis for sessions and feature flags

### Service Structure
- **Redis**: Port 6379 - Caching and session management
- **Backend API**: Port 8000 - Main API endpoints
- **Worker**: Background task processing
- **Frontend**: Port 3000 - Web interface

### Environment Configuration
- Setup wizard creates `.env` (backend) and `.env.local` (frontend)
- Required services: Supabase, LLM provider, Daytona, Tavily, Firecrawl
- Optional: RapidAPI, custom MCP servers, Slack integration

## Development Workflow

1. **Initial Setup**: Run `python setup.py` to configure all services
2. **Development**: Use Docker Compose or run services individually
3. **Testing**: Backend uses pytest, frontend may have Jest/React Testing Library
4. **Deployment**: Docker-based deployment with production compose files

## Common Tasks

### Adding New Tools
1. Create tool in `/backend/agent/tools/`
2. Register tool in the agent system
3. Update frontend components if needed

### Database Changes
1. Create migration in `/backend/supabase/migrations/`
2. Run `supabase db push` from backend directory
3. Update Prisma schema if needed

### Feature Flags
- Managed via Redis-backed system in `/backend/flags/`
- Use CLI: `python setup.py enable|disable|list <flag>`
- API endpoints: `/feature-flags`

## Troubleshooting

- **Redis connection issues**: Check `REDIS_HOST` in `.env` (localhost vs redis)
- **Docker issues**: Ensure Docker is running and sockets are accessible
- **API keys**: Verify all required API keys are configured in `.env`
- **Database**: Ensure Supabase project is properly configured and migrations applied