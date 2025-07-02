"""
Supabase database functions for WhatsApp Job Alert Bot
Handles user data management and job tracking
"""

import os
from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(self.url, self.key)
    
    def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get user by phone number"""
        try:
            response = self.supabase.table('users').select('*').eq('phone', phone).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user by phone {phone}: {str(e)}")
            return None
    
    def add_or_update_user(self, phone: str, interest: str = None, balance: int = None) -> Optional[Dict[str, Any]]:
        """Add new user or update existing user"""
        try:
            existing_user = self.get_user_by_phone(phone)
            
            if existing_user:
                # Update existing user
                update_data = {}
                if interest is not None:
                    update_data['interest'] = interest
                if balance is not None:
                    update_data['balance'] = existing_user['balance'] + balance
                
                if update_data:
                    response = self.supabase.table('users').update(update_data).eq('phone', phone).execute()
                    return response.data[0] if response.data else None
                return existing_user
            else:
                # Create new user
                user_data = {
                    'phone': phone,
                    'interest': interest or '',
                    'balance': balance or 0
                }
                response = self.supabase.table('users').insert(user_data).execute()
                return response.data[0] if response.data else None
                
        except Exception as e:
            logger.error(f"Error adding/updating user {phone}: {str(e)}")
            return None
    
    def add_balance(self, phone: str, amount: int) -> bool:
        """Add balance to user account"""
        try:
            user = self.get_user_by_phone(phone)
            if user:
                new_balance = user['balance'] + amount
                response = self.supabase.table('users').update({'balance': new_balance}).eq('phone', phone).execute()
                logger.info(f"Added {amount} credits to {phone}. New balance: {new_balance}")
                return True
            else:
                # Create new user with balance
                self.add_or_update_user(phone, balance=amount)
                logger.info(f"Created new user {phone} with {amount} credits")
                return True
        except Exception as e:
            logger.error(f"Error adding balance to {phone}: {str(e)}")
            return False
    
    def deduct_credit(self, phone: str) -> bool:
        """Deduct 1 credit from user balance"""
        try:
            user = self.get_user_by_phone(phone)
            if user and user['balance'] > 0:
                new_balance = user['balance'] - 1
                response = self.supabase.table('users').update({'balance': new_balance}).eq('phone', phone).execute()
                logger.info(f"Deducted 1 credit from {phone}. New balance: {new_balance}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deducting credit from {phone}: {str(e)}")
            return False
    
    def has_sufficient_balance(self, phone: str) -> bool:
        """Check if user has sufficient balance"""
        try:
            user = self.get_user_by_phone(phone)
            return user and user['balance'] > 0
        except Exception as e:
            logger.error(f"Error checking balance for {phone}: {str(e)}")
            return False
    
    def log_job_sent(self, phone: str, job_id: str, job_title: str = None, job_url: str = None) -> bool:
        """Log that a job was sent to prevent duplicates"""
        try:
            # Use only essential fields for job deduplication
            job_log = {
                'phone': phone,
                'job_id': job_id
            }
            
            response = self.supabase.table('jobs_sent').insert(job_log).execute()
            logger.info(f"Successfully logged job {job_id} sent to {phone}")
            return True
        except Exception as e:
            logger.error(f"Error logging job sent to {phone}: {str(e)}")
            return False
    
    def was_job_sent(self, phone: str, job_id: str) -> bool:
        """Check if job was already sent to user"""
        try:
            response = self.supabase.table('jobs_sent').select('*').eq('phone', phone).eq('job_id', job_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error checking if job was sent to {phone}: {str(e)}")
            return False
    
    def clear_old_job_records(self, phone: str, days_old: int = 7) -> bool:
        """Clear job records to allow re-sending jobs"""
        try:
            if days_old == 0:
                # Clear all records for this user
                response = self.supabase.table('jobs_sent').delete().eq('phone', phone).execute()
            else:
                # Since sent_at column may not exist, just clear all for now
                # In production, you'd want to add the sent_at column
                response = self.supabase.table('jobs_sent').delete().eq('phone', phone).execute()
            
            deleted_count = len(response.data) if response.data else 0
            logger.info(f"Cleared {deleted_count} job records for {phone}")
            
            return True
        except Exception as e:
            logger.error(f"Error clearing job records for {phone}: {str(e)}")
            return False
    
    def get_users_by_interest(self, interest: str) -> List[Dict[str, Any]]:
        """Get all users with specific interest and balance > 0"""
        try:
            response = self.supabase.table('users').select('*').eq('interest', interest).gt('balance', 0).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting users by interest {interest}: {str(e)}")
            return []

# Initialize database manager
db = DatabaseManager() 