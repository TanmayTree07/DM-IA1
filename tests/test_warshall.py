import pytest

from algorithms.warshall import is_reachable, warshall

ORDER = ["A", "B", "C", "D"]
# Undirected path A-B-C plus an isolated vertex D
PATH_PLUS_ISOLATED = [
    [0, 1, 0, 0],
    [1, 0, 1, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 0],
]


def test_reachability_matrix_is_correct():
    result = warshall(PATH_PLUS_ISOLATED).reachability
    assert result == [
        [1, 1, 1, 0],
        [1, 1, 1, 0],
        [1, 1, 1, 0],
        [0, 0, 0, 1],
    ]


def test_indirect_reachability():
    # A and C are not adjacent, but A-B-C is a path
    assert PATH_PLUS_ISOLATED[0][2] == 0
    reach = warshall(PATH_PLUS_ISOLATED).reachability
    assert is_reachable(reach, ORDER, "A", "C")


def test_disconnected_vertex_is_unreachable():
    reach = warshall(PATH_PLUS_ISOLATED).reachability
    assert not is_reachable(reach, ORDER, "A", "D")
    assert not is_reachable(reach, ORDER, "D", "B")


def test_reflexive_reachability_by_default():
    reach = warshall(PATH_PLUS_ISOLATED).reachability
    assert all(reach[i][i] == 1 for i in range(4))
    assert is_reachable(reach, ORDER, "D", "D")


def test_non_reflexive_option_keeps_diagonal_of_acyclic_graph_zero():
    directed_chain = [[0, 1, 0], [0, 0, 1], [0, 0, 0]]
    assert warshall(directed_chain, reflexive=False).reachability == [
        [0, 1, 1],
        [0, 0, 1],
        [0, 0, 0],
    ]


def test_directed_edges_are_respected():
    directed_chain = [[0, 1, 0], [0, 0, 1], [0, 0, 0]]
    reach = warshall(directed_chain).reachability
    assert reach[0][2] == 1 and reach[2][0] == 0


def test_input_matrix_is_not_modified():
    original = [row[:] for row in PATH_PLUS_ISOLATED]
    warshall(PATH_PLUS_ISOLATED)
    assert PATH_PLUS_ISOLATED == original


def test_intermediate_steps():
    result = warshall(PATH_PLUS_ISOLATED, keep_steps=True)
    assert len(result.steps) == 5  # R_0 ... R_4
    assert result.steps[0][0][2] == 0       # before any intermediate vertex
    assert result.steps[1][0][2] == 0       # A as intermediate does not connect A and C
    assert result.steps[2][0][2] == 1       # B as intermediate does
    assert result.steps[-1] == result.reachability


def test_invalid_matrices_are_rejected():
    with pytest.raises(ValueError):
        warshall([[0, 1], [0]])
    with pytest.raises(ValueError):
        warshall([[0, 2], [0, 0]])


def test_empty_matrix():
    assert warshall([]).reachability == []
