"""
Main Flask application for WhatsApp Job Alert Bot
Handles webhooks for WhatsApp messages (M-Pesa removed)
"""

from flask import Flask, request, jsonify, Response
import os
from dotenv import load_dotenv
import logging
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

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'active',
        'service': 'WhatsApp Job Alert Bot',
        'version': '2.0.0 - Credit Selection System'
    })

@app.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages from Twilio"""
    try:
        # Get message data from Twilio
        from_number = request.form.get('From', '')
        message_body = request.form.get('Body', '')
        
        logger.info(f"Received WhatsApp message from {from_number}: {message_body}")
        
        # Process the message and get response
        response_message = process_whatsapp_message(from_number, message_body)
        
        # Send the response back to the user via Twilio
        if response_message:
            send_whatsapp_message(from_number, response_message)
        
        # Return empty 200 response to Twilio webhook
        return Response('', status=200, mimetype='text/plain')
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
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

if __name__ == '__main__':
    # Start the job scheduler
    start_job_scheduler()
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting WhatsApp Job Alert Bot on port {port}")
    logger.info("Job scheduler started - will run every 60 minutes")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode) 