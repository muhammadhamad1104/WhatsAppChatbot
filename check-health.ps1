# 📊 Bot Health Monitor
# Check if your bot is running properly

param(
    [string]$Url = ""
)

Write-Host "📊 WhatsApp VeEX Bot - Health Monitor" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

if ([string]::IsNullOrWhiteSpace($Url)) {
    $Url = Read-Host "Enter your bot URL (e.g., https://your-app.onrender.com)"
}

# Remove trailing slash
$Url = $Url.TrimEnd('/')

Write-Host "🔍 Checking bot status..." -ForegroundColor Yellow
Write-Host ""

# Function to test endpoint
function Test-Endpoint {
    param($Endpoint, $Name)
    
    try {
        $response = Invoke-WebRequest -Uri $Endpoint -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $Name is responding (Status: 200)" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "⚠️ $Name returned status: $($response.StatusCode)" -ForegroundColor Yellow
            return $false
        }
    }
    catch {
        Write-Host "❌ $Name is not responding" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
        return $false
    }
}

# Test health endpoint
$healthOk = Test-Endpoint "$Url/health" "Health Check"
Write-Host ""

# Test webhook endpoint (should return 405 for GET)
try {
    $webhookResponse = Invoke-WebRequest -Uri "$Url/webhook" -UseBasicParsing -ErrorAction SilentlyContinue
}
catch {
    if ($_.Exception.Response.StatusCode -eq 405) {
        Write-Host "✅ Webhook endpoint exists (expects POST)" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️ Webhook might not be configured properly" -ForegroundColor Yellow
    }
}
Write-Host ""

# Overall status
Write-Host "==========================================" -ForegroundColor Cyan
if ($healthOk) {
    Write-Host "✅ Bot is HEALTHY and running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📱 Twilio Webhook URL:" -ForegroundColor Cyan
    Write-Host "   $Url/webhook" -ForegroundColor White
    Write-Host ""
    Write-Host "⚙️ Make sure this is set in Twilio console:" -ForegroundColor Yellow
    Write-Host "   https://console.twilio.com/" -ForegroundColor White
}
else {
    Write-Host "❌ Bot has issues!" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check if deployment completed successfully" -ForegroundColor White
    Write-Host "2. Check platform logs for errors" -ForegroundColor White
    Write-Host "3. Verify all environment variables are set" -ForegroundColor White
    Write-Host "4. Ensure port is set to 8000" -ForegroundColor White
}
Write-Host ""

# Show how to check logs
Write-Host "📋 To view logs:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Render.com:" -ForegroundColor Yellow
Write-Host "  Dashboard → Your Service → Logs tab" -ForegroundColor White
Write-Host ""
Write-Host "Railway.app:" -ForegroundColor Yellow
Write-Host "  Dashboard → Your Project → View Logs" -ForegroundColor White
Write-Host ""
Write-Host "Heroku:" -ForegroundColor Yellow
Write-Host "  heroku logs --tail -a your-app-name" -ForegroundColor White
Write-Host ""

$openConsole = Read-Host "Open Twilio console to check webhook? (y/n)"
if ($openConsole -eq "y") {
    Start-Process "https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox"
}

Write-Host ""
Write-Host "✨ Monitoring complete!" -ForegroundColor Green
