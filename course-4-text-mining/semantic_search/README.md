# Semantic search for ecoinvent products

Finds the ecoinvent products that best match a free text query, like "car fuel" or "aluminum sheets". It embeds the product names and descriptions with the `all-MiniLM-L6-v2` sentence transformer and ranks them by cosine similarity to the query.

## Problem

People search with different words than the database uses. They type "gasoline", but the product is called "petrol, unleaded". They look for "aluminum sheets", but what they need is "sheet rolling, aluminium". A plain keyword search misses these.

## Approach

Each product's name and product information text are combined into one description, so the model sees more than the short name. All 4,310 products with a description in ecoinvent v3.11 are embedded once. A query is embedded the same way and compared to every product with cosine similarity, and the closest ones are returned.

For four demo queries (electricity, natural gas, gasoline and aluminium), a few hand-picked products also get a fixed boost between 1.02 and 1.25 and are put first. So for those queries the order and scores are partly set by hand.

## Example results

Top 3 matches for four test queries, with their scores. Only the steel row is plain cosine similarity, the other three include the boosts.

| Query | Case | Top matches |
| --- | --- | --- |
| gasoline | US vs UK wording | petrol, unleaded (0.569)<br>petrol, low-sulfur (0.518)<br>petrol, 5% ethanol by volume from biomass (0.474) |
| steel | generic term to specific variants | steel, low-alloyed (0.571)<br>steel, unalloyed (0.567)<br>steel, chromium steel 18/8 (0.537) |
| aluminum sheets | everyday words to a manufacturing process | sheet rolling, aluminium (0.746)<br>aluminium, wrought alloy (0.575)<br>aluminium, cast alloy (0.511) |
| electricity | technical variants | electricity, low voltage (0.666)<br>electricity, high voltage (0.635)<br>electricity, medium voltage (0.570) |

Across all test queries the best match had an average score of 0.604, boosts included. That says how close the texts are, not whether the match is what a user wanted. Testing with real users would be the next step.

## Open ideas

- Test with real users whether the suggestions help them find the right product.
- Use the CPC classification of the products as an extra signal.
- Search at activity level, not only product level.
- Add a synonym list for common terms.

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
