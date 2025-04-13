"""
Simple scraper to extract LinkedIn URLs from Y Combinator job pages.
"""

import logging
import asyncio
import re
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, TimeoutError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('linkedin_scraper.log')
    ]
)

logger = logging.getLogger(__name__)

async def extract_linkedin_urls(url: str) -> List[Dict[str, Any]]:
    """Extract LinkedIn URLs from Y Combinator job pages."""
    results = []
    playwright = None
    browser = None
    
    try:
        logger.info(f"Starting LinkedIn URL extraction for {url}")
        
        # Initialize Playwright and browser
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        
        # Create a context
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        # Create a page and navigate to the job listings
        page = await context.new_page()
        logger.info(f"Navigating to {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        
        try:
            await page.wait_for_load_state('networkidle', timeout=15000)
        except TimeoutError:
            logger.warning("Network idle timeout reached, continuing anyway")
        
        # Wait for some content to load
        try:
            await page.wait_for_selector('body', timeout=10000)
            logger.info("Basic page content loaded")
        except TimeoutError:
            logger.error("Timed out waiting for body element")
            return []
        
        # Wait a moment for JavaScript to execute
        await asyncio.sleep(2)
        
        # Extract job URLs with a more robust approach
        logger.info("Extracting job URLs")
        job_urls = await page.evaluate("""
            () => {
                // Try different selectors that might contain job links
                const selectors = [
                    'a[href*="/companies/"][href*="/jobs/"]',
                    '.job-listing a',
                    '.JobListing a',
                    'article a[href*="/jobs/"]',
                    'a[href*="/jobs/"]',
                    // Add a more general selector as a fallback
                    'a'
                ];
                
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        // Filter for job URLs
                        const urls = Array.from(elements)
                            .map(el => el.href)
                            .filter(url => url && 
                                (url.includes('/jobs/') || 
                                 url.includes('/companies/') || 
                                 url.includes('ycombinator')));
                        
                        if (urls.length > 0) {
                            console.log(`Found ${urls.length} URLs with selector: ${selector}`);
                            return urls;
                        }
                    }
                }
                
                // Fallback: just return all links on the page
                return Array.from(document.querySelectorAll('a'))
                    .map(a => a.href)
                    .filter(url => url && url.length > 0);
            }
        """)
        
        if not job_urls or len(job_urls) == 0:
            logger.warning("No job URLs found")
            return []
            
        # Filter for likely job URLs
        filtered_urls = [url for url in job_urls if '/jobs/' in url and url.startswith('http')]
        if filtered_urls:
            job_urls = filtered_urls
        
        job_urls = list(set(job_urls))  # Remove duplicates
        logger.info(f"Found {len(job_urls)} job URLs")
        
        # Process each job URL (limit to 5 for testing)
        max_to_process = min(len(job_urls), 5)
        for i, job_url in enumerate(job_urls[:max_to_process]):
            try:
                logger.info(f"Processing job {i+1}/{max_to_process}: {job_url}")
                
                # Navigate to the job page
                job_page = await context.new_page()
                await job_page.goto(job_url, wait_until='domcontentloaded', timeout=30000)
                
                try:
                    await job_page.wait_for_load_state('networkidle', timeout=15000)
                except TimeoutError:
                    logger.warning(f"Network idle timeout reached for {job_url}, continuing anyway")
                
                # Wait a moment for JavaScript to execute
                await asyncio.sleep(2)
                
                # Extract job details and LinkedIn URLs
                job_data = await job_page.evaluate("""
                    () => {
                        // Get basic job info
                        const title = document.querySelector('h1')?.innerText.trim() || document.title || '';
                        let company = '';
                        
                        // Try different selectors for company name
                        const companySelectors = ['h2', '.company-name', '.CompanyName', '.company'];
                        for (const selector of companySelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.innerText.trim()) {
                                company = element.innerText.trim();
                                break;
                            }
                        }
                        
                        // Find all LinkedIn URLs
                        const linkedinUrls = Array.from(document.querySelectorAll('a[href*="linkedin.com"]'))
                            .map(a => a.href)
                            .filter(url => url && url.includes('linkedin.com'));
                            
                        return {
                            title,
                            company,
                            linkedin_urls: linkedinUrls
                        };
                    }
                """)
                
                # Add job URL to the data
                job_data['job_url'] = job_url
                
                # Log results
                linkedin_urls = job_data.get('linkedin_urls', [])
                if linkedin_urls and len(linkedin_urls) > 0:
                    logger.info(f"Found {len(linkedin_urls)} LinkedIn URLs on {job_url}")
                    logger.info(f"LinkedIn URLs: {linkedin_urls}")
                    results.append(job_data)
                else:
                    logger.warning(f"No LinkedIn URLs found on {job_url}")
                
                # Close the job page
                await job_page.close()
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing job {job_url}: {str(e)}")
                continue
        
        logger.info(f"Successfully extracted LinkedIn URLs from {len(results)} job pages")
        return results
        
    except Exception as e:
        logger.error(f"Error in LinkedIn URL extraction: {str(e)}")
        return results
        
    finally:
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()
        logger.info("Browser resources cleaned up")

async def main(url: str):
    """Main function to run the scraper."""
    results = await extract_linkedin_urls(url)
    return results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.ycombinator.com/jobs/role/software-engineer"
        
    asyncio.run(main(url)) 