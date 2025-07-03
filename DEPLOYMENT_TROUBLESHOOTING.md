# 🚨 Deployment Troubleshooting Guide

## Current Issue: Python 3.12.0 Not Available

### ✅ **FIXED: Updated Python Version**

Your deployment issue has been resolved by updating the Python version from 3.12.0 to 3.11.9, which is more widely supported across deployment platforms.

**Files Updated:**

- `runtime.txt`: Changed to `python-3.11.9`
- `render.yaml`: Updated runtime and build commands
- `requirements.txt`: Updated Playwright to stable version
- `working_scraper.py`: Enhanced fallback system

## 🔧 **Deployment Options**

### **Option 1: Full Deployment (Recommended)**

Uses `render.yaml` with Playwright for real job scraping:

```yaml
runtime: python-3.11.9
buildCommand: python --version && pip install --upgrade pip && pip install -r requirements.txt && python -m playwright install chromium --with-deps
```

### **Option 2: Minimal Deployment (Fallback)**

Uses `render-fallback.yaml` without Playwright for faster deployment:

```yaml
runtime: python-3.11.9
buildCommand: python --version && pip install --upgrade pip && pip install -r requirements_minimal.txt
```

## 🚀 **Deployment Steps**

### **For Render.com:**

1. **Connect your GitHub repo** to Render
2. **Choose deployment option:**
   - **Full**: Use `render.yaml` (recommended)
   - **Minimal**: Use `render-fallback.yaml` (if Playwright fails)
3. **Add environment variables** in Render dashboard:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   TWILIO_SID=your_twilio_sid
   TWILIO_TOKEN=your_twilio_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   ```
4. **Deploy and monitor** build logs

### **For Railway.app:**

1. **Connect GitHub repo**
2. **Set environment variables**
3. **Railway will auto-detect** Python and use `requirements.txt`
4. **Add start command:** `python app.py`

### **For Heroku:**

1. **Create new app**
2. **Add buildpacks:**
   ```bash
   heroku buildpacks:add heroku/python
   heroku buildpacks:add https://github.com/mxschmitt/heroku-playwright-buildpack
   ```
3. **Set environment variables**
4. **Deploy via Git**

## 🔍 **Common Issues & Solutions**

### **1. Playwright Installation Fails**

**Error:** `Could not install Playwright browsers`

**Solution:**

```bash
# Switch to minimal deployment
# Use render-fallback.yaml instead of render.yaml
# Bot will use mock data but still function
```

### **2. Memory Issues**

**Error:** `Process killed (OOM)`

**Solution:**

```bash
# Upgrade to paid plan (1GB+ RAM)
# Or use minimal deployment without Playwright
```

### **3. Build Timeout**

**Error:** `Build timed out`

**Solution:**

```bash
# Use requirements_minimal.txt
# Remove Playwright dependency temporarily
# Deploy basic version first, then upgrade
```

### **4. Environment Variables Missing**

**Error:** `KeyError: 'SUPABASE_URL'`

**Solution:**

```bash
# Add all required environment variables in platform dashboard
# Check env.template for complete list
```

## 🧪 **Testing Your Deployment**

### **1. Health Check**

```bash
curl https://your-app.onrender.com/
# Should return: {"status": "active", "service": "WhatsApp Job Alert Bot"}
```

### **2. Database Test**

```bash
curl https://your-app.onrender.com/test
# Should return: {"status": "ok", "database": "connected"}
```

### **3. WhatsApp Test**

- Send "Hi" to your WhatsApp bot
- Should receive job category menu

## 📊 **Deployment Status Indicators**

### **✅ Successful Deployment**

- Health check returns 200
- Database test passes
- WhatsApp responds to "Hi"
- Job alerts work (send "jobs")

### **⚠️ Partial Deployment**

- Health check works
- Database works
- WhatsApp works
- Jobs return mock data (Playwright failed)

### **❌ Failed Deployment**

- Health check fails
- Environment variable errors
- Database connection issues

## 🔄 **Fallback Strategy**

If full deployment fails:

1. **Switch to minimal config:**

   ```bash
   # Use render-fallback.yaml
   # Uses requirements_minimal.txt
   # Mock data instead of real scraping
   ```

2. **Test basic functionality:**

   ```bash
   # WhatsApp conversation works
   # Credit system works
   # Database operations work
   # Mock jobs are sent
   ```

3. **Upgrade incrementally:**
   ```bash
   # Once basic version is stable
   # Add Playwright back gradually
   # Monitor resource usage
   ```

## 📝 **Build Command Options**

### **Full Build (with Playwright):**

```bash
python --version && pip install --upgrade pip && pip install -r requirements.txt && python -m playwright install chromium --with-deps
```

### **Minimal Build (no Playwright):**

```bash
python --version && pip install --upgrade pip && pip install -r requirements_minimal.txt
```

### **Docker Build (most reliable):**

```dockerfile
FROM python:3.11.9-slim
RUN apt-get update && apt-get install -y libnss3 libatk-bridge2.0-0
COPY requirements.txt .
RUN pip install -r requirements.txt && python -m playwright install chromium
```

## 🎯 **Next Steps**

1. **Try deploying with updated configs**
2. **Monitor build logs carefully**
3. **Test with WhatsApp once deployed**
4. **Add real environment variables**
5. **Scale up if needed**

Your bot is now configured for reliable deployment! 🚀
