"""
Pytest configuration file.
"""

import pytest
import os
import sys
from pathlib import Path

# Add the application root directory to the Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Set test environment variables
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'true'

@pytest.fixture(autouse=True)
def app_context():
    """Create an app context for tests."""
    from app import app
    with app.app_context():
        yield 