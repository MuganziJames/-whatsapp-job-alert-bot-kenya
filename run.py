#!/usr/bin/env python3
"""
Simple startup script for Ajirawise - Smart Job Alert Bot
This provides an alternative way to run the application
"""

from app import app
import os
from dotenv import load_dotenv
from scheduler import start_smart_job_scheduler, get_scheduler_stats

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    # Get configuration from environment
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('HOST', '0.0.0.0')
    
    print("🚀 Starting Ajirawise - Smart Job Alert Bot...")
    print(f"📍 Running on http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print("💡 Send 'Hi' to your Ajirawise bot to get started!")
    
    # Smart job scheduler DISABLED to prevent bot instance conflicts
    print("🔇 Automatic job scheduler disabled")
    print("📱 Jobs will be sent only when users explicitly request them")
    print("✨ This prevents Telegram bot conflicts and improves user experience")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        from scheduler import stop_smart_job_scheduler
        stop_smart_job_scheduler()
        print("✅ Smart scheduler stopped") 