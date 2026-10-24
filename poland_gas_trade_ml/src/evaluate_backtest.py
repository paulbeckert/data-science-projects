import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import os

BACKTEST_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ml_backtest_disaggregation.csv')

def main():
    df = pd.read_csv(BACKTEST_PATH)
    print("=== Overall Metrics ===")
    mae_share = mean_absolute_error(df['true_share'], df['predicted_share_normalized'])
    rmse_share = np.sqrt(mean_squared_error(df['true_share'], df['predicted_share_normalized']))
    r2_share = r2_score(df['true_share'], df['predicted_share_normalized'])
    mae_value = mean_absolute_error(df['true_value'], df['predicted_value_normalized'])
    rmse_value = np.sqrt(mean_squared_error(df['true_value'], df['predicted_value_normalized']))
    r2_value = r2_score(df['true_value'], df['predicted_value_normalized'])
    print(f"MAE (share): {mae_share:.4f}")
    print(f"RMSE (share): {rmse_share:.4f}")
    print(f"R2 (share): {r2_share:.4f}")
    print(f"MAE (value): {mae_value:.2f} MIO_M3")
    print(f"RMSE (value): {rmse_value:.2f} MIO_M3")
    print(f"R2 (value): {r2_value:.4f}")

    print("\n=== Metrics by Aggregate ===")
    for agg in df['aggregate'].unique():
        sub = df[df['aggregate'] == agg]
        mae_s = mean_absolute_error(sub['true_share'], sub['predicted_share_normalized'])
        rmse_s = np.sqrt(mean_squared_error(sub['true_share'], sub['predicted_share_normalized']))
        r2_s = r2_score(sub['true_share'], sub['predicted_share_normalized'])
        mae_v = mean_absolute_error(sub['true_value'], sub['predicted_value_normalized'])
        rmse_v = np.sqrt(mean_squared_error(sub['true_value'], sub['predicted_value_normalized']))
        r2_v = r2_score(sub['true_value'], sub['predicted_value_normalized'])
        print(f"Aggregate: {agg}")
        print(f"  MAE (share): {mae_s:.4f}")
        print(f"  RMSE (share): {rmse_s:.4f}")
        print(f"  R2 (share): {r2_s:.4f}")
        print(f"  MAE (value): {mae_v:.2f} MIO_M3")
        print(f"  RMSE (value): {rmse_v:.2f} MIO_M3")
        print(f"  R2 (value): {r2_v:.4f}")

if __name__ == "__main__":
    main() 