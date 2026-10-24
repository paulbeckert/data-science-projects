import pandas as pd
import os

CLEANED_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned_gas_trade.csv')
TRAINING_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'training_data.csv')

EXCLUDE_PARTNERS = ["Total"]

def main():
    df = pd.read_csv(CLEANED_DATA_PATH)

    # Exclude 'Total' partners
    df = df[~df['Geopolitical entity (partner)'].isin(EXCLUDE_PARTNERS)]

    # Calculate total imports per year and product
    df['year'] = df['TIME_PERIOD']
    df['product'] = df['Standard international energy product classification (SIEC)']
    df['partner'] = df['Geopolitical entity (partner)']
    df['import_value'] = df['OBS_VALUE']

    # Group to get total per year/product
    total_by_year_product = df.groupby(['year', 'product'])['import_value'].sum().reset_index()
    total_by_year_product = total_by_year_product.rename(columns={'import_value': 'total_imports'})

    # Merge total imports back to main df
    df = df.merge(total_by_year_product, on=['year', 'product'], how='left')
    df['share_of_total'] = df['import_value'] / df['total_imports']

    # Select relevant columns
    out_df = df[['year', 'product', 'partner', 'import_value', 'share_of_total']]
    out_df.to_csv(TRAINING_DATA_PATH, index=False)
    print(f"Training data saved to {TRAINING_DATA_PATH}")
    print(out_df.head())

if __name__ == "__main__":
    main() 