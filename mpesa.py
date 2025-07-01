"""
M-Pesa Daraja C2B payment integration
Handles validation and confirmation for Kenya Job Alert Bot
"""

import os
import requests
import base64
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MpesaC2B:
    def __init__(self):
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
        self.shortcode = os.getenv('MPESA_SHORTCODE', '600000')
        self.environment = os.getenv('MPESA_ENV', 'sandbox')
        
        # Set base URL
        if self.environment == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
    
    def get_access_token(self) -> str:
        """Get OAuth access token"""
        try:
            credentials = base64.b64encode(
                f"{self.consumer_key}:{self.consumer_secret}".encode()
            ).decode()
            
            headers = {
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['access_token']
            else:
                logger.error(f"Failed to get token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None
    
    def register_urls(self, validation_url: str, confirmation_url: str) -> bool:
        """Register C2B URLs with Daraja"""
        try:
            token = self.get_access_token()
            if not token:
                return False
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "ShortCode": self.shortcode,
                "ResponseType": "Completed",
                "ConfirmationURL": confirmation_url,
                "ValidationURL": validation_url
            }
            
            response = requests.post(
                f"{self.base_url}/mpesa/c2b/v1/registerurl",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("C2B URLs registered successfully")
                return True
            else:
                logger.error(f"URL registration failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error registering URLs: {str(e)}")
            return False

def normalize_phone_number(phone: str) -> str:
    """Normalize phone number for Kenya"""
    # Remove any non-digit characters except +
    phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Handle Kenyan phone numbers
    if phone.startswith('+254'):
        return phone
    elif phone.startswith('254'):
        return f'+{phone}'
    elif phone.startswith('0'):
        return f'+254{phone[1:]}'
    elif len(phone) == 9:
        return f'+254{phone}'
    
    return phone

def validate_payment(data: Dict[str, Any]) -> Dict[str, str]:
    """C2B payment validation - always accept"""
    try:
        amount = data.get('TransAmount', 0)
        phone = data.get('MSISDN', '')
        
        logger.info(f"Validating payment: Amount={amount}, Phone={phone}")
        
        # Always return success (ResultCode: 0)
        return {
            "ResultCode": "0",
            "ResultDesc": "Accepted"
        }
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            "ResultCode": "0",
            "ResultDesc": "Accepted"
        }

def process_confirmation(data: Dict[str, Any]) -> Dict[str, str]:
    """Process C2B payment confirmation"""
    try:
        # Extract payment details
        trans_id = data.get('TransID', '')
        amount = float(data.get('TransAmount', 0))
        phone = data.get('MSISDN', '')
        bill_ref = data.get('BillRefNumber', '')
        
        logger.info(f"Processing confirmation: TransID={trans_id}, Amount={amount}, Phone={phone}")
        
        # Normalize phone number
        normalized_phone = normalize_phone_number(phone)
        
        if amount > 0 and normalized_phone:
            # Add credits to user account
            from db import db
            from bot import send_whatsapp_message
            
            # 1 KES = 1 credit
            credits = int(amount)
            
            # Add balance to user account
            success = db.add_balance(normalized_phone, credits)
            
            if success:
                # Send confirmation message
                message = f"✅ *Payment Confirmed!*\n\n💰 {credits} job alert credits added to your account.\n\nSend *jobs* to receive alerts!"
                send_whatsapp_message(normalized_phone, message)
                
                logger.info(f"Added {credits} credits to {normalized_phone}")
                
                return {
                    "ResultCode": "0",
                    "ResultDesc": "Payment processed successfully"
                }
            else:
                logger.error(f"Failed to add credits for {normalized_phone}")
                return {
                    "ResultCode": "1",
                    "ResultDesc": "Failed to process payment"
                }
        else:
            logger.error(f"Invalid payment data: amount={amount}, phone={normalized_phone}")
            return {
                "ResultCode": "1",
                "ResultDesc": "Invalid payment data"
            }
            
    except Exception as e:
        logger.error(f"Confirmation processing error: {str(e)}")
        return {
            "ResultCode": "1",
            "ResultDesc": "Processing error"
        }

# Initialize M-Pesa client
mpesa_client = MpesaC2B() 