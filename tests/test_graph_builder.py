from algorithms.graph_builder import analyze_graph, build_similarity_graph

# A-B and B-C are within 1.0 degree; D is far from everything.
TEMPS = {"A": 30.0, "B": 31.0, "C": 32.0, "D": 40.0}


def test_vertices_are_the_regions():
    g = build_similarity_graph(TEMPS, 1.0)
    assert set(g.nodes) == {"A", "B", "C", "D"}
    assert g.nodes["B"]["temperature"] == 31.0


def test_edges_follow_the_relation():
    g = build_similarity_graph(TEMPS, 1.0)
    assert {frozenset(e) for e in g.edges} == {frozenset("AB"), frozenset("BC")}
    assert not g.has_edge("A", "C")  # difference 2.0 > 1.0


def test_no_self_loops():
    g = build_similarity_graph(TEMPS, 5.0)
    assert all(a != b for a, b in g.edges)


def test_adjacency_matrix():
    a = analyze_graph(TEMPS, 1.0)
    assert a.order == ["A", "B", "C", "D"]
    assert a.matrix == [
        [0, 1, 0, 0],
        [1, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 0],
    ]


def test_matrix_matches_edges_and_is_symmetric_with_zero_diagonal():
    a = analyze_graph(TEMPS, 1.5)
    n = len(a.order)
    for i in range(n):
        assert a.matrix[i][i] == 0
        for j in range(n):
            assert a.matrix[i][j] == a.matrix[j][i]
            assert a.matrix[i][j] == (1 if a.graph.has_edge(a.order[i], a.order[j]) else 0)


def test_degrees_and_isolated_vertices():
    a = analyze_graph(TEMPS, 1.0)
    assert a.degrees == {"A": 1, "B": 2, "C": 1, "D": 0}
    assert a.isolated == ["D"]


def test_connected_components():
    a = analyze_graph(TEMPS, 1.0)
    assert a.components == [["A", "B", "C"], ["D"]]


def test_components_merge_when_tolerance_grows():
    assert analyze_graph(TEMPS, 20.0).components == [["A", "B", "C", "D"]]
    assert len(analyze_graph(TEMPS, 0.5).components) == 4


def test_two_separate_groups():
    temps = {"P": 20.0, "Q": 20.5, "R": 40.0, "S": 40.4}
    a = analyze_graph(temps, 1.0)
    assert a.components == [["P", "Q"], ["R", "S"]]
    assert a.isolated == []


def test_region_order_is_alphabetical_regardless_of_input_order():
    a = analyze_graph({"Zed": 30.0, "Amy": 30.5}, 1.0)
    assert a.order == ["Amy", "Zed"]
    assert a.adjacency_list == {"Amy": ["Zed"], "Zed": ["Amy"]}


def test_empty_input():
    a = analyze_graph({}, 1.0)
    assert a.order == [] and a.matrix == [] and a.components == []
