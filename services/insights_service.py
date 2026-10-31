"""Turns algorithm results into plain-language insights for the DM Insights tab.

Everything here is generated from the data and settings passed in - nothing is
hard-coded to the sample dataset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple

import pandas as pd

from algorithms.graph_builder import GraphAnalysis, analyze_graph
from algorithms.logic import LogicSummary, analyze_logic
from algorithms.pigeonhole import PigeonholeResult, analyze_pigeonhole
from algorithms.relations import (
    RelationAnalysis,
    analyze_relation,
    are_similar,
    build_similarity_relation,
)
from services import temperature_service as ts


# ---------------------------------------------------------------- logic / quantifiers
def _join(names: List[str], empty: str = "none") -> str:
    return ", ".join(names) if names else empty


def logic_sentences(summary: LogicSummary) -> List[str]:
    """Beginner-friendly reading of P(x) = temperature(x) >= threshold."""
    if summary.is_empty:
        return ["No regions are selected (or none have data for this period), so P(x) cannot be evaluated."]
    return [
        f"P(x) is true for {summary.count} of {summary.total} region(s): {_join(summary.satisfying)}.",
        f"P(x) is false for: {_join(summary.not_satisfying)}.",
    ]


def quantifier_rows(summary: LogicSummary) -> List[Dict[str, str]]:
    """Rows describing the three quantified statements with evidence from the data."""
    thr = f"{summary.threshold:g}"
    if summary.is_empty:
        return [{
            "Statement": "Any quantified statement",
            "Symbolic": "-",
            "Result": "Undefined",
            "Evidence": "The set of regions is empty. (Mathematically ∀ over an empty set is vacuously true, "
                        "but that would be misleading here, so no verdict is given.)",
        }]
    return [
        {
            "Statement": f"There exists a region with temperature ≥ {thr} °C",
            "Symbolic": "∃x P(x)",
            "Result": str(summary.exists_above),
            "Evidence": (f"Witness(es): {_join(summary.satisfying)}" if summary.exists_above
                         else "No region satisfies P(x)."),
        },
        {
            "Statement": f"Every region has temperature ≥ {thr} °C",
            "Symbolic": "∀x P(x)",
            "Result": str(summary.all_above),
            "Evidence": ("Every region satisfies P(x)." if summary.all_above
                         else f"Counterexample(s): {_join(summary.not_satisfying)}"),
        },
        {
            "Statement": f"Every region has temperature < {thr} °C",
            "Symbolic": "∀x ¬P(x)",
            "Result": str(summary.all_below),
            "Evidence": ("No region satisfies P(x)." if summary.all_below
                         else f"Counterexample(s): {_join(summary.satisfying)}"),
        },
    ]


# ---------------------------------------------------------------- relation
@dataclass
class RelationReport:
    analysis: RelationAnalysis
    regions: List[str]
    examples: List[str]
    summary: str


def explain_pair(temps: Mapping[str, float], a: str, b: str, tolerance: float) -> Tuple[bool, str]:
    """Why does (or doesn't) an edge exist between regions a and b?"""
    if a == b:
        return False, (f"{a} and {b} are the same region. R is reflexive (|t − t| = 0 ≤ {tolerance:g}), "
                       "but a region is not joined to itself by an edge, so the adjacency-matrix diagonal is 0.")
    diff = abs(temps[a] - temps[b])
    similar = are_similar(temps[a], temps[b], tolerance)
    comparison = "≤" if similar else ">"
    verdict = "an edge exists" if similar else "no edge"
    return similar, (f"|{temps[a]:.2f} − {temps[b]:.2f}| = {diff:.2f} {comparison} {tolerance:g}, so {verdict} "
                     f"between {a} and {b}.")


def relation_report(temps: Mapping[str, float], tolerance: float) -> RelationReport:
    """Test reflexive / symmetric / transitive and build examples from the actual data."""
    regions = sorted(temps)
    relation = build_similarity_relation(temps, tolerance)
    analysis = analyze_relation(regions, relation)
    examples: List[str] = []

    if regions:
        a = regions[0]
        examples.append(f"Reflexive: {a} R {a}, because |{temps[a]:.2f} − {temps[a]:.2f}| = 0 ≤ {tolerance:g}.")

    pair = next(((a, b) for (a, b) in sorted(relation) if a != b), None)
    if pair:
        a, b = pair
        d = abs(temps[a] - temps[b])
        examples.append(f"Symmetric: {a} R {b} and {b} R {a}, because |{temps[a]:.2f} − {temps[b]:.2f}| "
                        f"and |{temps[b]:.2f} − {temps[a]:.2f}| both equal {d:.2f} ≤ {tolerance:g}.")
    elif regions:
        examples.append("Symmetric: no two different regions are similar at this tolerance, "
                        "so there is no pair to illustrate it with (the property still holds).")

    if analysis.transitivity_violation:
        a, b, c = analysis.transitivity_violation
        examples.append(
            f"Transitivity FAILS: {a} R {b} (difference {abs(temps[a] - temps[b]):.2f}) and "
            f"{b} R {c} (difference {abs(temps[b] - temps[c]):.2f}) are both within {tolerance:g}, "
            f"but {a} R {c} is false (difference {abs(temps[a] - temps[c]):.2f} > {tolerance:g})."
        )
    else:
        chain = next(((a, b, c) for a in regions for b in regions for c in regions
                      if len({a, b, c}) == 3 and (a, b) in relation and (b, c) in relation), None)
        if chain:
            a, b, c = chain
            examples.append(f"Transitive (no counterexample): {a} R {b} and {b} R {c}, and indeed {a} R {c}.")
        elif regions:
            examples.append("Transitive: no chain A R B, B R C through three different regions exists, "
                            "so no counterexample can exist.")

    if not regions:
        summary = "There are no regions, so there is no relation to analyse."
    elif analysis.is_equivalence_relation:
        summary = ("At this tolerance R is reflexive, symmetric AND transitive, so it is an equivalence relation: "
                   "the regions split into groups where every pair inside a group is similar.")
    else:
        summary = ("R is reflexive and symmetric but NOT transitive, so it is not an equivalence relation. "
                   "Similarity is 'close enough', and closeness does not chain."
                   if analysis.reflexive and analysis.symmetric else
                   "R is missing a property it is normally expected to have - see the counterexamples.")
    return RelationReport(analysis=analysis, regions=regions, examples=examples, summary=summary)


# ---------------------------------------------------------------- components
def component_sentences(analysis: GraphAnalysis) -> List[str]:
    """'Group 1 contains A, B and C ...' generated from the actual graph."""
    sentences = []
    for number, members in enumerate(analysis.components, start=1):
        temps = [analysis.temperatures[m] for m in members]
        if len(members) == 1:
            sentences.append(f"Group {number} contains only {members[0]} ({temps[0]:.1f} °C) - an isolated vertex.")
        else:
            names = ", ".join(members[:-1]) + f" and {members[-1]}"
            sentences.append(f"Group {number} contains {names} "
                             f"({len(members)} regions, {min(temps):.1f}–{max(temps):.1f} °C).")
    return sentences


# ---------------------------------------------------------------- pigeonhole
def bin_labels(result: PigeonholeResult) -> List[str]:
    return [f"Bin {i + 1}: {result.edges[i]:.1f}–{result.edges[i + 1]:.1f} °C" for i in range(result.num_bins)]


def pigeonhole_sentences(result: PigeonholeResult) -> List[str]:
    if not result.valid:
        return [result.message]
    labels = bin_labels(result)
    largest = ", ".join(labels[i] for i in result.largest_bins)
    lines = [
        result.message,
        f"Observed: the fullest bin holds {result.max_count} region(s) ({largest}).",
    ]
    if result.max_count > result.guaranteed_min:
        lines.append(f"The guarantee is only a lower bound ({result.guaranteed_min}); the data happens to be "
                     f"more crowded than that ({result.max_count}).")
    else:
        lines.append(f"Here the observed maximum equals the guaranteed minimum ({result.guaranteed_min}).")
    return lines


# ---------------------------------------------------------------- bundle
@dataclass
class Insights:
    logic: LogicSummary
    logic_text: List[str]
    quantifiers: List[Dict[str, str]]
    category_table: pd.DataFrame
    category_counts: Dict[str, int]
    relation: RelationReport
    pigeonhole: PigeonholeResult
    pigeonhole_text: List[str]
    graph: GraphAnalysis
    components_text: List[str]


def build_insights(
    temps: Mapping[str, float],
    threshold: float,
    tolerance: float,
    moderate_min: float,
    high_min: float,
    num_bins: int,
) -> Insights:
    """Compute every Tab 4 insight from the current selection."""
    summary = analyze_logic(temps, threshold)
    graph = analyze_graph(temps, tolerance)
    pigeon = analyze_pigeonhole(temps, num_bins)
    return Insights(
        logic=summary,
        logic_text=logic_sentences(summary),
        quantifiers=quantifier_rows(summary),
        category_table=ts.category_table(temps, threshold, moderate_min, high_min),
        category_counts=ts.category_counts(temps, moderate_min, high_min),
        relation=relation_report(temps, tolerance),
        pigeonhole=pigeon,
        pigeonhole_text=pigeonhole_sentences(pigeon),
        graph=graph,
        components_text=component_sentences(graph),
    )
