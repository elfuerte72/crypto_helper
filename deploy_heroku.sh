#!/bin/bash

# Heroku Deployment Script for Crypto Helper Bot
# Automated deployment to Heroku using Container Registry

set -e

echo "🚀 Deploying Crypto Helper Bot to Heroku (testing branch)..."
echo "========================================================="

# Configuration
APP_NAME="crypto-helper-testing"
BRANCH="testing"

# Check prerequisites
echo "1. Checking prerequisites..."

# Check Heroku CLI
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Installing..."
    echo "   Please install: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check git branch
current_branch=$(git branch --show-current)
if [ "$current_branch" != "$BRANCH" ]; then
    echo "⚠️  Current branch is $current_branch, switching to $BRANCH..."
    git checkout $BRANCH
fi

echo "✅ Prerequisites checked"

# Login to Heroku
echo "2. Heroku authentication..."
heroku auth:whoami > /dev/null 2>&1 || {
    echo "Please login to Heroku:"
    heroku login
}
echo "✅ Heroku authenticated"

# Login to Container Registry
echo "3. Container Registry login..."
heroku container:login
echo "✅ Container Registry authenticated"

# Create or configure app
echo "4. Setting up Heroku app..."
if heroku apps:info $APP_NAME > /dev/null 2>&1; then
    echo "✅ App $APP_NAME already exists"
else
    echo "Creating new app: $APP_NAME"
    heroku apps:create $APP_NAME --region us
fi

# Set stack to container
echo "5. Setting stack to container..."
heroku stack:set container -a $APP_NAME

# Configure environment variables
echo "6. Configuring environment variables..."
heroku config:set ENVIRONMENT=production -a $APP_NAME
heroku config:set LOG_LEVEL=INFO -a $APP_NAME
heroku config:set API_TIMEOUT=30 -a $APP_NAME
heroku config:set API_RETRY_COUNT=3 -a $APP_NAME
heroku config:set USE_MOCK_DATA=false -a $APP_NAME
heroku config:set RAPIRA_API_URL=https://api.rapira.net/open/market/rates -a $APP_NAME
heroku config:set API_LAYER_URL=https://api.apilayer.com/exchangerates_data -a $APP_NAME

echo "✅ Basic config set"
echo ""
echo "⚠️  IMPORTANT: You need to set sensitive variables manually:"
echo "   heroku config:set BOT_TOKEN=your_actual_bot_token -a $APP_NAME"
echo "   heroku config:set RAPIRA_API_KEY=your_actual_api_key -a $APP_NAME"
echo "   heroku config:set API_LAYER_KEY=your_actual_api_layer_key -a $APP_NAME"
echo ""
read -p "Have you set the required secret variables? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "Please set the secret environment variables and run the script again."
    exit 1
fi

# Build and deploy
echo "7. Building and deploying..."
heroku container:push web -a $APP_NAME
heroku container:release web -a $APP_NAME

# Show deployment info
echo ""
echo "🎉 Deployment completed!"
echo "========================"
echo "App URL: https://$APP_NAME.herokuapp.com"
echo "Logs: heroku logs --tail -a $APP_NAME"
echo "Health: https://$APP_NAME.herokuapp.com/health"
echo ""

# Show recent logs
echo "Recent logs:"
heroku logs --tail=20 -a $APP_NAME 