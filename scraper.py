"""
ENHANCED Multi-Source Job Scraper
Searches multiple job sites for comprehensive job coverage
"""

import asyncio
import logging
import hashlib
import time
import requests
from typing import List, Dict, Any
from urllib.parse import urljoin, quote_plus
from bs4 import BeautifulSoup

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AI Helper import (with fallback)
try:
    from utils.ai_helper import improve_job_matching, AI_AVAILABLE
    logger.info("🤖 AI-enhanced scraper loaded")
except ImportError:
    AI_AVAILABLE = False
    logger.warning("⚠️ AI not available, using standard scraper")

# Enhanced search terms with broader coverage
ENHANCED_SEARCH_TERMS = {
    'data entry': [
        'data entry', 'data input', 'data processing', 'data clerk', 'data operator', 
        'typing', 'keying', 'data capture', 'data analyst', 'data assistant',
        'clerk', 'administrative assistant', 'office assistant', 'records clerk',
        'database', 'excel', 'spreadsheet', 'data management'
    ],
    'sales & marketing': [
        'sales', 'marketing', 'business development', 'sales rep', 'sales representative',
        'account manager', 'marketing manager', 'sales executive', 'marketing executive', 
        'sales agent', 'promoter', 'brand ambassador', 'digital marketing',
        'social media', 'advertising', 'market research', 'sales consultant',
        'business development', 'relationship manager', 'channel sales'
    ],
    'delivery & logistics': [
        'delivery', 'logistics', 'transport', 'courier', 'driver', 'dispatch',
        'shipping', 'warehouse', 'supply chain', 'distribution', 'fleet',
        'cargo', 'freight', 'inventory', 'procurement', 'operations',
        'delivery driver', 'truck driver', 'logistics coordinator'
    ],
    'customer service': [
        'customer service', 'customer support', 'call center', 'help desk',
        'customer care', 'client service', 'support agent', 'service representative',
        'customer success', 'client relations', 'support specialist',
        'call centre', 'contact center', 'customer experience', 'service desk'
    ],
    'finance & accounting': [
        'finance', 'accounting', 'bookkeeping', 'accountant', 'financial',
        'accounts', 'audit', 'tax', 'payroll', 'finance officer',
        'financial analyst', 'accounts clerk', 'bookkeeper', 'treasurer',
        'budget', 'financial planning', 'credit', 'banking', 'investment'
    ],
    'admin & office work': [
        'admin', 'administrative', 'office', 'secretary', 'receptionist',
        'office manager', 'executive assistant', 'personal assistant',
        'administrative assistant', 'office assistant', 'clerk',
        'coordinator', 'scheduler', 'documentation', 'filing'
    ],
    'teaching / training': [
        'teacher', 'teaching', 'tutor', 'instructor', 'educator', 'lecturer', 'trainer',
        'training', 'facilitator', 'curriculum', 'curriculum developer', 'academic', 'professor',
        'school', 'kindergarten', 'primary school', 'high school', 'education officer', 'coach',
        'learning', 'education', 'training coordinator', 'corporate trainer'
    ],
    'internships / attachments': [
        'internship', 'intern', 'attachment', 'industrial attachment', 'trainee', 'graduate trainee',
        'graduate program', 'entry level', 'junior', 'apprentice', 'fellowship', 'student', 
        'summer intern', 'graduate', 'fresh graduate', 'entry-level', 'beginner'
    ],
    'software engineering': [
        'software', 'software engineer', 'software developer', 'developer', 'programmer',
        'full stack', 'backend', 'frontend', 'front end', 'mobile developer', 'web developer',
        'python', 'java', 'javascript', 'react', 'node', 'django', 'flutter',
        'php', 'laravel', 'angular', 'vue', 'kotlin', 'swift', 'devops',
        'software architect', 'technical lead', 'coding', 'programming'
    ]
}

def generate_job_id(title: str, link: str) -> str:
    """Generate unique job ID"""
    return hashlib.md5(f"{title}_{link}".encode()).hexdigest()[:12]

