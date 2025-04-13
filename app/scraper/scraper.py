"""
Core scraping functionality for Y Combinator job pages.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser, TimeoutError, BrowserContext
import traceback
import sys
from contextlib import asynccontextmanager

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
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    @asynccontextmanager
    async def browser_context(self):
        """Context manager for browser initialization and cleanup."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-extensions',
                    '--disable-software-rasterizer',
                    '--disable-setuid-sandbox',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--window-size=1920,1080'
                ]
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            self.logger.info("Browser context initialized successfully")
            yield
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.logger.info("Browser resources cleaned up")

    async def _get_page(self) -> Page:
        """Get a new page instance."""
        if not self.context:
            raise RuntimeError("Browser context not initialized")
        
        try:
            page = await self.context.new_page()
            
            # Enable request/response logging
            page.on("request", lambda request: self.logger.debug(f"Request: {request.method} {request.url}"))
            page.on("response", lambda response: self.logger.debug(f"Response: {response.status} {response.url}"))
            
            return page
        except Exception as e:
            self.logger.error(f"Error creating page: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def wait_for_network_idle(self, page: Page, timeout: int = 30000):
        """Wait for network to be idle."""
        try:
            await page.wait_for_load_state('networkidle', timeout=timeout)
        except TimeoutError:
            self.logger.warning("Network idle timeout reached")

    async def scrape_job_details(self, job_url: str) -> Dict[str, Any]:
        """Scrape detailed information from a job listing page."""
        page = await self._get_page()
        try:
            self.logger.info(f"Scraping job details from {job_url}")
            
            # Navigate to the page with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await page.goto(job_url, wait_until='domcontentloaded', timeout=30000)
                    await self.wait_for_network_idle(page)
                    break
                except TimeoutError:
                    if attempt == max_retries - 1:
                        raise
                    self.logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(2)

            # Wait for content to load
            await page.wait_for_selector('main', timeout=10000)
            await page.wait_for_timeout(2000)

            # Log the page title and URL
            title = await page.title()
            self.logger.info(f"Page loaded: {title} ({page.url})")

            # Extract job details using JavaScript
            details = await page.evaluate("""
                () => {
                    function safeExtract(selectors, attribute = 'textContent') {
                        for (const selector of selectors) {
                            try {
                                const element = document.querySelector(selector);
                                if (element) {
                                    const value = attribute === 'textContent' ? 
                                        element.textContent.trim() : 
                                        element.getAttribute(attribute);
                                    if (value) return value;
                                }
                            } catch (e) {
                                console.error(`Error extracting ${selector}:`, e);
                            }
                        }
                        return '';
                    }

                    return {
                        title: safeExtract([
                            'h1',
                            '.job-title',
                            '.JobTitle',
                            '.role-title',
                            'title'
                        ]),
                        company: safeExtract([
                            '.company-name',
                            '.CompanyName',
                            '.company-title',
                            'h2'
                        ]),
                        description: safeExtract([
                            '.job-description',
                            '.JobDescription',
                            'article',
                            'main'
                        ]),
                        location: safeExtract([
                            '.job-location',
                            '.JobLocation',
                            '[data-test="job-location"]'
                        ]),
                        salary: safeExtract([
                            '.compensation',
                            '.Compensation',
                            '[data-test="compensation"]'
                        ])
                    };
                }
            """)

            self.logger.info(f"Successfully extracted details for {job_url}")
            self.logger.debug(f"Extracted details: {details}")
            return details

        except Exception as e:
            self.logger.error(f"Error scraping job details from {job_url}: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'title': '',
                'company': '',
                'description': '',
                'location': '',
                'salary': '',
                'error': str(e)
            }
        finally:
            await page.close()

    async def scrape_job_listings(self, url: str) -> list:
        """Scrape job listings from the main page."""
        page = await self._get_page()
        try:
            self.logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await self.wait_for_network_idle(page)
            
            # Wait for job listings to load
            await page.wait_for_selector('main', timeout=10000)
            await page.wait_for_timeout(2000)

            # Extract job URLs
            job_urls = await page.evaluate("""
                () => {
                    const selectors = [
                        'a[href*="/companies/"][href*="/jobs/"]',
                        '.job-listing a',
                        '.JobListing a',
                        'article a[href*="/jobs/"]'
                    ];
                    
                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 0) {
                            return Array.from(elements)
                                .map(el => el.href)
                                .filter(url => url && url.includes('/jobs/'));
                        }
                    }
                    return [];
                }
            """)

            if not job_urls:
                self.logger.warning("No job URLs found")
                return []

            # Make sure all URLs are properly formatted strings
            cleaned_urls = []
            for job_url in job_urls:
                if isinstance(job_url, str) and job_url.startswith('http'):
                    cleaned_urls.append(job_url)
                else:
                    self.logger.warning(f"Skipping invalid job URL: {job_url}")
            
            self.logger.info(f"Found {len(cleaned_urls)} valid job URLs")
            return list(set(cleaned_urls))  # Remove duplicates

        except Exception as e:
            self.logger.error(f"Error scraping job listings: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return []
        finally:
            await page.close()

    async def scrape(self, url: str) -> list:
        """Main scraping function."""
        results = []
        try:
            async with self.browser_context():
                # Get job listings
                job_urls = await self.scrape_job_listings(url)
                if not job_urls:
                    return []

                # Scrape job details with rate limiting
                for job_url in job_urls:
                    try:
                        details = await self.scrape_job_details(job_url)
                        if details:
                            results.append(details)
                        # Rate limiting
                        await asyncio.sleep(1)
                    except Exception as e:
                        self.logger.error(f"Error processing job {job_url}: {str(e)}")
                        continue

        except Exception as e:
            self.logger.error(f"Error in scrape process: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            
        return results 

    async def extract_linkedin_urls(self, job_url: str) -> Dict[str, Any]:
        """Extract LinkedIn URLs from a job page."""
        page = await self._get_page()
        try:
            self.logger.info(f"Extracting LinkedIn URLs from {job_url}")
            
            # Make sure job_url is a string, not a coroutine
            if not isinstance(job_url, str):
                self.logger.error(f"Job URL is not a string: {type(job_url)}")
                return {
                    'job_url': str(job_url),
                    'title': '',
                    'company': '',
                    'linkedin_urls': [],
                    'founder_linkedin_urls': [],
                    'error': f"Invalid job URL type: {type(job_url)}"
                }
            
            # Navigate to the page with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await page.goto(job_url, wait_until='domcontentloaded', timeout=30000)
                    await self.wait_for_network_idle(page)
                    break
                except TimeoutError:
                    if attempt == max_retries - 1:
                        raise
                    self.logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(2)

            # Wait for content to load
            await page.wait_for_selector('main', timeout=10000)
            await page.wait_for_timeout(3000)  # Extended wait time to ensure founders section loads

            # Extract basic job info and all LinkedIn URLs
            data = await page.evaluate("""
                () => {
                    function safeExtract(selectors, attribute = 'textContent') {
                        for (const selector of selectors) {
                            try {
                                const element = document.querySelector(selector);
                                if (element) {
                                    const value = attribute === 'textContent' ? 
                                        element.textContent.trim() : 
                                        element.getAttribute(attribute);
                                    if (value) return value;
                                }
                            } catch (e) {
                                console.error(`Error extracting ${selector}:`, e);
                            }
                        }
                        return '';
                    }
                    
                    // Extract all founder names
                    const founderNames = [];
                    document.querySelectorAll('.Founders h3, [class*="founder"] h3, .Founder h3').forEach(el => {
                        if (el && el.textContent) {
                            founderNames.push(el.textContent.trim());
                        }
                    });
                    
                    // Function to check if a URL is likely a founder profile
                    function isFounderUrl(url, names) {
                        if (!url || !names || names.length === 0) return false;
                        
                        // Convert URL to lowercase for case-insensitive matching
                        const lowerUrl = url.toLowerCase();
                        
                        // Check if any founder name appears in the URL
                        return names.some(name => {
                            if (!name) return false;
                            
                            // Split name into parts
                            const nameParts = name.toLowerCase().split(' ');
                            
                            // Check if any part of the name (at least 3 chars) is in the URL
                            return nameParts.some(part => part.length > 2 && lowerUrl.includes(part));
                        });
                    }
                    
                    // Extract founder LinkedIn URLs (from Founders section, or near founder names)
                    const foundersSection = document.querySelector('.Founders, [class*="founder"], [class*="Founder"]');
                    const founderLinks = foundersSection ? 
                        Array.from(foundersSection.querySelectorAll('a[href*="linkedin.com"]')).map(a => a.href) : [];
                    
                    // Extract all LinkedIn URLs from the page
                    const allLinkedinUrls = Array.from(document.querySelectorAll('a[href*="linkedin.com"]'))
                        .map(a => a.href)
                        .filter(url => url && url.includes('linkedin.com'));
                    
                    // Categorize LinkedIn URLs
                    let founderLinkedinUrls = founderLinks;
                    
                    // If no founder LinkedIn URLs found directly, try to identify them by name
                    if (founderLinkedinUrls.length === 0 && founderNames.length > 0) {
                        founderLinkedinUrls = allLinkedinUrls.filter(url => isFounderUrl(url, founderNames));
                    }
                    
                    // Remaining URLs are likely company URLs
                    const companyLinkedinUrls = allLinkedinUrls.filter(url => !founderLinkedinUrls.includes(url));
                    
                    return {
                        title: safeExtract([
                            'h1',
                            '.job-title',
                            '.JobTitle',
                            '.role-title',
                            'title'
                        ]),
                        company: safeExtract([
                            '.company-name',
                            '.CompanyName',
                            '.company-title',
                            'h2'
                        ]),
                        linkedin_urls: allLinkedinUrls,
                        founder_linkedin_urls: founderLinkedinUrls,
                        company_linkedin_urls: companyLinkedinUrls,
                        founder_names: founderNames
                    };
                }
            """)
            
            result = {
                'job_url': job_url,
                'title': data.get('title', ''),
                'company': data.get('company', ''),
                'linkedin_urls': data.get('linkedin_urls', []),
                'founder_linkedin_urls': data.get('founder_linkedin_urls', []),
                'company_linkedin_urls': data.get('company_linkedin_urls', []),
                'founder_names': data.get('founder_names', [])
            }
            
            self.logger.info(f"Found {len(result['linkedin_urls'])} total LinkedIn URLs for {job_url}")
            self.logger.info(f"Found {len(result['founder_linkedin_urls'])} founder LinkedIn URLs for {job_url}")
            
            # If we found any founder URLs, log them
            if result['founder_linkedin_urls']:
                self.logger.info(f"Founder LinkedIn URLs: {result['founder_linkedin_urls']}")
                self.logger.info(f"Founder names: {result['founder_names']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting LinkedIn URLs from {job_url}: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'job_url': job_url,
                'title': '',
                'company': '',
                'linkedin_urls': [],
                'founder_linkedin_urls': [],
                'company_linkedin_urls': [],
                'founder_names': [],
                'error': str(e)
            }
        finally:
            await page.close()
            
    async def scrape_linkedin_urls(self, url: str) -> list:
        """Scrape LinkedIn URLs from all job pages."""
        results = []
        try:
            async with self.browser_context():
                # Get job listings
                self.logger.info(f"Fetching job listings from {url}")
                job_urls = await self.scrape_job_listings(url)
                self.logger.info(f"Found {len(job_urls)} job URLs to process")
                
                if not job_urls:
                    self.logger.warning("No job URLs found to scrape")
                    return []

                # Extract LinkedIn URLs from each job page
                for i, job_url in enumerate(job_urls):
                    try:
                        self.logger.info(f"Processing job {i+1}/{len(job_urls)}: {job_url}")
                        data = await self.extract_linkedin_urls(job_url)
                        
                        # Log whether we found LinkedIn URLs
                        linkedin_urls = data.get('linkedin_urls', [])
                        if linkedin_urls:
                            self.logger.info(f"Found {len(linkedin_urls)} LinkedIn URLs on {job_url}")
                            self.logger.debug(f"LinkedIn URLs: {linkedin_urls}")
                            results.append(data)
                        else:
                            self.logger.warning(f"No LinkedIn URLs found on {job_url}")
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                    except Exception as e:
                        self.logger.error(f"Error processing job {job_url}: {str(e)}")
                        self.logger.error(f"Traceback: {traceback.format_exc()}")
                        continue

                self.logger.info(f"Successfully extracted LinkedIn URLs from {len(results)} out of {len(job_urls)} job pages")
                return results

        except Exception as e:
            self.logger.error(f"Error in LinkedIn URL scrape process: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return results 