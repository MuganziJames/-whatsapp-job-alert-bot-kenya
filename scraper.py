"""
WORKING Job Scraper - Based on Successful Testing
This version actually extracts real jobs from MyJobMag
"""

import asyncio
import logging
import hashlib
import time
from typing import List, Dict, Any
from urllib.parse import urljoin

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

# Enhanced search terms
ENHANCED_SEARCH_TERMS = {
    'data entry': ['data entry', 'data input', 'data processing', 'data clerk', 'data operator', 'typing', 'keying', 'data capture'],
    'sales & marketing': ['sales', 'marketing', 'business development', 'sales rep', 'account manager', 'marketing manager', 'sales executive', 'marketing executive', 'sales agent', 'promoter'],
    'delivery & logistics': ['delivery', 'logistics', 'transport', 'courier', 'driver', 'dispatch', 'shipping', 'warehouse', 'supply chain', 'distribution'],
    'customer service': ['customer service', 'customer support', 'call center', 'help desk', 'customer care', 'client service', 'support agent', 'service representative'],
    'finance & accounting': ['finance', 'accounting', 'bookkeeping', 'accountant', 'financial', 'accounts', 'audit', 'tax', 'payroll', 'finance officer'],
    'admin & office work': ['admin', 'administrative', 'office', 'secretary', 'receptionist', 'clerk', 'assistant', 'coordinator', 'office manager', 'office assistant'],
    'teaching / training': ['teacher', 'training', 'tutor', 'instructor', 'educator', 'trainer', 'teaching', 'academic', 'coach', 'facilitator'],
    'internships / attachments': ['internship', 'intern', 'attachment', 'trainee', 'graduate', 'entry level', 'junior', 'apprentice', 'student'],
    'software engineering': ['software', 'developer', 'programmer', 'engineering', 'coding', 'web developer', 'mobile developer', 'software engineer', 'tech', 'IT', 'systems']
}

def generate_job_id(title: str, link: str) -> str:
    """Generate unique job ID"""
    return hashlib.md5(f"{title}_{link}".encode()).hexdigest()[:12]

def matches_search_terms(title: str, interest: str) -> bool:
    """Check if job title matches any search terms for the interest"""
    if not title:
        return False
        
    search_terms = ENHANCED_SEARCH_TERMS.get(interest, [interest])
    title_lower = title.lower()
    
    return any(term.lower() in title_lower for term in search_terms)

