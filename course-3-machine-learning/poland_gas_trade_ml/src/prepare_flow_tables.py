import pandas as pd
import os

CLEANED_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned_gas_trade.csv')
PRODUCTION_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'estat_nrg_cb_gas_en.csv')
ML_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_disaggregation_2023.csv')
AGG_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_aggregation_2023_with_actuals.csv')
DISAGG_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_disaggregation_2023_with_actuals.csv')

AGGREGATES = [
    "Other African countries (aggregate changing according to the context)",
    "Other American countries (aggregate changing according to the context)",
    "Other Near and Middle East Asian countries",
    "Other European countries (aggregate changing according to the context)",
    "Other countries of former Soviet Union (before 1991)",
    "Not specified"
]

# Countries the GIFs show by name, all other predicted countries are grouped as "Other"
NAMED_COUNTRIES = ['Denmark', 'Qatar', 'Czechia', 'Russia', 'United States', 'Norway']


def share_table(values):
    """Table with the columns the GIF scripts read: country, value and percentage of the total."""
    table = values.rename('predicted_value_normalized').rename_axis('country').reset_index()
    table['share_percent'] = table['predicted_value_normalized'] / table['predicted_value_normalized'].sum() * 100
    # Same cutoff as the Sankey GIF, so countries with a tiny predicted share don't show up as 0.00%
    return table[table['share_percent'] > 0.01]


def main():
    cleaned = pd.read_csv(CLEANED_PATH)
    ml = pd.read_csv(ML_PATH)
    balance = pd.read_csv(PRODUCTION_PATH, low_memory=False)

    # Poland's own production, so the tables show the whole supply and not only imports
    production = balance[
        (balance['Energy balance'] == 'Indigenous production') &
        (balance['Standard international energy product classification (SIEC)'] == 'Natural gas') &
        (balance['Unit of measure'] == 'Million cubic metres') &
        (balance['Geopolitical entity (reporting)'] == 'Poland') &
        (balance['TIME_PERIOD'] == 2023)
    ]['OBS_VALUE']
    domestic = pd.Series({'Poland': production.iloc[0]})

    # 2023 natural gas imports as Eurostat reports them, aggregates and countries
    reported = cleaned[
        (cleaned['TIME_PERIOD'] == 2023) &
        (cleaned['Standard international energy product classification (SIEC)'] == 'Natural gas') &
        (cleaned['Geopolitical entity (partner)'] != 'Total') &
        (cleaned['OBS_VALUE'] > 0)
    ].set_index('Geopolitical entity (partner)')['OBS_VALUE']
    share_table(pd.concat([reported, domestic])).to_csv(AGG_OUTPUT_PATH, index=False)
    print(f"Saved reported 2023 supply to {AGG_OUTPUT_PATH}")

    # Same total, with the aggregates replaced by the model's country split
    reported_countries = reported[~reported.index.isin(AGGREGATES)]
    predicted = ml.groupby('country')['predicted_value_normalized'].sum()
    predicted.index = [c if c in NAMED_COUNTRIES else 'Other' for c in predicted.index]
    predicted = predicted.groupby(level=0).sum()
    combined = pd.concat([predicted, reported_countries, domestic]).groupby(level=0).sum()
    share_table(combined).to_csv(DISAGG_OUTPUT_PATH, index=False)
    print(f"Saved disaggregated 2023 supply to {DISAGG_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
