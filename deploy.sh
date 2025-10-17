#!/bin/bash

# Deployment Guide for WhatsApp VeEX Bot
# This file contains step-by-step deployment instructions

echo "🚀 WhatsApp VeEX Bot - Deployment Guide"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file from .env.example and configure it."
    exit 1
fi

echo "✅ Found .env file"
echo ""

# Check Python version
PYTHON_VERSION=$(python --version 2>&1)
echo "🐍 Python version: $PYTHON_VERSION"
echo ""

# Option menu
echo "Select deployment option:"
echo "1) Run locally (development)"
echo "2) Deploy to Heroku"
echo "3) Deploy to Railway"
echo "4) Run tests only"
echo "5) Install dependencies only"
echo ""

read -p "Enter option (1-5): " option

case $option in
    1)
        echo "🏃 Running locally..."
        echo ""
        
        # Check if venv exists
        if [ ! -d "venv" ]; then
            echo "Creating virtual environment..."
            python -m venv venv
        fi
        
        # Activate venv
        if [ -f "venv/Scripts/activate" ]; then
            source venv/Scripts/activate
        elif [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        fi
        
        # Install dependencies
        echo "Installing dependencies..."
        pip install -r requirements.txt
        
        # Install Playwright browsers
        echo "Installing Playwright browsers..."
        python -m playwright install chromium
        
        # Run tests
        echo ""
        echo "Running tests..."
        python test_bot.py
        
        # Start server
        echo ""
        echo "Starting Flask server..."
        echo "Server will be available at: http://localhost:8000"
        echo "Health check: http://localhost:8000/health"
        echo ""
        echo "⚠️  Don't forget to run ngrok in another terminal:"
        echo "   ngrok http 8000"
        echo ""
        python main.py
        ;;
    
    2)
        echo "🚢 Deploying to Heroku..."
        echo ""
        
        # Check if heroku CLI is installed
        if ! command -v heroku &> /dev/null; then
            echo "❌ Heroku CLI not found. Please install it first:"
            echo "   https://devcenter.heroku.com/articles/heroku-cli"
            exit 1
        fi
        
        # Login to Heroku
        echo "Logging in to Heroku..."
        heroku login
        
        # Create app or use existing
        read -p "Enter Heroku app name (or press Enter to create new): " app_name
        
        if [ -z "$app_name" ]; then
            echo "Creating new Heroku app..."
            heroku create
        else
            echo "Using app: $app_name"
            heroku git:remote -a $app_name
        fi
        
        # Add buildpacks
        echo "Adding buildpacks..."
        heroku buildpacks:clear
        heroku buildpacks:add heroku/python
        heroku buildpacks:add https://github.com/mxschmitt/heroku-playwright-buildpack
        
        # Set environment variables
        echo "Setting environment variables..."
        source .env
        heroku config:set TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID
        heroku config:set TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN
        heroku config:set TWILIO_WHATSAPP_NUMBER=$TWILIO_WHATSAPP_NUMBER
        heroku config:set VEEX_USERNAME=$VEEX_USERNAME
        heroku config:set VEEX_PASSWORD=$VEEX_PASSWORD
        heroku config:set VEEX_LOGIN_URL=$VEEX_LOGIN_URL
        
        # Deploy
        echo "Deploying to Heroku..."
        git add .
        git commit -m "Deploy WhatsApp VeEX Bot"
        git push heroku main
        
        # Open app
        heroku open
        
        echo ""
        echo "✅ Deployment complete!"
        echo "Don't forget to update Twilio webhook URL to:"
        heroku info -s | grep web_url | cut -d= -f2
        echo "/webhook"
        ;;
    
    3)
        echo "🚂 Deploying to Railway..."
        echo ""
        
        # Check if railway CLI is installed
        if ! command -v railway &> /dev/null; then
            echo "❌ Railway CLI not found. Installing..."
            npm i -g @railway/cli
        fi
        
        # Login to Railway
        echo "Logging in to Railway..."
        railway login
        
        # Link or create project
        echo "Linking to Railway project..."
        railway link
        
        # Set environment variables
        echo "Setting environment variables..."
        source .env
        railway variables set TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID
        railway variables set TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN
        railway variables set TWILIO_WHATSAPP_NUMBER=$TWILIO_WHATSAPP_NUMBER
        railway variables set VEEX_USERNAME=$VEEX_USERNAME
        railway variables set VEEX_PASSWORD=$VEEX_PASSWORD
        railway variables set VEEX_LOGIN_URL=$VEEX_LOGIN_URL
        
        # Deploy
        echo "Deploying to Railway..."
        railway up
        
        echo ""
        echo "✅ Deployment complete!"
        echo "Get your public URL with: railway domain"
        ;;
    
    4)
        echo "🧪 Running tests..."
        echo ""
        
        # Activate venv if exists
        if [ -f "venv/Scripts/activate" ]; then
            source venv/Scripts/activate
        elif [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        fi
        
        python test_bot.py
        ;;
    
    5)
        echo "📦 Installing dependencies..."
        echo ""
        
        # Create venv if doesn't exist
        if [ ! -d "venv" ]; then
            echo "Creating virtual environment..."
            python -m venv venv
        fi
        
        # Activate venv
        if [ -f "venv/Scripts/activate" ]; then
            source venv/Scripts/activate
        elif [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        fi
        
        # Install dependencies
        pip install --upgrade pip
        pip install -r requirements.txt
        
        # Install Playwright browsers
        echo "Installing Playwright browsers..."
        python -m playwright install chromium
        
        echo ""
        echo "✅ Dependencies installed successfully!"
        ;;
    
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac
