"""
Telegram bot for Kenya Job Alert Bot
Matches WhatsApp bot functionality exactly
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Telegram bot token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# Import shared modules
try:
    from scraper import scrape_jobs
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

# Valid job categories - same as WhatsApp bot
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
    """Get formatted categories menu - same as WhatsApp bot"""
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

def normalize_category(user_input: str) -> str:
    """Normalize user input to match valid categories - same as WhatsApp bot"""
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

def has_job_been_sent(user_id: str, job_id: str) -> bool:
    """Helper function to check if job has already been sent to user"""
    try:
        from db import db
        return db.was_job_sent(user_id, job_id)
    except Exception as e:
        logger.error(f"Error checking job sent status: {e}")
        return False

def process_telegram_message(user_id: str, username: str, message_body: str) -> str:
    """Process incoming Telegram message - same logic as WhatsApp bot"""
    try:
        # Database connection check
        try:
            from db import db
        except ImportError:
            logger.error("Failed to import database module")
            return "❌ System error: Database connection failed. Please try again later."
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            return "❌ System error: Database connection failed. Please try again later."
        
        message = message_body.strip()
        message_lower = message.lower()
        
        logger.info(f"Processing message from {user_id} (@{username}): {message}")
        
        # Check if user exists - using dual platform support
        user = None
        try:
            user = db.get_user(user_id)
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return "❌ System error: Unable to retrieve user information. Please try again later."
        
        # AI-powered career question detection (with rate limiting protection)
        if AI_AVAILABLE:
            try:
                is_career = is_career_question(message)
                if is_career:
                    logger.info(f"🤖 AI detected career question: {message}")
                    
                    # Get user context for personalized response
                    user_context = {
                        'user_info': user if user else {},
                        'available_categories': VALID_JOB_CATEGORIES
                    }
                    
                    # Get AI response with fallback handling
                    ai_response = ask_deepseek(message, user_context)
                    
                    # Check if AI suggests a job category (only if not rate limited)
                    if "daily AI limit" not in ai_response["content"]:
                        try:
                            suggested_interest = extract_job_interest(message)
                            if suggested_interest:
                                # Add category suggestion to response
                                ai_response["content"] += f"\n\n💡 Based on your question, you might be interested in *{suggested_interest.title()}* jobs. Send *{suggested_interest}* to set this as your interest!"
                        except Exception as e:
                            logger.warning(f"Non-critical error extracting job interest: {e}")
                    
                    # Log AI interaction
                    try:
                        db.log_ai_interaction(user_id, message, ai_response["content"], 'career_question')
                    except Exception as e:
                        logger.error(f"Error logging AI interaction: {e}")
                    
                    return ai_response["content"]
            except Exception as e:
                logger.error(f"Error in AI career question processing: {e}")
                # Fall through to normal processing
        
        # AI-powered job category recommendation
        if AI_AVAILABLE and any(phrase in message_lower for phrase in ['help me choose', 'which job', 'what should i', 'recommend', 'suggest']):
            logger.info(f"🤖 AI providing job category recommendation")
            
            recommendation = get_job_category_recommendation(message)
            
            if recommendation["category"]:
                # Add quick action to set the recommended category
                recommendation["explanation"] += f"\n\n🎯 Ready to get started? Send *{recommendation['category']}* to set this as your job interest!"
            
            # Log AI interaction
            try:
                db.log_ai_interaction(user_id, message, recommendation["explanation"], 'job_recommendation')
            except Exception as e:
                logger.error(f"Error logging AI interaction: {e}")
            
            return recommendation["explanation"]

        # Handle "hi" greeting with AI enhancement
        if message_lower in ['hi', 'hello', 'start', 'help', '/start']:
            base_menu = get_categories_menu()
        
            if AI_AVAILABLE and user and user.get('interests'):
                # Get first interest for display
                interest = user['interests'][0] if user['interests'] else None
                if interest:
                    return f"👋 Welcome back! You're currently interested in *{interest.title()}* jobs.\n\n{base_menu}\n\n💡 *Tip:* You can also ask me questions like 'What does a data analyst do?' or 'Help me choose a career path!'"
            
            # Enhanced greeting for new users (menu already includes AI help text)
            return base_menu
        
        # Handle job interests with AI validation
        if is_valid_category(message_lower):
            # Normalize the category
            normalized_category = normalize_category(message_lower)
            
            # Save user interest
            if user:
                # Update existing user
                current_interests = user.get('interests', [])
                if normalized_category in current_interests:
                    current_balance = user.get('balance', 0)
                    if current_balance > 0:
                        return f"✅ You already have *{normalized_category.title()}* jobs set as your interest.\n\n💳 Current Balance: *{current_balance}* credits\n\nSend *jobs* to get job alerts!"
                    else:
                        return f"✅ You already have *{normalized_category.title()}* jobs set as your interest.\n\n💰 *Choose your credits:*\nSend a number from *1 to 30* to get that many job alert credits.\n\nExample: Send *5* to get 5 credits"
                else:
                    # Set new interest
                    try:
                        db.set_user_interests(user_id, [normalized_category])
                        # Get updated user data
                        updated_user = db.get_user(user_id)
                        current_balance = updated_user.get('balance', 0) if updated_user else 0
                        
                        if current_balance > 0:
                            return f"✅ Interest updated to *{normalized_category.title()}* jobs!\n\n💳 Current Balance: *{current_balance}* credits\n\nSend *jobs* to get job alerts!"
                        else:
                            return f"✅ Interest updated to *{normalized_category.title()}* jobs!\n\n💰 *Choose your credits:*\nSend a number from *1 to 30* to get that many job alert credits.\n\nExample: Send *10* to get 10 credits"
                    except Exception as e:
                        logger.error(f"Error setting user interests: {e}")
                        return "❌ Error saving your interest. Please try again."
            else:
                # Create new user and check if they have credits
                try:
                    db.add_user(user_id, platform="telegram", username=username)
                    db.set_user_interests(user_id, [normalized_category])
                    # Get fresh user data to check current balance
                    fresh_user = db.get_user(user_id)
                    current_balance = fresh_user.get('balance', 0) if fresh_user else 0
                    
                    if current_balance > 0:
                        return f"✅ Great! You're now registered for *{normalized_category.title()}* job alerts.\n\n💳 Current Balance: *{current_balance}* credits\n\nSend *jobs* to get job alerts!"
                    else:
                        return f"✅ Great! You're now registered for *{normalized_category.title()}* job alerts.\n\n💰 *Choose your credits:*\nSend a number from *1 to 30* to get that many job alert credits.\n\nExample: Send *5* to get 5 credits"
                except Exception as e:
                    logger.error(f"Error creating user: {e}")
                    return "❌ Error registering. Please try again."
        
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
            return f"🤖 Our AI advisors are busy now. Please try again in a few minutes.\n\nFor now, you can use our regular job features:\n\n{get_categories_menu()}"
        
        # Handle credit selection (1-30)
        if message_lower.isdigit():
            credit_amount = int(message_lower)
            if 1 <= credit_amount <= 30:
                if not user:
                    return "❌ Please register first by sending *hi* and selecting your job interest."
                
                user_interests = user.get('interests', [])
                if not user_interests:
                    return "❌ Please set your job interest first. Send *hi* to see options."
                
                # Add credits to user account
                try:
                    success = db.add_balance(user_id, credit_amount)
                    
                    if success:
                        current_balance = user.get('balance', 0)
                        new_balance = current_balance + credit_amount
                        interest = user_interests[0] if user_interests else "Not set"
                        return f"✅ *Credits Added Successfully!*\n\n💰 Added: *{credit_amount}* credits\n💳 Total Balance: *{new_balance}* credits\n🎯 Job Interest: *{interest}*\n\nSend *jobs* to start receiving job alerts!"
                    else:
                        return "❌ Error adding credits. Please try again."
                except Exception as e:
                    logger.error(f"Error adding credits: {e}")
                    return "❌ Error adding credits. Please try again."
            else:
                return "❌ Please send a number between *1 and 30* to select your credits.\n\nExample: Send *5* to get 5 credits"
        
        # Handle balance check
        if message_lower in ['balance', 'credits', 'account', '/balance']:
            if user:
                interests = user.get('interests', [])
                interest_text = interests[0] if interests else 'Not set'
                balance = user.get('balance', 0)
                if balance > 0:
                    return f"💳 *Account Balance:*\nCredits: *{balance}*\nJob Interest: *{interest_text}*\n\nSend *jobs* to get job alerts!"
                else:
                    return f"💳 *Account Balance:*\nCredits: *{balance}*\nJob Interest: *{interest_text}*\n\nSend a number (1-30) to add more credits!"
            else:
                return "❌ You're not registered yet. Send *hi* to get started!"
        
        # Handle refresh command to clear old job records
        if message_lower in ['refresh', 'new', 'reset']:
            if not user:
                return "❌ Please register first by sending *hi*"
            
            # Clear old job records
            try:
                db.clear_old_job_records(user_id, days_old=0)  # Clear all records
                return f"🔄 *Job history refreshed!*\n\nAll previous job records cleared. You can now receive jobs again!\n\nSend *jobs* to get fresh job alerts."
            except Exception as e:
                logger.error(f"Error clearing job records: {e}")
                return "❌ Error refreshing job history. Please try again."
        
        # Handle job request with AI enhancement
        if message_lower in ['jobs', 'job', 'work', '/jobs']:
            if not user:
                return "❌ Please register first by sending *hi*"
            
            user_interests = user.get('interests', [])
            if not user_interests:
                return "❌ Please set your job interest first. Send *hi* to see options."
            
            if user.get('balance', 0) <= 0:
                return f"❌ No credits available!\n\n💰 *Add credits:*\nSend a number from *1 to 30* to get that many credits.\n\nExample: Send *5* to get 5 credits"
            
            # Get and send job
            interest = user_interests[0]  # Use first interest
            jobs = scrape_jobs(interest)
            
            if not jobs:
                return f"😔 No new *{interest}* jobs available right now. We'll keep looking!"
            
            # Basic job filtering (AI disabled to preserve rate limits)
            logger.info(f"📋 Basic filtering {len(jobs)} jobs for {interest}")
            
            # Simple filtering - just check if job hasn't been sent
            filtered_jobs = []
            for job in jobs:
                if not has_job_been_sent(user_id, job['id']):
                    filtered_jobs.append(job)
            
            jobs = filtered_jobs
            
            # Find first job that hasn't been sent
            job_to_send = None
            for job in jobs:
                if not has_job_been_sent(user_id, job['id']):
                    job_to_send = job
                    break
            
            # Check if we found a new job
            if not job_to_send:
                return f"🔍 All current *{interest}* jobs have been sent to you!\n\n💡 *What you can do:*\n• Try a different job category (send *hi*)\n• Send *refresh* to reset your job history\n• Check back in a few hours for new jobs\n• Send *balance* to see your credits\n\n🔄 New jobs are added regularly!"
            
            # Deduct credit and send job
            try:
                if db.deduct_credit(user_id):
                    # Log the job as sent
                    db.log_job_sent(user_id, job_to_send['id'], job_to_send['title'], job_to_send['link'])
                    
                    # Generate personalized message using AI
                    if AI_AVAILABLE:
                        try:
                            personalized_message = generate_personalized_message(job_to_send, user)
                            return personalized_message
                        except Exception as e:
                            logger.error(f"Error generating personalized message: {str(e)}")
                            # Fall back to standard message
                    
                    # Standard job message (fallback)
                    job_message = f"""🎯 *New {interest.title()} Job Alert:*

