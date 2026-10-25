import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.patches import FancyBboxPatch, Circle
import os

# Load aggregated and disaggregated data
agg_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_aggregation_2023_with_actuals.csv')
disagg_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_disaggregation_2023_with_actuals.csv')
df_agg = pd.read_csv(agg_path)
df_disagg = pd.read_csv(disagg_path)

# Remove SUM row and any empty rows
df_agg = df_agg[df_agg['country'].notnull() & (df_agg['country'] != 'SUM')]
df_disagg = df_disagg[df_disagg['country'].notnull() & (df_disagg['country'] != 'SUM')]

# Parse values and percentages for aggregates
aggregates = []
for idx, row in df_agg.iterrows():
    name = row['country']
    try:
        value = float(str(row['predicted_value_normalized']).replace(',',''))
    except:
        value = 0
    try:
        pct = float(str(row[df_agg.columns[2]]).replace('%','').replace(',','.'))
    except:
        pct = 0
    aggregates.append({'name': name, 'value': value, 'pct': pct})

# Parse values and percentages for disaggregated
countries = []
for idx, row in df_disagg.iterrows():
    name = row['country']
    try:
        value = float(str(row['predicted_value_normalized']).replace(',',''))
    except:
        value = 0
    try:
        pct = float(str(row[df_disagg.columns[2]]).replace('%','').replace(',','.'))
    except:
        pct = 0
    countries.append({'name': name, 'value': value, 'pct': pct})

# Assign y positions and colors
def get_color(name):
    color_map = {
        # Aggregates
        'Other African countries (aggregate changing according to the context)': '#a0522d',
        'Other American countries (aggregate changing according to the context)': '#b22234',
        'Other Near and Middle East Asian countries': '#ff9933',
        'Other European countries (aggregate changing according to the context)': '#003399',
        'Other countries of former Soviet Union (before 1991)': '#8b008b',
        'Not specified': '#808080',
        # Disaggregated
        'Denmark': '#ef2b2d',
        'Qatar': '#8b1538',
        'Czechia': '#005bbb',
        'Russia': '#0033a0',
        'United States': '#3c3b6e',
        'Other': '#808080',
        'Norway': '#1e90ff',
        'Belgium': '#ffd700',
        'Germany': '#000000',
        'Lithuania': '#006a44',
        'Ukraine': '#0057b7',
        'Poland': '#dc143c',
    }
    return color_map.get(name, '#aaaaaa')

for i, a in enumerate(aggregates):
    a['y'] = 9 - i * 0.7
    a['color'] = get_color(a['name'])
for i, c in enumerate(countries):
    c['y'] = 9 - i * 0.7
    c['color'] = get_color(c['name'])

# Animation parameters
flow_cycle = 60  # frames for one complete flow
frames = 120
transition_frame = frames // 2

# Helper for Poland label (avoid missing glyphs)
def poland_label():
    # Use text fallback if flag glyph is missing
    return 'Poland'

def animate(frame):
    ax.clear()
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    if frame < transition_frame:
        # Stage 1: Aggregated geographies
        ax.text(5, 9.7, 'Poland Natural Gas Supply 2023 (Aggregated Reporting)', ha='center', fontsize=18, fontweight='bold')
        # Poland box
        poland_box = FancyBboxPatch((7, 4), 2, 2, boxstyle="round,pad=0.1",
                                    facecolor='#dc143c', edgecolor='black', linewidth=2)
        ax.add_patch(poland_box)
        ax.text(8, 5, poland_label(), ha='center', va='center', fontsize=14, fontweight='bold', color='white')
        # Aggregated sources
        for a in aggregates:
            box = FancyBboxPatch((0.5, a['y']-0.25), 2.5, 0.5,
                                 boxstyle="round,pad=0.05",
                                 facecolor=a['color'], alpha=0.3,
                                 edgecolor='black', linewidth=1.5)
            ax.add_patch(box)
            ax.text(1.75, a['y'], f"{a['name']}: {a['pct']:.2f}%", ha='center', va='center', fontsize=11)
            ax.plot([3, 7], [a['y'], 5], color='gray', alpha=0.2, linewidth=1, linestyle='--')
            n_dots = max(1, int(a['pct'] / 3))
            for i in range(n_dots):
                offset = (i / n_dots) * flow_cycle
                progress = ((frame + offset) % flow_cycle) / flow_cycle
                eased_progress = 0.5 * (1 - np.cos(progress * np.pi))
                start_x, start_y = 3, a['y']
                end_x, end_y = 7, 5
                dot_x = start_x + (end_x - start_x) * eased_progress
                dot_y = start_y + (end_y - start_y) * eased_progress
                alpha = np.sin(progress * np.pi) * 0.8
                dot = Circle((dot_x, dot_y), 0.09, facecolor=a['color'], alpha=alpha)
                ax.add_patch(dot)
        ax.text(5, 0.7, 'Each dot: flow to Poland (size ~ share)', ha='center', fontsize=10, style='italic')
        ax.text(5, 0.3, 'Stage 1: Aggregated geographies (reported)', ha='center', fontsize=9, style='italic', alpha=0.7)
    else:
        # Stage 2: Disaggregated countries
        ax.text(5, 9.7, 'Poland Natural Gas Supply 2023 (Disaggregated/ML)', ha='center', fontsize=18, fontweight='bold')
        poland_box = FancyBboxPatch((7, 4), 2, 2, boxstyle="round,pad=0.1",
                                    facecolor='#dc143c', edgecolor='black', linewidth=2)
        ax.add_patch(poland_box)
        ax.text(8, 5, poland_label(), ha='center', va='center', fontsize=14, fontweight='bold', color='white')
        for c in countries:
            box = FancyBboxPatch((0.5, c['y']-0.25), 2.5, 0.5,
                                 boxstyle="round,pad=0.05",
                                 facecolor=c['color'], alpha=0.3,
                                 edgecolor='black', linewidth=1.5)
            ax.add_patch(box)
            ax.text(1.75, c['y'], f"{c['name']}: {c['pct']:.2f}%", ha='center', va='center', fontsize=11)
            ax.plot([3, 7], [c['y'], 5], color='gray', alpha=0.2, linewidth=1, linestyle='--')
            n_dots = max(1, int(c['pct'] / 3))
            for i in range(n_dots):
                offset = (i / n_dots) * flow_cycle
                progress = ((frame + offset) % flow_cycle) / flow_cycle
                eased_progress = 0.5 * (1 - np.cos(progress * np.pi))
                start_x, start_y = 3, c['y']
                end_x, end_y = 7, 5
                dot_x = start_x + (end_x - start_x) * eased_progress
                dot_y = start_y + (end_y - start_y) * eased_progress
                alpha = np.sin(progress * np.pi) * 0.8
                dot = Circle((dot_x, dot_y), 0.09, facecolor=c['color'], alpha=alpha)
                ax.add_patch(dot)
        ax.text(5, 0.7, 'Each dot: flow to Poland (size ~ share)', ha='center', fontsize=10, style='italic')
        ax.text(5, 0.3, 'Stage 2: Disaggregated/ML geographies', ha='center', fontsize=9, style='italic', alpha=0.7)

# Set up figure
fig, ax = plt.subplots(figsize=(12, 8))

anim = animation.FuncAnimation(fig, animate, frames=frames, interval=50, repeat=True)

# Save as GIF
print("Saving GIF animation to poland_gas_2023_flows.gif ...")
anim.save(os.path.join(os.path.dirname(__file__), '..', 'data', 'poland_gas_2023_flows.gif'), writer='pillow', fps=20)
print("Done! GIF saved in data/ directory.")

plt.show() 