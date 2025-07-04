#!/usr/bin/env python3
"""
Simplified Telegram bot entry point for Render deployment
"""

import os
import logging
from flask import Flask, jsonify
import threading

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app for health checks
app = Flask(__name__)

@app.route('/')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Ajirawise Telegram Bot',
        'version': '2.0.0'
    })

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Ajirawise Telegram Bot',
        'version': '2.0.0',
        'bot_running': True
    })

def start_telegram_bot():
    """Start the actual Telegram bot"""
    try:
        from telegram_bot import main
        logger.info("Starting Telegram bot from telegram_bot.py")
        main()
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")

def run_server():
    """Run Flask server with Telegram bot in background"""
    # Start Telegram bot in background thread
    bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask server
    port = int(os.getenv('PORT', 10001))
    logger.info(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    run_server() 