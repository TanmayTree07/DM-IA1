"""Loading, validating and filtering the temperature dataset.

Required CSV schema:  date,region,temperature_celsius
    date                  YYYY-MM-DD
    region                non-empty text
    temperature_celsius   a number (deg C)

Invalid data is REPORTED as an error, never silently repaired, so that the
dashboard cannot present misleading results.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ["date", "region", "temperature_celsius"]
DATE_FORMAT = "%Y-%m-%d"
SAMPLE_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_temperatures.csv"
PLAUSIBLE_RANGE_C = (-60.0, 60.0)


@dataclass
class ValidationResult:
    df: Optional[pd.DataFrame] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.df is not None and not self.errors


def _file_lines(mask: pd.Series, limit: int = 5) -> str:
    """Describe the offending rows using CSV line numbers (header = line 1)."""
    lines = [str(i + 2) for i in list(mask[mask].index[:limit])]
    extra = int(mask.sum()) - len(lines)
    text = ", ".join(lines)
    return text + (f" (and {extra} more)" if extra > 0 else "")


def _text(series: pd.Series) -> pd.Series:
    """Series of stripped strings with missing values turned into ''."""
    return series.where(series.notna(), "").astype(str).str.strip()


def validate_dataframe(raw: Optional[pd.DataFrame]) -> ValidationResult:
    """Check a raw table against the schema and return a cleaned copy if it is valid."""
    result = ValidationResult()
    if raw is None or len(raw.columns) == 0 or len(raw) == 0:
        result.errors.append(
            "The file has no data rows. Expected a header line "
            "'date,region,temperature_celsius' followed by observations."
        )
        return result

    table = raw.copy()
    table.columns = [str(c).strip().lower() for c in table.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in table.columns]
    if missing:
        result.errors.append(
            f"Missing required column(s): {', '.join(missing)}. "
            f"Found: {', '.join(table.columns)}. Required: {', '.join(REQUIRED_COLUMNS)}."
        )
        return result

    dates = pd.to_datetime(_text(table["date"]), format=DATE_FORMAT, errors="coerce")
    regions = _text(table["region"])
    temps = pd.to_numeric(_text(table["temperature_celsius"]), errors="coerce")

    bad_date = dates.isna()
    bad_region = regions == ""
    bad_temp = temps.isna() | np.isinf(temps)

    if bad_date.any():
        result.errors.append(
            f"{int(bad_date.sum())} row(s) have a missing or invalid date "
            f"(expected YYYY-MM-DD). File line(s): {_file_lines(bad_date)}."
        )
    if bad_region.any():
        result.errors.append(
            f"{int(bad_region.sum())} row(s) have no region name. File line(s): {_file_lines(bad_region)}."
        )
    if bad_temp.any():
        result.errors.append(
            f"{int(bad_temp.sum())} row(s) have a missing or non-numeric temperature_celsius. "
            f"File line(s): {_file_lines(bad_temp)}."
        )

    usable = ~(bad_date | bad_region | bad_temp)
    keys = pd.DataFrame({"date": dates, "region": regions})[usable]
    duplicated = pd.Series(False, index=table.index)
    duplicated.loc[keys.index] = keys.duplicated(keep=False)
    if duplicated.any():
        result.errors.append(
            f"{int(duplicated.sum())} row(s) repeat the same region and date. "
            f"Each region may appear only once per date. File line(s): {_file_lines(duplicated)}."
        )

    if result.errors:
        return result

    clean = pd.DataFrame({"date": dates, "region": regions, "temperature_celsius": temps.astype(float)})
    clean = clean.sort_values(["date", "region"]).reset_index(drop=True)

    n_regions = clean["region"].nunique()
    n_dates = clean["date"].nunique()
    if n_regions == 1:
        result.warnings.append(
            "The dataset contains only one region. The relationship graph and the algorithms "
            "need at least two regions to show anything interesting."
        )
    if n_dates == 1:
        result.warnings.append("The dataset contains only one date, so the time-series chart has little to show.")
    counts = clean.groupby("region").size()
    short = counts[counts < n_dates]
    if len(short) > 0:
        names = ", ".join(short.index[:5]) + (" ..." if len(short) > 5 else "")
        result.warnings.append(
            f"{len(short)} region(s) have missing observations (fewer than the {n_dates} distinct dates "
            f"in the file): {names}. On a date where a region has no observation it is left out of the analysis."
        )
    low, high = PLAUSIBLE_RANGE_C
    odd = clean[(clean["temperature_celsius"] < low) | (clean["temperature_celsius"] > high)]
    if len(odd) > 0:
        result.warnings.append(
            f"{len(odd)} temperature value(s) lie outside {low:.0f} to {high:.0f} deg C. "
            "Check that the column really is in degrees Celsius."
        )

    result.df = clean
    return result


def load_csv_bytes(data: bytes) -> ValidationResult:
    """Parse and validate CSV content (for example from an uploaded file)."""
    if not data or not data.strip():
        return ValidationResult(errors=["The file is empty."])
    try:
        raw = pd.read_csv(io.BytesIO(data), dtype=str, keep_default_na=False,
                          encoding="utf-8-sig", skipinitialspace=True)
    except pd.errors.EmptyDataError:
        return ValidationResult(errors=["The file is empty."])
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        return ValidationResult(errors=[f"The file could not be read as a CSV: {exc}"])
    return validate_dataframe(raw)


def load_sample_data(path: Path = SAMPLE_PATH) -> ValidationResult:
    """Load the built-in synthetic dataset."""
    path = Path(path)
    if not path.exists():
        return ValidationResult(errors=[
            f"Sample dataset not found at {path}. Create it with: python scripts/generate_sample_data.py"
        ])
    return load_csv_bytes(path.read_bytes())


def list_regions(df: pd.DataFrame) -> List[str]:
    return sorted(df["region"].unique())


def get_date_bounds(df: pd.DataFrame) -> Tuple[pd.Timestamp, pd.Timestamp]:
    return df["date"].min(), df["date"].max()


def representative_temperatures(
    df: pd.DataFrame,
    regions: Sequence[str],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> Tuple[Dict[str, float], List[str]]:
    """One temperature per region for the chosen period.

    Definition: the MEAN of the region's daily observations from `start` to
    `end` (inclusive), rounded to 2 decimals. For a single date this is simply
    that day's observation. Regions with no observation in the period are
    returned in the second list instead of being given an invented value.
    """
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    window = df[(df["date"] >= start) & (df["date"] <= end) & (df["region"].isin(regions))]
    means = window.groupby("region")["temperature_celsius"].mean().round(2)
    temps = {r: float(means[r]) for r in sorted(regions) if r in means.index}
    missing = [r for r in sorted(regions) if r not in means.index]
    return temps, missing
