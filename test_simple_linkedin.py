"""
Simple test script to directly test LinkedIn URL extraction without going through the API.
"""
import asyncio
import sys
from app.scraper.simple_scraper import extract_linkedin_urls

async def main():
    """Run the scraper directly."""
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.ycombinator.com/jobs/role/software-engineer"
    
    print(f"Extracting LinkedIn URLs from {url}")
    results = await extract_linkedin_urls(url)
    
    if not results:
        print("No LinkedIn URLs found.")
        return
    
    print(f"\nFound LinkedIn URLs in {len(results)} job pages:")
    for i, job in enumerate(results):
        print(f"\nJob {i+1}: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
        print(f"Job URL: {job.get('job_url', '')}")
        
        linkedin_urls = job.get('linkedin_urls', [])
        if linkedin_urls:
            print(f"Found {len(linkedin_urls)} LinkedIn URLs:")
            for j, linkedin_url in enumerate(linkedin_urls):
                print(f"  {j+1}. {linkedin_url}")
        else:
            print("No LinkedIn URLs found in this job")

if __name__ == "__main__":
    asyncio.run(main()) 