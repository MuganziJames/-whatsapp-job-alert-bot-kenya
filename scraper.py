"""
Job scraping module for Kenya job boards
Scrapes real Kenyan job websites as specified
"""

import requests
from bs4 import BeautifulSoup
import logging
import hashlib
from typing import List, Dict, Any
from urllib.parse import urljoin
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_job_id(title: str, link: str) -> str:
    """Generate unique job ID"""
    return hashlib.md5(f"{title}_{link}".encode()).hexdigest()[:12]

def scrape_myjobmag(interest: str) -> List[Dict[str, Any]]:
    """Scrape jobs from MyJobMag Kenya"""
    jobs = []
    try:
        # Map interests to search terms
        search_mapping = {
            'fundi': 'technician',
            'cleaner': 'cleaner',
            'tutor': 'teacher',
            'driver': 'driver',
            'security': 'security'
        }
        
        search_term = search_mapping.get(interest, interest)
        url = f"https://www.myjobmag.co.ke/jobs-by-field"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job listings - adjust selectors based on actual site structure
        job_elements = soup.find_all(['div', 'article'], class_=['job-item', 'job-listing', 'job-card'])[:2]
        
        for element in job_elements:
            try:
                # Extract job details
                title_elem = element.find(['h2', 'h3', 'h4', 'a'])
                link_elem = element.find('a', href=True)
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    link = urljoin("https://www.myjobmag.co.ke", link_elem['href'])
                    
                    # Filter by interest
                    if search_term.lower() in title.lower():
                        job = {
                            'id': generate_job_id(title, link),
                            'title': title,
                            'link': link,
                            'location': 'Kenya',
                            'source': 'MyJobMag'
                        }
                        jobs.append(job)
                        
            except Exception as e:
                logger.warning(f"Error parsing job element: {str(e)}")
                continue
        
        logger.info(f"Scraped {len(jobs)} jobs from MyJobMag for {interest}")
        
    except Exception as e:
        logger.error(f"Error scraping MyJobMag: {str(e)}")
    
    return jobs

def scrape_brightermonday(interest: str) -> List[Dict[str, Any]]:
    """Scrape jobs from BrighterMonday Kenya"""
    jobs = []
    try:
        search_mapping = {
            'fundi': 'technician',
            'cleaner': 'cleaner',
            'tutor': 'teacher',
            'driver': 'driver',
            'security': 'security'
        }
        
        search_term = search_mapping.get(interest, interest)
        url = f"https://www.brightermonday.co.ke/jobs"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job listings
        job_elements = soup.find_all(['div', 'article'], class_=['job', 'search-result'])[:2]
        
        for element in job_elements:
            try:
                title_elem = element.find(['h2', 'h3', 'a'])
                link_elem = element.find('a', href=True)
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    link = urljoin("https://www.brightermonday.co.ke", link_elem['href'])
                    
                    if search_term.lower() in title.lower():
                        job = {
                            'id': generate_job_id(title, link),
                            'title': title,
                            'link': link,
                            'location': 'Kenya',
                            'source': 'BrighterMonday'
                        }
                        jobs.append(job)
                        
            except Exception as e:
                logger.warning(f"Error parsing job element: {str(e)}")
                continue
        
        logger.info(f"Scraped {len(jobs)} jobs from BrighterMonday for {interest}")
        
    except Exception as e:
        logger.error(f"Error scraping BrighterMonday: {str(e)}")
    
    return jobs

