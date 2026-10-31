"""Build the temperature-similarity graph and derive its properties.

* Vertices: the selected regions (always in ALPHABETICAL order - this order is
  used for the adjacency matrix, BFS and Warshall so they always agree).
* Edges:    an undirected edge {A, B} exists  <=>  A != B and A R B, i.e.
            |temperature(A) - temperature(B)| <= tolerance.

Adjacency-matrix convention: the diagonal is 0 because the graph is a simple
graph (no self-loops). The relation R is reflexive, but "A is similar to
itself" is not drawn as an edge.

This is a MATHEMATICAL representation. Edges do not stand for roads, travel
routes or heat spreading between places.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple

import networkx as nx

from .bfs import bfs_traversal
from .relations import build_similarity_relation


@dataclass
class GraphAnalysis:
    order: List[str]
    temperatures: Dict[str, float]
    tolerance: float
    graph: nx.Graph
    matrix: List[List[int]]
    adjacency_list: Dict[str, List[str]]
    degrees: Dict[str, int]
    isolated: List[str]
    components: List[List[str]]

    @property
    def edges(self) -> List[Tuple[str, str]]:
        index = {name: i for i, name in enumerate(self.order)}
        return sorted((tuple(sorted(e, key=index.get)) for e in self.graph.edges()),
                      key=lambda e: (index[e[0]], index[e[1]]))

    @property
    def edge_count(self) -> int:
        return self.graph.number_of_edges()


def build_similarity_graph(temps: Mapping[str, float], tolerance: float) -> nx.Graph:
    """Vertices = regions, edges = pairs of distinct regions related by R."""
    order = sorted(temps)
    relation = build_similarity_relation(temps, tolerance)
    graph = nx.Graph()
    for region in order:
        graph.add_node(region, temperature=temps[region])
    for i, a in enumerate(order):
        for b in order[i + 1:]:
            if (a, b) in relation:
                graph.add_edge(a, b, difference=round(abs(temps[a] - temps[b]), 2))
    return graph


def adjacency_matrix(graph: nx.Graph, order: Sequence[str]) -> List[List[int]]:
    """0/1 matrix with rows and columns in `order`; diagonal is 0."""
    return [
        [1 if i != j and graph.has_edge(a, b) else 0 for j, b in enumerate(order)]
        for i, a in enumerate(order)
    ]


def adjacency_list(graph: nx.Graph, order: Sequence[str]) -> Dict[str, List[str]]:
    """Neighbours of each vertex, listed in `order` (deterministic for BFS)."""
    return {a: [b for b in order if b != a and graph.has_edge(a, b)] for a in order}


def vertex_degrees(graph: nx.Graph, order: Sequence[str]) -> Dict[str, int]:
    return {region: graph.degree(region) for region in order}


def isolated_vertices(degrees: Mapping[str, int], order: Sequence[str]) -> List[str]:
    return [region for region in order if degrees[region] == 0]


def connected_components(adj: Mapping[str, Sequence[str]], order: Sequence[str]) -> List[List[str]]:
    """Connected components, found by repeated BFS using our own bfs_traversal."""
    position = {name: i for i, name in enumerate(order)}
    seen = set()
    components: List[List[str]] = []
    for start in order:
        if start in seen:
            continue
        members = bfs_traversal(adj, start)
        seen.update(members)
        components.append(sorted(members, key=position.get))
    return components


def analyze_graph(temps: Mapping[str, float], tolerance: float) -> GraphAnalysis:
    """Build the graph and everything derived from it, in one consistent bundle."""
    order = sorted(temps)
    graph = build_similarity_graph(temps, tolerance)
    adj = adjacency_list(graph, order)
    degrees = vertex_degrees(graph, order)
    return GraphAnalysis(
        order=order,
        temperatures={r: temps[r] for r in order},
        tolerance=tolerance,
        graph=graph,
        matrix=adjacency_matrix(graph, order),
        adjacency_list=adj,
        degrees=degrees,
        isolated=isolated_vertices(degrees, order),
        components=connected_components(adj, order),
    )
