import requests

def main():
    url = 'https://www.ycombinator.com/jobs/role/sales-manager'
    print(f"Testing URL access: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        print("\nFirst 500 characters of response:")
        print(response.text[:500])
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    main() 