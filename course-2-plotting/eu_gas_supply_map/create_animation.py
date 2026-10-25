"""
EU Gas Trade Flow Animation Generator

This script creates an animated GIF showing the evolution of EU gas trade flows over multiple years.
It uses the static visualization function from trade_flow_visualization_static.py to generate
frames for each year, then combines them into an animated GIF.

Usage examples:
    # Basic usage (uses default settings):
    python create_animation.py data/eu_gas_flows_1990-2023.json
    
    # Customizing frame rate (0.5 = each frame shown for 2 seconds):
    python create_animation.py data/eu_gas_flows_1990-2023.json --fps 0.5
    
    # Skip years to create a faster overview (e.g., every 3rd year):
    python create_animation.py data/eu_gas_flows_1990-2023.json --skip 2
    
    # Specify custom output path:
    python create_animation.py data/eu_gas_flows_1990-2023.json --output my_animation.gif
    
The output GIF will be saved to the data directory by default.
"""

import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive before importing pyplot
import matplotlib.pyplot as plt
plt.ioff()  # Turn off interactive mode globally

import imageio.v2 as imageio
import argparse
import os
import sys
from pathlib import Path
import json
import tempfile
import shutil

project_root = Path(__file__).parent
from trade_flow_visualization_static import visualize_gas_flows

def create_gas_flow_gif(json_file_path, output_gif=None, fps=0.75, skip_years=0):
    """
    Create a GIF animation showing the evolution of EU gas flows over years.
    
    Args:
        json_file_path: Path to the multi-year JSON data file
        output_gif: Path to save the output GIF (default: based on input filename)
        fps: Frames per second for the GIF animation (default: 2.0)
        skip_years: Number of years to skip between frames (default: 0, use all years)
    """
    # Load the processed data
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON data: {e}")
        return
    
    # Check if this is a multi-year dataset
    if 'yearly_data' not in data:
        print(f"Error: The JSON file does not contain multi-year data")
        return
    
    # Extract available years and sort them
    years = sorted([int(year) for year in data['yearly_data'].keys()])
    
    if skip_years > 0:
        # Skip years as specified
        years = years[::skip_years+1]
    
    print(f"Creating animation for years: {years}")
    
    # Create a temporary directory for the image files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate images for each year without displaying them
        image_files = []
        
        for year in years:
            print(f"Generating visualization for {year}...")
            
            # Define the output file for this year
            year_file = os.path.join(temp_dir, f"eu_gas_{year}.png")
            image_files.append(year_file)
            
            # Generate the visualization for this year - ensuring no display
            visualize_gas_flows(
                json_file_path,
                year=year,
                output_image=year_file
            )
            plt.close('all')  # Close all figures to free memory and prevent display
        
        # Default output path if none specified
        if output_gif is None:
            output_dir = os.path.join(project_root, "data")
            os.makedirs(output_dir, exist_ok=True)
            json_name = Path(json_file_path).stem
            output_gif = os.path.join(output_dir, f"{json_name}_animation.gif")
        
        # Create list of frames
        frames = []
        for image_file in image_files:
            frames.append(imageio.imread(image_file))
        
        # Create the GIF animation
        print(f"Creating GIF animation with {fps} frames per second...")
        imageio.mimsave(output_gif, frames, fps=fps)
        
        print(f"GIF animation saved to {output_gif}")
    
    return output_gif

def main():
    parser = argparse.ArgumentParser(
        description='Create GIF animation of EU gas trade flows over years'
    )
    parser.add_argument(
        'json_file',
        type=str,
        help='Path to the multi-year JSON data file'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to save the output GIF (default: data/[jsonname]_animation.gif)'
    )
    parser.add_argument(
        '--fps',
        type=float,
        default=0.75,
        help='Frames per second for the animation (default: 0.75)'
    )
    parser.add_argument(
        '--skip',
        type=int,
        default=0,
        help='Number of years to skip between frames (default: 0, use all years)'
    )
    
    args = parser.parse_args()
    
    create_gas_flow_gif(
        args.json_file, 
        args.output, 
        args.fps, 
        args.skip
    )

if __name__ == "__main__":
    main()