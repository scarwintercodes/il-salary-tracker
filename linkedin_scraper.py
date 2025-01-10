import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import logging
from urllib.parse import quote
import json

class LinkedInScraper:
    """Scraper for LinkedIn job postings in Illinois"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://www.linkedin.com/jobs/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.jobs = []

    def get_search_url(self, page: int) -> str:
        """Generate search URL for given page"""
        params = {
            'keywords': '',
            'location': 'Illinois',
            'start': (page - 1) * 25,  # LinkedIn uses 25 jobs per page
            'sortBy': 'recent'
        }
        return f"{self.base_url}?{'&'.join(f'{k}={quote(str(v))}' for k, v in params.items())}"

    def extract_date(self, date_text: str) -> str:
        """Extract and standardize post date from LinkedIn format"""
        try:
            if 'hour' in date_text or 'minute' in date_text:
                return datetime.now().strftime('%Y-%m-%d')
            elif 'day' in date_text:
                return (datetime.now() - pd.Timedelta(days=int(date_text.split()[0]))).strftime('%Y-%m-%d')
            elif 'week' in date_text:
                return (datetime.now() - pd.Timedelta(weeks=int(date_text.split()[0]))).strftime('%Y-%m-%d')
            elif 'month' in date_text:
                return (datetime.now() - pd.Timedelta(days=int(date_text.split()[0]) * 30)).strftime('%Y-%m-%d')
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error parsing date {date_text}: {str(e)}")
            return None

    def extract_job_details(self, job_card) -> dict:
        """Extract job details from a job card element"""
        try:
            title_elem = job_card.find('h3', {'class': 'base-search-card__title'})
            company_elem = job_card.find('h4', {'class': 'base-search-card__subtitle'})
            date_elem = job_card.find('time', {'class': 'job-search-card__listdate'})
            link_elem = job_card.find('a', {'class': 'base-card__full-link'})

            title = title_elem.text.strip() if title_elem else 'Unknown Title'
            company = company_elem.text.strip() if company_elem else 'Unknown Company'
            post_date = self.extract_date(date_elem.text.strip()) if date_elem else None
            url = link_elem['href'] if link_elem else None

            return {
                'title': title,
                'company': company,
                'post_date': post_date,
                'date_found': datetime.now().strftime('%Y-%m-%d'),
                'url': url,
                'platform': 'LinkedIn'
            }
        except Exception as e:
            self.logger.error(f"Error extracting job details: {str(e)}")
            return None

    def scrape_job_page(self, page: int) -> bool:
        """Scrape a single page of job listings"""
        try:
            url = self.get_search_url(page)
            self.logger.info(f"Scraping page {page}: {url}")
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.find_all('div', {'class': 'base-card'})
            
            for job_card in job_cards:
                job_details = self.extract_job_details(job_card)
                if job_details:
                    if job_details['post_date'] and datetime.strptime(job_details['post_date'], '%Y-%m-%d') >= datetime(2025, 1, 1):
                        self.jobs.append(job_details)

            return len(job_cards) > 0
            
        except Exception as e:
            self.logger.error(f"Error scraping page {page}: {str(e)}")
            return False

    def scrape_jobs(self, max_pages: int = 5) -> pd.DataFrame:
        """Scrape multiple pages of job listings"""
        self.logger.info("Starting LinkedIn job scrape")
        page = 1
        
        while page <= max_pages:
            has_jobs = self.scrape_job_page(page)
            if not has_jobs:
                break
            
            self.logger.info(f"Scraped {len(self.jobs)} jobs so far")
            time.sleep(2)  # Respectful delay between requests
            page += 1

        df = pd.DataFrame(self.jobs)
        df = df[df['post_date'] >= '2025-01-01']  # Filter for jobs after Jan 1, 2025
        
        self.logger.info(f"Completed scraping with {len(df)} jobs found")
        return df

def save_jobs_to_csv(df: pd.DataFrame) -> str:
    """Save scraped jobs to CSV file"""
    filename = f'linkedin_jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df.to_csv(filename, index=False)
    return filename

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('linkedin_scraper.log'),
            logging.StreamHandler()
        ]
    )

    # Test the scraper
    scraper = LinkedInScraper()
    df = scraper.scrape_jobs(max_pages=5)
    filename = save_jobs_to_csv(df)
    print(f"Saved {len(df)} jobs to {filename}")