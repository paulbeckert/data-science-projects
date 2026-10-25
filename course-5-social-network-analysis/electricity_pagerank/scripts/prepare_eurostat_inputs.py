"""Builds the trade and generation files for network_pagerank_analysis.py from Eurostat downloads.

Trade: the gross flow from one country to another is what the importer reports in nrg_ti_eh
(electricity imports by partner). When the importer doesn't report to Eurostat, for example
Switzerland or the United Kingdom, the exporter's figure from nrg_te_eh (exports by partner)
is used instead. The trade file holds the net flow of each pair, in the direction it goes.

Generation: gross electricity production per country from nrg_cb_e.

Countries are ISO 2 letter codes as Eurostat uses them (Greece is EL). Eurostat
aggregates like EU27_2020 and partner groups like EUR_OTH are dropped.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
YEAR = 2023


def load_flows(path: Path, reporter_role: str) -> pd.Series:
    """Gross flows in GWh indexed by (exporter, importer). reporter_role says whether the reporting country is the importer or the exporter."""
    df = pd.read_csv(path, low_memory=False)
    df = df[
        (df["siec"] == "E7000")
        & (df["unit"] == "GWH")
        & (df["TIME_PERIOD"] == YEAR)
        & (df["geo"].str.len() == 2)
        & (df["partner"].str.len() == 2)
        & (df["OBS_VALUE"] > 0)
    ]
    partner_role = "exporter" if reporter_role == "importer" else "importer"
    df = df.rename(columns={"geo": reporter_role, "partner": partner_role})
    return df.set_index(["exporter", "importer"])["OBS_VALUE"]


def net_flows(gross: pd.Series) -> pd.DataFrame:
    reverse = gross.copy()
    reverse.index = reverse.index.swaplevel().set_names(["exporter", "importer"])
    net = gross.sub(reverse, fill_value=0)
    net = net[net > 0].rename("flow_gwh").reset_index()
    return net.sort_values(["exporter", "importer"])


def load_generation(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df = df[
        (df["nrg_bal"] == "GEP")
        & (df["siec"] == "E7000")
        & (df["unit"] == "GWH")
        & (df["TIME_PERIOD"] == YEAR)
        & (df["geo"].str.len() == 2)
    ]
    return df.rename(columns={"geo": "country", "OBS_VALUE": "generation_gwh"})[["country", "generation_gwh"]]


def main() -> None:
    imports = load_flows(DATA_DIR / "estat_nrg_ti_eh_en.csv", reporter_role="importer")
    exports = load_flows(DATA_DIR / "estat_nrg_te_eh_en.csv", reporter_role="exporter")
    trade = net_flows(imports.combine_first(exports))
    trade.to_csv(DATA_DIR / f"electricity_trade_{YEAR}.csv", index=False)
    print(f"Saved {len(trade)} net flows to {DATA_DIR / f'electricity_trade_{YEAR}.csv'}")

    generation = load_generation(DATA_DIR / "estat_nrg_cb_e_en.csv")
    generation.to_csv(DATA_DIR / f"electricity_generation_{YEAR}.csv", index=False)
    print(f"Saved generation for {len(generation)} countries to {DATA_DIR / f'electricity_generation_{YEAR}.csv'}")


if __name__ == "__main__":
    main()
