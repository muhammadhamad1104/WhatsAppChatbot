# PowerShell Deployment Script for WhatsApp VeEX Bot
# Run this with: .\deploy.ps1

Write-Host "🚀 WhatsApp VeEX Bot - Deployment Guide" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Host "❌ Error: .env file not found!" -ForegroundColor Red
    Write-Host "Please create .env file from .env.example and configure it." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found .env file" -ForegroundColor Green
Write-Host ""

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "🐍 Python version: $pythonVersion" -ForegroundColor Cyan
Write-Host ""

# Option menu
Write-Host "Select deployment option:" -ForegroundColor Yellow
Write-Host "1) Run locally (development)"
Write-Host "2) Deploy to Heroku"
Write-Host "3) Deploy to Railway"
Write-Host "4) Run tests only"
Write-Host "5) Install dependencies only"
Write-Host ""

$option = Read-Host "Enter option (1-5)"

switch ($option) {
    "1" {
        Write-Host "🏃 Running locally..." -ForegroundColor Cyan
        Write-Host ""
        
        # Check if venv exists
        if (-not (Test-Path venv)) {
            Write-Host "Creating virtual environment..." -ForegroundColor Yellow
            python -m venv venv
        }
        
        # Activate venv
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        .\venv\Scripts\Activate.ps1
        
        # Install dependencies
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        pip install -r requirements.txt
        
        # Install Playwright browsers
        Write-Host "Installing Playwright browsers..." -ForegroundColor Yellow
        python -m playwright install chromium
        
        # Run tests
        Write-Host ""
        Write-Host "Running tests..." -ForegroundColor Yellow
        python test_bot.py
        
        # Start server
        Write-Host ""
        Write-Host "Starting Flask server..." -ForegroundColor Green
        Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "Health check: http://localhost:8000/health" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "⚠️  Don't forget to run ngrok in another terminal:" -ForegroundColor Yellow
        Write-Host "   ngrok http 8000" -ForegroundColor White
        Write-Host ""
        python main.py
    }
    
    "2" {
        Write-Host "🚢 Deploying to Heroku..." -ForegroundColor Cyan
        Write-Host ""
        
        # Check if heroku CLI is installed
        $herokuInstalled = Get-Command heroku -ErrorAction SilentlyContinue
        if (-not $herokuInstalled) {
            Write-Host "❌ Heroku CLI not found. Please install it first:" -ForegroundColor Red
            Write-Host "   https://devcenter.heroku.com/articles/heroku-cli" -ForegroundColor Yellow
            exit 1
        }
        
        # Login to Heroku
        Write-Host "Logging in to Heroku..." -ForegroundColor Yellow
        heroku login
        
        # Create app or use existing
        $appName = Read-Host "Enter Heroku app name (or press Enter to create new)"
        
        if ([string]::IsNullOrWhiteSpace($appName)) {
            Write-Host "Creating new Heroku app..." -ForegroundColor Yellow
            heroku create
        } else {
            Write-Host "Using app: $appName" -ForegroundColor Yellow
            heroku git:remote -a $appName
        }
        
        # Add buildpacks
        Write-Host "Adding buildpacks..." -ForegroundColor Yellow
        heroku buildpacks:clear
        heroku buildpacks:add heroku/python
        heroku buildpacks:add https://github.com/mxschmitt/heroku-playwright-buildpack
        
        # Load .env and set variables
        Write-Host "Setting environment variables..." -ForegroundColor Yellow
        Get-Content .env | ForEach-Object {
            if ($_ -match '^([^=]+)=(.*)$') {
                $key = $matches[1]
                $value = $matches[2].Trim('"').Trim("'")
                heroku config:set "${key}=${value}"
            }
        }
        
        # Deploy
        Write-Host "Deploying to Heroku..." -ForegroundColor Yellow
        git add .
        git commit -m "Deploy WhatsApp VeEX Bot"
        git push heroku main
        
        # Get app URL
        $appUrl = heroku info -s | Select-String "web_url" | ForEach-Object { $_.ToString().Split('=')[1] }
        
        Write-Host ""
        Write-Host "✅ Deployment complete!" -ForegroundColor Green
        Write-Host "Don't forget to update Twilio webhook URL to:" -ForegroundColor Yellow
        Write-Host "$appUrl/webhook" -ForegroundColor Cyan
    }
    
    "3" {
        Write-Host "🚂 Deploying to Railway..." -ForegroundColor Cyan
        Write-Host ""
        
        # Check if railway CLI is installed
        $railwayInstalled = Get-Command railway -ErrorAction SilentlyContinue
        if (-not $railwayInstalled) {
            Write-Host "❌ Railway CLI not found. Installing via npm..." -ForegroundColor Red
            npm i -g @railway/cli
        }
        
        # Login to Railway
        Write-Host "Logging in to Railway..." -ForegroundColor Yellow
        railway login
        
        # Link or create project
        Write-Host "Linking to Railway project..." -ForegroundColor Yellow
        railway link
        
        # Set environment variables
        Write-Host "Setting environment variables..." -ForegroundColor Yellow
        Get-Content .env | ForEach-Object {
            if ($_ -match '^([^=]+)=(.*)$') {
                $key = $matches[1]
                $value = $matches[2].Trim('"').Trim("'")
                railway variables set "${key}=${value}"
            }
        }
        
        # Deploy
        Write-Host "Deploying to Railway..." -ForegroundColor Yellow
        railway up
        
        Write-Host ""
        Write-Host "✅ Deployment complete!" -ForegroundColor Green
        Write-Host "Get your public URL with: railway domain" -ForegroundColor Yellow
    }
    
    "4" {
        Write-Host "🧪 Running tests..." -ForegroundColor Cyan
        Write-Host ""
        
        # Activate venv if exists
        if (Test-Path venv\Scripts\Activate.ps1) {
            .\venv\Scripts\Activate.ps1
        }
        
        python test_bot.py
    }
    
    "5" {
        Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
        Write-Host ""
        
        # Create venv if doesn't exist
        if (-not (Test-Path venv)) {
            Write-Host "Creating virtual environment..." -ForegroundColor Yellow
            python -m venv venv
        }
        
        # Activate venv
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        .\venv\Scripts\Activate.ps1
        
        # Install dependencies
        Write-Host "Upgrading pip..." -ForegroundColor Yellow
        python -m pip install --upgrade pip
        
        Write-Host "Installing requirements..." -ForegroundColor Yellow
        pip install -r requirements.txt
        
        # Install Playwright browsers
        Write-Host "Installing Playwright browsers..." -ForegroundColor Yellow
        python -m playwright install chromium
        
        Write-Host ""
        Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
    }
    
    default {
        Write-Host "❌ Invalid option" -ForegroundColor Red
        exit 1
    }
}
