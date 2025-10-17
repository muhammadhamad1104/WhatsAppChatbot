# WhatsApp VeEX Bot - Automated Deployment Script
# This script automates the entire deployment process

Write-Host "=================================" -ForegroundColor Cyan
Write-Host "WhatsApp VeEX Bot Deployment" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-CommandExists {
    param([string]$Command)
    $exists = $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
    return $exists
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Test-CommandExists "git")) {
    Write-Host "ERROR: Git not found!" -ForegroundColor Red
    Write-Host "Install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}
Write-Host "SUCCESS: Git is installed" -ForegroundColor Green

# Initialize git if needed
if (-not (Test-Path ".git")) {
    Write-Host ""
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit - WhatsApp VeEX Bot ready for deployment"
    Write-Host "SUCCESS: Git repository initialized" -ForegroundColor Green
}

# Check for remote
$remoteCheck = git remote -v 2>$null
$hasRemote = $remoteCheck -match "origin"

if (-not $hasRemote) {
    Write-Host ""
    Write-Host "No GitHub repository connected." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To connect GitHub:" -ForegroundColor Cyan
    Write-Host "1. Create a new repository on GitHub" -ForegroundColor White
    Write-Host "2. Run: git remote add origin YOUR_GITHUB_URL" -ForegroundColor White
    Write-Host "3. Run: git branch -M main" -ForegroundColor White
    Write-Host "4. Run: git push -u origin main" -ForegroundColor White
    Write-Host ""
    
    $addRemote = Read-Host "Do you want to add GitHub remote now? (y/n)"
    if ($addRemote -eq "y" -or $addRemote -eq "Y") {
        $repoUrl = Read-Host "Enter your GitHub repository URL"
        if ($repoUrl) {
            git remote add origin $repoUrl
            git branch -M main
            Write-Host "SUCCESS: Remote added. Pushing to GitHub..." -ForegroundColor Green
            git push -u origin main
        }
    }
    else {
        Write-Host "WARNING: Skipping GitHub setup." -ForegroundColor Yellow
    }
}
else {
    Write-Host "SUCCESS: GitHub repository is connected" -ForegroundColor Green
}

# Show deployment options
Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "Choose Deployment Platform:" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "1. Render.com (FREE, Auto-deploy, Recommended)" -ForegroundColor White
Write-Host "2. Railway.app (Dollar 5 credit, Fast)" -ForegroundColor White
Write-Host "3. Heroku (Paid, Reliable)" -ForegroundColor White
Write-Host "4. Manual GitHub push only" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "=== Render.com Deployment ===" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "SUCCESS: render.yaml configuration file is ready!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Go to https://render.com/ and sign up/login" -ForegroundColor White
        Write-Host "2. Click 'New +' then 'Web Service'" -ForegroundColor White
        Write-Host "3. Connect your GitHub repository" -ForegroundColor White
        Write-Host "4. Render will auto-detect render.yaml" -ForegroundColor White
        Write-Host "5. Add environment variables in dashboard:" -ForegroundColor White
        Write-Host "   - TWILIO_ACCOUNT_SID" -ForegroundColor Gray
        Write-Host "   - TWILIO_AUTH_TOKEN" -ForegroundColor Gray
        Write-Host "   - TWILIO_WHATSAPP_NUMBER" -ForegroundColor Gray
        Write-Host "   - VEEX_USERNAME" -ForegroundColor Gray
        Write-Host "   - VEEX_PASSWORD" -ForegroundColor Gray
        Write-Host "   - VEEX_LOGIN_URL" -ForegroundColor Gray
        Write-Host "6. Click 'Create Web Service'" -ForegroundColor White
        Write-Host "7. Wait 5-10 minutes for deployment" -ForegroundColor White
        Write-Host "8. Update Twilio webhook with your Render URL" -ForegroundColor White
        Write-Host ""
        Write-Host "Full guide: See DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
    }
    "2" {
        Write-Host ""
        Write-Host "=== Railway.app Deployment ===" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Go to https://railway.app/ and sign up" -ForegroundColor White
        Write-Host "2. Click 'New Project' then 'Deploy from GitHub repo'" -ForegroundColor White
        Write-Host "3. Select your repository" -ForegroundColor White
        Write-Host "4. Add environment variables in Variables tab" -ForegroundColor White
        Write-Host "5. Railway will auto-deploy!" -ForegroundColor White
        Write-Host ""
        Write-Host "Full guide: See DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
    }
    "3" {
        Write-Host ""
        Write-Host "=== Heroku Deployment ===" -ForegroundColor Cyan
        Write-Host ""
        
        if (-not (Test-CommandExists "heroku")) {
            Write-Host "ERROR: Heroku CLI not found!" -ForegroundColor Red
            Write-Host "Install from: https://devcenter.heroku.com/articles/heroku-cli" -ForegroundColor Yellow
            exit 1
        }
        
        Write-Host "SUCCESS: Heroku CLI found" -ForegroundColor Green
        Write-Host ""
        
        $appName = Read-Host "Enter your Heroku app name"
        
        if ($appName) {
            Write-Host ""
            Write-Host "Creating Heroku app..." -ForegroundColor Yellow
            heroku create $appName
            
            Write-Host "Adding buildpacks..." -ForegroundColor Yellow
            heroku buildpacks:add heroku/python -a $appName
            heroku buildpacks:add https://github.com/mxschmitt/heroku-playwright-buildpack -a $appName
            
            Write-Host ""
            Write-Host "Setting environment variables..." -ForegroundColor Yellow
            
            if (Test-Path ".env") {
                Get-Content .env | ForEach-Object {
                    $line = $_.Trim()
                    if ($line -and -not $line.StartsWith("#")) {
                        $parts = $line.Split("=", 2)
                        if ($parts.Count -eq 2) {
                            $key = $parts[0].Trim()
                            $value = $parts[1].Trim()
                            Write-Host "Setting $key..." -ForegroundColor Gray
                            heroku config:set "${key}=${value}" -a $appName
                        }
                    }
                }
            }
            
            Write-Host ""
            Write-Host "Deploying to Heroku..." -ForegroundColor Yellow
            git push heroku main
            
            Write-Host ""
            Write-Host "SUCCESS: Deployment complete!" -ForegroundColor Green
            $appInfo = heroku apps:info -a $appName
            Write-Host "Your app info:" -ForegroundColor Cyan
            Write-Host $appInfo
            Write-Host ""
            Write-Host "WARNING: Update Twilio webhook with your Heroku URL!" -ForegroundColor Yellow
        }
    }
    "4" {
        Write-Host ""
        Write-Host "=== Manual GitHub Push ===" -ForegroundColor Cyan
        Write-Host ""
        
        $commitMsg = Read-Host "Enter commit message (or press Enter for default)"
        if (-not $commitMsg) {
            $commitMsg = "Update bot for deployment"
        }
        
        Write-Host ""
        Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
        git add .
        git commit -m $commitMsg
        git push origin main
        
        Write-Host ""
        Write-Host "SUCCESS: Pushed to GitHub!" -ForegroundColor Green
        Write-Host "Deploy manually from your chosen platform dashboard." -ForegroundColor Yellow
    }
    default {
        Write-Host "ERROR: Invalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "Deployment Process Complete!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Wait for deployment to complete (3-10 minutes)" -ForegroundColor White
Write-Host "2. Copy your production URL" -ForegroundColor White
Write-Host "3. Update Twilio webhook: https://console.twilio.com/" -ForegroundColor White
Write-Host "4. Set webhook to: YOUR_URL/webhook" -ForegroundColor White
Write-Host "5. Test with WhatsApp!" -ForegroundColor White
Write-Host ""
Write-Host "Your bot will run 24/7 automatically!" -ForegroundColor Green
Write-Host ""
Write-Host "For detailed instructions, see: DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
Write-Host ""

$openBrowser = Read-Host "Open Twilio console in browser? (y/n)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    Start-Process "https://console.twilio.com/"
}

Write-Host ""
Write-Host "All done! Bot is ready for 24/7 operation!" -ForegroundColor Green
Write-Host ""
