"""
Flask application initialization.
"""

from flask import Flask
from urllib.parse import urlparse

app = Flask(__name__)

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

# Import routes after app initialization to avoid circular imports
from app import routes 