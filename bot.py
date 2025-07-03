"""
WhatsApp bot logic using Twilio
Enhanced with DeepSeek AI for better user interactions
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

# AI Helper import (with fallback)
try:
    from utils.ai_helper import (
        ask_deepseek, 
        is_career_question, 
        extract_job_interest,
        get_job_category_recommendation,
        get_career_advice,
        generate_personalized_message,
        improve_job_matching,
        initialize_ai_helper
    )
    AI_AVAILABLE = True
    logger.info("🤖 AI Helper loaded successfully")
    
    # Initialize AI helper
    if not initialize_ai_helper():
        AI_AVAILABLE = False
        logger.warning("⚠️ AI Helper initialization failed, using fallback mode")
        
except ImportError as e:
    AI_AVAILABLE = False
    logger.warning(f"⚠️ AI Helper not available: {str(e)}")

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
    """Process incoming WhatsApp message with AI enhancement and return response"""
    try:
        from db import db
        
        # Normalize phone number
        phone = normalize_phone(from_number)
        message = message_body.strip()
        message_lower = message.lower()
        
        logger.info(f"Processing message from {phone}: {message}")
        
        # Check if user exists
        user = db.get_user_by_phone(phone)
        
        # AI-powered career question detection
        if AI_AVAILABLE and is_career_question(message):
            logger.info(f"🤖 AI detected career question: {message}")
            
            # Get user context for personalized response
            user_context = {
                'user_info': user if user else {},
                'available_categories': VALID_JOB_CATEGORIES
            }
            
            # Get AI response
            ai_response = ask_deepseek(message, user_context)
            
            # Check if AI suggests a job category
            if AI_AVAILABLE:
                suggested_interest = extract_job_interest(message)
                if suggested_interest:
                    # Add category suggestion to response
                    ai_response["content"] += f"\n\n💡 Based on your question, you might be interested in *{suggested_interest.title()}* jobs. Send *{suggested_interest}* to set this as your interest!"
            
            # Log AI interaction
            db.log_ai_interaction(phone, message, ai_response["content"], 'career_question')
            
            return ai_response["content"]
        
        # AI-powered job category recommendation
        if AI_AVAILABLE and any(phrase in message_lower for phrase in ['help me choose', 'which job', 'what should i', 'recommend', 'suggest']):
            logger.info(f"🤖 AI providing job category recommendation")
            
            recommendation = get_job_category_recommendation(message)
            
            if recommendation["category"]:
                # Add quick action to set the recommended category
                recommendation["explanation"] += f"\n\n🎯 Ready to get started? Send *{recommendation['category']}* to set this as your job interest!"
            
            # Log AI interaction
            db.log_ai_interaction(phone, message, recommendation["explanation"], 'job_recommendation')
            
            return recommendation["explanation"]
        
        # Handle "hi" greeting with AI enhancement
        if message_lower in ['hi', 'hello', 'start', 'help']:
            base_menu = get_categories_menu()
            
            if AI_AVAILABLE and user and user.get('interest'):
                # Personalized greeting for returning users
                return f"👋 Welcome back! You're currently interested in *{user['interest'].title()}* jobs.\n\n{base_menu}\n\n💡 *Tip:* You can also ask me questions like 'What does a data analyst do?' or 'Help me choose a career path!'"
            else:
                # Enhanced greeting for new users
                return f"{base_menu}\n\n🤖 *New!* I can also help answer your career questions! Try asking:\n• 'What does a [job title] do?'\n• 'Help me choose a job category'\n• 'What skills do I need for [career]?'"
        
        # Handle job interests with AI validation
        if is_valid_category(message_lower):
            # Normalize the category
            normalized_category = normalize_category(message_lower)
            
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
        
        # AI-powered fallback for unrecognized categories
        if AI_AVAILABLE and not message_lower.isdigit() and not message_lower in ['balance', 'credits', 'account', 'jobs', 'job', 'work', 'refresh', 'new', 'reset']:
            # Check if user might be trying to express a job interest
            suggested_interest = extract_job_interest(message)
            if suggested_interest:
                return f"🤖 It sounds like you might be interested in *{suggested_interest.title()}* jobs!\n\nSend *{suggested_interest}* to set this as your job interest, or send *hi* to see all available categories."
            
            # Check if it's a career question
            if any(word in message_lower for word in ['what', 'how', 'why', 'when', 'where', 'job', 'career', 'work', 'salary', 'skill']):
                career_advice = get_career_advice(message, {'user_info': user if user else {}})
                return career_advice
            
            # Generic AI response for other queries
            ai_response = ask_deepseek(f"User asked: {message}. Provide a helpful response about job searching or career advice in Kenya, and guide them to use the job alert bot features.")
            return ai_response["content"]
        
        # Check if user is trying to select a category but it's invalid (non-AI fallback)
        if not AI_AVAILABLE and not message_lower.isdigit() and not message_lower in ['balance', 'credits', 'account', 'jobs', 'job', 'work', 'refresh', 'new', 'reset']:
            # User might be trying to select an invalid category
            return f"❌ Sorry, I don't recognize that job category.\n\n{get_categories_menu()}"
        
        # Handle credit selection (1-30)
        if message_lower.isdigit():
            credit_amount = int(message_lower)
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
        if message_lower in ['balance', 'credits', 'account']:
            if user:
                return f"💳 *Account Balance:*\nCredits: *{user['balance']}*\nJob Interest: *{user.get('interest', 'Not set')}*\n\nSend a number (1-30) to add more credits!"
            else:
                return "❌ You're not registered yet. Send *hi* to get started!"
        
        # Handle refresh command to clear old job records
        if message_lower in ['refresh', 'new', 'reset']:
            if not user:
                return "❌ Please register first by sending *hi*"
            
            # Clear old job records
            db.clear_old_job_records(phone, days_old=0)  # Clear all records
            return f"🔄 *Job history refreshed!*\n\nAll previous job records cleared. You can now receive jobs again!\n\nSend *jobs* to get fresh job alerts."
        
        # Handle job request with AI enhancement
        if message_lower in ['jobs', 'job', 'work']:
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
            
            # AI-powered job filtering and ranking
            if AI_AVAILABLE:
                logger.info(f"🤖 AI filtering {len(jobs)} jobs for {user['interest']}")
                
                # Filter jobs using AI
                filtered_jobs = []
                for job in jobs:
                    if not has_job_been_sent(phone, job['id']):
                        # Use AI to improve job matching
                        job_analysis = improve_job_matching(
                            job.get('title', ''),
                            job.get('company', ''),
                            user['interest']
                        )
                        
                        if job_analysis['should_send']:
                            job['ai_score'] = job_analysis['match_score']
                            filtered_jobs.append(job)
                
                # Sort by AI score (highest first)
                filtered_jobs.sort(key=lambda x: x.get('ai_score', 50), reverse=True)
                jobs = filtered_jobs
            
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
                
                # Generate personalized message using AI
                if AI_AVAILABLE:
                    try:
                        personalized_message = generate_personalized_message(job_to_send, user)
                        return personalized_message
                    except Exception as e:
                        logger.error(f"Error generating personalized message: {str(e)}")
                        # Fall back to standard message
                
                # Standard job message (fallback)
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
        
        # AI-powered default response
        if AI_AVAILABLE:
            # Let AI handle unrecognized messages
            ai_response = ask_deepseek(f"User sent: '{message}'. This is a WhatsApp job alert bot. Provide a helpful response and guide them to available commands.")
            return ai_response["content"]
        
        # Standard default response
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