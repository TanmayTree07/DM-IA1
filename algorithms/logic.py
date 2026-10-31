"""Propositional logic and quantifiers over region temperatures.

Domain of discourse: the set X of regions currently selected.
Proposition:         P(x)  =  temperature(x) >= threshold

Quantifier convention
---------------------
Mathematically, over an EMPTY domain "there exists" is False and "for all" is
vacuously True. Showing "all regions are above the threshold: True" when there
are no regions at all would be misleading, so the helpers below return None
("not defined / no regions") for an empty domain instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Mapping, Optional, TypeVar

T = TypeVar("T")


def proposition(temperature: float, threshold: float) -> bool:
    """P(x): is the temperature at least the threshold? (>= so equality counts)."""
    return temperature >= threshold


def evaluate_proposition(temps: Mapping[str, float], threshold: float) -> Dict[str, bool]:
    """Truth value of P(x) for every region."""
    return {region: proposition(value, threshold) for region, value in temps.items()}


def exists(predicate: Callable[[T], bool], domain: Iterable[T]) -> Optional[bool]:
    """Existential quantifier: there is an x in the domain with predicate(x).

    Returns None for an empty domain (see module docstring).
    """
    items = list(domain)
    if not items:
        return None
    return any(predicate(item) for item in items)


def for_all(predicate: Callable[[T], bool], domain: Iterable[T]) -> Optional[bool]:
    """Universal quantifier: predicate(x) holds for every x in the domain.

    Returns None for an empty domain (see module docstring).
    """
    items = list(domain)
    if not items:
        return None
    return all(predicate(item) for item in items)


@dataclass(frozen=True)
class LogicSummary:
    threshold: float
    truth_values: Dict[str, bool]
    satisfying: List[str]        # regions where P(x) is True
    not_satisfying: List[str]    # regions where P(x) is False
    count: int                   # number of regions where P(x) is True
    total: int                   # size of the domain
    exists_above: Optional[bool]  # there exists x : P(x)
    all_above: Optional[bool]     # for all x : P(x)
    all_below: Optional[bool]     # for all x : not P(x)  (every temp < threshold)

    @property
    def is_empty(self) -> bool:
        return self.total == 0


def analyze_logic(temps: Mapping[str, float], threshold: float) -> LogicSummary:
    """Evaluate P(x) and the three quantified statements on the given data."""
    truth = evaluate_proposition(temps, threshold)
    regions = list(truth)
    satisfying = [r for r in regions if truth[r]]
    not_satisfying = [r for r in regions if not truth[r]]
    return LogicSummary(
        threshold=threshold,
        truth_values=truth,
        satisfying=satisfying,
        not_satisfying=not_satisfying,
        count=len(satisfying),
        total=len(regions),
        exists_above=exists(lambda r: truth[r], regions),
        all_above=for_all(lambda r: truth[r], regions),
        all_below=for_all(lambda r: not truth[r], regions),
    )
