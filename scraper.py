"""
Enhanced Job Scraper with AI Integration
Combines working scraper with AI-powered job filtering and ranking
"""

import logging
from typing import List, Dict, Any
from working_scraper import scrape_jobs_working

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
    raw_jobs = scrape_jobs_working(interest)
    
    if not raw_jobs:
        logger.info(f"No jobs found for {interest}")
        return []
    
    logger.info(f"📊 Got {len(raw_jobs)} raw jobs from scraper")
    
    # AI Enhancement
    if AI_AVAILABLE:
        logger.info("🤖 Applying AI enhancements...")
        
        enhanced_jobs = []
        
        for job in raw_jobs:
            try:
                # Use AI to analyze job quality and relevance
                analysis = improve_job_matching(
                    job.get('title', ''),
                    job.get('company', ''),
                    interest
                )
                
                # Add AI scores to job
                job['ai_match_score'] = analysis['match_score']
                job['ai_quality_score'] = analysis['quality_score']
                job['ai_should_send'] = analysis['should_send']
                job['ai_analysis'] = analysis.get('analysis', '')
                
                # Only include jobs that pass AI filtering
                if analysis['should_send']:
                    enhanced_jobs.append(job)
                    
            except Exception as e:
                logger.error(f"Error analyzing job {job.get('title', 'Unknown')}: {str(e)}")
                # Include job without AI analysis if AI fails
                job['ai_match_score'] = 50
                job['ai_quality_score'] = 50
                job['ai_should_send'] = True
                enhanced_jobs.append(job)
        
        # Sort by AI scores (match score first, then quality score)
        enhanced_jobs.sort(
            key=lambda x: (x.get('ai_match_score', 50), x.get('ai_quality_score', 50)), 
            reverse=True
        )
        
        logger.info(f"🤖 AI filtered to {len(enhanced_jobs)} high-quality jobs")
        
        return enhanced_jobs[:max_jobs]
    
    else:
        # Standard filtering without AI
        logger.info("📋 Using standard job filtering")
        
        # Basic quality filtering
        quality_jobs = []
        
        for job in raw_jobs:
            title = job.get('title', '').lower()
            
            # Skip obviously poor quality jobs
            if any(word in title for word in ['spam', 'scam', 'fake', 'test']):
                continue
                
            # Prefer jobs with clear titles
            if len(job.get('title', '')) > 10:
                quality_jobs.append(job)
        
        logger.info(f"📋 Standard filtering produced {len(quality_jobs)} jobs")
        
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
    # Test the enhanced scraper
    print("🧪 Testing Enhanced Job Scraper")
    print("=" * 50)
    
    test_categories = ['software engineering', 'sales & marketing', 'data entry']
    
    for category in test_categories:
        print(f"\n🔍 Testing: {category}")
        print("-" * 30)
        
        jobs = scrape_jobs(category, max_jobs=3)
        stats = get_job_stats(jobs)
        
        print(f"📊 Found {len(jobs)} jobs")
        
        if stats.get('ai_stats'):
            print(f"🤖 AI Match Score: {stats['ai_stats']['avg_match_score']}")
            print(f"🤖 AI Quality Score: {stats['ai_stats']['avg_quality_score']}")
        
        for i, job in enumerate(jobs, 1):
            print(f"\n{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Source: {job['source']}")
            
            if 'ai_match_score' in job:
                print(f"   AI Match: {job['ai_match_score']}/100")
                print(f"   AI Quality: {job['ai_quality_score']}/100")
            
            print(f"   Link: {job['link'][:60]}...")
        
        print(f"\n📈 Stats: {stats}")
        print() 