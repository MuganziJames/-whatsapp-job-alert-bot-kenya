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

# Valid job categories - centralized list
VALID_JOB_CATEGORIES = [
    'data entry',
    'sales & marketing', 
    'delivery & logistics',
    'customer service',
    'finance & accounting',
    'admin & office work',
    'teaching / training',
    'internships / attachments',
    'software engineering'
]

def get_categories_menu() -> str:
    """Get formatted categories menu for welcome message"""
    return """🔍 *Welcome to Kenya Job Alert Bot!*

Please reply with your job interest:
• *Data Entry* - Data input and processing jobs
• *Sales & Marketing* - Sales, marketing, and business development
• *Delivery & Logistics* - Delivery, transport, and logistics roles
• *Customer Service* - Customer support and service positions
• *Finance & Accounting* - Financial, accounting, and bookkeeping jobs
• *Admin & Office Work* - Administrative and office support roles
• *Teaching / Training* - Education, training, and tutoring positions
• *Internships / Attachments* - Internship and attachment opportunities
• *Software Engineering* - Programming, development, and tech roles

What type of work are you looking for?"""

def normalize_category(user_input: str) -> str:
    """Normalize user input to match valid categories"""
    user_input = user_input.strip().lower()
    
    # Direct matches
    if user_input in VALID_JOB_CATEGORIES:
        return user_input
    
    # Handle variations and shortcuts
    category_mappings = {
        'data': 'data entry',
        'entry': 'data entry',
        'sales': 'sales & marketing',
        'marketing': 'sales & marketing',
        'delivery': 'delivery & logistics',
        'logistics': 'delivery & logistics',
        'transport': 'delivery & logistics',
        'customer': 'customer service',
        'service': 'customer service',
        'support': 'customer service',
        'finance': 'finance & accounting',
        'accounting': 'finance & accounting',
        'admin': 'admin & office work',
        'office': 'admin & office work',
        'teaching': 'teaching / training',
        'training': 'teaching / training',
        'tutor': 'teaching / training',
        'teacher': 'teaching / training',
        'internship': 'internships / attachments',
        'attachment': 'internships / attachments',
        'intern': 'internships / attachments',
        'software': 'software engineering',
        'engineering': 'software engineering',
        'programming': 'software engineering',
        'developer': 'software engineering',
        'tech': 'software engineering',
        'it': 'software engineering'
    }
    
    return category_mappings.get(user_input, None)

def is_valid_category(user_input: str) -> bool:
    """Check if user input is a valid job category"""
    return normalize_category(user_input) is not None

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

def has_job_been_sent(phone: str, job_id: str) -> bool:
    """Helper function to check if job has already been sent to user"""
    from db import db
    return db.was_job_sent(phone, job_id)

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
            return get_categories_menu()
        
        # Handle job interests
        if is_valid_category(message):
            # Normalize the category
            normalized_category = normalize_category(message)
            
            # Save user interest
            if user:
                # Update existing user
                updated_user = db.add_or_update_user(phone, interest=normalized_category)
                # Get fresh user data to check current balance
                fresh_user = db.get_user_by_phone(phone)
                current_balance = fresh_user.get('balance', 0) if fresh_user else 0
                
                if user.get('interest') == normalized_category:
                    if current_balance > 0:
                        return f"✅ You already have *{normalized_category.title()}* jobs set as your interest.\n\n💳 Current Balance: *{current_balance}* credits\n\nSend *jobs* to get job alerts!"
                    else:
                        return f"✅ You already have *{normalized_category.title()}* jobs set as your interest.\n\n💰 *Choose your credits:*\nSend a number from *1 to 30* to get that many job alert credits.\n\nExample: Send *5* to get 5 credits"
                else:
                    if current_balance > 0:
                        return f"✅ Interest updated to *{normalized_category.title()}* jobs!\n\n💳 Current Balance: *{current_balance}* credits\n\nSend *jobs* to get job alerts!"
                    else:
                        return f"✅ Interest updated to *{normalized_category.title()}* jobs!\n\n💰 *Choose your credits:*\nSend a number from *1 to 30* to get that many job alert credits.\n\nExample: Send *10* to get 10 credits"
            else:
                # Create new user (always needs credits)
                new_user = db.add_or_update_user(phone, interest=normalized_category, balance=0)
                return f"✅ Great! You're now registered for *{normalized_category.title()}* job alerts.\n\n💰 *Choose your credits:*\nSend a number from *1 to 30* to get that many job alert credits.\n\nExample: Send *5* to get 5 credits"
        
        # Check if user is trying to select a category but it's invalid
        # This should come after valid category check but before credit selection
        if not message.isdigit() and not message in ['balance', 'credits', 'account', 'jobs', 'job', 'work', 'refresh', 'new', 'reset']:
            # User might be trying to select an invalid category
            return f"❌ Sorry, I don't recognize that job category.\n\n{get_categories_menu()}"
        
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
        
        # Handle refresh command to clear old job records
        if message in ['refresh', 'new', 'reset']:
            if not user:
                return "❌ Please register first by sending *hi*"
            
            # Clear old job records
            db.clear_old_job_records(phone, days_old=0)  # Clear all records
            return f"🔄 *Job history refreshed!*\n\nAll previous job records cleared. You can now receive jobs again!\n\nSend *jobs* to get fresh job alerts."
        
        # Handle job request
        if message in ['jobs', 'job', 'work']:
            if not user:
                return "❌ Please register first by sending *hi*"
            
            if not user.get('interest'):
                return "❌ Please set your job interest first. Send *hi* to see options."
            
            if user['balance'] <= 0:
                return f"❌ No credits available!\n\n💰 *Add credits:*\nSend a number from *1 to 30* to get that many credits.\n\nExample: Send *5* to get 5 credits"
            
            # Get and send job
            from working_scraper import scrape_jobs_working as scrape_jobs
            jobs = scrape_jobs(user['interest'])
            
            if not jobs:
                return f"😔 No new *{user['interest']}* jobs available right now. We'll keep looking!"
            
            # Find first job that hasn't been sent
            job_to_send = None
            for job in jobs:
                if not has_job_been_sent(phone, job['id']):
                    job_to_send = job
                    break
            
            # Check if we found a new job
            if not job_to_send:
                return f"🔍 All current *{user['interest']}* jobs have been sent to you!\n\n💡 *What you can do:*\n• Try a different job category (send *hi*)\n• Send *refresh* to reset your job history\n• Check back in a few hours for new jobs\n• Send *balance* to see your credits\n\n🔄 New jobs are added regularly!"
            
            # Deduct credit and send job
            if db.deduct_credit(phone):
                # Log the job as sent
                db.log_job_sent(phone, job_to_send['id'], job_to_send['title'], job_to_send['link'])
                
                job_message = f"""🎯 *New {user['interest'].title()} Job Alert:*

📋 *{job_to_send['title']}*
🏢 Company: {job_to_send.get('company', 'Not specified')}
📍 Location: {job_to_send.get('location', 'Kenya')}
🔗 {job_to_send['link']}
🌐 Source: {job_to_send.get('source', 'Job Board')}

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
• Send *refresh* to reset job history
• Send *1-30* to add credits

Try one of these commands!"""
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {str(e)}")
        return "❌ Sorry, there was an error. Please try again later." 