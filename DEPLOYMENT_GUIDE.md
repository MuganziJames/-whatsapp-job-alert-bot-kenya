# 🚀 Ajirawise Deployment Guide - Dual Service Blueprint

## 🎯 **Overview**

Deploy both WhatsApp and Telegram bots as separate Render services from a single `render.yaml` blueprint. Each service gets **750 hours/month** (full uptime).

## 📊 **What You'll Get**

- **WhatsApp Service**: `ajirawise-whatsapp-bot` (Web Service) - 750 hours/month
- **Telegram Service**: `ajirawise-telegram-bot` (Background Worker) - 750 hours/month
- **Total Uptime**: 1500 hours/month (both services running 24/7)

---

## 🚀 **Step-by-Step Deployment**

### **Step 1: Push Your Code to GitHub**

```bash
# Add all files
git add .

# Commit changes
git commit -m "Deploy Ajirawise with dual service blueprint"

# Push to GitHub
git push origin main
```

### **Step 2: Deploy Both Services with One Blueprint**

1. **Go to Render Dashboard**

   - Visit [render.com](https://render.com)
   - Click **"New +"** → **"Blueprint"**

2. **Connect Repository**

   - Select your GitHub account
   - Choose your repository: `MuganziJames/-whatsapp-job-alert-bot-kenya`
   - Branch: `master`
   - Click **"Connect"**

3. **Deploy Blueprint**
   - Render will automatically detect `render.yaml`
   - Click **"Apply"**
   - Both services will be created automatically:
     - `ajirawise-whatsapp-bot` (Web Service)
     - `ajirawise-telegram-bot` (Background Worker)

### **Step 3: Set Environment Variables**

You need to set environment variables for **BOTH services**:

#### **For WhatsApp Service (`ajirawise-whatsapp-bot`)**

Go to WhatsApp service → **Environment** tab and add:

```bash
# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# WhatsApp (Twilio)
TWILIO_SID=your-twilio-sid
TWILIO_TOKEN=your-twilio-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# AI Integration
OPENROUTER_API_KEY=your-openrouter-key

# Flask Configuration
PORT=10000
FLASK_ENV=production
FLASK_DEBUG=False
```

#### **For Telegram Service (`ajirawise-telegram-bot`)**

Go to Telegram service → **Environment** tab and add:

```bash
# Database (Supabase) - Same as WhatsApp
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# AI Integration - Same as WhatsApp
OPENROUTER_API_KEY=your-openrouter-key
```

### **Step 4: Configure Webhooks**

#### **WhatsApp (Twilio Setup)**

1. **Get Your Webhook URL**

   - Your WhatsApp service URL: `https://ajirawise-whatsapp-bot.onrender.com`
   - Webhook endpoint: `https://ajirawise-whatsapp-bot.onrender.com/whatsapp`

2. **Configure Twilio**
   - Go to [Twilio Console](https://console.twilio.com)
   - Navigate to **Messaging** → **Settings** → **WhatsApp Sandbox Settings**
   - Set **Webhook URL**: `https://ajirawise-whatsapp-bot.onrender.com/whatsapp`
   - **HTTP Method**: `POST`
   - Click **"Save Configuration"**

#### **Telegram (Automatic)**

- No setup needed - Telegram service uses polling
- Bot will automatically start receiving messages

### **Step 5: Test Your Services**

#### **Test WhatsApp**

1. **Send Test Message**

   - WhatsApp: `+1 415 523 8886`
   - Join code: `join seat-dear`
   - Send: `hi`

2. **Expected Response**

   ```
   🔍 Welcome to Ajirawise - Your Smart Job Assistant!

   Please reply with your job interest:
   • Data Entry - Data input and processing jobs
   • Sales & Marketing - Sales, marketing, and business development
   ...
   ```

#### **Test Telegram**

1. **Find Your Bot**

   - Search for your bot username in Telegram
   - Send: `/start`

2. **Expected Response**

   ```
   🔍 Welcome to Ajirawise - Your Smart Job Assistant!

   Please reply with your job interest:
   • Data Entry - Data input and processing jobs
   • Sales & Marketing - Sales, marketing, and business development
   ...
   ```

---

## 🔍 **Monitoring Your Services**

### **Health Checks**

- **WhatsApp**: `https://ajirawise-whatsapp-bot.onrender.com/health`
- **Telegram**: Check logs in Render dashboard

### **Service Status**

- **Render Dashboard**: Monitor both services
- **Logs**: View real-time logs for debugging
- **Metrics**: Track resource usage

### **Expected Logs**

```
# WhatsApp Service
INFO:app:Starting Ajirawise - Smart Job Alert Bot on port 10000
INFO:werkzeug:Running on http://0.0.0.0:10000

# Telegram Service
INFO:telegram_bot:Starting Ajirawise Telegram Bot …
INFO:telegram_bot:Starting polling...
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **Blueprint Deployment Failed**

   - Check that `render.yaml` exists in your repository
   - Verify the YAML syntax is correct
   - Check build logs for specific errors

2. **Environment Variables**

   - Make sure to set variables for BOTH services
   - WhatsApp service needs Twilio credentials
   - Telegram service needs bot token
   - Both need Supabase and OpenRouter keys

3. **WhatsApp Not Responding**

   - Verify Twilio webhook URL is correct
   - Check if service is sleeping (send a message to wake it)
   - Verify Twilio credentials

4. **Telegram Not Responding**
   - Check Telegram bot token is correct
   - Verify service is running (check logs)
   - Ensure bot is not blocked

### **Useful Commands**

```bash
# Check service health
curl https://ajirawise-whatsapp-bot.onrender.com/health

# View service logs
# (Use Render dashboard)

# Restart services
# (Use Render dashboard - "Manual Deploy")
```

---

## 🎉 **Success Checklist**

✅ **GitHub**: Code pushed with `render.yaml`  
✅ **Blueprint**: Deployed successfully  
✅ **WhatsApp Service**: Running and responding  
✅ **Telegram Service**: Running and responding  
✅ **Environment Variables**: Set for both services  
✅ **Webhooks**: Twilio configured correctly  
✅ **Database**: Supabase connected  
✅ **Health Checks**: Both services healthy  
✅ **Testing**: Both platforms working

---

## 📞 **Support**

If you encounter issues:

1. Check service logs in Render dashboard
2. Verify all environment variables are set for both services
3. Test health endpoints
4. Check Twilio webhook configuration

**🎉 Congratulations! Ajirawise is now live on both WhatsApp and Telegram with maximum uptime!**
