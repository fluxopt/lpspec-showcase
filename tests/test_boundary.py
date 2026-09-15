"""The dashboard process imports no lpspec, and runs against what the job wrote."""

import ast
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

SRC = Path(__file__).parents[1] / 'src' / 'showcase'
READERS = ['warehouse.py', 'dashboard.py']


def imported_by(module: Path) -> set[str]:
    tree = ast.parse(module.read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split('.')[0])
    return names


@pytest.mark.parametrize('module', READERS)
def test_a_reader_imports_no_lpspec(module: str):
    assert 'lpspec' not in imported_by(SRC / module), f'{module} reads parquet, and only the solve job imports lpspec'
    assert 'solve' not in imported_by(SRC / module)


def test_the_dashboard_renders_the_archive(runs: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('SHOWCASE_RUNS', str(runs))
    at = AppTest.from_file(str(SRC / 'dashboard.py'), default_timeout=120).run()
    assert not at.exception, at.exception
    assert at.title[0].value == 'Capacity-expansion pathway'


def test_the_dashboard_says_when_there_is_nothing_to_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('SHOWCASE_RUNS', str(tmp_path))
    at = AppTest.from_file(str(SRC / 'dashboard.py'), default_timeout=60).run()
    assert not at.exception, at.exception
    assert 'holds no archive' in at.error[0].value
