"""
Main Flask application for WhatsApp Job Alert Bot
Handles webhooks for WhatsApp messages (M-Pesa removed)
"""

from flask import Flask, request, jsonify, Response
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from bot import process_whatsapp_message, send_whatsapp_message
from scheduler import start_job_scheduler, run_job_alerts_once

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    """Health check endpoint"""
    # If this is a POST request (likely a misrouted webhook), redirect to proper endpoint
    if request.method == 'POST':
        logger.warning("Received POST to / - redirecting to /whatsapp")
        return whatsapp_webhook()
    
    return jsonify({
        'status': 'active',
        'service': 'Ajirawise - Smart Job Alert Bot',
        'version': '2.0.0 - Credit Selection System'
    })

@app.route('/health')
def health_check():
    """Detailed health check endpoint for monitoring"""
    try:
        from db import db
        
        # Test database connection
        db.get_connection()
        
        return jsonify({
            'status': 'healthy',
            'service': 'Ajirawise - Smart Job Alert Bot',
            'version': '2.0.0',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'Ajirawise - Smart Job Alert Bot',
            'version': '2.0.0',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages from Twilio"""
    try:
        # Get message data from Twilio webhook (form data)
        from_number = request.form.get('From', '')
        message_body = request.form.get('Body', '')
        
        logger.info(f"📱 Received WhatsApp message from {from_number}: {message_body}")
        
        if not from_number or not message_body:
            logger.warning("Invalid webhook data - missing From or Body")
            return Response('', status=200, mimetype='text/plain')
        
        # Process the message and get response
        response_message = process_whatsapp_message(from_number, message_body)
        
        logger.info(f"💬 Generated response: {response_message}")
        
        # Send the response back to the user via Twilio
        if response_message:
            logger.info(f"📤 Sending response to {from_number}")
            send_whatsapp_message(from_number, response_message)
        else:
            logger.warning("No response message generated")
        
        # Return empty 200 response to Twilio webhook
        return Response('', status=200, mimetype='text/plain')
        
    except Exception as e:
        logger.error(f"❌ Error processing WhatsApp webhook: {str(e)}")
        import traceback
        logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
        return Response('', status=200, mimetype='text/plain')

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint for debugging"""
    try:
        from db import db
        
        # Test database connection
        test_phone = "+254700000000"
        user = db.get_user_by_phone(test_phone)
        
        return jsonify({
            'status': 'ok',
            'database': 'connected',
            'test_user': user,
            'system': 'Credit Selection System (M-Pesa Removed)'
        })
        
    except Exception as e:
        logger.error(f"Test endpoint error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/admin/broadcast', methods=['POST'])
def broadcast_jobs():
    """Admin endpoint to broadcast jobs to all users with specific interest"""
    try:
        data = request.get_json()
        interest = data.get('interest', '')
        
        if not interest:
            return jsonify({'error': 'Interest is required'}), 400
        
        from db import db
        from scraper import job_scraper
        from bot import send_whatsapp_message
        
        # Get users with this interest and balance > 0
        users = db.get_users_by_interest(interest)
        
        if not users:
            return jsonify({'message': f'No users found with interest: {interest}'}), 404
        
        # Get latest jobs
        jobs = job_scraper.search_jobs(interest, max_per_site=2)
        
        if not jobs:
            return jsonify({'message': f'No jobs found for: {interest}'}), 404
        
        # Send jobs to users
        sent_count = 0
        for user in users:
            try:
                phone = user['phone']
                
                # Send up to 2 jobs per user
                jobs_sent = 0
                for job in jobs[:2]:
                    if user['balance'] <= 0:
                        break
                    
                    if not db.was_job_sent(phone, job['id']):
                        # Deduct credit and send job
                        if db.deduct_credit(phone):
                            message = f"""🎯 *New {interest.title()} Job Alert:*

📋 *{job['title']}*
🏢 {job['company']}
🌐 {job['url']}
📍 Source: {job['source']}

Send 'JOBS' for more alerts!"""
                            
                            if send_whatsapp_message(phone, message):
                                db.log_job_sent(phone, job['id'], job['title'], job['url'])
                                jobs_sent += 1
                                user['balance'] -= 1
                
                if jobs_sent > 0:
                    sent_count += 1
                    
            except Exception as e:
                logger.error(f"Error sending to {user.get('phone', 'unknown')}: {str(e)}")
        
        return jsonify({
            'message': f'Broadcast completed for {interest}',
            'users_reached': sent_count,
            'total_users': len(users),
            'jobs_available': len(jobs)
        })
        
    except Exception as e:
        logger.error(f"Broadcast error: {str(e)}")
        return jsonify({'error': 'Broadcast failed'}), 500

@app.route('/admin/run-alerts', methods=['POST'])
def run_alerts_now():
    """Admin endpoint to run job alerts immediately"""
    try:
        run_job_alerts_once()
        return jsonify({'message': 'Job alerts executed successfully'})
    except Exception as e:
        logger.error(f"Error running alerts: {str(e)}")
        return jsonify({'error': 'Failed to run alerts'}), 500

@app.route('/admin/ai-analytics', methods=['GET'])
def get_ai_analytics():
    """Admin endpoint to get AI usage analytics"""
    try:
        from db import db
        
        days = request.args.get('days', 7, type=int)
        analytics = db.get_ai_analytics(days)
        
        return jsonify({
            'ai_analytics': analytics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting AI analytics: {str(e)}")
        return jsonify({'error': 'Failed to get AI analytics'}), 500

@app.route('/admin/job-stats', methods=['GET'])
def get_job_stats():
    """Admin endpoint to get job performance statistics"""
    try:
        from db import db
        
        interest = request.args.get('interest', 'all')
        days = request.args.get('days', 30, type=int)
        
        if interest == 'all':
            # Get stats for all interests
            interests = [
                'data entry', 'sales & marketing', 'delivery & logistics',
                'customer service', 'finance & accounting', 'admin & office work',
                'teaching / training', 'internships / attachments', 'software engineering'
            ]
            
            all_stats = {}
            for int_cat in interests:
                all_stats[int_cat] = db.get_job_performance_stats(int_cat, days)
            
            return jsonify({
                'job_stats': all_stats,
                'period_days': days,
                'timestamp': datetime.now().isoformat()
            })
        else:
            stats = db.get_job_performance_stats(interest, days)
            return jsonify({
                'job_stats': {interest: stats},
                'period_days': days,
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error getting job stats: {str(e)}")
        return jsonify({'error': 'Failed to get job stats'}), 500

@app.route('/admin/test-ai', methods=['POST'])
def test_ai():
    """Admin endpoint to test AI functionality"""
    try:
        data = request.get_json()
        test_message = data.get('message', 'What does a software developer do?')
        
        # Test AI helper
        try:
            from utils.ai_helper import ask_deepseek, AI_AVAILABLE
            
            if not AI_AVAILABLE:
                return jsonify({
                    'ai_available': False,
                    'message': 'AI helper not available'
                })
            
            response = ask_deepseek(test_message)
            
            return jsonify({
                'ai_available': True,
                'test_message': test_message,
                'ai_response': response,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as ai_error:
            return jsonify({
                'ai_available': False,
                'error': str(ai_error),
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error testing AI: {str(e)}")
        return jsonify({'error': 'Failed to test AI'}), 500

if __name__ == '__main__':
    # Start the job scheduler
    start_job_scheduler()
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Ajirawise - Smart Job Alert Bot on port {port}")
    logger.info("Job scheduler started - will run every 60 minutes")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode) 