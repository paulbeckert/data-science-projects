import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.io import shapereader
import geopandas as gpd
import numpy as np
import json
import argparse
from pathlib import Path
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from shapely.geometry import LineString, Point
import warnings
warnings.filterwarnings('ignore')

"""
EU Gas Trade Flow Visualization

This script creates static visualizations of EU gas trade flows from processed JSON data.

Usage:
    # Visualize a specific year
    python trade_flow_visualization_static.py data/eu_gas_flows_1990-2023.json --year 2022
    
    # Visualize the latest year
    python trade_flow_visualization_static.py data/eu_gas_flows_1990-2023.json
"""

def abbreviate_country_name(name):
    """
    Abbreviate common country names for cleaner display.
    
    Args:
        name: The country name to potentially abbreviate
        
    Returns:
        Abbreviated country name if applicable, otherwise the original name
    """
    abbreviations = {
        "United Kingdom": "UK",
        "United States": "USA", 
        "United States of America": "USA",
        "Rest of World Pipeline": "Rest of World",
        "Rest of World LNG": "Rest of World"
    }
    
    # Remove any "LNG" or "Pipeline" suffix first
    base_name = name.replace(" LNG", "").replace(" Pipeline", "")
    
    # Return the abbreviation if it exists, otherwise return the original name
    return abbreviations.get(base_name, base_name)

