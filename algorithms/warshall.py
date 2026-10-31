"""Warshall's algorithm (transitive closure), implemented from scratch.

Input: a square 0/1 matrix M where M[i][j] = 1 means "there is an edge from
vertex i to vertex j". The row/column order is whatever order the caller uses
(HeatWave Explorer uses alphabetical region order everywhere).

Idea
----
Let R_k[i][j] = 1 if there is a path from i to j that only uses the first k
vertices as intermediate stops. Start with R_0 = M. Allow one more
intermediate vertex k at a time:

    R_k[i][j] = R_{k-1}[i][j]  OR  ( R_{k-1}[i][k] AND R_{k-1}[k][j] )

After all n vertices have been allowed, R_n[i][j] = 1 exactly when j can be
reached from i by some path.

Convention used in this project (REFLEXIVE reachability)
--------------------------------------------------------
Every vertex counts as reachable from itself (path of length 0), so the
diagonal of the reachability matrix is all 1s. The adjacency matrix itself has
0s on the diagonal (a simple graph has no self-loops). Pass reflexive=False to
get the classic closure without this convention.

Time complexity: three nested loops over n vertices -> O(V^3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

Matrix = List[List[int]]


@dataclass(frozen=True)
class WarshallResult:
    reachability: Matrix
    # steps[0] is the starting matrix (R_0), steps[k] is the matrix after the
    # k-th vertex has been allowed as an intermediate stop. Empty unless
    # keep_steps=True was requested.
    steps: List[Matrix] = field(default_factory=list)


def _validate(matrix: Sequence[Sequence[int]]) -> None:
    n = len(matrix)
    for row in matrix:
        if len(row) != n:
            raise ValueError("Adjacency matrix must be square")
        for value in row:
            if value not in (0, 1):
                raise ValueError("Adjacency matrix entries must be 0 or 1")


def warshall(
    adjacency: Sequence[Sequence[int]],
    reflexive: bool = True,
    keep_steps: bool = False,
) -> WarshallResult:
    """Compute the reachability (transitive closure) matrix."""
    _validate(adjacency)
    n = len(adjacency)
    reach = [[int(v) for v in row] for row in adjacency]  # work on a copy
    if reflexive:
        for i in range(n):
            reach[i][i] = 1

    steps: List[Matrix] = [[row[:] for row in reach]] if keep_steps else []

    for k in range(n):
        for i in range(n):
            if reach[i][k]:
                for j in range(n):
                    if reach[k][j]:
                        reach[i][j] = 1
        if keep_steps:
            steps.append([row[:] for row in reach])

    return WarshallResult(reachability=reach, steps=steps)


def is_reachable(reachability: Sequence[Sequence[int]], order: Sequence[str],
                 source: str, target: str) -> bool:
    """Look up source -> target in a reachability matrix with the given vertex order."""
    for vertex in (source, target):
        if vertex not in order:
            raise ValueError(f"Vertex {vertex!r} is not in the vertex list")
    return bool(reachability[list(order).index(source)][list(order).index(target)])
