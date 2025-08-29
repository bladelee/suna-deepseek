# FROM ghcr.io/astral-sh/uv:python3.11-alpine
FROM ghcr.nju.edu.cn/astral-sh/uv:python3.11-alpine

ENV ENV_MODE production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN apk add --no-cache curl git

# Install Python dependencies
COPY pyproject.toml uv.lock ./
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/root/.cache/uv

# Create a minimal .env file for build context
RUN echo "ENV_MODE=production" > .env && \
    echo "USE_LOCAL_DOCKER_SANDBOX=true" >> .env && \
    echo "REDIS_HOST=redis" >> .env && \
    echo "REDIS_PORT=6379" >> .env && \
    echo "LOG_LEVEL=INFO" >> .env

# Install dependencies - allow uv to update lockfile if needed
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --quiet || \
    (echo "uv sync failed, trying without cache..." && \
     uv sync --quiet)

# Copy application code
COPY . .

# Calculate optimal worker count based on 16 vCPUs
# Using (2*CPU)+1 formula for CPU-bound applications
ENV WORKERS=7
ENV THREADS=2
ENV WORKER_CONNECTIONS=2000

ENV PYTHONPATH=/app
EXPOSE 8000

# Gunicorn configuration
CMD ["sh", "-c", "uv run gunicorn api:app \
  --workers $WORKERS \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 1800 \
  --graceful-timeout 600 \
  --keep-alive 1800 \
  --max-requests 0 \
  --max-requests-jitter 0 \
  --forwarded-allow-ips '*' \
  --worker-connections $WORKER_CONNECTIONS \
  --worker-tmp-dir /dev/shm \
  --preload \
  --log-level info \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --enable-stdio-inheritance \
  --threads $THREADS"]