def matches_search_terms(title: str, interest: str, strict: bool = True) -> bool:
    """Check if job title matches any search terms for the interest"""
    if not title:
        return False
        
    search_terms = ENHANCED_SEARCH_TERMS.get(interest, [interest])
    title_lower = title.lower()
    
    if strict:
        # Use word boundaries for strict matching
        import re
        for term in search_terms:
            pattern = rf"\b{re.escape(term.lower())}\b"
            if re.search(pattern, title_lower):
                return True
        return False
    else:
        # Use substring matching for broader results
        return any(term.lower() in title_lower for term in search_terms)

def scrape_brightermondayke(interest: str, max_jobs: int = 10) -> List[Dict[str, Any]]:
    """Scrape BrighterMonday Kenya using requests and BeautifulSoup"""
    jobs = []
    
    try:
        logger.info(f"🔍 Scraping BrighterMonday for {interest} jobs...")
        
        # Get search terms
        search_terms = ENHANCED_SEARCH_TERMS.get(interest, [interest])
        primary_search = search_terms[0] if search_terms else interest
        
        # BrighterMonday search URL
        search_url = f"https://www.brightermonday.co.ke/jobs?q={quote_plus(primary_search)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job listings - try multiple approaches
        job_elements = []
        
        # Try specific job card selectors first
        job_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(
            term in x.lower() for term in ['job', 'listing', 'vacancy', 'position', 'card']
        ))
        job_elements.extend(job_cards)
        
        # Try job title selectors
        job_titles = soup.find_all(['h1', 'h2', 'h3', 'h4'], class_=lambda x: x and any(
            term in x.lower() for term in ['title', 'job', 'position']
        ))
        job_elements.extend(job_titles)
        
        # Try job links
        job_links = soup.find_all('a', href=lambda x: x and 'job' in x.lower())
        job_elements.extend(job_links)
        
        # Also try generic headings and links
        if not job_elements:
            job_elements = soup.find_all(['h2', 'h3', 'h4']) + soup.find_all('a', href=True)
        
        logger.info(f"📋 Found {len(job_elements)} potential job elements on BrighterMonday")
        
        processed_titles = set()  # Avoid duplicates
        
        for element in job_elements[:50]:  # Process more elements
            try:
                # Extract job title - try multiple approaches
                title = ""
                
                # Method 1: Direct text content
                if hasattr(element, 'get_text'):
                    title = element.get_text(strip=True)
                elif hasattr(element, 'text'):
                    title = element.text.strip()
                else:
                    title = str(element).strip()
                
                # Method 2: Try to find title in nested elements
                if not title or len(title) < 5:
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'span', 'div'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                
                # Method 3: Try link text
                if not title or len(title) < 5:
                    if element.name == 'a':
                        title = element.get_text(strip=True)
                
                if not title or len(title) < 5:
                    continue
                
                # Clean up title
                title = ' '.join(title.split())  # Normalize whitespace
                
                # Skip if too short or already processed
                if len(title) < 10 or title in processed_titles:
                    continue
                
                processed_titles.add(title)
                
                # Skip non-job content
                skip_words = ['search', 'filter', 'browse', 'categories', 'about us', 'contact', 'home', 'login', 'register']
                if any(word in title.lower() for word in skip_words):
                    continue
                
                # Extract link
                link = "https://www.brightermonday.co.ke"
                if element.name == 'a' and element.get('href'):
                    href = element.get('href')
                    link = href if href.startswith('http') else urljoin("https://www.brightermonday.co.ke", href)
                else:
                    # Try to find a link within the element
                    link_elem = element.find('a')
                    if link_elem and link_elem.get('href'):
                        href = link_elem.get('href')
                        link = href if href.startswith('http') else urljoin("https://www.brightermonday.co.ke", href)
                
                # Extract company and location
                company = "BrighterMonday Employer"
                location = "Kenya"
                
                # Try to extract company info from nearby elements
                company_elem = element.find(class_=lambda x: x and 'company' in x.lower())
                if not company_elem:
                    # Try parent or sibling elements
                    parent = element.parent
                    if parent:
                        company_elem = parent.find(class_=lambda x: x and 'company' in x.lower())
                
                if company_elem:
                    company_text = company_elem.get_text(strip=True)
                    if company_text and len(company_text) > 2:
                        company = company_text
                
                # Try to extract location
                location_elem = element.find(class_=lambda x: x and any(term in x.lower() for term in ['location', 'city', 'place']))
                if location_elem:
                    location_text = location_elem.get_text(strip=True)
                    if location_text and len(location_text) > 2:
                        location = location_text
                
                # Check if job matches interest - use relaxed matching for broader results
                if matches_search_terms(title, interest, strict=False):
                    job = {
                        'id': generate_job_id(title, link),
                        'title': title,
                        'link': link,
                        'location': location,
                        'company': company,
                        'source': 'BrighterMonday'
                    }
                    jobs.append(job)
                    logger.info(f"✅ MATCHED BrighterMonday {interest}: {title[:50]}...")
                    
                    if len(jobs) >= max_jobs:
                        break
                        
            except Exception as e:
                logger.debug(f"Error processing BrighterMonday element: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping BrighterMonday: {str(e)}")
    
    logger.info(f"📊 BrighterMonday found {len(jobs)} jobs for {interest}")
    return jobs

