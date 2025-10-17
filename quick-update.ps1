# 🔄 Quick Update Script
# Run this after changing .env or code to auto-deploy

Write-Host "🔄 Quick Update & Deploy" -ForegroundColor Cyan
Write-Host "=======================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "❌ Git not initialized. Run auto-deploy.ps1 first!" -ForegroundColor Red
    exit 1
}

# Show what changed
Write-Host "📝 Changes detected:" -ForegroundColor Yellow
git status --short
Write-Host ""

# Get commit message
$message = Read-Host "Enter commit message (or press Enter for 'Quick update')"
if ([string]::IsNullOrWhiteSpace($message)) {
    $message = "Quick update - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}

# Commit and push
Write-Host ""
Write-Host "📦 Committing changes..." -ForegroundColor Yellow
git add .
git commit -m $message

Write-Host "📤 Pushing to GitHub..." -ForegroundColor Yellow
git push origin main

Write-Host ""
Write-Host "✅ Pushed to GitHub successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "⏳ Your hosting platform will auto-deploy in 3-5 minutes..." -ForegroundColor Cyan
Write-Host ""

# Show platform-specific update instructions
Write-Host "🔐 If you changed .env values:" -ForegroundColor Yellow
Write-Host ""
Write-Host "📌 Render.com:" -ForegroundColor Cyan
Write-Host "   1. Go to https://dashboard.render.com/" -ForegroundColor White
Write-Host "   2. Select your service" -ForegroundColor White
Write-Host "   3. Click 'Environment' tab" -ForegroundColor White
Write-Host "   4. Update variables" -ForegroundColor White
Write-Host "   5. Click 'Save Changes'" -ForegroundColor White
Write-Host "   → Auto-restarts in ~30 seconds" -ForegroundColor Gray
Write-Host ""
Write-Host "📌 Railway.app:" -ForegroundColor Cyan
Write-Host "   1. Go to https://railway.app/dashboard" -ForegroundColor White
Write-Host "   2. Select your project" -ForegroundColor White
Write-Host "   3. Click 'Variables' tab" -ForegroundColor White
Write-Host "   4. Update variables" -ForegroundColor White
Write-Host "   → Auto-restarts immediately" -ForegroundColor Gray
Write-Host ""
Write-Host "📌 Heroku:" -ForegroundColor Cyan
Write-Host "   Run: heroku config:set VARIABLE_NAME=value -a your-app-name" -ForegroundColor White
Write-Host "   → Auto-restarts immediately" -ForegroundColor Gray
Write-Host ""

$openDashboard = Read-Host "Open platform dashboard in browser? (y/n)"
Write-Host ""
Write-Host "Which platform? (1=Render, 2=Railway, 3=Heroku, 4=None)" -ForegroundColor Yellow
$platform = Read-Host "Choice"

if ($openDashboard -eq "y") {
    switch ($platform) {
        "1" { Start-Process "https://dashboard.render.com/" }
        "2" { Start-Process "https://railway.app/dashboard" }
        "3" { Start-Process "https://dashboard.heroku.com/apps" }
    }
}

Write-Host ""
Write-Host "✨ Update complete! Bot will restart with new changes soon." -ForegroundColor Green
Write-Host ""
