"""
CSV handling utilities.
"""

import csv
from io import StringIO
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union

from app.config import get_config

logger = logging.getLogger(__name__)
config = get_config()

def get_csv_as_string(data: List[Dict[str, str]]) -> Optional[str]:
    """
    Generate CSV content as a string from job data.
    
    Args:
        data: List of job dictionaries to convert to CSV
        
    Returns:
        str: CSV content if successful, None otherwise
    """
    if not data:
        return None
    
    try:
        output = StringIO()
        fieldnames = config.CSV_HEADERS
        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            delimiter=config.CSV_DELIMITER,
            quotechar=config.CSV_QUOTECHAR
        )
        
        # Write header
        writer.writeheader()
        
        # Write data rows
        for row in data:
            writer.writerow(row)
        
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error generating CSV string: {str(e)}")
        return None 