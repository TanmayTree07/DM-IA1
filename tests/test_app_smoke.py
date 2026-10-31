"""Runs the whole Streamlit app headlessly (needs streamlit and plotly installed)."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def new_app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=90)
    at.run()
    return at


def test_app_starts_with_sample_data_without_errors():
    at = new_app()
    assert not at.exception
    assert not at.error
    assert len(at.tabs) == 4


def test_find_path_button_runs_bfs_and_warshall():
    at = new_app()
    at.slider(key="tolerance").set_value(10.0)   # large tolerance -> connected graph
    at.run()
    next(b for b in at.button if b.label == "Find Path").click()
    at.run()
    assert not at.exception
    assert any("reachable" in s.value.lower() for s in at.success)
    assert any("agree" in s.value for s in at.success)


def test_changing_inputs_does_not_crash():
    at = new_app()
    at.slider(key="tolerance").set_value(0.0)
    at.slider(key="num_bins").set_value(1)
    at.run()
    assert not at.exception
