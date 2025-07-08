#!/bin/bash

echo "🚀 Deploying Crypto Helper Bot from testing branch..."

# Commit current changes
git add .
git commit -m "Add internal keep-alive mechanism to prevent sleeping"

# Push testing branch to heroku main
echo "📤 Pushing testing branch to Heroku..."
git push heroku testing:main

# Check deployment status
echo "📊 Checking deployment status..."
heroku ps -a crypto-helper-testing

# Test health endpoint
echo "🏥 Testing health endpoint..."
sleep 10
curl -s https://crypto-helper-testing-7c5ffa6d9fbf.herokuapp.com/health/live | jq .

echo "✅ Deployment complete!"
echo "🔗 Bot URL: https://crypto-helper-testing-7c5ffa6d9fbf.herokuapp.com"
echo "📋 Monitor logs: heroku logs --tail -a crypto-helper-testing" 