"""
Dual Platform Job Alert Bot Runner
Runs both WhatsApp (Flask) and Telegram bots simultaneously
"""

import os
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_flask_app():
    """Run the Flask WhatsApp bot"""
    print("🚀 Starting WhatsApp Bot (Flask)...")
    from app import app
    app.run(host='0.0.0.0', port=5000, debug=False)

def run_telegram_bot():
    """Run the Telegram bot"""
    print("🤖 Starting Telegram Bot...")
    from telegram_bot import main
    main()

def main():
    """Main function to run both bots"""
    print("🌟 Starting Dual Platform Job Alert Bot")
    print("=" * 50)
    
    # Check environment variables
    required_vars = [
        'SUPABASE_URL', 'SUPABASE_KEY',
        'OPENROUTER_API_KEY',
        'TWILIO_SID', 'TWILIO_TOKEN', 'TWILIO_WHATSAPP_NUMBER',
        'TELEGRAM_BOT_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease update your .env file and try again.")
        return
    
    print("✅ Environment variables loaded")
    print(f"📱 WhatsApp: {os.getenv('TWILIO_WHATSAPP_NUMBER')}")
    print(f"🤖 Telegram: Bot token configured")
    print("=" * 50)
    
    # Start both bots in separate threads
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    
    try:
        # Start Flask app
        flask_thread.start()
        time.sleep(2)  # Give Flask time to start
        
        # Start Telegram bot
        telegram_thread.start()
        
        print("🎉 Both bots are running!")
        print("📱 WhatsApp: http://localhost:5000/whatsapp")
        print("🤖 Telegram: Polling for updates")
        print("\n💡 Press Ctrl+C to stop both bots")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping bots...")
        print("✅ Bots stopped successfully")

if __name__ == "__main__":
    main() 