async def scrape_myjobmag_enhanced(interest: str, max_jobs: int = 10) -> List[Dict[str, Any]]:
    """Enhanced MyJobMag scraping with better search coverage"""
    jobs = []
    
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("⚠️ Playwright not available, cannot scrape MyJobMag")
        return jobs
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            logger.info(f"🔍 Enhanced MyJobMag scraping for {interest}...")
            
            # Get multiple search terms for broader coverage
            search_terms = ENHANCED_SEARCH_TERMS.get(interest, [interest])
            
            # Try multiple search approaches
            search_urls = []
            
            # Primary search
            primary_term = search_terms[0] if search_terms else interest
            search_urls.append(f"https://www.myjobmag.co.ke/jobs?q={quote_plus(primary_term)}")
            
            # Secondary searches for broader coverage
            if len(search_terms) > 1:
                secondary_term = search_terms[1]
                search_urls.append(f"https://www.myjobmag.co.ke/jobs?q={quote_plus(secondary_term)}")
            
            # Also try category-based search
            search_urls.append("https://www.myjobmag.co.ke/jobs")
            
            all_jobs = []
            
            for search_url in search_urls:
                try:
                    logger.info(f"🔍 Searching: {search_url}")
                    await page.goto(search_url, timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    # Get all potential job elements
                    elements = await page.query_selector_all('h1, h2, h3, h4, .job-title, [class*="job"], [class*="title"], a[href*="job"]')
                    
                    logger.info(f"📋 Found {len(elements)} elements on page")
                    
                    for element in elements[:30]:  # Process more elements
                        try:
                            text = await element.inner_text()
                            if not text or len(text.strip()) < 10:
                                continue
                            
                            title = text.strip()
                            
                            # Skip non-job content
                            skip_words = ['search', 'filter', 'browse', 'categories', 'latest news', 'tips', 'guide']
                            if any(word in title.lower() for word in skip_words):
                                continue
                            
                            # Clean up title - remove extra text that's not part of job title
                            title = ' '.join(title.split())  # Normalize whitespace
                            
                            # Extract actual job title from long descriptions
                            if len(title) > 100:
                                # Try to extract the first sentence or line as the job title
                                lines = title.split('\n')
                                if lines:
                                    title = lines[0].strip()
                                
                                # If still too long, try to extract first meaningful part
                                if len(title) > 100:
                                    # Look for common job title patterns
                                    sentences = title.split('.')
                                    for sentence in sentences:
                                        sentence = sentence.strip()
                                        if len(sentence) > 10 and len(sentence) < 80:
                                            # Check if this looks like a job title
                                            job_indicators = ['position', 'role', 'job', 'vacancy', 'opportunity', 'wanted', 'required', 'seeking']
                                            if any(indicator in sentence.lower() for indicator in job_indicators):
                                                title = sentence
                                                break
                                    
                                    # If still too long, truncate at a reasonable point
                                    if len(title) > 100:
                                        title = title[:100].strip()
                                        # Try to end at a word boundary
                                        last_space = title.rfind(' ')
                                        if last_space > 50:
                                            title = title[:last_space]
                            
                            # Skip if still too short after cleaning
                            if len(title) < 10:
                                continue
                            
                            # Get link
                            link = "https://www.myjobmag.co.ke"
                            try:
                                href = await element.get_attribute('href')
                                if href:
                                    link = href if href.startswith('http') else urljoin("https://www.myjobmag.co.ke", href)
                                else:
                                    # Try to find parent link
                                    parent = await element.query_selector('xpath=./ancestor::a[1]')
                                    if parent:
                                        href = await parent.get_attribute('href')
                                        if href:
                                            link = href if href.startswith('http') else urljoin("https://www.myjobmag.co.ke", href)
                            except:
                                pass
                            
                            # Parse title for company and location
                            company = "MyJobMag Employer"
                            location = "Kenya"
                            original_title = title
                            
                            if " at " in title:
                                parts = title.split(" at ")
                                if len(parts) >= 2:
                                    company = parts[-1].strip()
                                    title = parts[0].strip()
                            
                            if " - " in title:
                                parts = title.split(" - ")
                                if len(parts) >= 2:
                                    # Check if the last part looks like a location
                                    potential_location = parts[-1].strip()
                                    if len(potential_location) < 30:  # Locations are usually short
                                        location = potential_location
                                        title = " - ".join(parts[:-1]).strip()
                            
                            # Check if job matches (use relaxed matching)
                            if matches_search_terms(title, interest, strict=False):
                                job = {
                                    'id': generate_job_id(original_title, link),
                                    'title': title,
                                    'link': link,
                                    'location': location,
                                    'company': company,
                                    'source': 'MyJobMag Enhanced'
                                }
                                all_jobs.append(job)
                                logger.info(f"✅ MATCHED MyJobMag {interest}: {title[:50]}...")
                                
                        except Exception as e:
                            logger.debug(f"Error processing element: {str(e)}")
                            continue
                    
                    # Don't overwhelm with too many requests
                    await page.wait_for_timeout(2000)
                    
                except Exception as e:
                    logger.debug(f"Error with search URL {search_url}: {str(e)}")
                    continue
            
            await browser.close()
            
            # Remove duplicates and limit results
            unique_jobs = {}
            for job in all_jobs:
                if job['id'] not in unique_jobs:
                    unique_jobs[job['id']] = job
            
            jobs = list(unique_jobs.values())[:max_jobs]
            
    except Exception as e:
        logger.error(f"Error in enhanced MyJobMag scraping: {str(e)}")
    
    logger.info(f"📊 MyJobMag Enhanced found {len(jobs)} jobs for {interest}")
    return jobs

def scrape_jobskenya(interest: str, max_jobs: int = 5) -> List[Dict[str, Any]]:
    """Scrape Jobs Kenya using requests and BeautifulSoup"""
    jobs = []
    
    try:
        logger.info(f"🔍 Scraping Jobs Kenya for {interest} jobs...")
        
        # Get search terms
        search_terms = ENHANCED_SEARCH_TERMS.get(interest, [interest])
        primary_search = search_terms[0] if search_terms else interest
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Try the main jobs page
        search_url = "https://www.jobskenya.info/"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job listings
        job_elements = soup.find_all(['h2', 'h3', 'h4', 'a'], href=True)
        
        logger.info(f"📋 Found {len(job_elements)} potential job elements on Jobs Kenya")
        
        processed_titles = set()
        
        for element in job_elements[:20]:
            try:
                title = element.get_text(strip=True)
                
                if not title or len(title) < 10 or title in processed_titles:
                    continue
                
                processed_titles.add(title)
                
                # Skip non-job content
                skip_words = ['home', 'about', 'contact', 'privacy', 'terms', 'search', 'categories']
                if any(word in title.lower() for word in skip_words):
                    continue
                
                # Check if it looks like a job
                job_indicators = ['position', 'job', 'vacancy', 'opportunity', 'wanted', 'required', 'officer', 'manager', 'assistant', 'coordinator', 'specialist', 'representative', 'agent', 'analyst', 'developer', 'engineer', 'executive']
                if not any(indicator in title.lower() for indicator in job_indicators):
                    continue
                
                # Extract link
                link = "https://www.jobskenya.info/"
                if element.get('href'):
                    href = element.get('href')
                    link = href if href.startswith('http') else urljoin("https://www.jobskenya.info/", href)
                
                # Check if job matches interest
                if matches_search_terms(title, interest, strict=False):
                    job = {
                        'id': generate_job_id(title, link),
                        'title': title,
                        'link': link,
                        'location': 'Kenya',
                        'company': 'Jobs Kenya Employer',
                        'source': 'Jobs Kenya'
                    }
                    jobs.append(job)
                    logger.info(f"✅ MATCHED Jobs Kenya {interest}: {title[:50]}...")
                    
                    if len(jobs) >= max_jobs:
                        break
                        
            except Exception as e:
                logger.debug(f"Error processing Jobs Kenya element: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping Jobs Kenya: {str(e)}")
    
    logger.info(f"📊 Jobs Kenya found {len(jobs)} jobs for {interest}")
    return jobs

def scrape_brightermonday_advanced(interest: str, max_jobs: int = 10) -> List[Dict[str, Any]]:
    """Advanced BrighterMonday scraper with proper CSS selectors and pagination"""
    jobs = []
    
    try:
        logger.info(f"🔍 Advanced BrighterMonday scraping for {interest} jobs...")
        
        # Get search terms
        search_terms = ENHANCED_SEARCH_TERMS.get(interest, [interest])
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Try multiple search approaches for better coverage
        search_queries = []
        
        # Primary search with main term
        primary_term = search_terms[0] if search_terms else interest
        search_queries.append(primary_term)
        
        # For STEM jobs, add specific tech terms
        if interest == 'software engineering':
            search_queries.extend(['software developer', 'programmer', 'web developer', 'mobile developer', 'python', 'javascript'])
        elif 'engineering' in interest.lower():
            search_queries.extend(['engineer', 'technical', 'technology'])
        
        # Add secondary terms for broader coverage
        if len(search_terms) > 1:
            search_queries.append(search_terms[1])
        
        processed_titles = set()
        
        # Search with different queries and pages
        for query in search_queries[:3]:  # Limit to avoid too many requests
            for page in range(1, 4):  # Search first 3 pages
                try:
                    # BrighterMonday search URL with pagination
                    search_url = f"https://www.brightermonday.co.ke/jobs?q={quote_plus(query)}&page={page}"
                    
                    logger.info(f"🔍 Searching: {search_url}")
                    
                    response = requests.get(search_url, headers=headers, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for job cards using BrighterMonday's actual structure
                    job_cards = []
                    
                    # Method 1: Look for featured job cards
                    featured_jobs = soup.find_all('div', class_=lambda x: x and 'featured' in x.lower())
                    job_cards.extend(featured_jobs)
                    
                    # Method 2: Look for job listing containers
                    job_containers = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                        term in x.lower() for term in ['job', 'listing', 'vacancy', 'card', 'item']
                    ))
                    job_cards.extend(job_containers)
                    
                    # Method 3: Look for elements with job-related href attributes
                    job_links = soup.find_all('a', href=lambda x: x and any(
                        term in x.lower() for term in ['/job/', '/vacancy/', '/position/']
                    ))
                    job_cards.extend(job_links)
                    
                    # Method 4: Look for salary information (jobs usually have salary)
                    salary_elements = soup.find_all(text=lambda x: x and 'KSh' in str(x))
                    for salary_elem in salary_elements:
                        parent = salary_elem.parent
                        if parent:
                            # Find the job card containing this salary
                            job_card = parent
                            for _ in range(5):  # Look up to 5 levels up
                                if job_card and job_card.name in ['div', 'article']:
                                    job_cards.append(job_card)
                                    break
                                job_card = job_card.parent if hasattr(job_card, 'parent') else None
                    
                    logger.info(f"📋 Found {len(job_cards)} potential job elements on page {page}")
                    
                    # Extract job information from cards
                    for card in job_cards:
                        try:
                            # Extract job title
                            title = ""
                            
                            # Look for title in various ways
                            title_selectors = [
                                'h1', 'h2', 'h3', 'h4',
                                '[class*="title"]', '[class*="job"]', '[class*="position"]',
                                'a[href*="/job/"]', 'a[href*="/vacancy/"]'
                            ]
                            
                            for selector in title_selectors:
                                title_elem = card.find(selector) if hasattr(card, 'find') else None
                                if title_elem:
                                    title_text = title_elem.get_text(strip=True)
                                    if title_text and len(title_text) > 5 and len(title_text) < 150:
                                        title = title_text
                                        break
                            
                            # If no title found, try getting text from links
                            if not title and hasattr(card, 'find'):
                                link_elem = card.find('a')
                                if link_elem:
                                    title = link_elem.get_text(strip=True)
                            
                            if not title or len(title) < 10:
                                continue
                            
                            # Clean up title
                            title = ' '.join(title.split())
                            
                            # Skip if already processed
                            if title in processed_titles:
                                continue
                            processed_titles.add(title)
                            
                            # Skip non-job content
                            skip_words = ['search', 'filter', 'browse', 'categories', 'about us', 'contact', 'home', 'login', 'register', 'sign up', 'newsletter']
                            if any(word in title.lower() for word in skip_words):
                                continue
                            
                            # Extract job link
                            link = "https://www.brightermonday.co.ke"
                            if hasattr(card, 'get') and card.get('href'):
                                href = card.get('href')
                                link = href if href.startswith('http') else urljoin("https://www.brightermonday.co.ke", href)
                            elif hasattr(card, 'find'):
                                link_elem = card.find('a')
                                if link_elem and link_elem.get('href'):
                                    href = link_elem.get('href')
                                    link = href if href.startswith('http') else urljoin("https://www.brightermonday.co.ke", href)
                            
                            # Extract company
                            company = "BrighterMonday Employer"
                            if hasattr(card, 'find'):
                                company_elem = card.find(class_=lambda x: x and 'company' in x.lower())
                                if not company_elem:
                                    # Look for company name in text
                                    company_text = card.get_text()
                                    lines = company_text.split('\n')
                                    for line in lines:
                                        line = line.strip()
                                        if len(line) > 5 and len(line) < 50 and not any(word in line.lower() for word in ['job', 'position', 'vacancy', 'apply', 'salary', 'ksh']):
                                            # This might be a company name
                                            if line != title:
                                                company = line
                                                break
                                
                                if company_elem:
                                    company_text = company_elem.get_text(strip=True)
                                    if company_text and len(company_text) > 2:
                                        company = company_text
                            
                            # Extract location
                            location = "Kenya"
                            if hasattr(card, 'find'):
                                location_elem = card.find(class_=lambda x: x and any(term in x.lower() for term in ['location', 'city', 'place']))
                                if location_elem:
                                    location_text = location_elem.get_text(strip=True)
                                    if location_text and len(location_text) > 2:
                                        location = location_text
                                else:
                                    # Look for common Kenyan cities in the text
                                    card_text = card.get_text().lower()
                                    kenyan_cities = ['nairobi', 'mombasa', 'kisumu', 'nakuru', 'eldoret', 'thika', 'malindi', 'kitale', 'garissa', 'kakamega']
                                    for city in kenyan_cities:
                                        if city in card_text:
                                            location = city.title()
                                            break
                            
                            # Check if job matches interest - use both strict and relaxed matching
                            is_match = False
                            
                            # First try strict matching
                            if matches_search_terms(title, interest, strict=True):
                                is_match = True
                            # Then try relaxed matching
                            elif matches_search_terms(title, interest, strict=False):
                                is_match = True
                            # For STEM jobs, be extra flexible
                            elif interest == 'software engineering':
                                tech_keywords = ['developer', 'programmer', 'software', 'web', 'mobile', 'app', 'code', 'tech', 'it', 'system', 'database', 'api', 'frontend', 'backend', 'fullstack']
                                if any(keyword in title.lower() for keyword in tech_keywords):
                                    is_match = True
                            
                            if is_match:
                                job = {
                                    'id': generate_job_id(title, link),
                                    'title': title,
                                    'link': link,
                                    'location': location,
                                    'company': company,
                                    'source': 'BrighterMonday Advanced'
                                }
                                jobs.append(job)
                                logger.info(f"✅ MATCHED BrighterMonday {interest}: {title[:50]}...")
                                
                                if len(jobs) >= max_jobs:
                                    break
                                    
                        except Exception as e:
                            logger.debug(f"Error processing BrighterMonday card: {str(e)}")
                            continue
                    
                    # Break if we have enough jobs
                    if len(jobs) >= max_jobs:
                        break
                        
                    # Add delay between pages to be respectful
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    logger.debug(f"Error with search query {query} page {page}: {str(e)}")
                    continue
            
            # Break if we have enough jobs
            if len(jobs) >= max_jobs:
                break
                
    except Exception as e:
        logger.error(f"Error in advanced BrighterMonday scraping: {str(e)}")
    
    logger.info(f"📊 BrighterMonday Advanced found {len(jobs)} jobs for {interest}")
    return jobs

