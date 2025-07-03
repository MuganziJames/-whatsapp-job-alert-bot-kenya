# WhatsApp Job Alert Bot - Deployment Guide

## Quick Fix for Current Build Error

The build error you're seeing is related to Python 3.13 compatibility issues with some packages. Here are the solutions:

### Option 1: Use Render/Railway/Heroku

```bash
# After deployment, run this command in your deployment console:
python install_playwright_browsers.py
```

### Option 2: Use Docker (Recommended for Playwright)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11.9-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright browsers
RUN python -m playwright install chromium
RUN python -m playwright install-deps chromium

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
```

### Option 3: Platform-Specific Solutions

#### Render.com

1. Use Python 3.11.9 (already set in runtime.txt)
2. Add build command: `pip install -r requirements.txt && python install_playwright_browsers.py`
3. Start command: `python app.py`

#### Railway

1. Add environment variable: `PYTHONUNBUFFERED=1`
2. Build command: `pip install -r requirements.txt && python install_playwright_browsers.py`

#### Heroku

1. Add buildpack: `heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-google-chrome`
2. Deploy normally

## Environment Variables Required

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
FLASK_ENV=production
```

## Troubleshooting

### If Playwright installation fails:

1. The bot will automatically fall back to mock data
2. Check logs for specific error messages
3. Try running `python install_playwright_browsers.py` manually

### If still getting build errors:

1. Use `requirements_minimal.txt` (without Playwright)
2. Bot will use mock data but still function for testing
3. Upgrade to full version once deployment is stable

## Testing Deployment

Send "hi" to your WhatsApp number to test the bot functionality.
