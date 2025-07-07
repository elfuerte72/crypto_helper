#!/bin/bash

# Quick Docker Test Script for Crypto Helper Bot

echo "🐳 Testing Docker container..."
echo "============================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your real tokens and run again."
    exit 1
fi

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "1. Building Docker image..."
docker build -t crypto-helper-test .

echo "2. Running container (detached)..."
docker run -d \
    --name crypto-helper-test-container \
    --env-file .env \
    -p 8080:8080 \
    crypto-helper-test

echo "3. Waiting for container to start..."
sleep 10

echo "4. Testing health endpoints..."
echo "Health check:"
curl -s http://localhost:8080/health | python3 -m json.tool

echo -e "\nLiveness check:"
curl -s http://localhost:8080/health/live | python3 -m json.tool

echo -e "\nContainer logs:"
docker logs crypto-helper-test-container --tail 20

echo -e "\n5. Cleanup..."
docker stop crypto-helper-test-container
docker rm crypto-helper-test-container

echo "✅ Docker test completed!" 