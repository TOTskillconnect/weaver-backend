"""
Test script for the Y Combinator job scraper.
"""

import asyncio
import json
from app.scraper.scraper import YCombinatorScraper
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_scraper():
    """Test the scraper with a Y Combinator jobs URL."""
    try:
        # Initialize scraper
        scraper = YCombinatorScraper()
        
        # Test URL - Y Combinator software engineering jobs
        test_url = "https://www.ycombinator.com/jobs/role/software-engineer"
        
        logger.info(f"Starting test with URL: {test_url}")
        
        # Run scraper
        results = await scraper.scrape(test_url)
        
        # Log results
        logger.info(f"Found {len(results)} jobs")
        
        # Save results to file
        with open('scraper_results.json', 'w') as f:
            json.dump(results, f, indent=2)
            logger.info("Results saved to scraper_results.json")
            
        # Print first job details
        if results:
            logger.info("\nFirst job details:")
            first_job = results[0]
            for key, value in first_job.items():
                logger.info(f"{key}: {value}")
                
        return results
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_scraper()) 