import logging
from pathlib import Path
import argparse
import json
import sys
import numpy as np
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom JSON encoder for NumPy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer)):
            return int(obj)
        elif isinstance(obj, (np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def main():
    """Main entry point for the visualization pipeline."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Process and visualize EU gas trade flows.'
    )
    parser.add_argument(
        '--years', 
        type=int,
        nargs='+',
        help='Specific years to process (default: process all available years)'
    )
    parser.add_argument(
        '--range', 
        type=int,
        nargs=2,
        metavar=('START_YEAR', 'END_YEAR'),
        help='Year range to process (e.g., --range 2010 2023)'
    )
    parser.add_argument(
        '--latest',
        type=int,
        help='Process only the latest N years'
    )
    parser.add_argument(
        '--import-file',
        type=str,
        default='data/estat_nrg_ti_gas_en.csv',
        help='Path to import data CSV file'
    )
    parser.add_argument(
        '--supply-file',
        type=str,
        default='data/estat_nrg_cb_gas_en.csv',
        help='Path to supply data CSV file'
    )
    parser.add_argument(
        '--coordinates-file',
        type=str,
        default='data/coordinates.json',
        help='Path to country coordinates JSON file'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Directory to save output files'
    )
    
    args = parser.parse_args()
    
    # Convert paths to absolute paths
    base_dir = Path.cwd()
    import_file = base_dir / args.import_file
    supply_file = base_dir / args.supply_file
    coordinates_file = base_dir / args.coordinates_file
    output_dir = base_dir / args.output_dir
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Determine which years to process
        years_to_process = None  # Default: all available years
        
        if args.years:
            years_to_process = args.years
            logger.info(f"Processing specific years: {years_to_process}")
        elif args.range:
            years_to_process = tuple(args.range)
            logger.info(f"Processing year range: {years_to_process[0]}-{years_to_process[1]}")
        elif args.latest:
            # The actual years will be determined after loading the data
            years_to_process = -args.latest  # Negative number indicates "latest N years"
            logger.info(f"Processing latest {args.latest} years")
        else:
            logger.info("Processing all available years")
            
        # Configuration dictionary for data processing
        config = {
            'import_file': import_file,
            'supply_file': supply_file,
            'coordinates_file': coordinates_file,
            'output_dir': output_dir,
            'years': years_to_process
        }
        
        # Process data and get the JSON output file
        json_file_path = process_gas_trade_data(config)
        logger.info(f"Data processing completed. JSON file saved to: {json_file_path}")
        
        # Print instruction for manual visualization
        logger.info("To visualize this data, run:")
        logger.info(f"python trade_flow_visualization_static.py {json_file_path} --year <YEAR>")
            
    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)
        sys.exit(1)

def process_gas_trade_data(config):
    """Process gas trade data and save to JSON file.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Path to the JSON output file
    """
    # Add the current directory to path
    current_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(current_dir))
    
    # Now import from relative paths
    from loader.loader import load_eurostat_import_data, load_eurostat_supply_data
    from processor.processor import process_gas_trade_data as process_data
    from processor.processor import load_or_create_coordinates_file
    
    # Load data
    logger.info(f"Loading import data from {config['import_file']}")
    import_data = load_eurostat_import_data(config['import_file'])
    
    logger.info(f"Loading supply data from {config['supply_file']}")
    supply_data = load_eurostat_supply_data(config['supply_file'])
    
    # If we are processing the latest N years
    years_to_process = config['years']
    if isinstance(years_to_process, int) and years_to_process < 0:
        # Extract all available years from the import data
        available_years = sorted(pd.unique(import_data['period'].dropna().astype(int)))
         # Convert the negative number to positive
        num_years = abs(years_to_process)
        # Take only the last N years from available years
         # If there aren't enough years available, take all available years
        years_to_process = available_years[-num_years:] if len(available_years) >= num_years else available_years
        logger.info(f"Processing latest {num_years} years: {years_to_process}")
    
    # Load coordinates
    coordinates_file = config['coordinates_file']
    if Path(coordinates_file).exists():
        logger.info(f"Loading coordinates from {coordinates_file}")
        coordinates = load_or_create_coordinates_file(str(coordinates_file))
    else:
        logger.info(f"Coordinates file not found, using default coordinates")
        # Create a new coordinates file in the specified location
        coordinates = load_or_create_coordinates_file(str(coordinates_file))
    
    # Process data
    logger.info("Processing gas trade data")
    
    # Process the data
    result = process_data(
        import_data,
        supply_data,
        coordinates,
        years_to_process
    )
    
    # Get the years that were processed and convert NumPy integers to standard Python integers
    processed_years = [int(year) for year in result['period']]
    result['period'] = processed_years
    
    # Create a compact representation of the years for the filename
    if len(processed_years) > 3:
        years_str = f"{min(processed_years)}-{max(processed_years)}"
    else:
        years_str = '_'.join(map(str, processed_years))
    
    logger.info(f"Processed data for years: {processed_years}")
    
    # Save the processed data to a JSON file
    output_file = Path(config['output_dir']) / f"eu_gas_flows_{years_str}.json"
    
    # For large datasets, we will use line-by-line writing to avoid memory issues
    with open(output_file, 'w') as f:
        # Write the initial part of the JSON manually
        f.write('{\n')
        
        # Write the period array using our custom encoder
        f.write(f'  "period": {json.dumps(processed_years, cls=NumpyEncoder)},\n')
        
        # Write central europe coordinates
        f.write(f'  "central_europe": {json.dumps(result["central_europe"], cls=NumpyEncoder)},\n')
        
        # Write metadata if available
        if 'metadata' in result:
            f.write(f'  "metadata": {json.dumps(result["metadata"], indent=2, cls=NumpyEncoder)},\n')
        
        # Write the yearly data section header
        f.write('  "yearly_data": {\n')
        
        # Write each year's data
        for i, year in enumerate(sorted(result['yearly_data'].keys())):
            # Convert NumPy int to Python int for the key
            year_int = int(year)
            year_data = result['yearly_data'][year]
            
            # Convert year to string to ensure it's quoted in the JSON
            year_str = f'"{year_int}"'
            
            # Write this year's data with proper indentation using our custom encoder
            year_json = json.dumps(year_data, indent=4, cls=NumpyEncoder)
            
            # Indent all lines of the year data
            indented_year_json = '\n'.join(['    ' + line for line in year_json.split('\n')])
            
            # Add a comma after every year except the last one
            comma = ',' if i < len(result['yearly_data']) - 1 else ''
            
            # Write to file
            f.write(f'    {year_str}: {indented_year_json}{comma}\n')
        
        # Close the yearly_data and root objects
        f.write('  }\n')
        f.write('}\n')
        
    logger.info(f"Saved processed data to {output_file}")
    
    return output_file

if __name__ == "__main__":
    main()