#!/bin/bash

# Set Secret Environment Variables for Heroku
# This script helps set up secret variables from your .env file

APP_NAME="crypto-helper-testing"

echo "🔐 Setting up secret environment variables for $APP_NAME"
echo "========================================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file with your tokens first."
    exit 1
fi

echo "⚠️  This script will read your .env file and set variables in Heroku."
echo "Make sure your .env contains the real tokens, not example values."
echo ""
read -p "Continue? (y/N): " confirm

if [[ $confirm != [yY] ]]; then
    echo "Cancelled."
    exit 0
fi

# Function to get value from .env file
get_env_value() {
    local key=$1
    grep "^$key=" .env | cut -d '=' -f2- | tr -d '"'"'"
}

# Get values from .env
BOT_TOKEN=$(get_env_value "BOT_TOKEN")
RAPIRA_API_KEY=$(get_env_value "RAPIRA_API_KEY")
API_LAYER_KEY=$(get_env_value "API_LAYER_KEY")

# Check if values are not empty and not example values
if [[ -z "$BOT_TOKEN" || "$BOT_TOKEN" == "your_bot_token_here" ]]; then
    echo "❌ BOT_TOKEN is empty or contains example value"
    echo "Please set real BOT_TOKEN in .env file"
    exit 1
fi

# RAPIRA_API_KEY is optional (Rapira works without API key)
if [[ -n "$RAPIRA_API_KEY" && "$RAPIRA_API_KEY" == "your_rapira_api_key_here" ]]; then
    echo "⚠️  RAPIRA_API_KEY contains example value, setting to empty"
    RAPIRA_API_KEY=""
fi

if [[ -z "$API_LAYER_KEY" || "$API_LAYER_KEY" == "your_api_layer_key_here" ]]; then
    echo "❌ API_LAYER_KEY is empty or contains example value"
    echo "Please set real API_LAYER_KEY in .env file"
    exit 1
fi

echo "Setting secret variables..."

# Set BOT_TOKEN
echo "1. Setting BOT_TOKEN..."
if heroku config:set BOT_TOKEN="$BOT_TOKEN" -a $APP_NAME; then
    echo "✅ BOT_TOKEN set successfully"
else
    echo "❌ Failed to set BOT_TOKEN"
    exit 1
fi

# Set RAPIRA_API_KEY (optional)
echo "2. Setting RAPIRA_API_KEY..."
if [[ -n "$RAPIRA_API_KEY" ]]; then
    if heroku config:set RAPIRA_API_KEY="$RAPIRA_API_KEY" -a $APP_NAME; then
        echo "✅ RAPIRA_API_KEY set successfully"
    else
        echo "❌ Failed to set RAPIRA_API_KEY"
        exit 1
    fi
else
    echo "ℹ️  RAPIRA_API_KEY is empty (Rapira works without API key)"
    heroku config:unset RAPIRA_API_KEY -a $APP_NAME 2>/dev/null || true
fi

# Set API_LAYER_KEY
echo "3. Setting API_LAYER_KEY..."
if heroku config:set API_LAYER_KEY="$API_LAYER_KEY" -a $APP_NAME; then
    echo "✅ API_LAYER_KEY set successfully"
else
    echo "❌ Failed to set API_LAYER_KEY"
    exit 1
fi

echo ""
echo "🎉 All secret variables set successfully!"
echo ""
echo "Current config:"
heroku config -a $APP_NAME

echo ""
echo "Next steps:"
echo "1. Wait for container build to complete"
echo "2. Run: heroku container:release web -a $APP_NAME"
echo "3. Check: heroku logs --tail -a $APP_NAME" 