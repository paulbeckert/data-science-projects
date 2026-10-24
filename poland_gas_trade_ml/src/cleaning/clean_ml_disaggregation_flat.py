import pandas as pd
import os

INPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_disaggregation_2023.csv')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_disaggregation_2023_flat.csv')

THRESHOLD = 0.02  # 1% as a fraction

def main():
    df = pd.read_csv(INPUT_PATH)
    # Sum up predicted values and shares for each country across all aggregates
    grouped = df.groupby('country').agg({
        'predicted_value_normalized': 'sum',
        'predicted_share_normalized': 'sum'
    }).reset_index()
    total_value = grouped['predicted_value_normalized'].sum()
    # Mark small countries as 'Other'
    grouped['is_other'] = grouped['predicted_value_normalized'] < (THRESHOLD * total_value)
    # Main countries
    main_countries = grouped[~grouped['is_other']].copy()
    # Sum 'Other'
    other_share = grouped.loc[grouped['is_other'], 'predicted_share_normalized'].sum()
    other_value = grouped.loc[grouped['is_other'], 'predicted_value_normalized'].sum()
    # Add 'Other' row if needed
    if other_value > 0:
        other_row = pd.DataFrame([{
            'country': 'Other',
            'predicted_value_normalized': other_value,
            'predicted_share_normalized': other_share
        }])
        final = pd.concat([main_countries, other_row], ignore_index=True)
    else:
        final = main_countries
    # Sort by predicted value
    final = final.sort_values('predicted_value_normalized', ascending=False)
    # Add rank and cumulative share
    final['rank'] = final['predicted_value_normalized'].rank(method='first', ascending=False).astype(int)
    final['cumulative_share'] = final['predicted_share_normalized'].cumsum()
    final.to_csv(OUTPUT_PATH, index=False)
    print(f"Flat cleaned ML disaggregation saved to {OUTPUT_PATH}")
    print(final.head(20))

if __name__ == "__main__":
    main() 