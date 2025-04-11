"""
Tests for the Flask application.
"""

import pytest
from unittest.mock import Mock, patch
from flask import json
from datetime import datetime

from app import app, validate_url

# Mock the entire scraper module to avoid importing selenium during tests
YCombinatorScraper = Mock()

@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_scraper():
    """Mock the YCombinator scraper."""
    with patch('app.routes.YCombinatorScraper') as mock:
        scraper_instance = Mock()
        mock.return_value = scraper_instance
        yield scraper_instance

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['version'] == '0.1.0'
    assert 'timestamp' in data

def test_validate_url():
    """Test URL validation function."""
    # Valid URLs
    assert validate_url('https://www.ycombinator.com/jobs')
    assert validate_url('https://ycombinator.com/jobs/123')
    
    # Invalid URLs
    assert not validate_url('https://example.com/jobs')
    assert not validate_url('https://www.ycombinator.com/about')
    assert not validate_url('invalid-url')
    assert not validate_url('')

class TestSubmitEndpoint:
    """Tests for the /submit endpoint."""
    
    def test_missing_url(self, client):
        """Test submission without URL."""
        response = client.post(
            '/submit',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'URL is required'

    def test_invalid_url(self, client):
        """Test submission with invalid URL."""
        response = client.post(
            '/submit',
            json={'url': 'https://example.com'},
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Invalid Y Combinator jobs URL'

    def test_invalid_content_type(self, client):
        """Test submission with wrong content type."""
        response = client.post(
            '/submit',
            data='not-json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Content-Type must be application/json' in data['error']

    def test_invalid_format(self, client):
        """Test submission with invalid format."""
        response = client.post(
            '/submit',
            json={
                'url': 'https://www.ycombinator.com/jobs',
                'format': 'invalid'
            },
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Invalid format' in data['error']

    def test_successful_json_response(self, client, mock_scraper):
        """Test successful submission with JSON response."""
        # Mock scraper results
        mock_results = [
            Mock(to_dict=lambda: {'title': 'Job 1', 'company': 'Company 1'}),
            Mock(to_dict=lambda: {'title': 'Job 2', 'company': 'Company 2'})
        ]
        mock_scraper.scrape.return_value = mock_results

        response = client.post(
            '/submit',
            json={
                'url': 'https://www.ycombinator.com/jobs',
                'format': 'json'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check metadata
        assert 'metadata' in data
        assert data['metadata']['source_url'] == 'https://www.ycombinator.com/jobs'
        assert data['metadata']['record_count'] == 2
        assert 'request_id' in data['metadata']
        assert 'timestamp' in data['metadata']
        
        # Check data
        assert 'data' in data
        assert len(data['data']) == 2
        assert data['data'][0]['title'] == 'Job 1'
        assert data['data'][1]['company'] == 'Company 2'

    def test_successful_csv_response(self, client, mock_scraper):
        """Test successful submission with CSV response."""
        # Mock CSV content
        mock_csv = "title,company\nJob 1,Company 1\nJob 2,Company 2"
        from app.utils import csv_handler
        with patch.object(csv_handler, 'get_csv_as_string', return_value=mock_csv):
            mock_scraper.scrape.return_value = [Mock(), Mock()]  # Two mock results
            
            response = client.post(
                '/submit',
                json={'url': 'https://www.ycombinator.com/jobs'},
                content_type='application/json'
            )
            
            assert response.status_code == 200
            assert response.headers['Content-Type'] == 'text/csv'
            assert 'X-Request-ID' in response.headers
            assert response.headers['X-Record-Count'] == '2'
            assert response.data.decode() == mock_csv

    def test_no_results(self, client, mock_scraper):
        """Test when scraper returns no results."""
        mock_scraper.scrape.return_value = []
        
        response = client.post(
            '/submit',
            json={'url': 'https://www.ycombinator.com/jobs'},
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'No data found'

    def test_scraper_error(self, client, mock_scraper):
        """Test when scraper raises an exception."""
        mock_scraper.scrape.side_effect = Exception('Scraper error')
        
        response = client.post(
            '/submit',
            json={'url': 'https://www.ycombinator.com/jobs'},
            content_type='application/json'
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['error'] == 'Internal server error' 