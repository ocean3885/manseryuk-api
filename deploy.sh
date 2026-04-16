#!/bin/bash

# =================================================================
# Manseryuk API Auto-Deployment Script
# =================================================================

# 1. Configuration
SERVER_USER="root"
SERVER_IP="1.234.44.174"
SERVER_PATH="/var/www/manseryuk-api"
PM2_NAME="bazi-api"
BRANCH="main"

echo "--------------------------------------------------------"
echo "🚀 Starting Deployment: $SERVER_IP"
echo "--------------------------------------------------------"

# 2. Remote execution via SSH
ssh -t $SERVER_USER@$SERVER_IP << EOF
  echo "📂 Navigating to project directory..."
  cd $SERVER_PATH || { echo "❌ Failed to change directory to $SERVER_PATH"; exit 1; }

  echo "📥 Fetching latest code from Git ($BRANCH)..."
  # Fetch and reset to ensure a clean state from origin
  git fetch origin
  git reset --hard origin/$BRANCH

  echo "📦 Updating Python dependencies..."
  if [ -d "venv" ]; then
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
  else
    echo "⚠️  venv directory not found. Skipping pip install."
  fi

  echo "🔄 Restarting application with PM2..."
  # Check if PM2 is running the app, if not start it, otherwise restart
  if pm2 show $PM2_NAME > /dev/null 2>&1; then
    pm2 restart $PM2_NAME --update-env
  else
    echo "⚠️  $PM2_NAME not found in PM2 list. Starting it using ecosystem.config.js..."
    pm2 start ecosystem.config.js
  fi

  echo "--------------------------------------------------------"
  echo "✅ Deployment Process Completed Successfully!"
  echo "--------------------------------------------------------"
EOF

if [ $? -eq 0 ]; then
  echo "🌟 All steps finished!"
else
  echo "❌ Deployment failed. Please check the error messages above."
  exit 1
fi
