"""
API routes for the Flask application.
"""

from datetime import datetime, UTC
from flask import request, jsonify, make_response
import asyncio
from functools import wraps

from app import app, validate_url
from app.scraper import YCombinatorScraper
from app.utils import csv_handler

# Constants
MAX_REQUEST_SIZE = 1024 * 1024  # 1MB

def get_timestamp():
    """Get current UTC timestamp in ISO format."""
    return datetime.now(UTC).isoformat()

def error_response(message: str, status_code: int = 400, request_id: str = None) -> tuple:
    """Generate consistent error response."""
    response = {
        'error': message,
        'timestamp': get_timestamp(),
        'request_id': request_id
    }
    return jsonify(response), status_code

def async_route(f):
    """Decorator to handle async routes."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(f(*args, **kwargs))
    return wrapper

@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'version': '0.1.0',
        'timestamp': get_timestamp()
    })

@app.route('/submit', methods=['POST'])
@async_route
async def submit_url():
    """
    Submit a URL for scraping Y Combinator job pages.
    
    Expected payload:
    {
        "url": "https://www.ycombinator.com/jobs",
        "format": "csv"  # Optional, defaults to csv. Alternatives: json
    }
    """
    try:
        # Generate request ID
        request_id = datetime.now(UTC).strftime('%Y%m%d%H%M%S-') + str(id(request))[:8]
        
        # Validate request size
        if request.content_length and request.content_length > MAX_REQUEST_SIZE:
            return error_response(
                'Request too large',
                413,
                request_id
            )
        
        # Validate content type
        if not request.is_json:
            return error_response(
                'Content-Type must be application/json',
                400,
                request_id
            )
        
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
        app.logger.info(f"Starting scrape for URL: {source_url} (Request ID: {request_id})")
        try:
            results = await scraper.scrape(url=source_url)
            if not results:
                return error_response(
                    'No data found',
                    404,
                    request_id
                )
        except Exception as e:
            app.logger.error(f"Scraping error for {source_url}: {str(e)}")
            return error_response(
                f'Scraping failed: {str(e)}',
                500,
                request_id
            )
        
        # Prepare response metadata
        metadata = {
            'request_id': request_id,
            'source_url': source_url,
            'timestamp': get_timestamp(),
            'record_count': len(results)
        }
        
        # Return based on requested format
        if response_format == 'json':
            return jsonify({
                'metadata': metadata,
                'data': results
            })
        
        # Generate CSV
        try:
            csv_content = csv_handler.get_csv_as_string(results)
            if not csv_content:
                return error_response(
                    'Failed to generate CSV',
                    500,
                    request_id
                )
        except Exception as e:
            app.logger.error(f"CSV generation error: {str(e)}")
            return error_response(
                'Failed to generate CSV',
                500,
                request_id
            )
        
        # Prepare CSV response
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=yc_jobs_{request_id}.csv'
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Record-Count'] = str(len(results))
        
        return response
        
    except Exception as e:
        app.logger.error(f"Error processing request {request_id}: {str(e)}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return error_response(
            'Internal server error',
            500,
            request_id
        ) 