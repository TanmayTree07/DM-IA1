"""Breadth-First Search (BFS), implemented from scratch.

Input graph: an adjacency list, i.e. a dict {vertex: [neighbours, ...]}.

How it works
------------
1. Put the source in a queue and mark it visited.
2. Take the vertex at the front of the queue. For each unvisited neighbour,
   mark it visited, remember who discovered it (its parent) and add it to the
   back of the queue.
3. Repeat until the destination is discovered or the queue is empty.

Because vertices are processed in order of distance from the source, the first
time the destination is discovered the path found is a SHORTEST path (fewest
edges) in an unweighted graph.

Time complexity: O(V + E) with an adjacency list - every vertex is queued at
most once and every edge is looked at a constant number of times.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence

AdjacencyList = Mapping[str, Sequence[str]]


@dataclass(frozen=True)
class BFSResult:
    source: str
    target: str
    reachable: bool
    path: List[str] = field(default_factory=list)
    search_order: List[str] = field(default_factory=list)  # order of discovery

    @property
    def length(self) -> Optional[int]:
        """Number of edges on the path, or None when unreachable."""
        return len(self.path) - 1 if self.reachable else None


def bfs_shortest_path(adj: AdjacencyList, source: str, target: str) -> BFSResult:
    """Find a shortest path from source to target (fewest edges)."""
    for vertex in (source, target):
        if vertex not in adj:
            raise ValueError(f"Vertex {vertex!r} is not in the graph")

    if source == target:
        return BFSResult(source, target, True, [source], [source])

    visited = {source}
    parent: Dict[str, Optional[str]] = {source: None}
    queue = deque([source])
    order = [source]

    while queue:
        current = queue.popleft()
        for neighbour in adj[current]:
            if neighbour in visited:
                continue
            visited.add(neighbour)
            parent[neighbour] = current
            order.append(neighbour)
            if neighbour == target:
                return BFSResult(source, target, True, _rebuild_path(parent, target), order)
            queue.append(neighbour)

    return BFSResult(source, target, False, [], order)


def bfs_traversal(adj: AdjacencyList, start: str) -> List[str]:
    """All vertices reachable from `start`, in BFS discovery order."""
    if start not in adj:
        raise ValueError(f"Vertex {start!r} is not in the graph")
    visited = {start}
    queue = deque([start])
    order = [start]
    while queue:
        current = queue.popleft()
        for neighbour in adj[current]:
            if neighbour not in visited:
                visited.add(neighbour)
                order.append(neighbour)
                queue.append(neighbour)
    return order


def _rebuild_path(parent: Mapping[str, Optional[str]], target: str) -> List[str]:
    path = []
    node: Optional[str] = target
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path