def scrape_jobs_multi_source(interest: str, max_jobs: int = 15) -> List[Dict[str, Any]]:
    """Multi-source job scraping for comprehensive coverage"""
    logger.info(f"🚀 MULTI-SOURCE SCRAPER: Searching for {interest} jobs")
    
    start_time = time.time()
    all_jobs = []
    
    # 1. Scrape BrighterMonday Advanced (primary source for comprehensive job coverage)
    try:
        brighter_jobs = scrape_brightermonday_advanced(interest, max_jobs=8)
        all_jobs.extend(brighter_jobs)
        logger.info(f"✅ BrighterMonday Advanced: {len(brighter_jobs)} jobs")
    except Exception as e:
        logger.error(f"BrighterMonday Advanced scraping failed: {str(e)}")
        # Fallback to basic BrighterMonday if advanced fails
        try:
            brighter_jobs = scrape_brightermondayke(interest, max_jobs=6)
            all_jobs.extend(brighter_jobs)
            logger.info(f"✅ BrighterMonday Fallback: {len(brighter_jobs)} jobs")
        except Exception as e2:
            logger.error(f"BrighterMonday Fallback also failed: {str(e2)}")
    
    # 2. Scrape Jobs Kenya (fast, using requests)
    try:
        kenya_jobs = scrape_jobskenya(interest, max_jobs=3)
        all_jobs.extend(kenya_jobs)
        logger.info(f"✅ Jobs Kenya: {len(kenya_jobs)} jobs")
    except Exception as e:
        logger.error(f"Jobs Kenya scraping failed: {str(e)}")
    
    # 3. Scrape MyJobMag (slower, using Playwright)
    try:
        # Run async scraping
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, scrape_myjobmag_enhanced(interest, max_jobs=5))
                myjob_jobs = future.result()
        except RuntimeError:
            myjob_jobs = asyncio.run(scrape_myjobmag_enhanced(interest, max_jobs=5))
        
        all_jobs.extend(myjob_jobs)
        logger.info(f"✅ MyJobMag: {len(myjob_jobs)} jobs")
    except Exception as e:
        logger.error(f"MyJobMag scraping failed: {str(e)}")
    
    # Remove duplicates based on title similarity
    unique_jobs = {}
    for job in all_jobs:
        # Create a key based on title (normalized)
        title_key = job['title'].lower().strip()
        title_key = ' '.join(title_key.split())  # Normalize whitespace
        
        if title_key not in unique_jobs:
            unique_jobs[title_key] = job
        else:
            # Keep the one with more complete information
            existing = unique_jobs[title_key]
            if len(job.get('company', '')) > len(existing.get('company', '')):
                unique_jobs[title_key] = job
    
    final_jobs = list(unique_jobs.values())
    
    # Sort by relevance (strict matches first)
    strict_matches = []
    relaxed_matches = []
    
    for job in final_jobs:
        if matches_search_terms(job['title'], interest, strict=True):
            strict_matches.append(job)
        else:
            relaxed_matches.append(job)
    
    # Combine with strict matches first
    final_jobs = strict_matches + relaxed_matches
    final_jobs = final_jobs[:max_jobs]
    
    elapsed_time = time.time() - start_time
    
    logger.info(f"✅ Multi-source scraper completed in {elapsed_time:.2f}s")
    logger.info(f"📊 Found {len(final_jobs)} unique jobs from multiple sources")
    logger.info(f"📊 Breakdown: {len(strict_matches)} strict matches, {len(relaxed_matches)} relaxed matches")
    
    return final_jobs

