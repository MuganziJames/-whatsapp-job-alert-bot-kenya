"""
Smart Job scheduler for automatic job alerts
- Sends job alerts every 5 minutes until 5 jobs are sent per user
- Then switches to 2-3 hour intervals for subsequent alerts
"""

import time
import logging
import random
from datetime import datetime, timedelta
from threading import Thread
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartJobScheduler:
    def __init__(self):
        """Initialize smart job scheduler"""
        self.scheduler = BackgroundScheduler()
        self.running = False
        self.user_job_counts = {}  # Track jobs sent per user today
        self.last_reset_date = datetime.now().date()
        
    def reset_daily_counts(self):
        """Reset job counts daily"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            logger.info("🗓️ Resetting daily job counts")
            self.user_job_counts = {}
            self.last_reset_date = today
    
    def get_user_job_count_today(self, phone: str) -> int:
        """Get number of jobs sent to user today"""
        self.reset_daily_counts()
        return self.user_job_counts.get(phone, 0)
    
    def increment_user_job_count(self, phone: str):
        """Increment job count for user"""
        self.reset_daily_counts()
        self.user_job_counts[phone] = self.user_job_counts.get(phone, 0) + 1
    
    def get_next_alert_interval(self, phone: str) -> int:
        """Get next alert interval in minutes based on jobs sent today"""
        job_count = self.get_user_job_count_today(phone)
        
        if job_count < 5:
            # First 5 jobs: every 5 minutes
            return 5
        else:
            # After 5 jobs: random interval between 2-3 hours (120-180 minutes)
            return random.randint(120, 180)
    
    def should_send_alert_to_user(self, phone: str) -> bool:
        """Check if we should send alert to this user based on timing"""
        try:
            from db import db
            
            # Get user's last job sent time
            last_job_time = db.get_last_job_sent_time(phone)
            
            if not last_job_time:
                # No jobs sent yet, can send
                logger.info(f"📅 User {phone}: No previous jobs sent - SENDING FIRST JOB")
                return True
            
            # Calculate time since last job
            time_since_last = datetime.now() - last_job_time
            minutes_since_last = time_since_last.total_seconds() / 60
            
            # Get required interval
            required_interval = self.get_next_alert_interval(phone)
            
            # Check if enough time has passed
            should_send = minutes_since_last >= required_interval
            
            if should_send:
                logger.info(f"📅 User {phone}: {minutes_since_last:.1f} min since last job (required: {required_interval} min) - SENDING")
            else:
                logger.info(f"⏰ User {phone}: {minutes_since_last:.1f} min since last job (required: {required_interval} min) - WAITING")
            
            return should_send
            
        except Exception as e:
            logger.error(f"Error checking timing for {phone}: {str(e)}")
            # If there's an error, allow sending (fail-safe)
            return True
    
    def start(self):
        """Start the smart job scheduler"""
        try:
            if not self.running:
                # Schedule job alerts to run every minute (we'll handle timing logic inside)
                self.scheduler.add_job(
                    send_smart_job_alerts,
                    'interval',
                    minutes=1,  # Check every minute, but smart logic controls actual sending
                    id='smart_job_alerts'
                )
                
                self.scheduler.start()
                self.running = True
                
                logger.info("🧠 Smart job scheduler started - checking every minute with intelligent timing")
            else:
                logger.warning("Scheduler is already running")
                
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
    
    def stop(self):
        """Stop the smart job scheduler"""
        try:
            if self.running:
                self.scheduler.shutdown()
                self.running = False
                logger.info("Smart job scheduler stopped")
            else:
                logger.warning("Scheduler is not running")
                
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
    
    def run_once(self):
        """Run job alerts once manually"""
        logger.info("Running smart job alerts manually...")
        send_smart_job_alerts()
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        self.reset_daily_counts()
        return {
            "total_users_tracked": len(self.user_job_counts),
            "jobs_sent_today": sum(self.user_job_counts.values()),
            "user_job_counts": self.user_job_counts.copy(),
            "last_reset_date": self.last_reset_date.isoformat()
        }

def send_smart_job_alerts():
    """Send job alerts with smart timing logic"""
    try:
        from db import db
        from scraper import scrape_jobs
        from bot import send_whatsapp_message
        from utils.ai_helper import generate_personalized_message, improve_job_matching, AI_AVAILABLE
        
        logger.info("🚀 Starting smart job alert process...")
        
        # Get all users with balance > 0
        users_with_balance = []
        
        # Get users for each job interest
        interests = [
            'data entry', 'sales & marketing', 'delivery & logistics',
            'customer service', 'finance & accounting', 'admin & office work',
            'teaching / training', 'internships / attachments', 'software engineering'
        ]
        
        for interest in interests:
            users = db.get_users_by_interest(interest)
            users_with_balance.extend(users)
        
        if not users_with_balance:
            logger.info("No users with balance found")
            return
        
        logger.info(f"Found {len(users_with_balance)} users with balance")
        
        # Process each user with smart timing
        alerts_sent = 0
        
        for user in users_with_balance:
            try:
                phone = user['phone']
                interest = user['interest']
                balance = user['balance']
                
                if balance <= 0:
                    continue
                
                # Check if we should send alert to this user based on timing
                if not smart_scheduler.should_send_alert_to_user(phone):
                    continue
                
                # Get jobs for this interest
                jobs = scrape_jobs(interest)
                
                if not jobs:
                    logger.info(f"No jobs found for {interest}")
                    continue
                
                # Basic job filtering (AI disabled to preserve rate limits)
                logger.info(f"📋 Basic filtering {len(jobs)} jobs for {interest}")
                
                # Simple filtering - just check if job hasn't been sent
                filtered_jobs = []
                for job in jobs:
                    if not db.was_job_sent(phone, job['id']):
                        filtered_jobs.append(job)
                
                jobs = filtered_jobs
                
                # Send first available job that hasn't been sent
                job_sent = False
                
                for job in jobs:
                    if not db.was_job_sent(phone, job['id']):
                        # Get current job count for timing info
                        current_count = smart_scheduler.get_user_job_count_today(phone)
                        next_interval = smart_scheduler.get_next_alert_interval(phone)
                        
                        # Use standard job message without AI interference
                        logger.info(f"📋 Sending standard job message for {interest}")
                        
                        # Standard job message
                        message = None
                        if not message:
                            timing_info = ""
                            if current_count < 4:  # Show timing info for first 5 jobs
                                timing_info = f"\n⏰ Next alert in ~{next_interval} minutes"
                            elif current_count == 4:  # Last quick alert
                                timing_info = f"\n⏰ Next alert in 2-3 hours"
                            else:
                                timing_info = f"\n⏰ Next alert in 2-3 hours"
                            
                            message = f"""🔔 *Smart Job Alert #{current_count + 1} - {interest.title()}*

