import pandas as pd
import os

INPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_disaggregation_2023.csv')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_disaggregation_2023_cleaned.csv')

THRESHOLD = 0.0001  # 0.01% as a fraction

def clean_and_group_other(df):
    cleaned = []
    for agg, group in df.groupby('aggregate'):
        total = group['aggregate_total_2023'].iloc[0]
        # Mark countries below threshold
        group['is_other'] = group['predicted_value_normalized'] < (THRESHOLD * total)
        # Sum 'other' countries
        other_share = group.loc[group['is_other'], 'predicted_share_normalized'].sum()
        other_value = group.loc[group['is_other'], 'predicted_value_normalized'].sum()
        # Keep only main countries
        main_countries = group[~group['is_other']].copy()
        # Add 'Other' row if needed
        if other_value > 0:
            other_row = main_countries.iloc[0].copy()
            other_row['country'] = 'Other'
            other_row['predicted_share_normalized'] = other_share
            other_row['predicted_value_normalized'] = other_value
            cleaned.append(pd.concat([main_countries, pd.DataFrame([other_row])], ignore_index=True))
        else:
            cleaned.append(main_countries)
    return pd.concat(cleaned, ignore_index=True)

def main():
    df = pd.read_csv(INPUT_PATH)
    df_cleaned = clean_and_group_other(df)
    df_cleaned = df_cleaned.drop(columns=['is_other'], errors='ignore')
    df_cleaned.to_csv(OUTPUT_PATH, index=False)
    print(f"Cleaned ML disaggregation saved to {OUTPUT_PATH}")
    print(df_cleaned.head())

if __name__ == "__main__":
    main()  