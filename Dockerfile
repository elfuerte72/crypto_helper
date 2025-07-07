# Crypto Helper Telegram Bot - Production Dockerfile
# Optimized for Heroku deployment

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set work directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/tmp && \
    chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Expose port (Heroku will set PORT env var)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health/live || exit 1

# Combined start command for bot and health server
CMD ["sh", "-c", "python -c \"import asyncio; from src.main import main; from src.health_check import start_health_server; asyncio.run(asyncio.gather(start_health_server(), main()))\""]