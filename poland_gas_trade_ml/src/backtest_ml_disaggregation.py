import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

TRAINING_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'training_data_with_lags.csv')
MAPPING_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'aggregate_country_mapping.csv')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_backtest_disaggregation.csv')

AGGREGATES = [
    "Other African countries (aggregate changing according to the context)",
    "Other American countries (aggregate changing according to the context)",
    "Other Near and Middle East Asian countries",
    "Other European countries (aggregate changing according to the context)",
    "Other countries of former Soviet Union (before 1991)",
    "Not specified"
]

BACKTEST_YEAR = 2019  # Change to 2022 or another year as needed

# Load data
train = pd.read_csv(TRAINING_PATH)
mapping_df = pd.read_csv(MAPPING_PATH)

# Only use years before the backtest year for training
train_model = train[train['year'] < BACKTEST_YEAR]

# Filter for Natural gas only
train_model = train_model[train_model['product'] == 'Natural gas']

# Drop rows with missing lagged features
train_model = train_model.dropna(subset=['import_value_lag1', 'import_value_lag2', 'share_of_total_lag1', 'share_of_total_lag2'])

# Encode categorical variables
le_country = LabelEncoder()
le_country.fit(train['partner'])
train_model['country_enc'] = le_country.transform(train_model['partner'])

# Features and target
features = ['year', 'country_enc', 'import_value_lag1', 'import_value_lag2', 'share_of_total_lag1', 'share_of_total_lag2']
X = train_model[features]
y = train_model['share_of_total']

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Prepare backtest data for prediction
results = []
for agg in AGGREGATES:
    # Countries assigned to this aggregate
    assigned_countries = mapping_df[mapping_df['aggregate'] == agg]['country'].unique()
    # Get the aggregate total for the backtest year (sum over assigned countries)
    agg_total = train[(train['year'] == BACKTEST_YEAR) & (train['partner'].isin(assigned_countries)) & (train['product'] == 'Natural gas')]['import_value'].sum()
    if agg_total == 0:
        continue
    # For each country, get lagged features from the previous year
    preds = []
    for country in assigned_countries:
        lagged = train[(train['partner'] == country) & (train['product'] == 'Natural gas') & (train['year'] == BACKTEST_YEAR)]
        if lagged.empty:
            continue
        row = lagged.iloc[0]
        X_pred = pd.DataFrame([{
            'year': BACKTEST_YEAR,
            'country_enc': le_country.transform([country])[0],
            'import_value_lag1': row['import_value_lag1'],
            'import_value_lag2': row['import_value_lag2'],
            'share_of_total_lag1': row['share_of_total_lag1'],
            'share_of_total_lag2': row['share_of_total_lag2']
        }])
        pred_share = model.predict(X_pred)[0]
        preds.append({'country': country, 'predicted_share': pred_share})
    # Normalize predicted shares
    pred_df = pd.DataFrame(preds)
    if pred_df.empty:
        continue
    pred_df['predicted_share_normalized'] = pred_df['predicted_share'] / pred_df['predicted_share'].sum() if pred_df['predicted_share'].sum() > 0 else 0
    pred_df['predicted_value_normalized'] = pred_df['predicted_share_normalized'] * agg_total
    # Get true shares and values
    true_df = train[(train['year'] == BACKTEST_YEAR) & (train['partner'].isin(assigned_countries)) & (train['product'] == 'Natural gas')][['partner', 'import_value']]
    true_df = true_df.groupby('partner')['import_value'].sum().reset_index().rename(columns={'partner': 'country', 'import_value': 'true_value'})
    true_df['true_share'] = true_df['true_value'] / agg_total
    # Merge predictions and true values
    merged = pd.merge(pred_df, true_df, on='country', how='outer').fillna(0)
    merged['aggregate'] = agg
    merged['agg_total'] = agg_total
    merged['year'] = BACKTEST_YEAR
    results.append(merged)

out_df = pd.concat(results, ignore_index=True)
out_df.to_csv(OUTPUT_PATH, index=False)
print(f"Backtest ML disaggregation results saved to {OUTPUT_PATH}")
print(out_df.head()) 