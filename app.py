"""
Main Flask application for the Cursor Y Combinator job scraper.
"""

from flask import Flask, request, jsonify, send_file, make_response
from pathlib import Path
import logging
import re
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse
import os

from app.config import Config, DevelopmentConfig, TestingConfig, ProductionConfig
from app.scraper import YCombinatorScraper
from app.utils import csv_handler

# Initialize Flask app
app = Flask(__name__)

# Setup logging
config = Config()
logger = logging.getLogger(__name__)

# Constants
MAX_REQUEST_SIZE = 1024 * 1024  # 1MB
ALLOWED_DOMAINS = ['www.ycombinator.com', 'ycombinator.com']
REQUEST_TIMEOUT = 300  # 5 minutes

def validate_url(url: str) -> bool:
    """Validate if URL is from Y Combinator jobs."""
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in ['http', 'https'] and
            parsed.netloc in ALLOWED_DOMAINS and
            '/jobs' in parsed.path
        )
    except Exception:
        return False

def error_response(message: str, status_code: int = 400, request_id: str = None) -> tuple:
    """Generate consistent error response."""
    response = {
        'error': message,
        'timestamp': datetime.utcnow().isoformat(),
        'request_id': request_id
    }
    return jsonify(response), status_code

def request_validation(f):
    """Decorator for common request validation."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Generate request ID
        request_id = datetime.utcnow().strftime('%Y%m%d%H%M%S-') + str(id(request))[:8]
        
        # Validate content length
        if request.content_length and request.content_length > MAX_REQUEST_SIZE:
            return error_response(
                'Request too large',
                413,
                request_id
            )
        
        # Validate content type for POST requests
        if request.method == 'POST':
            if not request.is_json:
                return error_response(
                    'Content-Type must be application/json',
                    400,
                    request_id
                )
        
        return f(request_id=request_id, *args, **kwargs)
    return decorated_function

@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'version': '0.1.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/submit', methods=['POST'])
@request_validation
def submit_url(request_id: str):
    """
    Submit a URL for scraping Y Combinator job pages.
    
    Expected payload:
    {
        "url": "https://www.ycombinator.com/jobs",
        "format": "csv"  # Optional, defaults to csv. Alternatives: json
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'url' not in data:
            return error_response(
                'URL is required',
                400,
                request_id
            )
        
        source_url = data['url']
        response_format = data.get('format', 'csv').lower()
        
        # Validate URL
        if not validate_url(source_url):
            return error_response(
                'Invalid Y Combinator jobs URL',
                400,
                request_id
            )
        
        # Validate format
        if response_format not in ['csv', 'json']:
            return error_response(
                'Invalid format. Supported formats: csv, json',
                400,
                request_id
            )
        
        # Initialize scraper
        scraper = YCombinatorScraper()
        
        # Start scraping
        logger.info(f"Starting scrape for URL: {source_url} (Request ID: {request_id})")
        results = scraper.scrape()
        
        if not results:
            return error_response(
                'No data found',
                404,
                request_id
            )
        
        # Prepare response metadata
        metadata = {
            'request_id': request_id,
            'source_url': source_url,
            'timestamp': datetime.utcnow().isoformat(),
            'record_count': len(results)
        }
        
        # Return based on requested format
        if response_format == 'json':
            return jsonify({
                'metadata': metadata,
                'data': [info.to_dict() for info in results]
            })
        
        # Generate CSV
        csv_content = csv_handler.get_csv_as_string(results)
        if not csv_content:
            return error_response(
                'Failed to generate CSV',
                500,
                request_id
            )
        
        # Prepare CSV response
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={config.csv.FILENAME_PREFIX}.csv'
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Record-Count'] = str(len(results))
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request {request_id}: {str(e)}")
        return error_response(
            'Internal server error',
            500,
            request_id
        )

def get_config():
    """Get the appropriate configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    config_map = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig
    }
    return config_map.get(env, DevelopmentConfig)

def main():
    """Run the Flask application."""
    # Get config
    config = get_config()
    
    # Setup logging
    config.setup_logging()
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.DEBUG
    )

if __name__ == '__main__':
    main() 