import pandas as pd
import numpy as np
from datetime import datetime
import logging
import os
from typing import Tuple, Optional
import dateparser

# set up logging
logging.basicConfig(
    filename='job_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DataValidator:
    """Handles data validation and repair for job posting data"""
    
    ILLINOIS_LOCATIONS = {
        'cities': [
            'chicago', 'aurora', 'rockford', 'joliet', 'naperville', 
            'springfield', 'peoria', 'elgin', 'waukegan', 'champaign',
            'bloomington', 'decatur', 'evanston', 'schaumburg', 'bolingbrook',
            'palatine', 'skokie', 'des plaines', 'orland park', 'tinley park',
            'oak lawn', 'berwyn', 'mount prospect', 'normal', 'wheaton',
            'hoffman estates', 'downers grove', 'gurnee', 'oak park', 'lombard',
            'buffalo grove', 'crystal lake', 'quincy', 'romeoville', 'moline',
            'urbana', 'belleville', 'rockton', 'rock island', 'dekalb'
        ],
        'regions': [
            'chicago metropolitan area', 'greater chicago', 'chicagoland',
            'northern illinois', 'central illinois', 'southern illinois',
            'quad cities', 'metro east', 'fox valley'
        ],
        'identifiers': [
            'il', 'ill', 'illinois', 'chicago area', 'chicago, il',
            'chicago region', 'illinois region'
        ]
    }

    def validate_illinois_location(self, location_text: str) -> bool:
        """
        Validate if a location is in Illinois
        
        Args:
            location_text: Location string to validate
            
        Returns:
            bool: True if location is in Illinois, False otherwise
        """
        if not location_text or not isinstance(location_text, str):
            return False
            
        # convert to lowercase for comparison
        location_text = location_text.lower().strip()
        
        # direct match with cities
        for city in self.ILLINOIS_LOCATIONS['cities']:
            if city in location_text:
                return True
        
        # check for regions
        for region in self.ILLINOIS_LOCATIONS['regions']:
            if region in location_text:
                return True
                
        # check for state identifiers
        for identifier in self.ILLINOIS_LOCATIONS['identifiers']:
            if identifier in location_text:
                return True
        
        # check for hyphenated city names
        for city in self.ILLINOIS_LOCATIONS['cities']:
            if city.replace(' ', '-') in location_text:
                return True
        
        # may be unnecessary, LI posts are standardized re: city
        # check for common formats like "City, IL" or "City (IL)"
        for city in self.ILLINOIS_LOCATIONS['cities']:
            patterns = [
                f"{city}, il",
                f"{city}, ill",
                f"{city}, illinois",
                f"{city} il",
                f"{city} (il)",
                f"{city} illinois"
            ]
            if any(pattern in location_text for pattern in patterns):
                return True
        
        return False

    def get_city_from_location(self, location_text: str) -> str:
        """
        Extract city name from location string if it's in Illinois
        
        Args:
            location_text: Location string to parse
            
        Returns:
            str: City name if found, otherwise 'Unknown'
        """
        if not location_text or not isinstance(location_text, str):
            return 'Unknown'
            
        location_text = location_text.lower().strip()
        
        # check for exact city matches
        for city in self.ILLINOIS_LOCATIONS['cities']:
            if city in location_text:
                return city.title()
        
        # check for hyphenated cities
        for city in self.ILLINOIS_LOCATIONS['cities']:
            if city.replace(' ', '-') in location_text:
                return city.title()
        
        # check for cities with state abbreviations
        for city in self.ILLINOIS_LOCATIONS['cities']:
            patterns = [
                f"{city}, il",
                f"{city}, ill",
                f"{city} il",
                f"{city} (il)"
            ]
            if any(pattern in location_text for pattern in patterns):
                return city.title()
        
        # if no specific city found but location is in Illinois
        if any(region in location_text for region in self.ILLINOIS_LOCATIONS['regions']):
            if 'chicago' in location_text:
                return 'Chicago Area'
            return 'Illinois Region'
            
        return 'Unknown'
    
    REQUIRED_COLUMNS = [
        'date_found', 'post_date', 'platform', 'company', 'title', 'url', 'location'
    ]
    
    DATE_FORMATS = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%b %d, %Y',
        '%B %d, %Y'
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_csv_structure(self, df: pd.DataFrame) -> Tuple[bool, list]:
        """
        Validate the structure of the CSV data
        
        Returns:
        Tuple[bool, list]: (is_valid, list of missing columns)
        """
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        is_valid = len(missing_columns) == 0
        
        if not is_valid:
            self.logger.error(f"Missing required columns: {missing_columns}")
        
        return is_valid, missing_columns

    def repair_missing_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add missing columns with default values"""
        for column in self.REQUIRED_COLUMNS:
            if column not in df.columns:
                self.logger.info(f"Adding missing column: {column}")
                df[column] = None
        return df

    def parse_date_with_formats(self, date_str: str) -> Optional[datetime]:
        """Try parsing date string with multiple formats"""
        if pd.isna(date_str):
            return None
            
        #try standard formats first
        for date_format in self.DATE_FORMATS:
            try:
                return datetime.strptime(str(date_str), date_format)
            except ValueError:
                continue
        
        #try dateparser for more complex formats
        try:
            parsed_date = dateparser.parse(str(date_str))
            if parsed_date:
                return parsed_date
        except Exception as e:
            self.logger.warning(f"dateparser failed for {date_str}: {str(e)}")
        
        return None

    def repair_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Repair and standardize date columns"""
        for date_column in ['date_found', 'post_date']:
            if date_column in df.columns:
                self.logger.info(f"Repairing {date_column} column")
                
                #convert to datetime with pandas first
                df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
                
                #try parsing unparsed dates with multiple formats
                mask = df[date_column].isna()
                if mask.any():
                    original_values = df.loc[mask, date_column].index
                    for idx in original_values:
                        original_value = str(df.loc[idx, date_column])
                        parsed_date = self.parse_date_with_formats(original_value)
                        if parsed_date:
                            df.loc[idx, date_column] = parsed_date
                            self.logger.info(f"Successfully parsed date: {original_value} -> {parsed_date}")
                        else:
                            self.logger.warning(f"Could not parse date: {original_value}")
        
        return df

    def validate_urls(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean URLs"""
        if 'url' in df.columns:
            self.logger.info("Validating URLs")
            #remove any whitespace
            df['url'] = df['url'].str.strip()
            
            #ensure URLs start with http:// or https://
            mask = ~df['url'].str.contains('^https?://', na=False, regex=True)
            df.loc[mask, 'url'] = 'https://' + df.loc[mask, 'url']
            
            #log invalid URLs
            invalid_urls = df[~df['url'].str.match(r'^https?://[^\s/$.?#].[^\s]*$', na=False)]
            if not invalid_urls.empty:
                self.logger.warning(f"Found {len(invalid_urls)} invalid URLs")
        
        return df

    # may be unnecessary. LI job titles are standardized re: spacing etc
    def clean_text_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean text fields (company, title)"""
        text_columns = ['company', 'title']
        for column in text_columns:
            if column in df.columns:
                self.logger.info(f"Cleaning {column} column")
                #remove extra whitespace
                df[column] = df[column].str.strip()
                #replace multiple spaces with single space
                df[column] = df[column].str.replace(r'\s+', ' ', regex=True)
                #remove special characters
                df[column] = df[column].str.replace(r'[^\w\s-]', '', regex=True)
        
        return df

    def validate_and_repair_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
        """
        Main function to validate and repair the dataset
        
        Returns:
        Tuple[pd.DataFrame, bool]: (repaired_dataframe, is_valid)
        """
        try:
            self.logger.info("Starting data validation and repair")
            
            #check structure
            is_valid, missing_columns = self.validate_csv_structure(df)
            if not is_valid:
                df = self.repair_missing_columns(df)
            
            #repair dates
            df = self.repair_dates(df)
            
            #validate URLs
            df = self.validate_urls(df)
            
            #clean text fields
            df = self.clean_text_fields(df)
            
            self.logger.info("Data validation and repair completed successfully")
            return df, True
            
        except Exception as e:
            self.logger.error(f"Error during data validation: {str(e)}")
            return df, False

def get_data_summary(df: pd.DataFrame) -> dict:
    """Generate summary statistics for the dataset"""
    summary = {
        'total_records': len(df),
        'null_counts': df.isnull().sum().to_dict(),
        'platforms': df['platform'].value_counts().to_dict() if 'platform' in df.columns else {},
        'date_range': {
            'earliest_post': df['post_date'].min() if 'post_date' in df.columns else None,
            'latest_post': df['post_date'].max() if 'post_date' in df.columns else None
        }
    }
    logging.info(f"Data summary generated: {summary}")
    return summary