# Update main functions to use multi-source scraping
def scrape_jobs_working(interest: str, max_jobs: int = 10) -> List[Dict[str, Any]]:
    """Main working scraper function - now uses multi-source approach"""
    return scrape_jobs_multi_source(interest, max_jobs)

def scrape_jobs(interest: str, max_jobs: int = 10) -> List[Dict[str, Any]]:
    """
    Enhanced job scraping with multi-source support
    """
    logger.info(f"🔍 Enhanced multi-source scraper searching for {interest} jobs")
    
    # Get jobs from multi-source scraper
    raw_jobs = scrape_jobs_multi_source(interest, max_jobs)
    
    if not raw_jobs:
        logger.info(f"No jobs found for {interest}")
        return []
    
    logger.info(f"📊 Got {len(raw_jobs)} raw jobs from multi-source scraper")
    
    # Basic quality filtering
    quality_jobs = []
    
    for job in raw_jobs:
        title = job.get('title', '').lower()
        
        # Skip obviously poor quality jobs
        if any(word in title for word in ['spam', 'scam', 'fake', 'test', 'earn money fast', 'work from home easy']):
            continue
            
        # Prefer jobs with clear titles
        if len(job.get('title', '')) > 10:
            quality_jobs.append(job)
    
    logger.info(f"📋 Quality filtering produced {len(quality_jobs)} jobs")
    
    return quality_jobs[:max_jobs]

