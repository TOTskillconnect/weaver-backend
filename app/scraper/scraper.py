"""
Core scraping functionality for Y Combinator job pages.
"""

import logging
import time
import asyncio
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urljoin
from playwright.async_api import async_playwright, Page, TimeoutError, Route, Request
import json
import re

from app.config import get_config

# Initialize configuration and logging
config = get_config()
logger = logging.getLogger(__name__)

class YCombinatorScraper:
    """Scrapes job listings from Y Combinator."""
    
    def __init__(self):
        """Initialize the job scraper."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.seen_urls = set()
    
    async def handle_route(self, route: Route, request: Request) -> None:
        """Handle route interception for job data."""
        if 'graphql' in request.url.lower() and request.method == "POST":
            logger.info(f"Intercepted GraphQL request: {request.url}")
            try:
                # Get the request data
                post_data = request.post_data
                if post_data:
                    logger.debug(f"Request data: {post_data}")
            except Exception as e:
                logger.error(f"Error reading request data: {e}")
        
        # Continue with the request
        await route.continue_()
    
    def is_job_listing_url(self, url: str) -> bool:
        """Check if a URL is a job listing rather than a category page."""
        # Category page patterns to exclude
        category_patterns = [
            r'/jobs/role/[^/]+$',  # Role category pages
            r'/jobs/location/[^/]+$',  # Location category pages
            r'/jobs/role/[^/]+/[^/]+$',  # Combined role/location category pages
        ]
        
        # Check if the URL matches any category pattern
        for pattern in category_patterns:
            if re.search(pattern, url):
                return False
        
        # Check if it's a company job listing
        return '/companies/' in url and '/jobs/' in url
    
    async def scrape_job_details(self, page: Page, job_url: str) -> Dict[str, Any]:
        """
        Scrape detailed information from a job listing page.
        
        Args:
            page: Playwright page instance
            job_url: URL of the job listing
            
        Returns:
            Dictionary containing detailed job information
        """
        try:
            self.logger.info(f"Scraping job details from {job_url}")
            await page.goto(job_url, wait_until='networkidle')
            await page.wait_for_timeout(2000)  # Wait for dynamic content
            
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
                    
                    // Extract job description
                    const description = extract('.job-description, [class*="description"], [class*="Description"]');
                    
                    // Extract requirements
                    const requirements = extract('[class*="requirements"], [class*="Requirements"]');
                    
                    // Extract benefits
                    const benefits = extract('[class*="benefits"], [class*="Benefits"]');
                    
                    // Extract company info
                    const companyInfo = {
                        size: extract('[class*="size"], [class*="Size"]'),
                        funding: extract('[class*="funding"], [class*="Funding"]'),
                        batch: extract('[class*="batch"], [class*="Batch"]'),
                        website: document.querySelector('a[class*="website"]')?.href || ''
                    };
                    
                    // Extract tech stack
                    const techStack = extractList('[class*="tech"], [class*="Tech"], [class*="stack"], [class*="Stack"]');
                    
                    // Extract location details
                    const locationEl = document.querySelector('[class*="location"], [class*="Location"]');
                    let location = locationEl ? locationEl.textContent.trim() : '';
                    let isRemote = false;
                    let workplaceType = '';
                    
                    if (location) {
                        isRemote = /remote|distributed/i.test(location);
                        if (location.includes('•')) {
                            const parts = location.split('•').map(p => p.trim());
                            location = parts[0];
                            workplaceType = parts[1] || '';
                        }
                    }
                    
                    return {
                        description,
                        requirements,
                        benefits,
                        company_info: companyInfo,
                        tech_stack: techStack,
                        location_details: {
                            full_location: location,
                            is_remote: isRemote,
                            workplace_type: workplaceType
                        }
                    };
                }
            """)
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error scraping job details: {str(e)}")
            return {}
    
    async def scrape_with_pagination(self, page: Page, base_url: str) -> List[Dict[str, Any]]:
        """
        Scrape job listings with pagination support.
        
        Args:
            page: Playwright page instance
            base_url: Base URL to start scraping from
            
        Returns:
            List of job listings
        """
        all_jobs = []
        page_num = 1
        has_more = True
        
        while has_more and page_num <= self.config.MAX_PAGES:
            self.logger.info(f"Scraping page {page_num}")
            
            # Wait for job listings to load
            await page.wait_for_timeout(2000)
            
            # Get jobs from current page
            jobs = await self._extract_jobs_from_page(page)
            
            # Filter new jobs
            new_jobs = [job for job in jobs if job['url'] not in self.seen_urls]
            
            if not new_jobs:
                self.logger.info("No new jobs found, stopping pagination")
                break
                
            # Add new jobs to results
            all_jobs.extend(new_jobs)
            for job in new_jobs:
                self.seen_urls.add(job['url'])
            
            # Try to load more jobs
            try:
                load_more = await page.query_selector('button[class*="load-more"], button:has-text("Load More")')
                if load_more:
                    await load_more.click()
                    await page.wait_for_timeout(2000)
                    page_num += 1
                else:
                    has_more = False
            except Exception as e:
                self.logger.error(f"Error loading more jobs: {str(e)}")
                has_more = False
        
        return all_jobs
    
    async def _extract_jobs_from_page(self, page: Page) -> List[Dict[str, Any]]:
        """Extract job listings from the current page."""
        jobs_data = await page.evaluate("""
            () => {
                const jobs = [];
                
                // Try multiple approaches to find job listings
                const selectors = [
                    'div[class*="job-"]',
                    'div[class*="JobListing"]',
                    'div[role="list"] > div',
                    '.jobs-list > div',
                    'a[href*="/company/"]'
                ];
                
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    
                    elements.forEach(element => {
                        try {
                            const link = element.tagName === 'A' ? element : element.querySelector('a');
                            if (!link) return;
                            
                            const href = link.getAttribute('href');
                            if (!href || !href.includes('/companies/')) return;
                            
                            const container = element.tagName === 'A' ? element.parentElement : element;
                            const title = link.textContent.trim();
                            
                            // Extract company name
                            let company = '';
                            const companyEl = container.querySelector('[class*="company"], [class*="Company"]');
                            if (companyEl) {
                                company = companyEl.textContent.trim();
                            } else {
                                const match = href.match(/\\/companies\\/([^/]+)/);
                                if (match) {
                                    company = match[1].split('-').map(word => 
                                        word.charAt(0).toUpperCase() + word.slice(1)
                                    ).join(' ');
                                }
                            }
                            
                            // Extract location with more detail
                            let location = '';
                            let isRemote = false;
                            let workplaceType = '';
                            
                            const locationEl = container.querySelector('[class*="location"], [class*="Location"]');
                            if (locationEl) {
                                location = locationEl.textContent.trim();
                                isRemote = /remote|distributed/i.test(location);
                                
                                if (location.includes('•')) {
                                    const parts = location.split('•').map(p => p.trim());
                                    location = parts[0];
                                    workplaceType = parts[1] || '';
                                }
                            }
                            
                            // Extract posting date if available
                            let postedDate = '';
                            const dateEl = container.querySelector('[class*="date"], [class*="Date"], time');
                            if (dateEl) {
                                postedDate = dateEl.textContent.trim();
                            }
                            
                            if (href && title) {
                                jobs.push({
                                    title: title || 'Unknown Title',
                                    company: company || 'Unknown Company',
                                    location: {
                                        text: location || 'Location not specified',
                                        is_remote: isRemote,
                                        workplace_type: workplaceType
                                    },
                                    posted_date: postedDate,
                                    url: href.startsWith('http') ? href : 'https://www.ycombinator.com' + href
                                });
                            }
                        } catch (e) {
                            console.error('Error processing element:', e);
                        }
                    });
                    
                    if (jobs.length > 0) break;
                }
                
                return jobs;
            }
        """)
        
        return jobs_data
    
    async def scrape(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape job listings from the given URL.
        
        Args:
            url: Target URL to scrape
            
        Returns:
            List of job listing dictionaries
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': self.config.BROWSER_WINDOW_WIDTH, 'height': self.config.BROWSER_WINDOW_HEIGHT},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                # If we're given a specific job URL, scrape just that job
                if '/companies/' in url and '/jobs/' in url:
                    details = await self.scrape_job_details(page, url)
                    return [details] if details else []
                
                # Otherwise, scrape job listings with pagination
                target_url = url if '/role/' in url or '/jobs/' in url else 'https://www.ycombinator.com/jobs/role/software-engineer'
                
                self.logger.info(f"Navigating to {target_url}")
                await page.goto(target_url, wait_until='networkidle')
                self.logger.info("Page loaded")
                
                # Get all jobs with pagination
                jobs = await self.scrape_with_pagination(page, target_url)
                
                # Scrape detailed information for each job
                detailed_jobs = []
                for job in jobs:
                    if len(detailed_jobs) >= self.config.MAX_PAGES * 10:  # Limit total jobs
                        break
                        
                    # Add delay between requests
                    await page.wait_for_timeout(self.config.REQUEST_DELAY * 1000)
                    
                    details = await self.scrape_job_details(page, job['url'])
                    if details:
                        detailed_job = {**job, **details}
                        detailed_jobs.append(detailed_job)
                
                self.logger.info(f"Successfully extracted {len(detailed_jobs)} detailed job listings")
                return detailed_jobs
            
            except TimeoutError as e:
                self.logger.error(f"Timeout error: {str(e)}")
                return []
            except Exception as e:
                self.logger.error(f"Error during scraping: {str(e)}")
                raise
            
            finally:
                await browser.close()

    async def _extract_job_data(self, element) -> Dict[str, Any]:
        """
        Extract data from a job listing element.
        
        Args:
            element: Playwright ElementHandle containing job listing
            
        Returns:
            Dictionary containing job data or None if extraction fails
        """
        async def safe_extract(selector: str, get_text: bool = True) -> str:
            try:
                el = await element.query_selector(selector)
                if el:
                    if get_text:
                        return (await el.text_content()).strip()
                    else:
                        return await el.get_attribute('href')
                return ""
            except Exception as e:
                self.logger.error(f"Error extracting {selector}: {str(e)}")
                return ""
        
        # Try multiple selectors for each field
        title_selectors = ['h3', 'h4', '.job-title', 'a[href^="/jobs/"]']
        company_selectors = ['.company-name', 'h3 + div', 'a[href^="/companies/"]']
        location_selectors = ['.location', 'div:has-text("Location")', '.job-location']
        
        title = ""
        for selector in title_selectors:
            title = await safe_extract(selector)
            if title:
                break
        
        company = ""
        for selector in company_selectors:
            company = await safe_extract(selector)
            if company:
                break
        
        location = ""
        for selector in location_selectors:
            location = await safe_extract(selector)
            if location:
                break
        
        # Get the job URL if available
        job_url = await safe_extract('a[href^="/jobs/"]', get_text=False)
        
        self.logger.info(f"Extracted job: {title} at {company}")
        
        return {
            'title': title,
            'company': company,
            'location': location,
            'url': job_url
        } 