"""
WhatsApp bot logic using Twilio
Enhanced with DeepSeek AI for better user interactions
Handles user interactions for Kenya Job Alert Bot
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Twilio client
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioException
    
    twilio_client = Client(os.getenv('TWILIO_SID'), os.getenv('TWILIO_TOKEN'))
    TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
    logger.info("📱 Twilio client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Twilio client: {e}")
    twilio_client = None

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

# Smart Job Detection import
try:
    from utils.smart_job_detection import (
        detect_job_request,
        is_smart_job_request,
        extract_job_context_from_message
    )
    SMART_JOB_DETECTION_AVAILABLE = True
    logger.info("🧠 Smart Job Detection loaded successfully")
except ImportError as e:
    SMART_JOB_DETECTION_AVAILABLE = False
    logger.warning(f"⚠️ Smart Job Detection not available: {str(e)}")

def get_categories_menu() -> str:
    """Get formatted categories menu for welcome message"""
    return """🔍 *Welcome to Ajirawise - Your Smart Job Assistant!*

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

What type of work are you looking for?

🤖 *New!* I can also help answer your career questions! Try asking:
• 'What does a [job title] do?'
• 'Help me choose a job category'
• 'What skills do I need for [career]?'"""

def smart_extract_job_category(user_input: str) -> str:
    """
    Smart extraction of job categories from natural language input
    Handles phrases like "switch my interest to software engineering"
    """
    user_input = user_input.strip().lower()
    
    # Remove common filler words and phrases
    filler_patterns = [
        r'\b(switch|change|set|update|my|interest|to|for|in|i want|i need|looking for|search for|find|get)\b',
        r'\b(job|jobs|work|career|position|role|roles)\b',
        r'\b(please|can you|could you|would you|help me)\b'
    ]
    
    cleaned_input = user_input
    for pattern in filler_patterns:
        cleaned_input = re.sub(pattern, ' ', cleaned_input)
    
    # Clean up extra spaces
    cleaned_input = ' '.join(cleaned_input.split())
    
    # Try to match against our categories
    return normalize_category(cleaned_input)

def normalize_category(user_input: str) -> str:
    """Enhanced normalize user input to match valid categories with better fuzzy matching"""
    user_input = user_input.strip().lower()
    
    # Direct matches (case insensitive)
    for category in VALID_JOB_CATEGORIES:
        if user_input == category.lower():
            return category
    
    # Handle exact phrase matches with flexible spacing and punctuation
    category_variations = {
        'data entry': ['data entry', 'data-entry', 'dataentry', 'data_entry'],
        'sales & marketing': [
            'sales & marketing', 'sales and marketing', 'sales marketing', 
            'sales&marketing', 'sales_marketing', 'sales-marketing'
        ],
        'delivery & logistics': [
            'delivery & logistics', 'delivery and logistics', 'delivery logistics',
            'delivery&logistics', 'delivery_logistics', 'delivery-logistics'
        ],
        'customer service': [
            'customer service', 'customer-service', 'customerservice', 'customer_service'
        ],
        'finance & accounting': [
            'finance & accounting', 'finance and accounting', 'finance accounting',
            'finance&accounting', 'finance_accounting', 'finance-accounting'
        ],
        'admin & office work': [
            'admin & office work', 'admin and office work', 'admin office work',
            'admin&office work', 'admin_office_work', 'admin-office-work',
            'admin & office', 'admin office'
        ],
        'teaching / training': [
            'teaching / training', 'teaching and training', 'teaching training',
            'teaching/training', 'teaching_training', 'teaching-training',
            'teaching / training', 'teaching/ training'  # Handle the exact case from screenshot
        ],
        'internships / attachments': [
            'internships / attachments', 'internships and attachments', 'internships attachments',
            'internships/attachments', 'internships_attachments', 'internships-attachments',
            'internship / attachment', 'internship attachment'
        ],
        'software engineering': [
            'software engineering', 'software-engineering', 'softwareengineering', 'software_engineering'
        ]
    }
    
    # Check variations
    for category, variations in category_variations.items():
        for variation in variations:
            if user_input == variation.lower():
                return category
    
    # Handle partial matches and shortcuts (but avoid confusion)
    category_mappings = {
        # Data Entry
        'data': 'data entry',
        'entry': 'data entry',
        
        # Sales & Marketing  
        'sales': 'sales & marketing',
        'marketing': 'sales & marketing',
        'business development': 'sales & marketing',
        'sales rep': 'sales & marketing',
        'sales representative': 'sales & marketing',
        
        # Delivery & Logistics
        'delivery': 'delivery & logistics',
        'logistics': 'delivery & logistics',
        'transport': 'delivery & logistics',
        'transportation': 'delivery & logistics',
        'courier': 'delivery & logistics',
        'driver': 'delivery & logistics',
        'warehouse': 'delivery & logistics',
        
        # Customer Service
        'customer': 'customer service',
        'service': 'customer service',
        'support': 'customer service',
        'customer support': 'customer service',
        'call center': 'customer service',
        'helpdesk': 'customer service',
        
        # Finance & Accounting
        'finance': 'finance & accounting',
        'accounting': 'finance & accounting',
        'bookkeeping': 'finance & accounting',
        'accounts': 'finance & accounting',
        'financial': 'finance & accounting',
        
        # Admin & Office Work
        'admin': 'admin & office work',
        'office': 'admin & office work',
        'administrative': 'admin & office work',
        'secretary': 'admin & office work',
        'receptionist': 'admin & office work',
        'clerk': 'admin & office work',
        
        # Teaching / Training
        'teaching': 'teaching / training',
        'training': 'teaching / training',
        'tutor': 'teaching / training',
        'teacher': 'teaching / training',
        'education': 'teaching / training',
        'instructor': 'teaching / training',
        'lecturer': 'teaching / training',
        
        # Internships / Attachments
        'internship': 'internships / attachments',
        'attachment': 'internships / attachments',
        'intern': 'internships / attachments',
        'trainee': 'internships / attachments',
        'graduate program': 'internships / attachments',
        
        # Software Engineering
        'software': 'software engineering',
        'engineering': 'software engineering',
        'programming': 'software engineering',
        'developer': 'software engineering',
        'tech': 'software engineering',
        'it': 'software engineering',
        'coding': 'software engineering',
        'web development': 'software engineering',
        'mobile development': 'software engineering',
        'app development': 'software engineering',
        'python': 'software engineering',
        'javascript': 'software engineering',
        'java': 'software engineering'
    }
    
    # Avoid confusion with common greetings
    if user_input in ['hi', 'hello', 'hey', 'start', 'help']:
        return None
    
    # Check single word matches (be careful with short words)
    if len(user_input) >= 3:  # Avoid very short words that might be confusing
        for key, category in category_mappings.items():
            if user_input == key.lower():
                return category
    
    # Check if the input contains any of our keywords
    for key, category in category_mappings.items():
        if key in user_input and len(key) >= 4:  # Only match longer keywords within text
            return category
    
    return None

def detect_job_interest_from_message(message: str) -> str:
    """
    Detect job interest from natural language messages
    Handles phrases like "switch my interest to software engineering"
    """
    message = message.strip().lower()
    
    # Common patterns for changing interests
    interest_patterns = [
        r'(?:switch|change|set|update).*?(?:interest|job|career).*?(?:to|for|in)\s+(.+)',
        r'(?:i want|i need|looking for|search for|find|get)\s+(.+?)(?:\s+job|work|career|position|role)?',
        r'(?:interested in|focus on|specialize in)\s+(.+)',
        r'(?:my interest is|i am interested in)\s+(.+)'
    ]
    
    for pattern in interest_patterns:
        match = re.search(pattern, message)
        if match:
            potential_category = match.group(1).strip()
            # Try smart extraction first
            category = smart_extract_job_category(potential_category)
            if category:
                return category
            # Fallback to normal normalization
            category = normalize_category(potential_category)
            if category:
                return category
    
    # If no pattern matches, try direct category detection
    return normalize_category(message)

def is_valid_category(user_input: str) -> bool:
    """Check if user input is a valid job category"""
    return normalize_category(user_input) is not None

def is_interest_change_request(message: str) -> bool:
    """Check if message is requesting to change job interest"""
    message = message.lower()
    change_indicators = [
        'switch', 'change', 'set', 'update', 'my interest', 'i want', 'i need',
        'looking for', 'search for', 'interested in', 'focus on', 'specialize in'
    ]
    
    return any(indicator in message for indicator in change_indicators)

def send_whatsapp_message(to_number: str, message: str) -> bool:
    """Send WhatsApp message via Twilio"""
    try:
        if not twilio_client:
            logger.error("Twilio client not initialized")
            return False
        
        # Ensure phone number has whatsapp: prefix
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
        
        # Send message via Twilio API
        message_obj = twilio_client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=to_number
        )
        
        logger.info(f"WhatsApp message sent to {to_number}: {message_obj.sid}")
        return True
        
    except TwilioException as e:
        logger.error(f"Twilio API error: {str(e)}")
        return False
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

def is_career_question_check(message: str) -> bool:
    """Check if message is a career question (wrapper for AI function)"""
    if AI_AVAILABLE:
        return is_career_question(message)
    return False

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
        
        # Handle job request FIRST - prioritize explicit job commands (moved to top)
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
            
            # Basic job filtering (AI disabled to preserve rate limits)
            logger.info(f"📋 Basic filtering {len(jobs)} jobs for {user['interest']}")
            
            # Simple filtering - just check if job hasn't been sent
            filtered_jobs = []
            for job in jobs:
                if not has_job_been_sent(phone, job['id']):
                    filtered_jobs.append(job)
            
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

Good luck! 🍀

💡 *Want more jobs?* Type *jobs* anytime to get another job alert!"""
                return job_message
            else:
                return "❌ Error processing your request. Please try again."
        
        # AI-powered career question detection (with rate limiting protection)
        if AI_AVAILABLE and is_career_question(message):
            logger.info(f"🤖 AI detected career question: {message}")
            
            # Get user context for personalized response
            user_context = {
                'user_info': user if user else {},
                'available_categories': VALID_JOB_CATEGORIES
            }
            
            # Get AI response with fallback handling
            ai_response = ask_deepseek(message, user_context)
            
            # Check if AI suggests a job category (only if not rate limited)
            if AI_AVAILABLE and "daily AI limit" not in ai_response["content"]:
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
        
        # Admin stats command (hidden feature)
        if message_lower == 'admin_stats' and phone == 'whatsapp:+254104827342':  # Your phone number
            try:
                from utils.ai_helper import get_model_usage_stats
                stats = get_model_usage_stats()
                
                if not stats:
                    return "📊 *AI Model Stats:*\nNo usage data yet."
                
                stats_text = "📊 *AI Model Usage Stats:*\n\n"
                for stat in stats:
                    stats_text += f"🤖 *{stat['model']}*\n"
                    stats_text += f"  • Attempts: {stat['attempts']}\n"
                    stats_text += f"  • Success Rate: {stat['success_rate']}\n\n"
                
                return stats_text
            except Exception as e:
                return f"❌ Error getting stats: {str(e)}"

        # Handle "hi" greeting with AI enhancement
        if message_lower in ['hi', 'hello', 'start', 'help']:
            base_menu = get_categories_menu()
        
            if AI_AVAILABLE and user and user.get('interest'):
                # Personalized greeting for returning users
                return f"👋 Welcome back! You're currently interested in *{user['interest'].title()}* jobs.\n\n{base_menu}\n\n💡 *Tip:* You can also ask me questions like 'What does a data analyst do?' or 'Help me choose a career path!'"
            else:
                # Enhanced greeting for new users (menu already includes AI help text)
                return base_menu
        
        # Smart job interest detection - handles natural language and case sensitivity
        detected_category = None
        
        # First, try to detect if this is an interest change request
        if is_interest_change_request(message):
            detected_category = detect_job_interest_from_message(message)
        
        # If not an explicit change request, try direct category detection
        if not detected_category:
            detected_category = normalize_category(message_lower)
        
        # Handle job interests with smart detection
        if detected_category:
            # Use the detected category
            normalized_category = detected_category
            
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
                        return f"✅ You already have *{normalized_category.title()}* jobs set as your interest.\n\n💰 *Choose your credits:*\nSend a number from *1 to 30* to get that many job alert credits.\n\nExample: Send *10* to get 10 credits"
                else:
                    if current_balance > 0:
                        return f"✅ Interest updated to *{normalized_category.title()}* jobs!\n\n💳 Current Balance: *{current_balance}* credits\n\nSend *jobs* to get job alerts!"
                    else:
                        return f"✅ Interest updated to *{normalized_category.title()}* jobs!\n\n💰 *Choose your credits:*\nSend a number from *1 to 30* to get that many job alert credits.\n\nExample: Send *10* to get 10 credits"
            else:
                # Create new user and check if they have credits
                new_user = db.add_or_update_user(phone, interest=normalized_category, balance=0)
                # Get fresh user data to check current balance
                fresh_user = db.get_user_by_phone(phone)
                current_balance = fresh_user.get('balance', 0) if fresh_user else 0
                
                if current_balance > 0:
                    return f"✅ Great! You're now registered for *{normalized_category.title()}* job alerts.\n\n💳 Current Balance: *{current_balance}* credits\n\nSend *jobs* to get job alerts!"
                else:
                    return f"✅ Great! You're now registered for *{normalized_category.title()}* job alerts.\n\n💰 *Choose your credits:*\nSend a number from *1 to 30* to get that many job alert credits.\n\nExample: Send *5* to get 5 credits"
        
        # Check if this might be a job request that wasn't handled above (user not registered)
        if SMART_JOB_DETECTION_AVAILABLE and is_smart_job_request(message, threshold=0.4):
            return f"🔍 I detected you're looking for jobs! To get started:\n\n1. Send *hi* to register\n2. Choose your job interest\n3. Add credits (1-30)\n4. Start receiving job alerts!\n\n💡 *Try*: Send *hi* to begin"
        
        # AI-powered fallback for unrecognized categories (excluding job requests)
        if AI_AVAILABLE and not message_lower.isdigit() and not message_lower in ['balance', 'credits', 'account', 'refresh', 'new', 'reset']:
            # Skip AI processing if this is already identified as a job request
            if SMART_JOB_DETECTION_AVAILABLE and is_smart_job_request(message, threshold=0.2):
                return f"🔍 I understand you're looking for jobs! Please register first by sending *hi* and selecting your job interest."
            
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
        if not AI_AVAILABLE and not message_lower.isdigit() and not message_lower in ['balance', 'credits', 'account', 'refresh', 'new', 'reset']:
            # Check if this might be a job request using smart detection
            if SMART_JOB_DETECTION_AVAILABLE and is_smart_job_request(message, threshold=0.3):
                return f"🔍 I detected you're looking for jobs! To get started:\n\n1. Send *hi* to register\n2. Choose your job interest\n3. Add credits (1-30)\n4. Start receiving job alerts!\n\n💡 *Try*: Send *hi* to begin"
            
            # User might be trying to select an invalid category
            return f"🤖 Our AI advisors are busy now. Please try again in a few minutes.\n\nFor now, you can use our regular job features:\n\n{get_categories_menu()}"
        
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
                    return f"✅ *Credits Added Successfully!*\n\n💰 Added: *{credit_amount}* credits\n💳 Total Balance: *{new_balance}* credits\n🎯 Job Interest: *{user['interest']}*\n\n💡 Type *jobs* anytime to get job alerts!"
                else:
                    return "❌ Error adding credits. Please try again."
            else:
                return "❌ Please send a number between *1 and 30* to select your credits.\n\nExample: Send *5* to get 5 credits"
        
        # Handle balance check
        if message_lower in ['balance', 'credits', 'account']:
            if user:
                balance = user.get('balance', 0)
                if balance > 0:
                    return f"💳 *Account Balance:*\nCredits: *{balance}*\nJob Interest: *{user.get('interest', 'Not set')}*\n\n💡 Type *jobs* anytime to get job alerts!"
                else:
                    return f"💳 *Account Balance:*\nCredits: *{balance}*\nJob Interest: *{user.get('interest', 'Not set')}*\n\nSend a number (1-30) to add more credits!"
            else:
                return "❌ You're not registered yet. Send *hi* to get started!"
        
        # Handle refresh command to clear old job records
        if message_lower in ['refresh', 'new', 'reset']:
            if not user:
                return "❌ Please register first by sending *hi*"
            
            # Clear old job records
            db.clear_old_job_records(phone, days_old=0)  # Clear all records
            return f"🔄 *Job history refreshed!*\n\nAll previous job records cleared. You can now receive jobs again!\n\n💡 Type *jobs* anytime to get fresh job alerts."
        

        
        # Smart job request detection - enhanced with natural language understanding
        is_job_request = False
        job_confidence = 0.0
        
        # Check if this is a job request using smart detection (excluding explicit commands handled above)
        if SMART_JOB_DETECTION_AVAILABLE and message_lower not in ['jobs', 'job', 'work']:
            is_job_request, job_confidence, detection_reason = detect_job_request(message)
            if is_job_request:
                logger.info(f"🧠 Smart detection identified job request: {message[:50]} "
                           f"(confidence: {job_confidence:.2f}, reason: {detection_reason})")
        
        # Handle smart-detected job requests (but not explicit commands)
        if is_job_request and message_lower not in ['jobs', 'job', 'work']:
            if not user:
                return f"🔍 I detected you're looking for jobs! To get started:\n\n1. Send *hi* to register\n2. Choose your job interest\n3. Add credits (1-30)\n4. Start receiving job alerts!\n\n💡 *Try*: Send *hi* to begin"
            
            if not user.get('interest'):
                return f"🔍 I detected you're looking for jobs! Please set your job interest first. Send *hi* to see options."
            
            if user['balance'] <= 0:
                return f"🔍 I detected you're looking for jobs! You need credits first.\n\n💰 *Add credits:*\nSend a number from *1 to 30* to get that many credits.\n\nExample: Send *5* to get 5 credits"
            
            # For smart-detected requests, redirect to explicit command
            return f"🔍 I detected you're looking for jobs! Send *jobs* to get your job alerts."
        
        # AI-powered default response
        if AI_AVAILABLE:
            # Let AI handle unrecognized messages
            ai_response = ask_deepseek(f"User sent: '{message}'. This is a WhatsApp job alert bot. Provide a helpful response and guide them to available commands.")
            return ai_response["content"]
        
        # Standard default response (when AI is not available)
        return """🤖 Our AI advisors are busy now. Please try again in a few minutes.

For now, you can use these commands:
• Send *hi* to get started
• Send *jobs* to get job alerts
• Send *balance* to check credits
• Send *refresh* to reset job history
• Send *1-30* to add credits

Try one of these commands!"""
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {str(e)}")
        return "❌ Sorry, there was an error. Please try again later." 