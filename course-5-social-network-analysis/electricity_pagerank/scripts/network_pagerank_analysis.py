"""Network PageRank Analysis for European Electricity Trade

Step 1 Prototype: Load trade flow edge list and perform basic validation.

Planned Next Steps (not yet implemented):
- Build directed weighted graph
- Compute PageRank centrality (alpha configurable)
- Merge with optional domestic generation data
- Export results to CSV and basic visualization

Usage (current step only):
    python network_pagerank_analysis.py --trade-file ../data/electricity_trade_2023_sample.csv

Assumptions:
- CSV has at least columns: exporter, importer, flow_gwh
- flow_gwh is positive numeric value (net annual flow A -> B)

"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Tuple


import pandas as pd
import networkx as nx

REQUIRED_COLUMNS = ["exporter", "importer", "flow_gwh"]


def load_trade_flows(path: Path) -> pd.DataFrame:
    """Load and minimally validate the trade flow edge list.

    Validation rules:
    - Required columns present
    - No missing exporter/importer codes
    - flow_gwh numeric & > 0
    - Drop zero or negative flows (warn)
    - Remove self-loops (exporter == importer)
    - Aggregate duplicate exporter-importer pairs by summing flows
    """
    if not path.exists():
        raise FileNotFoundError(f"Trade flow file not found: {path}")

    df = pd.read_csv(path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Found columns: {list(df.columns)}")

    # Basic cleaning
    before_rows = len(df)
    df = df.dropna(subset=["exporter", "importer", "flow_gwh"])  # drop rows with NAs
    after_dropna = len(df)

    # Coerce numeric
    df["flow_gwh"] = pd.to_numeric(df["flow_gwh"], errors="coerce")
    df = df.dropna(subset=["flow_gwh"])  # remove rows where conversion failed

    # Remove non-positive flows
    positive_mask = df["flow_gwh"] > 0
    removed_non_positive = (~positive_mask).sum()
    df = df[positive_mask]

    # Remove self-loops
    self_loop_mask = df["exporter"] == df["importer"]
    self_loops = df[self_loop_mask]
    df = df[~self_loop_mask]

    # Aggregate duplicates
    df = (
        df.groupby(["exporter", "importer"], as_index=False)["flow_gwh"].sum()
        .sort_values("flow_gwh", ascending=False)
        .reset_index(drop=True)
    )

    print("=== Trade Flow Validation Summary ===")
    print(f"Input rows: {before_rows}")
    print(f"After drop NA rows: {after_dropna}")
    print(f"Removed non-positive flows: {removed_non_positive}")
    print(f"Removed self-loops: {len(self_loops)}")
    print(f"Unique directed edges: {len(df)}")
    total_flow = df["flow_gwh"].sum()
    print(f"Total aggregated flow (GWh): {total_flow:,.0f}")

    return df


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prototype: Load & validate electricity trade flows and compute PageRank")
    parser.add_argument(
        "--trade-file",
        type=Path,
        required=True,
        help="Path to CSV file containing columns exporter, importer, flow_gwh",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.85,
        help="PageRank damping factor (default: 0.85)",
    )
    parser.add_argument(
        "--generation-file",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "electricity_generation_2023.csv",
        help="Path to CSV file with columns country,generation_gwh (default: data/electricity_generation_2023.csv)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    try:
        df = load_trade_flows(args.trade_file)
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print("\nHead of cleaned trade flow table:")
    print(df.head())

    # Step 2: Build directed weighted graph
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_edge(row.exporter, row.importer, weight=row.flow_gwh)

    # Compute node metrics
    in_strength = dict(G.in_degree(weight="weight"))
    out_strength = dict(G.out_degree(weight="weight"))
    all_nodes = set(in_strength) | set(out_strength)
    net_export = {n: out_strength.get(n, 0) - in_strength.get(n, 0) for n in all_nodes}

    # Print summary table
    print("\n=== Node Metrics (GWh) ===")
    print(f"{'Country':<8} {'In_Strength':>12} {'Out_Strength':>13} {'Net_Export':>12}")
    for n in sorted(all_nodes):
        print(f"{n:<8} {in_strength.get(n,0):12,.0f} {out_strength.get(n,0):13,.0f} {net_export[n]:12,.0f}")

    # Step 3: Compute PageRank
    alpha = args.alpha

    pagerank = nx.pagerank(G, alpha=alpha, weight="weight")

    # Verify that the PageRank vector sums to 1
    import pandas as pd
    pagerank_series = pd.Series(pagerank)
    print(f"\nSum of PageRank vector: {pagerank_series.sum():.6f}")

    # Print PageRank results
    print(f"\n=== PageRank Results (alpha={alpha}) ===")
    print(f"{'Country':<8} {'PageRank':>10}")
    for country, score in sorted(pagerank.items(), key=lambda x: x[1], reverse=True):
        print(f"{country:<8} {score:10.4f}")

    # --- Betweenness centrality for all geographies ---
    betweenness = nx.betweenness_centrality(G, weight="weight", normalized=True)


    # Step 4: Merge with production data and classify
    gen_path = args.generation_file
    try:
        generation = pd.read_csv(gen_path)
        generation = generation.set_index("country")
    except Exception:
        print(f"Warning: Could not load generation data from {gen_path}. Skipping merge/classification.")
        generation = None

    # Build merged DataFrame
    import numpy as np
    metrics = []
    for n in sorted(all_nodes):
        metrics.append({
            "country": n,
            "in_strength": in_strength.get(n, 0),
            "out_strength": out_strength.get(n, 0),
            "net_export": net_export[n],
            "pagerank": pagerank.get(n, np.nan),
            "betweenness": betweenness.get(n, np.nan),
            "generation_gwh": generation.loc[n, "generation_gwh"] if generation is not None and n in generation.index else np.nan,
        })
    df_merged = pd.DataFrame(metrics)

    # Classification rules (simple):
    # - Producer: generation > in_strength + out_strength and net_export > 0
    # - Transit: generation < 0.5*(in_strength + out_strength) and in_strength > 0 and out_strength > 0
    # - Consumer: net_export < 0 and generation < in_strength
    def classify(row):
        if np.isnan(row["generation_gwh"]):
            return "unknown"
        if row["generation_gwh"] > (row["in_strength"] + row["out_strength"]) and row["net_export"] > 0:
            return "producer"
        if row["generation_gwh"] < 0.5 * (row["in_strength"] + row["out_strength"]) and row["in_strength"] > 0 and row["out_strength"] > 0:
            return "transit"
        if row["net_export"] < 0 and row["generation_gwh"] < row["in_strength"]:
            return "consumer"
        return "other"

    df_merged["classification"] = df_merged.apply(classify, axis=1)

    # Add interpretative 'role' layer
    import numpy as np
    df_merged['role'] = np.select(
        [
            df_merged['pagerank'] > 0.12,          # structurally central
            df_merged['net_export'] > 2000,        # high exporter
            df_merged['net_export'] < -2000        # high importer
        ],
        ['transit_hub', 'producer', 'consumer'],
        default='balanced'
    )

    print("\n=== Merged Node Table with Classification and Role ===")
    def format_col(col):
        if col in ["pagerank", "betweenness"]:
            return lambda x: f"{x:.4f}"
        else:
            return lambda x: f"{x:,.0f}" if pd.notnull(x) and isinstance(x, (int, float)) else str(x)

    print(df_merged[["country", "generation_gwh", "in_strength", "out_strength", "net_export", "pagerank", "betweenness", "classification", "role"]]
          .to_string(index=False, formatters={
              col: format_col(col) for col in ["generation_gwh", "in_strength", "out_strength", "net_export", "pagerank", "betweenness"]
          }))

    # --- Brand-styled Visualization: PageRank vs Betweenness ---
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    from adjustText import adjust_text
    from matplotlib.colors import LinearSegmentedColormap
    import matplotlib.patheffects as path_effects

    plt.figure(figsize=(11, 8))
    sns.set(style="whitegrid")

    # Set font to PPMori-Light-like (fallback to DejaVu Sans if not available)
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.weight'] = 'light'

    # Brand color palette for diverging colormap (eco green, digital blue, sunny yellow)
    brand_colors = ['#3ACB81', '#FFD70C', '#3F59DC']
    brand_cmap = LinearSegmentedColormap.from_list('brand_cmap', brand_colors, N=256)

    # Filter out countries with NaN generation_gwh
    plot_df = df_merged[df_merged['generation_gwh'].notna()].copy()

    # Convert GWh to TWh for plotting
    plot_df['generation_twh'] = plot_df['generation_gwh'] / 1000
    plot_df['net_export_twh'] = plot_df['net_export'] / 1000

    # Normalize sizes for better visibility (using TWh)
    # Increase the scale factor to make all circles bigger
    size_scale = 5000 / plot_df['generation_twh'].max() if plot_df['generation_twh'].max() > 0 else 1

    # Scatter plot
    # Restore 3-color brand colormap for net export
    from matplotlib.colors import TwoSlopeNorm
    vmin = plot_df['net_export_twh'].min()
    vmax = plot_df['net_export_twh'].max()
    norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
    sc = plt.scatter(
        plot_df['betweenness'],
        plot_df['pagerank'],
        s=plot_df['generation_twh'] * size_scale,
        c=plot_df['net_export_twh'],
        cmap=brand_cmap,
        norm=norm,
        alpha=0.8,
        edgecolor='black',
        linewidth=0.7,
        zorder=5
    )
    cbar = plt.colorbar(sc, label="Net Export (TWh)")

    # Add country labels for all geographies in plot_df, centered in each circle
    # Use adjustText to avoid label overlap and add connecting lines
    texts = []
    for _, row in plot_df.iterrows():
        txt = plt.text(
            row['betweenness'], row['pagerank'], row['country'],
            fontsize=9, ha='center', va='center',
            color='black', weight='light', zorder=10
        )
        txt.set_path_effects([
            path_effects.Stroke(linewidth=2.5, foreground='white'),
            path_effects.Normal()
        ])
        texts.append(txt)
    from adjustText import adjust_text
    adjust_text(
        texts,
        only_move={'points': 'y', 'text': 'xy'},
        expand_points=(2.5, 2.5),
        expand_text=(2.5, 2.5),
        force_points=0.3,
        force_text=0.8,
        arrowprops=dict(arrowstyle='-', color='gray', lw=0.6)
    )

    # Bubble size legend (reference circles for generation, now in TWh)
    ref_sizes_twh = [5, 50, 500]  # TWh
    # Place at top right
    ref_x = plot_df['betweenness'].max() * 0.98 if plot_df['betweenness'].max() > 0 else 0.1
    ref_y_start = plot_df['pagerank'].max() * 0.98 if plot_df['pagerank'].max() > 0 else 0.1
    ref_y_gap = (plot_df['pagerank'].max() - plot_df['pagerank'].min()) * 0.07 if plot_df['pagerank'].max() > plot_df['pagerank'].min() else 0.02
    for i, ref in enumerate(ref_sizes_twh):
        # Move the 500 TWh circle and label a bit lower
        y_offset = 0.007 if ref == 500 else 0.0
        circle_y = ref_y_start - i * ref_y_gap - y_offset
        # Draw the reference circle
        plt.scatter(ref_x, circle_y, s=ref * size_scale, facecolors='none', edgecolors='black', linewidths=1.2, zorder=20)
        # Place the label to the right, with a white halo
        label_x = ref_x + 0.01
        label_y = circle_y
        ref_label = plt.text(
            label_x, label_y, f"{ref} TWh",
            va='center', ha='left', fontsize=9, color='black', weight='light', zorder=21
        )
        ref_label.set_path_effects([
            path_effects.Stroke(linewidth=2.5, foreground='white'),
            path_effects.Normal()
        ])

    # Labels and title
    plt.title("Who matters vs who connects - Electricity trade in Europe (2023)", fontsize=16, weight='light')
    plt.xlabel("Betweenness centrality", fontsize=13, weight='light')
    plt.ylabel("PageRank", fontsize=13, weight='light')
    # Set axes to start at requested values
    plt.xlim(left=-0.01)
    plt.ylim(bottom=-0.002)
    plt.grid(True, linestyle='--', alpha=0.5, zorder=0)

    plt.tight_layout()

    # Save high-resolution image
    plt.savefig("pagerank_vs_betweenness_with_size_legend.png", dpi=300, bbox_inches='tight')
    print('Scatter plot saved to pagerank_vs_betweenness_with_size_legend.png')
    plt.show()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
