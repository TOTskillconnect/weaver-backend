"""
CORS proxy server for Weaver Backend.
"""

from flask import Flask, request, jsonify, Response, make_response
import requests
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cors_proxy.log')
    ]
)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Render backend URL
BACKEND_URL = "https://weaver-backend.onrender.com"

# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
    return response

# Handle OPTIONS requests explicitly
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    response = make_response()
    return response

# Index route for root path
@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'CORS Proxy running'
    })

# Health check endpoint
@app.route('/health')
def health_check():
    try:
        # Forward health check to backend
        backend_response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        return jsonify({
            'status': 'healthy',
            'proxy': True,
            'backend_status': backend_response.status_code
        })
    except Exception as e:
        logger.error(f"Error checking backend health: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'proxy': True,
            'error': str(e)
        }), 500

# Proxy for LinkedIn scraping endpoint
@app.route('/api/scrape/linkedin', methods=['POST'])
def scrape_linkedin():
    try:
        # Get request data
        data = request.json
        logger.info(f"Received scrape request for URL: {data.get('url', 'None')}")
        
        # Forward request to backend
        backend_url = f"{BACKEND_URL}/api/scrape/linkedin"
        logger.info(f"Forwarding to backend URL: {backend_url}")
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        backend_response = requests.post(
            backend_url,
            json=data,
            headers=headers,
            timeout=120  # 2-minute timeout
        )
        
        # Log backend response
        logger.info(f"Backend response status: {backend_response.status_code}")
        
        # Return backend response with CORS headers
        return Response(
            backend_response.content,
            status=backend_response.status_code,
            content_type=backend_response.headers.get('Content-Type', 'application/json')
        )
        
    except Exception as e:
        logger.error(f"Error proxying request: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Proxy error: {str(e)}',
            'data': [],
            'progress': {
                'status': 'error',
                'message': str(e),
                'processed': 0,
                'total': 0
            }
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False) 