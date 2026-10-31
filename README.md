<<<<<<< HEAD
# HeatWave Explorer

An interactive **Discrete Mathematics** dashboard built with Python and Streamlit. It takes temperature observations from different regions and uses them to demonstrate propositional logic, quantifiers, functions, relations, graphs, adjacency matrices, BFS, Warshall's algorithm, connected components and the pigeonhole principle — all computed live from the selected data.

> **Important:** the bundled dataset is **synthetic** (fictional regions, computer-generated numbers). It is not real weather data and is not from the India Meteorological Department or any other source. The temperature thresholds are **adjustable teaching values, not an official heatwave classification**.

---

## 1. Project overview

HeatWave Explorer lets you pick a date (or date range), choose regions, set a temperature threshold, and then explore the same data through different Discrete Mathematics lenses: *Which regions satisfy a logical condition? Which regions are "similar"? How do they group together? Can I get from region A to region B through a chain of similar regions?*

## 2. Problem statement

Discrete Mathematics concepts such as relations, graphs and logic are often taught on paper with tiny hand-made examples. This project shows how the same ideas work on a realistic table of data, with sliders and buttons so you can *see* what changes when you change an input.

## 3. Objectives

- Implement BFS and Warshall's algorithm from scratch and use them inside a working application.
- Show how logic, relations, graphs and the pigeonhole principle connect to one dataset.
- Make every result dynamic: nothing on the dashboard is hard-coded to the sample data.
- Keep the code beginner-friendly, tested and easy to extend.

## 4. Main features

| Tab | What you can do |
|---|---|
| **Temperature Explorer** | Load the sample dataset or upload your own CSV, choose a date or range and regions, set the threshold, see summary cards, a regional bar chart, a time-series chart, a table with categories, regions above the threshold and descriptive statistics. |
| **Relationship Graph** | Adjust the similarity tolerance; see the graph, vertex degrees, connected components, isolated vertices, the adjacency matrix, an explanation of any chosen edge, and a test of the relation's properties. |
| **Graph Algorithms** | Pick a start and destination, press **Find Path** to run BFS (path, length, search order, highlighted graph), view Warshall's reachability matrix and optionally every intermediate matrix R_k. |
| **DM Insights** | Propositional logic, ∃/∀ quantifiers, the temperature-category function, relation properties, an interactive pigeonhole demonstration and a connected-component summary. |

## 5. Discrete Mathematics concepts used

| Concept | Where |
|---|---|
| Propositional logic: `P(x) = temperature(x) ≥ threshold` | `algorithms/logic.py` |
| Predicates and quantifiers (∃, ∀) | `algorithms/logic.py` |
| Functions (region → category) | `services/temperature_service.py` |
| Relations (reflexive, symmetric, transitive) | `algorithms/relations.py` |
| Graphs, degrees, isolated vertices, connected components | `algorithms/graph_builder.py` |
| Adjacency matrix | `algorithms/graph_builder.py`, `visualizations/matrix_visualization.py` |
| Breadth-First Search | `algorithms/bfs.py` |
| Warshall's algorithm (transitive closure) | `algorithms/warshall.py` |
| Pigeonhole principle | `algorithms/pigeonhole.py` |

## 6. Technology stack

Python · Streamlit · Pandas · NumPy · NetworkX · Plotly · Pytest.
All charts and matrices are drawn with Plotly. NetworkX stores the graph; **BFS, Warshall and the connected components are my own code** — NetworkX's algorithms are used only inside a test (`tests/test_cross_check.py`) as an independent referee. No machine learning, no external APIs, no database, no internet needed after installing the dependencies.

## 7. Folder structure

```
heatwave-analysis/
├── app.py                         Streamlit dashboard (UI only)
├── requirements.txt
├── README.md
├── pytest.ini                     lets `pytest` find the project packages
├── .gitignore
├── .streamlit/config.toml         light theme, usage statistics off
├── data/
│   └── sample_temperatures.csv    synthetic sample data (1,080 rows)
├── scripts/
│   └── generate_sample_data.py    regenerates the CSV deterministically
├── algorithms/                    pure Python, no Streamlit
│   ├── logic.py                   P(x), ∃, ∀
│   ├── relations.py               similarity relation + property tests
│   ├── graph_builder.py           graph, adjacency matrix, degrees, components
│   ├── bfs.py                     BFS from scratch
│   ├── warshall.py                Warshall from scratch
│   └── pigeonhole.py              pigeonhole principle
├── services/
│   ├── data_service.py            CSV loading, validation, filtering
│   ├── temperature_service.py     categories, statistics, tables
│   └── insights_service.py        plain-language insights
├── visualizations/
│   ├── graph_visualization.py     Plotly graph
│   └── matrix_visualization.py    Plotly matrices
└── tests/                         pytest suite
```

## 8. Dataset schema

```
date,region,temperature_celsius
2026-03-01,Northfield,24.9
```

| Column | Meaning |
|---|---|
| `date` | `YYYY-MM-DD` |
| `region` | non-empty text |
| `temperature_celsius` | number, °C |

Each region may appear only once per date.

## 9. The sample CSV is synthetic

`data/sample_temperatures.csv` contains 12 **fictional** regions (Northfield, Eastvale, Southridge, …) for 90 consecutive days (1 March – 29 May 2026), 1,080 observations. Each region follows a slow warming trend plus short weather swings, a few shared hot spells and some region-specific events, with small random noise from a fixed seed. Different regions have different base temperatures, so categories, similarity groups and unreachable pairs all appear in the demo.

### Regenerating the CSV

```powershell
python scripts/generate_sample_data.py
```

The script is deterministic (fixed seed), so it writes the same file every time on the same library versions. The committed CSV is the reference copy.

