"""Discrete Mathematics algorithms used by HeatWave Explorer (no Streamlit code here)."""

from .bfs import BFSResult, bfs_shortest_path, bfs_traversal
from .graph_builder import GraphAnalysis, analyze_graph, build_similarity_graph
from .logic import LogicSummary, analyze_logic, evaluate_proposition
from .pigeonhole import PigeonholeResult, analyze_pigeonhole, guaranteed_minimum
from .relations import RelationAnalysis, analyze_relation, build_similarity_relation
from .warshall import WarshallResult, is_reachable, warshall

__all__ = [
    "BFSResult", "bfs_shortest_path", "bfs_traversal",
    "GraphAnalysis", "analyze_graph", "build_similarity_graph",
    "LogicSummary", "analyze_logic", "evaluate_proposition",
    "PigeonholeResult", "analyze_pigeonhole", "guaranteed_minimum",
    "RelationAnalysis", "analyze_relation", "build_similarity_relation",
    "WarshallResult", "is_reachable", "warshall",
]
