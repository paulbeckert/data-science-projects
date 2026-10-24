import pandas as pd
import logging
import os

# Set up logger
logger = logging.getLogger("data_prep")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# File path
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'estat_nrg_ti_gas_en.csv')

# Aggregated partner names (add more as needed)
AGGREGATED_PARTNERS = [
    "Other African countries (aggregate changing according to the context)",
    "Other American countries (aggregate changing according to the context)",
    "Other Near and Middle East Asian countries",
    "Other European countries (aggregate changing according to the context)",
    "Other countries of former Soviet Union (before 1991)",
    "Not specified",
    "Total"
]

def load_and_clean_data():
    logger.info("Loading data from %s", DATA_PATH)
    df = pd.read_csv(DATA_PATH, low_memory=False)
    logger.info("Initial shape: %s", df.shape)

    # Debug: print column names and unique values
    print("Columns:", df.columns.tolist())
    print("Unique 'Unit of measure':", df['Unit of measure'].unique())
    print("Unique 'Geopolitical entity (reporting)':", df['Geopolitical entity (reporting)'].unique())
    print("Unique 'Standard international energy product classification (SIEC)':", df['Standard international energy product classification (SIEC)'].unique())

    # Standardize column names
    df.columns = [col.strip() for col in df.columns]

    # Filter for Poland, Million cubic metres, and correct SIEC
    df = df[
        (df['Unit of measure'] == 'Million cubic metres') &
        (df['Geopolitical entity (reporting)'] == 'Poland') &
        (df['Standard international energy product classification (SIEC)'].isin([
            'Natural gas', 'Liquefied natural gas']))
    ]
    logger.info("After filtering: %s", df.shape)

    # Mark aggregated vs. disaggregated partners
    df['is_aggregated_partner'] = df['Geopolitical entity (partner)'].apply(
        lambda x: x in AGGREGATED_PARTNERS)

    logger.info("Aggregated partners: %d, Disaggregated: %d", 
        df['is_aggregated_partner'].sum(), (~df['is_aggregated_partner']).sum())

    # Save cleaned data (optional)
    cleaned_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned_gas_trade.csv')
    df.to_csv(cleaned_path, index=False)
    logger.info("Cleaned data saved to %s", cleaned_path)

    return df

if __name__ == "__main__":
    df = load_and_clean_data()
    print(df.head())



