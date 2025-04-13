"""
Flask routes for the job scraping API.
"""

import logging
import traceback
import uuid
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from app.scraper.scraper import YCombinatorScraper
import asyncio
import sys
from typing import Dict

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

# In-memory job storage
jobs: Dict[str, dict] = {}

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
        
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        logger.info(f"Created job with ID: {job_id}")
        
        # Initialize job status
        jobs[job_id] = {
            'status': 'in_progress',
            'url': url,
            'results': None,
            'error': None
        }
        
        logger.info(f"Processing URL: {url}")
        
        # Initialize scraper
        scraper = YCombinatorScraper()
        
        try:
            # Scrape the URL
            results = await scraper.scrape(url)
            
            if not results:
                logger.warning("No results found")
                jobs[job_id].update({
                    'status': 'completed',
                    'results': [],
                    'message': "No job listings found"
                })
                return jsonify({
                    "status": "success",
                    "message": "No job listings found",
                    "data": [],
                    "job_id": job_id
                })
            
            logger.info(f"Successfully scraped {len(results)} jobs")
            jobs[job_id].update({
                'status': 'completed',
                'results': results,
                'message': f"Successfully scraped {len(results)} jobs"
            })
            
            return jsonify({
                "status": "success",
                "message": f"Successfully scraped {len(results)} jobs",
                "data": results,
                "job_id": job_id
            })
            
        except Exception as e:
            error_msg = f"Error scraping URL: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            jobs[job_id].update({
                'status': 'error',
                'error': error_msg
            })
            return jsonify({
                "status": "error",
                "message": error_msg,
                "data": [],
                "job_id": job_id
            }), 500
            
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": error_msg,
            "data": [],
        }), 500

@bp.route('/api/scrape/progress/<job_id>', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:3000", "https://weaver-frontend.onrender.com", "https://weaverai.vercel.app"])
def get_job_progress(job_id):
    """Get the progress of a scraping job."""
    logger.info(f"Progress check requested for job: {job_id}")
    
    if not job_id:
        logger.error("No job ID provided")
        return jsonify({"error": "Job ID is required"}), 400
        
    job = jobs.get(job_id)
    if not job:
        logger.error(f"Job not found: {job_id}")
        return jsonify({"error": "Job not found"}), 404
        
    response = {
        "status": job['status'],
        "message": job.get('message', ''),
        "data": job.get('results', [])
    }
    
    if job['status'] == 'error':
        response['error'] = job['error']
        return jsonify(response), 500
        
    return jsonify(response)

@bp.route('/api/scrape/linkedin', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:3000", "https://weaver-frontend.onrender.com", "https://weaverai.vercel.app"])
@async_route
async def scrape_linkedin():
    """Scrape LinkedIn URLs directly from Y Combinator job pages without job tracking."""
    try:
        logger.info("Received LinkedIn scrape request")
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
        
        logger.info(f"Processing URL for LinkedIn extraction: {url}")
        
        try:
            # Check if this is a direct company job URL
            is_direct_job = '/companies/' in url and '/jobs/' in url
            
            # Progress update for frontend compatibility
            progress_data = {
                "status": "starting",
                "message": "Initializing scraper...",
                "processed": 0,
                "total": 0
            }
            
            # Initialize scraper
            scraper = YCombinatorScraper()
            
            # Update progress
            progress_data["status"] = "scraping"
            progress_data["message"] = "Scraping LinkedIn URLs..."
            progress_data["total"] = 100
            
            # Perform the scraping
            if is_direct_job:
                # For direct job URLs, use the main scraper's extract_linkedin_urls method
                logger.info(f"Direct job URL detected, extracting LinkedIn URLs from: {url}")
                
                async with scraper.browser_context():
                    result = await scraper.extract_linkedin_urls(url)
                    # Only include the result if LinkedIn URLs were found
                    results = [result] if result.get('linkedin_urls') else []
            else:
                # For job listings pages, use scrape_linkedin_urls
                logger.info(f"Job listing page detected, extracting LinkedIn URLs from all jobs on: {url}")
                results = await scraper.scrape_linkedin_urls(url)
            
            # Log detailed information about results
            logger.info(f"Scraping complete. Found {len(results)} results with LinkedIn URLs")
            
            # Process each result to prioritize founder LinkedIn URLs
            for i, result in enumerate(results):
                founder_urls = result.get('founder_linkedin_urls', [])
                all_urls = result.get('linkedin_urls', [])
                
                # Log the breakdown of URLs
                if founder_urls:
                    logger.info(f"Result {i+1}: {result.get('title')} at {result.get('company')}")
                    logger.info(f"  Founder LinkedIn URLs ({len(founder_urls)}): {founder_urls}")
                    logger.info(f"  Founder Names: {result.get('founder_names', [])}")
                else:
                    logger.info(f"Result {i+1}: {result.get('title')} at {result.get('company')}")
                    logger.info(f"  No founder LinkedIn URLs found")
                    logger.info(f"  All LinkedIn URLs ({len(all_urls)}): {all_urls}")
                
                # Remove company_linkedin_urls from the result to simplify response
                if 'company_linkedin_urls' in result:
                    del result['company_linkedin_urls']
            
            # Update progress
            progress_data["status"] = "complete"
            progress_data["message"] = "Scraping complete"
            progress_data["processed"] = 100
            
            if not results:
                logger.warning("No LinkedIn URLs found")
                return jsonify({
                    "status": "success",
                    "message": "No LinkedIn URLs found",
                    "data": [],
                    "progress": progress_data
                })
            
            # Count founder URLs across all results
            total_founder_urls = sum(len(result.get('founder_linkedin_urls', [])) for result in results)
            
            if total_founder_urls > 0:
                success_message = f"Successfully found {total_founder_urls} founder LinkedIn URLs from {len(results)} jobs"
            else:
                success_message = f"Found LinkedIn URLs from {len(results)} jobs, but no founder URLs identified"
                
            logger.info(success_message)
            
            return jsonify({
                "status": "success",
                "message": success_message,
                "data": results,
                "progress": progress_data
            })
            
        except Exception as e:
            error_msg = f"Error scraping LinkedIn URLs: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                "status": "error",
                "message": error_msg,
                "data": [],
                "progress": {
                    "status": "error",
                    "message": error_msg,
                    "processed": 0,
                    "total": 100
                }
            }), 500
            
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": error_msg,
            "data": [],
            "progress": {
                "status": "error",
                "message": error_msg,
                "processed": 0,
                "total": 100
            }
        }), 500

@bp.route('/api/cors-test', methods=['GET', 'POST', 'OPTIONS'])
@cross_origin(supports_credentials=True, origins=["http://localhost:3000", "https://weaver-frontend.onrender.com", "https://weaverai.vercel.app"], max_age=600)
def cors_test():
    """Test endpoint for CORS functionality."""
    logger.info("CORS test endpoint called")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request origin: {request.headers.get('Origin', 'Unknown')}")
    
    response = jsonify({
        "status": "success",
        "message": "CORS is working",
        "request_method": request.method,
        "request_origin": request.headers.get('Origin', 'Unknown')
    })
    
    # Log response headers for debugging
    logger.info(f"Response headers: {dict(response.headers)}")
    
    return response 