import logging
from datetime import datetime
import tkinter as tk
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import quote
from job_filter_ui import JobFilterUI
import sys
import traceback

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create handlers
file_handler = logging.FileHandler('job_scraper.log')
console_handler = logging.StreamHandler(sys.stdout)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class JobScraperApp:
    def __init__(self):
        self.base_url = "https://www.linkedin.com/jobs/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.jobs = []
        self.root = None
        self.ui = None

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
            logger.error(f"Error parsing date {date_text}: {str(e)}")
            return None

    def extract_job_details(self, job_card) -> dict:
        """Extract job details from a job card element"""
        try:
            title_elem = job_card.find('h3', {'class': 'base-search-card__title'})
            company_elem = job_card.find('h4', {'class': 'base-search-card__subtitle'})
            date_elem = job_card.find('time', {'class': 'job-search-card__listdate'})
            link_elem = job_card.find('a', {'class': 'base-card__full-link'})
            location_elem = job_card.find('span', {'class': 'job-search-card__location'})

            title = title_elem.text.strip() if title_elem else 'Unknown Title'
            company = company_elem.text.strip() if company_elem else 'Unknown Company'
            post_date = self.extract_date(date_elem.text.strip()) if date_elem else None
            url = link_elem['href'] if link_elem else None
            location = location_elem.text.strip() if location_elem else 'Unknown Location'

            return {
                'title': title,
                'company': company,
                'post_date': post_date,
                'date_found': datetime.now().strftime('%Y-%m-%d'),
                'url': url,
                'platform': 'LinkedIn',
                'location': location
            }
        except Exception as e:
            logger.error(f"Error extracting job details: {str(e)}")
            return None

    def scrape_job_page(self, page: int) -> bool:
        """Scrape a single page of job listings"""
        try:
            url = self.get_search_url(page)
            logger.info(f"Scraping page {page}: {url}")
            
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
            logger.error(f"Error scraping page {page}: {str(e)}")
            return False

    def scrape_jobs(self, max_pages: int = 5) -> pd.DataFrame:
        """Scrape multiple pages of job listings"""
        logger.info("Starting LinkedIn job scrape")
        page = 1
        
        while page <= max_pages:
            has_jobs = self.scrape_job_page(page)
            if not has_jobs:
                break
            
            logger.info(f"Scraped {len(self.jobs)} jobs so far")
            time.sleep(2)  # Respectful delay between requests
            page += 1

        df = pd.DataFrame(self.jobs)
        if not df.empty:
            df = df[df['post_date'] >= '2025-01-01']  # Filter for jobs after Jan 1, 2025
        
        logger.info(f"Completed scraping with {len(df)} jobs found")
        return df

    def save_jobs_to_csv(self, df: pd.DataFrame) -> str:
        """Save scraped jobs to CSV file"""
        filename = f'linkedin_jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        df.to_csv(filename, index=False)
        return filename

    def run_scraper(self):
        """Run the LinkedIn scraper"""
        try:
            logger.info("Starting LinkedIn scraper")
            df = self.scrape_jobs(max_pages=5)
            filename = self.save_jobs_to_csv(df)
            logger.info(f"Saved {len(df)} jobs to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Scraping error: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def start_ui(self):
        """Initialize and start the UI"""
        try:
            logger.info("Initializing UI")
            self.root = tk.Tk()
            self.ui = JobFilterUI(self.root)
            logger.info("UI initialized successfully")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"UI error: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def run(self):
        """Main application run method"""
        try:
            # First scrape the jobs
            self.run_scraper()
            
            # Then start the UI
            self.start_ui()
            
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Show error in GUI if possible
            if self.root is not None:
                tk.messagebox.showerror("Error", f"An error occurred: {str(e)}")
            raise

def main():
    """Main entry point"""
    try:
        logger.info("Starting application")
        app = JobScraperApp()
        app.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()