📋 *{job_to_send['title']}*
🏢 Company: {job_to_send.get('company', 'Not specified')}
📍 Location: {job_to_send.get('location', 'Kenya')}
🔗 {job_to_send['link']}
🌐 Source: {job_to_send.get('source', 'Job Board')}

💰 Credit used: 1
💳 Remaining: {user.get('balance', 0) - 1}

Good luck! 🍀"""
                    return job_message
                else:
                    return "❌ Error processing your request. Please try again."
            except Exception as e:
                logger.error(f"Error processing job request: {e}")
                return "❌ Error processing your request. Please try again."
        
        # AI-powered default response
        if AI_AVAILABLE:
            # Let AI handle unrecognized messages
            try:
                ai_response = ask_deepseek(f"User sent: '{message}'. This is a Telegram job alert bot. Provide a helpful response and guide them to available commands.")
                return ai_response["content"]
            except Exception as e:
                logger.error(f"Error in AI response: {e}")
        
        # Standard default response (when AI is not available)
        return """🤖 I'm not sure how to help with that.
Send /menu or ask a career question!

For now, you can use these commands:
• Send *hi* to get started
• Send *jobs* to get job alerts
• Send *balance* to check credits
• Send *refresh* to reset job history
• Send *1-30* to add credits

Try one of these commands!"""
        
    except Exception as e:
        logger.error(f"Critical error in process_telegram_message: {str(e)}", exc_info=True)
        return "❌ Sorry, there was a system error. Please try again later."

# ----------------------------------------------------------------------------
# Telegram handlers

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "user"
    
    response = process_telegram_message(user_id, username, "/start")
    
    # Handle Markdown safely
    try:
        await update.message.reply_markdown(response)
    except Exception as e:
        logger.error(f"Failed to send /start response with markdown: {e}")
        # Fallback to plain text if markdown fails
        await update.message.reply_text(
            f"{response}\n\n(Note: Some formatting was removed for compatibility)"
        )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "user"
    
    response = process_telegram_message(user_id, username, "help")
    
    # Handle Markdown safely
    try:
        await update.message.reply_markdown(response)
    except Exception as e:
        logger.error(f"Failed to send /help response with markdown: {e}")
        # Fallback to plain text if markdown fails
        await update.message.reply_text(
            f"{response}\n\n(Note: Some formatting was removed for compatibility)"
        )

async def jobs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /jobs command"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "user"
    
    response = process_telegram_message(user_id, username, "jobs")
    
    # Handle Markdown safely
    try:
        await update.message.reply_markdown(response, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Failed to send /jobs response with markdown: {e}")
        # Fallback to plain text if markdown fails
        await update.message.reply_text(
            f"{response}\n\n(Note: Some formatting was removed for compatibility)",
            disable_web_page_preview=True
        )

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /balance command"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "user"
    
    response = process_telegram_message(user_id, username, "balance")
    
    # Handle Markdown safely
    try:
        await update.message.reply_markdown(response)
    except Exception as e:
        logger.error(f"Failed to send /balance response with markdown: {e}")
        # Fallback to plain text if markdown fails
        await update.message.reply_text(
            f"{response}\n\n(Note: Some formatting was removed for compatibility)"
        )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all text messages"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "user"
    message = update.message.text
    
    response = process_telegram_message(user_id, username, message)
    
    # Handle Markdown safely
    try:
        await update.message.reply_markdown(response, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Failed to send response with markdown: {e}")
        # Fallback to plain text if markdown fails
        await update.message.reply_text(
            f"{response}\n\n(Note: Some formatting was removed for compatibility)",
            disable_web_page_preview=True
        )

# ----------------------------------------------------------------------------
# Main entrypoint

def main() -> None:
    """Main entry point for the Telegram bot"""
    import asyncio
    
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info("Starting Ajirawise Telegram Bot …")
        app = Application.builder().token(TELEGRAM_TOKEN).build()
    
        # Commands
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_cmd))
        app.add_handler(CommandHandler("jobs", jobs_cmd))
        app.add_handler(CommandHandler("balance", balance_cmd))
    
        # Text messages
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
        # Start the bot
        logger.info("Starting polling...")
        # Disable signal handling since this may run in a background thread (Render starts Flask wrapper)
        app.run_polling(stop_signals=None)
    except Exception as e:
        logger.critical(f"Failed to start Telegram bot: {e}", exc_info=True)
        raise
    finally:
        # Clean up the event loop
        try:
            loop.close()
        except:
            pass

def run_web_server():
    """Run a simple web server for Render deployment"""
    import threading
    import os
    from flask import Flask, jsonify
    
    # Create Flask app
    flask_app = Flask(__name__)
    
    @flask_app.route('/')
    def health():
        return jsonify({
            'status': 'healthy',
            'service': 'Ajirawise Telegram Bot',
            'version': '2.0.0'
        })
    
    @flask_app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'Ajirawise Telegram Bot',
            'version': '2.0.0',
            'bot_running': True
        })
    
    # Start Telegram bot in a separate thread
    def start_telegram_bot():
        try:
            main()
        except Exception as e:
            logger.error(f"Telegram bot error: {e}")
    
    # Start the Telegram bot
    telegram_thread = threading.Thread(target=start_telegram_bot, daemon=True)
    telegram_thread.start()
    
    # Start Flask web server
    port = int(os.getenv('PORT', 10001))
    logger.info(f"Starting Telegram bot web server on port {port}")
    
    try:
        flask_app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Flask server error: {e}")
        raise

if __name__ == "__main__":
    import os
    # Check if we're running on Render (has PORT env var)
    if os.getenv('PORT'):
        run_web_server()
    else:
        main() 