def get_job_stats(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get statistics about scraped jobs"""
    if not jobs:
        return {}
    
    stats = {
        'total_jobs': len(jobs),
        'sources': {},
        'locations': {},
        'companies': {}
    }
    
    for job in jobs:
        # Source stats
        source = job.get('source', 'Unknown')
        stats['sources'][source] = stats['sources'].get(source, 0) + 1
        
        # Location stats
        location = job.get('location', 'Unknown')
        stats['locations'][location] = stats['locations'].get(location, 0) + 1
        
        # Company stats
        company = job.get('company', 'Unknown')
        stats['companies'][company] = stats['companies'].get(company, 0) + 1
    
    # AI stats if available
    if AI_AVAILABLE and jobs:
        ai_jobs = [job for job in jobs if 'ai_match_score' in job]
        if ai_jobs:
            avg_match_score = sum(job.get('ai_match_score', 0) for job in ai_jobs) / len(ai_jobs)
            avg_quality_score = sum(job.get('ai_quality_score', 0) for job in ai_jobs) / len(ai_jobs)
            
            stats['ai_stats'] = {
                'avg_match_score': round(avg_match_score, 2),
                'avg_quality_score': round(avg_quality_score, 2),
                'ai_analyzed_jobs': len(ai_jobs)
            }
    
    return stats

def search_jobs_by_keywords(keywords: List[str], max_jobs: int = 5) -> List[Dict[str, Any]]:
    """
    Search for jobs using multiple keywords
    
    Args:
        keywords: List of keywords to search for
        max_jobs: Maximum jobs per keyword
        
    Returns:
        Combined list of jobs from all keywords
    """
    all_jobs = []
    
    for keyword in keywords:
        try:
            jobs = scrape_jobs(keyword, max_jobs)
            all_jobs.extend(jobs)
        except Exception as e:
            logger.error(f"Error searching for {keyword}: {str(e)}")
    
    # Remove duplicates based on job ID
    unique_jobs = {}
    for job in all_jobs:
        job_id = job.get('id')
        if job_id and job_id not in unique_jobs:
            unique_jobs[job_id] = job
    
    return list(unique_jobs.values())

# Alias for backward compatibility
job_scraper = type('JobScraper', (), {
    'search_jobs': scrape_jobs,
    'get_stats': get_job_stats
})()

if __name__ == "__main__":
    # Test the working scraper
    print("🧪 Testing WORKING Job Scraper")
    print("=" * 50)
    
    test_categories = ['software engineering', 'sales & marketing', 'data entry']
    
    for category in test_categories:
        print(f"\n🔍 Testing: {category}")
        print("-" * 30)
        
        jobs = scrape_jobs_working(category)
        
        print(f"📊 Found {len(jobs)} jobs")
        
        for i, job in enumerate(jobs[:3], 1):
            print(f"{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Source: {job['source']}")
            print(f"   Link: {job['link'][:60]}...")
            print() 