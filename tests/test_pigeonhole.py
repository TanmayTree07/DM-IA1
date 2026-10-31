import pytest

from algorithms.pigeonhole import analyze_pigeonhole, assign_to_bins, guaranteed_minimum


@pytest.mark.parametrize("items, boxes, expected", [
    (7, 3, 3),   # ceil(7/3)
    (6, 3, 2),   # exact division
    (3, 3, 1),
    (5, 1, 5),
    (1, 3, 1),
    (0, 3, 0),
    (10, 4, 3),
])
def test_ceiling_calculation(items, boxes, expected):
    assert guaranteed_minimum(items, boxes) == expected


def test_invalid_box_count_raises():
    with pytest.raises(ValueError):
        guaranteed_minimum(5, 0)


TEMPS = {"A": 20.0, "B": 21.0, "C": 30.0, "D": 31.0, "E": 40.0}


def test_more_regions_than_bins():
    r = analyze_pigeonhole(TEMPS, 2)
    assert r.valid and r.basic_principle_applies
    assert r.guaranteed_min == 3            # ceil(5/2)
    assert r.counts == {0: 2, 1: 3}
    assert r.max_count == 3 and r.largest_bins == [1]
    assert r.max_count >= r.guaranteed_min  # the principle itself


def test_equal_regions_and_bins_does_not_force_a_shared_bin():
    temps = {"A": 20.0, "B": 30.0, "C": 40.0}
    r = analyze_pigeonhole(temps, 3)
    assert r.valid
    assert not r.basic_principle_applies    # n = k, principle gives nothing forced
    assert r.guaranteed_min == 1
    assert r.counts == {0: 1, 1: 1, 2: 1}


def test_one_category_holds_everything():
    r = analyze_pigeonhole(TEMPS, 1)
    assert r.basic_principle_applies
    assert r.guaranteed_min == 5
    assert r.counts == {0: 5}


def test_empty_input():
    r = analyze_pigeonhole({}, 3)
    assert not r.valid
    assert r.guaranteed_min is None
    assert "no regions" in r.message


def test_zero_bins_is_handled():
    r = analyze_pigeonhole(TEMPS, 0)
    assert not r.valid
    assert r.guaranteed_min is None


def test_every_region_is_assigned_exactly_once():
    bins = assign_to_bins(TEMPS, 3)
    assigned = [region for members in bins.values() for region in members]
    assert sorted(assigned) == sorted(TEMPS)


def test_maximum_temperature_goes_into_last_bin():
    bins = assign_to_bins(TEMPS, 4)
    assert "E" in bins[3] and "A" in bins[0]


def test_identical_temperatures_share_one_bin():
    bins = assign_to_bins({"A": 33.0, "B": 33.0, "C": 33.0}, 3)
    assert bins[0] == ["A", "B", "C"]
