import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import json
import time
from collections import deque

# Set up detailed logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_debug.log'),
        logging.StreamHandler()
    ]
)

class RateLimiter:
    """Rate limiter using token bucket algorithm"""
    
    def __init__(self, max_requests: int = 60, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.logger = logging.getLogger(__name__)

    def wait_if_needed(self):
        now = datetime.now()
        while self.requests and self.requests[0] < now - timedelta(seconds=self.time_window):
            self.requests.popleft()
        
        if len(self.requests) >= self.max_requests:
            wait_time = (self.requests[0] + timedelta(seconds=self.time_window) - now).total_seconds()
            if wait_time > 0:
                self.logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
        
        self.requests.append(now)

class TheirStackAPIClient:
    """Client for interacting with TheirStack API with enhanced debugging"""
    
    def __init__(self, api_key: str):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing TheirStack API Client")
        
        # Log API key length and format check
        self.logger.debug(f"API key length: {len(api_key)}")
        self.logger.debug(f"API key starts with: {api_key[:10]}...")
        
        self.base_url = "https://api.theirstack.com/v1"
        self.api_key = api_key
        
        # Create headers with explicit string concatenation
        auth_header = "Bearer " + api_key
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": auth_header
        }
        
        # Log headers (excluding full API key)
        safe_headers = self.headers.copy()
        safe_headers["Authorization"] = safe_headers["Authorization"][:20] + "..."
        self.logger.debug(f"Initialized headers: {json.dumps(safe_headers, indent=2)}")
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(max_requests=60, time_window=60)
        
        # Test API connection
        self.test_connection()

    def test_connection(self):
        """Test API connection and authorization"""
        try:
            self.logger.info("Testing API connection...")
            
            # Make a minimal test request
            test_payload = {
                "limit": 1,
                "page": 0,
                "company_location_pattern_or": ["Chicago"],
                "posted_at_max_age_days": 1
            }
            
            response = requests.post(
                f"{self.base_url}/jobs/search",
                headers=self.headers,
                data=json.dumps(test_payload)
            )
            
            self.logger.debug(f"Test request URL: {response.url}")
            self.logger.debug(f"Test request status code: {response.status_code}")
            
            if response.status_code == 200:
                self.logger.info("API connection test successful")
            else:
                self.logger.error(f"API connection test failed with status {response.status_code}")
                self.logger.debug(f"Response headers: {dict(response.headers)}")
                self.logger.debug(f"Response body: {response.text[:500]}...")
                
            response.raise_for_status()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API connection test failed: {str(e)}")
            if hasattr(e.response, 'text'):
                self.logger.debug(f"Error response body: {e.response.text}")
            raise

    def search_jobs(self, cities: List[str] = None, max_age_days: int = 10, 
                   page: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Search for jobs with detailed logging"""
        if cities is None:
            cities = ["Chicago", "Rockford", "Peoria"]

        payload = {
            "order_by": [{"desc": True, "field": "num_jobs"}],
            "include_total_results": False,
            "company_location_pattern_or": cities,
            "posted_at_max_age_days": max_age_days,
            "company_country_code_or": ["US"],
            "max_salary_usd": 1,
            "job_location_pattern_or": cities + ["Illinois", "Greater Chicago Area"],
            "page": page,
            "limit": limit,
            "blur_company_data": False
        }

        self.logger.debug(f"Preparing job search request - Page: {page}, Limit: {limit}")
        self.logger.debug(f"Search payload: {json.dumps(payload, indent=2)}")

        try:
            # Log request attempt
            self.logger.info(f"Making API request to {self.base_url}/jobs/search")
            
            # Check rate limit
            self.rate_limiter.wait_if_needed()
            
            # Make request
            response = requests.post(
                f"{self.base_url}/jobs/search",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            # Log response details
            self.logger.debug(f"Response status code: {response.status_code}")
            self.logger.debug(f"Response headers: {dict(response.headers)}")
            
            # Raise for status
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            self.logger.info(f"Successfully retrieved {len(data.get('jobs', []))} jobs")
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            self.logger.error(f"Request URL: {self.base_url}/jobs/search")
            
            # Create sanitized headers for logging
            sanitized_headers = self.headers.copy()
            sanitized_headers["Authorization"] = sanitized_headers["Authorization"][:20] + "..."
            self.logger.error(f"Request headers (sanitized): {sanitized_headers}")
            
            self.logger.error(f"Request payload: {json.dumps(payload, indent=2)}")
            
            if hasattr(e.response, 'text'):
                self.logger.error(f"Error response: {e.response.text}")
            raise

    def fetch_all_jobs(self, max_age_days: int = 10) -> pd.DataFrame:
        """Fetch all jobs with enhanced error handling and logging"""
        all_jobs = []
        page = 0
        limit = 100
        retry_count = 0
        max_retries = 3
        retry_delay = 5

        self.logger.info(f"Starting job fetch - Max age: {max_age_days} days")

        try:
            while True:
                try:
                    self.logger.debug(f"Fetching page {page}")
                    response_data = self.search_jobs(
                        max_age_days=max_age_days,
                        page=page,
                        limit=limit
                    )
                    
                    jobs = response_data.get('jobs', [])
                    self.logger.info(f"Retrieved {len(jobs)} jobs from page {page}")
                    
                    if not jobs:
                        self.logger.info("No more jobs to fetch")
                        break

                    for job in jobs:
                        processed_job = {
                            'post_date': job.get('posted_at'),
                            'date_found': datetime.now().strftime('%Y-%m-%d'),
                            'platform': job.get('source'),
                            'company': job.get('company_name'),
                            'title': job.get('title'),
                            'url': job.get('url'),
                            'location': job.get('location'),
                            'description': job.get('description')
                        }
                        all_jobs.append(processed_job)

                    if len(jobs) < limit:
                        self.logger.info("Reached last page of results")
                        break
                        
                    page += 1

                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    self.logger.warning(f"Request failed on page {page}, attempt {retry_count}/{max_retries}")
                    self.logger.debug(f"Error details: {str(e)}")
                    
                    if retry_count > max_retries:
                        self.logger.error("Max retries exceeded")
                        raise
                    
                    wait_time = retry_delay * retry_count
                    self.logger.info(f"Waiting {wait_time} seconds before retry")
                    time.sleep(wait_time)
                    continue

            # Create DataFrame
            df = pd.DataFrame(all_jobs)
            self.logger.info(f"Created DataFrame with {len(df)} jobs")
            
            # Convert dates
            df['post_date'] = pd.to_datetime(df['post_date'])
            
            # Filter for jobs after Jan 1, 2025
            df = df[df['post_date'] >= '2025-01-01']
            self.logger.info(f"Filtered to {len(df)} jobs after 2025-01-01")
            
            return df

        except Exception as e:
            self.logger.error(f"Error in fetch_all_jobs: {str(e)}")
            raise

def save_jobs_to_csv(df: pd.DataFrame, filename: str = None) -> str:
    """Save jobs to CSV with logging"""
    logger = logging.getLogger(__name__)
    
    if filename is None:
        filename = f'non_compliant_jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    try:
        df.to_csv(filename, index=False)
        logger.info(f"Successfully saved {len(df)} jobs to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving to CSV: {str(e)}")
        raise

if __name__ == "__main__":
    # Test the API client
    logging.info("Starting API client test")
    API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzY2Fyd2ludGVya2Vsc2V5QGdtYWlsLmNvbSIsInBlcm1pc3Npb25zIjoidXNlciJ9.AzWYwlB1kp0Wdz0uOBGNZ8VvdlAshS0UhEtolpyQflg"
    
    try:
        client = TheirStackAPIClient(API_KEY)
        logging.info("Successfully initialized API client")
        
        # Test a single API call
        response = client.search_jobs(max_age_days=1, limit=1)
        logging.info("Test API call successful")
        
        # Test full job fetching
        df = client.fetch_all_jobs(max_age_days=10)
        filename = save_jobs_to_csv(df)
        logging.info(f"Full test complete - Saved {len(df)} jobs to {filename}")
        
    except Exception as e:
        logging.error(f"Test failed: {str(e)}")
        raise