# Poland Gas Trade Disaggregation

## Project Summary

This project reconstructs the country-level breakdown of Poland's 2023 natural gas imports, which are reported as aggregated regions in Eurostat data. It provides a baseline disaggregation using historical import patterns, robust data cleaning, and clear visualizations. The codebase is structured for easy extension to machine learning models and further validation.

## Motivation

In 2023, Poland reported many of its natural gas imports as coming from aggregated regions (e.g., "Other European countries") rather than individual countries, making it difficult to analyze trade flows. This project aims to disaggregate these flows using historical data and predictive modeling.

## Approach

1. **Data Cleaning & Preparation**: Load and clean Eurostat gas trade data, filter for Poland and relevant units/products, and identify aggregated vs. disaggregated partners.
2. **Mapping**: Assign countries to aggregates using region logic and user review, ensuring no country is in more than one aggregate.
3. **Baseline Disaggregation**: Use historical country shares to estimate the 2023 breakdown for each aggregate, ensuring the sum matches the reported total.
4. **Visualization**: Visualize the baseline results and compare with previous years to check plausibility and highlight changes in trade structure.

## Next Steps / ML Plan

- **Feature Engineering**: Add features such as year, product, country, lagged values, and geopolitical event flags (e.g., post-invasion).
- **Machine Learning Modeling**: Train regression or classification models (e.g., Random Forest, XGBoost) to predict country shares within each aggregate, using historical data.
- **Validation**: Backtest the ML model on years before 2023 (masking country-level data, aggregating, and checking if the model can recover the true split). Compare with partner country export data if available.
- **Refinement**: Iterate on features, mapping, and model selection to improve accuracy and robustness.
- **Documentation & Reproducibility**: Ensure all steps are well-documented and reproducible for future research or policy analysis.

## Repository Structure

- `src/` — Data processing, mapping, modeling, and visualization scripts
- `data/` — Raw and processed data (ignored by git)
- `README.md` — Project summary and plan
- `.gitignore` — Ignore data, logs, and Python artifacts

## How to Run

1. Place the Eurostat CSV in the `data/` folder.
2. Run the scripts in `src/` in order: data cleaning, mapping, baseline disaggregation, and visualization.
3. Review the output plots and logs for results and validation.


