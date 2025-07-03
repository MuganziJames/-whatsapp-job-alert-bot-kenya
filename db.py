"""
Supabase database functions for WhatsApp Job Alert Bot
Enhanced with AI conversation tracking and analytics
Handles user data management and job tracking
"""

import os
from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import logging
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

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
    
    # AI-Enhanced Features
    
    def log_ai_interaction(self, phone: str, user_message: str, ai_response: str, interaction_type: str = 'general') -> bool:
        """Log AI interactions for analytics and improvement"""
        try:
            # Match the actual table structure
            interaction_log = {
                'user-phone': phone,                    # Correct column name (with hyphen)
                'question': user_message[:500],         # Correct column name, truncate long messages
                'ai_response': ai_response[:1000],      # Truncate long responses
                'response_time_ms': 0,                  # Default value
                'model_used': 'deepseek/deepseek-r1:free',      # Default model
                'tokens_used': 0,                       # Default value
                'success': ai_response is not None,     # True if we got a response
                'error_message': None if ai_response else 'AI service unavailable'
            }
            
            response = self.supabase.table('ai_interactions').insert(interaction_log).execute()
            logger.info(f"Logged AI interaction for {phone}")
            return True
        except Exception as e:
            logger.error(f"Could not log AI interaction: {str(e)}")
            return False
    
    def get_user_conversation_history(self, phone: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history for personalized responses"""
        try:
            response = self.supabase.table('ai_interactions').select('*').eq('user-phone', phone).order('created_at', desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            logger.debug(f"Could not get conversation history: {str(e)}")
            return []
    
    def update_user_preferences(self, phone: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences based on AI interactions"""
        try:
            user = self.get_user_by_phone(phone)
            if user:
                # Store preferences as JSON string
                preferences_json = json.dumps(preferences)
                response = self.supabase.table('users').update({'preferences': preferences_json}).eq('phone', phone).execute()
                logger.info(f"Updated preferences for {phone}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating preferences for {phone}: {str(e)}")
            return False
    
    def get_user_preferences(self, phone: str) -> Dict[str, Any]:
        """Get user preferences"""
        try:
            user = self.get_user_by_phone(phone)
            if user and user.get('preferences'):
                return json.loads(user['preferences'])
            return {}
        except Exception as e:
            logger.error(f"Error getting preferences for {phone}: {str(e)}")
            return {}
    
    def get_ai_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get AI usage analytics"""
        try:
            # Get interactions from the last N days
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            response = self.supabase.table('ai_interactions').select('*').gte('created_at', since_date).execute()
            interactions = response.data
            
            if not interactions:
                return {'total_interactions': 0, 'unique_users': 0, 'interaction_types': {}}
            
            # Analyze interactions
            unique_users = set()
            interaction_types = {}
            
            for interaction in interactions:
                unique_users.add(interaction['user-phone'])
                # Since we don't have interaction_type column, categorize by success
                interaction_type = 'success' if interaction.get('success') else 'error'
                interaction_types[interaction_type] = interaction_types.get(interaction_type, 0) + 1
            
            return {
                'total_interactions': len(interactions),
                'unique_users': len(unique_users),
                'interaction_types': interaction_types,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting AI analytics: {str(e)}")
            return {'error': str(e)}
    
    def log_job_ai_analysis(self, job_id: str, analysis: Dict[str, Any]) -> bool:
        """Log AI analysis of jobs for improvement"""
        try:
            analysis_log = {
                'job_id': job_id,
                'match_score': analysis.get('match_score', 0),
                'quality_score': analysis.get('quality_score', 0),
                'should_send': analysis.get('should_send', False),
                'analysis_text': analysis.get('analysis', '')[:500],
                'created_at': datetime.now().isoformat()
            }
            
            response = self.supabase.table('job_ai_analysis').insert(analysis_log).execute()
            logger.debug(f"Logged AI analysis for job {job_id}")
            return True
        except Exception as e:
            logger.debug(f"Could not log job AI analysis: {str(e)}")
            return False
    
    def get_job_performance_stats(self, interest: str, days: int = 30) -> Dict[str, Any]:
        """Get job performance statistics"""
        try:
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get jobs sent for this interest
            jobs_sent_response = self.supabase.table('jobs_sent').select('*').gte('sent_at', since_date).execute()
            
            # Get users with this interest
            users_response = self.supabase.table('users').select('*').eq('interest', interest).execute()
            
            return {
                'jobs_sent': len(jobs_sent_response.data) if jobs_sent_response.data else 0,
                'active_users': len(users_response.data) if users_response.data else 0,
                'interest': interest,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting job performance stats: {str(e)}")
            return {'error': str(e)}

# Initialize database manager
db = DatabaseManager() 