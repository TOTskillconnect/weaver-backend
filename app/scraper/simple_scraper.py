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

async def process_job_page(context, job_url: str) -> Dict[str, Any]:
    """Process a single job page and extract LinkedIn URLs."""
    job_page = await context.new_page()
    try:
        await job_page.goto(job_url, wait_until='domcontentloaded', timeout=30000)
        
        try:
            await job_page.wait_for_load_state('networkidle', timeout=15000)
        except TimeoutError:
            logger.warning(f"Network idle timeout reached for {job_url}, continuing anyway")
        
        # Wait longer for JavaScript to execute and ensure all elements are loaded
        await asyncio.sleep(5)
        
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
                
                // Find all LinkedIn URLs with a more comprehensive approach
                const linkedinUrls = [];
                
                // Method 1: Direct link detection
                document.querySelectorAll('a[href*="linkedin.com"]').forEach(a => {
                    if (a.href && a.href.includes('linkedin.com')) {
                        linkedinUrls.push(a.href);
                    }
                });
                
                // Method 2: Look for social links that might contain LinkedIn
                document.querySelectorAll('a.social-link, a.linkedin, a[aria-label*="LinkedIn"], a[title*="LinkedIn"]').forEach(a => {
                    if (a.href && a.href.includes('linkedin.com')) {
                        linkedinUrls.push(a.href);
                    }
                });
                
                // Method 3: Look for social icons
                document.querySelectorAll('a i.fa-linkedin, a i.linkedin, a svg[class*="linkedin"], a svg[class*="Linkedin"]').forEach(icon => {
                    const link = icon.closest('a');
                    if (link && link.href && link.href.includes('linkedin.com')) {
                        linkedinUrls.push(link.href);
                    }
                });
                
                // Method 4: Look for Founder section LinkedIn links (new)
                document.querySelectorAll('.Founders a, [class*="founder"] a').forEach(a => {
                    if (a.href && a.href.includes('linkedin.com')) {
                        linkedinUrls.push(a.href);
                    }
                });
                
                // Method 4b: Try to find founder cards and extract LinkedIn URLs
                const founderElements = document.querySelectorAll('.Founders > div, [id*="founder"], [class*="Founder"]');
                founderElements.forEach(founderEl => {
                    const links = founderEl.querySelectorAll('a');
                    links.forEach(link => {
                        if (link.href && link.href.includes('linkedin.com')) {
                            linkedinUrls.push(link.href);
                        }
                    });
                });
                
                // Method 5: Look for any SVG inside links that might be LinkedIn icons
                document.querySelectorAll('a svg').forEach(svg => {
                    const link = svg.closest('a');
                    if (link && link.href && link.href.includes('linkedin.com')) {
                        linkedinUrls.push(link.href);
                    }
                });

                // Method 6: Look specifically for LinkedIn icons by examining all links
                document.querySelectorAll('a').forEach(a => {
                    // Check if link contains an image that might be a LinkedIn icon
                    const hasLinkedInIcon = 
                        a.querySelector('img[src*="linkedin"], img[alt*="LinkedIn"], svg[class*="linkedin"]') !== null ||
                        (a.innerHTML.includes('in') && a.classList.length > 0 && a.textContent.trim().length <= 2);
                    
                    if (hasLinkedInIcon && a.href && a.href.includes('linkedin.com')) {
                        linkedinUrls.push(a.href);
                    } else if (a.href && a.href.includes('linkedin.com')) {
                        linkedinUrls.push(a.href);
                    }
                });
                
                // Method 7: Target the social icons section specifically
                const socialIconsSection = document.querySelectorAll('.social-icons, [class*="social"], [class*="Social"]');
                socialIconsSection.forEach(section => {
                    const links = section.querySelectorAll('a');
                    links.forEach(link => {
                        if (link.href && link.href.includes('linkedin.com')) {
                            linkedinUrls.push(link.href);
                        }
                    });
                });
                
                // Method 8: Look for any links near the company info section
                const companyInfo = document.querySelector('[class*="company-info"], .CompanyInfo, .company');
                if (companyInfo) {
                    const links = companyInfo.querySelectorAll('a');
                    links.forEach(link => {
                        if (link.href && link.href.includes('linkedin.com')) {
                            linkedinUrls.push(link.href);
                        }
                    });
                }
                
                // Debug info - output all link elements with their href
                console.log('All links on page:');
                const allLinks = Array.from(document.querySelectorAll('a')).map(a => ({
                    href: a.href,
                    text: a.textContent.trim(),
                    hasChildren: a.children.length > 0,
                    classes: a.className
                }));
                console.log(JSON.stringify(allLinks));
                
                return {
                    title,
                    company,
                    linkedin_urls: [...new Set(linkedinUrls)] // Remove duplicates
                };
            }
        """)
        
        # Add job URL to the data
        job_data['job_url'] = job_url
        
        return job_data
        
    except Exception as e:
        logger.error(f"Error processing job page {job_url}: {str(e)}")
        
        # Try to capture debug info for troubleshooting
        try:
            # Capture a screenshot
            screenshot_path = f"debug_screenshot_{job_url.split('/')[-1]}.png"
            await job_page.screenshot(path=screenshot_path)
            logger.info(f"Captured debug screenshot to {screenshot_path}")
            
            # Capture HTML structure
            html_content = await job_page.content()
            with open(f"debug_html_{job_url.split('/')[-1]}.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Captured HTML content to debug_html_{job_url.split('/')[-1]}.html")
        except Exception as debug_err:
            logger.error(f"Error capturing debug info: {str(debug_err)}")
        
        return {
            'job_url': job_url,
            'title': '',
            'company': '',
            'linkedin_urls': [],
            'error': str(e)
        }
    finally:
        await job_page.close()

async def extract_linkedin_urls(url: str) -> List[Dict[str, Any]]:
    """Extract LinkedIn URLs from Y Combinator job pages."""
    results = []
    playwright = None
    browser = None
    
    try:
        logger.info(f"Starting LinkedIn URL extraction for {url}")
        
        # Check if this is already a direct job page URL
        is_direct_job_page = '/companies/' in url and '/jobs/' in url
        if is_direct_job_page:
            logger.info(f"Direct job page URL detected: {url}")
        
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
        
        # If this is a direct job page URL, process it directly
        if is_direct_job_page:
            logger.info(f"Processing direct job page URL: {url}")
            job_data = await process_job_page(context, url)
            linkedin_urls = job_data.get('linkedin_urls', [])
            
            if linkedin_urls and len(linkedin_urls) > 0:
                logger.info(f"Found {len(linkedin_urls)} LinkedIn URLs on direct job page")
                logger.info(f"LinkedIn URLs: {linkedin_urls}")
                results.append(job_data)
            else:
                logger.warning(f"No LinkedIn URLs found on direct job page")
            
            return results
        
        # Otherwise, process as a job listing page
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
            # Try to wait for common content selectors
            selectors_to_try = ['main', 'body', 'article', '.job-listing', '.Founders']
            selector_found = False
            for selector in selectors_to_try:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    logger.info(f"Found content with selector: {selector}")
                    selector_found = True
                    break
                except TimeoutError:
                    continue
                
            if selector_found:
                logger.info("Basic page content loaded")
            else:
                logger.warning("No expected content selectors found, but continuing anyway")
        except Exception as e:
            logger.warning(f"Error waiting for selectors, but proceeding anyway: {str(e)}")
        
        # Wait a moment for JavaScript to execute
        await asyncio.sleep(2)
        
        # Extract job URLs with a more robust approach
        logger.info("Extracting job URLs")
        job_urls = await page.evaluate("""
            () => {
                // Debug helper to log found elements
                function logFoundElements(selector, count) {
                    console.log(`Found ${count} elements with selector: ${selector}`);
                }
                
                // Get all links that might be job listings
                let allJobUrls = [];
                
                // Try different selectors that might contain job links
                const selectors = [
                    'a[href*="/companies/"][href*="/jobs/"]',
                    '.job-listing a',
                    '.JobListing a',
                    'article a[href*="/jobs/"]',
                    'a[href*="/jobs/"]',
                    // Add more specific selectors based on the Y Combinator job page structure
                    '[role="job"] a',
                    '[role="listitem"] a',
                    'main a',
                    // Selector for job cards as seen in the screenshot
                    'article a', 
                    // Add a more general selector as a fallback
                    'a'
                ];
                
                // Instead of returning on first match, collect all potential job URLs from all selectors
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
                            logFoundElements(selector, urls.length);
                            allJobUrls = [...allJobUrls, ...urls];
                        }
                    }
                }
                
                // If we found any job URLs through selectors, return them
                if (allJobUrls.length > 0) {
                    // Remove duplicates
                    return [...new Set(allJobUrls)];
                }
                
                // Fallback: try to find any links that look like job URLs
                console.log("Using fallback method to find job URLs");
                return Array.from(document.querySelectorAll('a'))
                    .map(a => a.href)
                    .filter(url => url && url.includes('/jobs/'));
            }
        """)
        
        # Log the found URLs for debugging
        logger.info(f"Raw job URLs found: {len(job_urls)}")
        for i, url in enumerate(job_urls[:5]):
            logger.info(f"Sample URL {i+1}: {url}")
        
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
        
        # If URL is the main jobs page, process more URLs
        if '/jobs' in url and not ('/role/' in url or '/companies/' in url):
            logger.info("Main jobs page detected - processing more URLs")
            max_to_process = min(len(job_urls), 15)  # Process more URLs from the main page
            
        # If URL is a role-specific page, process more URLs
        if '/role/' in url:
            logger.info("Role-specific page detected - processing more URLs")
            max_to_process = min(len(job_urls), 15)  # Process more URLs from role pages
                
        for i, job_url in enumerate(job_urls[:max_to_process]):
            try:
                logger.info(f"Processing job {i+1}/{max_to_process}: {job_url}")
                
                # Process the job page using our helper function
                job_data = await process_job_page(context, job_url)
                
                # Log results
                linkedin_urls = job_data.get('linkedin_urls', [])
                if linkedin_urls and len(linkedin_urls) > 0:
                    logger.info(f"Found {len(linkedin_urls)} LinkedIn URLs on {job_url}")
                    logger.info(f"LinkedIn URLs: {linkedin_urls}")
                    results.append(job_data)
                else:
                    logger.warning(f"No LinkedIn URLs found on {job_url}")
                
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
