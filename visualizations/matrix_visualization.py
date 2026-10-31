"""Adjacency / reachability matrices as tables and heatmaps.

Rows and columns always use the SAME region order that the algorithms use
(alphabetical), so cell (i, j) refers to the same pair everywhere.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

import pandas as pd
import plotly.graph_objects as go

ZERO_COLOR = "#f1f5f9"
ONE_COLOR = "#ea580c"


def matrix_to_dataframe(matrix: Sequence[Sequence[int]], order: Sequence[str]) -> pd.DataFrame:
    """Labelled table version of a matrix (row label = from, column label = to)."""
    return pd.DataFrame(matrix, index=list(order), columns=list(order))


def build_matrix_figure(matrix: Sequence[Sequence[int]], order: Sequence[str], title: str,
                        highlight: Optional[Tuple[str, str]] = None) -> Optional[go.Figure]:
    """Heatmap of a 0/1 matrix with the numbers written inside the cells.

    `highlight=(row_region, column_region)` outlines one cell (e.g. the selected pair).
    """
    if not order:
        return None
    n = len(order)
    fig = go.Figure(go.Heatmap(
        z=[list(row) for row in matrix],
        x=list(order),
        y=list(order),
        zmin=0,
        zmax=1,
        colorscale=[[0, ZERO_COLOR], [1, ONE_COLOR]],
        showscale=False,
        text=[[str(v) for v in row] for row in matrix],
        texttemplate="%{text}",
        hovertemplate="row %{y}, column %{x}: %{z}<extra></extra>",
        xgap=2,
        ygap=2,
    ))
    if highlight and highlight[0] in order and highlight[1] in order:
        row, col = list(order).index(highlight[0]), list(order).index(highlight[1])
        fig.add_shape(type="rect", x0=col - 0.5, x1=col + 0.5, y0=row - 0.5, y1=row + 0.5,
                      line=dict(color="#1e293b", width=3))
    fig.update_layout(
        title=title,
        height=max(340, 34 * n + 150),
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(side="top", tickangle=-45),
        yaxis=dict(autorange="reversed"),
    )
    return fig
