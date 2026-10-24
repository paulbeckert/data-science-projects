import pandas as pd
import os

TRAINING_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'training_data.csv')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'training_data_with_lags.csv')

# Load data

def add_lagged_features(df, lags=[1, 2]):
    df = df.sort_values(['partner', 'product', 'year'])
    for lag in lags:
        df[f'import_value_lag{lag}'] = df.groupby(['partner', 'product'])['import_value'].shift(lag)
        df[f'share_of_total_lag{lag}'] = df.groupby(['partner', 'product'])['share_of_total'].shift(lag)
    return df

def main():
    df = pd.read_csv(TRAINING_DATA_PATH)
    df_with_lags = add_lagged_features(df, lags=[1, 2])
    df_with_lags.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved training data with lagged features to {OUTPUT_PATH}")
    print(df_with_lags.head())

if __name__ == "__main__":
    main() 