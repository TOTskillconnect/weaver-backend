"""
Flask routes for the job scraping API.
"""

import logging
import traceback
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from app.scraper.scraper import YCombinatorScraper
import asyncio
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)
bp = Blueprint('routes', __name__)

def async_route(f):
    """Decorator to run route handlers asynchronously."""
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(f(*args, **kwargs))
    wrapper.__name__ = f.__name__
    return wrapper

@bp.route('/health')
@cross_origin(supports_credentials=True, origins=["http://localhost:3000", "https://weaver-frontend.onrender.com", "https://weaverai.vercel.app"])
def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    return jsonify({
        "status": "healthy",
        "version": "0.1.0"
    })

@bp.route('/api/scrape/start', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:3000", "https://weaver-frontend.onrender.com", "https://weaverai.vercel.app"])
@async_route
async def start_scrape():
    """Start a new scraping job."""
    try:
        logger.info("Received scrape request")
        data = request.get_json()
        
        if not data:
            logger.error("No JSON data received")
            return jsonify({"error": "No data provided"}), 400
        
        url = data.get('url')
        
        if not url:
            logger.error("No URL provided in request")
            return jsonify({"error": "URL is required"}), 400
            
        if not url.startswith('https://www.ycombinator.com'):
            logger.error(f"Invalid URL domain: {url}")
            return jsonify({"error": "Only Y Combinator URLs are supported"}), 400
        
        logger.info(f"Processing URL: {url}")
        
        # Initialize scraper
        scraper = YCombinatorScraper()
        
        try:
            # Scrape the URL
            results = await scraper.scrape(url)
            
            if not results:
                logger.warning("No results found")
                return jsonify({
                    "status": "success",
                    "message": "No job listings found",
                    "data": []
                })
            
            logger.info(f"Successfully scraped {len(results)} jobs")
            
            return jsonify({
                "status": "success",
                "message": f"Successfully scraped {len(results)} jobs",
                "data": results
            })
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                "status": "error",
                "message": f"Error scraping URL: {str(e)}",
                "data": []
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}",
            "data": []
        }), 500 