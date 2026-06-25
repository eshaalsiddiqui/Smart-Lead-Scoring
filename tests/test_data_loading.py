"""Regression test for a pandas footgun: pd.read_csv's default na_values
list includes the literal string "NA", which silently nulled out every
lead whose region is North America (region code "NA") when loaded the
naive way."""

import pandas as pd

from api.enhanced_main import load_leads_csv

DATA_PATH = "data/generated_leads.csv"


def test_naive_read_csv_corrupts_na_region():
    naive = pd.read_csv(DATA_PATH)
    assert naive["region"].isna().any(), (
        "expected the naive read to demonstrate the bug; if this starts "
        "failing, pandas' default NA handling may have changed upstream"
    )


def test_load_leads_csv_preserves_na_region():
    df = load_leads_csv(DATA_PATH)
    assert not df["region"].isna().any()
    assert "NA" in df["region"].unique()
