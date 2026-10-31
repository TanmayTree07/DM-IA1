from algorithms.relations import (
    analyze_relation,
    are_similar,
    build_similarity_relation,
    find_transitivity_violation,
    is_reflexive,
    is_symmetric,
    is_transitive,
)

TEMPS = {"A": 30.0, "B": 31.0, "C": 32.0}
ORDER = ["A", "B", "C"]


def test_similarity_boundary_is_inclusive():
    assert are_similar(30.0, 31.5, 1.5)
    assert not are_similar(30.0, 31.6, 1.5)


def test_floating_point_boundary_is_handled():
    # 36.4 - 34.9 is 1.5000000000000036 in floating point but should count as 1.5
    assert are_similar(36.4, 34.9, 1.5)


def test_relation_is_reflexive():
    relation = build_similarity_relation(TEMPS, 1.0)
    assert is_reflexive(ORDER, relation)
    assert all((r, r) in relation for r in ORDER)


def test_relation_is_symmetric():
    relation = build_similarity_relation(TEMPS, 1.0)
    assert is_symmetric(relation)
    assert ("A", "B") in relation and ("B", "A") in relation


def test_transitivity_fails_for_chain_of_close_temperatures():
    # A~B (diff 1) and B~C (diff 1) but A!~C (diff 2 > 1)
    relation = build_similarity_relation(TEMPS, 1.0)
    assert not is_transitive(ORDER, relation)
    assert find_transitivity_violation(ORDER, relation) == ("A", "B", "C")
    assert ("A", "C") not in relation


def test_transitivity_holds_with_larger_tolerance():
    relation = build_similarity_relation(TEMPS, 2.0)
    assert is_transitive(ORDER, relation)


def test_zero_tolerance_still_reflexive_and_transitive_for_distinct_temps():
    relation = build_similarity_relation(TEMPS, 0.0)
    assert relation == {("A", "A"), ("B", "B"), ("C", "C")}
    assert analyze_relation(ORDER, relation).is_equivalence_relation


def test_checks_detect_broken_relations():
    # not reflexive (missing (B, B)), not symmetric (A,B without B,A)
    broken = {("A", "A"), ("C", "C"), ("A", "B")}
    result = analyze_relation(ORDER, broken)
    assert not result.reflexive and result.reflexivity_violation == "B"
    assert not result.symmetric and result.symmetry_violation == ("A", "B")


def test_analysis_of_similarity_relation():
    result = analyze_relation(ORDER, build_similarity_relation(TEMPS, 1.0))
    assert result.reflexive and result.symmetric and not result.transitive
    assert not result.is_equivalence_relation
