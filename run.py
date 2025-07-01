#!/usr/bin/env python3
"""
Simple startup script for WhatsApp Job Alert Bot
This provides an alternative way to run the application
"""

from app import app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    # Get configuration from environment
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('HOST', '0.0.0.0')
    
    print("🚀 Starting WhatsApp Job Alert Bot...")
    print(f"📍 Running on http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print("💡 Send 'Hi' to your WhatsApp bot to get started!")
    
    app.run(host=host, port=port, debug=debug) 