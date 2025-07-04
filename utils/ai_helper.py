"""
AI Helper module for WhatsApp Job Alert Bot
Integrates DeepSeek Reasoner AI for enhanced user interactions
"""

import os
import logging
from openai import OpenAI
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import hashlib
import json
import re
import time
import threading
from queue import Queue
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting and queuing
REQUEST_QUEUE = Queue()
LAST_REQUEST_TIME = 0
MIN_REQUEST_INTERVAL = 2.0  # 2 seconds between requests
MAX_REQUESTS_PER_MINUTE = 20  # Conservative limit
request_times = []
request_lock = threading.Lock()

# Simple cache for AI responses
AI_CACHE = {}
CACHE_EXPIRY_MINUTES = 30
cache_lock = threading.Lock()

# Multiple model fallback configuration - Optimized with 4 models for faster response
FALLBACK_MODELS = [
    {
        "name": "deepseek/deepseek-r1:free",
        "description": "Primary - Best for complex career advice",
        "max_tokens": 1000,
        "temperature": 0.7,
        "priority": 1
    },
    {
        "name": "meta-llama/llama-4-scout:free",
        "description": "NEW Llama 4 - Advanced multimodal reasoning",
        "max_tokens": 900,
        "temperature": 0.6,
        "priority": 2
    },
    {
        "name": "google/gemma-2-9b-it:free",
        "description": "Balanced general-purpose model from Google, reliable quality",
        "max_tokens": 700,
        "temperature": 0.6,
        "priority": 3
    },
    {
        "name": "openrouter/cypher-alpha:free",
        "description": "Community model - final safety net if others are busy",
        "max_tokens": 600,
        "temperature": 0.5,
        "priority": 4
    }
]

# Model usage tracking
model_usage = {}
model_lock = threading.Lock()

# Usage monitoring
daily_usage = {"date": "", "requests": 0, "cache_hits": 0, "model_switches": 0}
usage_lock = threading.Lock()

def log_usage_stats():
    """Log daily usage statistics"""
    today = datetime.now().strftime("%Y-%m-%d")
    with usage_lock:
        if daily_usage["date"] != today:
            if daily_usage["date"]:  # Not first run
                logger.info(f"📊 Daily AI Usage Summary for {daily_usage['date']}: {daily_usage['requests']} requests, {daily_usage['cache_hits']} cache hits, {daily_usage['model_switches']} model switches")
            daily_usage["date"] = today
            daily_usage["requests"] = 0
            daily_usage["cache_hits"] = 0
            daily_usage["model_switches"] = 0
        
        daily_usage["requests"] += 1
        logger.info(f"📈 Today's AI usage: {daily_usage['requests']} requests, {daily_usage['cache_hits']} cache hits, {daily_usage['model_switches']} model switches")

def get_model_usage_stats():
    """Get current model usage statistics"""
    with model_lock:
        stats = []
        for model_name, usage in model_usage.items():
            success_rate = (usage["successes"] / usage["attempts"] * 100) if usage["attempts"] > 0 else 0
            stats.append({
                "model": model_name.split("/")[-1],  # Short name
                "attempts": usage["attempts"],
                "successes": usage["successes"],
                "success_rate": f"{success_rate:.1f}%"
            })
        return stats

# Initialize OpenRouter client for free DeepSeek access
AI_AVAILABLE = False
try:
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        AI_AVAILABLE = True
        logger.info("🤖 OpenRouter AI client initialized successfully")
    else:
        logger.warning("⚠️ OPENROUTER_API_KEY not found in environment")
        client = None
except Exception as e:
    logger.error(f"❌ Failed to initialize OpenRouter client: {str(e)}")
    client = None

# Job categories for context
JOB_CATEGORIES = {
    'data entry': 'Data input, processing, and management tasks',
    'sales & marketing': 'Sales, marketing, and business development roles',
    'delivery & logistics': 'Delivery, transport, and logistics positions',
    'customer service': 'Customer support and service roles',
    'finance & accounting': 'Financial, accounting, and bookkeeping jobs',
    'admin & office work': 'Administrative and office support positions',
    'teaching / training': 'Education, training, and tutoring roles',
    'internships / attachments': 'Internship and attachment opportunities',
    'software engineering': 'Programming, development, and tech roles'
}

