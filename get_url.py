#!/usr/bin/env python3
"""
Get public URL for WhatsApp webhook
"""
from pyngrok import ngrok
import time

def get_public_url():
    """Get the public ngrok URL for port 5000"""
    try:
        # Create tunnel to port 5000
        tunnel = ngrok.connect(5000)
        public_url = tunnel.public_url
        
        print("🌐 PUBLIC URL READY!")
        print("=" * 50)
        print(f"Your webhook URL: {public_url}/whatsapp")
        print(f"Your base URL: {public_url}")
        print("=" * 50)
        print("\n📋 NEXT STEPS:")
        print("1. Copy the webhook URL above")
        print("2. Go to Twilio Console → WhatsApp → Sandbox")
        print("3. Set webhook URL to: " + public_url + "/whatsapp")
        print("4. Your bot is ready to receive messages!")
        print("\n⚠️  Keep this script running while testing...")
        
        # Keep the tunnel alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Tunnel closed.")
            ngrok.disconnect(tunnel.public_url)
            ngrok.kill()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Alternative: Use your local IP for testing")
        print("Your Flask app is running on: http://192.168.1.141:5000")
        print("Webhook URL would be: http://192.168.1.141:5000/whatsapp")
        print("(Only works if phone and computer are on same WiFi)")

if __name__ == "__main__":
    get_public_url() 