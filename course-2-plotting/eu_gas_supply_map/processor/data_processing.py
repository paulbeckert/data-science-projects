"""
Core data processing logic for gas trade visualization.
"""

import logging
from typing import Dict, List, Any, Tuple
import pandas as pd

from .coordinates import get_country_coordinates

logger = logging.getLogger(__name__)

# Constants
EU_AGGREGATE = "European Union - 27 countries (from 2020)"
CENTRAL_EUROPE = (10, 51)  # Central Europe coordinates (approximate center of Germany)

# List of EU-27 countries
EU_COUNTRIES = [
    'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 
    'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 
    'Hungary', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg',
    'Malta', 'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia',
    'Slovenia', 'Spain', 'Sweden'
]

def filter_and_process_data(
    import_data: pd.DataFrame,
    supply_data: pd.DataFrame,
    years: List[int]
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, float, float, float, float]:
    """
    Filter and pre-process raw data.
    
    Args:
        import_data: DataFrame containing import data
        supply_data: DataFrame containing supply data
        years: List of years to filter for
        
    Returns:
        Tuple of (filtered_import_data, filtered_supply_data, intra_eu_imports,
                total_imports, total_intra_eu, intra_eu_pipeline, intra_eu_lng)
    """
    # Filter data for specified years
    import_data = import_data[import_data['period'].isin(years)]
    supply_data = supply_data[supply_data['period'].isin(years)]
    
    # Filter for MIO_M3 units
    import_data = import_data[import_data['unit'] == 'MIO_M3']
    supply_data = supply_data[supply_data['unit'] == 'MIO_M3']
    
    # Store the "Total" import value for validation
    total_imports = import_data[
        (import_data['demanding_geography'] == EU_AGGREGATE) & 
        (import_data['supplying_geography'] == 'Total') &
        (import_data['product_type'] == 'Natural gas')
    ]['importVolume'].sum()
    
    logger.info(f"Total reported gas imports: {total_imports:.2f} million cubic meters")
    
    # Filter out "Total" entries
    import_data = import_data[import_data['supplying_geography'] != 'Total']
    
    # Separate intra-EU imports before further processing
    intra_eu_imports = import_data[
        (import_data['demanding_geography'] == EU_AGGREGATE) &
        (import_data['supplying_geography'].isin(EU_COUNTRIES))
    ].copy()
    
    # Calculate total intra-EU imports
    intra_eu_pipeline = intra_eu_imports[intra_eu_imports['product_type'] == 'Natural gas']['importVolume'].sum()
    intra_eu_lng = intra_eu_imports[intra_eu_imports['product_type'] == 'Liquefied natural gas']['importVolume'].sum()
    total_intra_eu = intra_eu_pipeline + intra_eu_lng
    
    logger.info(f"Intra-EU imports: {total_intra_eu:.2f} million cubic meters")
    logger.info(f"  Pipeline: {intra_eu_pipeline:.2f} million cubic meters")
    logger.info(f"  LNG: {intra_eu_lng:.2f} million cubic meters")
    
    # Remove intra-EU imports from the main dataset to avoid double counting
    import_data = import_data[~import_data['supplying_geography'].isin(EU_COUNTRIES)]
    
    return (import_data, supply_data, intra_eu_imports, 
            total_imports, total_intra_eu, intra_eu_pipeline, intra_eu_lng)


