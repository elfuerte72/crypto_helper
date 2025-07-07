# Crypto Helper Telegram Bot - Unified Dockerfile
# Simple configuration for development and production

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/

# Create necessary directories
RUN mkdir -p /app/logs && \
    mkdir -p /app/tmp

# Create non-root user for security
RUN groupadd -r botuser && useradd -r -g botuser botuser && \
    chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Expose port for health checks (optional)
EXPOSE 8080

# Default command
CMD ["python", "-m", "src.main"]