import requests
import json

# Test the Render.com deployed service
url = "https://weaver-backend.onrender.com/api/scrape/start"
headers = {"Content-Type": "application/json", "Origin": "https://weaverai.vercel.app"}
data = {"url": "https://www.ycombinator.com/jobs/role/sales-manager"}

print(f"Making request to {url}...")
response = requests.post(url, headers=headers, json=data)
print(f"Status code: {response.status_code}")
print(f"Response headers: {response.headers}")
print(f"Response body: {json.dumps(response.json(), indent=2)}")

# Verify that job_id is in the response
if response.status_code == 200:
    response_data = response.json()
    print("Response keys:", list(response_data.keys()))
    if "job_id" in response_data:
        print(f"\nJob ID found: {response_data['job_id']}")
        
        # Test the progress endpoint
        progress_url = f"https://weaver-backend.onrender.com/api/scrape/progress/{response_data['job_id']}"
        print(f"\nChecking progress at {progress_url}...")
        progress_response = requests.get(progress_url, headers={"Origin": "https://weaverai.vercel.app"})
        print(f"Progress status code: {progress_response.status_code}")
        try:
            print(f"Progress response: {json.dumps(progress_response.json(), indent=2)}")
        except:
            print(f"Progress response text: {progress_response.text}")
    else:
        print("\nERROR: No job_id found in response!")
else:
    print("\nERROR: Request failed!") 