def calculate_volumes_and_shares(
    import_data: pd.DataFrame,
    supply_data: pd.DataFrame,
    intra_eu_imports: pd.DataFrame,
    years: List[int],
    total_intra_eu: float
) -> Tuple[pd.DataFrame, pd.DataFrame, float, float, float, float, float, float, float, float, Dict[int, float]]:
    """
    Calculate volumes and shares for pipeline, LNG, and domestic production.
    
    Args:
        import_data: Filtered import data
        supply_data: Filtered supply data
        intra_eu_imports: Intra-EU imports data
        years: List of years being processed
        total_intra_eu: Total intra-EU trade volume
        
    Returns:
        Tuple containing:
        - pipeline_by_country: DataFrame with pipeline imports by country
        - lng_by_country: DataFrame with LNG imports by country
        - domestic_production: Domestic production volume
        - domestic_share: Share of domestic production
        - total_pipeline: Total pipeline imports volume
        - total_lng: Total LNG imports volume
        - external_supply: Total external supply volume
        - total_supply_with_intra: Total supply volume including intra-EU
        - pipeline_share: Share of pipeline imports
        - lng_share: Share of LNG imports
        - inland_consumption: Dictionary mapping years to inland consumption values
    """
    # Filter for natural gas and LNG products
    all_natural_gas = import_data[
        (import_data['product_type'] == 'Natural gas') & 
        (import_data['demanding_geography'] == EU_AGGREGATE)
    ]
    
    lng_data = import_data[
        (import_data['product_type'] == 'Liquefied natural gas') & 
        (import_data['demanding_geography'] == EU_AGGREGATE)
    ]
    
    # Create pipeline data: Natural gas minus LNG (to avoid double counting)
    # First, group both datasets by supplying country
    all_gas_by_country = all_natural_gas.groupby('supplying_geography')['importVolume'].sum().reset_index()
    lng_by_country = lng_data.groupby('supplying_geography')['importVolume'].sum().reset_index()
    
    # Merge to subtract LNG from total natural gas
    pipeline_by_country = all_gas_by_country.merge(
        lng_by_country, 
        on='supplying_geography', 
        how='left', 
        suffixes=('_total', '_lng')
    )
    
    # Replace NaN with 0 for countries that don't supply LNG
    pipeline_by_country['importVolume_lng'] = pipeline_by_country['importVolume_lng'].fillna(0)
    
    # Calculate pipeline volume (total gas minus LNG)
    pipeline_by_country['importVolume'] = pipeline_by_country['importVolume_total'] - pipeline_by_country['importVolume_lng']
    
    # Keep only rows where pipeline volume is positive
    pipeline_by_country = pipeline_by_country[pipeline_by_country['importVolume'] > 0]
    
    # Keep only necessary columns
    pipeline_by_country = pipeline_by_country[['supplying_geography', 'importVolume']]
    
    # Use the LNG data directly (already filtered)
    lng_by_country = lng_by_country[['supplying_geography', 'importVolume']]
    
    # Calculate EU domestic production
    domestic_production = supply_data[
        (supply_data['volume_type'] == 'Indigenous production') &
        (supply_data['geography'] == EU_AGGREGATE) &
        (supply_data['product_type'] == 'Natural gas') &
        (supply_data['unit'] == 'MIO_M3') &
        (supply_data['period'].isin(years))
    ]['supplyVolume'].sum()
    
    logger.info(f"EU domestic production: {domestic_production:.2f} million cubic meters")
    
    # If we get zero, something is wrong - log details for debugging
    if domestic_production == 0:
        logger.warning("Found zero domestic production. This is unexpected.")
        logger.info(f"Checking for entries with volume_type='Indigenous production': {len(supply_data[supply_data['volume_type'] == 'Indigenous production'])}")
        logger.info(f"Checking for entries with geography='{EU_AGGREGATE}': {len(supply_data[supply_data['geography'] == EU_AGGREGATE])}")
    
    # Calculate total supply and external supply (imports + domestic)
    total_pipeline = pipeline_by_country['importVolume'].sum()
    total_lng = lng_by_country['importVolume'].sum()
    total_imports_calculated = total_pipeline + total_lng
    
    # External supply excludes intra-EU flows
    external_supply = total_imports_calculated + domestic_production
    
    # Total supply including intra-EU flows (for reference)
    total_supply_with_intra = external_supply + total_intra_eu
    
    # Calculate shares based on external supply (excluding intra-EU)
    pipeline_by_country['share'] = pipeline_by_country['importVolume'] / external_supply
    lng_by_country['share'] = lng_by_country['importVolume'] / external_supply
    domestic_share = domestic_production / external_supply
    
    # Calculate percentages for reporting
    pipeline_share = total_pipeline / external_supply
    lng_share = total_lng / external_supply
    
    # Extract inland consumption data for each year
    inland_consumption_by_year = {}
    for year in years:
        # Filter for inland consumption for EU aggregate in million cubic meters
        inland_data = supply_data[
            (supply_data['volume_type'] == 'Inland consumption - calculated') &
            (supply_data['geography'] == EU_AGGREGATE) &
            (supply_data['product_type'] == 'Natural gas') &
            (supply_data['unit'] == 'MIO_M3') &
            (supply_data['period'] == year)
        ]
        
        # Extract the value if available
        if not inland_data.empty:
            inland_consumption = inland_data['supplyVolume'].iloc[0]
            inland_consumption_by_year[year] = float(inland_consumption)
            logger.info(f"EU inland consumption for {year}: {inland_consumption:.2f} million cubic meters")
        else:
            logger.warning(f"No inland consumption data found for {year}")
            inland_consumption_by_year[year] = None
    
    # Log summary
    logger.info(f"External supply total (excluding intra-EU): {external_supply:.2f} million cubic meters")
    logger.info(f"Pipeline gas: {total_pipeline:.2f} million cubic meters ({pipeline_share*100:.2f}%)")
    logger.info(f"LNG: {total_lng:.2f} million cubic meters ({lng_share*100:.2f}%)")
    logger.info(f"Domestic: {domestic_production:.2f} million cubic meters ({domestic_share*100:.2f}%)")
    logger.info(f"Intra-EU: {total_intra_eu:.2f} million cubic meters (excluded from share calculation)")
    
    # Check that external supply shares sum to approximately 1.0
    total_share = pipeline_share + lng_share + domestic_share
    if abs(total_share - 1.0) > 0.01:
        logger.warning(f"Warning: Total external supply share ({total_share:.4f}) differs from 1.0 by more than 1%")
        
    return (pipeline_by_country, lng_by_country, domestic_production, domestic_share,
            total_pipeline, total_lng, external_supply, total_supply_with_intra,
            pipeline_share, lng_share, inland_consumption_by_year)


