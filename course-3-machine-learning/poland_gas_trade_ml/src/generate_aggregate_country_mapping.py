import pandas as pd
import os
import logging

CLEANED_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned_gas_trade.csv')
MAPPING_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'aggregate_country_mapping.csv')
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'project.log')

logging.basicConfig(
    filename=LOG_PATH,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("aggregate_country_mapping")

# Simple region keyword mapping
REGION_KEYWORDS = {
    'African': 'Africa',
    'American': 'America',
    'European': 'Europe',
    'Near and Middle East Asian': 'Asia',
    'countries of former Soviet Union': 'Soviet',
}

# Helper: assign region to country name (very basic, can be improved)
def assign_region(country):
    africa = ['Algeria', 'Angola', 'Libya', 'Morocco', 'Nigeria', 'Tunisia', 'South Africa', 'Mozambique', 'Congo', 'Gabon', 'Ghana', 'Ivory Coast', 'Senegal', 'Sudan', 'Cameroon', 'Equatorial Guinea', 'Namibia', 'Mauritania', 'Botswana', 'Zimbabwe', 'Zambia', 'Tanzania', 'Uganda', 'Kenya', 'Ethiopia']
    america = ['United States', 'Canada', 'Mexico', 'Trinidad and Tobago', 'Argentina', 'Brazil', 'Venezuela', 'Colombia', 'Peru', 'Bolivia', 'Chile', 'Ecuador', 'Uruguay', 'Paraguay', 'Cuba', 'Dominican Republic', 'Jamaica', 'Bahamas', 'Barbados', 'Honduras', 'Guatemala', 'Nicaragua', 'Panama', 'Costa Rica', 'El Salvador']
    europe = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Czechia', 'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta', 'Netherlands', 'Norway', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'United Kingdom', 'Serbia', 'Moldova', 'Montenegro', 'North Macedonia', 'Bosnia and Herzegovina', 'Albania', 'Kosovo*']
    asia = ['Qatar', 'Iran', 'Iraq', 'Israel', 'Saudi Arabia', 'United Arab Emirates', 'Kuwait', 'Oman', 'Yemen', 'Syria', 'Jordan', 'Lebanon', 'Pakistan', 'India', 'Bangladesh', 'China', 'Japan', 'South Korea', 'North Korea', 'Malaysia', 'Indonesia', 'Singapore', 'Thailand', 'Vietnam', 'Philippines', 'Brunei', 'Myanmar', 'Sri Lanka', 'Afghanistan', 'Mongolia', 'Nepal', 'Cambodia', 'Laos', 'Turkey', 'Egypt']
    soviet = ['Armenia', 'Azerbaijan', 'Belarus', 'Georgia', 'Kazakhstan', 'Kyrgyzstan', 'Moldova', 'Russia', 'Tajikistan', 'Turkmenistan', 'Ukraine', 'Uzbekistan']
    if country in africa:
        return 'Africa'
    if country in america:
        return 'America'
    if country in europe:
        return 'Europe'
    if country in asia:
        return 'Asia'
    if country in soviet:
        return 'Soviet'
    return 'Other'

def main():
    df = pd.read_csv(CLEANED_DATA_PATH)
    # Get all unique countries from historical data (exclude aggregates and not specified/total)
    all_partners = set(df['Geopolitical entity (partner)'].unique())
    aggregates_2023 = set(df[(df['TIME_PERIOD'] == 2023)]['Geopolitical entity (partner)'].unique())
    known_aggregates = [k for k in aggregates_2023 if any(key in k for key in REGION_KEYWORDS.keys()) or k == 'Not specified']
    countries_2023 = set(
        df[
            (df['TIME_PERIOD'] == 2023) &
            (~df['Geopolitical entity (partner)'].isin(known_aggregates)) &
            (df['OBS_VALUE'] > 0)
        ]['Geopolitical entity (partner)'].unique()
    )
    # Only use countries that are not aggregates or not specified/total
    all_countries = [c for c in all_partners if c not in known_aggregates and c not in ['Total', 'Not specified']]

    logger.info(f"Total unique countries in historical data: {len(all_countries)}. Examples: {all_countries[:10]}")
    logger.info(f"Countries reported separately in 2023: {len(countries_2023)}. Examples: {list(countries_2023)[:10]}")
    logger.info(f"Aggregates detected in 2023: {len(known_aggregates)}. {known_aggregates}")
    not_reported_2023 = [c for c in all_countries if c not in countries_2023]
    logger.info(f"Countries NOT reported separately in 2023: {len(not_reported_2023)}. Examples: {not_reported_2023[:10]}")

    # Assign region to each country
    country_region = {c: assign_region(c) for c in all_countries}
    # For each aggregate, assign countries not reported separately in 2023 and matching the region
    mapping = []
    for agg in known_aggregates:
        for key, region in REGION_KEYWORDS.items():
            if key in agg:
                # Countries in this region and not reported separately in 2023
                assigned = [c for c in all_countries if country_region[c] == region and c not in countries_2023]
                for c in assigned:
                    mapping.append({'aggregate': agg, 'country': c})
    # For 'Not specified', assign all countries not reported separately in 2023
    for c in all_countries:
        if c not in countries_2023:
            mapping.append({'aggregate': 'Not specified', 'country': c})
    mapping_df = pd.DataFrame(mapping)
    mapping_df.to_csv(MAPPING_PATH, index=False)
    logger.info(f"Aggregate-country mapping saved to {MAPPING_PATH}. Mapping rows: {len(mapping_df)}")
    logger.info(f"Sample mapping: {mapping_df.head(20).to_dict('records')}")

if __name__ == "__main__":
    main() 