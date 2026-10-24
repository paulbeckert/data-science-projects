# PageRank of the European electricity trade network

Builds a directed, weighted graph of cross-border electricity flows and ranks countries by PageRank. A country ranks high when a lot of electricity flows into it from countries that rank high themselves. You can optionally add domestic generation to compare network position with production size.

## Data

No data is included. The script expects:

- a trade file with the columns `exporter`, `importer` and `flow_gwh` (net annual flow from exporter to importer)
- optionally a generation file with the columns `country` and `generation_gwh`

## How to run

```bash
pip install pandas networkx matplotlib adjustText
cd scripts
python network_pagerank_analysis.py --trade-file ../data/electricity_trade_2023.csv
```
