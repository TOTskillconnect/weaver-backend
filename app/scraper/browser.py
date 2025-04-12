"""
Browser management module.
"""

from typing import Optional
import logging
import os
import undetected_chromedriver as uc
from selenium.common.exceptions import WebDriverException

from app.config import get_config

logger = logging.getLogger(__name__)

class BrowserManager:
    """Manages browser instances for scraping."""
    
    def __init__(self):
        """Initialize the browser manager."""
        self.config = get_config()
        self.driver: Optional[uc.Chrome] = None
        
    def __enter__(self) -> uc.Chrome:
        """Context manager entry."""
        if not self.driver:
            self.initialize_browser()
        return self.driver
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_browser()
        
    def initialize_browser(self) -> None:
        """Initialize a new browser instance with configured options."""
        try:
            options = uc.ChromeOptions()
            
            # Set headless mode based on config
            if self.config.BROWSER_HEADLESS:
                options.add_argument('--headless=new')
            
            # Add common options for stability
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-extensions')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-infobars')
            
            # Set window size
            options.add_argument(f'--window-size={self.config.BROWSER_WINDOW_WIDTH},'
                               f'{self.config.BROWSER_WINDOW_HEIGHT}')
            
            try:
                self.driver = uc.Chrome(options=options)
                
                # Set timeouts
                self.driver.implicitly_wait(self.config.BROWSER_WAIT)
                
                logger.info("Browser initialized successfully")
                
            except WebDriverException as e:
                logger.error(f"Failed to initialize Chrome browser: {str(e)}")
                raise
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
            
    def close_browser(self) -> None:
        """Safely close the browser instance."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Browser closed successfully")
        except WebDriverException as e:
            logger.error(f"Error closing browser: {str(e)}")
            self.driver = None 