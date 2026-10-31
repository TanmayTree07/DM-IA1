from algorithms.logic import analyze_logic
from services import insights_service as ins

TEMPS = {"A": 30.0, "B": 31.0, "C": 32.0, "D": 40.0}


def test_quantifier_rows_contain_witnesses_and_counterexamples():
    rows = ins.quantifier_rows(analyze_logic(TEMPS, 35.0))
    exists_row, all_row, none_row = rows
    assert exists_row["Result"] == "True" and "D" in exists_row["Evidence"]
    assert all_row["Result"] == "False" and "A" in all_row["Evidence"]
    assert none_row["Result"] == "False" and "D" in none_row["Evidence"]


def test_quantifiers_on_empty_data_are_undefined():
    rows = ins.quantifier_rows(analyze_logic({}, 35.0))
    assert len(rows) == 1 and rows[0]["Result"] == "Undefined"


def test_explain_pair():
    similar, text = ins.explain_pair(TEMPS, "A", "B", 1.0)
    assert similar and "an edge exists" in text
    similar, text = ins.explain_pair(TEMPS, "A", "C", 1.0)
    assert not similar and "no edge" in text and "2.00 > 1" in text
    assert ins.explain_pair(TEMPS, "A", "A", 1.0)[0] is False


def test_relation_report_shows_transitivity_counterexample():
    report = ins.relation_report(TEMPS, 1.0)
    assert report.analysis.reflexive and report.analysis.symmetric and not report.analysis.transitive
    assert any("FAILS" in line and "A R B" in line for line in report.examples)
    assert "NOT transitive" in report.summary


def test_relation_report_equivalence_case():
    report = ins.relation_report(TEMPS, 20.0)
    assert report.analysis.is_equivalence_relation
    assert "equivalence relation" in report.summary


def test_component_sentences_are_generated_from_the_graph():
    from algorithms.graph_builder import analyze_graph
    lines = ins.component_sentences(analyze_graph(TEMPS, 1.0))
    assert lines[0].startswith("Group 1 contains A, B and C")
    assert "only D" in lines[1] and "isolated" in lines[1]


def test_build_insights_bundle():
    bundle = ins.build_insights(TEMPS, 35.0, 1.0, 35.0, 40.0, 2)
    assert bundle.logic.count == 1
    assert bundle.category_counts == {"Normal": 3, "Moderate": 0, "High": 1}
    assert bundle.pigeonhole.guaranteed_min == 2
    assert len(bundle.components_text) == 2


def test_pigeonhole_text_for_invalid_input():
    bundle = ins.build_insights({}, 35.0, 1.0, 35.0, 40.0, 3)
    assert not bundle.pigeonhole.valid
    assert "no regions" in bundle.pigeonhole_text[0]
