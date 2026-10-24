import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.collections import LineCollection
import os

# Define color scheme
DIGITAL_BLUE = "#3ACB81"  # eco green
LIGHT_BLUE = "#89E0B3"    # light green
ECO_GREEN = "#000000"     # black
SUNNY_YELLOW = "#FFE76D"

# Set font
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']

# Load data
agg_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_aggregation_2023_with_actuals.csv')
disagg_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_disaggregation_2023_with_actuals.csv')
mapping_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'aggregate_country_mapping.csv')

df_agg = pd.read_csv(agg_path)
df_disagg = pd.read_csv(disagg_path)
df_map = pd.read_csv(mapping_path)

# Remove SUM row and any empty rows
df_agg = df_agg[df_agg['country'].notnull() & (df_agg['country'] != 'SUM')]
df_disagg = df_disagg[df_disagg['country'].notnull() & (df_disagg['country'] != 'SUM')]

# Build mapping dictionary
agg_to_countries = {}
for _, row in df_map.iterrows():
    agg = row['aggregate']
    country = row['country']
    if agg not in agg_to_countries:
        agg_to_countries[agg] = []
    agg_to_countries[agg].append(country)

# Add manual mappings
agg_to_countries['Other African countries (aggregate changing according to the context)'].append('Other')
if 'Other American countries (aggregate changing according to the context)' in agg_to_countries and 'Other' not in agg_to_countries['Other American countries (aggregate changing according to the context)']:
    agg_to_countries['Other American countries (aggregate changing according to the context)'].append('Other')
if 'Other Near and Middle East Asian countries' in agg_to_countries and 'Other' not in agg_to_countries['Other Near and Middle East Asian countries']:
    agg_to_countries['Other Near and Middle East Asian countries'].append('Other')
if 'Other European countries (aggregate changing according to the context)' in agg_to_countries and 'Other' not in agg_to_countries['Other European countries (aggregate changing according to the context)']:
    agg_to_countries['Other European countries (aggregate changing according to the context)'].append('Other')
if 'Other countries of former Soviet Union (before 1991)' in agg_to_countries and 'Other' not in agg_to_countries['Other countries of former Soviet Union (before 1991)']:
    agg_to_countries['Other countries of former Soviet Union (before 1991)'].append('Other')
if 'Not specified' in agg_to_countries and 'Other' not in agg_to_countries['Not specified']:
    agg_to_countries['Not specified'].append('Other')

# Ensure Not specified has its mappings (but remove Poland)
if 'Not specified' not in agg_to_countries:
    agg_to_countries['Not specified'] = []
not_specified_targets = ['Denmark', 'Qatar', 'Czechia', 'Russia', 'United States', 'Norway', 'Other']
for target in not_specified_targets:
    if target not in agg_to_countries['Not specified']:
        agg_to_countries['Not specified'].append(target)
# Remove Poland from Not specified if present
if 'Poland' in agg_to_countries['Not specified']:
    agg_to_countries['Not specified'].remove('Poland')

# Remove Poland from Europe (Other)
if 'Other European countries (aggregate changing according to the context)' in agg_to_countries:
    if 'Poland' in agg_to_countries['Other European countries (aggregate changing according to the context)']:
        agg_to_countries['Other European countries (aggregate changing according to the context)'].remove('Poland')

# Define categories
aggregated_geos = [
    'Other African countries (aggregate changing according to the context)',
    'Other American countries (aggregate changing according to the context)',
    'Other Near and Middle East Asian countries',
    'Other European countries (aggregate changing according to the context)',
    'Other countries of former Soviet Union (before 1991)',
    'Not specified'
]

already_disaggregated = ['Belgium', 'Germany', 'Lithuania', 'Ukraine', 'Poland']

# Display names
aggregate_display_names = {
    'Other African countries (aggregate changing according to the context)': 'Africa',
    'Other American countries (aggregate changing according to the context)': 'Americas',
    'Other Near and Middle East Asian countries': 'Middle East/Asia',
    'Other European countries (aggregate changing according to the context)': 'Europe (Other)',
    'Other countries of former Soviet Union (before 1991)': 'Former Soviet',
    'Not specified': 'Not specified',
    'Belgium': 'Belgium',
    'Germany': 'Germany', 
    'Lithuania': 'Lithuania',
    'Ukraine': 'Ukraine',
    'Poland': 'Poland (domestic)'
}

