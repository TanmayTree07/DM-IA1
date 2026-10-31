import pandas as pd
import pytest

from services import data_service as ds

HEADER = "date,region,temperature_celsius\n"


def load(text: str):
    return ds.load_csv_bytes(text.encode("utf-8"))


def test_valid_csv_is_accepted():
    r = load(HEADER + "2026-01-01,A,30.5\n2026-01-01,B,31.0\n2026-01-02,A,30.9\n2026-01-02,B,31.2\n")
    assert r.ok and not r.errors and not r.warnings
    assert list(r.df.columns) == ds.REQUIRED_COLUMNS
    assert len(r.df) == 4


def test_empty_file():
    assert not load("").ok
    assert "empty" in load("").errors[0].lower()


def test_header_only_file():
    r = load(HEADER)
    assert not r.ok and "no data rows" in r.errors[0]


def test_missing_column():
    r = load("date,region\n2026-01-01,A\n")
    assert not r.ok
    assert "temperature_celsius" in r.errors[0]


def test_invalid_date():
    r = load(HEADER + "2026-13-45,A,30\n2026-01-02,A,31\n")
    assert not r.ok
    assert any("invalid date" in e for e in r.errors)


def test_non_numeric_temperature():
    r = load(HEADER + "2026-01-01,A,hot\n")
    assert not r.ok
    assert any("non-numeric" in e for e in r.errors)


def test_missing_region_name():
    r = load(HEADER + "2026-01-01,,30\n")
    assert not r.ok
    assert any("no region name" in e for e in r.errors)


def test_duplicate_region_date():
    r = load(HEADER + "2026-01-01,A,30\n2026-01-01,A,31\n")
    assert not r.ok
    assert any("repeat the same region and date" in e for e in r.errors)


def test_all_problems_are_reported_together():
    r = load(HEADER + "bad,A,30\n2026-01-01,,31\n2026-01-02,B,x\n")
    assert len(r.errors) == 3


def test_single_region_gives_warning_not_error():
    r = load(HEADER + "2026-01-01,A,30\n2026-01-02,A,31\n")
    assert r.ok
    assert any("only one region" in w for w in r.warnings)


def test_missing_observations_give_warning():
    r = load(HEADER + "2026-01-01,A,30\n2026-01-01,B,31\n2026-01-02,A,30\n")
    assert r.ok
    assert any("missing observations" in w and "B" in w for w in r.warnings)


def test_implausible_temperature_gives_warning():
    r = load(HEADER + "2026-01-01,A,300\n2026-01-01,B,30\n")
    assert r.ok and any("outside" in w for w in r.warnings)


def test_column_names_are_case_insensitive_and_whitespace_tolerant():
    r = load(" Date , Region ,Temperature_Celsius\n2026-01-01, A ,30\n")
    assert r.ok and r.df["region"].tolist() == ["A"]


def test_representative_temperature_for_single_date_and_range():
    df = load(HEADER + "2026-01-01,A,30\n2026-01-02,A,32\n2026-01-03,A,40\n"
                       "2026-01-01,B,20\n2026-01-02,B,22\n2026-01-03,B,24\n").df
    day = pd.Timestamp("2026-01-02")
    assert ds.representative_temperatures(df, ["A", "B"], day, day)[0] == {"A": 32.0, "B": 22.0}
    temps, missing = ds.representative_temperatures(df, ["A", "B"], pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-03"))
    assert temps == {"A": 34.0, "B": 22.0} and missing == []


def test_region_without_data_in_period_is_reported_missing():
    df = load(HEADER + "2026-01-01,A,30\n2026-01-02,B,31\n").df
    day = pd.Timestamp("2026-01-01")
    temps, missing = ds.representative_temperatures(df, ["A", "B"], day, day)
    assert temps == {"A": 30.0} and missing == ["B"]


def test_built_in_sample_dataset_meets_the_spec():
    r = ds.load_sample_data()
    assert r.ok, r.errors
    df = r.df
    assert 10 <= df["region"].nunique() <= 12
    days = df["date"].drop_duplicates().sort_values()
    assert len(days) >= 90
    assert (days.diff().dropna() == pd.Timedelta(days=1)).all()       # consecutive days
    assert (df.groupby("region").size() == len(days)).all()           # every region, every day
    assert not df.duplicated(["date", "region"]).any()
    assert df["temperature_celsius"].between(-10, 60).all()
    assert not r.warnings


def test_sample_data_has_variety_for_the_demo():
    df = ds.load_sample_data().df
    last = df[df["date"] == df["date"].max()]["temperature_celsius"]
    assert last.max() - last.min() > 8