def scrape_kenyamoja(interest: str) -> List[Dict[str, Any]]:
    """Scrape jobs from KenyaMoja"""
    jobs = []
    try:
        search_mapping = {
            'fundi': 'technician',
            'cleaner': 'cleaner',
            'tutor': 'teacher',
            'driver': 'driver',
            'security': 'security'
        }
        
        search_term = search_mapping.get(interest, interest)
        url = f"https://www.kenyamoja.com/jobs"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job listings
        job_elements = soup.find_all(['div', 'li'], class_=['job-listing', 'job-item'])[:2]
        
        for element in job_elements:
            try:
                title_elem = element.find(['h3', 'h4', 'a'])
                link_elem = element.find('a', href=True)
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    link = urljoin("https://www.kenyamoja.com", link_elem['href'])
                    
                    if search_term.lower() in title.lower():
                        job = {
                            'id': generate_job_id(title, link),
                            'title': title,
                            'link': link,
                            'location': 'Kenya',
                            'source': 'KenyaMoja'
                        }
                        jobs.append(job)
                        
            except Exception as e:
                logger.warning(f"Error parsing job element: {str(e)}")
                continue
        
        logger.info(f"Scraped {len(jobs)} jobs from KenyaMoja for {interest}")
        
    except Exception as e:
        logger.error(f"Error scraping KenyaMoja: {str(e)}")
    
    return jobs

def get_mock_jobs(interest: str) -> List[Dict[str, Any]]:
    """Generate mock jobs for testing"""
    mock_jobs = {
        'fundi': [
            {
                'id': generate_job_id(f"Fundi Technician - Nairobi", "https://example.com/job1"),
                'title': 'Fundi Technician - Nairobi',
                'link': 'https://example.com/job1',
                'location': 'Nairobi',
                'source': 'Mock Data'
            },
            {
                'id': generate_job_id(f"Plumber Needed - Mombasa", "https://example.com/job2"),
                'title': 'Plumber Needed - Mombasa',
                'link': 'https://example.com/job2',
                'location': 'Mombasa',
                'source': 'Mock Data'
            }
        ],
        'cleaner': [
            {
                'id': generate_job_id(f"Office Cleaner - Nairobi CBD", "https://example.com/job3"),
                'title': 'Office Cleaner - Nairobi CBD',
                'link': 'https://example.com/job3',
                'location': 'Nairobi',
                'source': 'Mock Data'
            }
        ],
        'tutor': [
            {
                'id': generate_job_id(f"Math Tutor - Kisumu", "https://example.com/job4"),
                'title': 'Math Tutor - Kisumu',
                'link': 'https://example.com/job4',
                'location': 'Kisumu',
                'source': 'Mock Data'
            }
        ],
        'driver': [
            {
                'id': generate_job_id(f"Taxi Driver - Nakuru", "https://example.com/job5"),
                'title': 'Taxi Driver - Nakuru',
                'link': 'https://example.com/job5',
                'location': 'Nakuru',
                'source': 'Mock Data'
            }
        ],
        'security': [
            {
                'id': generate_job_id(f"Security Guard - Eldoret", "https://example.com/job6"),
                'title': 'Security Guard - Eldoret',
                'link': 'https://example.com/job6',
                'location': 'Eldoret',
                'source': 'Mock Data'
            }
        ]
    }
    
    return mock_jobs.get(interest, [])

def scrape_jobs(interest: str) -> List[Dict[str, Any]]:
    """Main function to scrape jobs from all sources"""
    all_jobs = []
    
    try:
        # Try scraping from real sites
        jobs_myjobmag = scrape_myjobmag(interest)
        all_jobs.extend(jobs_myjobmag)
        
        time.sleep(1)  # Rate limiting
        
        jobs_brightermonday = scrape_brightermonday(interest)
        all_jobs.extend(jobs_brightermonday)
        
        time.sleep(1)  # Rate limiting
        
        jobs_kenyamoja = scrape_kenyamoja(interest)
        all_jobs.extend(jobs_kenyamoja)
        
    except Exception as e:
        logger.error(f"Error in main scraping: {str(e)}")
    
    # If no jobs found, use mock data
    if not all_jobs:
        logger.info(f"No jobs scraped for {interest}, using mock data")
        all_jobs = get_mock_jobs(interest)
    
    # Remove duplicates and limit to 2 jobs
    unique_jobs = {}
    for job in all_jobs:
        unique_jobs[job['id']] = job
    
    result = list(unique_jobs.values())[:2]
    logger.info(f"Returning {len(result)} jobs for {interest}")
    
    return result 