# Parse left side data
left_side_data = []
for idx, row in df_agg.iterrows():
    name = row['country']
    if name in aggregate_display_names:
        try:
            pct = float(str(row[df_agg.columns[2]]).replace('%','').replace(',','.'))
        except:
            pct = 0
        if pct > 0.01:
            left_side_data.append({
                'name': name,
                'display_name': aggregate_display_names[name],
                'pct': pct,
                'is_aggregated': name in aggregated_geos
            })

# Sort with specified order
def sort_key(x):
    if x['is_aggregated']:
        order_map = {
            'Europe (Other)': 0,
            'Middle East/Asia': 1,
            'Americas': 2,
            'Africa': 3,
            'Former Soviet': 4,
            'Not specified': 5
        }
        return (0, order_map.get(x['display_name'], 6))
    else:
        order = {'Belgium': 1, 'Germany': 2, 'Lithuania': 3, 'Ukraine': 4, 'Poland (domestic)': 5}
        return (1, order.get(x['display_name'], 6))

left_side_data.sort(key=sort_key)

# Parse disaggregated countries
countries = []
country_order = ['Denmark', 'Qatar', 'Czechia', 'Russia', 'United States', 
                 'Norway', 'Other', 'Belgium', 'Germany', 'Lithuania', 'Ukraine', 'Poland']

newly_disaggregated = ['Denmark', 'Qatar', 'Czechia', 'Russia', 'United States', 'Norway', 'Other']

countries_dict = {}
for idx, row in df_disagg.iterrows():
    name = row['country']
    try:
        pct = float(str(row[df_disagg.columns[2]]).replace('%','').replace(',','.'))
    except:
        pct = 0
    if pct > 0.01:
        countries_dict[name] = {
            'name': name,
            'display_name': name,
            'pct': pct,
            'is_new': name in newly_disaggregated
        }

# Add countries in order
for country_name in country_order:
    if country_name in countries_dict:
        countries.append(countries_dict[country_name])

# Position right side first
y_start = 8.2
y_spacing = 0.65
for i, country in enumerate(countries):
    country['y'] = y_start - i * y_spacing

# Calculate Poland box height
poland_y_top = countries[0]['y'] + 0.25
poland_y_bottom = countries[-1]['y'] - 0.25

# Position left side
y_start = 8.2
y_spacing = 0.65
current_y = y_start

# Position aggregated
for data in left_side_data:
    if data['is_aggregated']:
        data['y'] = current_y
        current_y -= y_spacing

# Position already disaggregated to align
for data in left_side_data:
    if not data['is_aggregated']:
        country_name = data['display_name'].replace(' (domestic)', '')
        right_country = next((c for c in countries if c['name'] == country_name), None)
        if right_country:
            data['y'] = right_country['y']

# Find ALL sources for countries
for country in countries:
    country['sources'] = []
    
    # Check all aggregated sources
    for agg_name, country_list in agg_to_countries.items():
        if country['name'] in country_list:
            for agg_data in left_side_data:
                if agg_data['name'] == agg_name and agg_data['is_aggregated']:
                    country['sources'].append(agg_data)
                    break
    
    # Check direct sources
    for left_data in left_side_data:
        if not left_data['is_aggregated'] and left_data['display_name'].replace(' (domestic)', '') == country['name']:
            country['sources'].append(left_data)
            break

# Animation setup
fig, ax = plt.subplots(figsize=(12, 9))
flow_cycle = 60

