#!/usr/bin/env python3
"""
Test script for WhatsApp Job Alert Bot
Helps test the complete flow without needing actual WhatsApp/M-Pesa
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database():
    """Test database connectivity and operations"""
    print("🔍 Testing database operations...")
    
    try:
        from db import db
        
        # Test phone number
        test_phone = "+254700123456"
        
        # Test adding user
        user = db.add_or_update_user(test_phone, interest="fundi", balance=5)
        print(f"✅ Added test user: {user}")
        
        # Test getting user
        retrieved_user = db.get_user_by_phone(test_phone)
        print(f"✅ Retrieved user: {retrieved_user}")
        
        # Test balance operations
        db.add_balance(test_phone, 3)
        print("✅ Added 3 credits")
        
        db.deduct_credit(test_phone)
        print("✅ Deducted 1 credit")
        
        final_user = db.get_user_by_phone(test_phone)
        print(f"✅ Final user state: {final_user}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False

def test_scraping():
    """Test job scraping functionality"""
    print("\n🌐 Testing job scraping...")
    
    try:
        from scraper import scrape_jobs
        
        # Test each job interest
        interests = ['fundi', 'cleaner', 'tutor', 'driver', 'security']
        
        for interest in interests:
            jobs = scrape_jobs(interest)
            print(f"✅ {interest}: Found {len(jobs)} jobs")
            
            if jobs:
                print(f"   Sample: {jobs[0]['title']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scraping test failed: {str(e)}")
        return False

def test_whatsapp_bot():
    """Test WhatsApp bot logic"""
    print("\n📱 Testing WhatsApp bot...")
    
    try:
        from bot import process_whatsapp_message
        
        test_phone = "+254700123456"
        
        # Test conversation flow
        responses = []
        
        # Test greeting
        response1 = process_whatsapp_message(test_phone, "hi")
        responses.append(("hi", response1))
        
        # Test job interest selection
        response2 = process_whatsapp_message(test_phone, "fundi")
        responses.append(("fundi", response2))
        
        # Test balance check
        response3 = process_whatsapp_message(test_phone, "balance")
        responses.append(("balance", response3))
        
        # Test job request
        response4 = process_whatsapp_message(test_phone, "jobs")
        responses.append(("jobs", response4))
        
        for command, response in responses:
            print(f"✅ '{command}' -> {response[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ WhatsApp bot test failed: {str(e)}")
        return False

def test_mpesa():
    """Test M-Pesa functionality"""
    print("\n💰 Testing M-Pesa functionality...")
    
    try:
        from mpesa import validate_payment, process_confirmation
        
        # Test validation
        validation_data = {
            'TransAmount': 50,
            'MSISDN': '254700123456',
            'BillRefNumber': 'TEST123'
        }
        
        validation_response = validate_payment(validation_data)
        print(f"✅ Validation: {validation_response}")
        
        # Test confirmation
        confirmation_data = {
            'TransID': 'TEST12345',
            'TransAmount': 50,
            'MSISDN': '254700123456',
            'BillRefNumber': 'TEST123'
        }
        
        confirmation_response = process_confirmation(confirmation_data)
        print(f"✅ Confirmation: {confirmation_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ M-Pesa test failed: {str(e)}")
        return False

def test_scheduler():
    """Test job scheduler"""
    print("\n⏰ Testing job scheduler...")
    
    try:
        from scheduler import run_job_alerts_once
        
        # Run alerts once
        run_job_alerts_once()
        print("✅ Scheduler test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Scheduler test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 WhatsApp Job Alert Bot - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Database", test_database),
        ("Job Scraping", test_scraping),
        ("WhatsApp Bot", test_whatsapp_bot),
        ("M-Pesa", test_mpesa),
        ("Scheduler", test_scheduler)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! Your bot is ready for deployment.")
        print("\n📋 Next steps:")
        print("1. Run: python app.py")
        print("2. Use ngrok to expose your local server")
        print("3. Register M-Pesa URLs: python register_url.py")
        print("4. Set Twilio webhook to: https://your-ngrok.ngrok.io/whatsapp")
        print("5. Test with real WhatsApp messages!")
    else:
        print(f"\n⚠️  {len(tests) - passed} tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 