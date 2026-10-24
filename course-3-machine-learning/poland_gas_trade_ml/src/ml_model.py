import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

TRAINING_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'training_data_with_lags.csv')
CLEANED_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned_gas_trade.csv')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_disaggregation_2023.csv')

AGGREGATES = [
    "Other African countries (aggregate changing according to the context)",
    "Other American countries (aggregate changing according to the context)",
    "Other Near and Middle East Asian countries",
    "Other European countries (aggregate changing according to the context)",
    "Other countries of former Soviet Union (before 1991)",
    "Not specified"
]

# Load data
history = pd.read_csv(TRAINING_PATH)
cleaned = pd.read_csv(CLEANED_PATH)

# Filter for Natural gas only
history = history[history['product'] == 'Natural gas']

# 2022 is left out, both for training and as input for the 2023 prediction, because the
# Russian invasion of Ukraine disrupted the trade pattern so much that it would drive the split
train = history[history['year'] < 2022]

# Drop rows with missing lagged features (optional: could impute or fillna(0))
train = train.dropna(subset=['import_value_lag1', 'import_value_lag2', 'share_of_total_lag1', 'share_of_total_lag2'])

# Encode categorical variables
le_country = LabelEncoder()
le_country.fit(history['partner'])
train['country_enc'] = le_country.transform(train['partner'])

# Features and target
features = ['year', 'country_enc', 'import_value_lag1', 'import_value_lag2', 'share_of_total_lag1', 'share_of_total_lag2']
X = train[features]
y = train['share_of_total']

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Prepare 2023 data for prediction
mapping_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'aggregate_country_mapping.csv')
mapping_df = pd.read_csv(mapping_path)

# Get 2023 aggregates and their values
tagged_2023 = cleaned[(cleaned['TIME_PERIOD'] == 2023) & (cleaned['Geopolitical entity (partner)'].isin(AGGREGATES)) & (cleaned['Standard international energy product classification (SIEC)'] == 'Natural gas')]

results = []
for _, agg_row in tagged_2023.iterrows():
    aggregate = agg_row['Geopolitical entity (partner)']
    product = agg_row['Standard international energy product classification (SIEC)']
    total_value = agg_row['OBS_VALUE']
    # Countries assigned to this aggregate
    assigned_countries = mapping_df[mapping_df['aggregate'] == aggregate]['country'].unique()
    for country in assigned_countries:
        # Use the 2021 and 2020 values as lags, skipping 2022
        lagged = history[(history['partner'] == country) & (history['year'] == 2021)]
        if lagged.empty:
            continue  # No lagged data for this country
        row = lagged.iloc[0]
        X_pred = pd.DataFrame([{
            'year': 2023,
            'country_enc': le_country.transform([country])[0],
            'import_value_lag1': row['import_value'],
            'import_value_lag2': row['import_value_lag1'],
            'share_of_total_lag1': row['share_of_total'],
            'share_of_total_lag2': row['share_of_total_lag1']
        }])
        pred_share = model.predict(X_pred)[0]
        pred_value = pred_share * total_value
        results.append({
            'year': 2023,
            'product': product,
            'aggregate': aggregate,
            'country': country,
            'predicted_share': pred_share,
            'predicted_value': pred_value
        })

out_df = pd.DataFrame(results)

# Normalize predicted_share for each aggregate so they sum to 1
out_df['predicted_share_normalized'] = out_df.groupby('aggregate')['predicted_share'].transform(lambda x: x / x.sum() if x.sum() > 0 else 0)

# Map the true aggregate value from 2023 data
agg_totals = tagged_2023.set_index('Geopolitical entity (partner)')['OBS_VALUE'].to_dict()
out_df['aggregate_total_2023'] = out_df['aggregate'].map(agg_totals)
out_df['predicted_value_normalized'] = out_df['predicted_share_normalized'] * out_df['aggregate_total_2023']

out_df.to_csv(OUTPUT_PATH, index=False)
print(f"ML disaggregation predictions saved to {OUTPUT_PATH}")
print(out_df.head()) 