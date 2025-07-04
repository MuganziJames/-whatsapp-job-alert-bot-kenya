"""
Smart Job Request Detection
Intelligently detects when users are asking for jobs in natural language
"""

import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# Job-related keywords and phrases
JOB_REQUEST_KEYWORDS = [
    # Direct job requests
    'jobs', 'job', 'work', 'employment', 'vacancy', 'vacancies', 'opening', 'openings',
    'position', 'positions', 'opportunity', 'opportunities', 'role', 'roles',
    
    # Job search phrases
    'find job', 'get job', 'search job', 'look for job', 'need job', 'want job',
    'job alert', 'job alerts', 'job notification', 'job notifications',
    'new job', 'latest job', 'recent job', 'fresh job', 'available job',
    
    # Employment-related
    'hire', 'hiring', 'recruitment', 'recruit', 'career', 'careers',
    'employ', 'employment', 'occupation',
    
    # Action verbs for job seeking
    'apply', 'applying', 'application', 'applications',
    
    # Kenyan job context
    'kazi', 'ajira', 'nafasi', 'nafasi za kazi'
]

# Phrases that indicate job requests
JOB_REQUEST_PATTERNS = [
    # Direct requests
    r'\b(show|send|get|give|find|share|provide)\s+me\s+(job|jobs|work|kazi|ajira)',
    r'\b(i\s+)?(want|need|looking\s+for|search\s+for|find)\s+(job|jobs|work|kazi|ajira)',
    r'\b(any\s+)?(new|latest|recent|fresh|available)\s+(job|jobs|work|kazi|ajira)',
    
    # Job alerts
    r'\b(job\s+)?(alert|alerts|notification|notifications)',
    r'\b(send|get|share)\s+(alert|alerts|notification|notifications)',
    
    # Employment seeking
    r'\b(seeking|looking\s+for|searching\s+for)\s+(employment|work|job|jobs)',
    r'\b(help\s+me\s+)?(find|get|search)\s+(work|job|jobs|employment)',
    
    # Questions about jobs
    r'\b(what|where|how|when)\s+.*(job|jobs|work|employment|kazi|ajira)',
    r'\b(are\s+there|is\s+there)\s+.*(job|jobs|work|employment)',
    
    # Availability questions
    r'\b(any\s+)?(job|jobs|work)\s+(available|vacancy|vacancies|opening|openings)',
    r'\b(do\s+you\s+have|got\s+any)\s+(job|jobs|work)',
    
    # Kenyan context
    r'\b(tafuta|natafuta|napenda|nina\s+haja)\s+(kazi|ajira)',
    r'\b(kuna|iko|ipo)\s+(kazi|ajira)',
]

# Context words that strengthen job request detection
CONTEXT_STRENGTHENERS = [
    'urgent', 'urgently', 'immediately', 'asap', 'now', 'today', 'tomorrow',
    'salary', 'pay', 'payment', 'income', 'money', 'earning',
    'full time', 'part time', 'freelance', 'remote', 'office',
    'experience', 'skills', 'qualification', 'requirements',
    'application', 'apply', 'cv', 'resume', 'interview'
]

# Words that might indicate other intents (to avoid false positives)
NON_JOB_INDICATORS = [
    'balance', 'credit', 'credits', 'account', 'help', 'support',
    'problem', 'issue', 'error', 'bug', 'question', 'how to',
    'what is', 'explain', 'tell me about', 'describe'
]


def detect_job_request(message: str) -> Tuple[bool, float, str]:
    """
    Detect if a message is requesting jobs using intelligent analysis
    
    Returns:
        Tuple[bool, float, str]: (is_job_request, confidence_score, reason)
    """
    message = message.strip().lower()
    confidence = 0.0
    reasons = []
    
    # 1. Direct keyword matching
    keyword_score = _check_direct_keywords(message)
    if keyword_score > 0:
        confidence += keyword_score
        reasons.append(f"job keywords (score: {keyword_score:.2f})")
    
    # 2. Pattern matching
    pattern_score = _check_job_patterns(message)
    if pattern_score > 0:
        confidence += pattern_score
        reasons.append(f"job patterns (score: {pattern_score:.2f})")
    
    # 3. Context analysis
    context_score = _analyze_context(message)
    if context_score > 0:
        confidence += context_score
        reasons.append(f"job context (score: {context_score:.2f})")
    
    # 4. Check for non-job indicators (reduce confidence)
    non_job_penalty = _check_non_job_indicators(message)
    if non_job_penalty > 0:
        confidence -= non_job_penalty
        reasons.append(f"non-job penalty (score: -{non_job_penalty:.2f})")
    
    # 5. Length and structure analysis
    structure_bonus = _analyze_message_structure(message)
    if structure_bonus > 0:
        confidence += structure_bonus
        reasons.append(f"structure bonus (score: {structure_bonus:.2f})")
    
    # Normalize confidence to 0-1 range
    confidence = max(0.0, min(1.0, confidence))
    
    # Decision threshold
    is_job_request = confidence >= 0.3
    
    reason_text = ", ".join(reasons) if reasons else "no indicators found"
    
    logger.info(f"Job detection - Message: '{message[:50]}...' | "
               f"Confidence: {confidence:.2f} | Is job request: {is_job_request} | "
               f"Reasons: {reason_text}")
    
    return is_job_request, confidence, reason_text


