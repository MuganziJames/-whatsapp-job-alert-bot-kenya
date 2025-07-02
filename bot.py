"""
WhatsApp bot logic using Twilio
Handles user interactions for Kenya Job Alert Bot
"""

import os
import logging
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Twilio client
twilio_client = Client(
    os.getenv('TWILIO_SID'),
    os.getenv('TWILIO_TOKEN')
)

def send_whatsapp_message(to_number: str, message: str) -> bool:
    """Send WhatsApp message via Twilio"""
    try:
        # Ensure proper WhatsApp format
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
        
        message_instance = twilio_client.messages.create(
            body=message,
            from_=os.getenv('TWILIO_WHATSAPP_NUMBER'),
            to=to_number
        )
        
        logger.info(f"WhatsApp message sent to {to_number}: {message_instance.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp message to {to_number}: {str(e)}")
        return False

def normalize_phone(phone: str) -> str:
    """Normalize phone number"""
    # Remove whatsapp: prefix if present
    if phone.startswith('whatsapp:'):
        phone = phone.replace('whatsapp:', '')
    
    # Remove + if present
    if phone.startswith('+'):
        phone = phone[1:]
    
    # Handle Kenyan numbers
    if phone.startswith('254'):
        return f'+{phone}'
    elif phone.startswith('0'):
        return f'+254{phone[1:]}'
    elif len(phone) == 9:
        return f'+254{phone}'
    
    return phone

def process_whatsapp_message(from_number: str, message_body: str) -> str:
    """Process incoming WhatsApp message and return response"""
    try:
        from db import db
        
        # Normalize phone number
        phone = normalize_phone(from_number)
        message = message_body.strip().lower()
        
        logger.info(f"Processing message from {phone}: {message}")
        
        # Check if user exists
        user = db.get_user_by_phone(phone)
        
        # Handle "hi" greeting
        if message in ['hi', 'hello', 'start', 'help']:
            return """🔍 *Welcome to Kenya Job Alert Bot!*

Please reply with your job interest:
• *fundi* - Handyman/Technician work
• *cleaner* - Cleaning jobs
• *tutor* - Teaching/tutoring jobs
• *driver* - Driving jobs
• *security* - Security guard jobs

What type of work are you looking for?"""
        
        # Handle job interests
        job_interests = ['fundi', 'cleaner', 'tutor', 'driver', 'security']
        
        if message in job_interests:
            # Save user interest
            if user:
                # Update existing user
                updated_user = db.add_or_update_user(phone, interest=message)
                if user['interest'] == message:
                    return f"✅ You already have *{message}* jobs set as your interest.\n\n💰 *Choose your credits:*\nSend a number from *1 to 30* to get that many job alert credits.\n\nExample: Send *5* to get 5 credits"
                else:
                    return f"✅ Interest updated to *{message}* jobs!\n\n💰 *Choose your credits:*\nSend a number from *1 to 30* to get that many job alert credits.\n\nExample: Send *10* to get 10 credits"
            else:
                # Create new user
                new_user = db.add_or_update_user(phone, interest=message, balance=0)
                return f"✅ Great! You're now registered for *{message}* job alerts.\n\n💰 *Choose your credits:*\nSend a number from *1 to 30* to get that many job alert credits.\n\nExample: Send *5* to get 5 credits"
        
        # Handle credit selection (1-30)
        if message.isdigit():
            credit_amount = int(message)
            if 1 <= credit_amount <= 30:
                if not user:
                    return "❌ Please register first by sending *hi* and selecting your job interest."
                
                if not user.get('interest'):
                    return "❌ Please set your job interest first. Send *hi* to see options."
                
                # Add credits to user account
                success = db.add_balance(phone, credit_amount)
                
                if success:
                    new_balance = user['balance'] + credit_amount
                    return f"✅ *Credits Added Successfully!*\n\n💰 Added: *{credit_amount}* credits\n💳 Total Balance: *{new_balance}* credits\n🎯 Job Interest: *{user['interest']}*\n\nSend *jobs* to start receiving job alerts!"
                else:
                    return "❌ Error adding credits. Please try again."
            else:
                return "❌ Please send a number between *1 and 30* to select your credits.\n\nExample: Send *5* to get 5 credits"
        
        # Handle balance check
        if message in ['balance', 'credits', 'account']:
            if user:
                return f"💳 *Account Balance:*\nCredits: *{user['balance']}*\nJob Interest: *{user.get('interest', 'Not set')}*\n\nSend a number (1-30) to add more credits!"
            else:
                return "❌ You're not registered yet. Send *hi* to get started!"
        
        # Handle job request
        if message in ['jobs', 'job', 'work']:
            if not user:
                return "❌ Please register first by sending *hi*"
            
            if not user.get('interest'):
                return "❌ Please set your job interest first. Send *hi* to see options."
            
            if user['balance'] <= 0:
                return f"❌ No credits available!\n\n💰 *Add credits:*\nSend a number from *1 to 30* to get that many credits.\n\nExample: Send *5* to get 5 credits"
            
            # Get and send job
            from scraper import scrape_jobs
            jobs = scrape_jobs(user['interest'])
            
            if not jobs:
                return f"😔 No new *{user['interest']}* jobs available right now. We'll keep looking!"
            
            # Send first available job
            job = jobs[0]
            
            # Check if already sent
            if db.was_job_sent(phone, job['id']):
                return f"✅ You're up to date! No new *{user['interest']}* jobs since last check."
            
            # Deduct credit and send job
            if db.deduct_credit(phone):
                db.log_job_sent(phone, job['id'], job['title'], job['link'])
                
                job_message = f"""🎯 *New {user['interest'].title()} Job Alert:*

📋 *{job['title']}*
🔗 {job['link']}
�� Location: {job.get('location', 'Kenya')}

💰 Credit used: 1
💳 Remaining: {user['balance'] - 1}

Good luck! 🍀"""
                return job_message
            else:
                return "❌ Error processing your request. Please try again."
        
        # Default response
        return """🤔 I didn't understand that.

*Available commands:*
• Send *hi* to get started
• Send *jobs* to get job alerts
• Send *balance* to check credits
• Send *1-30* to add credits

Try one of these commands!"""
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {str(e)}")
        return "❌ Sorry, there was an error. Please try again later." 