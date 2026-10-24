# Semantic search for ecoinvent products

Finds the ecoinvent products that best match a free text query, like "car fuel" or "aluminum sheets". It embeds the product names and descriptions with the `all-MiniLM-L6-v2` sentence transformer and ranks them by cosine similarity to the query.

## Data

The input is the ecoinvent v3.11 database overview, which you can download from the [ecoinvent website](https://ecoinvent.org). The scripts read its "Intermediate Exchanges" sheet. Save it as `data/raw/Database-Overview-for-ecoinvent-v3.11.xlsx`.

## How to run

```bash
pip install -r requirements.txt
cd src
python 01_data_extraction.py
python 02_data_preprocessing.py
python 04_create_user_queries.py
python 05_demo_evaluation.py
```

`notebooks/demo.ipynb` walks through the same steps interactively.