async def scrape_myjobmag_working(interest: str) -> List[Dict[str, Any]]:
    """Scrape MyJobMag with working selectors and proper category filtering"""
    jobs = []
    
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("⚠️ Playwright not available, cannot scrape MyJobMag")
        return jobs
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            logger.info(f"🔍 Scraping MyJobMag for {interest} jobs with WORKING selectors...")
            
            # Try to search for specific category first
            search_terms = ENHANCED_SEARCH_TERMS.get(interest, [interest])
            primary_search_term = search_terms[0] if search_terms else interest
            
            # Navigate to MyJobMag search page
            search_url = f"https://www.myjobmag.co.ke/jobs?q={primary_search_term.replace(' ', '+')}"
            logger.info(f"🔍 Searching: {search_url}")
            
            try:
                await page.goto(search_url, timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Check if we got search results
                search_results = await page.query_selector_all('h2, h3, .job-title, [class*="job"], [class*="title"]')
                logger.info(f"🔍 Found {len(search_results)} potential job elements on search page")
                
                if len(search_results) < 5:
                    # Fall back to main page if search didn't work well
                    logger.info("🔄 Search results limited, falling back to main page")
                    await page.goto("https://www.myjobmag.co.ke", timeout=30000)
                    await page.wait_for_timeout(5000)
                
            except Exception as e:
                logger.info(f"🔄 Search page failed, using main page: {str(e)}")
                await page.goto("https://www.myjobmag.co.ke", timeout=30000)
                await page.wait_for_timeout(5000)
            
            # Get all potential job elements
            h2_elements = await page.query_selector_all('h2')
            h3_elements = await page.query_selector_all('h3')
            job_links = await page.query_selector_all('a[href*="job"]')
            
            logger.info(f"✅ Found {len(h2_elements)} H2, {len(h3_elements)} H3, {len(job_links)} job links")
            
            # Process H2 and H3 elements (job titles)
            all_title_elements = h2_elements + h3_elements
            category_matched_jobs = []
            fallback_jobs = []
            
            for i, element in enumerate(all_title_elements[:25]):  # Process more elements
                try:
                    title_text = await element.inner_text()
                    
                    if not title_text or len(title_text.strip()) < 10:
                        continue
                        
                    title = title_text.strip()
                    
                    # Skip clearly non-job content
                    skip_words = ['statistics', 'tips', 'strategies', 'blog', 'guide', 'how to', 'latest news', 'trending']
                    if any(word in title.lower() for word in skip_words):
                        continue
                    
                    # Try to get link
                    link = "https://www.myjobmag.co.ke"
                    try:
                        parent_link = await element.query_selector('xpath=./ancestor::a[1]')
                        if parent_link:
                            href = await parent_link.get_attribute('href')
                            if href:
                                link = href if href.startswith('http') else urljoin("https://www.myjobmag.co.ke", href)
                        else:
                            nearby_link = await element.query_selector('xpath=./following-sibling::a[1] | ./preceding-sibling::a[1]')
                            if nearby_link:
                                href = await nearby_link.get_attribute('href')
                                if href:
                                    link = href if href.startswith('http') else urljoin("https://www.myjobmag.co.ke", href)
                    except:
                        pass
                    
                    # Extract company and location from title
                    company = "MyJobMag Company"
                    location = "Kenya"
                    original_title = title
                    
                    # Parse title for company (usually after "at")
                    if " at " in title:
                        parts = title.split(" at ")
                        if len(parts) >= 2:
                            company = parts[-1].strip()
                            title = parts[0].strip()
                    
                    # Parse for location (usually after "-")
                    if " - " in title:
                        parts = title.split(" - ")
                        if len(parts) >= 2:
                            location = parts[-1].strip()
                            title = " - ".join(parts[:-1]).strip()
                    
                    job = {
                        'id': generate_job_id(original_title, link),
                        'title': title,
                        'link': link,
                        'location': location,
                        'company': company,
                        'source': 'MyJobMag (Working)'
                    }
                    
                    # Strict category matching first
                    if matches_search_terms(title, interest):
                        category_matched_jobs.append(job)
                        logger.info(f"✅ MATCHED {interest}: {title[:50]}...")
                    else:
                        # Keep as fallback if it looks like a real job
                        job_indicators = ['position', 'officer', 'manager', 'assistant', 'coordinator', 'specialist', 'representative', 'agent', 'analyst', 'developer', 'engineer', 'executive']
                        if any(indicator in title.lower() for indicator in job_indicators):
                            fallback_jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error processing title element {i}: {str(e)}")
                    continue
            
            # Process job links for additional matches
            for i, link_element in enumerate(job_links[:15]):
                try:
                    link_text = await link_element.inner_text()
                    href = await link_element.get_attribute('href')
                    
                    if not link_text or not href or len(link_text.strip()) < 10:
                        continue
                    
                    # Skip navigation links
                    if any(word in link_text.lower() for word in ['jobs by', 'find jobs', 'search', 'browse', 'view all', 'see more']):
                        continue
                    
                    title = link_text.strip()
                    full_link = href if href.startswith('http') else urljoin("https://www.myjobmag.co.ke", href)
                    
                    if matches_search_terms(title, interest):
                        job = {
                            'id': generate_job_id(title, full_link),
                            'title': title,
                            'link': full_link,
                            'location': 'Kenya',
                            'company': 'MyJobMag Employer',
                            'source': 'MyJobMag (Links)'
                        }
                        category_matched_jobs.append(job)
                        logger.info(f"✅ MATCHED LINK {interest}: {title[:50]}...")
                
                except Exception as e:
                    logger.debug(f"Error processing link {i}: {str(e)}")
                    continue
            
            # Prioritize category matches, use fallback if needed
            if len(category_matched_jobs) >= 3:
                jobs = category_matched_jobs[:5]
                logger.info(f"🎯 Using {len(jobs)} category-matched jobs for {interest}")
            elif len(category_matched_jobs) > 0:
                # Mix category matches with best fallback jobs
                jobs = category_matched_jobs + fallback_jobs[:5-len(category_matched_jobs)]
                logger.info(f"🎯 Using {len(category_matched_jobs)} matched + {len(jobs)-len(category_matched_jobs)} fallback jobs for {interest}")
            else:
                # Use fallback jobs but mark them clearly
                jobs = fallback_jobs[:5]
                for job in jobs:
                    job['title'] = f"[General] {job['title']}"
                    job['source'] = f"MyJobMag (General - {interest} not found)"
                logger.info(f"⚠️ No specific {interest} jobs found, using {len(jobs)} general jobs")
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"Error scraping MyJobMag: {str(e)}")
    
    return jobs

def scrape_jobs_working(interest: str, max_jobs: int = 10) -> List[Dict[str, Any]]:
    """Main working scraper function"""
    logger.info(f"🚀 WORKING SCRAPER: Searching for {interest} jobs")
    
    start_time = time.time()
    
    # Run async scraping - handle existing event loop
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # If we're already in an event loop, create a task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, scrape_myjobmag_working(interest))
            jobs = future.result()
    except RuntimeError:
        # No event loop running, create a new one
        jobs = asyncio.run(scrape_myjobmag_working(interest))
    
    # Remove duplicates
    unique_jobs = {}
    for job in jobs:
        unique_jobs[job['id']] = job
    
    final_jobs = list(unique_jobs.values())
    
    elapsed_time = time.time() - start_time
    
    logger.info(f"✅ Working scraper completed in {elapsed_time:.2f}s")
    logger.info(f"📊 Found {len(final_jobs)} unique jobs from MyJobMag")
    
    return final_jobs

def scrape_jobs(interest: str, max_jobs: int = 10) -> List[Dict[str, Any]]:
    """
    Enhanced job scraping with AI filtering and ranking
    
    Args:
        interest: Job category to search for
        max_jobs: Maximum number of jobs to return
        
    Returns:
        List of enhanced job dictionaries
    """
    logger.info(f"🔍 Enhanced scraper searching for {interest} jobs")
    
    # Get jobs from working scraper
    raw_jobs = scrape_jobs_working(interest, max_jobs)
    
    if not raw_jobs:
        logger.info(f"No jobs found for {interest}")
        return []
    
    logger.info(f"📊 Got {len(raw_jobs)} raw jobs from scraper")
    
    # Simple filtering without AI to preserve rate limits
    logger.info("📋 Using basic job filtering (AI disabled to preserve rate limits)")
    
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
    
    logger.info(f"📋 Basic filtering produced {len(quality_jobs)} jobs")
    
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