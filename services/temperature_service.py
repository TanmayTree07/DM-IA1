"""Temperature categories (a function), summary tables and descriptive statistics.

Category function  f : regions -> {Normal, Moderate, High}

    f(x) = High      if temperature(x) >= high_min
           Moderate  if moderate_min <= temperature(x) < high_min
           Normal    otherwise

The boundaries are adjustable teaching values. They are NOT an official
heatwave classification.
"""

from __future__ import annotations

from typing import Dict, Mapping, Optional

import numpy as np
import pandas as pd

from algorithms.logic import evaluate_proposition

CATEGORIES = ("Normal", "Moderate", "High")
DEFAULT_MODERATE_MIN = 35.0
DEFAULT_HIGH_MIN = 40.0


def validate_boundaries(moderate_min: float, high_min: float) -> Optional[str]:
    """Return an error message when the boundaries are unusable, else None."""
    if moderate_min >= high_min:
        return "The 'Moderate' boundary must be lower than the 'High' boundary."
    return None


def categorize_temperature(temperature: float, moderate_min: float, high_min: float) -> str:
    if temperature >= high_min:
        return "High"
    if temperature >= moderate_min:
        return "Moderate"
    return "Normal"


def category_counts(temps: Mapping[str, float], moderate_min: float, high_min: float) -> Dict[str, int]:
    counts = {name: 0 for name in CATEGORIES}
    for value in temps.values():
        counts[categorize_temperature(value, moderate_min, high_min)] += 1
    return counts


def category_table(temps: Mapping[str, float], threshold: float,
                   moderate_min: float, high_min: float) -> pd.DataFrame:
    """One row per region: temperature, category f(x) and the truth value of P(x)."""
    truth = evaluate_proposition(temps, threshold)
    return pd.DataFrame({
        "Region": list(temps),
        "Temperature (°C)": [temps[r] for r in temps],
        "Category": [categorize_temperature(temps[r], moderate_min, high_min) for r in temps],
        "P(x): temp ≥ threshold": [truth[r] for r in temps],
    })


def describe_temperatures(temps: Mapping[str, float]) -> Dict[str, object]:
    """Descriptive statistics computed from the selected temperatures."""
    if not temps:
        return {"count": 0}
    values = np.array(list(temps.values()), dtype=float)
    hottest = max(temps, key=temps.get)
    coolest = min(temps, key=temps.get)
    return {
        "count": len(values),
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "std": float(values.std(ddof=1)) if len(values) > 1 else None,
        "min": float(values.min()),
        "max": float(values.max()),
        "range": float(values.max() - values.min()),
        "hottest": hottest,
        "coolest": coolest,
    }


def statistics_table(stats: Mapping[str, object]) -> pd.DataFrame:
    """Two-column table (Statistic, Value) for display."""
    if not stats or stats.get("count", 0) == 0:
        return pd.DataFrame({"Statistic": [], "Value": []})

    def fmt(x):
        return "n/a" if x is None else f"{x:.2f}"

    rows = [
        ("Regions", str(stats["count"])),
        ("Mean (°C)", fmt(stats["mean"])),
        ("Median (°C)", fmt(stats["median"])),
        ("Std. deviation (°C)", fmt(stats["std"])),
        ("Minimum (°C)", f"{fmt(stats['min'])}  ({stats['coolest']})"),
        ("Maximum (°C)", f"{fmt(stats['max'])}  ({stats['hottest']})"),
        ("Range (°C)", fmt(stats["range"])),
    ]
    return pd.DataFrame(rows, columns=["Statistic", "Value"])
