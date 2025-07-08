#!/bin/bash

# Complete Heroku Deployment Script
# Run this after setting secret environment variables

APP_NAME="crypto-helper-testing"

echo "🎯 Completing Heroku deployment for $APP_NAME"
echo "=============================================="

# Check if secret variables are set
echo "1. Checking secret variables..."
BOT_TOKEN=$(heroku config:get BOT_TOKEN -a $APP_NAME)
RAPIRA_API_KEY=$(heroku config:get RAPIRA_API_KEY -a $APP_NAME)
API_LAYER_KEY=$(heroku config:get API_LAYER_KEY -a $APP_NAME)

if [[ -z "$BOT_TOKEN" ]]; then
    echo "❌ BOT_TOKEN not set. Please run ./set_heroku_secrets.sh first"
    exit 1
fi

# RAPIRA_API_KEY is optional (Rapira works without API key)
if [[ -z "$RAPIRA_API_KEY" ]]; then
    echo "ℹ️  RAPIRA_API_KEY is empty (Rapira API works without key)"
fi

if [[ -z "$API_LAYER_KEY" ]]; then
    echo "❌ API_LAYER_KEY not set. Please run ./set_heroku_secrets.sh first"
    exit 1
fi

echo "✅ All secret variables are set"

# Release the container
echo "2. Releasing container..."
if heroku container:release web -a $APP_NAME; then
    echo "✅ Container released successfully"
else
    echo "❌ Failed to release container"
    exit 1
fi

# Wait a bit for the app to start
echo "3. Waiting for app to start..."
sleep 30

# Check app status
echo "4. Checking app status..."
heroku ps -a $APP_NAME

echo ""
echo "5. Checking recent logs..."
heroku logs --tail=50 -a $APP_NAME

echo ""
echo "6. Testing health endpoint..."
APP_URL="https://crypto-helper-testing-7c5ffa6d9fbf.herokuapp.com"
if curl -s "$APP_URL/health" | grep -q "healthy\|alive"; then
    echo "✅ Health check passed!"
else
    echo "⚠️  Health check failed or app not ready yet"
fi

echo ""
echo "🎉 DEPLOYMENT COMPLETED!"
echo "======================="
echo ""
echo "📱 App URL: $APP_URL"
echo "🩺 Health: $APP_URL/health"
echo "📊 Metrics: $APP_URL/metrics"
echo ""
echo "📋 Useful commands:"
echo "heroku logs --tail -a $APP_NAME          # View logs"
echo "heroku restart -a $APP_NAME              # Restart app"
echo "heroku config -a $APP_NAME               # View config"
echo "heroku ps -a $APP_NAME                   # View dynos"
echo ""
echo "🤖 Your Telegram bot should now be running on Heroku!" 