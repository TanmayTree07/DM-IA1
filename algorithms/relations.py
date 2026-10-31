"""The temperature-similarity relation and tests for its properties.

Set:       X = the selected regions
Relation:  A R B  <=>  |temperature(A) - temperature(B)| <= tolerance

R is stored as a set of ordered pairs (A, B). The three properties are
*tested* against that set - they are never assumed.

* Reflexive:  for every A in X, (A, A) is in R
* Symmetric:  whenever (A, B) is in R, (B, A) is in R
* Transitive: whenever (A, B) and (B, C) are in R, (A, C) is in R
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Sequence, Set, Tuple

Pair = Tuple[str, str]

# Tiny slack so that 36.4 - 34.9 (= 1.5000000000000036 in floating point) still
# counts as "within a tolerance of 1.5".
EPSILON = 1e-9


def are_similar(temp_a: float, temp_b: float, tolerance: float) -> bool:
    """|temp_a - temp_b| <= tolerance."""
    return abs(temp_a - temp_b) <= tolerance + EPSILON


def build_similarity_relation(temps: Mapping[str, float], tolerance: float) -> Set[Pair]:
    """All ordered pairs (A, B), including (A, A), with A R B."""
    regions = list(temps)
    return {
        (a, b)
        for a in regions
        for b in regions
        if are_similar(temps[a], temps[b], tolerance)
    }


def find_reflexivity_violation(elements: Sequence[str], relation: Set[Pair]) -> Optional[str]:
    """Return an element A with (A, A) not in R, or None if R is reflexive."""
    for a in elements:
        if (a, a) not in relation:
            return a
    return None


def find_symmetry_violation(relation: Set[Pair]) -> Optional[Pair]:
    """Return a pair (A, B) in R whose reverse (B, A) is missing, or None."""
    for a, b in sorted(relation):
        if (b, a) not in relation:
            return (a, b)
    return None


def find_transitivity_violation(
    elements: Sequence[str], relation: Set[Pair]
) -> Optional[Tuple[str, str, str]]:
    """Return (A, B, C) with A R B and B R C but NOT A R C, or None."""
    for a in elements:
        for b in elements:
            if (a, b) not in relation:
                continue
            for c in elements:
                if (b, c) in relation and (a, c) not in relation:
                    return (a, b, c)
    return None


def is_reflexive(elements: Sequence[str], relation: Set[Pair]) -> bool:
    return find_reflexivity_violation(elements, relation) is None


def is_symmetric(relation: Set[Pair]) -> bool:
    return find_symmetry_violation(relation) is None


def is_transitive(elements: Sequence[str], relation: Set[Pair]) -> bool:
    return find_transitivity_violation(elements, relation) is None


@dataclass(frozen=True)
class RelationAnalysis:
    reflexive: bool
    symmetric: bool
    transitive: bool
    reflexivity_violation: Optional[str]
    symmetry_violation: Optional[Pair]
    transitivity_violation: Optional[Tuple[str, str, str]]

    @property
    def is_equivalence_relation(self) -> bool:
        return self.reflexive and self.symmetric and self.transitive


def analyze_relation(elements: Sequence[str], relation: Set[Pair]) -> RelationAnalysis:
    """Test all three properties and keep a counterexample for each failure."""
    reflexivity = find_reflexivity_violation(elements, relation)
    symmetry = find_symmetry_violation(relation)
    transitivity = find_transitivity_violation(elements, relation)
    return RelationAnalysis(
        reflexive=reflexivity is None,
        symmetric=symmetry is None,
        transitive=transitivity is None,
        reflexivity_violation=reflexivity,
        symmetry_violation=symmetry,
        transitivity_violation=transitivity,
    )
