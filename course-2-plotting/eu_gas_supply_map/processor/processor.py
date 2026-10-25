"""
Gas Trade Data Processor

This script processes Eurostat natural gas import and production data 
for visualization of EU gas trade flows.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import pandas as pd
import json

# Import from submodules
from .coordinates import load_or_create_coordinates_file, get_country_coordinates
from .data_processing import (
    filter_and_process_data, 
    calculate_volumes_and_shares, 
    process_intra_eu_flows,
    create_flow_data,
    EU_AGGREGATE,
    CENTRAL_EUROPE,
    EU_COUNTRIES
)

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler and set level to info
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Add ch to logger
logger.addHandler(ch)

def process_gas_trade_data(
    import_data: pd.DataFrame,
    supply_data: pd.DataFrame,
    country_coordinates: Dict[str, Dict[str, float]],
    years: Optional[Union[List[int], Tuple[int, int]]] = None,
) -> Dict[str, Any]:
    """
    Process Eurostat gas trade data for visualization.
    
    Args:
        import_data: DataFrame containing import data
        supply_data: DataFrame containing supply data
        country_coordinates: Dictionary mapping countries to coordinates
        years: List of specific years to process, or tuple (start_year, end_year) for a range,
               or None to process all available years
        
    Returns:
        Dict containing processed data ready for visualization
    """
    # Remove duplicate columns first to avoid filtering issues
    import_data = import_data.loc[:, ~import_data.columns.duplicated()]
    supply_data = supply_data.loc[:, ~supply_data.columns.duplicated()]
    
    # Get all available years from the data
    available_years = sorted(pd.unique(import_data['period'].dropna().astype(int)))
    if not available_years:
        raise ValueError("No data available")
    
    logger.info(f"Available years in dataset: {min(available_years)}-{max(available_years)}")
    
    # Determine which years to process
    if years is None:
        # Process all available years
        valid_years = available_years
        logger.info(f"Processing all available years: {min(valid_years)}-{max(valid_years)}")
    elif isinstance(years, tuple) and len(years) == 2:
        # Process a range of years
        start_year, end_year = years
        valid_years = [y for y in available_years if start_year <= y <= end_year]
        logger.info(f"Processing year range: {start_year}-{end_year}")
    else:
        # Process specific years
        valid_years = [y for y in years if y in available_years]
        
        if not valid_years:
            logger.warning(f"None of the requested years {years} are available.")
            valid_years = [max(available_years)]
            logger.info(f"Using most recent available year instead: {valid_years[0]}")
        elif len(valid_years) < len(years):
            missing_years = set(years) - set(valid_years)
            logger.warning(f"Some requested years are not available: {missing_years}")
    
    # Check if we're processing too many years (performance warning)
    if len(valid_years) > 10:
        logger.warning(f"Processing {len(valid_years)} years - this may take some time")
    
    logger.info(f"Processing {len(valid_years)} years: {valid_years}")
    
    # Process each year separately
    yearly_results = {}
    
    for year in valid_years:
        logger.info(f"Processing year {year}...")
        try:
            yearly_results[year] = process_single_year(
                import_data, 
                supply_data,
                country_coordinates,
                [year]
            )
            logger.info(f"Processed year {year}")
        except Exception as e:
            logger.error(f"Error processing year {year}: {str(e)}")
            logger.debug("Detailed error", exc_info=True)
    
    # If no years were successfully processed, raise an error
    if not yearly_results:
        raise ValueError("Failed to process any years")
    
    # Create a combined structure with data for all years
    combined_result = {
        'period': sorted(list(yearly_results.keys())),
        'central_europe': CENTRAL_EUROPE,
        'yearly_data': yearly_results
    }
    
    # Add metadata about the processing
    combined_result['metadata'] = {
        'total_years_processed': len(yearly_results),
        'years_range': f"{min(combined_result['period'])}-{max(combined_result['period'])}",
        'data_generated_at': pd.Timestamp.now().isoformat()
    }
    
    return combined_result

def process_single_year(
    import_data: pd.DataFrame,
    supply_data: pd.DataFrame,
    country_coordinates: Dict[str, Dict[str, float]],
    years: List[int]
) -> Dict[str, Any]:
    """
    Process a single year of data.
    
    Args:
        import_data: DataFrame containing import data
        supply_data: DataFrame containing supply data
        country_coordinates: Dictionary mapping countries to coordinates
        years: List containing a single year to filter for
        
    Returns:
        Dict containing processed data for a single year
    """
    # Filter and pre-process data
    import_data_filtered, supply_data_filtered, intra_eu_imports, total_imports, total_intra_eu, intra_eu_pipeline, intra_eu_lng = (
        filter_and_process_data(import_data, supply_data, years)
    )
    
    # Calculate volumes and shares
    (pipeline_by_country, lng_by_country, domestic_production, domestic_share,
     total_pipeline, total_lng, external_supply, total_supply_with_intra,
     pipeline_share, lng_share, inland_consumption_by_year) = calculate_volumes_and_shares(
        import_data_filtered, supply_data_filtered, intra_eu_imports, years, total_intra_eu
    )
    
    # Process intra-EU flows
    intra_eu_flows = process_intra_eu_flows(intra_eu_imports)
    
    # Create flow data
    flows, other_flows, zero_flow_count = create_flow_data(
        pipeline_by_country, lng_by_country, external_supply, country_coordinates
    )
    
    # Just log the number of intra-EU flows without details
    if intra_eu_flows:
        logger.info(f"Collected {len(intra_eu_flows)} intra-EU flow entries")
    
    # Get the current year being processed
    year = years[0]
    
    # Create the output structure with more precision for small values
    visualization_data = {
        'flows': flows,
        'domestic_production_share': float(domestic_share),
        'domestic_production_volume': float(domestic_production),
        'central_europe': CENTRAL_EUROPE,
        'intra_eu_flows': intra_eu_flows,
        'intra_eu_volume': float(total_intra_eu),
        'external_supply_volume': float(external_supply),
        'inland_consumption': inland_consumption_by_year.get(year)  # Add inland consumption
    }
    
    # Only include other_flows if there are any
    if other_flows:
        visualization_data['other_flows'] = other_flows
        total_other_volume = sum(flow['import_volume'] for flow in other_flows)
        visualization_data['other_flows_volume'] = float(total_other_volume)
        visualization_data['other_flows_share'] = float(total_other_volume / external_supply)
    
    # Add summary statistics
    visualization_data['summary'] = {
        'pipeline_share': float(pipeline_share),
        'lng_share': float(lng_share),
        'domestic_share': float(domestic_share),
        'external_supply_volume': float(external_supply),
        'total_supply_with_intra_volume': float(total_supply_with_intra),
        'total_pipeline_volume': float(total_pipeline),
        'total_lng_volume': float(total_lng),
        'domestic_production_volume': float(domestic_production),
        'intra_eu_volume': float(total_intra_eu),
        'inland_consumption': inland_consumption_by_year.get(year),  # Add inland consumption here too
        'year': years[0]
    }
    
    return visualization_data
