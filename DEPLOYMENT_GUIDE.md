# 🚀 24/7 Deployment Guide

This bot is currently working locally. To make it run **24/7 automatically** with auto-deployment on changes, follow one of these options:

---

## ⚡ Option 1: Render.com (RECOMMENDED - Free & Easy)

### Why Render?
- ✅ **FREE** for web services
- ✅ **Auto-deploys** from GitHub on every push
- ✅ **24/7 uptime**
- ✅ **Easy environment variable management**
- ✅ **Supports Playwright** out of the box

### Setup Steps:

#### 1. Push to GitHub

```powershell
cd "d:\ALL SEMESTER\WhatsAppChatbot"

# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit - WhatsApp VeEX Bot"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/whatsapp-veex-bot.git
git branch -M main
git push -u origin main
```

#### 2. Deploy to Render

1. Go to https://render.com/ and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `whatsapp-veex-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python -m playwright install chromium --with-deps`
   - **Start Command**: `python main.py`
   - **Instance Type**: `Free`

5. **Add Environment Variables** (click "Environment" tab):
   Copy values from your local `.env` file:
   ```
   TWILIO_ACCOUNT_SID=your_account_sid_here
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   VEEX_USERNAME=your_veex_username
   VEEX_PASSWORD=your_veex_password
   VEEX_LOGIN_URL=https://charter.veexinc.net/
   DEBUG_MODE=false
   PORT=8000
   ```

6. Click **"Create Web Service"**

7. Wait 5-10 minutes for deployment

8. Copy your Render URL: `https://whatsapp-veex-bot.onrender.com`

9. **Update Twilio Webhook**:
   - Go to https://console.twilio.com/
   - Navigate to **Messaging** → **WhatsApp Sandbox Settings**
   - Set webhook to: `https://whatsapp-veex-bot.onrender.com/webhook`
   - Click **Save**

#### 3. Auto-Deploy on Changes

✅ **Automatic!** Every time you push to GitHub, Render auto-deploys!

To update `.env` values:
1. Go to Render dashboard → Your service
2. Click **"Environment"** tab
3. Update any variable
4. Click **"Save Changes"**
5. Render will **automatically restart** with new values! 🎉

---

## 🔷 Option 2: Railway.app (Also Great)

### Why Railway?
- ✅ **$5 free credit** (enough for ~1 month)
- ✅ **Auto-deploys** from GitHub
- ✅ **Simple environment variable management**
- ✅ **Faster than Render**

### Setup Steps:

1. **Push to GitHub** (same as Option 1)

2. Go to https://railway.app/ and sign up

3. Click **"New Project"** → **"Deploy from GitHub repo"**

4. Select your repository

5. Railway will auto-detect Python and deploy

6. **Add Environment Variables**:
   - Click on your service
   - Go to **"Variables"** tab
   - Add all variables from `.env` (copy your actual values):
     ```
     TWILIO_ACCOUNT_SID=your_account_sid_here
     TWILIO_AUTH_TOKEN=your_auth_token_here
     TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
     VEEX_USERNAME=your_veex_username
     VEEX_PASSWORD=your_veex_password
     VEEX_LOGIN_URL=https://charter.veexinc.net/
     DEBUG_MODE=false
     PORT=8000
     ```

7. Go to **"Settings"** tab
   - Add custom build command: `pip install -r requirements.txt && python -m playwright install chromium --with-deps`
   - Add start command: `python main.py`

8. Click **"Deploy"**

9. Copy your Railway URL (under "Deployments")

10. **Update Twilio Webhook** with Railway URL

#### Auto-Deploy:
✅ Every GitHub push = Auto-deploy
✅ Change environment variables in Railway dashboard = Auto-restart

---

## 🟣 Option 3: Heroku (Paid but Reliable)

**Note**: Heroku no longer has a free tier, but very reliable for production.

### Setup:

