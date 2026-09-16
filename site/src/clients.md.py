"""The archive read twice, by two clients that import nothing this repository ships.

A page loader: it runs both clients over the archives at build time and prints
what each returned, beside the source of each. The sources are read from the
files that run, so the page cannot drift from them.
"""

import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'clients'))
from headline import headline  # noqa: E402

runs = Path(os.environ.get('SHOWCASE_RUNS', '../runs'))
if not any(runs.glob('*/answer/objective.parquet')):
    sys.exit(f'{runs.resolve()} holds no archive: run `showcase-solve --runs {runs}` first')

polars_source = (ROOT / 'clients' / 'headline.py').read_text()
sql_source = (ROOT / 'clients' / 'headline.sql').read_text()

in_sql = {
    row['run']: row
    for row in duckdb.sql(sql_source.replace("'runs/", f"'{runs.resolve().as_posix()}/")).pl().to_dicts()
}
NUMBERS = {
    'pathway_cost': ('Pathway cost', '{:,.0f}'),
    'emissions_cut': ('Emissions cut', '{:.1%}'),
    'zero_carbon_share': ('Zero-carbon fleet', '{:.1%}'),
    'carbon_price': ('Carbon price', '{:,.2f}'),
}

rows = []
for name in sorted(in_sql):
    polars_answer = headline(runs / name)
    for key, (label, fmt) in NUMBERS.items():
        agree = abs(polars_answer[key] - in_sql[name][key]) <= abs(in_sql[name][key]) * 1e-9
        rows.append(
            f'| `{name}` | {label} | {fmt.format(polars_answer[key])} | {fmt.format(in_sql[name][key])} | {"yes" if agree else "**no**"} |'
        )

table = '\n'.join(rows)

sys.stdout.write(f"""---
title: Clients
---

# The archive has no client library

The other pages read the archive through one: [`warehouse.py`](https://github.com/fluxopt/lpspec-showcase/blob/main/src/showcase/warehouse.py), about sixty lines of queries. That file is a convenience, not a contract. The contract is the directory: **one parquet file per variable, dual, named expression and input, keyed by the model's own dimensions.** Anything that reads parquet is already a client.

Here are two that import nothing this repository ships. Both were run when this page was built, over the same `runs/` directory the other pages read, and both answer the four questions the [pathway page](./) leads with.

| run | number | polars | DuckDB | agree |
|---|---|---|---|---|
{table}

That last column is checked in CI as well as printed here: `tests/test_clients.py` holds the two clients to each other on every archive in the directory, so a drift between them fails the build rather than reaching this page.

## In polars

Ten lines of dataframe code, no SQL, no server.

```python
{polars_source.rstrip()}
```

## In DuckDB

One query, every scenario at once, in a shell with nothing installed:

```bash
duckdb -c ".read clients/headline.sql"
```

```sql
{sql_source.rstrip()}
```

## Why this page exists

Two properties of the archive make it possible, and neither is about this repository.

**The dimensions carry the model's own names.** A value frame is `(year, day, hour, generator, value)`, not `(dim1, dim2, dim3, value)`, because the names come from the spec that was solved. So a reader who has never seen the model can still group by `generator`, and two quantities keyed the same way join without a mapping table.

**The record tables carry `run`, and a value frame does not.** Digests, statuses and metrics concatenate across archives with one glob. A value frame holds the model's columns only, so `run` comes off the path — which is what `filename = true` is doing in the query above.

The consequence is that a DuckDB shell, a notebook, a BI tool pointed at the directory, and this site are the same kind of thing. Nothing here is privileged.
""")
