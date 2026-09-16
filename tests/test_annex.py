"""The annex is the model page and the dashboard joined, and these hold it to both halves.

What could go wrong is silent: an equation printed in derived names rather than
the declared notation, a number that does not come from the archive beside it,
or a declaration missing because the catalogue moved.
"""

import os
import subprocess
import sys
from pathlib import Path

import polars as pl

from showcase import warehouse
from showcase.annex import annex

ROOT = Path(__file__).parents[1]
SYMBOLS = ROOT / 'models' / 'pathway.symbols.yaml'
LOADER = ROOT / 'site' / 'src' / 'annex.md.py'


def test_every_declaration_the_archive_holds_is_printed(runs: Path):
    page = annex(runs, 'base', SYMBOLS)
    catalogue = warehouse.catalogue(runs)
    for row in catalogue.filter(pl.col('kind') != 'source').iter_rows(named=True):
        assert f'### {row["name"]}\n' in page, f'{row["kind"]} {row["name"]} is in the catalogue and not on the page'
    for row in catalogue.filter(pl.col('kind') == 'source').iter_rows(named=True):
        assert f'### {row["name"]}\n' not in page, 'a parameter is data, not a declaration to typeset'


def test_the_equations_are_in_the_declared_notation(runs: Path):
    page = annex(runs, 'base', SYMBOLS)
    assert 'x^{0}_{g}' in page, 'the symbol table is applied, not the derived name'
    assert 'E^{\\max}' in page and '\\mathcal{G}' in page
    assert '```tex' in page, "the equations are fenced for the site's own renderer"


def test_the_objective_row_is_what_the_archive_recorded(runs: Path):
    page = annex(runs, 'base', SYMBOLS)
    records = warehouse.records(runs).filter(pl.col('run') == 'base')
    assert f'**{records["objective"].sum():,.0f}**' in page, "the total is the archive's, not a transcription"
    for value in records['objective']:
        assert f'{value:,.0f}' in page, 'and so is every period'


def test_a_priced_row_is_told_apart_from_one_that_costs_nothing(runs: Path):
    """An equality binds everywhere and is still unpriced where the objective would not move."""
    page = annex(runs, 'base', SYMBOLS)
    balance = page.split('### balance\n')[1].split('###')[0]
    rows, priced, largest = (cell.strip() for cell in balance.strip().splitlines()[-1].strip('|').split('|'))
    assert 0 < int(priced) < int(rows), 'the price of meeting demand varies by hour, so some rows are unpriced'
    assert float(largest.replace(',', '')) > 0, 'and the priced ones carry a price'

    slack = annex(runs, 'cheap_solar', SYMBOLS).split('### carbon\n')[1].split('###')[0]
    assert '| 0 | 0.00 |' in slack, 'a cap the fleet stays under has no binding row and no price'


def test_the_page_loader_prints_the_reference_run(runs: Path):
    done = subprocess.run(
        [sys.executable, str(LOADER)],
        env={**os.environ, 'SHOWCASE_RUNS': str(runs)},
        capture_output=True,
        check=True,
    )
    page = done.stdout.decode()
    assert page.startswith('---\ntitle: Annex\n---'), 'a page loader prints front matter first'
    assert '# base, as solved' in page, 'the first archive in the directory is the one printed'
    assert '$`' not in page, "none of GitHub's inline delimiters survive"


def test_the_page_loader_says_when_there_is_nothing_to_read(tmp_path: Path):
    done = subprocess.run(
        [sys.executable, str(LOADER)], env={**os.environ, 'SHOWCASE_RUNS': str(tmp_path)}, capture_output=True
    )
    assert done.returncode != 0
    assert b'holds no archive' in done.stderr
