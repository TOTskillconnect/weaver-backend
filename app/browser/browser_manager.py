"""
Browser management module.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from app.config import get_config

class BrowserManager:
    """Manages browser instances for web scraping."""
    
    def __init__(self):
        """Initialize browser manager with configuration."""
        self.config = get_config()
        self.driver = None
    
    def get_browser(self) -> webdriver.Chrome:
        """
        Get or create a browser instance.
        
        Returns:
            webdriver.Chrome: Configured Chrome browser instance
        """
        if self.driver is None:
            self._initialize_browser()
        return self.driver
    
    def _initialize_browser(self):
        """Initialize Chrome browser with configured options."""
        options = Options()
        
        # Set headless mode
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
        
        # Initialize Chrome driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Set implicit wait time
        self.driver.implicitly_wait(self.config.BROWSER_WAIT)
    
    def close(self):
        """Close browser instance if it exists."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass  # Ignore errors during cleanup
            finally:
                self.driver = None
    
    def __enter__(self):
        """Context manager entry."""
        return self.get_browser()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 