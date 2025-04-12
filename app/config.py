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
    BROWSER_WAIT: int = 30  # Seconds to wait for elements
    BROWSER_HEADLESS: bool = True
    BROWSER_WINDOW_WIDTH: int = 1920
    BROWSER_WINDOW_HEIGHT: int = 1080
    
    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 2.0  # Base delay in seconds
    REQUEST_DELAY: float = 1.0  # Delay between requests
    
    # CSS Selectors for job listings
    SELECTORS: Dict[str, str] = field(default_factory=lambda: {
        'job_listing': '.jobs-list div[role="listitem"]',  # Each job listing container
        'job_title': 'h4.font-bold',  # Job title text
        'company_name': 'div.text-gray-900',  # Company name
        'company_description': 'div.text-gray-600',  # Company description
        'job_type': 'span.text-gray-500',  # Job type (Full-time, Part-time, etc)
        'location': 'span.text-gray-500',  # Location info
        'job_url': 'a[href^="/jobs/"]',  # Full job listing URL
        'posted_time': 'span.text-gray-500',  # Posted time
        
        # Job details page selectors
        'job_details': 'div.job-description',  # Job description section
        'company_info': 'div.company-info',  # Company information section
        'requirements': 'div.requirements',  # Job requirements section
        'benefits': 'div.benefits',  # Benefits section
        'tech_stack': 'div.tech-stack',  # Technology stack section
        
        # Company details
        'company_logo': 'img.company-logo',  # Company logo
        'company_website': 'a.company-website',  # Company website link
        'company_size': 'span.company-size',  # Company size
        'funding_stage': 'span.funding-stage',  # Funding information
        'yc_batch': 'span.yc-batch'  # YC batch information
    })
    
    # CSV output settings
    CSV_HEADERS: List[str] = field(default_factory=lambda: [
        'title',
        'company',
        'company_description',
        'location',
        'job_type',
        'url',
        'posted_time',
        'company_size',
        'funding_stage',
        'yc_batch',
        'tech_stack',
        'requirements',
        'benefits',
        'scraped_at'
    ])
    
    CSV_DELIMITER: str = ','
    CSV_QUOTECHAR: str = '"'
    CSV_ENCODING: str = 'utf-8'
    CSV_FILENAME_PREFIX: str = 'yc_jobs'
    
    # Scraping settings
    MAX_PAGES: int = 10  # Maximum number of pages to scrape
    CONCURRENT_WORKERS: int = 4  # Number of concurrent workers for processing
    
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