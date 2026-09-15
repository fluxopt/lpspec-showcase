"""Nothing past the solve job imports lpspec, and the site's loader ships what the pages read."""

import ast
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
LOADER = ROOT / 'site' / 'src' / 'data' / 'runs.zip.py'
READERS = [ROOT / 'src' / 'showcase' / 'warehouse.py', LOADER]


def imported_by(module: Path) -> set[str]:
    names = set()
    for node in ast.walk(ast.parse(module.read_text())):
        if isinstance(node, ast.Import):
            names.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split('.')[0])
    return names


@pytest.mark.parametrize('module', READERS, ids=lambda p: p.name)
def test_a_reader_imports_no_lpspec(module: Path):
    assert 'lpspec' not in imported_by(module), f'{module.name} reads parquet; only the solve job imports lpspec'


def test_the_loader_ships_every_table(runs: Path, tmp_path: Path):
    """The zip the pages read: the record tables, one frame per catalogue entry, the catalogue and the model."""
    done = subprocess.run(
        [sys.executable, str(LOADER)],
        env={**os.environ, 'SHOWCASE_RUNS': str(runs)},
        capture_output=True,
        check=True,
    )
    out = tmp_path / 'runs.zip'
    out.write_bytes(done.stdout)
    names = set(zipfile.ZipFile(out).namelist())
    assert {'objective.parquet', 'metrics.parquet', 'sources.parquet', 'catalogue.json', 'model.yaml'} <= names
    assert {
        'primal/total.parquet',
        'dual/balance.parquet',
        'expression/emissions.parquet',
        'source/load.parquet',
    } <= names
    assert 'source/day.parquet' not in names, 'a table of labels is not shipped'


def test_the_loader_says_when_there_is_nothing_to_read(tmp_path: Path):
    done = subprocess.run(
        [sys.executable, str(LOADER)], env={**os.environ, 'SHOWCASE_RUNS': str(tmp_path)}, capture_output=True
    )
    assert done.returncode != 0
    assert b'holds no archive' in done.stderr
