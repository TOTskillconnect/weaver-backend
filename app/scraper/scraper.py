"""
Core scraping functionality for Y Combinator job pages.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser, TimeoutError
import traceback
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper.log')
    ]
)

from app.config import get_config

# Initialize logging
logger = logging.getLogger(__name__)
config = get_config()

class YCombinatorScraper:
    """Scrapes job listings from Y Combinator."""
    
    def __init__(self):
        """Initialize the job scraper."""
        self.config = config
        self.browser: Optional[Browser] = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
    
    async def _init_browser(self) -> Browser:
        """Initialize the browser."""
        try:
            self.logger.info("Initializing playwright and browser")
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-extensions'
                ]
            )
            self.logger.info("Browser initialized successfully")
            return browser
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def _get_page(self) -> Page:
        """Get a new page instance."""
        if not self.browser:
            self.browser = await self._init_browser()
        
        try:
            self.logger.info("Creating new page")
            page = await self.browser.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Enable request/response logging
            page.on("request", lambda request: self.logger.debug(f"Request: {request.method} {request.url}"))
            page.on("response", lambda response: self.logger.debug(f"Response: {response.status} {response.url}"))
            
            return page
        except Exception as e:
            self.logger.error(f"Error creating page: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def scrape_job_details(self, page: Page, job_url: str) -> Dict[str, Any]:
        """Scrape detailed information from a job listing page."""
        try:
            self.logger.info(f"Scraping job details from {job_url}")
            
            # Navigate to the page with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await page.goto(job_url, wait_until='networkidle', timeout=30000)
                    break
                except TimeoutError:
                    if attempt == max_retries - 1:
                        raise
                    self.logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(2)
            
            # Wait for content to load
            await page.wait_for_timeout(2000)
            
            # Log the page title and URL
            title = await page.title()
            self.logger.info(f"Page loaded: {title} ({page.url})")
            
            # Extract job details using JavaScript
            details = await page.evaluate("""
                () => {
                    function extract(selector) {
                        const el = document.querySelector(selector);
                        return el ? el.textContent.trim() : '';
                    }
                    
                    function extractList(selector) {
                        const elements = document.querySelectorAll(selector);
                        return Array.from(elements).map(el => el.textContent.trim());
                    }
                    
                    const details = {
                        title: extract('h1, .job-title'),
                        company: extract('.company-name, [class*="company-name"]'),
                        description: extract('.job-description, [class*="description"]'),
                        location: extract('.location, [class*="location"]'),
                        salary: extract('.compensation, [class*="compensation"]'),
                        requirements: extract('.requirements, [class*="requirements"]'),
                        tech_stack: extractList('.tech-stack li, [class*="tech-stack"] li'),
                        company_info: {
                            size: extract('.company-size, [class*="company-size"]'),
                            funding: extract('.funding, [class*="funding"]'),
                            website: document.querySelector('a[class*="website"]')?.href || ''
                        }
                    };
                    
                    // Log extracted data
                    console.log('Extracted job details:', JSON.stringify(details, null, 2));
                    
                    return details;
                }
            """)
            
            self.logger.info(f"Successfully extracted details for {job_url}")
            self.logger.debug(f"Extracted details: {details}")
            return details
            
        except Exception as e:
            self.logger.error(f"Error scraping job details from {job_url}: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def scrape_job_listings(self, page: Page) -> List[Dict[str, Any]]:
        """Scrape all job listings from the page."""
        try:
            self.logger.info("Waiting for job listings to load")
            
            # Wait for any of these selectors
            selectors = [
                '[class*="job-listing"]',
                '.jobs-list > div',
                'div[role="list"] > div'
            ]
            
            # Try each selector
            found_selector = None
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    found_selector = selector
                    self.logger.info(f"Found job listings with selector: {selector}")
                    break
                except TimeoutError:
                    continue
            
            if not found_selector:
                self.logger.error("No job listings found with any selector")
                return []
            
            # Extract job listings
            listings = await page.evaluate("""
                (selector) => {
                    const jobs = [];
                    document.querySelectorAll(selector).forEach(job => {
                        try {
                            const link = job.querySelector('a');
                            if (link && link.href.includes('/companies/')) {
                                const data = {
                                    title: job.querySelector('h2, h3, .job-title')?.textContent?.trim() || '',
                                    company: job.querySelector('[class*="company"]')?.textContent?.trim() || '',
                                    url: link.href,
                                    location: job.querySelector('[class*="location"]')?.textContent?.trim() || '',
                                    posted_date: job.querySelector('time, [class*="date"]')?.textContent?.trim() || ''
                                };
                                console.log('Found job:', JSON.stringify(data));
                                jobs.push(data);
                            }
                        } catch (e) {
                            console.error('Error processing job element:', e);
                        }
                    });
                    return jobs;
                }
            """, found_selector)
            
            self.logger.info(f"Found {len(listings)} job listings")
            self.logger.debug(f"Listings: {listings}")
            return listings
            
        except Exception as e:
            self.logger.error(f"Error scraping job listings: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def scrape(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape job listings from the given URL.
        
        Args:
            url: Target URL to scrape
            
        Returns:
            List of job listing dictionaries
        """
        try:
            self.logger.info(f"Starting scrape for URL: {url}")
            page = await self._get_page()
            
            # If it's a specific job URL, scrape just that job
            if '/companies/' in url and '/jobs/' in url:
                self.logger.info("Detected single job URL")
                details = await self.scrape_job_details(page, url)
                return [details] if details else []
            
            # Otherwise, scrape job listings
            self.logger.info("Scraping job listings page")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            self.logger.info("Page loaded, waiting for content")
            
            listings = await self.scrape_job_listings(page)
            if not listings:
                self.logger.warning("No job listings found")
                return []
            
            # Get detailed information for each job
            detailed_jobs = []
            for i, job in enumerate(listings[:10]):  # Limit to 10 jobs for testing
                try:
                    self.logger.info(f"Scraping details for job {i+1}/{len(listings[:10])}: {job['url']}")
                    details = await self.scrape_job_details(page, job['url'])
                    detailed_jobs.append({**job, **details})
                except Exception as e:
                    self.logger.error(f"Error scraping details for {job['url']}: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(detailed_jobs)} jobs with details")
            return detailed_jobs
            
        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
            
        finally:
            if self.browser:
                self.logger.info("Closing browser")
                await self.browser.close()
                self.browser = None 