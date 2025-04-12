import asyncio
import logging
from app.scraper.scraper import YCombinatorScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    scraper = YCombinatorScraper()
    url = "https://www.ycombinator.com/jobs"
    
    print("Starting scraper test...")
    results = await scraper.scrape(url)
    
    print("\nResults:")
    for i, job in enumerate(results, 1):
        print(f"\nJob {i}:")
        for key, value in job.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    asyncio.run(main()) 