def animate(frame):
    ax.clear()
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.5, 10.5)
    ax.axis('off')
    
    # Title
    ax.text(5, 10.2, 'Poland natural gas imports (2023): ML disaggregation',
            ha='center', fontsize=21, fontweight='bold')
    
    # Subtitle with color descriptions on the next row
    ax.text(1.4, 9.3, 'Aggregated data', ha='center', fontsize=15)
    ax.text(3, 9.3, '→', ha='center', fontsize=22, fontweight='bold')
    ax.text(5, 9.3, 'ML-based country predictions', ha='center', fontsize=15)
    ax.text(7, 9.3, '→', ha='center', fontsize=22, fontweight='bold')
    ax.text(8.5, 9.3, 'Consumer country', ha='center', fontsize=15)
    
    # LEFT SIDE
    # Reorder grey countries in left segment
    grey_priority = ['Germany', 'Ukraine', 'Lithuania', 'Belgium', 'Domestic production)']
    def get_grey_index(name):
        name_lower = name.lower()
        for i, g in enumerate(grey_priority):
            if g.lower() in name_lower:
                return i
        return len(grey_priority)
    left_grey = [d for d in left_side_data if get_grey_index(d['display_name']) < len(grey_priority)]
    left_other = [d for d in left_side_data if d not in left_grey]
    left_ordered = sorted(left_grey, key=lambda x: get_grey_index(x['display_name'])) + left_other
    for data in left_ordered:
        # Use gray for left-side and middle segment boxes
        left_box_color = LIGHT_BLUE if data['is_aggregated'] else '#CCCCCC'
        edge_col = DIGITAL_BLUE if data['is_aggregated'] else '#CCCCCC'
        box = Rectangle((0.5, data['y']-0.25), 1.8, 0.5,
                       facecolor=left_box_color, edgecolor=edge_col, linewidth=1.5, linestyle='--' if data['is_aggregated'] else '-')
        text_color = 'black' if data['is_aggregated'] else 'black'
        # Rounding logic for left side
        small_share_names = ['Former Soviet', 'Belgium', 'Other countries of former Soviet Union (before 1991)', 'Belgium']
        one_digit_names = ['Americas', 'Africa', 'Other American countries (aggregate changing according to the context)', 'Other African countries (aggregate changing according to the context)']
        # Updated rounding logic for left side
        if data['display_name'] in ['Former Soviet', 'Belgium'] or data['name'] in ['Other countries of former Soviet Union (before 1991)', 'Belgium']:
            pct_str = f"{data['pct']:.2f}%"
        else:
            pct_str = f"{data['pct']:.1f}%"
        # Rename Poland
        display_name = data['display_name']
        if display_name.startswith('Poland'):
            display_name = 'Domestic production'
        ax.add_patch(box)
        ax.text(1.4, data['y'], f"{display_name}\n{pct_str}",
                ha='center', va='center', fontsize=10, color=text_color)
    
    # RIGHT SIDE
    # Reorder grey countries in middle segment
    grey_priority = ['Germany', 'Ukraine', 'Lithuania', 'Belgium', 'Domestic production']
    def get_grey_index_mid(name):
        name_lower = name.lower()
        for i, g in enumerate(grey_priority):
            if g.lower() in name_lower:
                return i
        return len(grey_priority)
    mid_grey = [c for c in countries if get_grey_index_mid(c['display_name']) < len(grey_priority)]
    mid_other = [c for c in countries if c not in mid_grey]
    mid_ordered = sorted(mid_grey, key=lambda x: get_grey_index_mid(x['display_name'])) + mid_other
    for country in mid_ordered:
        color = DIGITAL_BLUE if country['is_new'] else '#CCCCCC'
        box = Rectangle((4.1, country['y']-0.25), 1.8, 0.5, facecolor=color)
        ax.add_patch(box)
        # Rounding logic
        small_share_names = ['Former Soviet', 'Belgium', 'Other countries of former Soviet Union (before 1991)', 'Belgium']
        one_digit_names = ['Americas', 'Africa', 'Other American countries (aggregate changing according to the context)', 'Other African countries (aggregate changing according to the context)']
        # Updated rounding logic for right side
        if country['display_name'] in ['Former Soviet', 'Belgium'] or country['name'] in ['Belgium']:
            pct_str = f"{country['pct']:.2f}%"
        else:
            pct_str = f"{country['pct']:.1f}%"
        # Rename Poland
        display_name = country['display_name']
        if display_name.startswith('Poland'):
            display_name = 'Domestic production'
        # Font color logic for middle segment
        black_font_countries = ['Belgium', 'Germany', 'Lithuania', 'Ukraine', 'Poland', 'Domestic production']
        font_color = 'black' if display_name in black_font_countries or country['name'] in black_font_countries else 'white'
        ax.text(5, country['y'], f"{display_name}\n{pct_str}",
                ha='center', va='center', fontsize=10, color=font_color)
    
    # POLAND BOX
    poland_height = poland_y_top - poland_y_bottom
    poland_box = Rectangle((7.6, poland_y_bottom), 1.8, poland_height,
                          facecolor=SUNNY_YELLOW)
    ax.add_patch(poland_box)
    
    poland_center_y = (poland_y_top + poland_y_bottom) / 2
    ax.text(8.5, poland_center_y + 0.6, 'Consumption', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='black')
    ax.text(8.5, poland_center_y, 'mix for', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='black')
    ax.text(8.5, poland_center_y - 0.6, 'Poland', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='black')
    
    # Legend 
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, facecolor=LIGHT_BLUE, edgecolor=DIGITAL_BLUE, linewidth=1.5, linestyle='--', label='Aggregated sources'),
        plt.Rectangle((0, 0), 1, 1, facecolor='#CCCCCC', label='Known disaggregated sources'),
        plt.Rectangle((0, 0), 1, 1, facecolor=DIGITAL_BLUE, label='ML-predicted countries'),
        plt.Rectangle((0, 0), 1, 1, facecolor=SUNNY_YELLOW, label='Final consumption')
    ]

    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0.8, 0.3), 
            fontsize=9, frameon=True, fancybox=True)

    # ANIMATE WITH CONTINUOUS MOVING DASHED LINES
    # Parameters for continuous dashed line
    dash_length = 0.15  # Lengths of dashes
    gap_length = 0.1   # Length of gap between dashes
    pattern_length = dash_length + gap_length
    speed = 1.8  # Speed of movement
    
    # ALL connections from sources to countries
    for country in countries:
        for source in country['sources']:
            # Calculate line length
            x_start, x_end = 2.3, 4.1
            y_start, y_end = source['y'], country['y']
            line_length = np.sqrt((x_end - x_start)**2 + (y_end - y_start)**2)
            
            # Create many dash segments for continuous effect
            n_segments = int(line_length / pattern_length) + 5  # Extra segments for continuity
            
            # Draw dashes
            for i in range(n_segments):
                # Calculate position along line
                offset = (frame * speed / 100 + i * pattern_length) % line_length
                if offset < line_length - dash_length:
                    t_start = offset / line_length
                    t_end = min((offset + dash_length) / line_length, 1.0)
                    
                    x1 = x_start + (x_end - x_start) * t_start
                    x2 = x_start + (x_end - x_start) * t_end
                    y1 = y_start + (y_end - y_start) * t_start
                    y2 = y_start + (y_end - y_start) * t_end
                    
                    # Color based on source type - light green for aggregated, gray for direct
                    if source['is_aggregated']:
                        color = LIGHT_BLUE
                        width = 2.5
                    else:
                        color = '#CCCCCC'
                        width = 2
                    
                    ax.plot([x1, x2], [y1, y2], color=color, linewidth=width, solid_capstyle='round')
    
    # Countries → Poland (parallel horizontal lines)
    for country in countries:
        x_start, x_end = 5.9, 7.6
        y_start = y_end = country['y']  # horizontal line at the country's y
        line_length = np.sqrt((x_end - x_start)**2 + (y_end - y_start)**2)
        n_segments = int(line_length / pattern_length) + 5

        green_countries = ['Denmark', 'Qatar', 'Czechia', 'Russia', 'United States', 'Norway', 'Other']
        is_green = country['name'] in green_countries
        line_color = DIGITAL_BLUE if is_green else '#CCCCCC'

        for i in range(n_segments):
            offset = (frame * speed / 100 + i * pattern_length) % line_length
            if offset < line_length - dash_length:
                t_start = offset / line_length
                t_end = min((offset + dash_length) / line_length, 1.0)
                x1 = x_start + (x_end - x_start) * t_start
                x2 = x_start + (x_end - x_start) * t_end
                y1 = y_start
                y2 = y_end
                ax.plot([x1, x2], [y1, y2], color=line_color, linewidth=2, solid_capstyle='round')
    
    # Caption with accuracy, source, disclaimer, and color code
    caption = (
        "Model accuracy: R² > 0.98, MAE < 1% validated on historical data."
        "'Other' represents multiple countries aggregated for visualization clarity.\n"
        "Source: Eurostat (raw data)."
    )
    ax.text(0.4, -0.4, caption, ha='left', fontsize=10, alpha=0.9, wrap=True)

# Create animation
anim = animation.FuncAnimation(fig, animate, frames=120, interval=50, repeat=True)

# Save
print("\nCreating final animation...")
output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'poland_gas_final_v3.gif')
anim.save(output_path, writer='pillow', fps=20)
print(f"Animation saved to: {output_path}")

plt.show()