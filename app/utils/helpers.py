"""
Helper utilities for the Cursor application.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Union
import tempfile

from app.config import config
from app.scraper.scraper import FounderInfo

logger = logging.getLogger(__name__)

class CSVHandler:
    """Handles CSV file generation and management."""
    
    def __init__(self):
        """Initialize the CSV handler with configuration."""
        self.logger = logging.getLogger(__name__)
        self._setup_output_directory()
    
    def _setup_output_directory(self) -> None:
        """Ensure the output directory exists."""
        try:
            output_dir = Path(config.csv.OUTPUT_DIR)
            output_dir.mkdir(parents=True, exist_ok=True)
            self.output_dir = output_dir
        except Exception as e:
            self.logger.error(f"Failed to create output directory: {str(e)}")
            # Fallback to system temp directory
            self.output_dir = Path(tempfile.gettempdir())
    
    def _generate_filename(self) -> str:
        """Generate a filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{config.csv.FILENAME_PREFIX}_{timestamp}.csv"
    
    def _get_output_path(self, filename: Optional[str] = None) -> Path:
        """Get the full path for the output file."""
        if not filename:
            filename = self._generate_filename()
        return self.output_dir / filename
    
    def _write_csv(
        self,
        data: List[FounderInfo],
        output_path: Path
    ) -> Optional[Path]:
        """
        Write data to CSV file.
        
        Args:
            data: List of FounderInfo objects to write
            output_path: Path to write the CSV file
            
        Returns:
            Path to the written file if successful, None otherwise
        """
        try:
            with output_path.open('w', newline='', encoding=config.csv.ENCODING) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=config.csv.COLUMNS)
                
                # Write header
                writer.writeheader()
                
                # Write data rows
                for info in data:
                    writer.writerow(info.to_dict())
                
            self.logger.info(f"Successfully wrote CSV file: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error writing CSV file: {str(e)}")
            return None
    
    def _validate_data(self, data: List[FounderInfo]) -> bool:
        """
        Validate the data before writing to CSV.
        
        Args:
            data: List of FounderInfo objects to validate
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        if not data:
            self.logger.warning("No data to write to CSV")
            return False
        
        # Validate each record
        for info in data:
            if not isinstance(info, FounderInfo):
                self.logger.error(
                    f"Invalid data type in records: {type(info)}. Expected FounderInfo"
                )
                return False
        
        return True
    
    def generate_csv(
        self,
        data: List[FounderInfo],
        output_filename: Optional[str] = None
    ) -> Optional[Path]:
        """
        Generate a CSV file from the provided founder information.
        
        Args:
            data: List of FounderInfo objects to write to CSV
            output_filename: Optional custom filename for the CSV
            
        Returns:
            Path to the generated CSV file if successful, None otherwise
        """
        if not self._validate_data(data):
            return None
        
        try:
            output_path = self._get_output_path(output_filename)
            
            # Check if file already exists
            if output_path.exists():
                self.logger.warning(f"File already exists: {output_path}")
                # Generate new filename with current timestamp
                output_path = self._get_output_path()
            
            return self._write_csv(data, output_path)
            
        except Exception as e:
            self.logger.error(f"Error generating CSV: {str(e)}")
            return None
    
    def get_csv_as_string(self, data: List[FounderInfo]) -> Optional[str]:
        """
        Generate CSV content as a string (useful for API responses).
        
        Args:
            data: List of FounderInfo objects to convert to CSV
            
        Returns:
            str: CSV content if successful, None otherwise
        """
        if not self._validate_data(data):
            return None
        
        try:
            from io import StringIO
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=config.csv.COLUMNS)
            
            # Write header
            writer.writeheader()
            
            # Write data rows
            for info in data:
                writer.writerow(info.to_dict())
            
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error generating CSV string: {str(e)}")
            return None
    
    def read_csv(self, file_path: Union[str, Path]) -> Optional[List[Dict]]:
        """
        Read data from a CSV file (useful for testing or data verification).
        
        Args:
            file_path: Path to the CSV file to read
            
        Returns:
            List of dictionaries containing the CSV data if successful, None otherwise
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.error(f"CSV file not found: {file_path}")
                return None
            
            data = []
            with file_path.open('r', encoding=config.csv.ENCODING) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append(row)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error reading CSV file: {str(e)}")
            return None

# Create a global CSV handler instance
csv_handler = CSVHandler() 