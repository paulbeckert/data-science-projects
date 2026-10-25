"""
Country coordinates management for gas trade visualization.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Tuple
import unicodedata

logger = logging.getLogger(__name__)

def get_country_coordinates(country: str, coordinates_dict: Dict[str, Dict[str, float]]) -> tuple:
    """
    Get coordinates for a country with fallback mechanisms.
    
    Args:
        country: Country name
        coordinates_dict: Dictionary of country coordinates
        
    Returns:
        Tuple of (longitude, latitude)
    """
    # Try direct lookup first
    coords = coordinates_dict.get(country)
    if coords:
        return (coords['longitude'], coords['latitude'])
    
    # Try to clean up encoding issues
    try:
        normalized_country = unicodedata.normalize('NFKC', country)
        if normalized_country != country:
            coords = coordinates_dict.get(normalized_country)
            if coords:
                return (coords['longitude'], coords['latitude'])
    except:
        pass
    
    # Handle common country name variations
    variations = {
        "TÃ¼rkiye": "Turkey",
        "Türkiye": "Turkey",
        "USA": "United States",
        "UAE": "United Arab Emirates"
    }
    
    if country in variations:
        coords = coordinates_dict.get(variations[country])
        if coords:
            return (coords['longitude'], coords['latitude'])
    
    # Log missing coordinate with more detail for future updates
    logger.warning(f"No coordinates found for {country}, using default")
    
    # Fallback to 0,0
    return (0, 0)


def load_or_create_coordinates_file(file_path: str) -> Dict[str, Dict[str, float]]:
    """
    Load coordinates from file or create a new one if it doesn't exist.
    
    Args:
        file_path: Path to coordinates JSON file
        
    Returns:
        Dictionary of country coordinates
    """
    path = Path(file_path)
    if path.exists():
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error loading coordinates file: {e}")
    
    # Create a default file if none exists
    default_coords = generate_default_coordinates()
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(default_coords, f, indent=2, sort_keys=True)
        logger.info(f"Created new coordinates file at {path}")
    except Exception as e:
        logger.error(f"Error creating coordinates file: {e}")
    
    return default_coords


def load_country_coordinates(coordinates_file: Path) -> Dict[str, Dict[str, float]]:
    """
    Load country coordinates from a JSON file.
    
    Args:
        coordinates_file: Path to JSON file with country coordinates
        
    Returns:
        Dictionary mapping country names to their coordinates
    """
    try:
        with open(coordinates_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading coordinates file: {e}")
        return {}


def generate_default_coordinates() -> Dict[str, Dict[str, float]]:
    """
    Generate default coordinates for common gas exporting countries.
    
    Returns:
        Dictionary with default coordinates for major gas exporters
    """
    return {
        "Russia": {"latitude": 60, "longitude": 55},
        "Norway": {"latitude": 62, "longitude": 10},
        "Algeria": {"latitude": 28, "longitude": 1.6},
        "Qatar": {"latitude": 25.3, "longitude": 51.2},
        "United States": {"latitude": 40, "longitude": -100},
        "Nigeria": {"latitude": 9.1, "longitude": 8.7},
        "Azerbaijan": {"latitude": 40.1, "longitude": 47.6},
        "Libya": {"latitude": 26.3, "longitude": 17.2},
        "United Kingdom": {"latitude": 55, "longitude": -3},
        "Australia": {"latitude": -25, "longitude": 135},
        "Egypt": {"latitude": 26, "longitude": 30},
        "Trinidad and Tobago": {"latitude": 10.7, "longitude": -61.2},
        "Peru": {"latitude": -9.2, "longitude": -75},
        "Oman": {"latitude": 21, "longitude": 57},
        "Malaysia": {"latitude": 2.5, "longitude": 112.5},
        "Indonesia": {"latitude": -0.8, "longitude": 113.9},

        # Other potential countries
        "Turkey": {"latitude": 39, "longitude": 35},
        "Ukraine": {"latitude": 49, "longitude": 32},
        "Angola": {"latitude": -12.5, "longitude": 18.5},
        "Cameroon": {"latitude": 6, "longitude": 12},
        "Equatorial Guinea": {"latitude": 2, "longitude": 10},
        "Mozambique": {"latitude": -18.25, "longitude": 35},
        "Kazakhstan": {"latitude": 48, "longitude": 68},
        "Guinea-Bissau": {"latitude": 12, "longitude": -15},
        "Senegal": {"latitude": 14.5, "longitude": -14.5},
        "Morocco": {"latitude": 32, "longitude": -5},
        "Tunisia": {"latitude": 34, "longitude": 9},
        "Iraq": {"latitude": 33, "longitude": 44},
        "Iran": {"latitude": 32, "longitude": 53},
        "United Arab Emirates": {"latitude": 24, "longitude": 54},
        "Saudi Arabia": {"latitude": 24, "longitude": 45},
        "Yemen": {"latitude": 15, "longitude": 48},
        "Brunei": {"latitude": 4.5, "longitude": 114.5},
        "Singapore": {"latitude": 1.3, "longitude": 103.8},
        "Thailand": {"latitude": 15, "longitude": 100},
        "Vietnam": {"latitude": 16, "longitude": 108}
    }