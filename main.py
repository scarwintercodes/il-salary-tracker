import logging
from datetime import datetime
import tkinter as tk
from linkedin_scraper import LinkedInScraper, save_jobs_to_csv
from job_filter_ui import JobFilterUI

# Configure logging
logging.basicConfig(
    filename='job_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class JobScraperApp:
    def __init__(self):
        self.scraper = LinkedInScraper()
        self.root = None
        self.ui = None

    def fetch_new_jobs(self):
        """Fetch new jobs using LinkedIn scraper"""
        try:
            logger.info("Starting job fetch process")
            df = self.scraper.scrape_jobs(max_pages=5)
            filename = save_jobs_to_csv(df)
            logger.info(f"Saved {len(df)} jobs to {filename}")
            
            # If UI exists, refresh it
            if self.ui:
                self.ui.load_data()
            
            return filename
        except Exception as e:
            logger.error(f"Error fetching jobs: {str(e)}")
            raise

    def run(self):
        """Run the application"""
        try:
            # Fetch initial jobs
            self.fetch_new_jobs()
            
            # Create and run UI
            self.root = tk.Tk()
            self.ui = JobFilterUI(self.root)
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            raise

def main():
    app = JobScraperApp()
    app.run()

if __name__ == "__main__":
    main()