"""The pigeonhole principle applied to regions and temperature bins.

Pigeons = the selected regions, pigeonholes = equal-width temperature bins
that together cover [lowest selected temperature, highest selected temperature].

* Basic pigeonhole principle: if n items are placed in k boxes and n > k,
  at least one box holds two or more items.
* Generalised form: some box holds at least ceil(n / k) items.

The generalised bound is a guaranteed LOWER bound. The largest bin you actually
observe can be bigger - it is only ever >= the bound.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional


def guaranteed_minimum(num_items: int, num_boxes: int) -> int:
    """ceil(num_items / num_boxes) using integer arithmetic."""
    if num_boxes <= 0:
        raise ValueError("The number of boxes must be at least 1")
    if num_items < 0:
        raise ValueError("The number of items cannot be negative")
    return -(-num_items // num_boxes)


def bin_edges(low: float, high: float, num_bins: int) -> List[float]:
    """num_bins + 1 equally spaced edges from low to high."""
    if num_bins <= 0:
        raise ValueError("The number of bins must be at least 1")
    width = (high - low) / num_bins
    return [low + i * width for i in range(num_bins)] + [high]


def bin_index(value: float, low: float, high: float, num_bins: int) -> int:
    """Bin number (0-based) for a value. Bins are [lo, hi) except the last, which includes `high`."""
    if high <= low:
        return 0
    index = int((value - low) / (high - low) * num_bins)
    return min(max(index, 0), num_bins - 1)


def assign_to_bins(temps: Mapping[str, float], num_bins: int) -> Dict[int, List[str]]:
    """Place each region into a bin; every bin index appears, possibly with an empty list."""
    if num_bins <= 0:
        raise ValueError("The number of bins must be at least 1")
    bins: Dict[int, List[str]] = {i: [] for i in range(num_bins)}
    if not temps:
        return bins
    low, high = min(temps.values()), max(temps.values())
    for region in sorted(temps):
        bins[bin_index(temps[region], low, high, num_bins)].append(region)
    return bins


@dataclass(frozen=True)
class PigeonholeResult:
    valid: bool                      # False when the inputs make the question meaningless
    message: str                     # plain-language note about the situation
    num_items: int = 0
    num_bins: int = 0
    basic_principle_applies: bool = False   # n > k
    guaranteed_min: Optional[int] = None    # ceil(n / k)
    bins: Dict[int, List[str]] = field(default_factory=dict)
    edges: List[float] = field(default_factory=list)
    max_count: int = 0
    largest_bins: List[int] = field(default_factory=list)

    @property
    def counts(self) -> Dict[int, int]:
        return {i: len(members) for i, members in self.bins.items()}


def analyze_pigeonhole(temps: Mapping[str, float], num_bins: int) -> PigeonholeResult:
    """Assign regions to bins and compare the observed counts with the guarantee."""
    n = len(temps)
    if num_bins <= 0:
        return PigeonholeResult(False, "The number of bins must be at least 1, so the pigeonhole principle cannot be applied.",
                                num_items=n, num_bins=max(num_bins, 0))
    if n == 0:
        return PigeonholeResult(False, "There are no regions to place into bins, so the pigeonhole principle has nothing to say.",
                                num_items=0, num_bins=num_bins)

    bins = assign_to_bins(temps, num_bins)
    counts = {i: len(members) for i, members in bins.items()}
    max_count = max(counts.values())
    guarantee = guaranteed_minimum(n, num_bins)
    applies = n > num_bins
    if applies:
        message = (f"{n} regions > {num_bins} bins, so the pigeonhole principle guarantees that at "
                   f"least one bin holds {guarantee} or more regions.")
    else:
        message = (f"{n} regions <= {num_bins} bins, so the basic pigeonhole principle does NOT force "
                   f"two regions into the same bin. (The general bound ceil({n}/{num_bins}) = {guarantee} "
                   f"still holds, but it is trivial.)")
    return PigeonholeResult(
        valid=True,
        message=message,
        num_items=n,
        num_bins=num_bins,
        basic_principle_applies=applies,
        guaranteed_min=guarantee,
        bins=bins,
        edges=bin_edges(min(temps.values()), max(temps.values()), num_bins),
        max_count=max_count,
        largest_bins=[i for i, c in counts.items() if c == max_count],
    )
