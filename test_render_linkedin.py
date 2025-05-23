import requests
import json

# Test the LinkedIn URL extraction endpoint on Render.com
url = "https://weaver-backend.onrender.com/api/scrape/linkedin"
headers = {
    "Content-Type": "application/json", 
    "Origin": "https://weaverai.vercel.app",
    "Accept": "application/json",
    "X-Requested-With": "XMLHttpRequest"
}
data = {"url": "https://www.ycombinator.com/companies/prelim/jobs/RzlfhQq-people-talent-lead"}

print(f"Making request to {url}...")
print(f"With headers: {headers}")
response = requests.post(url, headers=headers, json=data)
print(f"Status code: {response.status_code}")
print(f"Response headers: {response.headers}")

try:
    response_data = response.json()
    print(f"Response data keys: {list(response_data.keys())}")
    
    # Pretty print the response
    print(f"Response body: {json.dumps(response_data, indent=2)}")
    
    # Analyze the results
    if response.status_code == 200:
        data = response_data.get("data", [])
        if data:
            print(f"\nFound results from {len(data)} jobs:")
            for i, job in enumerate(data):
                print(f"\nJob {i+1}: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                print(f"Job URL: {job.get('job_url', '')}")
                
                # Check for founder LinkedIn URLs first
                founder_urls = job.get('founder_linkedin_urls', [])
                if founder_urls:
                    print(f"Found {len(founder_urls)} FOUNDER LinkedIn URLs:")
                    for j, linkedin_url in enumerate(founder_urls):
                        print(f"  {j+1}. {linkedin_url}")
                    
                    # If there are founder names, show them
                    founder_names = job.get('founder_names', [])
                    if founder_names:
                        print(f"Founder names: {', '.join(founder_names)}")
                
                # Check for regular LinkedIn URLs as fallback
                linkedin_urls = job.get('linkedin_urls', [])
                if not founder_urls and linkedin_urls:
                    print(f"Found {len(linkedin_urls)} LinkedIn URLs (not categorized):")
                    for j, linkedin_url in enumerate(linkedin_urls):
                        print(f"  {j+1}. {linkedin_url}")
                
                if not linkedin_urls and not founder_urls:
                    print("No LinkedIn URLs found in this job")
        else:
            print("\nNo LinkedIn URLs found in any jobs")
    else:
        print("\nERROR: Request failed!")
except Exception as e:
    print(f"Error parsing response: {e}")
    print(f"Raw response: {response.text}") 