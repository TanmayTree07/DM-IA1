import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_sample_data.py"


def load_script():
    spec = importlib.util.spec_from_file_location("generate_sample_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generation_is_deterministic():
    gen = load_script()
    assert gen.generate_rows() == gen.generate_rows()


def test_shape_of_generated_data():
    gen = load_script()
    rows = gen.generate_rows()
    assert len(rows) == len(gen.REGIONS) * gen.NUM_DAYS
    assert len({(d, r) for d, r, _ in rows}) == len(rows)  # no duplicate region/date


def test_writing_the_csv_twice_gives_identical_files(tmp_path):
    gen = load_script()
    first, second = tmp_path / "a.csv", tmp_path / "b.csv"
    gen.write_csv(first)
    gen.write_csv(second)
    assert first.read_bytes() == second.read_bytes()
    assert first.read_text().splitlines()[0] == "date,region,temperature_celsius"
