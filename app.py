"""
Main Flask application for the Cursor Y Combinator job scraper.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import logging
from datetime import datetime

def create_app():
    """Create and configure the Flask application."""
    # Create the Flask application instance
    app = Flask(__name__)

    # Enable CORS
    CORS(app)

    # Setup logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Add file handler for logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    @app.route('/')
    def index():
        """Root endpoint."""
        return jsonify({
            'status': 'ok',
            'message': 'Y Combinator Job Scraper API'
        })

    @app.route('/health')
    def health_check():
        """Basic health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'version': '0.1.0',
            'timestamp': datetime.utcnow().isoformat()
        })

    return app

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 