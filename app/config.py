"""
Application configuration module.
"""

import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class Config:
    """Application configuration."""
    
    # Browser settings
    BROWSER_WAIT: int = 10  # Seconds to wait for elements
    BROWSER_HEADLESS: bool = True
    BROWSER_WINDOW_WIDTH: int = 1920
    BROWSER_WINDOW_HEIGHT: int = 1080
    
    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0  # Base delay in seconds
    REQUEST_DELAY: float = 0.5  # Delay between requests
    
    # CSS Selectors for job listings
    SELECTORS: Dict[str, str] = field(default_factory=lambda: {
        'job_listing': '.job-listing',  # Main job listing container
        'job_title': '.job-title',      # Job title element
        'company_name': '.company-name', # Company name element
        'job_url': '.job-link',         # Job URL element
        'job_details': '.job-details'    # Job details element
    })
    
    # CSV output settings
    CSV_HEADERS: List[str] = field(default_factory=lambda: [
        'title',
        'company',
        'url',
        'details',
        'scraped_at'
    ])
    CSV_DELIMITER: str = ','
    CSV_QUOTECHAR: str = '"'
    CSV_ENCODING: str = 'utf-8'
    CSV_FILENAME_PREFIX: str = 'yc_jobs'
    
    # CSV column configuration
    CSV_COLUMNS: List[str] = field(default_factory=lambda: [
        'role_page_url',
        'founder_name',
        'founder_title',
        'linkedin_url',
        'extraction_timestamp',
        'status'
    ])
    
    # Logging settings
    LOG_LEVEL: int = logging.INFO
    DEBUG: bool = False

    def setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=self.LOG_LEVEL,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG: bool = True
    LOG_LEVEL: int = logging.DEBUG
    BROWSER_HEADLESS: bool = False  # Show browser in development

class TestingConfig(Config):
    """Testing configuration."""
    TESTING: bool = True
    BROWSER_HEADLESS: bool = True
    LOG_LEVEL: int = logging.DEBUG
    MAX_PAGES: int = 2  # Limit pages during testing
    CONCURRENT_WORKERS: int = 2  # Reduce concurrency in testing

class ProductionConfig(Config):
    """Production configuration."""
    LOG_LEVEL: int = logging.WARNING
    BROWSER_HEADLESS: bool = True
    MAX_RETRIES: int = 5  # More retries in production
    CONCURRENT_WORKERS: int = 8  # More workers in production

def get_config() -> Config:
    """
    Get application configuration.
    
    Returns:
        Config instance based on environment
    """
    env = os.getenv('FLASK_ENV', 'development')
    config_map = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig
    }
    config_class = config_map.get(env, DevelopmentConfig)
    return config_class()

# Create initial configuration instance
current_config = get_config() 