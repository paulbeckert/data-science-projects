import pandas as pd
import matplotlib.pyplot as plt
import os

ML_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_disaggregation_2023.csv')
BASELINE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'baseline_disaggregation_2023.csv')
PLOT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

AGGREGATES = [
    "Other African countries (aggregate changing according to the context)",
    "Other American countries (aggregate changing according to the context)",
    "Other Near and Middle East Asian countries",
    "Other European countries (aggregate changing according to the context)",
    "Other countries of former Soviet Union (before 1991)",
    "Not specified"
]

def plot_ml_vs_baseline():
    ml = pd.read_csv(ML_PATH)
    baseline = pd.read_csv(BASELINE_PATH)
    # Use normalized predicted values for ML
    ml = ml[['aggregate', 'country', 'predicted_value_normalized']]
    ml = ml.rename(columns={'predicted_value_normalized': 'ML_predicted'})
    # Use predicted_value for baseline (already sums to aggregate total)
    baseline = baseline[['aggregate', 'country', 'predicted_value']]
    baseline = baseline.rename(columns={'predicted_value': 'Baseline_predicted'})
    for agg in AGGREGATES:
        ml_agg = ml[ml['aggregate'] == agg].groupby('country').sum()
        base_agg = baseline[baseline['aggregate'] == agg].groupby('country').sum()
        # Combine for plotting
        df_plot = pd.concat([ml_agg, base_agg], axis=1).fillna(0)
        df_plot = df_plot.sort_values('ML_predicted', ascending=False)
        plt.figure(figsize=(14, 7))
        bar_width = 0.4
        x = range(len(df_plot))
        bars_ml = plt.bar([i - bar_width/2 for i in x], df_plot['ML_predicted'], width=bar_width, label='ML Predicted')
        bars_base = plt.bar([i + bar_width/2 for i in x], df_plot['Baseline_predicted'], width=bar_width, label='Baseline Predicted')
        plt.title(f'{agg}: ML vs Baseline Disaggregation (2023, Natural gas)')
        plt.ylabel('Predicted Imports (MIO_M3)')
        plt.xlabel('Country')
        plt.xticks(x, df_plot.index, rotation=90)
        plt.legend()
        plt.tight_layout()
        # Add value labels
        for bars, col in zip([bars_ml, bars_base], ['ML_predicted', 'Baseline_predicted']):
            for idx, bar in enumerate(bars):
                height = bar.get_height()
                if height > 0:
                    plt.text(bar.get_x() + bar.get_width() / 2, height, f'{height:.1f}', ha='center', va='bottom', fontsize=7, rotation=90)
        plot_path = os.path.join(PLOT_DIR, f'ml_vs_baseline_{agg[:30].replace(" ", "_")}_2023_natural_gas.png')
        plt.savefig(plot_path)
        plt.close()
        print(f"Saved ML vs Baseline plot: {plot_path}")

if __name__ == "__main__":
    plot_ml_vs_baseline() 