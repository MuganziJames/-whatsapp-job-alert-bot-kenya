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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def ask_deepseek(prompt: str, context: Dict[str, Any] = None) -> Dict[str, str]:
    """
    Ask DeepSeek Reasoner AI with enhanced context
    
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
        
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        reasoning = getattr(response.choices[0].message, 'reasoning_content', '')
        content = response.choices[0].message.content
        
        # Log the interaction for analytics
        logger.info(f"AI Query: {prompt[:50]}... | Response: {content[:50]}...")
        
        return {
            "reasoning": reasoning or "",
            "content": content or "I'm sorry, I couldn't generate a response. Please try again."
        }
        
    except Exception as e:
        logger.error(f"Error with DeepSeek API: {str(e)}")
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
        
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.1
        )
        
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
        
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        
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
        prompt = f"""Analyze if this job matches the user's interest category.

Job Title: {job_title}
Job Description: {job_description[:500]}...
User Interest: {user_interest}

Consider:
1. Job responsibilities and required skills
2. Career progression opportunities
3. Relevance to the user's chosen category
4. Job quality and legitimacy

Respond with:
- match_score: 0-100 (how well it matches)
- reasoning: Brief explanation
- quality_score: 0-100 (job posting quality)
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
        
        return {
            "match_score": match_score,
            "quality_score": quality_score,
            "analysis": content,
            "should_send": match_score > 60 and quality_score > 50
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