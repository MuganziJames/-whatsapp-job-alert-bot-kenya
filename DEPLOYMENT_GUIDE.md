# 🚀 Ajirawise Deployment Guide - Same Repo, Separate Services

## 🎯 **Overview**

Deploy both WhatsApp and Telegram bots as separate Render services from the same GitHub repository. Each service gets **750 hours/month** (full uptime).

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
git commit -m "Deploy Ajirawise as separate services"

# Push to GitHub
git push origin main
```

### **Step 2: Deploy WhatsApp Service**

1. **Go to Render Dashboard**

   - Visit [render.com](https://render.com)
   - Click **"New +"** → **"Blueprint"**

2. **Connect Repository**

   - Select your GitHub account
   - Choose your repository: `vibeCoding`
   - Click **"Connect"**

3. **Configure Blueprint**

   - **Blueprint Name**: `Ajirawise WhatsApp Service`
   - **Blueprint File**: `whatsapp-render.yaml`
   - Click **"Apply"**

4. **Set Environment Variables**
   Go to the created service → **Environment** tab and add:

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

5. **Deploy**
   - Click **"Create Web Service"**
   - Wait for deployment to complete
   - Note your service URL: `https://ajirawise-whatsapp-bot.onrender.com`

### **Step 3: Deploy Telegram Service**

1. **Create Second Service**

   - Click **"New +"** → **"Blueprint"** again
   - Connect the **same** repository: `vibeCoding`

2. **Configure Blueprint**

   - **Blueprint Name**: `Ajirawise Telegram Service`
   - **Blueprint File**: `telegram-render.yaml`
   - Click **"Apply"**

3. **Set Environment Variables**
   Go to the created service → **Environment** tab and add:

   ```bash
   # Database (Supabase) - Same as WhatsApp
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key

   # Telegram Bot
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token

   # AI Integration - Same as WhatsApp
   OPENROUTER_API_KEY=your-openrouter-key
   ```

4. **Deploy**
   - Click **"Create Background Worker"**
   - Wait for deployment to complete

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

1. **Service Won't Start**

   - Check environment variables are set correctly
   - Verify blueprint file path is correct
   - Check logs for specific error messages

2. **WhatsApp Not Responding**

   - Verify Twilio webhook URL is correct
   - Check if service is sleeping (send a message to wake it)
   - Verify Twilio credentials

3. **Telegram Not Responding**

   - Check Telegram bot token is correct
   - Verify service is running (check logs)
   - Ensure bot is not blocked

4. **Database Errors**
   - Verify Supabase URL and key
   - Check if database tables exist
   - Test database connection

### **Useful Commands**

```bash
# Check service health
curl https://ajirawise-whatsapp-bot.onrender.com/health

# View service logs
# (Use Render dashboard)

# Restart service
# (Use Render dashboard - "Manual Deploy")
```

---

## 🎉 **Success Checklist**

✅ **GitHub**: Code pushed successfully  
✅ **WhatsApp Service**: Deployed and responding  
✅ **Telegram Service**: Deployed and responding  
✅ **Webhooks**: Twilio configured correctly  
✅ **Database**: Supabase connected  
✅ **Health Checks**: Both services healthy  
✅ **Testing**: Both platforms working

---

## 📞 **Support**

If you encounter issues:

1. Check service logs in Render dashboard
2. Verify all environment variables
3. Test health endpoints
4. Check Twilio webhook configuration

**🎉 Congratulations! Ajirawise is now live on both WhatsApp and Telegram with maximum uptime!**
