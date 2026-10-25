"""
Eurostat Data Loader

This script loads Eurostat natural gas import and production data 
and prepares it for further processing.
"""

from pathlib import Path
import pandas as pd
from typing import List, Optional


def load_eurostat_import_data(filepath: Path, years: Optional[List[int]] = None) -> pd.DataFrame:
    """
    Load and validate Eurostat trade data for multiple years.

    Args:
        filepath: Path to the Eurostat data file
        years: List of years to filter for (or None for all years)

    Returns:
        pd.DataFrame: Processed Eurostat data with renamed columns

    Raises:
        ValueError: If required columns are missing
    """
    column_map = {
        "OBS_VALUE": "importVolume",
        "Geopolitical entity (reporting)": "demanding_geography",
        "Geopolitical entity (partner)": "supplying_geography",
        "Standard international energy product classification (SIEC)": "product_type",
        "unit": "unit",
        "TIME_PERIOD": "period",
    }

    import_data = pd.read_csv(
        filepath, encoding="utf-8",
    )

    missing = set(column_map.keys()) - set(import_data.columns)
    if missing:
        error_msg = f"Missing required Eurostat columns: {missing}"
        raise ValueError(error_msg)

    # Rename columns
    import_data = import_data.rename(columns=column_map)
    
    # Convert period to integer
    import_data['period'] = import_data['period'].astype(str).astype(int)
    
    # Filter for specific years if provided
    if years:
        available_years = import_data['period'].unique()
        missing_years = set(years) - set(available_years)
        if missing_years:
            print(f"Warning: Some requested years are not available: {missing_years}")
            print(f"Available years: {sorted(available_years)}")
        
        import_data = import_data[import_data['period'].isin(years)]

    return import_data


def load_eurostat_supply_data(filepath: Path, years: Optional[List[int]] = None) -> pd.DataFrame:
    """
    Load and validate Eurostat supply data for multiple years.

    Args:
        filepath: Path to the Eurostat supply data file
        years: List of years to filter for (or None for all years)

    Returns:
        pd.DataFrame: Processed Eurostat supply data with renamed columns

    Raises:
        ValueError: If required columns are missing
    """
    column_map = {
        "OBS_VALUE": "supplyVolume",
        "Geopolitical entity (reporting)": "geography",
        "Energy balance": "volume_type", 
        "Standard international energy product classification (SIEC)": "product_type",
        "unit": "unit",
        "TIME_PERIOD": "period",
    }

    supply_data = pd.read_csv(
        filepath, encoding="utf-8", low_memory=False,
    )  # Added low_memory=False to avoid dtype warnings

    missing = set(column_map.keys()) - set(supply_data.columns)
    if missing:
        error_msg = f"Missing required Eurostat columns: {missing}"
        raise ValueError(error_msg)

    # Rename columns
    supply_data = supply_data.rename(columns=column_map)
    
    # Convert period to integer
    supply_data['period'] = supply_data['period'].astype(str).astype(int)
    
    # Filter for specific years if provided
    if years:
        available_years = supply_data['period'].unique()
        missing_years = set(years) - set(available_years)
        if missing_years:
            print(f"Warning: Some requested years are not available: {missing_years}")
            print(f"Available years: {sorted(available_years)}")
        
        supply_data = supply_data[supply_data['period'].isin(years)]

    return supply_data
