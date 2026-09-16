"""What the archive lets you ask: three questions, each one query, each crossing a boundary.

A page loader, because the client sources at the bottom are files on disk. The
questions themselves are live queries, run by DuckDB in the reader's browser
against the same parquet every other page reads.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
runs = Path(os.environ.get('SHOWCASE_RUNS', '../runs'))
if not any(runs.glob('*/answer/objective.parquet')):
    sys.exit(f'{runs.resolve()} holds no archive: run `showcase-solve --runs {runs}` first')

sources = {name: (ROOT / 'clients' / name).read_text().rstrip() for name in ('headline.py', 'headline.sql')}

sys.stdout.write(f"""---
title: Clients
sql:
  objective: ./data/runs/objective.parquet
  price: ./data/runs/dual/balance.parquet
  dispatch: ./data/runs/primal/p.parquet
  cost: ./data/runs/source/cost.parquet
  digests: ./data/runs/sources.parquet
---

# What the archive lets you ask

Solver output is usually indexed by whatever the builder happened to name its variables, so reading it means running the builder's code. This archive is parquet keyed by **the model's own declared dimensions**, and the duals, the primals and the named expressions all come back in the same shape.

The consequence is that questions which are normally a scripting exercise become a join. Here are three, each one query, run by DuckDB in your browser.

## Which hours are paying for the fleet?

The shadow price on the energy balance is what one more MW would cost at that hour. Joining it to what was running needs a **dual and a primal in the same query**, keyed on the dimensions the model declared:

```sql id=scarcity
select p.year, p.day, p.hour, round(p.value) as price_per_mw,
       string_agg(d.generator || ' ' || round(d.value) || ' MW', ', ' order by d.value desc) as running
from price p join dispatch d on p.run = d.run and p.year = d.year and p.day = d.day and p.hour = d.hour
where p.run = 'base' and p.value > 1e-9 and d.value > 1e-6
group by p.year, p.day, p.hour, p.value
order by p.value desc limit 5
```

```js
display(Inputs.table(scarcity, {{maxHeight: 210}}));
```

```sql id=rent
select count(*) as hours, count(*) filter (where value > 1e-9) as priced,
       round(100.0 * count(*) filter (where value > 1e-9) / count(*)) as pct_of_hours
from price where run = 'base'
```

```js
const only = rent.get(0);
display(html`<p><b>${{only.priced}} of ${{only.hours}} hours</b> carry any price at all — ${{only.pct_of_hours}}% of them — and the three most expensive are all the summer evening, after solar has gone and gas is at its cap. Those hours are what the build decision is paying for. Nothing in the model says "peak"; it falls out of the duals.</p>`);
```

## What did the carbon cap cost?

The record tables carry `run` on every row, so comparing scenarios needs no bookkeeping and no join key you invented:

```sql id=cost_of_cap
select run, round(sum(objective)) as pathway_cost,
       round(sum(objective) - (select sum(objective) from objective where run = 'base')) as vs_base
from objective group by run order by vs_base
```

```js
display(Inputs.table(cost_of_cap, {{maxHeight: 180}}));
```

## Which input moved between two runs?

Every archive digests the bytes of every input it was solved with. So *what changed* is a query rather than a convention or a changelog:

```sql id=moved
select source, count(distinct digest) as distinct_bytes
from digests where run in ('base', 'cheap_solar')
group by source having count(distinct digest) > 1
```

```js
display(Inputs.table(moved, {{maxHeight: 140}}));
```

One row. `cheap_solar` differs from `base` in `invest` and in nothing else, and the archive proves it rather than asserting it — which is the difference between a result you can defend and one you remember writing.

## Why these are one query each

Three properties, none of them about this repository:

**The dimensions carry the model's own names.** `year`, `day`, `hour`, `generator` come from the spec that was solved, so a reader who has never seen the model can group by `generator`, and two quantities keyed the same way join without a mapping table.

**A dual, a primal and a named expression have the same shape.** `(dims…, value)` for all three. That is why the first query above is a join rather than a script.

**The spec and the digests are in the box.** `model.yaml` sits beside the answer and every input is digested, so a number can be traced to the math and the bytes that produced it.

## Run one yourself

`objective`, `price`, `dispatch`, `cost` and `digests` are registered. Edit and it re-runs.

```js
const db = await DuckDBClient.of({{
  objective: FileAttachment("data/runs/objective.parquet"),
  price: FileAttachment("data/runs/dual/balance.parquet"),
  dispatch: FileAttachment("data/runs/primal/p.parquet"),
  cost: FileAttachment("data/runs/source/cost.parquet"),
  digests: FileAttachment("data/runs/sources.parquet"),
}});
```

```js
const typed = view(Inputs.textarea({{
  label: "SQL",
  rows: 5,
  submit: "Run",
  value: "-- what does each technology earn at those scarcity prices?\\nselect d.generator, round(sum(d.value * p.value)) as rent\\nfrom dispatch d join price p on d.run = p.run and d.year = p.year and d.day = p.day and d.hour = p.hour\\nwhere d.run = 'base'\\ngroup by d.generator order by rent desc",
}}));
```

```js
const answer = await db.query(typed).then((rows) => Inputs.table(rows, {{maxHeight: 300}}))
  .catch((error) => html`<div class="warning" style="padding:0.5rem 1rem"><b>${{error.name}}</b>: ${{error.message}}</div>`);
display(answer);
```

## Away from the browser

Neither of these imports lpspec, and neither imports this repository's `warehouse.py`. `tests/test_clients.py` holds them to each other on every archive in the directory.

<details><summary><b>Ten lines of polars</b> — <code>uv run python clients/headline.py runs/base</code></summary>

```python
{sources['headline.py']}
```

</details>

<details><summary><b>One DuckDB query</b>, every scenario at once — <code>duckdb -c ".read clients/headline.sql"</code></summary>

`runs/` is written by the solve job rather than checked in, and the globs are
relative, so both of these matter:

```bash
uv run showcase-solve --runs runs     # once, if runs/ is not there yet
duckdb -c ".read clients/headline.sql"
```

```sql
{sources['headline.sql']}
```

</details>
""")
