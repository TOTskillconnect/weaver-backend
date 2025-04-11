"""
Run the Flask development server.
"""
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 