def _check_direct_keywords(message: str) -> float:
    """Check for direct job-related keywords"""
    score = 0.0
    words = message.split()
    
    for keyword in JOB_REQUEST_KEYWORDS:
        if keyword in message:
            # Higher score for exact word matches
            if keyword in words:
                score += 0.3
            else:
                score += 0.2
    
    return min(score, 0.6)  # Cap at 0.6


def _check_job_patterns(message: str) -> float:
    """Check for job request patterns using regex"""
    score = 0.0
    
    for pattern in JOB_REQUEST_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            score += 0.4
            break  # Only count one pattern match to avoid over-scoring
    
    return score


def _analyze_context(message: str) -> float:
    """Analyze context words that strengthen job requests"""
    score = 0.0
    
    for strengthener in CONTEXT_STRENGTHENERS:
        if strengthener in message:
            score += 0.1
    
    return min(score, 0.3)  # Cap at 0.3


def _check_non_job_indicators(message: str) -> float:
    """Check for words that indicate non-job intents"""
    penalty = 0.0
    
    for indicator in NON_JOB_INDICATORS:
        if indicator in message:
            penalty += 0.15
    
    return min(penalty, 0.4)  # Cap penalty at 0.4


def _analyze_message_structure(message: str) -> float:
    """Analyze message structure for job request indicators"""
    bonus = 0.0
    
    # Question marks often indicate requests
    if '?' in message:
        bonus += 0.1
    
    # Polite language
    polite_words = ['please', 'can you', 'could you', 'would you', 'help me']
    for word in polite_words:
        if word in message:
            bonus += 0.05
            break
    
    # Urgency indicators
    urgent_words = ['urgent', 'asap', 'immediately', 'now', 'today']
    for word in urgent_words:
        if word in message:
            bonus += 0.1
            break
    
    return min(bonus, 0.2)  # Cap bonus at 0.2


def is_smart_job_request(message: str, threshold: float = 0.3) -> bool:
    """
    Simple function to check if message is a job request
    
    Args:
        message: User message to analyze
        threshold: Confidence threshold (default 0.3)
    
    Returns:
        bool: True if message is likely a job request
    """
    is_request, confidence, _ = detect_job_request(message)
    return is_request and confidence >= threshold


def extract_job_context_from_message(message: str) -> Optional[str]:
    """
    Extract job-related context from a message
    
    Returns:
        Optional[str]: Job context or None if not found
    """
    message_lower = message.lower()
    
    # Look for specific job types mentioned
    job_types = [
        'data entry', 'sales', 'marketing', 'delivery', 'logistics',
        'customer service', 'finance', 'accounting', 'admin', 'office',
        'teaching', 'training', 'internship', 'attachment', 'software',
        'engineering', 'programming', 'tech', 'it'
    ]
    
    for job_type in job_types:
        if job_type in message_lower:
            return job_type
    
    return None


# Example usage and testing
if __name__ == "__main__":
    test_messages = [
        "I need a job urgently",
        "Do you have any software engineering jobs?",
        "Show me jobs please",
        "Looking for work in data entry",
        "Any new job alerts?",
        "Natafuta kazi ya sales",
        "Help me find employment opportunities",
        "What's my balance?",
        "How does this bot work?",
        "Can you send me some job notifications for customer service roles?",
        "I want to check my account credits",
        "Are there any available positions in finance sector?",
    ]
    
    print("Testing Smart Job Detection:")
    print("=" * 50)
    
    for msg in test_messages:
        is_request, confidence, reason = detect_job_request(msg)
        print(f"Message: '{msg}'")
        print(f"Result: {'JOB REQUEST' if is_request else 'NOT JOB REQUEST'} "
              f"(confidence: {confidence:.2f})")
        print(f"Reason: {reason}")
        print("-" * 30) 