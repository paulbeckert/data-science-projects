import pandas as pd
import matplotlib.pyplot as plt
import os

CLEANED_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned_gas_trade.csv')

def main():
    # Load data
    df = pd.read_csv(CLEANED_DATA_PATH)
    print("\n--- Data Head ---\n", df.head())
    print("\n--- Data Info ---\n")
    print(df.info())
    print("\n--- Missing Values ---\n", df.isnull().sum())
    print("\n--- Columns ---\n", df.columns.tolist())

    # Total imports by year
    total_by_year = df.groupby('TIME_PERIOD')['OBS_VALUE'].sum()
    print("\n--- Total Imports by Year ---\n", total_by_year)
    total_by_year.plot(title='Total Gas Imports to Poland by Year', marker='o')
    plt.xlabel('Year')
    plt.ylabel('Imports (MIO_M3)')
    plt.tight_layout()
    plt.show()

    # Top partners (excluding aggregates)
    disagg = df[~df['is_aggregated_partner']]
    top_partners = disagg.groupby('Geopolitical entity (partner)')['OBS_VALUE'].sum().sort_values(ascending=False).head(10)
    print("\n--- Top 10 Partners (All Years) ---\n", top_partners)
    top_partners.plot(kind='bar', title='Top 10 Export Partners to Poland (Total 1990-2023)')
    plt.ylabel('Total Imports (MIO_M3)')
    plt.tight_layout()
    plt.show()

    # Aggregated vs. disaggregated share by year
    share_by_year = df.groupby(['TIME_PERIOD', 'is_aggregated_partner'])['OBS_VALUE'].sum().unstack(fill_value=0)
    share_by_year.plot(kind='bar', stacked=True, title='Aggregated vs. Disaggregated Imports by Year', figsize=(12,6))
    plt.ylabel('Imports (MIO_M3)')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main() 