def process_intra_eu_flows(intra_eu_imports: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Process intra-EU flows for visualization.
    
    Args:
        intra_eu_imports: DataFrame with intra-EU import data
        
    Returns:
        List of intra-EU flow dictionaries
    """
    intra_eu_flows = []
    
    # Process intra-EU pipeline imports
    intra_eu_pipeline_data = intra_eu_imports[intra_eu_imports['product_type'] == 'Natural gas']
    for _, row in intra_eu_pipeline_data.groupby('supplying_geography')['importVolume'].sum().reset_index().iterrows():
        country = row['supplying_geography']
        volume = row['importVolume']
        
        # Skip zero values
        if volume <= 0:
            continue
        
        # Include volume but not share in output - using name only, removed geography
        intra_eu_flows.append({
            'name': country,
            'import_volume': float(volume),
            'type': 'pipeline'
        })

    # Process intra-EU LNG imports
    intra_eu_lng_data = intra_eu_imports[intra_eu_imports['product_type'] == 'Liquefied natural gas']
    for _, row in intra_eu_lng_data.groupby('supplying_geography')['importVolume'].sum().reset_index().iterrows():
        country = row['supplying_geography']
        volume = row['importVolume']
        lng_name = f"{country} LNG"
        
        # Skip zero values
        if volume <= 0:
            continue
        
        # Include volume but not share in output - using name only, removed geography
        intra_eu_flows.append({
            'name': lng_name,
            'import_volume': float(volume),
            'type': 'lng'
        })
        
    return intra_eu_flows


def create_flow_data(
    pipeline_by_country: pd.DataFrame,
    lng_by_country: pd.DataFrame,
    external_supply: float,
    country_coordinates: Dict[str, Dict[str, float]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """
    Create flow data structure for visualization.
    
    Args:
        pipeline_by_country: Processed pipeline data
        lng_by_country: Processed LNG data
        external_supply: External supply volume
        country_coordinates: Dictionary of country coordinates
        
    Returns:
        Tuple of (flows, other_flows, zero_flow_count)
    """
    # Set a minimum threshold for visualization
    min_share_threshold = 0.01  # 1% threshold
    
    # Collection for other flows (small, not specified, or "Other...")
    other_flows = []
    zero_flow_count = 0
    
    # Create flow data structure for visualization
    flows = []
    
    # Add pipeline flows
    for _, row in pipeline_by_country.iterrows():
        country = row['supplying_geography']
        share = row['share']
        volume = row['importVolume']
        
        # Skip zero values completely
        if volume <= 0 or share <= 0:
            zero_flow_count += 1
            continue
        
        # Check if this flow should go to "other_flows"
        is_other = (share < min_share_threshold or 
                    country == "Not specified" or 
                    country.startswith("Other"))
        
        if is_other:
            other_flows.append({
                'name': country,
                'import_volume': float(volume),
                'share': float(share),
                'type': 'pipeline'
            })
            continue
            
        # Get coordinates for country
        from_coords = get_country_coordinates(country, country_coordinates)
        
        flows.append({
            'from': from_coords,
            'to': CENTRAL_EUROPE,
            'name': country,
            'import_volume': float(volume),
            'share': float(share),
            'type': 'pipeline'
        })
    
    # Add LNG flows
    for _, row in lng_by_country.iterrows():
        country = row['supplying_geography']
        share = row['share']
        volume = row['importVolume']
        lng_name = f"{country} LNG"
        
        # Skip zero values completely
        if volume <= 0 or share <= 0:
            zero_flow_count += 1
            continue
            
        # Check if this flow should go to "other_flows"
        is_other = (share < min_share_threshold or
                    country == "Not specified" or 
                    country.startswith("Other"))
        
        if is_other:
            other_flows.append({
                'name': lng_name,
                'import_volume': float(volume),
                'share': float(share),
                'type': 'lng'
            })
            continue
            
        # Get coordinates for country
        from_coords = get_country_coordinates(country, country_coordinates)
        
        flows.append({
            'from': from_coords,
            'to': CENTRAL_EUROPE,
            'name': lng_name,
            'import_volume': float(volume),
            'share': float(share),
            'type': 'lng'
        })
    
    # Log summary of other flows and zero flows
    if zero_flow_count > 0:
        logger.info(f"Dropped {zero_flow_count} flows with zero volume/share")
    
    if other_flows:
        logger.info(f"Collected {len(other_flows)} other flows (small volumes, not specified, or other categories)")
        total_other_volume = sum(flow['import_volume'] for flow in other_flows)
        other_share = total_other_volume / external_supply
        logger.info(f"Other flows total: {total_other_volume:.2f} million cubic meters ({other_share*100:.4f}%)")
    
    return flows, other_flows, zero_flow_count