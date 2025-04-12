"""
Flask application factory.
"""

import os
from flask import Flask
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
                 "allow_headers": ["Content-Type"],
                 "supports_credentials": True,
                 "send_wildcard": False
             }
         }
    )
    
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