📋 *{job['title']}*
🏢 Company: {job.get('company', 'Not specified')}
📍 Location: {job.get('location', 'Kenya')}
🔗 {job['link']}
🌐 Source: {job.get('source', 'Job Board')}

💰 1 credit used
💳 Remaining: {balance - 1}{timing_info}

Apply now! 🚀"""
                        
                        if send_whatsapp_message(phone, message):
                            # Deduct credit and log
                            if db.deduct_credit(phone):
                                db.log_job_sent(phone, job['id'], job['title'], job['link'])
                                smart_scheduler.increment_user_job_count(phone)
                                alerts_sent += 1
                                job_sent = True
                                
                                new_count = smart_scheduler.get_user_job_count_today(phone)
                                logger.info(f"✅ Sent job alert #{new_count} to {phone}")
                                break
                
                if not job_sent:
                    logger.info(f"No new jobs to send to {phone}")
                    
                # Small delay between users
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing user {user.get('phone', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"🎯 Smart job alert process completed. Sent {alerts_sent} alerts.")
        
    except Exception as e:
        logger.error(f"Error in smart job alerts: {str(e)}")

# Initialize global smart scheduler
smart_scheduler = SmartJobScheduler()

def start_smart_job_scheduler():
    """Start the smart job scheduler"""
    smart_scheduler.start()

def stop_smart_job_scheduler():
    """Stop the smart job scheduler"""
    smart_scheduler.stop()

def run_smart_job_alerts_once():
    """Run smart job alerts once"""
    smart_scheduler.run_once()

def get_scheduler_stats():
    """Get scheduler statistics"""
    return smart_scheduler.get_user_stats()

# Backwards compatibility
start_job_scheduler = start_smart_job_scheduler
stop_job_scheduler = stop_smart_job_scheduler
run_job_alerts_once = run_smart_job_alerts_once 