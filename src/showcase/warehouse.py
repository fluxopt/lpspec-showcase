"""Queries over a directory of archives, with no lpspec in the process.

Every archive the solve job writes is a tree of parquet files, so the whole
directory is a table per glob. The three record tables carry ``run`` on every
row already; a value frame does not, so :func:`frame` derives it from the path.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import polars as pl

#: The kinds of value frame an archive holds, and where each lives under it.
KINDS = {
    'primal': 'answer/primal/{name}/*.parquet',
    'dual': 'answer/dual/{name}/*.parquet',
    'expression': 'answer/expression/{name}/*.parquet',
    'source': 'sources/{name}.parquet',
}


def records(runs: Path) -> pl.DataFrame:
    """One row per run and period: how it terminated, what it reached, when."""
    return _union(runs, 'answer/objective.parquet').sort('run', 'year')


def metrics(runs: Path) -> pl.DataFrame:
    """One row per run and period: how big the model was and what it cost to solve."""
    return _union(runs, 'answer/metrics.parquet').sort('run', 'year')


def inputs(runs: Path) -> pl.DataFrame:
    """One row per run and source: what each input's bytes digest to."""
    return _union(runs, 'sources.parquet').sort('run', 'source')


def catalogue(runs: Path) -> pl.DataFrame:
    """Every kind and name the archives hold, with the dimensions each is keyed by.

    Read off the tree and the parquet schema, so a model with other variables
    lists other rows and nothing here has to change. A source that only lists
    a dimension's labels carries no ``value`` and is left out.
    """
    rows = []
    for kind, pattern in KINDS.items():
        for first in sorted(runs.glob('*/' + pattern.format(name='*'))):
            name = first.stem if kind == 'source' else first.parent.name
            columns = pl.scan_parquet(first).collect_schema().names()
            if 'value' in columns:
                rows.append({'kind': kind, 'name': name, 'dims': [c for c in columns if c != 'value']})
    schema = {'kind': pl.String, 'name': pl.String, 'dims': pl.List(pl.String)}
    return pl.DataFrame(rows, schema=schema).unique(subset=['kind', 'name'], maintain_order=True)


def frame(runs: Path, kind: str, name: str) -> pl.DataFrame:
    """One value frame across every run: ``(run, <dims…>, value)``.

    ``run`` is the archive's directory name, which is the scenario the job
    solved, because a value frame carries the model's own columns only.
    """
    root = runs.resolve().as_posix()
    glob = f'{root}/*/' + KINDS[kind].format(name=name)
    return duckdb.execute(
        """
        select regexp_extract(filename, ? || '/([^/]+)/', 1) as run, * exclude (filename)
        from read_parquet(?, filename = true)
        """,
        [root, glob],
    ).pl()


def changed_inputs(runs: Path, base: str, other: str) -> list[str]:
    """The sources whose bytes differ between two runs, by name."""
    digests = inputs(runs).pivot('run', index='source', values='digest')
    return digests.filter(pl.col(base) != pl.col(other))['source'].sort().to_list()


def _union(runs: Path, member: str) -> pl.DataFrame:
    glob = (runs.resolve() / '*' / member).as_posix()
    return duckdb.execute('select * from read_parquet(?, union_by_name = true)', [glob]).pl()
