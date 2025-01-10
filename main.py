import logging
from datetime import datetime
import tkinter as tk
from api_client import TheirStackAPIClient, save_jobs_to_csv
from job_filter_ui import JobFilterUI

# Configure logging
logging.basicConfig(
    filename='job_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def fetch_new_jobs():
    """Fetch new jobs using the API client"""
    try:
        API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzY2Fyd2ludGVya2Vsc2V5QGdtYWlsLmNvbSIsInBlcm1pc3Npb25zIjoidXNlciJ9.AzWYwlB1kp0Wdz0uOBGNZ8VvdlAshS0UhEtolpyQflg'
        
        logger.info("Starting job fetch process")
        client = TheirStackAPIClient(API_KEY)
        df = client.fetch_all_jobs(max_age_days=10)
        filename = save_jobs_to_csv(df)
        logger.info(f"Saved {len(df)} jobs to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error fetching jobs: {str(e)}")
        raise

def main():
    try:
        # Fetch initial jobs
        fetch_new_jobs()
        
        # Launch UI
        root = tk.Tk()
        app = JobFilterUI(root, refresh_callback=fetch_new_jobs)
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
