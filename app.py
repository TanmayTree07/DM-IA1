"""HeatWave Explorer - Streamlit dashboard.

This file only builds the user interface. The mathematics lives in
algorithms/, the data handling in services/ and the figures in visualizations/.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import datetime as dt
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from algorithms.bfs import bfs_shortest_path
from algorithms.graph_builder import analyze_graph
from algorithms.logic import analyze_logic
from algorithms.warshall import is_reachable, warshall
from services import data_service as ds
from services import insights_service as ins
from services import temperature_service as ts
from visualizations.graph_visualization import build_graph_figure
from visualizations.matrix_visualization import build_matrix_figure, matrix_to_dataframe

CATEGORY_COLORS = {"Normal": "#4c78a8", "Moderate": "#f2a900", "High": "#c0392b"}

st.set_page_config(page_title="HeatWave Explorer", page_icon="🌡️", layout="wide")
st.markdown(
    """
    <style>
    :root {
        --heatwave-ink: #172554;
        --heatwave-muted: #64748b;
        --heatwave-border: #e2e8f0;
        --heatwave-accent: #0f766e;
    }
    .block-container {padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1500px;}
    [data-testid="stSidebar"] {
        border-right: 1px solid var(--heatwave-border);
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: var(--heatwave-ink);
    }
    .heatwave-hero {
        padding: 1.5rem 1.75rem;
        margin: 0 0 1.25rem;
        border: 1px solid #dbeafe;
        border-radius: 18px;
        background: linear-gradient(120deg, #eff6ff 0%, #f0fdfa 72%, #f8fafc 100%);
    }
    .heatwave-eyebrow {
        margin: 0 0 .35rem;
        color: var(--heatwave-accent);
        font-size: .75rem;
        font-weight: 700;
        letter-spacing: .12em;
        text-transform: uppercase;
    }
    .heatwave-hero h1 {
        margin: 0;
        color: var(--heatwave-ink);
        font-size: clamp(1.8rem, 3vw, 2.5rem);
        line-height: 1.15;
    }
    .heatwave-hero p:last-child {
        margin: .55rem 0 0;
        color: #475569;
        font-size: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: .45rem;
        border-bottom: 1px solid var(--heatwave-border);
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 1rem;
        border-radius: 10px 10px 0 0;
        color: #475569;
    }
    .stTabs [aria-selected="true"] {
        color: var(--heatwave-accent);
        font-weight: 700;
    }
    [data-testid="stMetric"] {
        min-height: 112px;
        background: #ffffff;
        border: 1px solid var(--heatwave-border);
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 3px 12px rgba(15, 23, 42, .04);
    }
    [data-testid="stMetricLabel"] {
        color: var(--heatwave-muted);
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        color: var(--heatwave-ink);
    }
    .stButton > button[kind="primary"] {
        border-radius: 10px;
        font-weight: 700;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--heatwave-border);
        border-radius: 12px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------- helpers
def show_figure(builder, *args, key: str, **kwargs) -> None:
    """Draw an optional visualisation; a failure here must never crash the dashboard."""
    try:
        fig = builder(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - deliberately broad, see docstring
        st.warning(f"This visualisation could not be drawn: {exc}")
        return
    if fig is None:
        st.info("Nothing to draw for the current selection.")
        return
    st.plotly_chart(fig, key=key)


def init_state() -> None:
    if "df" in st.session_state:
        return
    result = ds.load_sample_data()
    if not result.ok:
        st.error("The built-in sample dataset could not be loaded.")
        for message in result.errors:
            st.error(message)
        st.stop()
    st.session_state.df = result.df
    st.session_state.sample_warnings = result.warnings
    st.session_state.bfs_run = None


# ----------------------------------------------------------------------------- page
init_state()
st.markdown(
    """
    <header class="heatwave-hero">
      <p class="heatwave-eyebrow">Discrete mathematics · Interactive dashboard</p>
      <h1>🌡️ HeatWave Explorer</h1>
      <p>Explore regional temperatures through logic, relations, graph theory, and algorithms.</p>
    </header>
    """,
    unsafe_allow_html=True,
)
for message in st.session_state.sample_warnings:
    st.warning(message)

tab_explorer, tab_graph, tab_algorithms, tab_insights = st.tabs(
    ["🌡️ Temperature Explorer", "🔗 Relationship Graph", "🧭 Graph Algorithms", "📐 DM Insights"]
)

df: pd.DataFrame = st.session_state.df
min_date, max_date = ds.get_date_bounds(df)
all_regions = ds.list_regions(df)
dataset_key = f"{len(df)}|{min_date:%Y%m%d}|{max_date:%Y%m%d}"

# ----------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Explore the data")
    st.caption("Adjust the analysis once; your selection is shared across every view.")
    st.subheader("Observation period")
    mode = st.radio("Use", ["Single date", "Date range"], key=f"mode|{dataset_key}")
    if mode == "Single date":
        picked = st.date_input("Date", value=max_date.date(), min_value=min_date.date(),
                               max_value=max_date.date(), key=f"date|{dataset_key}")
        start = end = pd.Timestamp(picked)
        period_text = f"{start:%d %b %Y}"
        method_text = "each region's observation on that date"
    else:
        default_start = max(min_date, max_date - pd.Timedelta(days=6))
        picked = st.date_input("Date range", value=(default_start.date(), max_date.date()),
                               min_value=min_date.date(), max_value=max_date.date(),
                               key=f"range|{dataset_key}")
        if not isinstance(picked, (tuple, list)) or len(picked) != 2:
            st.info("Pick both a start date and an end date.")
            st.stop()
        start, end = pd.Timestamp(picked[0]), pd.Timestamp(picked[1])
        period_text = f"{start:%d %b %Y} to {end:%d %b %Y}"
        method_text = "each region's MEAN temperature over the range"

    st.subheader("Regions")
    chosen = st.multiselect("Regions to include", all_regions, default=all_regions,
                            key=f"regions|{dataset_key}")

    st.subheader("Threshold P(x)")
    lo = float(math.floor(df["temperature_celsius"].min()))
    hi = float(math.ceil(df["temperature_celsius"].max()))
    if hi <= lo:
        hi = lo + 1.0
    threshold = st.slider("Temperature threshold (°C)", lo, hi, min(max(38.0, lo), hi), 0.5,
                          key=f"threshold|{dataset_key}",
                          help="P(x) is true when a region's temperature is at least this value.")

    with st.expander("Advanced: category boundaries"):
        moderate_min = st.number_input("'Moderate' starts at (°C)", value=ts.DEFAULT_MODERATE_MIN, step=0.5,
                                       key="moderate_min")
        high_min = st.number_input("'High' starts at (°C)", value=ts.DEFAULT_HIGH_MIN, step=0.5, key="high_min")
        boundary_error = ts.validate_boundaries(moderate_min, high_min)
        if boundary_error:
            st.error(boundary_error + " Using the defaults instead.")
            moderate_min, high_min = ts.DEFAULT_MODERATE_MIN, ts.DEFAULT_HIGH_MIN
        st.caption("Teaching values only; not an official heatwave classification.")

regions = sorted(chosen)
temps, missing = ds.representative_temperatures(df, regions, start, end) if regions else ({}, [])


# ----------------------------------------------------------------------------- chart builders (UI only)
def bar_chart(table: pd.DataFrame, threshold: float, period_text: str) -> go.Figure:
    ordered = table.sort_values("Temperature (°C)", ascending=False)
    fig = px.bar(
        ordered, x="Region", y="Temperature (°C)", color="Category",
        color_discrete_map=CATEGORY_COLORS, category_orders={"Category": list(ts.CATEGORIES)},
        title=f"Regional temperatures — {period_text}",
    )
    fig.add_hline(y=threshold, line_dash="dash", line_color="#334155",
                  annotation_text=f"Threshold {threshold:g} °C")
    fig.update_layout(xaxis_title="Region", yaxis_title="Temperature (°C)", legend_title="Category")
    return fig


def time_series_chart(data: pd.DataFrame, chosen_regions, start: pd.Timestamp, end: pd.Timestamp,
                      threshold: float) -> go.Figure:
    subset = data[data["region"].isin(chosen_regions)]
    fig = px.line(
        subset, x="date", y="temperature_celsius", color="region",
        title="Temperature over time (shaded band = selected period)",
        labels={"date": "Date", "temperature_celsius": "Temperature (°C)", "region": "Region"},
    )
    fig.add_vrect(x0=(start - pd.Timedelta(hours=12)).isoformat(), x1=(end + pd.Timedelta(hours=12)).isoformat(),
                  fillcolor="#f2a900", opacity=0.2, line_width=0)
    fig.add_hline(y=threshold, line_dash="dash", line_color="#334155")
    return fig


def pigeonhole_chart(result) -> go.Figure:
    labels = ins.bin_labels(result)
    fig = go.Figure(go.Bar(x=labels, y=[result.counts[i] for i in range(result.num_bins)],
                           marker_color="#4c78a8", name="Regions in bin"))
    fig.add_hline(y=result.guaranteed_min, line_dash="dash", line_color="#c0392b",
                  annotation_text=f"Guaranteed minimum for some bin: ⌈{result.num_items}/{result.num_bins}⌉ "
                                  f"= {result.guaranteed_min}")
    fig.update_layout(title="Regions per temperature bin", xaxis_title="Temperature bin",
                      yaxis_title="Number of regions", yaxis=dict(dtick=1))
    return fig


def yes_no(value) -> str:
    return "n/a" if value is None else ("Yes" if value else "No")


def render_relation(report: ins.RelationReport) -> None:
    analysis_ = report.analysis
    cols = st.columns(3)
    cols[0].metric("Reflexive", yes_no(analysis_.reflexive) if report.regions else "n/a")
    cols[1].metric("Symmetric", yes_no(analysis_.symmetric) if report.regions else "n/a")
    cols[2].metric("Transitive", yes_no(analysis_.transitive) if report.regions else "n/a")
    st.markdown(report.summary)
    for line in report.examples:
        st.markdown(f"- {line}")


# ----------------------------------------------------------------------------- TAB 1
with tab_explorer:
    st.subheader("Temperature explorer")
    st.caption("A regional snapshot for the selected period, with trends and summary statistics.")
    if not regions:
        st.warning("Select at least one region in the sidebar.")
    elif not temps:
        st.warning(f"None of the selected regions has an observation for {period_text}. "
                   "Choose another date or period in the sidebar.")
    else:
        if missing:
            st.warning(f"No observation for {', '.join(missing)} in this period; they are left out of the analysis.")
        st.caption(f"Period: {period_text}. Temperature used for each region = {method_text}.")
        logic = analyze_logic(temps, threshold)
        stats = ts.describe_temperatures(temps)
        table = ts.category_table(temps, threshold, moderate_min, high_min)

        cards = st.columns(5)
        cards[0].metric("Regions analysed", stats["count"])
        cards[1].metric("Mean temperature", f"{stats['mean']:.1f} °C")
        cards[2].metric(f"Hottest: {stats['max']:.1f} °C", stats["hottest"])
        cards[3].metric(f"Coolest: {stats['min']:.1f} °C", stats["coolest"])
        cards[4].metric(f"At or above {threshold:g} °C", f"{logic.count} of {logic.total}")

        chart_left, chart_right = st.columns(2)
        with chart_left:
            show_figure(bar_chart, table, threshold, period_text, key="bar_chart")
        with chart_right:
            show_figure(time_series_chart, df, regions, start, end, threshold, key="time_series")

        if logic.satisfying:
            st.success(f"{logic.count} region(s) at or above {threshold:g} °C: {', '.join(logic.satisfying)}")
        else:
            st.info(f"No region reaches {threshold:g} °C in this selection.")

        table_col, stats_col = st.columns([3, 2])
        with table_col:
            st.markdown("**Regions, temperatures and categories**")
            st.dataframe(table, hide_index=True)
        with stats_col:
            st.markdown("**Descriptive statistics**")
            st.dataframe(ts.statistics_table(stats), hide_index=True)
        counts = ts.category_counts(temps, moderate_min, high_min)
        st.caption(
            f"Categories (Normal < {moderate_min:g} °C ≤ Moderate < {high_min:g} °C ≤ High): "
            + " · ".join(f"{name}: {counts[name]}" for name in ts.CATEGORIES)
            + ". These are adjustable teaching values, not official heatwave declarations."
        )

# ----------------------------------------------------------------------------- TAB 2
analysis = None
with tab_graph:
    st.subheader("Temperature-similarity graph")
    st.caption("Vertices are regions. Two regions are joined by an edge when |temperature(A) − temperature(B)| ≤ "
               "tolerance. This is a mathematical representation only — edges are not roads, routes or proof "
               "of heat spreading. Regions and the period are chosen in the sidebar.")
    tolerance = st.slider("Similarity tolerance (°C)", 0.0, 10.0, 1.5, 0.1, key="tolerance",
                          help="A larger tolerance joins more regions and merges groups.")
    if not temps:
        st.warning("No temperatures are available for the current selection (see the sidebar).")
    else:
        analysis = analyze_graph(temps, tolerance)
        if len(temps) < 2:
            st.warning("Only one region is selected, so the graph has a single vertex and no edges.")

        metrics = st.columns(4)
        metrics[0].metric("Vertices", len(analysis.order))
        metrics[1].metric("Edges", analysis.edge_count)
        metrics[2].metric("Connected components", len(analysis.components))
        metrics[3].metric("Isolated vertices", len(analysis.isolated))

        graph_col, info_col = st.columns([3, 2])
        with graph_col:
            show_figure(build_graph_figure, analysis, key="graph_main",
                        title=f"Temperature-similarity graph ({period_text}, tolerance {tolerance:g} °C)")
            st.caption("Colour = connected component. Diamond = isolated vertex. "
                       "Hover over a vertex, or the middle of an edge, for details.")
        with info_col:
            st.markdown("**Vertex degrees** (number of edges at each vertex)")
            degree_table = pd.DataFrame({
                "Region": analysis.order,
                "Temperature (°C)": [analysis.temperatures[r] for r in analysis.order],
                "Degree": [analysis.degrees[r] for r in analysis.order],
            })
            st.dataframe(degree_table, hide_index=True)
            st.markdown("**Connected components**")
            for sentence in ins.component_sentences(analysis):
                st.markdown(f"- {sentence}")
            st.markdown("**Isolated vertices:** " + (", ".join(analysis.isolated) if analysis.isolated else "none"))

        st.markdown("### Adjacency matrix")
        show_figure(build_matrix_figure, analysis.matrix, analysis.order,
                    "Adjacency matrix (1 = edge, 0 = no edge)", key="adjacency_matrix")
        st.caption("Rows and columns use the same alphabetical region order as BFS and Warshall. "
                   "Entry (i, j) = 1 when regions i and j are joined by an edge, otherwise 0. The matrix is "
                   "symmetric because edges are undirected. The diagonal is 0: the graph has no self-loops "
                   "(even though every region is similar to itself).")
        with st.expander("Show the matrix as a table"):
            st.dataframe(matrix_to_dataframe(analysis.matrix, analysis.order))

        st.markdown("### Why is there (or isn't there) an edge?")
        pair_a, pair_b = st.columns(2)
        region_a = pair_a.selectbox("Region A", analysis.order, key="pair_a")
        region_b = pair_b.selectbox("Region B", analysis.order, index=min(1, len(analysis.order) - 1), key="pair_b")
        has_edge, explanation = ins.explain_pair(analysis.temperatures, region_a, region_b, tolerance)
        (st.success if has_edge else st.info)(explanation)

        st.markdown("### Relation-property analysis")
        render_relation(ins.relation_report(temps, tolerance))

# ----------------------------------------------------------------------------- TAB 3
with tab_algorithms:
    st.subheader("Graph algorithms: BFS and Warshall's algorithm")
    if analysis is None:
        st.warning("No graph is available for the current selection. Choose regions and a period with data.")
    else:
        order = analysis.order
        st.caption(f"Working on the graph for {period_text} with tolerance {tolerance:g} °C: "
                   f"{len(order)} vertices, {analysis.edge_count} edges.")
        col_source, col_target = st.columns(2)
        source = col_source.selectbox("Starting region", order, key="bfs_source")
        target = col_target.selectbox("Destination region", order, index=len(order) - 1, key="bfs_target")
        signature = (tuple(order), tuple(tuple(row) for row in analysis.matrix), source, target)

        if st.button("Find Path", type="primary"):
            st.session_state.bfs_run = {
                "signature": signature,
                "result": bfs_shortest_path(analysis.adjacency_list, source, target),
            }
        run = st.session_state.bfs_run
        current = run if run is not None and run["signature"] == signature else None

        st.markdown("### Breadth-First Search")
        if run is None:
            st.info("Choose two regions and press Find Path.")
        elif current is None:
            st.warning("The graph or the selected regions changed since the last search, so that result was "
                       "cleared. Press Find Path to search the current graph.")
        else:
            result = current["result"]
            if result.source == result.target:
                st.success(f"Source and destination are the same region ({result.source}); "
                           "the path has length 0.")
            elif result.reachable:
                st.success(f"{result.target} is reachable from {result.source}.")
            else:
                st.error(f"No path: {result.target} is not reachable from {result.source} in this graph "
                         "(they lie in different connected components).")
            result_cols = st.columns(3)
            result_cols[0].metric("Reachable", "Yes" if result.reachable else "No")
            result_cols[1].metric("Path length (edges)", result.length if result.reachable else "—")
            result_cols[2].metric("Vertices discovered", len(result.search_order))
            if result.reachable:
                st.markdown("**Shortest path:** " + " → ".join(result.path))
            st.markdown("**Search (discovery) order:** " + " → ".join(result.search_order))
            show_figure(build_graph_figure, analysis, key="graph_path",
                        path=result.path if result.reachable else None,
                        title="Graph with BFS path highlighted in red" if result.reachable
                        else "Graph (no path found)")

        st.markdown("### Warshall's algorithm (reachability)")
        warshall_result = warshall(analysis.matrix, reflexive=True, keep_steps=True)
        reach = warshall_result.reachability
        reachable_by_warshall = is_reachable(reach, order, source, target)
        left, right = st.columns(2)
        with left:
            show_figure(build_matrix_figure, analysis.matrix, order, "Original adjacency matrix",
                        key="warshall_adjacency", highlight=(source, target))
        with right:
            show_figure(build_matrix_figure, reach, order, "Reachability matrix (reflexive)",
                        key="warshall_reach", highlight=(source, target))
        if reachable_by_warshall:
            st.success(f"Warshall: {target} is reachable from {source} (entry = 1 in the reachability matrix).")
        else:
            st.error(f"Warshall: {target} is NOT reachable from {source} (entry = 0).")
        if current is not None:
            if current["result"].reachable == reachable_by_warshall:
                st.success("BFS and Warshall agree on the current graph.")
            else:
                st.error("BFS and Warshall disagree — this should never happen; please report it.")

        if st.checkbox("Show intermediate matrices R_k", key="show_steps"):
            n = len(order)
            k = st.slider("k = number of vertices allowed as intermediate stops", 0, n, 0, key="warshall_k")
            steps = warshall_result.steps
            if k == 0:
                st.caption("R_0: the adjacency matrix with the diagonal set to 1 (reflexive convention).")
            else:
                added = sum(1 for i in range(n) for j in range(n)
                            if steps[k][i][j] and not steps[k - 1][i][j])
                st.caption(f"R_{k}: paths may now pass through {', '.join(order[:k])}. "
                           f"Allowing {order[k - 1]} added {added} new reachable pair(s).")
            show_figure(build_matrix_figure, steps[k], order, f"Intermediate matrix R_{k}", key=f"warshall_step_{k}")

        with st.expander("How do these algorithms work?"):
            st.markdown(
                "**BFS** uses a queue. Start at the source, visit all its neighbours, then their neighbours, and so "
                "on, remembering who discovered each vertex. The first time the destination is discovered, the "
                "path found has the fewest edges. Time complexity: **O(V + E)** with an adjacency list.\n\n"
                "**Warshall's algorithm** starts from the adjacency matrix and, for each vertex k in turn, sets "
                "`R[i][j] = 1` whenever `R[i][k] = 1` and `R[k][j] = 1`. After all vertices have been used as "
                "intermediate stops, `R[i][j] = 1` exactly when j is reachable from i. Three nested loops give "
                "**O(V³)** time. Convention here: every region is reachable from itself, so the diagonal is 1."
            )

# ----------------------------------------------------------------------------- TAB 4
with tab_insights:
    st.subheader("Discrete Mathematics insights")
    num_bins = st.slider("Number of temperature bins (pigeonholes)", 1, 10, 3, key="num_bins")
    if not temps:
        st.warning("No temperatures are available for the current selection (see the sidebar).")
    else:
        insights = ins.build_insights(temps, threshold, tolerance, moderate_min, high_min, num_bins)
        summary = insights.logic

        st.markdown("### 1. Propositional logic")
        st.markdown(f"Proposition **P(x): temperature(x) ≥ {threshold:g} °C**, evaluated for every region x "
                    f"({period_text}). A proposition is a statement that is either true or false.")
        truth_table = pd.DataFrame({
            "Region": list(summary.truth_values),
            "Temperature (°C)": [temps[r] for r in summary.truth_values],
            "P(x)": list(summary.truth_values.values()),
        })
        st.dataframe(truth_table, hide_index=True)
        for line in insights.logic_text:
            st.markdown(f"- {line}")
        logic_cols = st.columns(4)
        logic_cols[0].metric("Regions with P(x) true", f"{summary.count} of {summary.total}")
        logic_cols[1].metric("At least one above?", yes_no(summary.exists_above))
        logic_cols[2].metric("All above?", yes_no(summary.all_above))
        logic_cols[3].metric("All below?", yes_no(summary.all_below))

        st.markdown("### 2. Predicates and quantifiers")
        st.markdown("A **predicate** is a statement about a variable, like P(x). **∃** (there exists) is true if at "
                    "least one region satisfies it; **∀** (for all) is true only if every region does. "
                    "∀x ¬P(x) is the same as saying ¬∃x P(x).")
        st.dataframe(pd.DataFrame(insights.quantifiers), hide_index=True)

        st.markdown("### 3. Functions: temperature → category")
        st.markdown(f"The function f maps each region to exactly one category: **High** if temperature ≥ "
                    f"{high_min:g} °C, **Moderate** if ≥ {moderate_min:g} °C, otherwise **Normal**. Several regions "
                    "can share a category, so f is a function but not one-to-one. These are adjustable teaching "
                    "values, not official heatwave declarations.")
        st.dataframe(insights.category_table, hide_index=True)
        st.caption(" · ".join(f"{name}: {insights.category_counts[name]}" for name in ts.CATEGORIES))

        st.markdown("### 4. Relations")
        st.markdown(f"R on the set of selected regions: **A R B ⇔ |temperature(A) − temperature(B)| ≤ "
                    f"{tolerance:g} °C**.")
        render_relation(insights.relation)

        st.markdown("### 5. Pigeonhole principle")
        st.markdown("Regions are the pigeons; equal-width temperature bins between the lowest and highest selected "
                    "temperature are the pigeonholes. If there are more regions than bins, some bin must hold at "
                    "least ⌈regions ÷ bins⌉ regions.")
        for line in insights.pigeonhole_text:
            st.markdown(f"- {line}")
        if insights.pigeonhole.valid:
            show_figure(pigeonhole_chart, insights.pigeonhole, key="pigeonhole_chart")
            labels = ins.bin_labels(insights.pigeonhole)
            st.dataframe(pd.DataFrame({
                "Bin": labels,
                "Regions": [len(insights.pigeonhole.bins[i]) for i in range(len(labels))],
                "Which regions": [", ".join(insights.pigeonhole.bins[i]) or "—" for i in range(len(labels))],
            }), hide_index=True)

        st.markdown("### 6. Connected components")
        st.markdown("Under the current tolerance the regions fall into these groups of the "
                    "temperature-similarity graph:")
        for sentence in insights.components_text:
            st.markdown(f"- {sentence}")

st.divider()
st.caption("HeatWave Explorer is a Discrete Mathematics teaching project. The sample data is synthetic and the "
           "temperature-similarity graph is a mathematical model, not a map of roads or heat propagation.")