def can_make_request() -> bool:
    """Check if we can make a request without hitting rate limits"""
    global request_times
    now = time.time()
    
    with request_lock:
        # Remove requests older than 1 minute
        request_times = [t for t in request_times if now - t < 60]
        
        # Check if we're under the per-minute limit
        if len(request_times) >= MAX_REQUESTS_PER_MINUTE:
            return False
        
        # Check minimum interval since last request
        global LAST_REQUEST_TIME
        if now - LAST_REQUEST_TIME < MIN_REQUEST_INTERVAL:
            return False
    
    return True

def wait_for_rate_limit():
    """Wait until we can make a request"""
    global LAST_REQUEST_TIME
    
    while not can_make_request():
        time.sleep(0.5)  # Check every 500ms
    
    # Record this request
    now = time.time()
    with request_lock:
        request_times.append(now)
        LAST_REQUEST_TIME = now

def log_model_usage(model_name: str, success: bool):
    """Log model usage statistics"""
    with model_lock:
        if model_name not in model_usage:
            model_usage[model_name] = {"attempts": 0, "successes": 0, "failures": 0}
        
        model_usage[model_name]["attempts"] += 1
        if success:
            model_usage[model_name]["successes"] += 1
        else:
            model_usage[model_name]["failures"] += 1

def make_ai_request_with_retry(messages: List[Dict], max_retries: int = 1) -> Any:
    """Make AI request with intelligent fallback across multiple models (optimized for speed)"""
    if not AI_AVAILABLE or not client:
        return None
    
    # Wait for rate limit clearance
    wait_for_rate_limit()
    
    # Try each model in fallback order
    for model_config in FALLBACK_MODELS:
        model_name = model_config["name"]
        max_tokens = model_config["max_tokens"]
        temperature = model_config["temperature"]
        
        logger.info(f"🤖 Trying model: {model_name}")
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Log successful usage
                log_model_usage(model_name, True)
                
                # Log model switch if not using primary model
                if model_config["priority"] > 1:
                    with usage_lock:
                        daily_usage["model_switches"] += 1
                    logger.info(f"✅ Using fallback model: {model_config['description']}")
                else:
                    logger.info("✅ AI request successful with primary model")
                
                return response
                
            except Exception as e:
                error_msg = str(e)
                log_model_usage(model_name, False)
                
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    logger.warning(f"⚠️ Model {model_name} rate limited, trying next model...")
                    break  # Try next model immediately
                elif attempt == max_retries - 1:
                    logger.warning(f"⚠️ Model {model_name} failed after {max_retries} attempt(s): {error_msg}")
                    break  # Try next model
                else:
                    # Other error, short wait and retry same model
                    time.sleep(0.5)  # Reduced wait time for faster response
                    continue
    
    # All models failed
    logger.error("❌ All AI models failed or rate limited")
    return None

def get_cache_key(prompt: str, context: Dict[str, Any] = None) -> str:
    """Generate cache key for AI requests"""
    context_str = json.dumps(context, sort_keys=True) if context else ""
    return hashlib.md5(f"{prompt}{context_str}".encode()).hexdigest()

def get_cached_response(cache_key: str) -> Optional[Dict[str, str]]:
    """Get cached AI response if available and not expired"""
    with cache_lock:
        if cache_key in AI_CACHE:
            cached_item = AI_CACHE[cache_key]
            # Check if cache is still valid (30 minutes)
            if time.time() - cached_item['timestamp'] < CACHE_EXPIRY_MINUTES * 60:
                logger.info("✅ Using cached AI response")
                return cached_item['response']
            else:
                # Remove expired cache
                del AI_CACHE[cache_key]
    return None

