"""
Job scheduler for automatic job alerts
Sends job alerts to users with balance > 0 every X minutes
"""

import time
import logging
from threading import Thread
from typing import List, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_scheduled_job_alerts():
    """Send job alerts to all eligible users"""
    try:
        from db import db
        from scraper import scrape_jobs
        from bot import send_whatsapp_message
        
        logger.info("Starting scheduled job alert process...")
        
        # Get all users with balance > 0
        users_with_balance = []
        
        # Get users for each job interest
        interests = ['fundi', 'cleaner', 'tutor', 'driver', 'security']
        
        for interest in interests:
            users = db.get_users_by_interest(interest)
            users_with_balance.extend(users)
        
        if not users_with_balance:
            logger.info("No users with balance found")
            return
        
        logger.info(f"Found {len(users_with_balance)} users with balance")
        
        # Process each user
        alerts_sent = 0
        
        for user in users_with_balance:
            try:
                phone = user['phone']
                interest = user['interest']
                balance = user['balance']
                
                if balance <= 0:
                    continue
                
                # Get jobs for this interest
                jobs = scrape_jobs(interest)
                
                if not jobs:
                    logger.info(f"No jobs found for {interest}")
                    continue
                
                # Send first available job that hasn't been sent
                job_sent = False
                
                for job in jobs:
                    if not db.was_job_sent(phone, job['id']):
                        # Send the job
                        message = f"""🔔 *Scheduled Job Alert - {interest.title()}*

📋 *{job['title']}*
🔗 {job['link']}
📍 {job.get('location', 'Kenya')}

💰 1 credit used
💳 Remaining: {balance - 1}

Apply now! 🚀"""
                        
                        if send_whatsapp_message(phone, message):
                            # Deduct credit and log
                            if db.deduct_credit(phone):
                                db.log_job_sent(phone, job['id'], job['title'], job['link'])
                                alerts_sent += 1
                                job_sent = True
                                logger.info(f"Sent job alert to {phone}")
                                break
                
                if not job_sent:
                    logger.info(f"No new jobs to send to {phone}")
                    
                # Small delay between users
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing user {user.get('phone', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"Scheduled job alert process completed. Sent {alerts_sent} alerts.")
        
    except Exception as e:
        logger.error(f"Error in scheduled job alerts: {str(e)}")

class JobScheduler:
    def __init__(self, interval_minutes: int = 60):
        """Initialize job scheduler"""
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()
        self.running = False
    
    def start(self):
        """Start the job scheduler"""
        try:
            if not self.running:
                # Schedule job alerts
                self.scheduler.add_job(
                    send_scheduled_job_alerts,
                    'interval',
                    minutes=self.interval_minutes,
                    id='job_alerts'
                )
                
                self.scheduler.start()
                self.running = True
                
                logger.info(f"Job scheduler started - running every {self.interval_minutes} minutes")
            else:
                logger.warning("Scheduler is already running")
                
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
    
    def stop(self):
        """Stop the job scheduler"""
        try:
            if self.running:
                self.scheduler.shutdown()
                self.running = False
                logger.info("Job scheduler stopped")
            else:
                logger.warning("Scheduler is not running")
                
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
    
    def run_once(self):
        """Run job alerts once manually"""
        logger.info("Running job alerts manually...")
        send_scheduled_job_alerts()

# Initialize global scheduler
job_scheduler = JobScheduler(interval_minutes=60)

def start_job_scheduler():
    """Start the job scheduler"""
    job_scheduler.start()

def stop_job_scheduler():
    """Stop the job scheduler"""
    job_scheduler.stop()

def run_job_alerts_once():
    """Run job alerts once"""
    job_scheduler.run_once() 