## 10. Windows setup (PowerShell)

Requires Python 3.9 or newer. From the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell refuses to run the activation script, allow it for this window only and try again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Run the application

```powershell
streamlit run app.py
```

It opens in your browser (normally http://localhost:8501) and loads the sample dataset immediately.

### Run the tests

```powershell
python -m pytest -q
```

`tests/test_app_smoke.py` starts the whole app headlessly and is skipped automatically if Streamlit or Plotly is not installed.

## 11. How the key ideas work

### Temperature analysis vs. similarity relation vs. graph path vs. geography

- **Temperature analysis** — looking at each region's temperature on its own: comparing, categorising, testing against a threshold.
- **Temperature-similarity relation** — a mathematical rule on *pairs* of regions: `A R B ⇔ |temperature(A) − temperature(B)| ≤ tolerance`.
- **Graph path** — a chain of regions where each neighbouring pair is similar, e.g. `A – B – C`. It exists only in the graph built from the relation.
- **Physical geographical connectivity** — whether places are actually near each other or joined by roads. **HeatWave Explorer does not model this.** The temperature-similarity graph is a mathematical representation; its edges are not roads or travel routes and do not show heat propagating from one place to another.

### Representative temperature

For a **single date**, each region's temperature is its observation on that date. For a **date range**, it is the **mean** of its daily observations in that range. Regions with no observation in the period are listed and left out — a value is never invented.

### Adjacency matrix

The graph has *n* regions, listed in alphabetical order. The adjacency matrix is an *n × n* table where entry (i, j) is **1** if regions i and j are joined by an edge and **0** otherwise. It is symmetric (edges are undirected). **Convention:** the diagonal is 0 because the graph has no self-loops. Rows and columns use the same order in the matrix view, BFS and Warshall.

### Breadth-First Search (BFS)

BFS keeps a queue. Start at the source, visit all its neighbours, then *their* neighbours, and so on, remembering which vertex discovered each one. The first time the destination is discovered, the path back through those "parents" has the **fewest edges** possible in an unweighted graph. Time complexity with an adjacency list: **O(V + E)**. The "search order" shown is the order in which vertices were discovered.

### Warshall's algorithm

Start with the adjacency matrix. For each vertex k in turn, allow k as an intermediate stop: if i reaches k and k reaches j, then i reaches j. After all vertices have been tried, entry (i, j) = 1 exactly when j can be reached from i. Three nested loops give **O(V³)** time. **Convention:** reachability is *reflexive* — every region can reach itself, so the reachability matrix has 1s on the diagonal. The optional "intermediate matrices" view shows R₀ … Rₙ.

### Relation properties

For the set of selected regions and `A R B ⇔ |t(A) − t(B)| ≤ tolerance`:

- **Reflexive** — every region is related to itself (|t − t| = 0). Always true.
- **Symmetric** — if A R B then B R A (|a − b| = |b − a|). Always true.
- **Transitive** — if A R B and B R C then A R C. **Not always true:** with a tolerance of 1 °C, 30 °C ~ 31 °C and 31 °C ~ 32 °C, but 30 °C and 32 °C differ by 2. The dashboard *tests* all three properties on the current data and shows a counterexample when one fails. When all three hold, R is an equivalence relation and the groups are cliques.

### Pigeonhole principle

The selected regions are the pigeons; equal-width temperature bins covering the lowest to the highest selected temperature are the pigeonholes. If there are more regions than bins, at least two regions must share a bin, and in general some bin must hold at least **⌈regions ÷ bins⌉** regions. That number is a guaranteed *lower bound* — the fullest bin you actually observe can be larger. If regions ≤ bins the basic principle forces nothing, and with no regions or zero bins the dashboard says it cannot be applied.

## 12. CSV upload and validation

Upload a CSV in the Temperature Explorer tab. It must have the columns `date, region, temperature_celsius`. The app **rejects** (with a clear message that includes file line numbers) files that are empty, miss a column, contain invalid dates, non-numeric temperatures, missing region names, or duplicate region/date pairs. It **warns** about a single region, a single date, missing observations for some regions, and implausible temperatures. A valid upload replaces the active dataset; **Use built-in sample dataset** switches back.

## 13. Limitations

- Similarity is based only on temperature; it says nothing about distance, wind, terrain or causes.
- A date range is summarised by the mean, which hides short hot spells inside the range.
- Pigeonhole bins are equal-width and derived from the selected regions, so their edges change when the selection changes.
- Warshall's O(V³) cost is fine for a dozen regions but not designed for thousands.
- The sample data is synthetic and the categories are not an official classification.

## 14. Future enhancements

- Weighted edges and Dijkstra's shortest path.
- Compare two dates side by side.
- Minimum spanning tree of the similarity graph.
- Export the adjacency matrix and results as CSV.
- Optional real geographic coordinates (kept clearly separate from the similarity graph).

## 15. Uploading this project to GitHub

Clone your repository, copy the project files into the clone, then commit and push:

```powershell
git clone https://github.com/soujanyamohanty11-ToT/heatwave-analysis.git
cd heatwave-analysis
# Copy everything from the extracted ZIP's heatwave-analysis folder into this folder.
# (Check first: if the clone already has files, compare them before overwriting anything.)
git status
git add .
git commit -m "Add HeatWave Explorer Discrete Mathematics dashboard"
git push origin HEAD
```

If the repository is completely empty, `git push origin HEAD` creates its first branch. If the clone already contains files you want to keep, resolve any name clashes (`README.md`, `.gitignore`) by merging them by hand before committing.
=======
# heatwave-analysis
>>>>>>> 3b572c54a4454e774af047e7a07bb57f3ce3bd89
