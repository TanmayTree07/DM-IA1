from algorithms.logic import analyze_logic, evaluate_proposition, exists, for_all, proposition

TEMPS = {"A": 30.0, "B": 35.0, "C": 40.0}


def test_temperature_above_threshold_is_true():
    assert proposition(36.0, 35.0) is True


def test_temperature_below_threshold_is_false():
    assert proposition(34.9, 35.0) is False


def test_temperature_equal_to_threshold_is_true():
    # P(x) uses >=, so equality counts as satisfying the proposition
    assert proposition(35.0, 35.0) is True


def test_truth_values_per_region():
    assert evaluate_proposition(TEMPS, 35.0) == {"A": False, "B": True, "C": True}


def test_mixed_case_summary():
    s = analyze_logic(TEMPS, 35.0)
    assert s.satisfying == ["B", "C"]
    assert s.not_satisfying == ["A"]
    assert (s.count, s.total) == (2, 3)
    assert s.exists_above is True
    assert s.all_above is False
    assert s.all_below is False


def test_all_regions_above():
    s = analyze_logic(TEMPS, 20.0)
    assert s.count == 3
    assert (s.exists_above, s.all_above, s.all_below) == (True, True, False)


def test_all_regions_below():
    s = analyze_logic(TEMPS, 50.0)
    assert s.count == 0
    assert (s.exists_above, s.all_above, s.all_below) == (False, False, True)


def test_empty_input_gives_undefined_quantifiers():
    s = analyze_logic({}, 35.0)
    assert s.is_empty
    assert s.count == 0 and s.total == 0
    # None, not a misleading vacuous "True"
    assert s.exists_above is None
    assert s.all_above is None
    assert s.all_below is None


def test_quantifier_helpers():
    assert exists(lambda x: x > 2, [1, 2, 3]) is True
    assert exists(lambda x: x > 5, [1, 2, 3]) is False
    assert for_all(lambda x: x > 0, [1, 2, 3]) is True
    assert for_all(lambda x: x > 1, [1, 2, 3]) is False
    assert exists(lambda x: True, []) is None
    assert for_all(lambda x: True, []) is None
