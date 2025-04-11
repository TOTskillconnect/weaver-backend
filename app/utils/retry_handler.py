"""
Retry handler utility with exponential backoff.
"""

import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Any
from app.config import Config

T = TypeVar('T')

logger = logging.getLogger(__name__)

def with_retry(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that implements retry logic with exponential backoff.
    
    Args:
        func: The function to be decorated
        
    Returns:
        The decorated function that implements retry logic
        
    Raises:
        The last exception encountered after all retries are exhausted
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        last_exception = None
        
        for attempt in range(Config.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < Config.MAX_RETRIES - 1:  # Don't sleep on the last attempt
                    delay = Config.RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Attempt {attempt + 1} failed. Retrying in {delay} seconds. "
                        f"Error: {str(e)}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"All {Config.MAX_RETRIES} attempts failed. "
                        f"Final error: {str(e)}"
                    )
        
        if last_exception:
            raise last_exception
            
    return wrapper 