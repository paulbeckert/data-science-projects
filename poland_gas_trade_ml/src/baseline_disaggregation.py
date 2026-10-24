import pandas as pd
import os
import logging

# Set up logging
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'project.log')
logging.basicConfig(
    filename=LOG_PATH,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("baseline_disaggregation")

TRAINING_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'training_data.csv')
CLEANED_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned_gas_trade.csv')
MAPPING_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'aggregate_country_mapping.csv')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'baseline_disaggregation_2023.csv')

# List of aggregates to disaggregate (add more if needed)
AGGREGATES = [
    "Other African countries (aggregate changing according to the context)",
    "Other American countries (aggregate changing according to the context)",
    "Other Near and Middle East Asian countries",
    "Other European countries (aggregate changing according to the context)",
    "Other countries of former Soviet Union (before 1991)",
    "Not specified"
]

def main():
    logger.info("Loading training, cleaned data, and mapping...")
    df = pd.read_csv(TRAINING_DATA_PATH)
    cleaned = pd.read_csv(CLEANED_DATA_PATH)
    mapping_df = pd.read_csv(MAPPING_PATH)

    # Only use years before 2023 for historical shares
    hist = df[df['year'] < 2023]
    pred_2023 = cleaned[(cleaned['TIME_PERIOD'] == 2023) & (cleaned['Geopolitical entity (partner)'].isin(AGGREGATES))]

    # Get countries reported separately in 2023 (with positive value)
    countries_2023 = set(
        cleaned[
            (cleaned['TIME_PERIOD'] == 2023) &
            (~cleaned['Geopolitical entity (partner)'].isin(AGGREGATES)) &
            (cleaned['OBS_VALUE'] > 0)
        ]['Geopolitical entity (partner)'].unique()
    )

    # Ensure no country is assigned to an aggregate if it is reported separately in 2023
    for agg in AGGREGATES:
        assigned_countries = set(mapping_df[mapping_df['aggregate'] == agg]['country'])
        overlap = assigned_countries & countries_2023
        if overlap:
            logger.warning(f"Countries {overlap} are reported separately in 2023 and assigned to aggregate '{agg}'. They will be excluded from disaggregation.")
            # Remove these countries from the mapping for this aggregate
            mapping_df = mapping_df[~((mapping_df['aggregate'] == agg) & (mapping_df['country'].isin(overlap)))]

    logger.info("Starting baseline disaggregation using mapping...")
    results = []
    for _, row in pred_2023.iterrows():
        aggregate = row['Geopolitical entity (partner)']
        product = row['Standard international energy product classification (SIEC)']
        total_value = row['OBS_VALUE']
        # Get countries assigned to this aggregate
        assigned_countries = mapping_df[mapping_df['aggregate'] == aggregate]['country'].tolist()
        if not assigned_countries:
            logger.warning(f"No countries assigned to aggregate '{aggregate}' for 2023 disaggregation. Skipping.")
            continue
        # Get historical mean shares for these countries
        ms = hist[(hist['partner'].isin(assigned_countries)) & (hist['product'] == product)]
        if ms.empty:
            logger.warning(f"No historical data for assigned countries in aggregate '{aggregate}' and product '{product}'. Skipping.")
            continue
        mean_shares = ms.groupby('partner')['share_of_total'].mean()
        sum_shares = mean_shares.sum()
        if sum_shares == 0:
            logger.warning(f"Sum of mean shares is zero for aggregate '{aggregate}' and product '{product}'. Skipping.")
            continue
        # Normalize shares to sum to 1
        mean_shares = mean_shares / sum_shares
        for country, share in mean_shares.items():
            pred_value = share * total_value
            results.append({
                'year': 2023,
                'product': product,
                'aggregate': aggregate,
                'country': country,
                'predicted_share': share,
                'predicted_value': pred_value
            })
        logger.info(f"Disaggregated {aggregate} ({product}) for 2023 into {len(mean_shares)} countries.")

    out_df = pd.DataFrame(results)
    out_df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Baseline disaggregation predictions saved to {OUTPUT_PATH}")
    logger.info(f"Sample output:\n{out_df.head()}\n")

    # Validation: check sum of predicted_value matches aggregate OBS_VALUE
    logger.info("Validation: Checking sum of predicted_value vs. aggregate OBS_VALUE for each aggregate and product...")
    # Get original aggregate values from 2023
    agg_2023 = cleaned[(cleaned['TIME_PERIOD'] == 2023) & (cleaned['Geopolitical entity (partner)'].isin(AGGREGATES))]
    for (agg, prod), group in out_df.groupby(['aggregate', 'product']):
        pred_sum = group['predicted_value'].sum()
        orig_row = agg_2023[(agg_2023['Geopolitical entity (partner)'] == agg) & (agg_2023['Standard international energy product classification (SIEC)'] == prod)]
        if not orig_row.empty:
            orig_val = orig_row['OBS_VALUE'].values[0]
            diff = abs(pred_sum - orig_val)
            logger.info(f"Aggregate: {agg}, Product: {prod}, Predicted sum: {pred_sum:.3f}, Original: {orig_val:.3f}, Diff: {diff:.6f}")
            if diff > 1e-6:
                logger.warning(f"Discrepancy for {agg}, {prod}: Predicted sum {pred_sum:.3f} != Original {orig_val:.3f}")
        else:
            logger.warning(f"No original OBS_VALUE found for aggregate {agg}, product {prod} in 2023.")

if __name__ == "__main__":
    main() 