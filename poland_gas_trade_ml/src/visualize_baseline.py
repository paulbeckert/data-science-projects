import pandas as pd
import matplotlib.pyplot as plt
import os

BASELINE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'baseline_disaggregation_2023.csv')
TRAINING_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'training_data.csv')
PLOT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

AGGREGATES = [
    "Other African countries (aggregate changing according to the context)",
    "Other American countries (aggregate changing according to the context)",
    "Other Near and Middle East Asian countries",
    "Other European countries (aggregate changing according to the context)",
    "Other countries of former Soviet Union (before 1991)",
    "Not specified"
]


def plot_baseline_2023():
    df = pd.read_csv(BASELINE_PATH)
    df = df[df['product'] == 'Natural gas']
    for agg in df['aggregate'].unique():
        agg_df = df[df['aggregate'] == agg].sort_values('predicted_value', ascending=False)
        plt.figure(figsize=(10, 6))
        bars = plt.bar(agg_df['country'], agg_df['predicted_value'])
        plt.title(f'2023 Baseline Disaggregation: {agg} (Natural gas)')
        plt.ylabel('Predicted Imports (MIO_M3)')
        plt.xlabel('Country')
        plt.xticks(rotation=90)
        plt.tight_layout()
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                plt.text(bar.get_x() + bar.get_width() / 2, height, f'{height:.1f}', ha='center', va='bottom', fontsize=8, rotation=90)
        plot_path = os.path.join(PLOT_DIR, f'baseline_2023_{agg[:30].replace(" ", "_")}_natural_gas.png')
        plt.savefig(plot_path)
        plt.close()
        print(f"Saved plot: {plot_path}")

def compare_with_previous_years(years=[2021, 2022]):
    baseline = pd.read_csv(BASELINE_PATH)
    training = pd.read_csv(TRAINING_PATH)
    baseline = baseline[baseline['product'] == 'Natural gas']
    training = training[training['product'] == 'Natural gas']
    for agg in baseline['aggregate'].unique():
        countries = baseline[baseline['aggregate'] == agg]['country'].unique()
        # Get actuals for each year
        actuals = {}
        for y in years:
            prev = training[(training['year'] == y) & (training['partner'].isin(countries))]
            prev = prev.groupby('partner')['import_value'].sum()
            actuals[y] = prev
        # Get baseline 2023 prediction
        base = baseline[baseline['aggregate'] == agg].set_index('country')['predicted_value']
        # Combine for plotting
        df_plot = pd.DataFrame({'2023_predicted': base})
        for y in years:
            df_plot[f'{y}_actual'] = actuals[y]
        df_plot = df_plot.fillna(0)
        df_plot = df_plot.sort_values('2023_predicted', ascending=False)
        plt.figure(figsize=(14, 7))
        bar_width = 0.25
        x = range(len(df_plot))
        # Plot order: 2021 actual, 2022 actual, 2023 baseline
        bars_2021 = plt.bar([i - bar_width for i in x], df_plot['2021_actual'], width=bar_width, label='2021 Actual')
        bars_2022 = plt.bar(x, df_plot['2022_actual'], width=bar_width, label='2022 Actual')
        bars_2023 = plt.bar([i + bar_width for i in x], df_plot['2023_predicted'], width=bar_width, label='2023 Baseline')
        plt.title(f'{agg}: 2023 Baseline vs 2021 & 2022 Actual (Natural gas)')
        plt.ylabel('Imports (MIO_M3)')
        plt.xlabel('Country')
        plt.xticks(x, df_plot.index, rotation=90)
        plt.legend()
        plt.tight_layout()
        # Add value labels in the same order
        for bars, col in zip([bars_2021, bars_2022, bars_2023], ['2021_actual', '2022_actual', '2023_predicted']):
            for idx, bar in enumerate(bars):
                height = bar.get_height()
                if height > 0:
                    plt.text(bar.get_x() + bar.get_width() / 2, height, f'{height:.1f}', ha='center', va='bottom', fontsize=7, rotation=90)
        plot_path = os.path.join(PLOT_DIR, f'compare_{agg[:30].replace(" ", "_")}_2023_vs_2021_2022_natural_gas.png')
        plt.savefig(plot_path)
        plt.close()
        print(f"Saved comparison plot: {plot_path}")

if __name__ == "__main__":
    plot_baseline_2023()
    compare_with_previous_years(years=[2021, 2022]) 