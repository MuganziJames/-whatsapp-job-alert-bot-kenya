"""
Register M-Pesa C2B callback URLs with Daraja API
Run this script once to set up your webhook endpoints
"""

import os
from dotenv import load_dotenv
from mpesa import mpesa_client

# Load environment variables
load_dotenv()

def main():
    """Register C2B URLs with M-Pesa Daraja API"""
    print("🔧 Registering M-Pesa C2B URLs...")
    
    # Get base URL for callbacks
    base_url = input("Enter your base URL (e.g., https://abc123.ngrok.io): ").strip()
    
    if not base_url:
        print("❌ Base URL is required!")
        return
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    # Construct callback URLs
    validation_url = f"{base_url}/c2b/validate"
    confirmation_url = f"{base_url}/c2b/confirm"
    
    print(f"📝 Validation URL: {validation_url}")
    print(f"📝 Confirmation URL: {confirmation_url}")
    
    # Confirm registration
    confirm = input("\n✅ Proceed with registration? (y/n): ").lower().strip()
    
    if confirm != 'y':
        print("❌ Registration cancelled")
        return
    
    # Register URLs
    success = mpesa_client.register_urls(validation_url, confirmation_url)
    
    if success:
        print("\n🎉 C2B URLs registered successfully!")
        print("\n📋 Next steps:")
        print("1. Start your Flask app: python app.py")
        print("2. Test payments via M-Pesa")
        print("3. Check that callbacks are working")
    else:
        print("\n❌ Registration failed!")
        print("Check your M-Pesa credentials and try again.")

if __name__ == "__main__":
    main() 