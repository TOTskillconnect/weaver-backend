"""
Flask application factory.
"""

import os
from flask import Flask, request, current_app
from flask_cors import CORS
from urllib.parse import urlparse
from app.routes import bp

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, 
         resources={
             r"/*": {
                 "origins": [
                     "http://localhost:3000",
                     "https://weaver-frontend.onrender.com",
                     "https://weaverai.vercel.app"
                 ],
                 "methods": ["GET", "POST", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
                 "expose_headers": ["Content-Type", "X-Total-Count", "Access-Control-Allow-Origin"],
                 "supports_credentials": True,
                 "max_age": 600,
                 "send_wildcard": False
             }
         },
         supports_credentials=True
    )
    
    # Add global after_request handler to ensure CORS headers are set
    @app.after_request
    def add_cors_headers(response):
        # Get origin from request
        origin = request.headers.get('Origin')
        
        # If origin is from allowed domains, add specific CORS headers
        allowed_origins = [
            "http://localhost:3000",
            "https://weaver-frontend.onrender.com",
            "https://weaverai.vercel.app"
        ]
        
        if origin in allowed_origins:
            response.headers.add('Access-Control-Allow-Origin', origin)
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Max-Age', '600')
            
        return response
    
    # Special route for CORS preflight requests
    @app.route('/api/<path:path>', methods=['OPTIONS'])
    def handle_preflight(path):
        response = current_app.make_default_options_response()
        
        # Add CORS headers
        origin = request.headers.get('Origin')
        allowed_origins = [
            "http://localhost:3000",
            "https://weaver-frontend.onrender.com",
            "https://weaverai.vercel.app"
        ]
        
        if origin in allowed_origins:
            response.headers.add('Access-Control-Allow-Origin', origin)
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Max-Age', '600')
            
        return response
    
    def validate_url(url: str) -> bool:
        """Validate if URL is from Y Combinator jobs."""
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ['http', 'https'] and
                parsed.netloc in ['www.ycombinator.com', 'ycombinator.com'] and
                '/jobs' in parsed.path
            )
        except Exception:
            return False

    # Register blueprints
    app.register_blueprint(bp)
    
    return app 