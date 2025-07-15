# Crypto Helper Telegram Bot - Production Dockerfile

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

# Railway будет автоматически назначать PORT
# Expose port (Railway автоматически назначит PORT)
EXPOSE 8080

# Health check для Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health/live || exit 1

# Start application using dedicated starter script with internal keep-alive
CMD ["python", "src/start_app.py"]