import json
import os
from datetime import datetime, timedelta
import logging

class CompanyCache:
    def __init__(self, cache_file='company_cache.json', cache_duration_days=14):
        self.cache_file = cache_file
        self.cache_duration = timedelta(days=cache_duration_days)
        self.cache = self._load_cache()
        self.logger = logging.getLogger(__name__)

    def _load_cache(self):
        """Load cache from file or create new cache"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Convert stored timestamps back to datetime objects
                    for company_id, data in cache_data.items():
                        if 'timestamp' in data:
                            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                    return cache_data
        except Exception as e:
            self.logger.error(f"Error loading cache: {str(e)}")
        return {}

    def _save_cache(self):
        """Save cache to file"""
        try:
            cache_to_save = {}
            for company_id, data in self.cache.items():
                cache_to_save[company_id] = {
                    **data,
                    'timestamp': data['timestamp'].isoformat()
                }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_to_save, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving cache: {str(e)}")

    def get_company_info(self, company_id):
        """Get company info from cache if valid"""
        if company_id in self.cache:
            company_data = self.cache[company_id]
            if datetime.now() - company_data['timestamp'] < self.cache_duration:
                return company_data
        return None

    def update_company_info(self, company_id, company_data):
        """Update company information in cache"""
        self.cache[company_id] = {
            **company_data,
            'timestamp': datetime.now()
        }
        self._save_cache()

    def get_cache_stats(self):
        """Get cache statistics"""
        total_entries = len(self.cache)
        valid_entries = sum(1 for data in self.cache.values() 
                          if datetime.now() - data['timestamp'] < self.cache_duration)
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'cache_file_size': os.path.getsize(self.cache_file) if os.path.exists(self.cache_file) else 0
        }

    def cleanup_expired(self):
        """Remove expired entries from cache"""
        current_time = datetime.now()
        expired_keys = [
            k for k, v in self.cache.items() 
            if current_time - v['timestamp'] >= self.cache_duration
        ]
        for k in expired_keys:
            del self.cache[k]
        if expired_keys:
            self._save_cache()
        return len(expired_keys)