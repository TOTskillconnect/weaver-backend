"""
Core scraping functionality for Y Combinator job pages.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import List, Optional, Generator, Dict
import re
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.config import get_config
from app.scraper.browser import BrowserManager

# Initialize configuration and logging
config = get_config()
logger = logging.getLogger(__name__)

# Initialize browser manager
browser_manager = BrowserManager()

@dataclass
class FounderInfo:
    """Data class to store founder information."""
    role_page_url: str
    founder_name: str
    founder_title: str
    linkedin_url: Optional[str]
    extraction_timestamp: datetime
    status: str = "success"

    def to_dict(self) -> dict:
        """Convert the founder info to a dictionary for CSV export."""
        return {
            "role_page_url": self.role_page_url,
            "founder_name": self.founder_name,
            "founder_title": self.founder_title,
            "linkedin_url": self.linkedin_url or "N/A",
            "extraction_timestamp": self.extraction_timestamp.isoformat(),
            "status": self.status
        }

    @staticmethod
    def validate_linkedin_url(url: Optional[str]) -> Optional[str]:
        """Validate and clean LinkedIn URL."""
        if not url:
            return None
        
        # Basic LinkedIn URL validation
        linkedin_pattern = r'^https?://(?:www\.)?linkedin\.com/.*'
        if re.match(linkedin_pattern, url):
            return url
        return None

class YCombinatorScraper:
    """Scrapes job listings from Y Combinator."""
    
    def __init__(self):
        """Initialize the job scraper."""
        self.config = config
        self.browser = browser_manager
        
    def scrape(self, url: str, max_pages: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Scrape job listings from the given URL.
        
        Args:
            url: Target URL to scrape
            max_pages: Optional maximum number of pages to process
            
        Returns:
            List of job listing dictionaries
        """
        results = []
        retry_count = 0
        
        while retry_count < self.config.MAX_RETRIES:
            try:
                with self.browser as driver:
                    driver.get(url)
                    
                    # Wait for job listings to load
                    job_elements = WebDriverWait(driver, self.config.BROWSER_WAIT).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, self.config.SELECTORS['job_listing']))
                    )
                    
                    for job in job_elements:
                        try:
                            job_data = self._extract_job_data(job)
                            if job_data:
                                results.append(job_data)
                        except Exception as e:
                            logger.error(f"Error extracting job data: {str(e)}")
                            continue
                    
                    return results
                    
            except TimeoutException:
                logger.warning(f"Timeout while loading page (attempt {retry_count + 1}/{self.config.MAX_RETRIES})")
            except WebDriverException as e:
                logger.error(f"Browser error: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                
            retry_count += 1
            if retry_count < self.config.MAX_RETRIES:
                time.sleep(self.config.RETRY_DELAY)
                
        logger.error(f"Failed to scrape jobs after {self.config.MAX_RETRIES} attempts")
        return results
        
    def _extract_job_data(self, job_element) -> Optional[Dict[str, str]]:
        """
        Extract data from a job listing element.
        
        Args:
            job_element: Selenium WebElement containing job listing
            
        Returns:
            Dictionary containing job data or None if extraction fails
        """
        try:
            selectors = self.config.SELECTORS
            
            # Extract job details
            title = job_element.find_element(By.CSS_SELECTOR, selectors['job_title']).text.strip()
            company = job_element.find_element(By.CSS_SELECTOR, selectors['company_name']).text.strip()
            url = job_element.find_element(By.CSS_SELECTOR, selectors['job_url']).get_attribute('href')
            details = job_element.find_element(By.CSS_SELECTOR, selectors['job_details']).text.strip()
            
            return {
                'title': title,
                'company': company,
                'url': url,
                'details': details,
                'scraped_at': datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to extract job data: {str(e)}")
            return None

    def _setup_browser(self) -> None:
        """Set up the browser manager."""
        self.browser = browser_manager
    
    def _extract_role_links(self, max_pages: Optional[int] = None) -> Generator[str, None, None]:
        """
        Extract job role page links from the main jobs page.
        
        Args:
            max_pages: Optional maximum number of pages to process
            
        Yields:
            str: Role page URLs
        """
        page_count = 0
        processed_urls = set()
        
        try:
            # Load the main jobs page
            if not self.browser.load_page(self.base_url):
                self.logger.error("Failed to load main jobs page")
                return
            
            while True:
                # Find all job links on the current page
                elements = self.browser.find_elements_with_wait(
                    By.CSS_SELECTOR,
                    config.SELECTORS["role_links"]
                )
                
                # Process found links
                for element in elements:
                    try:
                        url = element.get_attribute('href')
                        if url and url not in processed_urls:
                            processed_urls.add(url)
                            yield urljoin(self.base_url, url)
                    except WebDriverException as e:
                        self.logger.warning(f"Error extracting URL from element: {str(e)}")
                
                # Check if we've reached the limit
                page_count += 1
                if max_pages and page_count >= max_pages:
                    break
                
                # TODO: Implement pagination logic if needed
                # For now, we'll assume all jobs are on one page
                break
                
        except Exception as e:
            self.logger.error(f"Error extracting role links: {str(e)}")
    
    def _extract_founder_info(self, role_url: str) -> Optional[FounderInfo]:
        """
        Extract founder information from a role page.
        
        Args:
            role_url: URL of the role page
            
        Returns:
            FounderInfo if successful, None otherwise
        """
        try:
            if not self.browser.load_page(role_url):
                return FounderInfo(
                    role_page_url=role_url,
                    founder_name="N/A",
                    founder_title="N/A",
                    linkedin_url=None,
                    extraction_timestamp=datetime.now(UTC),
                    status="failed_to_load"
                )
            
            # Extract founder name
            name_elem = self.browser.find_element_with_wait(
                By.CSS_SELECTOR,
                config.SELECTORS["founder_name"]
            )
            founder_name = name_elem.text.strip() if name_elem else "N/A"
            
            # Extract founder title
            title_elem = self.browser.find_element_with_wait(
                By.CSS_SELECTOR,
                config.SELECTORS["founder_title"]
            )
            founder_title = title_elem.text.strip() if title_elem else "N/A"
            
            # Extract LinkedIn URL
            linkedin_elem = self.browser.find_element_with_wait(
                By.CSS_SELECTOR,
                config.SELECTORS["linkedin_url"]
            )
            linkedin_url = linkedin_elem.get_attribute('href') if linkedin_elem else None
            linkedin_url = FounderInfo.validate_linkedin_url(linkedin_url)
            
            return FounderInfo(
                role_page_url=role_url,
                founder_name=founder_name,
                founder_title=founder_title,
                linkedin_url=linkedin_url,
                extraction_timestamp=datetime.now(UTC)
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting founder info from {role_url}: {str(e)}")
            return FounderInfo(
                role_page_url=role_url,
                founder_name="N/A",
                founder_title="N/A",
                linkedin_url=None,
                extraction_timestamp=datetime.now(UTC),
                status="error"
            )
    
    def _process_role_page(self, role_url: str) -> FounderInfo:
        """
        Process a single role page with retry logic.
        
        Args:
            role_url: URL of the role page
            
        Returns:
            FounderInfo: Extracted founder information
        """
        for attempt in range(config.MAX_RETRIES):
            try:
                result = self._extract_founder_info(role_url)
                if result and result.status == "success":
                    return result
                
                if attempt < config.MAX_RETRIES - 1:
                    delay = self.browser._exponential_backoff(attempt)
                    self.logger.info(f"Retrying {role_url} in {delay:.2f} seconds...")
                    time.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Error processing {role_url} (attempt {attempt + 1}): {str(e)}")
                if attempt < config.MAX_RETRIES - 1:
                    continue
                
        return FounderInfo(
            role_page_url=role_url,
            founder_name="N/A",
            founder_title="N/A",
            linkedin_url=None,
            extraction_timestamp=datetime.now(UTC),
            status="max_retries_reached"
        )
    
    def scrape(self, max_pages: Optional[int] = None) -> List[FounderInfo]:
        """
        Scrape founder information from Y Combinator job pages.
        
        Args:
            max_pages: Optional maximum number of pages to process
            
        Returns:
            List[FounderInfo]: List of extracted founder information
        """
        results = []
        max_pages = max_pages or config.MAX_PAGES
        
        try:
            # Get role links
            role_links = list(self._extract_role_links(max_pages))
            total_links = len(role_links)
            self.logger.info(f"Found {total_links} role pages to process")
            
            # Process role pages concurrently
            with ThreadPoolExecutor(max_workers=config.CONCURRENT_WORKERS) as executor:
                future_to_url = {
                    executor.submit(self._process_role_page, url): url 
                    for url in role_links
                }
                
                # Collect results as they complete
                for i, future in enumerate(as_completed(future_to_url), 1):
                    url = future_to_url[future]
                    try:
                        founder_info = future.result()
                        results.append(founder_info)
                        self.logger.info(
                            f"Processed {i}/{total_links} pages - Status: {founder_info.status}"
                        )
                        
                        # Add delay between requests
                        if i < total_links:
                            time.sleep(config.REQUEST_DELAY)
                            
                    except Exception as e:
                        self.logger.error(f"Error processing future for {url}: {str(e)}")
                        results.append(FounderInfo(
                            role_page_url=url,
                            founder_name="N/A",
                            founder_title="N/A",
                            linkedin_url=None,
                            extraction_timestamp=datetime.now(UTC),
                            status="future_error"
                        ))
        
        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}")
        
        return results 