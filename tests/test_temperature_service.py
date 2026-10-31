from services import temperature_service as ts


def test_category_boundaries():
    assert ts.categorize_temperature(34.9, 35.0, 40.0) == "Normal"
    assert ts.categorize_temperature(35.0, 35.0, 40.0) == "Moderate"
    assert ts.categorize_temperature(39.9, 35.0, 40.0) == "Moderate"
    assert ts.categorize_temperature(40.0, 35.0, 40.0) == "High"


def test_boundaries_are_adjustable():
    assert ts.categorize_temperature(30.0, 25.0, 29.0) == "High"


def test_invalid_boundaries_are_rejected():
    assert ts.validate_boundaries(40.0, 35.0) is not None
    assert ts.validate_boundaries(35.0, 35.0) is not None
    assert ts.validate_boundaries(35.0, 40.0) is None


def test_category_table_and_counts():
    temps = {"A": 30.0, "B": 36.0, "C": 41.0}
    table = ts.category_table(temps, 36.0, 35.0, 40.0)
    assert table["Category"].tolist() == ["Normal", "Moderate", "High"]
    assert table["P(x): temp ≥ threshold"].tolist() == [False, True, True]
    assert ts.category_counts(temps, 35.0, 40.0) == {"Normal": 1, "Moderate": 1, "High": 1}


def test_descriptive_statistics():
    stats = ts.describe_temperatures({"A": 30.0, "B": 40.0, "C": 35.0})
    assert stats["count"] == 3
    assert stats["mean"] == 35.0 and stats["median"] == 35.0
    assert stats["min"] == 30.0 and stats["max"] == 40.0 and stats["range"] == 10.0
    assert stats["hottest"] == "B" and stats["coolest"] == "A"
    assert abs(stats["std"] - 5.0) < 1e-9


def test_statistics_for_one_region_and_none():
    assert ts.describe_temperatures({"A": 30.0})["std"] is None
    assert ts.describe_temperatures({}) == {"count": 0}
    assert ts.statistics_table({"count": 0}).empty