```powershell
# Install Heroku CLI
# Download from: https://devcenter.heroku.com/articles/heroku-cli

heroku login
heroku create whatsapp-veex-bot

# Add buildpacks
heroku buildpacks:add heroku/python
heroku buildpacks:add https://github.com/mxschmitt/heroku-playwright-buildpack

# Set environment variables (use your actual values from .env)
heroku config:set TWILIO_ACCOUNT_SID=your_account_sid_here
heroku config:set TWILIO_AUTH_TOKEN=your_auth_token_here
heroku config:set TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
heroku config:set VEEX_USERNAME=your_veex_username
heroku config:set VEEX_PASSWORD=your_veex_password
heroku config:set VEEX_LOGIN_URL=https://charter.veexinc.net/
heroku config:set DEBUG_MODE=false

# Deploy
git push heroku main

# Get URL
heroku open
```

Update Twilio webhook with Heroku URL.

#### Auto-Deploy:
- **Option A**: Enable GitHub auto-deploy in Heroku dashboard
- **Option B**: Push to Heroku: `git push heroku main`

To update environment variables:
```powershell
heroku config:set VARIABLE_NAME=new_value
```

---

## 🐳 Option 4: Docker + Any Cloud (Advanced)

I can create Docker setup if you prefer AWS, Google Cloud, DigitalOcean, etc.

---

## 📊 Comparison Table

| Feature | Render | Railway | Heroku |
|---------|--------|---------|--------|
| **Price** | FREE ✅ | $5 credit | Paid |
| **Auto-Deploy** | ✅ | ✅ | ✅ |
| **Playwright Support** | ✅ | ✅ | ✅ |
| **Setup Difficulty** | Easy | Easy | Medium |
| **Speed** | Medium | Fast | Fast |
| **Best For** | Free forever | Quick testing | Production |

---

## 🎯 Recommended Workflow

### For Development/Testing → Use Render (Free)

1. Push code to GitHub
2. Deploy to Render
3. Update env vars in Render dashboard
4. Auto-deploys on every push

### For Production/Client → Use Railway or Heroku

- More reliable uptime
- Faster response times
- Better monitoring

---

## 🔄 How Auto-Deployment Works

```
You change .env or code
        ↓
Push to GitHub (git push origin main)
        ↓
Render/Railway detects change
        ↓
Automatically rebuilds & redeploys
        ↓
Bot restarts with new configuration
        ↓
✅ Running 24/7 with new settings!
```

**Time from push to live: 3-5 minutes**

---

## 🛠️ Local Development → Production Workflow

### 1. Make Changes Locally

```powershell
# Edit .env or code files
# Test locally
python main.py
```

### 2. Commit & Push

```powershell
git add .
git commit -m "Updated configuration"
git push origin main
```

### 3. Wait for Auto-Deploy
- Render/Railway automatically detects the push
- Rebuilds and redeploys (3-5 minutes)
- Bot restarts with new code/config

### 4. Update Environment Variables (Without Code Push)

**Render:**
- Dashboard → Environment → Edit → Save
- Auto-restarts in ~30 seconds

**Railway:**
- Dashboard → Variables → Edit
- Auto-restarts immediately

**Heroku:**
```powershell
heroku config:set VARIABLE_NAME=new_value
```
Auto-restarts immediately

---

## 🚨 Important Notes

### 1. Remove `.env` from GitHub

Your `.gitignore` already includes `.env`, but verify:

```powershell
cat .gitignore | Select-String ".env"
```

Should show `.env` is ignored. ✅

### 2. Never Commit Credentials

Always use environment variables in production:
- ✅ Render dashboard
- ✅ Railway dashboard  
- ✅ Heroku config
- ❌ Never in `.env` pushed to GitHub

### 3. Update Twilio Webhook

After deployment, MUST update Twilio webhook to production URL:
```
https://your-service.render.com/webhook
```

### 4. Test Health Endpoint

```powershell
curl https://your-service.render.com/health
```

Should return: `{"status": "healthy"}`

---

## 🎉 Next Steps

1. **Choose a platform** (I recommend Render for free 24/7)
2. **Push to GitHub**
3. **Deploy to platform**
4. **Update Twilio webhook**
5. **Test with WhatsApp**
6. **Done! Bot runs 24/7 automatically!** 🚀

---

**Need help with deployment? Let me know which platform you choose and I'll guide you through it step-by-step!**
