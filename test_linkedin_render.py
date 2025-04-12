import requests
import json

# Test the deployed LinkedIn URL extraction endpoint on Render.com
url = "https://weaver-backend.onrender.com/api/scrape/linkedin"
headers = {"Content-Type": "application/json", "Origin": "https://weaverai.vercel.app"}
data = {"url": "https://www.ycombinator.com/jobs/role/sales-manager"}

print(f"Making request to {url}...")
response = requests.post(url, headers=headers, json=data)
print(f"Status code: {response.status_code}")
print(f"Response headers: {response.headers}")
try:
    print(f"Response body: {json.dumps(response.json(), indent=2)}")
    
    # Analyze the results
    if response.status_code == 200:
        response_data = response.json()
        data = response_data.get("data", [])
        if data:
            print(f"\nFound LinkedIn URLs from {len(data)} jobs:")
            for i, job in enumerate(data):
                print(f"\nJob {i+1}: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                print(f"Job URL: {job.get('job_url', '')}")
                linkedin_urls = job.get('linkedin_urls', [])
                if linkedin_urls:
                    print(f"Found {len(linkedin_urls)} LinkedIn URLs:")
                    for j, linkedin_url in enumerate(linkedin_urls):
                        print(f"  {j+1}. {linkedin_url}")
                else:
                    print("No LinkedIn URLs found in this job")
        else:
            print("\nNo LinkedIn URLs found in any jobs")
    else:
        print("\nERROR: Request failed!")
except Exception as e:
    print(f"Failed to parse response: {e}")
    print(f"Raw response: {response.text}") 