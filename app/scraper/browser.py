"""
Browser management module.
"""

from typing import Optional
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from app.config import get_config

logger = logging.getLogger(__name__)

class BrowserManager:
    """Manages browser instances for scraping."""
    
    def __init__(self):
        """Initialize the browser manager."""
        self.config = get_config()
        self.driver: Optional[webdriver.Chrome] = None
        
    def __enter__(self) -> webdriver.Chrome:
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
            chrome_options = Options()
            
            # Set headless mode based on config
            if self.config.BROWSER_HEADLESS:
                chrome_options.add_argument('--headless=new')
            
            # Add common options for stability
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-infobars')
            
            # Set window size
            chrome_options.add_argument(f'--window-size={self.config.BROWSER_WINDOW_WIDTH},'
                                     f'{self.config.BROWSER_WINDOW_HEIGHT}')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
            
            # Set timeouts
            self.driver.implicitly_wait(self.config.BROWSER_WAIT)
            
            logger.info("Browser initialized successfully")
            
        except WebDriverException as e:
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