def visualize_gas_flows(json_file_path, year=None, output_image=None):
    """
    Generate a visualization of EU gas trade flows from processed JSON data.
    
    Args:
        json_file_path: Path to the processed JSON data file
        year: Specific year to visualize (if None, uses the latest year)
        output_image: Path to save the output image (optional)
    """
    # Load the processed data
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON data: {e}")
        return
    
    # Check if this is a multi-year dataset
    is_multi_year = 'yearly_data' in data
    
    if is_multi_year:
        # Get available years
        available_years = sorted([int(y) for y in data['yearly_data'].keys()])
        
        if not available_years:
            print("No years found in the data")
            return
            
        # If no year specified or specified year not available, use the latest
        if year is None:
            year = max(available_years)
            print(f"No year specified. Using the latest year: {year}")
        else:
            # Convert to int if it's a string
            year = int(year)
            if str(year) not in data['yearly_data']:
                print(f"Year {year} not found in data. Available years: {available_years}")
                year = max(available_years)
                print(f"Using the latest year instead: {year}")
        
        # Get the data for the selected year
        year_data = data['yearly_data'][str(year)]
        
        # Update central_europe if it exists in the year data
        central_europe = year_data.get('central_europe', data['central_europe'])
        
        # Extract key components from the year data
        flows = year_data['flows']
        domestic_production_share = year_data['domestic_production_share']
    else:
        # Legacy format - single year data
        year_data = data
        flows = data['flows']
        domestic_production_share = data['domestic_production_share']
        central_europe = tuple(data['central_europe'])
        
        # Try to extract year from the data
        if 'summary' in data and 'year' in data['summary']:
            year = data['summary']['year']
        elif 'period' in data:
            # Try to get it from period
            if isinstance(data['period'], list) and len(data['period']) > 0:
                year = data['period'][0]
            else:
                year = data['period']
    
    # Create a dictionary for other flows (if present)
    other_flows = {}
    if 'other_flows' in year_data:
        # Aggregate other flows by type
        other_pipeline = [f for f in year_data['other_flows'] if f['type'] == 'pipeline']
        other_lng = [f for f in year_data['other_flows'] if f['type'] == 'lng']
        
        other_pipeline_share = sum(f['share'] for f in other_pipeline)
        other_lng_share = sum(f['share'] for f in other_lng)
        
        # Place both "Other" flows in the Atlantic (near Greenland) with same coordinates
        other_location = (-35, 45)
        
        # Set a minimum threshold for visibility (0.005 = will display as 0.01 after rounding)
        min_flow_threshold = 0.005

        # Add aggregated other flows only if they exceed the threshold
        if other_pipeline_share >= min_flow_threshold:
            other_flows['pipeline'] = {
                'from': other_location,
                'to': central_europe,
                'name': 'Rest of World',
                'share': other_pipeline_share,
                'type': 'pipeline'
            }

        if other_lng_share >= min_flow_threshold:
            other_flows['lng'] = {
                'from': other_location,
                'to': central_europe,
                'name': 'Rest of World',
                'share': other_lng_share,
                'type': 'lng'
            }

    # Load Natural Earth shapefile
    world = gpd.read_file(shapereader.natural_earth(resolution='110m', category='cultural', name='admin_0_countries'))

    # Define EU countries (EU-27) using country names
    eu_names = [
        'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Denmark', 
        'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Ireland', 
        'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta', 'Netherlands', 
        'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden'
    ]

    # Brand colors
    # Primary colors
    DIGITAL_BLUE = '#3F59DC'
    ECO_GREEN = '#3ACB81'
    SUNNY_YELLOW = '#FFD70C'
    # Secondary colors
    DARK_BLUE = '#324692'
    # New color for domestic production (Blue 40%)
    LIGHT_BLUE = '#B2BDF1'

    # Use ECO_GREEN for both pipeline and LNG flows
    FLOW_COLOR = ECO_GREEN

    # Create a new column for colors (Default gray for non-EU countries)
    world['color'] = '#CCCCCC'

    # Color EU countries using Digital Blue
    world.loc[world['NAME'].isin(eu_names), 'color'] = DIGITAL_BLUE

    # Initialize Cartopy plot
    fig, ax = plt.subplots(figsize=(12, 6), subplot_kw={'projection': ccrs.PlateCarree()})

    # Plot countries with their respective colors
    for idx, row in world.iterrows():
        ax.add_geometries(
            [row.geometry], 
            ccrs.PlateCarree(),
            facecolor=row['color'],
            edgecolor='white',
            linewidth=0.3
        )

    # Extract EU coastline for flow termination, but exclude French Guiana
    eu_countries = world[world['NAME'].isin(eu_names)]

    # Create a function to identify and remove French Guiana
    def remove_french_guiana(eu_gdf):
        # Make a copy to avoid modifying the original
        modified_eu = eu_gdf.copy()
        
        # Try to find France
        france_idx = modified_eu[modified_eu['NAME'] == 'France'].index
        
        if len(france_idx) > 0:
            # Get France's geometry
            france_geom = modified_eu.loc[france_idx[0], 'geometry']
            
            # If France has multiple polygons (likely includes overseas territories)
            if france_geom.geom_type == 'MultiPolygon':
                # Extract all polygons
                polygons = list(france_geom.geoms)
                
                # Filter out French Guiana based on longitude/latitude
                # French Guiana is around -53° longitude
                mainland_polygons = [p for p in polygons if not (
                    p.centroid.x < -40 and p.centroid.y > 0 and p.centroid.y < 10
                )]
                
                # Create new geometry without French Guiana
                if mainland_polygons:
                    from shapely.geometry import MultiPolygon
                    modified_eu.loc[france_idx[0], 'geometry'] = MultiPolygon(mainland_polygons)
        
        return modified_eu

    # Apply the function to remove French Guiana
    modified_eu_countries = remove_french_guiana(eu_countries)

    # Dissolve to create a single multipolygon for all EU
    eu_union = modified_eu_countries.dissolve()
    eu_coastline = eu_union.geometry.iloc[0].boundary

    # Remove gridlines and unnecessary details
    ax.set_global()
    ax.spines['geo'].set_visible(False)

    # Set specific map extent instead of global view
    # Format: [lon_min, lon_max, lat_min, lat_max] in degrees (longitude/latitude)
    ax.set_extent([-110, 65, 0, 75], crs=ccrs.PlateCarree())

    # Add "Other" flows to the main flows for visualization
    combined_flows = flows.copy()
    if 'pipeline' in other_flows:
        combined_flows.append(other_flows['pipeline'])
    if 'lng' in other_flows:
        combined_flows.append(other_flows['lng'])

    # Validate that shares sum to 1.0
    total_import_share = sum(flow['share'] for flow in combined_flows)
    total_share = total_import_share + domestic_production_share

    print(f"Total Imports: {total_import_share:.2f}")
    print(f"Indigenous production: {domestic_production_share:.2f}")
    print(f"Total: {total_share:.2f}")

    if abs(total_share - 1.0) > 0.01:  # Allow small rounding errors
        print("WARNING: Shares do not sum to 1.0. Adjust values.")

    # Function to get line width based on share - increased width
    def get_line_width(share, max_width=10, min_width=1.5):
        # Use a more exponential scaling to emphasize larger flows
        # This will make larger flows visibly thicker while keeping small flows visible
        return min_width + (share / 0.25)**1.5 * (max_width - min_width)

    # Function to find index of the closest point in a list of coordinates to a given point
    def find_closest_point_index(x_coords, y_coords, point):
        distances = [(x_coords[i] - point[0])**2 + (y_coords[i] - point[1])**2 for i in range(len(x_coords))]
        return np.argmin(distances)

    # Function to create curved lines with automatic coastal termination
    def plot_curved_flow(ax, start_point, end_point, line_style, color, width, 
                        eu_coastline, flow_type, transform=ccrs.PlateCarree()):
        # Create a curved path using a simple quadratic curve
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        
        # Create perpendicular vector for control point
        # Flip control point direction based on flow type for visual distinction
        if flow_type == 'pipeline':
            # Pipeline flows curve one way (positive flip)
            flip = 1
        else:  # LNG
            # LNG flows curve the opposite way (negative flip)
            flip = -1
            
        # Adjust curve amount based on distance
        curve_factor = 0.3
        
        perp_x = -dy * curve_factor * flip
        perp_y = dx * curve_factor * flip
        
        # Define control point at midpoint plus perpendicular offset
        control_x = (start_point[0] + end_point[0]) / 2 + perp_x
        control_y = (start_point[1] + end_point[1]) / 2 + perp_y
        
        # Create a higher resolution path for the curve
        t = np.linspace(0, 1, 100)
        
        # Quadratic Bezier curve formula: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
        curve_x = (1-t)**2 * start_point[0] + 2*(1-t)*t * control_x + t**2 * end_point[0]
        curve_y = (1-t)**2 * start_point[1] + 2*(1-t)*t * control_y + t**2 * end_point[1]
        
        # For both LNG and pipeline flows, find intersection with EU boundary
        # Create LineString of the full path
        full_curve = LineString([(curve_x[i], curve_y[i]) for i in range(len(curve_x))])
        
        # Find intersection with EU coastline
        if eu_coastline.intersects(full_curve):
            # Get the intersection point(s)
            intersection = eu_coastline.intersection(full_curve)
            
            # Handle different types of intersections (point, multipoint, etc.)
            if intersection.geom_type == 'Point':
                # Single intersection point
                intersect_pt = (intersection.x, intersection.y)
                intersect_idx = find_closest_point_index(curve_x, curve_y, intersect_pt)
            elif intersection.geom_type == 'MultiPoint':
                # Multiple intersection points - use the one closest to the source
                # Find the closest to start_point
                distances = [Point(start_point).distance(Point(p.x, p.y)) for p in intersection.geoms]
                closest_idx = np.argmin(distances)
                intersect_pt = (intersection.geoms[closest_idx].x, intersection.geoms[closest_idx].y)
                intersect_idx = find_closest_point_index(curve_x, curve_y, intersect_pt)
            elif intersection.geom_type == 'GeometryCollection':
                # More complex intersection - use the closest point to the source
                points = []
                for geom in intersection.geoms:
                    if geom.geom_type == 'Point':
                        points.append((geom.x, geom.y))
                
                if points:
                    distances = [Point(start_point).distance(Point(p[0], p[1])) for p in points]
                    closest_idx = np.argmin(distances)
                    intersect_pt = points[closest_idx]
                    intersect_idx = find_closest_point_index(curve_x, curve_y, intersect_pt)
                else:
                    # If no points, use default (whole curve)
                    intersect_idx = len(curve_x) - 1
            else:
                # Default to showing the whole curve if intersection is complex
                intersect_idx = len(curve_x) - 1
                
            # Crop curve to intersection point
            truncated_x = curve_x[:intersect_idx+1]
            truncated_y = curve_y[:intersect_idx+1]
            
            # Plot the truncated curve without any arrows
            ax.plot(
                truncated_x, truncated_y,
                linestyle=line_style,
                color=color,
                alpha=0.8,
                linewidth=width,
                transform=transform,
                zorder=5
            )
            return  # Exit function after plotting the flow
            
        # For pipeline flows or if LNG didn't hit coastline, plot full curve without arrows
        ax.plot(
            curve_x, curve_y,
            linestyle=line_style,
            color=color,
            alpha=0.8,
            linewidth=width,
            transform=transform,
            zorder=5
        )

    # Group flows by origin country for coordinated text placement
    country_flows = {}
    for flow in combined_flows:
        # Extract base country name
        base_country = flow['name'].replace(" LNG", "") if flow['type'] == 'lng' else flow['name']
        
        if base_country not in country_flows:
            country_flows[base_country] = []
        
        country_flows[base_country].append(flow)

    # Plot curved flows for trade connections
    for country, flows_list in country_flows.items():
        # Skip if coordinates are invalid
        if not all(isinstance(coord, (int, float)) for flow in flows_list for coord in flow['from']):
            print(f"Warning: Skipping flow with invalid coordinates: {country}")
            continue
            
        # We will use the same starting point for all flows from this country
        start_point = flows_list[0]['from']

        # Track if we have pipeline and LNG from this country
        has_pipeline = any(flow['type'] == 'pipeline' for flow in flows_list)
        has_lng = any(flow['type'] == 'lng' for flow in flows_list)
        
        # Plot all flows for this country
        for flow in flows_list:
            # Skip flows with negligible shares
            if flow['share'] < min_flow_threshold:
                continue
                
            # Set line style based on gas type
            if flow['type'] == 'pipeline':
                line_style = '-'  # Solid line for pipeline
            else:  # LNG
                line_style = (0, (5, 3))  # Dashed line for LNG
            
            line_color = FLOW_COLOR  # Same color for both types
            
            # Plot flow line with width proportional to share and coastal termination
            line_width = get_line_width(flow['share'])
            plot_curved_flow(
                ax,
                start_point,  # Same start point for pipeline and LNG
                flow['to'],
                line_style,
                line_color,
                line_width,
                eu_coastline,
                flow['type']  # This will determine the curve direction
            )
        
        # Calculate the total share for this country (pipeline + LNG)
        total_country_share = sum(flow['share'] for flow in flows_list)
        
        # Add source country marker only once per country, sized by TOTAL share
        marker_size = 5 + (total_country_share * 50)
        
        ax.plot(
            start_point[0], start_point[1], 
            'o', color=SUNNY_YELLOW, markersize=marker_size,
            transform=ccrs.PlateCarree(),
            zorder=6
        )

        # Add labels for all flows from this country
        vertical_offset = 0
        for i, flow in enumerate(flows_list):
            # Skip labels for negligible shares
            if flow['share'] < min_flow_threshold:
                continue
                
            # Format the country name with flow type in parentheses
            base_country_name = flow['name'].replace(" LNG", "")  # Strip "LNG" suffix if present
            base_country_name = abbreviate_country_name(base_country_name)  # Apply abbreviations

            # Special handling for Rest of World - swap the text positions
            is_rest_of_world = base_country_name == "Rest of World"
            
            # Determine offset based on flow type and number of flows
            if len(flows_list) > 1:
                if flow['type'] == 'pipeline':
                    # First label below marker (or above for Rest of World)
                    text_y_offset = 3 if is_rest_of_world else -3
                else:  # LNG 
                    # Second label above marker (or below for Rest of World)
                    text_y_offset = -3 if is_rest_of_world else 3
            else:
                # Single flow - center the label (with slight offset)
                text_y_offset = -3
            
            # Check if this country has both PNG and LNG flows
            has_both_types = len(flows_list) > 1 and has_pipeline and has_lng
            
            # Only add the flow type if the country has both PNG and LNG
            if has_both_types:
                flow_type_abbr = "PNG" if flow['type'] == 'pipeline' else "LNG"
                formatted_name = f"{base_country_name} ({flow_type_abbr})"
            else:
                # Just show country name without flow type for countries with only one flow type
                formatted_name = base_country_name
            
            # Add source country name with share as decimal
            ax.text(
                start_point[0], start_point[1] + text_y_offset,
                f"{formatted_name}: {flow['share']:.2f}",
                fontsize=8,
                ha='center',
                va='center',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1),
                transform=ccrs.PlateCarree(),
                zorder=7
            )

    # Add a single marker for central Europe (destination point) using Digital Blue
    ax.plot(
        central_europe[0], central_europe[1],
        'o', color=DIGITAL_BLUE, markersize=10,
        transform=ccrs.PlateCarree(),
        zorder=9
    )

    # Add circle representing EU domestic production at the center of Europe
    # Calculate marker size based on share (for visual comparison with flow lines)
    domestic_marker_size = 5 + (domestic_production_share * 100)

    # Calculate marker size based on share (using the same formula as source countries)
    domestic_marker_size = 5 + (domestic_production_share * 50)

    # Plot EU domestic production as a larger circle at center of Europe
    ax.plot(
        central_europe[0], central_europe[1],
        'o', color=LIGHT_BLUE,
        markersize=domestic_marker_size,
        transform=ccrs.PlateCarree(),
        zorder=15
    )

    # Add a label for domestic production with white background - now closer to the circle
    ax.text(
        central_europe[0], central_europe[1] - 3,  # Position label BELOW the circle but closer
        f"Indigenous Production: {domestic_production_share:.2f}",
        fontsize=8,
        ha='center',
        va='center',
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1),  # Added back white background
        transform=ccrs.PlateCarree(),
        zorder=16
    )

    # Extract summary data from the JSON
    if 'summary' in year_data:
        summary = year_data['summary']
        pipeline_total = summary['pipeline_share']
        lng_total = summary['lng_share']
        domestic_share = summary['domestic_share']
        display_year = summary['year']
        # Extract inland consumption if available
        inland_consumption = summary.get('inland_consumption')
    else:
        # Fallback to calculated values if summary not available
        pipeline_total = sum(flow['share'] for flow in combined_flows if flow['type'] == 'pipeline')
        lng_total = sum(flow['share'] for flow in combined_flows if flow['type'] == 'lng')
        domestic_share = domestic_production_share
        display_year = year  # Use the selected year
        # Try to get inland consumption directly from year_data
        inland_consumption = year_data.get('inland_consumption')

    # Format the inland consumption value for the title if available
    consumption_text = ""
    if inland_consumption is not None and inland_consumption > 0:
        # Convert from million to billion cubic meters (divide by 1000)
        consumption_billion = inland_consumption / 1000
        # Format with thousand separators and no decimal place
        consumption_text = f" – Total Consumption: {consumption_billion:.0f} billion m³"

    # Add a title with year and inland consumption
    plt.suptitle(
        f'EU Natural Gas Supply Sources ({display_year}){consumption_text}',
        fontsize=14, y=0.94
    )

    # Add pie chart showing overall breakdown
    # Data for pie chart (aggregate by type)
    pie_data = [pipeline_total, lng_total, domestic_share]
    pie_colors = [FLOW_COLOR, FLOW_COLOR, LIGHT_BLUE]  # ECO_GREEN for pipeline and LNG, LIGHT_BLUE for domestic

    # Updated pie chart labels with revised wording
    pie_labels = [
        f'Pipeline Import share: {pipeline_total:.2f}', 
        f'LNG Import share: {lng_total:.2f}', 
        f'Indigenous Production share: {domestic_share:.2f}'
    ]

    # Create an inset axis for the pie chart in the bottom left corner, but positioned higher
    pie_ax = fig.add_axes([0.05, 0.15, 0.15, 0.15], frameon=True)

    # Format decimal values for the pie chart (2 decimal places with white background)
    def make_autopct(values):
        def my_autopct(pct):
            # Convert percentage to decimal
            decimal = pct / 100
            return f'{decimal:.2f}'
        return my_autopct

    # Use a longer dashed pattern for the LNG slice in the pie chart
    pie_hatches = ['', '////////', '']  # Use slashes for LNG segment (better than dots)
    
    pie_ax.pie(pie_data, labels=None, colors=pie_colors, autopct=make_autopct(pie_data), 
            startangle=90, 
            textprops={'color': 'black', 'fontweight': 'bold', 
                    'bbox': {'facecolor': 'white', 'alpha': 0.7, 'edgecolor': 'none', 'pad': 1}},
            wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
            hatch=pie_hatches) 
    pie_ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    pie_ax.set_title('Supply Breakdown', fontsize=9)

    class HatchedPatch(Patch):
        def __init__(self, hatch, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.set_hatch(hatch)
            self.set_edgecolor('white')  # To make the space between hatch lines white
    
    # Add a custom legend for the pie chart with hatching for LNG
    pie_patches = [
        Patch(facecolor=FLOW_COLOR, label=pie_labels[0]),  # Pipeline
        HatchedPatch('////////', facecolor=FLOW_COLOR, label=pie_labels[1]),  # LNG with hatching
        Patch(facecolor=LIGHT_BLUE, label=pie_labels[2])   # Domestic
    ]
    pie_ax.legend(handles=pie_patches, loc='upper center', bbox_to_anchor=(0.5, -0.15), fontsize=7)

    # Add a simplified legend for the main plot including domestic production
    # Creating a dashed line for LNG in the legend
    legend_elements = [
        Line2D([0], [0], color=FLOW_COLOR, linewidth=3, label='Pipeline Natural Gas (PNG) Imports'),
        Patch(facecolor=FLOW_COLOR, 
            label='Liquefied Natural Gas (LNG) Imports',
            hatch='////////', 
            edgecolor='white'),  # Replace dashed line with hatched patch
        Line2D([0], [0], marker='o', color='w', markerfacecolor=SUNNY_YELLOW, markersize=8, label='Exporting Country'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=LIGHT_BLUE, markersize=10, label='Indigenous Production'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=DIGITAL_BLUE, markersize=8, label='European Union - 27 countries (from 2020)')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=8, frameon=True, framealpha=0.9)

    # Minimalist design - no axis
    ax.set_axis_off()

    # Add data source attribution at the bottom of the figure
    fig.text(0.99, 0.01, "Source: Eurostat", 
            fontsize=8, 
            ha='right', 
            va='bottom', 
            style='italic', 
            alpha=0.7)

    plt.tight_layout(rect=[0, 0, 1, 0.94])  # Adjust layout to make room for the title

    # Save the figure if output path specified
    if output_image:
        # If output_image doesn't contain the year, insert it before the extension
        if str(display_year) not in str(output_image):
            output_path = Path(output_image)
            output_image = output_path.with_stem(f"{output_path.stem}_{display_year}").as_posix()
        
        plt.savefig(output_image, dpi=300, bbox_inches='tight')
        print(f"Visualization saved to {output_image}")
    
    plt.show()


def main():
    """Command line entry point for visualization"""
    parser = argparse.ArgumentParser(
        description='Visualize EU gas trade flows from JSON data'
    )
    parser.add_argument(
        'json_file',
        type=str,
        help='Path to the JSON data file'
    )
    parser.add_argument(
        '--year',
        type=int,
        help='Specific year to visualize (defaults to latest year)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to save the output image'
    )
    
    args = parser.parse_args()
    
    # Generate visualization
    visualize_gas_flows(args.json_file, args.year, args.output)


if __name__ == "__main__":
    main()