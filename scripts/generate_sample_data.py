"""Generate the SYNTHETIC sample dataset used by HeatWave Explorer.

Run from the project root:

    python scripts/generate_sample_data.py

The output (data/sample_temperatures.csv) is *not* real weather data. The
region names are fictional and every number is produced by a simple formula
plus pseudo-random noise with a fixed seed, so the file can be regenerated.

Model for one region on day d (d = 0 ... NUM_DAYS - 1):

    T(d) = base + warming * d                 gradual seasonal warming
           + 1.2 * sin(2*pi*(d + phase)/11)   short weather swings
           + sensitivity * heat_events(d)     shared hot spells
           + local_event(d)                   optional region-specific event
           + noise(d)                         small AR(1) day-to-day noise
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from pathlib import Path
from typing import List, Tuple

import numpy as np

SEED = 2026
START_DATE = date(2026, 3, 1)
NUM_DAYS = 90
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_temperatures.csv"

# region: (temperature on day 0 in deg C, warming per day, heat sensitivity, phase)
REGIONS = {
    "Northfield": (25.5, 0.030, 0.6, 0),
    "Hillview": (26.8, 0.033, 0.7, 3),
    "Lakeside": (28.2, 0.038, 0.8, 5),
    "Meadowbrook": (29.5, 0.040, 0.9, 8),
    "Greenfield": (30.4, 0.042, 0.9, 2),
    "Riverdale": (31.8, 0.046, 1.0, 6),
    "Coastview": (32.6, 0.040, 0.8, 10),
    "Central Park": (33.4, 0.050, 1.0, 4),
    "Westhaven": (34.5, 0.054, 1.1, 7),
    "Eastvale": (35.2, 0.058, 1.1, 1),
    "Sunnydale": (36.4, 0.062, 1.2, 9),
    "Southridge": (37.2, 0.066, 1.3, 12),
}

# Shared hot spells: (first day, length in days, peak extra deg C)
HEAT_EVENTS = [(31, 6, 3.0), (58, 7, 3.8), (78, 8, 4.5)]

# Region-specific events (negative = cooling, e.g. a sea breeze)
LOCAL_EVENTS = {
    "Eastvale": (45, 5, 3.0),
    "Coastview": (66, 4, -2.0),
    "Hillview": (20, 6, -1.5),
    "Southridge": (10, 5, 2.5),
}


def _bump(day: int, start: int, length: int, peak: float) -> float:
    """Smooth half-sine bump of height `peak` lasting `length` days."""
    if start <= day < start + length:
        return peak * math.sin(math.pi * (day - start + 0.5) / length)
    return 0.0


def generate_rows() -> List[Tuple[str, str, float]]:
    """Return (date, region, temperature) rows, ordered by date then region."""
    rng = np.random.default_rng(SEED)
    series = {}
    for name, (base, warming, sensitivity, phase) in REGIONS.items():
        noise = 0.0
        values = []
        for d in range(NUM_DAYS):
            noise = 0.6 * noise + rng.normal(0.0, 0.7)
            value = base + warming * d
            value += 1.2 * math.sin(2 * math.pi * (d + phase) / 11)
            value += sensitivity * sum(_bump(d, *event) for event in HEAT_EVENTS)
            if name in LOCAL_EVENTS:
                value += _bump(d, *LOCAL_EVENTS[name])
            values.append(round(value + noise, 1))
        series[name] = values

    rows = []
    for d in range(NUM_DAYS):
        day = (START_DATE + timedelta(days=d)).isoformat()
        for name in REGIONS:
            rows.append((day, name, series[name][d]))
    return rows


def write_csv(path: Path = OUTPUT_PATH) -> int:
    rows = generate_rows()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write manually with "\n" so the file is byte-identical on every OS.
    with open(path, "w", newline="", encoding="utf-8") as handle:
        handle.write("date,region,temperature_celsius\n")
        for day, region, temperature in rows:
            handle.write(f"{day},{region},{temperature:.1f}\n")
    return len(rows)


if __name__ == "__main__":
    count = write_csv()
    print(f"Wrote {count} synthetic observations to {OUTPUT_PATH}")
