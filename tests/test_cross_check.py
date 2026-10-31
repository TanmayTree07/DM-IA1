"""Cross-checks the hand-written algorithms against NetworkX on random graphs.

NetworkX is used here ONLY as an independent referee inside the tests; the
application itself never calls NetworkX's BFS, reachability or component code.
"""

import random

import networkx as nx
import pytest

from algorithms.bfs import bfs_shortest_path
from algorithms.graph_builder import analyze_graph
from algorithms.warshall import warshall


def random_temps(seed: int, n: int = 9):
    rng = random.Random(seed)
    return {f"R{i}": round(rng.uniform(25.0, 45.0), 1) for i in range(n)}


@pytest.mark.parametrize("seed", range(15))
@pytest.mark.parametrize("tolerance", [0.5, 1.5, 3.0])
def test_bfs_warshall_and_components_agree_with_networkx(seed, tolerance):
    a = analyze_graph(random_temps(seed), tolerance)
    reach = warshall(a.matrix).reachability

    for i, source in enumerate(a.order):
        for j, target in enumerate(a.order):
            connected = nx.has_path(a.graph, source, target)
            assert bool(reach[i][j]) == connected
            result = bfs_shortest_path(a.adjacency_list, source, target)
            assert result.reachable == connected
            if connected:
                assert result.length == nx.shortest_path_length(a.graph, source, target)

    ours = sorted(sorted(c) for c in a.components)
    reference = sorted(sorted(c) for c in nx.connected_components(a.graph))
    assert ours == reference
