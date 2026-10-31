"""Plotly drawing of the temperature-similarity graph.

The layout is a fixed circle in alphabetical order, so vertices do not jump
around when the tolerance changes - only the edges appear or disappear.
"""

from __future__ import annotations

import math
from typing import Optional, Sequence

import plotly.graph_objects as go

from algorithms.graph_builder import GraphAnalysis

PALETTE = ["#4c78a8", "#f58518", "#54a24b", "#b279a2", "#9d755d",
           "#72b7b2", "#e45756", "#eeca3b", "#ff9da6", "#bab0ac"]
PATH_COLOR = "#d62728"
EDGE_COLOR = "#94a3b8"


def _circle_positions(order: Sequence[str]):
    n = len(order)
    if n == 1:
        return {order[0]: (0.0, 0.0)}
    return {
        name: (math.cos(2 * math.pi * i / n + math.pi / 2), math.sin(2 * math.pi * i / n + math.pi / 2))
        for i, name in enumerate(order)
    }


def _text_position(x: float, y: float) -> str:
    if y > 0.35:
        return "top center"
    if y < -0.35:
        return "bottom center"
    return "middle right" if x >= 0 else "middle left"


def build_graph_figure(analysis: GraphAnalysis, path: Optional[Sequence[str]] = None,
                       title: str = "Temperature-similarity graph") -> Optional[go.Figure]:
    """Return a Plotly figure, or None when there is nothing to draw."""
    order = analysis.order
    if not order:
        return None
    pos = _circle_positions(order)
    group_of = {name: i for i, members in enumerate(analysis.components) for name in members}
    path = list(path or [])
    path_edges = {frozenset(pair) for pair in zip(path, path[1:])}

    plain_x, plain_y, path_x, path_y = [], [], [], []
    mid_x, mid_y, mid_text = [], [], []
    for a, b in analysis.edges:
        target_x, target_y = (path_x, path_y) if frozenset((a, b)) in path_edges else (plain_x, plain_y)
        target_x += [pos[a][0], pos[b][0], None]
        target_y += [pos[a][1], pos[b][1], None]
        mid_x.append((pos[a][0] + pos[b][0]) / 2)
        mid_y.append((pos[a][1] + pos[b][1]) / 2)
        diff = abs(analysis.temperatures[a] - analysis.temperatures[b])
        mid_text.append(f"{a} – {b}<br>|Δ| = {diff:.2f} °C ≤ {analysis.tolerance:g}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plain_x, y=plain_y, mode="lines", hoverinfo="skip",
                             line=dict(color=EDGE_COLOR, width=1.5), showlegend=False))
    if path_x:
        fig.add_trace(go.Scatter(x=path_x, y=path_y, mode="lines", hoverinfo="skip",
                                 line=dict(color=PATH_COLOR, width=5), showlegend=False))
    fig.add_trace(go.Scatter(x=mid_x, y=mid_y, mode="markers", hovertext=mid_text, hoverinfo="text",
                             marker=dict(size=10, opacity=0), showlegend=False))

    on_path = set(path)
    fig.add_trace(go.Scatter(
        x=[pos[v][0] for v in order],
        y=[pos[v][1] for v in order],
        mode="markers+text",
        text=[f"{v}<br>{analysis.temperatures[v]:.1f}°C" for v in order],
        textposition=[_text_position(*pos[v]) for v in order],
        hovertext=[
            f"<b>{v}</b><br>{analysis.temperatures[v]:.2f} °C<br>degree {analysis.degrees[v]}"
            f"<br>group {group_of[v] + 1}" for v in order
        ],
        hoverinfo="text",
        marker=dict(
            size=24,
            color=[PALETTE[group_of[v] % len(PALETTE)] for v in order],
            symbol=["diamond" if v in analysis.isolated else "circle" for v in order],
            line=dict(color=[PATH_COLOR if v in on_path else "#ffffff" for v in order],
                      width=[4 if v in on_path else 1 for v in order]),
        ),
        showlegend=False,
    ))
    fig.update_layout(
        title=title,
        height=620,
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(visible=False, range=[-1.6, 1.6]),
        yaxis=dict(visible=False, range=[-1.45, 1.45], scaleanchor="x", scaleratio=1),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig
