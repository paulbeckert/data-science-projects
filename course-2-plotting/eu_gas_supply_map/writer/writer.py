"""
Gas Trade Data Writer

This script writes processed gas trade data to a JSON file
for visualization of EU gas trade flows.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler and set level to info
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Add ch to logger
logger.addHandler(ch)


def write_gas_trade_json(
    data: Dict[str, Any], 
    output_path: Path,
    filename: Optional[str] = None
) -> Path:
    """
    Write processed gas trade data to a JSON file.
    
    Args:
        data: Dictionary containing processed gas trade data
        output_path: Directory to save output file
        filename: Optional output filename (defaults to eu_gas_flows_YYYY.json)
        
    Returns:
        Path to the created JSON file
    """
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    
    # Determine filename if not provided
    if filename is None:
        # Use the first year in the period for the filename
        year = data.get('period', [2022])[0]
        filename = f"eu_gas_flows_{year}.json"
    
    # Create full file path
    file_path = output_path / filename
    
    # Write to JSON file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Gas trade data written to {file_path}")
    return file_path


def validate_flows_data(data: Dict[str, Any]) -> bool:
    """
    Validate the structure and contents of flow data.
    
    Args:
        data: Dictionary containing processed gas trade data
        
    Returns:
        Boolean indicating if data is valid
    """
    # Check required top-level keys
    required_keys = ['flows', 'domestic_production_share', 'central_europe', 'period']
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        logger.error(f"Missing required keys in data: {missing_keys}")
        return False
    
    # Check flow structure
    for i, flow in enumerate(data['flows']):
        # Check required flow keys
        flow_keys = ['from', 'to', 'name', 'share', 'type']
        missing_flow_keys = [key for key in flow_keys if key not in flow]
        if missing_flow_keys:
            logger.error(f"Flow {i} missing required keys: {missing_flow_keys}")
            return False
        
        # Validate flow type
        if flow['type'] not in ['pipeline', 'lng']:
            logger.error(f"Flow {i} has invalid type: {flow['type']}")
            return False
    
    # Check that shares sum to approximately 1.0
    flow_shares_sum = sum(flow['share'] for flow in data['flows'])
    total_share = flow_shares_sum + data['domestic_production_share']

    # Add other_flows share if it exists
    if 'other_flows_share' in data:
        total_share += data['other_flows_share']
        
    if abs(total_share - 1.0) > 0.01:
        logger.warning(
            f"Total share ({total_share:.4f}) differs from 1.0 by more than 1%"
        )

    return True


if __name__ == "__main__":
    # Example usage for testing
    from pathlib import Path
    import sys
    
    # Add project root to path to import processor
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    from scripts.visualization.processor import process_gas_trade_data, generate_default_coordinates, EU_AGGREGATE
    
    # Create dummy data
    import pandas as pd
    
    # Add project root to path to import processor
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    from scripts.visualization.processor import process_gas_trade_data, generate_default_coordinates, EU_AGGREGATE
    
    import_data = pd.DataFrame({
        "demanding_geography": [EU_AGGREGATE, EU_AGGREGATE],
        "supplying_geography": ["Russia", "Norway"],
        "importVolume": [100, 50],
        "product_type": ["Natural gas", "Liquefied natural gas"],
        "period": [2023, 2023]
    })
    
    supply_data = pd.DataFrame({
        "geography": [EU_AGGREGATE],
        "supplyVolume": [30],
        "volume_type": ["Indigenous production"],
        "product_type": ["Natural gas"],
        "period": [2023]
    })
    
    # Process data
    coordinates = generate_default_coordinates()
    processed_data = process_gas_trade_data(import_data, supply_data, coordinates)
    
    # Validate the data
    is_valid = validate_flows_data(processed_data)
    print(f"Data validation result: {is_valid}")
    
    # Write to a test location
    output_dir = Path.cwd() / "data-output"
    output_path = write_gas_trade_json(processed_data, output_dir)
    print(f"Test data written to {output_path}")