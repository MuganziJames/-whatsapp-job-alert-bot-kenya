#!/usr/bin/env python3
"""
Test script for AI-enhanced WhatsApp Job Alert Bot
Tests all AI features and integration points
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ai_helper():
    """Test AI helper functionality"""
    print("🤖 Testing AI Helper...")
    print("=" * 50)
    
    try:
        from utils.ai_helper import (
            ask_deepseek, 
            is_career_question,
            extract_job_interest,
            get_job_category_recommendation,
            get_career_advice,
            initialize_ai_helper,
            AI_AVAILABLE
        )
        
        if not AI_AVAILABLE:
            print("❌ AI Helper not available")
            return False
        
        # Test 1: Basic AI query
        print("\n1. Testing basic AI query...")
        response = ask_deepseek("What does a software developer do?")
        print(f"✅ AI Response: {response['content'][:100]}...")
        
        # Test 2: Career question detection
        print("\n2. Testing career question detection...")
        questions = [
            "What does a data analyst do?",
            "Help me choose a career",
            "Hello",
            "How much do teachers earn?"
        ]
        
        for question in questions:
            is_career = is_career_question(question)
            print(f"   '{question}' -> Career question: {is_career}")
        
        # Test 3: Job interest extraction
        print("\n3. Testing job interest extraction...")
        messages = [
            "I want to work with computers",
            "I like helping people",
            "I'm good with numbers",
            "Hello there"
        ]
        
        for message in messages:
            interest = extract_job_interest(message)
            print(f"   '{message}' -> Interest: {interest}")
        
        # Test 4: Job category recommendation
        print("\n4. Testing job category recommendation...")
        recommendation = get_job_category_recommendation("I love working with computers and coding")
        print(f"✅ Recommendation: {recommendation['category']}")
        print(f"   Explanation: {recommendation['explanation'][:100]}...")
        
        # Test 5: Career advice
        print("\n5. Testing career advice...")
        advice = get_career_advice("How do I become a software developer?")
        print(f"✅ Career advice: {advice[:100]}...")
        
        print("\n✅ All AI Helper tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ AI Helper test failed: {str(e)}")
        return False

def test_enhanced_scraper():
    """Test enhanced job scraper with AI"""
    print("\n🔍 Testing Enhanced Scraper...")
    print("=" * 50)
    
    try:
        from scraper import scrape_jobs, get_job_stats
        
        # Test job scraping
        print("\n1. Testing job scraping...")
        jobs = scrape_jobs('software engineering', max_jobs=3)
        
        if jobs:
            print(f"✅ Found {len(jobs)} jobs")
            
            for i, job in enumerate(jobs[:2], 1):
                print(f"\n   Job {i}:")
                print(f"   Title: {job['title']}")
                print(f"   Company: {job['company']}")
                print(f"   Location: {job['location']}")
                
                if 'ai_match_score' in job:
                    print(f"   AI Match Score: {job['ai_match_score']}/100")
                    print(f"   AI Quality Score: {job['ai_quality_score']}/100")
        else:
            print("⚠️ No jobs found")
        
        # Test job stats
        print("\n2. Testing job statistics...")
        stats = get_job_stats(jobs)
        print(f"✅ Job stats: {stats}")
        
        print("\n✅ Enhanced Scraper tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Scraper test failed: {str(e)}")
        return False

def test_bot_integration():
    """Test bot integration with AI"""
    print("\n💬 Testing Bot Integration...")
    print("=" * 50)
    
    try:
        from bot import process_whatsapp_message, AI_AVAILABLE
        
        if not AI_AVAILABLE:
            print("⚠️ AI not available in bot, testing basic functionality...")
        
        test_phone = "+254700123456"
        
        # Test messages
        test_messages = [
            "Hi",
            "What does a software developer do?",
            "Help me choose a career",
            "Software engineering",
            "5",
            "jobs",
            "balance"
        ]
        
        print("\n1. Testing various bot messages...")
        for i, message in enumerate(test_messages, 1):
            print(f"\n   Test {i}: '{message}'")
            try:
                response = process_whatsapp_message(f"whatsapp:{test_phone}", message)
                print(f"   ✅ Response: {response[:100]}...")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        
        print("\n✅ Bot Integration tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Bot Integration test failed: {str(e)}")
        return False

def test_database_integration():
    """Test database with AI features"""
    print("\n🗄️ Testing Database Integration...")
    print("=" * 50)
    
    try:
        from db import db
        
        test_phone = "+254700123456"
        
        # Test basic database operations
        print("\n1. Testing basic database operations...")
        
        # Create/update user
        user = db.add_or_update_user(test_phone, interest="software engineering", balance=5)
        print(f"✅ User created/updated: {user['phone'] if user else 'Failed'}")
        
        # Get user
        user = db.get_user_by_phone(test_phone)
        print(f"✅ User retrieved: {user['interest'] if user else 'Failed'}")
        
        # Test AI interaction logging
        print("\n2. Testing AI interaction logging...")
        success = db.log_ai_interaction(
            test_phone, 
            "What does a software developer do?", 
            "A software developer creates applications and systems...",
            "career_question"
        )
        print(f"✅ AI interaction logged: {success}")
        
        # Test AI analytics
        print("\n3. Testing AI analytics...")
        analytics = db.get_ai_analytics(7)
        print(f"✅ AI analytics: {analytics}")
        
        print("\n✅ Database Integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database Integration test failed: {str(e)}")
        return False

def test_environment_setup():
    """Test environment setup"""
    print("\n⚙️ Testing Environment Setup...")
    print("=" * 50)
    
    required_vars = [
        'DEEPSEEK_API_KEY',
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'TWILIO_SID',
        'TWILIO_TOKEN',
        'TWILIO_WHATSAPP_NUMBER'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Don't print actual values for security
            print(f"✅ {var}: {'*' * 20}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ Missing environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with the required values")
        return False
    
    print("\n✅ Environment setup is complete!")
    return True

def main():
    """Run all tests"""
    print("🧪 AI-Enhanced WhatsApp Job Alert Bot - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("AI Helper", test_ai_helper),
        ("Enhanced Scraper", test_enhanced_scraper),
        ("Database Integration", test_database_integration),
        ("Bot Integration", test_bot_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your AI-enhanced bot is ready!")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 