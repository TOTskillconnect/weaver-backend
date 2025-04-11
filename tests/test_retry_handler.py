"""
Tests for the retry handler utility.
"""

import pytest
from unittest.mock import Mock, patch
from app.utils.retry_handler import with_retry
from app.config import Config

def test_successful_execution():
    """Test that a successful function executes without retries."""
    mock_func = Mock(return_value="success")
    decorated_func = with_retry(mock_func)
    
    result = decorated_func()
    
    assert result == "success"
    assert mock_func.call_count == 1

def test_retry_on_failure():
    """Test that the function retries on failure."""
    mock_func = Mock(side_effect=[ValueError, ValueError, "success"])
    decorated_func = with_retry(mock_func)
    
    result = decorated_func()
    
    assert result == "success"
    assert mock_func.call_count == 3

def test_max_retries_exceeded():
    """Test that the function raises an exception after max retries."""
    error = ValueError("Test error")
    mock_func = Mock(side_effect=[error] * 4)  # Will fail all attempts
    decorated_func = with_retry(mock_func)
    
    with pytest.raises(ValueError) as exc_info:
        decorated_func()
    
    assert str(exc_info.value) == "Test error"
    assert mock_func.call_count == 3  # Original attempt + 2 retries

@patch('time.sleep')  # Mock sleep to speed up tests
def test_exponential_backoff(mock_sleep):
    """Test that exponential backoff is correctly implemented."""
    mock_func = Mock(side_effect=[ValueError, ValueError, "success"])
    decorated_func = with_retry(mock_func)
    
    result = decorated_func()
    
    assert result == "success"
    assert mock_sleep.call_count == 2  # Called twice for the two retries
    mock_sleep.assert_any_call(1.0)  # First retry
    mock_sleep.assert_any_call(2.0)  # Second retry with exponential backoff 