def cache_response(cache_key: str, response: Dict[str, str]):
    """Cache AI response"""
    with cache_lock:
        AI_CACHE[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
        # Clean up old cache entries (keep only last 100)
        if len(AI_CACHE) > 100:
            oldest_key = min(AI_CACHE.keys(), key=lambda k: AI_CACHE[k]['timestamp'])
            del AI_CACHE[oldest_key]

def ask_deepseek(prompt: str, context: Dict[str, Any] = None) -> Dict[str, str]:
    """
    Ask DeepSeek Reasoner AI with enhanced context, caching, and rate limiting
    
    Args:
        prompt: User's question or request
        context: Additional context (user info, job categories, etc.)
    
    Returns:
        Dict with 'reasoning' and 'content' keys
    """
    if not AI_AVAILABLE or not client:
        return {
            "reasoning": "",
            "content": "AI assistant is currently unavailable. Please try again later or contact support."
        }
    
    # Check cache first
    cache_key = get_cache_key(prompt, context)
    cached_response = get_cached_response(cache_key)
    if cached_response:
        with usage_lock:
            daily_usage["cache_hits"] += 1
        return cached_response
    
    # Log usage
    log_usage_stats()
    
    try:
        # Build enhanced prompt with context
        enhanced_prompt = build_enhanced_prompt(prompt, context)
        
        messages = [
            {
                "role": "system",
                "content": get_system_prompt()
            },
            {
                "role": "user", 
                "content": enhanced_prompt
            }
        ]
        
        # Use the new multi-model fallback function
        response = make_ai_request_with_retry(messages)
        
        if not response:
            return {
                "reasoning": "",
                "content": "🤖 All our AI advisors are busy now. Please try again in a few minutes.\n\nIn the meantime, you can use our regular job alert features:\n\n📋 *Available Job Categories:*\n• *Data Entry* - Data processing jobs\n• *Sales & Marketing* - Business development roles\n• *Software Engineering* - Programming and tech jobs\n• *Customer Service* - Support and service roles\n• *Finance & Accounting* - Financial jobs\n• *Admin & Office Work* - Administrative roles\n• *Teaching / Training* - Education roles\n• *Delivery & Logistics* - Transport jobs\n• *Internships / Attachments* - Learning opportunities\n\n💡 *How to use:*\n• Send any category name to set your interest\n• Send *jobs* to get job alerts\n• Send *balance* to check your credits\n\nTry sending a job category now!"
            }
        
        reasoning = getattr(response.choices[0].message, 'reasoning_content', '')
        content = response.choices[0].message.content
        
        # Log the interaction for analytics
        logger.info(f"AI Query: {prompt[:50]}... | Response: {content[:50]}...")
        
        response_dict = {
            "reasoning": reasoning or "",
            "content": content or "I'm sorry, I couldn't generate a response. Please try again."
        }
        
        # Cache the response
        cache_response(cache_key, response_dict)
        
        return response_dict
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error with DeepSeek API: {error_msg}")
        
        # Handle rate limiting specifically
        if "429" in error_msg or "rate limit" in error_msg.lower():
            return {
                "reasoning": "",
                "content": "🤖 I'm currently at my daily AI limit, but I can still help! Try asking about our job categories:\n\n• *Data Entry* - Data processing jobs\n• *Sales & Marketing* - Business development roles\n• *Software Engineering* - Programming and tech jobs\n• *Customer Service* - Support and service roles\n\nOr send the name of any category to get started!"
            }
        else:
            return {
                "reasoning": "",
                "content": "I'm having trouble connecting to my AI assistant right now. Please try again later, or feel free to ask me about our job categories!"
            }

def get_system_prompt() -> str:
    """Get the system prompt for DeepSeek"""
    return f"""You are an AI assistant for a WhatsApp Job Alert Bot in Kenya. Your role is to:

1. Help users understand different job roles and career paths
2. Explain job categories in simple, clear terms
3. Assist users in choosing the right job category based on their interests and skills
4. Provide career advice and guidance
5. Help with onboarding and explaining how the bot works

Available job categories:
{chr(10).join([f"• {cat}: {desc}" for cat, desc in JOB_CATEGORIES.items()])}

Guidelines:
- Keep responses concise (under 200 words for WhatsApp)
- Use simple, clear language suitable for all education levels
- Be encouraging and supportive
- Focus on practical, actionable advice
- When suggesting job categories, explain why they might be a good fit
- Always end with a helpful next step or question

Context: This is for a Kenyan job market, so be relevant to local opportunities and culture."""

def build_enhanced_prompt(prompt: str, context: Dict[str, Any] = None) -> str:
    """Build enhanced prompt with context"""
    enhanced = prompt
    
    if context:
        user_info = context.get('user_info', {})
        if user_info:
            enhanced += f"\n\nUser context: Interest={user_info.get('interest', 'Not set')}, Balance={user_info.get('balance', 0)} credits"
        
        conversation_history = context.get('conversation_history', [])
        if conversation_history:
            enhanced += f"\n\nRecent conversation: {conversation_history[-3:]}"
    
    return enhanced

def is_career_question(message: str) -> bool:
    """Check if message is a career-related question"""
    career_keywords = [
        'what does', 'what is', 'how to', 'help me choose', 'which job',
        'career advice', 'job role', 'responsibilities', 'skills needed',
        'salary', 'requirements', 'qualification', 'experience',
        'difference between', 'better job', 'should i', 'recommend'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in career_keywords)

def extract_job_interest(message: str) -> Optional[str]:
    """Extract potential job interest from user message using AI"""
    if not AI_AVAILABLE or not client:
        return None
    
    try:
        prompt = f"""Analyze this message and determine if the user is expressing interest in a specific job category.

Message: "{message}"

Available categories: {', '.join(JOB_CATEGORIES.keys())}

If the message indicates interest in a specific category, respond with just the category name (exactly as listed above).
If no clear interest is expressed, respond with "none".

Examples:
- "I want to work with computers" → "software engineering"
- "I like helping people" → "customer service"
- "I'm good with numbers" → "finance & accounting"
- "Hello" → "none"
"""
        
        messages = [{"role": "user", "content": prompt}]
        response = make_ai_request_with_retry(messages)
        
        if not response:
            return None
        
        result = response.choices[0].message.content.strip().lower()
        
        # Validate the result
        if result in JOB_CATEGORIES:
            return result
        elif result != "none":
            # Try to match partial responses
            for category in JOB_CATEGORIES:
                if category in result:
                    return category
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting job interest: {str(e)}")
        return None

def get_job_category_recommendation(user_input: str) -> Dict[str, Any]:
    """Get AI-powered job category recommendation"""
    if not AI_AVAILABLE or not client:
        return {
            "category": None,
            "explanation": "AI assistant is currently unavailable. Please try selecting a job category from our available options.",
            "confidence": "low"
        }
    
    try:
        prompt = f"""A user is asking for help choosing a job category. Based on their message, recommend the most suitable category and explain why.

User message: "{user_input}"

Available categories:
{chr(10).join([f"• {cat}: {desc}" for cat, desc in JOB_CATEGORIES.items()])}

Provide:
1. The recommended category name (exactly as listed above)
2. A brief explanation (2-3 sentences) of why this category suits them
3. What typical tasks they would do in this role
4. Any skills they might need to develop

Format your response as a helpful WhatsApp message."""
        
        messages = [{"role": "user", "content": prompt}]
        response = make_ai_request_with_retry(messages)
        
        if not response:
            return {
                "category": None,
                "explanation": "I'm temporarily busy processing other requests. Please try again in a moment, or feel free to browse our job categories!",
                "confidence": "low"
            }
        
        content = response.choices[0].message.content
        
        # Extract category from response
        recommended_category = None
        for category in JOB_CATEGORIES:
            if category in content.lower():
                recommended_category = category
                break
        
        return {
            "category": recommended_category,
            "explanation": content,
            "confidence": "high" if recommended_category else "low"
        }
        
    except Exception as e:
        logger.error(f"Error getting category recommendation: {str(e)}")
        return {
            "category": None,
            "explanation": "I'd be happy to help you choose a job category! Could you tell me more about what kind of work interests you or what skills you have?",
            "confidence": "low"
        }

def improve_job_matching(job_title: str, job_description: str, user_interest: str) -> Dict[str, Any]:
    """Use AI to improve job matching beyond keyword matching"""
    try:
        # Handle minimal job descriptions common in scraped jobs
        description_text = job_description if job_description and len(job_description.strip()) > 10 else "No detailed description provided"
        
        prompt = f"""Analyze if this job matches the user's interest category.

Job Title: {job_title}
Job Description: {description_text}
User Interest: {user_interest}

IMPORTANT: Many legitimate job postings from job boards have minimal descriptions but are still valid opportunities.

Consider:
1. Does the job title align with the user's interest category?
2. Are there obvious red flags (scam, fake, spam)?
3. Does this look like a legitimate job posting?
4. For scraped jobs with minimal descriptions, focus on title relevance

Be more lenient with quality scores for jobs with minimal descriptions if the title seems legitimate.

Respond with:
- match_score: 0-100 (how well it matches the category)
- reasoning: Brief explanation
- quality_score: 0-100 (job posting quality - be generous for minimal descriptions)
- red_flags: Any concerns about the job posting
"""
        
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        
        # Extract scores using regex
        match_score = extract_score(content, "match_score")
        quality_score = extract_score(content, "quality_score")
        
        # More lenient filtering for scraped jobs with minimal descriptions
        min_match_score = 40  # Reduced from 60
        min_quality_score = 30  # Reduced from 50
        
        # Additional check: if it's a very short job description, be more lenient
        if len(description_text.strip()) < 50:
            min_quality_score = 25
        
        # Check for obvious red flags in title
        red_flag_terms = ['scam', 'fake', 'spam', 'too good to be true', 'earn money fast', 'work from home easy money']
        has_red_flags = any(term in job_title.lower() for term in red_flag_terms)
        
        should_send = (
            match_score > min_match_score and 
            quality_score > min_quality_score and 
            not has_red_flags
        )
        
        return {
            "match_score": match_score,
            "quality_score": quality_score,
            "analysis": content,
            "should_send": should_send
        }
        
    except Exception as e:
        logger.error(f"Error improving job matching: {str(e)}")
        return {
            "match_score": 50,
            "quality_score": 50,
            "analysis": "Unable to analyze job matching",
            "should_send": True  # Default to sending if analysis fails
        }

def extract_score(text: str, score_name: str) -> int:
    """Extract numeric score from AI response"""
    try:
        pattern = rf"{score_name}:\s*(\d+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 50  # Default score
    except:
        return 50

def generate_personalized_message(job: Dict[str, Any], user_info: Dict[str, Any]) -> str:
    """Generate personalized job alert message"""
    try:
        prompt = f"""Create a personalized WhatsApp job alert message.

Job Details:
- Title: {job.get('title', 'N/A')}
- Company: {job.get('company', 'N/A')}
- Location: {job.get('location', 'Kenya')}
- URL: {job.get('link', 'N/A')}

User Info:
- Interest: {user_info.get('interest', 'N/A')}
- Balance: {user_info.get('balance', 0)} credits

Create an engaging message that:
1. Highlights why this job matches their interest
2. Includes key job details
3. Encourages them to apply
4. Mentions credit usage
5. Keeps it under 200 words for WhatsApp

Use emojis and formatting for better readability."""
        
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating personalized message: {str(e)}")
        # Fallback to standard message
        return f"""🎯 *New {user_info.get('interest', 'Job').title()} Alert!*

📋 *{job.get('title', 'Job Opportunity')}*
🏢 {job.get('company', 'Company')}
📍 {job.get('location', 'Kenya')}
🔗 {job.get('link', 'Apply now!')}

💳 1 credit used | Balance: {user_info.get('balance', 0) - 1}

Good luck with your application! 🚀"""

def get_career_advice(question: str, user_context: Dict[str, Any] = None) -> str:
    """Get career advice from AI"""
    try:
        context_info = ""
        if user_context:
            context_info = f"\nUser context: {user_context}"
        
        prompt = f"""Provide career advice for this question in the context of the Kenyan job market.

Question: {question}{context_info}

Provide practical, actionable advice that:
1. Is relevant to Kenya's job market
2. Considers local opportunities and challenges
3. Includes specific next steps
4. Is encouraging and supportive
5. Fits in a WhatsApp message (under 200 words)

Focus on practical skills, networking, and realistic career paths."""
        
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error getting career advice: {str(e)}")
        return "I'd be happy to help with career advice! Could you be more specific about what you'd like to know? You can ask about job requirements, skills to develop, or career paths in any of our job categories."

# Initialize AI helper
def initialize_ai_helper():
    """Initialize the AI helper and check API connectivity"""
    try:
        # Test API connection
        test_response = ask_deepseek("Hello, are you working?")
        if test_response["content"]:
            logger.info("✅ DeepSeek AI Helper initialized successfully")
            return True
        else:
            logger.error("❌ DeepSeek AI Helper initialization failed")
            return False
    except Exception as e:
        logger.error(f"❌ DeepSeek AI Helper initialization error: {str(e)}")
        return False 