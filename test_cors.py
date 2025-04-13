import requests
import json

# Test the CORS debug endpoint
url = "https://weaver-backend.onrender.com/api/cors-test"
headers = {
    "Content-Type": "application/json", 
    "Origin": "https://weaverai.vercel.app",
    "Accept": "application/json",
    "X-Requested-With": "XMLHttpRequest"
}

print(f"Making request to {url}...")
print(f"With headers: {headers}")
response = requests.get(url, headers=headers)
print(f"Status code: {response.status_code}")
print(f"Response headers: {response.headers}")

try:
    response_data = response.json()
    print(f"Response data: {json.dumps(response_data, indent=2)}")
    
    # Check for CORS headers specifically
    cors_headers = [
        'Access-Control-Allow-Origin',
        'Access-Control-Allow-Headers',
        'Access-Control-Allow-Methods',
        'Access-Control-Allow-Credentials',
        'Access-Control-Expose-Headers',
        'Access-Control-Max-Age'
    ]
    
    print("\nCORS Headers Analysis:")
    for header in cors_headers:
        if header in response.headers:
            print(f"✅ {header}: {response.headers[header]}")
        else:
            print(f"❌ {header} not found")
    
except Exception as e:
    print(f"Error parsing response: {e}")
    print(f"Raw response: {response.text}") 