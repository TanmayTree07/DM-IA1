import pytest

from algorithms.bfs import bfs_shortest_path, bfs_traversal

# Two routes from A to F:  A-B-C-F (3 edges)  and  A-E-F (2 edges)
GRAPH = {
    "A": ["B", "E"],
    "B": ["A", "C"],
    "C": ["B", "F"],
    "E": ["A", "F"],
    "F": ["C", "E"],
    "Z": [],  # isolated
}


def test_valid_path_exists():
    r = bfs_shortest_path(GRAPH, "A", "C")
    assert r.reachable
    assert r.path == ["A", "B", "C"]
    assert r.length == 2


def test_shortest_path_is_returned():
    r = bfs_shortest_path(GRAPH, "A", "F")
    assert r.path == ["A", "E", "F"]
    assert r.length == 2  # not the 3-edge route through B and C


def test_no_path_to_isolated_vertex():
    r = bfs_shortest_path(GRAPH, "A", "Z")
    assert not r.reachable
    assert r.path == []
    assert r.length is None


def test_source_equals_destination():
    r = bfs_shortest_path(GRAPH, "A", "A")
    assert r.reachable
    assert r.path == ["A"]
    assert r.length == 0


def test_source_equals_destination_for_isolated_vertex():
    assert bfs_shortest_path(GRAPH, "Z", "Z").path == ["Z"]


def test_search_order_is_breadth_first():
    adj = {"A": ["B", "C"], "B": ["A", "D"], "C": ["A"], "D": ["B"]}
    r = bfs_shortest_path(adj, "A", "D")
    assert r.search_order == ["A", "B", "C", "D"]


def test_unknown_vertex_raises():
    with pytest.raises(ValueError):
        bfs_shortest_path(GRAPH, "A", "nope")
    with pytest.raises(ValueError):
        bfs_traversal(GRAPH, "nope")


def test_traversal_visits_only_the_component():
    assert sorted(bfs_traversal(GRAPH, "A")) == ["A", "B", "C", "E", "F"]
    assert bfs_traversal(GRAPH, "Z") == ["Z"]
